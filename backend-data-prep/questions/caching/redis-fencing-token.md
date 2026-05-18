# Redis Fencing Tokens — Monotonic Tokens for Safe Critical Sections

## Source / Origin
- Kleppmann's "How to do distributed locking" (2016) — introduced fencing tokens as the correct primitive missing from Redlock.
- ZooKeeper's `zxid` and etcd's raft index are *de-facto* fencing tokens.
- Companion: `redis-redlock-distributed-lock.md` (this directory).
- Interview prompt: "How do you protect against a lock holder whose process paused longer than the lock's TTL?"

## Why this question matters in interviews
Fencing tokens are the unambiguous senior-level answer to "how do you make a distributed lock actually safe?" Candidates who only know about Redlock have read the docs. Candidates who reach for fencing tokens have read the critique. Interviewers use this question to (a) test whether you understand that lock acquisition is not the same as mutual exclusion at the resource, and (b) test whether you can design a *resource-side* check that closes the safety gap.

## Concepts involved

### Syntax to lock in

The pattern in three lines:
```
# Lock service hands out a monotonic token alongside acquisition
acquired, token = lock.acquire(key)

# Downstream resource accepts only operations with token > last_seen_token
UPDATE resource
   SET value = $value, last_token = $token
 WHERE id = $id AND last_token < $token
```

Redis-side: combine SET NX with an atomic INCR:
```lua
-- KEYS[1] = lock key, KEYS[2] = token counter
-- ARGV[1] = owner uuid, ARGV[2] = TTL in ms
if redis.call('SET', KEYS[1], ARGV[1], 'NX', 'PX', ARGV[2]) then
  return {1, redis.call('INCR', KEYS[2])}
else
  return {0, 0}
end
```

### Edge cases / interview traps
1. **Token counter must be globally monotonic** — a single shared INCR key, *not* per-lock counters. Otherwise tokens across different locks aren't comparable.
2. **Resource must check the token** — the lock service handing out tokens does nothing on its own. The downstream resource (DB, blob store, queue) must reject lower tokens.
3. **Per-resource last-seen tokens** — every resource needs to remember the highest token it has seen. Usually a `last_token` column or a Redis hash field on the resource.
4. **Idempotency via tokens** — if a write retries with the same token, the resource can detect the duplicate (token == last_seen) and either reject or accept-idempotently.
5. **Wrap-around** — 64-bit monotonic counters effectively never wrap. 32-bit can wrap in long-running systems; use 64.
6. **Token persistence after Redis restart** — if the INCR counter is in non-persistent Redis, restart resets tokens. Old high tokens block all writes. Use AOF persistence with `everysec` minimum.
7. **Skewed tokens across multiple lock services** — if you have N independent lock services each with their own counter, tokens aren't globally monotonic. Solutions: single source of truth, or per-resource scoped tokens.
8. **Read tokens for read-side fencing** — also useful for read-modify-write loops: read with token T, write with token T+1 conditional on `last_token == T`.

## Mental Model

### Without fencing — the GC pause race

```
Time   Client A                      Client B               Lock        Resource (DB)
─────  ──────────────────────────    ───────────────────    ─────       ──────────────
0      acquire OK (TTL=30s)                                  A           value=100
1      start critical section
2      ... GC pause 35s ...
30                                                           expired      value=100
31                                    acquire OK              B           value=100
32                                    update value=200        B           value=200
33                                    release                 —           value=200
35     resume, update value=150                                            value=150
                                                                          ^ A's stale write won.
```

### With fencing — the GC pause is benign

```
Time   Client A (token=42)         Client B (token=43)     Resource (DB, last_token=0)
─────  ──────────────────────      ─────────────────────   ───────────────────────────
0      acquire OK, token=42
1      start critical section
2      ... GC pause 35s ...
30                                                          (no operations yet)
31                                  acquire OK, token=43
32                                  UPDATE … WHERE last_token < 43
                                                            value=200, last_token=43
33                                  release
35     UPDATE … WHERE last_token < 42
                                                            REJECTED (last_token=43)
                                                            ─ A's stale write rejected.
```

The token is the only difference. The lock acquisition mechanism is unchanged.

### Token lifecycle

```
                ┌─────────────┐
                │ Token Counter│   (monotonic, persistent)
                │   GLOBAL     │
                └──────┬───────┘
                       │ INCR on each lock acquisition
                       ▼
         ┌──────────────────────────┐
         │ Lock Acquisition Service │
         └────────────┬─────────────┘
                       │ {token=42}
                       ▼
                  Client A
                       │ operation_with_token(42)
                       ▼
            ┌─────────────────────┐
            │ Resource (DB / KV)   │
            │ checks token ≥ last │
            │ rejects stale tokens │
            └─────────────────────┘
```

## Why interviewers care
- It's the cleanest demonstration that **mutual exclusion at the lock is not mutual exclusion at the resource**.
- Tests whether you understand that **the resource is the ultimate guard**, not the lock service.
- Distinguishes between candidates who've read the docs vs. read the critique.
- Maps directly to real production tech: ZooKeeper zxid, etcd raft index, MongoDB's optimistic locking via version numbers.

