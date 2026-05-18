# Leader Election — Toy Implementation (Redis-Lock Style)

## Source / Origin
- Distributed systems primitive; foundational to Zookeeper / etcd / Consul.
- Practical pattern: "Run this job on exactly one instance" via Redis SETNX + heartbeat.
- Asked at: Razorpay, Atlassian, Stripe.
- Concept reference: `backend-data-prep/questions/distributed-systems/leader-election-bully-algorithm.md`, `leader-election-raft-intuition.md`.

## Why this question matters in interviews
Background jobs ("send daily summary emails") often need to run on *exactly one* instance — not zero, not many. Leader election is how. The full algorithm (Raft, Paxos) is overkill for most apps; a Redis-lock-based "whoever grabs the key is leader" pattern is what you actually build. Senior bar: you reason about (1) lease + heartbeat vs single-shot lock, (2) fencing tokens, (3) split-brain when the leader's clock pauses (GC, swap, network blip).

## Concepts involved

### Syntax to lock in
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
    this.fencingToken = 0;          // monotonic, server-issued
  }

  async tryAcquireOrRenew() {
    const ok = await this.redis.set(this.key, this.instanceId, 'NX', 'PX', this.ttlMs);
    if (ok) { this.isLeader = true; this.fencingToken = await this.redis.incr(`${this.key}:fence`); return; }
    // not acquired; check if we already are the leader (renew)
    const current = await this.redis.get(this.key);
    if (current === this.instanceId) {
      const renewed = await this._safeRenew();
      this.isLeader = !!renewed;
    } else {
      this.isLeader = false;
    }
  }

  async _safeRenew() {
    // Lua: if value == myId then PEXPIRE else 0
    const script = `if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('pexpire', KEYS[1], ARGV[2]) else return 0 end`;
    return await this.redis.eval(script, 1, this.key, this.instanceId, this.ttlMs);
  }

  start() {
    const tick = async () => {
      await this.tryAcquireOrRenew();
      this.timer = setTimeout(tick, this.renewMs);
    };
    tick();
  }

  async stop() {
    clearTimeout(this.timer);
    const script = `if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end`;
    await this.redis.eval(script, 1, this.key, this.instanceId);
  }
}
```

### Edge cases / interview traps
1. **Don't `DEL` blindly.** "If value == myId then DEL" via Lua — otherwise you'd delete the *next* leader's lock.
2. **Don't `PEXPIRE` blindly.** Same conditional Lua.
3. **TTL > renewMs by 2-3x.** Renew at 10s, TTL 30s: gives you two missed renewals before losing leadership.
4. **GC/swap/network pause.** If the leader pauses for `> TTL`, Redis times out the key; another instance becomes leader; the original leader, on resuming, *still thinks it's leader* and writes to shared state → split-brain. **Fencing token** mitigates: every write to shared state must include the token; downstream rejects stale tokens.
5. **Clock skew.** Don't trust local clocks for lease decisions; trust Redis TTL (server time).
6. **Redis itself failing over.** A Redis primary failover can lose the SETNX (asynchronous replication). Redlock tries to fix this; Martin Kleppmann famously criticizes it.
7. **Election storms.** Many instances trying NX every 100ms = thrash. Stagger with jitter.
8. **Graceful shutdown** — `stop()` deletes the key (Lua-guarded) so the next leader takes over within milliseconds, not after TTL.

## Mental Model

A **microphone with a 30-second timer**:

```
   instances:  I1, I2, I3
   key: cron_leader
   ttl: 30s, renew: 10s

   t=0   I1.tryAcquire → SETNX → OK → I1 is leader → fencingToken=1
                                          ▲
   t=0   I2.tryAcquire → SETNX → FAIL → I2 NOT leader
   t=0   I3.tryAcquire → SETNX → FAIL → I3 NOT leader

   t=10  I1.renew (Lua-guarded PEXPIRE) → still leader; fencingToken stays 1
         I2/I3.tryAcquire still FAIL

   t=30  I1 crashed at t=20; TTL elapsed → key gone
         I2.tryAcquire → SETNX → OK → I2 is leader → fencingToken=2 (incremented!)

   t=35  I1 recovers; thinks it's leader → tries to write with token 1
         downstream sees token 1 < currentToken 2 → REJECT write (split-brain averted)
