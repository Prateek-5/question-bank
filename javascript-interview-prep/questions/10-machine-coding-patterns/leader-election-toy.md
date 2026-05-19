# Leader Election — Redis SETNX + lease + fencing token

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [idempotency-wrapper.md](./idempotency-wrapper.md), [cache-stampede-single-flight.md](./cache-stampede-single-flight.md)
>
> **Source:** Distributed-systems primitive; foundational to Zookeeper, etcd, Consul. Practical pattern via Redis SETNX. Razorpay, Atlassian, Stripe.

---

## 1. Problem statement

**Signature**
```ts
class LeaderElector {
  constructor(opts: { redis; key: string; ttlMs?: number; renewMs?: number; instanceId?: string });
  start(): void;
  stop(): Promise<void>;
  isLeader: boolean;
  fencingToken: number;
}
```

**Input / Output examples**

| Setup (3 instances, ttl=30s, renew=10s)              | Behaviour                                              |
|------------------------------------------------------|---------------------------------------------------------|
| I1 calls `start()` first                              | SETNX succeeds → I1 is leader; fencingToken=1          |
| I2, I3 call `start()`                                 | SETNX fails → not leaders                              |
| I1 calls `start()` every 10s                          | Lua-guarded PEXPIRE renews lease                       |
| I1 crashes; 30s elapses                               | key expires; I2 SETNX → leader; fencingToken=2         |
| I1 resumes (GC pause), still thinks leader            | writes with token=1; downstream rejects (token < 2)   |
| `stop()`                                              | Lua-guarded DEL → next leader elected immediately      |

**Constraints**
- TTL > renewMs × 2 (survive missed renewal).
- Lua-guarded renew/delete (only if value === instanceId).
- **Fencing token** — monotonic, server-issued; downstream rejects stale.
- Redis isn't strong consensus — failovers can lose locks.

---

## 2. Plain-English restatement

You have N replicas of your service but want exactly ONE to run a cron job (or hold a leader role). Have all replicas try to atomically claim a Redis key with a TTL. Whoever wins is leader; they renew the lease periodically. The TTL bounds how long a dead leader holds the role. **Fencing tokens** protect against split-brain when a leader pauses (GC, swap) past TTL.

---

## 3. Why this matters in interviews

Background jobs ("send daily summary emails") need exactly-once execution. Full Raft is overkill; Redis-lock pattern is the practical answer. Tests: lease + heartbeat vs single-shot lock, **fencing tokens** (the canonical fix for split-brain), Redis failover trade-offs.

---

## 4. Mental model

```
   3 instances; key=cron_leader; ttl=30s, renew=10s

   t=0   I1: SETNX → OK → isLeader=true, fencingToken=1
         I2: SETNX → FAIL → not leader
         I3: SETNX → FAIL → not leader

   t=10  I1: Lua renew (if value==me then PEXPIRE) → still leader
   t=20  I1: renew → still leader

   t=22  I1: GC pause begins (Node old-gen mark-sweep)

   t=30  I1 still paused; Redis TTL expires → key gone
   t=30  I2: SETNX → OK → isLeader=true, fencingToken=2 (INCR'd!)

   t=33  I1: GC ends; STILL thinks isLeader=true (no notification)
         I1 writes with token=1
         downstream service: current_token=2, request_token=1 → REJECT ✓
         (split-brain averted by fencing)

   t=33  I1: next renew tick → Lua: GET == 'I2' not 'I1' → returns 0
         I1 corrects: isLeader=false
```

**Fencing token** is the non-negotiable piece. SETNX elects; fencing protects.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why must renew be Lua-guarded (not just `PEXPIRE`)?
> 2. What's the split-brain scenario without fencing tokens?
> 3. Why TTL > renewMs × 2?

---

## 6. Brute force — walked through

### Wrong attempt 1: no coordination
10 replicas → 10 daily-summary emails per user. Disaster.

### Wrong attempt 2: SETNX only, no fencing
Leader pauses 35s, TTL expires, new leader elected. Old leader resumes, writes to shared state with same authority → split-brain → data corruption.

### Wrong attempt 3: blind `DEL` on shutdown
Leader A's `stop()` may delete leader B's key (if B took over right before). Lua-guard.

### Wrong attempt 4: very long TTL "for safety"
Longer TTL = longer time without a leader after the leader crashes. Worse availability.

---

## 7. The unlocking insight

> **`SETNX key val NX PX ttl` to atomically claim. Lua-guarded renew (`if GET == me then PEXPIRE`). Lua-guarded shutdown DEL. Monotonic fencing token (`INCR`) issued on acquire; downstream rejects stale tokens. TTL > renewMs × 2 to survive a missed renewal.**

Three properties:

1. **Atomic SETNX + TTL** for election.
2. **Lua-guarded renew/del** so we never act on someone else's lease.
3. **Fencing token** protects shared state from paused-resumed leader.

---

## 8. Solution (annotated)

