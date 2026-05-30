# Redis Redlock — Distributed Lock + Critique + Fencing Tokens

## Source / Origin
- Original "Redlock" algorithm by antirez (Salvatore Sanfilippo): <a href="https://redis.io/docs/manual/patterns/distributed-locks/" target="_blank" rel="noopener noreferrer">https://redis.io/docs/manual/patterns/distributed-locks/</a>
- Famous critique by Martin Kleppmann: "How to do distributed locking" (2016) — disputed Redlock's safety.
- Counter-rebuttal by antirez: "Is Redlock safe?" — same year.
- Companion concept doc: `backend-data-prep/caching/02-redis-patterns.md` — Distributed locks section.
- Interview prompt: "How would you implement a distributed lock with Redis? What are its safety properties?"

## Why this question matters in interviews
Distributed locks are the canonical "easy to get wrong" interview problem. Naive `SETNX` is unsafe; SETNX + EX TTL is *almost* safe; Redlock claims to be safe across multiple Redis instances; Kleppmann argues Redlock is *fundamentally* unsafe under network partitions and GC pauses. The senior signal is being able to (a) name plain SETNX's failure modes, (b) describe the SETNX+TTL+UUID+Lua release pattern, (c) describe Redlock's algorithm, (d) explain Kleppmann's critique honestly, and (e) propose fencing tokens as the cleaner correctness primitive.

## Concepts involved

### Syntax to lock in

**Plain SETNX (unsafe):**
```
SETNX lock:order:42 1     # acquire
DEL lock:order:42         # release
```

Why unsafe: no TTL → stuck lock if holder dies; no owner identification → anyone can release.

**Safe single-instance lock (SETNX + TTL + UUID + Lua release):**
```
# Acquire
SET lock:order:42 <uuid> NX EX 30

# Release (atomic check-and-delete)
EVAL "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end" 1 lock:order:42 <uuid>
```

**Redlock (multi-instance):**
1. Get current ms timestamp T0.
2. Try to acquire the lock on each of N independent Redis masters with the same key, value (UUID), and TTL, using SET NX EX with a short per-node timeout (typically 5-50ms).
3. If acquired on majority (N/2 + 1) AND elapsed time < TTL, lock is held.
4. Effective lock validity = TTL - (T_acquired - T0) - clock_drift.
5. Release on all N masters using the Lua check-and-delete.

### Edge cases / interview traps
1. **Stuck lock without TTL** — holder dies; lock never released. *Always* TTL.
2. **Wrong-owner release** — release operation deletes someone else's lock if you forget the UUID check.
3. **TTL expires mid-operation** — operation continues without the lock; another node also acquires and proceeds. Race. Fence with monotonic tokens.
4. **GC pause / VM freeze longer than TTL** — same race as #3 but caused by the *holder's* execution stalling.
5. **Clock drift between Redis instances** — Redlock validity is tied to wall-clock time on Redis nodes; drift breaks the safety argument.
6. **Network partition during release** — one of N Redis masters can't be reached for release; key lingers until TTL.
7. **Lock renewal (watchdog) hazards** — renewing the TTL from a background thread requires careful synchronization with main lock logic.
8. **Replicas + failover** — if you lock against a master, then it dies before async-replicating the lock to a replica, the replica takes over without the lock → another client can acquire. Redlock against multiple *masters* mitigates by majority; against one master + replica is unsafe.
9. **Fairness** — Redis locks are not FIFO; under contention, a recently-arrived client can win against a long-waiting one.

## Mental Model

### Plain SETNX lock — what fails

```
Time  Client A                    Client B           Lock state
0     SETNX lock 1 → 1 (ok)                            lock=1 (held by A)
1                                  SETNX lock 1 → 0    lock=1
... A crashes ...
1000                                                    lock=1   ← stuck forever
```

### SETNX + TTL — better, still racy

```
Time  Client A                    Client B           Lock state
0     SET lock UUID-A NX EX 30 → ok                     lock=UUID-A, TTL=30
... A's process pauses 35s for GC ...
30                                                      lock expired
31                                  SET lock UUID-B NX EX 30 → ok    lock=UUID-B
35    A resumes, thinks it has lock                     lock=UUID-B
35    A does critical operation                         ← A and B both think they hold the lock
                                  B also doing critical op
                                                        ← split-brain
```