```

## Why interviewers care

- **Distributed systems judgment** — leader election is on every senior backend rubric.
- **Failure-mode literacy** — pauses, network blips, clock skew, replication lag.
- **Fencing token concept** — the canonical fix for the GC-pause split-brain story.

## Common beginner confusion

- **"SETNX is enough."** It's enough to *elect* but not to *protect*. Without fencing, a paused-then-resumed leader corrupts state.
- **"Just use a longer TTL."** Longer TTL = longer time without a leader after the leader crashes. Worse availability.
- **"DEL on shutdown is fine."** Only if Lua-guarded — otherwise you delete the new leader's key.
- **"Redis is the truth."** Redis is *one* truth, until it isn't (failover). For strong guarantees use etcd/Zookeeper/consul.

## Brute force approach

```js
// Single instance assumption — breaks under HPA, blue/green, multi-AZ
setInterval(() => runDailySummary(), 24 * 60 * 60 * 1000);
```

10 instances → 10 emails per user per day.

## Optimal approach

Each instance periodically tries `SETNX` with a TTL; on success, becomes leader and renews via Lua-guarded `PEXPIRE`. All writes carry a fencing token so a paused-resumed leader's writes are rejected downstream.

## Solution (JavaScript)

See "Syntax to lock in" above. Usage:

```js
const elector = new LeaderElector({
  redis,
  key: 'leader:daily-summary',
  ttlMs: 30_000,
  renewMs: 10_000,
});
elector.start();

// in your job
setInterval(async () => {
  if (!elector.isLeader) return;
  const token = elector.fencingToken;
  await sendDailySummaries({ fencingToken: token });
}, 60_000);

process.on('SIGTERM', () => elector.stop());
```

## Step-by-step dry run

3 instances I1, I2, I3; `ttl=30s, renew=10s`:

```
t=0   I1 tryAcquire → SETNX OK → isLeader=true, token=1
      I2 tryAcquire → FAIL → isLeader=false
      I3 tryAcquire → FAIL → isLeader=false
t=10  I1 renew Lua → still leader → token=1
t=20  I1 renew Lua → still leader
t=22  I1 GC pause begins
t=30  I1 still paused; Redis key TTL expires; key gone
t=30  I2 tryAcquire (next tick) → SETNX OK → isLeader=true, token=2
t=33  I1 GC pause ends; I1 tries to write with token=1
      downstream service: current_fencing_token=2, request_token=1 → REJECT
t=33  I1 renew Lua → GET == 'I2', not 'I1' → returns 0; isLeader=false
      I1 corrects itself
```

## How to think aloud in the interview

> "Redis SETNX with TTL + Lua-guarded renew. Each instance polls; whoever gets the key is leader. Renew with Lua so you only PEXPIRE if value == myId. TTL is 2-3x renew interval so a hiccup doesn't lose leadership. Critical: fencing token. Issue a monotonic token at acquire; every leader-only write carries it; downstream rejects stale tokens. This survives the 'leader paused for GC, key expired, new leader elected, old leader resumes' scenario. For stronger guarantees I'd use etcd or Zookeeper."

## Important takeaways

- **SETNX + TTL + Lua-guarded renew + fencing token.** The 4-piece recipe.
- **TTL > renewInterval × 2.** Survive a missed renewal.
- **Fencing token** is non-optional for protecting shared state.
- **Graceful shutdown** Lua-guards a DEL so the next leader takes over fast.
- **Redis isn't strong.** Failovers can lose locks; use etcd/Zookeeper for strict semantics.

## Variants

- **Zookeeper ephemeral z-node** — first to create the ephemeral node wins; watchers are notified on disconnect. Stronger than Redis; more operationally heavy.
- **etcd lease** — `Put(key, val, leaseId)`; lease auto-expires unless KeepAlive'd. Strong consensus (Raft) underneath.
- **DB-row lock** — `SELECT FOR UPDATE` of a `leaders` table row. Fine for low-throughput; Postgres advisory locks are nicer.
- **Bully algorithm** — peers compare instance IDs; highest wins. Used in older systems, less common today.
- **Raft** — full consensus, leader is elected by majority vote in a term. Used inside etcd, Consul, TiDB.

## Revision notes

```
LeaderElector (Redis flavor):
  tryAcquireOrRenew(): SETNX with TTL (or Lua-guarded PEXPIRE)
  loop every renewMs
  ttl > renewMs × 2 (survive a missed tick)
  Lua-guarded DEL on shutdown
  fencing token: INCR on acquire; pass to downstream; reject stale
  
  4-piece recipe: SETNX + TTL + Lua renew + fencing
  alternatives: etcd lease, Zookeeper ephemeral, advisory lock, Raft
  GC-pause split-brain: fencing token fixes it
```