## Common beginner confusion
- **"Fencing tokens replace the lock."** No — you still need a lock to serialize lock acquisitions. The token *strengthens* the lock by closing the GC-pause gap.
- **"Fencing tokens work without resource cooperation."** No — the resource must check the token. If it doesn't, the token is decorative.
- **"Per-lock token counters are fine."** Only if you never need to compare tokens across locks. Globally monotonic is safer.
- **"Tokens are like UUIDs."** UUIDs are unique but not ordered. Tokens must be *monotonically increasing* to be comparable.
- **"Lock TTL doesn't matter if I have fencing."** TTL still matters — it lets the system reclaim crashed-holder locks promptly. Without TTL, stuck locks block new acquisitions.

## Brute force approach
**"Just use the lock; trust no GC pauses."** Works until production GC pauses (Java with old GCs can pause 30s; container OOM-kills can stall a process for minutes).

**"Use a shorter TTL."** Reduces the window but doesn't eliminate it. If TTL=1s, you've made the race rare but not impossible, and now you need watchdog renewals.

**"Lock the database directly with SELECT FOR UPDATE."** Works for single-DB scenarios. Bad for cross-resource operations (e.g., updating Redis cache + DB row + emitting an event atomically — they don't share a transaction).

## Optimal approach

### Implementation checklist
- **Single global monotonic counter** for token generation (INCR on a dedicated key).
- **Token counter must be persistent** — AOF `everysec` or stronger.
- **Resource stores `last_token` per protected entity** (column, Redis hash field, file metadata).
- **Every write to the resource checks `token > last_token`** in the same atomic step.
- **Lock acquisition returns `{acquired, token}` together** — atomic acquire+token.

### Storage-side check patterns
- **SQL:** `UPDATE table SET ..., last_token=$t WHERE id=$id AND last_token < $t` — uses the row's WHERE clause to reject stale tokens.
- **Redis:** Lua script `if last_token < new_token then SET ... return ok else return reject`.
- **Object stores (S3):** Use object versioning + conditional headers; less precise but viable for blob writes.
- **Message queues:** Include token in message metadata; consumer checks before acting.

### When to use
- Payment / billing operations.
- Critical state machines (order → fulfillment → ship).
- Any operation where "both holders run" causes corruption (not just inefficiency).

### When *not* to use
- Idempotent operations (retries are safe; ordering doesn't matter).
- Operations where last-write-wins is acceptable.
- Throw-away coordination (cron-job leader election).

## Solution

### Lock + token acquisition (Node.js + ioredis)

```javascript
const Redis = require('ioredis');
const crypto = require('crypto');
const redis = new Redis();

const LOCK_ACQUIRE_LUA = `
  if redis.call('SET', KEYS[1], ARGV[1], 'NX', 'PX', ARGV[2]) then
    return {1, redis.call('INCR', KEYS[2])}
  else
    return {0, 0}
  end
`;

const LOCK_RELEASE_LUA = `
  if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
  else
    return 0
  end
`;

async function acquireWithToken(resource, ttlMs = 30_000) {
  const uuid = crypto.randomUUID();
  const [ok, token] = await redis.eval(
    LOCK_ACQUIRE_LUA,
    2,
    `lock:${resource}`, 'fencing:counter',
    uuid, ttlMs.toString(),
  );
  return ok === 1 ? { acquired: true, token, uuid } : { acquired: false };
}

async function release(resource, uuid) {
  return await redis.eval(LOCK_RELEASE_LUA, 1, `lock:${resource}`, uuid);
}
```

### Resource-side check (Postgres)

```sql
-- Schema
CREATE TABLE orders (
  id BIGINT PRIMARY KEY,
  status TEXT,
  last_token BIGINT NOT NULL DEFAULT 0
);

-- Token-checked update
UPDATE orders
   SET status = $1, last_token = $2
 WHERE id = $3
   AND last_token < $2
RETURNING id;
-- 0 rows returned → token was stale, write rejected
```

### Resource-side check (Redis hash)

```lua
-- KEYS[1] = resource hash key, ARGV[1] = field, ARGV[2] = new_value, ARGV[3] = token
local last = tonumber(redis.call('HGET', KEYS[1], 'last_token') or '0')
local incoming = tonumber(ARGV[3])
if incoming > last then
  redis.call('HSET', KEYS[1], ARGV[1], ARGV[2], 'last_token', incoming)
  return 1
else
  return 0  -- rejected
end
```

### Putting it together

```javascript
async function processOrderSafely(orderId) {
  const { acquired, token, uuid } = await acquireWithToken(`order:${orderId}`);
  if (!acquired) throw new Error('lock not acquired');

  try {
    // Read current state
    const order = await db.query('SELECT * FROM orders WHERE id=$1', [orderId]);
    const newStatus = computeNewStatus(order);

    // Write with token guard
    const result = await db.query(
      `UPDATE orders SET status=$1, last_token=$2
        WHERE id=$3 AND last_token < $2
        RETURNING id`,
      [newStatus, token, orderId],
    );

    if (result.rowCount === 0) {
      // Our token was stale — another holder ran with a higher token
      throw new Error('stale fencing token; aborting');
    }
  } finally {
    await release(`order:${orderId}`, uuid);
  }
}
```

## Step-by-step dry run

**Scenario:** Client A gets token=42, pauses for GC. Client B gets token=43, completes. Client A resumes.

| T (s) | Counter | Lock state    | Client A             | Client B              | DB row              |
|-------|---------|--------------|----------------------|------------------------|----------------------|
| 0     | 41      | empty         | acquire → ok, t=42  |                        | last_token=0         |
| 1     | 42      | A (TTL=30)    | reads order=Pending |                        | last_token=0         |
| 2     | 42      | A             | GC pause begins      |                        | last_token=0         |
| 30    | 42      | expired       |                      |                        | last_token=0         |
| 31    | 43      | B (TTL=30)    |                      | acquire → ok, t=43    | last_token=0         |
| 32    | 43      | B             |                      | UPDATE WHERE lt<43    | last_token=43, status=Confirmed |
| 33    | 43      | empty         |                      | release                | last_token=43         |
| 35    | 43      | empty         | resumes              |                        | last_token=43         |
| 36    | 43      | empty         | UPDATE WHERE lt<42  |                        | **0 rows updated**   |
| 36    | 43      | empty         | throws 'stale token'|                        | last_token=43         |

**A's stale write is rejected at the DB.** The DB row remains correct (status=Confirmed). A's exception triggers retry or escalation upstream.

## How to think aloud in the interview

"Fencing tokens are the answer to the problem Redlock can't solve: what if my process pauses longer than the lock's TTL? Even with a perfect lock acquisition, the holder can resume after the lock has expired and another client has taken it. Both clients now believe they hold the lock and both proceed to write. Mutual exclusion is violated at the resource even though it was enforced at the lock.

The fix is to attach a monotonically increasing token to every lock acquisition, and have the downstream resource — the database, the storage system — refuse any operation whose token is lower than what it has already seen. Now the lock holder's stale write is rejected on arrival; the resource is the final arbiter.

Concretely: the lock service uses a single shared INCR counter. Each acquisition gets a fresh token. The application carries the token through every write. The DB has a `last_token` column per row, and every UPDATE includes `WHERE last_token < $token, last_token = $token` in the same statement. A stale write updates zero rows and the app can detect and abort.

Critical details. The counter has to be globally monotonic — one counter for the whole system, not per-lock — so tokens are comparable. The counter has to be persistent — AOF on Redis, ideally — because if it resets after a restart, old high tokens block all new writes. And the resource has to actively cooperate; without the resource-side check, the token is just decoration.

This is why ZooKeeper and etcd are so widely used in payments: ZooKeeper's `zxid` is a built-in fencing token. You get it for free with any lock. Redis can do the same with a couple of lines of Lua.

If they push me on when not to bother: idempotent operations don't need fencing. If A's stale write and B's correct write produce the same outcome — say both are SET-the-same-value — there's no corruption. Use fencing where order matters and where 'both holders ran' is a correctness bug, not just an efficiency one."

## Important takeaways

- **Lock acquisition ≠ resource mutual exclusion.** Fencing closes the gap.
- **Monotonic token per acquisition; resource rejects stale tokens.**
- **Token counter must be global and persistent.**
- **Resource must cooperate** — check the token in the same atomic write.
- **Use SQL WHERE clause** (`AND last_token < $t`) for atomicity in DB writes.
- **ZooKeeper and etcd provide tokens (zxid, raft index) natively.**
- **Pair with a lock** — fencing alone doesn't serialize; it just prevents stale writes.
- **Skip fencing for idempotent operations.**

## Variants

1. **Per-resource scoped tokens** — counter per resource type; works if you never compare across types.
2. **ZooKeeper / etcd as the token source** — battle-tested, atomic.
3. **Timestamp-as-token** — works if clocks are well-synced (NTP, TrueTime); risky otherwise.
4. **Optimistic concurrency control (OCC)** — version column per row; functionally equivalent for many use cases without the lock.
5. **Token in HTTP If-Match header** — for HTTP API resources; aligns with ETag-based concurrency control.
6. **Fencing for message queues** — consumer checks token in message metadata; rejects out-of-order processing.

## Revision notes

> **fencing tokens — 60 second recap**
> - **Problem:** lock holder pauses past TTL; another holder acquires; both write. Mutual exclusion violated at resource.
> - **Fix:** lock service hands out a globally monotonic token on every acquisition.
> - **Resource checks token > last_seen on every write.** Stale tokens rejected.
> - **Implement via SQL:** `UPDATE ... WHERE id=$id AND last_token < $t, SET last_token=$t`.
> - **Token counter must be globally monotonic + persistent.**
> - **Use a lock for serialization; use a token for safety.** Both layers.
> - **ZooKeeper zxid and etcd raft index** are built-in fencing tokens.
> - **Skip fencing only for idempotent operations.**
> - **Trap:** per-lock counters; non-persistent counter; resource not checking the token.