This is the fundamental race that **fencing tokens** solve.

### Redlock — majority across N independent masters

```
Redis 1   Redis 2   Redis 3   Redis 4   Redis 5
  │         │         │         │         │
  ▼         ▼         ▼         ▼         ▼
 OK        OK        OK        FAIL       OK     ← majority (4/5) → lock held
                                  (network blip)

Validity duration = initial_TTL − time_spent_acquiring − clock_drift_budget
```

### Kleppmann's critique

```
"Even if Redlock is acquired correctly, two clients can still violate mutual exclusion under:
   - Long GC pauses
   - Network partitions delaying release
   - Clock drift on Redis nodes

  Because Redlock's safety is based on wall-clock TTLs, any source of time deviation
  breaks the model."

Antirez's response: "These failures are rare. For most use cases Redlock is fine.
                    For correctness-critical use cases, use a coordination service (ZooKeeper, etcd)
                    with fencing tokens."
```

### Fencing token timeline

```
Time  Client A                  Lock service           Storage system
0     acquire() → token=42      lock granted to A
1     A proceeds with write
2     ... A pauses (GC)
30                              A's lease expires
31                              B acquires, token=43
32    B writes (token=43)                              accept (token 43 > last 0)
33                                                     last_seen_token = 43
40    A resumes, writes (token=42)                     REJECT (42 < 43)
                                                       (storage rejects A's write)
```

The storage system checks the monotonic token; A's stale write is rejected even though A still believes it holds the lock. See `redis-fencing-token.md`.

## Why interviewers care
- Distributed locks are the canonical "easy to get wrong" question.
- Tests understanding of **time, partial failure, and isolation in distributed systems**.
- Knowing **Redlock's controversy** signals you've read past the docs.
- Fencing tokens are the right answer for correctness-critical paths and a senior-level concept.

## Common beginner confusion
- **"SETNX is a distributed lock."** Only with TTL + UUID + Lua release.
- **"Adding a TTL makes it safe."** Safe against crashed holders; not safe against GC pauses or partition-induced delays.
- **"Redlock is the gold standard."** Disputed by Kleppmann; safe for most use cases but not for correctness-critical mutual exclusion.
- **"The lock guarantees mutual exclusion of clients."** No — it guarantees mutual exclusion *at lock-grant time*. Without fencing, the underlying resource can still receive operations from a stale lock holder.
- **"Use Redis replicas for HA."** Async replication makes Redis-based locks unsafe under failover. Either use multi-master Redlock or accept the single-instance failure mode.

## Brute force approach
**Database row lock.** Use Postgres `SELECT FOR UPDATE` or a dedicated `locks` table. Works, but ties lock latency to DB latency (~5-50ms) and adds DB load. Fine for low-frequency locks.

**ZooKeeper / etcd ephemeral nodes.** Battle-tested, correct, slower than Redis (10s of ms). Use when correctness matters more than latency.

**"Just use Redis SETNX."** Unsafe. See above.

## Optimal approach

### Single-instance safe lock (most common production choice)
- `SET key uuid NX EX ttl` for acquisition.
- Lua `if get == uuid then del end` for release.
- Choose TTL > expected operation time × 2.
- Optional watchdog: renew TTL periodically while operation in progress.
- **Limitations:** unsafe under Redis failover (async replication).

### Redlock (multi-instance)
- N=5 independent Redis masters.
- Acquire on majority, validity = TTL − elapsed − clock-drift.
- **Limitations:** safety argument depends on wall-clock; controversial.

### Fencing tokens (correctness-critical)
- Lock service hands out a monotonic token with each acquisition.
- Downstream resource checks token on every operation; rejects stale tokens.
- Lock can be Redis, ZooKeeper, etcd — doesn't matter if the token is monotonic.
- **The resource must cooperate** — your DB / storage must check the token.

### Decision tree
- "Just need to serialize a cron job across instances" → single-instance Redis lock, TTL safety net.
- "Need exclusive access to a payment / billing operation" → Redlock + fencing token, or ZooKeeper / etcd.
- "Throw-away coordination, OK to retry on conflict" → optimistic CAS instead of lock.