```js
class LeaderElector {
  constructor({ redis, key, ttlMs = 30_000, renewMs = 10_000, instanceId = randomUUID() }) {
    this.redis = redis;
    this.key = key;
    this.ttlMs = ttlMs;
    this.renewMs = renewMs;
    this.instanceId = instanceId;
    this.isLeader = false;
    this.timer = null;
    this.fencingToken = 0;
  }

  async tryAcquireOrRenew() {
    const ok = await this.redis.set(this.key, this.instanceId, 'NX', 'PX', this.ttlMs);
    if (ok) {                                                          // step 1: fresh acquire
      this.isLeader = true;
      this.fencingToken = await this.redis.incr(`${this.key}:fence`);
      return;
    }
    const current = await this.redis.get(this.key);
    if (current === this.instanceId) {
      const renewed = await this._safeRenew();                          // step 2: Lua renew
      this.isLeader = !!renewed;
    } else {
      this.isLeader = false;
    }
  }

  async _safeRenew() {
    // Lua: only PEXPIRE if value still mine
    const script = `if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('pexpire', KEYS[1], ARGV[2]) else return 0 end`;
    return await this.redis.eval(script, 1, this.key, this.instanceId, this.ttlMs);
  }

  start() {
    const tick = async () => {
      try { await this.tryAcquireOrRenew(); } catch {}
      this.timer = setTimeout(tick, this.renewMs);                      // step 3: heartbeat
    };
    tick();
  }

  async stop() {
    clearTimeout(this.timer);
    const script = `if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end`;
    await this.redis.eval(script, 1, this.key, this.instanceId);        // step 4: Lua-guarded DEL
  }
}
```

**Try it yourself**

```js
const elector = new LeaderElector({
  redis,
  key: 'leader:daily-summary',
  ttlMs: 30_000,
  renewMs: 10_000,
});
elector.start();

// In the job
setInterval(async () => {
  if (!elector.isLeader) return;
  const token = elector.fencingToken;                                   // step 5: pass token
  await sendDailySummaries({ fencingToken: token });                    // downstream enforces
}, 60_000);

process.on('SIGTERM', () => elector.stop());
```

---

## 9. Step-by-step dry run

```
3 instances I1, I2, I3; ttl=30s, renew=10s

t=0   I1 tryAcquire: SETNX OK → isLeader=true, fencingToken=1
      I2 tryAcquire: FAIL → isLeader=false
      I3 tryAcquire: FAIL → isLeader=false
t=10  I1 renew Lua → still leader. token unchanged.
t=20  I1 renew Lua → still leader.
t=22  I1 GC pause begins.
t=30  Redis TTL expires; key gone.
      I2 tryAcquire (next tick at t=30): SETNX OK → leader, fencingToken=2 (INCR'd!)
t=33  I1 GC ends. I1.isLeader STILL true (stale).
      I1 writes shared state with fencingToken=1.
      Downstream: current_token=2, request_token=1 → REJECT.
      Split-brain averted.
t=33  I1 next renew tick: Lua: GET == 'I2' not 'I1' → returns 0.
      I1 corrects isLeader=false.

Without fencing, I1's write at t=33 would have corrupted shared state.
```

---

## 10. Common confusion + traps

1. **No fencing token** — paused-resumed leader writes with stale authority → split-brain.
2. **Blind `DEL` on shutdown** — may delete next leader's key.
3. **Blind `PEXPIRE`** — may extend next leader's lease.
4. **Very long TTL** — longer no-leader gap on crash.
5. **TTL < renewMs × 2** — single missed renewal loses leadership.
6. **Clock skew** — don't trust local clocks for lease; use Redis TTL (server time).
7. **Redis failover loses lock** — async replication can drop the SETNX. Use etcd/Zookeeper for strong consensus.

---

## 11. Senior follow-ups & variants

### Variant 1 — Zookeeper ephemeral z-node
First to create the ephemeral node wins; watchers notified on disconnect. Stronger than Redis; operationally heavier.

### Variant 2 — etcd lease
`Put(key, val, leaseId)`; lease auto-expires unless KeepAlive'd. Strong Raft consensus underneath.

### Variant 3 — Postgres advisory lock
`pg_try_advisory_lock(id)`. Fine for low-throughput; ties leader to a DB connection.

### Variant 4 — Bully algorithm
Peers compare IDs; highest wins. Older systems.

### Variant 5 — Raft / Paxos
Full consensus. Used inside etcd, Consul, TiDB. Strong guarantees; heaviest to deploy.

### Variant 6 — Redlock (Redis-cluster)
Distributed Redis lock across N independent Redis nodes; majority quorum. Famously critiqued by Martin Kleppmann for lacking strong guarantees.

---

## 12. How to think aloud

> "Redis SETNX + TTL + Lua-guarded renew + monotonic fencing token — the 4-piece recipe. Each instance polls; whoever SETNX'd is leader. Renew via Lua: only PEXPIRE if value is still mine. TTL = 2-3× renew so a hiccup doesn't lose leadership. Critical: fencing token issued on acquire (`INCR fence_counter`); every leader-only write carries it; downstream rejects stale tokens. This survives the 'leader GC-paused, key expired, new leader elected, old leader resumes' split-brain. Graceful shutdown: Lua-guarded DEL so the next leader takes over fast. For strong guarantees: etcd/Zookeeper. Trap: no fencing; blind DEL; long TTL hurting availability."

---

## 13. 60-second revision

> - **`SETNX key val NX PX ttl`** to elect.
> - **Lua-guarded `PEXPIRE`** to renew (only if mine).
> - **Lua-guarded `DEL`** on shutdown.
> - **Monotonic fencing token** (`INCR`); downstream rejects stale.
> - **TTL > renewMs × 2** to survive a missed renewal.
> - **Without fencing → split-brain** under GC/swap/network pauses.
> - **Redis isn't strong consensus** — failovers can lose locks. Use etcd/Zookeeper for strict.
> - **Alternatives:** Zookeeper z-node, etcd lease, advisory lock, Raft.
> - **Trap:** no fencing; blind DEL/PEXPIRE; TTL too long; trusting local clocks.

---

**Related:** [idempotency-wrapper.md](./idempotency-wrapper.md) · [cache-stampede-single-flight.md](./cache-stampede-single-flight.md) · [`backend-data-prep/questions/distributed-systems/leader-election-bully-algorithm.md`](../../../backend-data-prep/questions/distributed-systems/leader-election-bully-algorithm.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