## Solution

### Safe single-instance lock (Node.js + ioredis)

```javascript
const crypto = require('crypto');
const Redis = require('ioredis');
const redis = new Redis();

class RedisLock {
  constructor(key, ttlMs = 30_000) {
    this.key = key;
    this.ttlMs = ttlMs;
    this.token = crypto.randomUUID();
  }

  async acquire(retries = 0, backoffMs = 100) {
    for (let i = 0; i <= retries; i++) {
      const result = await redis.set(this.key, this.token, 'PX', this.ttlMs, 'NX');
      if (result === 'OK') return true;
      if (i < retries) await new Promise(r => setTimeout(r, backoffMs));
    }
    return false;
  }

  async release() {
    const lua = `
      if redis.call('GET', KEYS[1]) == ARGV[1] then
        return redis.call('DEL', KEYS[1])
      else
        return 0
      end
    `;
    return await redis.eval(lua, 1, this.key, this.token);
  }

  async extend(extendMs) {
    const lua = `
      if redis.call('GET', KEYS[1]) == ARGV[1] then
        return redis.call('PEXPIRE', KEYS[1], ARGV[2])
      else
        return 0
      end
    `;
    return await redis.eval(lua, 1, this.key, extendMs);
  }
}

// Usage
const lock = new RedisLock('lock:order:42', 30_000);
if (await lock.acquire()) {
  try {
    await processOrder(42);
  } finally {
    await lock.release();
  }
}
```

### Redlock (multi-instance, conceptual)

```javascript
const Redlock = require('redlock');
const redlock = new Redlock([redis1, redis2, redis3, redis4, redis5], {
  retryCount: 3,
  retryDelay: 200,
  driftFactor: 0.01,
});

const lock = await redlock.acquire(['lock:order:42'], 30_000);
try {
  await processOrder(42);
} finally {
  await lock.release();
}
```

### Fencing token (Lua-based monotonic counter + lock)

```lua
-- KEYS[1] = lock key, KEYS[2] = global token counter
-- ARGV[1] = client uuid, ARGV[2] = TTL ms

if redis.call('SET', KEYS[1], ARGV[1], 'NX', 'PX', ARGV[2]) then
  local token = redis.call('INCR', KEYS[2])
  return {1, token}
else
  return {0, 0}
end
```

```javascript
// Acquire returns {acquired, token}
const [ok, token] = await redis.eval(luaScript, 2,
  'lock:order:42', 'token:counter',
  uuid, 30_000);

if (ok === 1) {
  // Pass token to downstream operation
  await db.query('UPDATE orders SET ... WHERE id=$1 AND last_token < $2',
    [42, token]);
}
```

## Step-by-step dry run

**Scenario:** Two clients A and B both try to acquire `lock:order:42`. A wins; A's process pauses for 35s due to GC; TTL=30s.

**Without fencing token:**

| T (s) | Client A          | Client B          | Lock | DB        |
|-------|-------------------|-------------------|------|-----------|
| 0     | acquire OK (TTL=30) |                   | A    | balance=100 |
| 1     | start update       |                   | A    | balance=100 |
| 2     | ... GC pause ...   |                   | A    | balance=100 |
| 30    | (still paused)     |                   | (expired) | balance=100 |
| 31    |                    | acquire OK         | B    | balance=100 |
| 32    |                    | update: balance=200 | B    | balance=200 |
| 33    |                    | release             | —    | balance=200 |
| 35    | resume; update: balance=150 |          | —    | balance=150 |

**A's stale update overwrote B's commit.** Mutual exclusion violated.

**With fencing token:**

| T (s) | Client A (token=42)     | Client B (token=43)    | DB                               |
|-------|--------------------------|------------------------|----------------------------------|
| 0     | acquire OK, token=42      |                        | balance=100, last_token=0         |
| 1-30  | ... GC pause ...          |                        | balance=100                       |
| 31    |                           | acquire OK, token=43    | balance=100, last_token=0         |
| 32    |                           | UPDATE WHERE token < 43 | balance=200, last_token=43        |
| 35    | UPDATE WHERE token < 42   |                        | **rejected** (42 < 43)            |
|       |                           |                        | balance=200, last_token=43        |

**A's stale write rejected by the DB.** Correctness preserved despite mutual-exclusion failure.

## How to think aloud in the interview

"Plain `SETNX` is the obvious distributed lock and the obvious foot-gun. Three things break it: no TTL means a crashed holder leaves the lock stuck forever; no owner identification means anyone can release it; and the release path isn't atomic with the ownership check.

The safe single-instance pattern is `SET key uuid NX EX ttl` to acquire — atomic, with a TTL and a unique owner identifier. To release, you run a tiny Lua script that checks the value matches your UUID and deletes only if so. Atomic, owner-safe.

This works for single Redis. The failure mode is Redis failover: if your master dies before async-replicating your lock acquisition, the new master accepts a competing acquisition and now two clients think they hold the lock. Redlock addresses this by acquiring across N independent Redis masters and requiring majority — it doesn't rely on replication.

But there's a deeper problem that Redlock doesn't solve, and this is where Kleppmann's critique comes in. The lock has a wall-clock TTL. If the lock holder's process pauses for longer than the TTL — long GC, VM freeze, swap thrash, container OOM — the lock expires, another client acquires, and now the original holder resumes thinking it still has the lock. Both clients proceed. Mutual exclusion is violated even though the lock was acquired correctly.

The clean fix is fencing tokens. The lock service hands out a monotonically-increasing token with each acquisition. The downstream resource — your DB, storage, queue — checks the token on every operation: if my last-seen token is 43 and someone shows up with token 42, I reject the operation. Now even if the lock holder is split-brained, their stale writes are rejected at the storage layer.

So my recommendation depends on the stakes: for cron-style serialization where 'occasionally two run' is acceptable, single-instance Redis lock is fine. For correctness-critical operations like payments, I use a lock plus a fencing token, with the DB checking the token in the UPDATE's WHERE clause. For absolute safety I'd reach for ZooKeeper or etcd, which give you fencing tokens as a built-in via the zxid/raft index."

## Important takeaways

- **Plain SETNX is unsafe.** Add TTL + UUID + Lua release.
- **Safe single-instance pattern:** `SET k v NX PX ttl` + Lua check-and-delete.
- **Single-instance unsafe under Redis failover** (async replication).
- **Redlock** uses majority across N masters — addresses failover but not GC pauses.
- **Kleppmann's critique:** wall-clock TTL safety is illusory under pauses/partitions.
- **Fencing tokens** are the correct primitive for correctness — storage rejects stale-token operations.
- **Choose by stakes:** Redis lock for serialization, Redis lock + fencing for correctness, ZooKeeper/etcd for absolute safety.
- **Renewing TTL (watchdog)** is hard to get right; prefer short critical sections.

## Variants

1. **Single-instance lock (Redlock-like API, one node)** — most common.
2. **Redlock multi-instance** — N independent Redis masters.
3. **Fencing token lock** — pair lock acquisition with a monotonic counter.
4. **ZooKeeper / etcd lock** — battle-tested, slower, gives fencing for free.
5. **Optimistic locking (CAS)** — no lock; detect concurrent modification on commit.
6. **Lease / lease renewal** — short TTL with explicit renewal; reduces stuck-lock duration.
7. **Reentrant lock** — counter-based; allows same client to re-acquire.

## Revision notes

> **Redis distributed lock — 60 second recap**
> - **Plain SETNX is unsafe** (no TTL, no owner, no atomic release).
> - **Safe pattern:** `SET k uuid NX PX ttl` + Lua check-and-delete release.
> - **Watch out for failover** — async replication can lose the lock state.
> - **Redlock:** majority across N masters; better failover story.
> - **Kleppmann's critique:** wall-clock TTL safety breaks under GC pauses, partitions, clock drift.
> - **Fencing tokens** are the correct primitive — downstream resource rejects stale tokens.
> - **For correctness-critical:** lock + fencing, or ZooKeeper/etcd.
> - **For serialization-only:** single-instance Redis lock is fine.
> - **Trap:** no TTL, no UUID, no Lua release, no fencing, assuming Redlock = absolute safety.
