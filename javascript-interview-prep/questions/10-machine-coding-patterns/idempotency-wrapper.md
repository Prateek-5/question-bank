# Idempotency Wrapper

## Source / Origin
- Stripe's "Idempotent requests" API pattern (2015).
- Asked at: Stripe, Razorpay, PayPal, AWS, Booking — anywhere money or state changes hands.
- Concept reference: `backend-data-prep/questions/transactions-concurrency/idempotency-key-design.md`.

## Why this question matters in interviews
Networks lose responses. The client retries. The server now sees the request twice. If the operation creates a payment, you've just double-charged a customer. The idempotency wrapper is how you make "exactly once" out of "at least once" delivery. Every payments interviewer asks this. Senior expectation: you handle in-flight duplicates (not just completed ones), use proper key scoping, and reason about TTL vs storage cost.

## Concepts involved

### Syntax to lock in
```js
// Pseudo-API: store keyed by (tenant, key); state machine: PENDING → SUCCESS|FAILURE
class IdempotencyWrapper {
  constructor(store) { this.store = store; }
  async run(key, fn, { ttlSec = 86400 } = {}) {
    const slot = await this.store.acquire(key, { ttlSec });
    if (slot.status === 'SUCCESS')  return slot.result;            // replay cached result
    if (slot.status === 'FAILURE')  throw slot.error;              // replay cached error (if policy says so)
    if (slot.status === 'PENDING')  return this.store.waitFor(key, slot.deadline);  // dedupe in-flight
    // slot.status === 'NEW' — we own it; run the work
    try {
      const result = await fn();
      await this.store.commitSuccess(key, result);
      return result;
    } catch (err) {
      await this.store.commitFailure(key, err);
      throw err;
    }
  }
}
```

### Edge cases / interview traps
1. **Replay must return the same body, status, and headers.** Not "the new computed value."
2. **In-flight duplicate** — two requests arrive 50ms apart with the same key. The slow one must *wait*, not run independently. Otherwise you double-execute.
3. **Failure replay policy** — some teams cache failures (so the client doesn't keep retrying); some don't (so transient failures can be retried). Pick a policy and document it.
4. **TTL** — Stripe defaults to 24h. Long enough for retries; short enough for storage. Tie to your max retry window.
5. **Key scope** — `(tenant_id, key)` or `(api_user, key)`. Otherwise tenant A's key collides with tenant B.
6. **Request fingerprint** — same key, different body = client bug. Either reject (`409 Conflict`) or hash body and store with slot.
7. **Storage layer** — Redis with `SETNX` + TTL is the typical primary; for strict durability, write to a durable table within the same transaction as the work.
8. **Crash during work** — if the server dies after taking the slot but before commit, the slot stays PENDING. Next retry sees PENDING and... waits forever. Need deadline-based expiry of PENDING.

## Mental Model

Idempotency is a **mailbox slot with a sticky note**. The first sender drops their letter into slot `key`; the postman processes it and pins the response to the slot. Every subsequent sender with the same key gets handed the pinned response — they don't go through the post office again.

```
                              ┌──────────────────────────────┐
   client A: key=42, op=charge ─▶│ slot[42]                     │
                              │   status: PENDING (A owns)   │
                              │   started_at: t=0            │
                              └──────────────────────────────┘
                                              │ A runs
                                              ▼
                              ┌──────────────────────────────┐
                              │ slot[42]                     │
                              │   status: SUCCESS            │
                              │   result: {chargeId: ch_xyz} │
                              └──────────────────────────────┘
                                              ▲
   client A retry (network lost) ─────────────┘  ← reads pinned result, no re-charge
```

State transitions:

```
              acquire (NEW)
   (no slot) ─────────────▶ PENDING
                              │
                              ├──── work succeeds ──▶ SUCCESS (cache, return result)
                              ├──── work fails    ──▶ FAILURE (cache error, throw)
                              └──── deadline expired ──▶ NEW (someone else can pick up)
```

## Why interviewers care

- **Money correctness.** Double-charge incidents are headline-making.
- **At-least-once → exactly-once reasoning.** Senior bar.
- **Failure modes.** Crash mid-work, in-flight dedupe, replay policy.

## Common beginner confusion

- **"Just check before insert."** Race: two requests both read "not exists" → both insert. Need atomic acquire (`SETNX` or unique constraint).
- **"Cache the result in memory."** Single instance only. Production needs a shared store (Redis, DB) so all replicas see the same key state.
- **"TTL forever."** Storage bloat. 24-72h covers retries; that's it.
- **"Idempotency = retry-safety."** Half-true. Idempotency is the *server-side* contract; retry is the *client-side* behavior. You need both.
- **"GET requests don't need keys."** Right — GET is inherently safe. Keys exist for POST/PUT/DELETE.
- **"Two different bodies, same key, return either result."** No — that's a client bug. Reject with `409` or fingerprint and stop.

## Brute force approach

```js
// Check-then-act — race condition
if (!await store.exists(key)) {
  const r = await fn();
  await store.set(key, r);
  return r;
} else {
  return await store.get(key);   // might be PENDING and undefined!
}
```

Two requests can both read "not exists" → both execute → double-charge.

## Optimal approach

Atomic `acquire(key)` returns one of `NEW | PENDING | SUCCESS | FAILURE`. Only `NEW` runs the work; others wait or replay. Use Redis `SET key val NX PX <ttl>` for atomicity; or a unique constraint in the DB if you need durability and atomicity coupled with the work.

## Solution (JavaScript) — Redis-backed sketch

```js
// store interface uses ioredis-style API
class RedisIdempotencyStore {
  constructor(redis) { this.redis = redis; }
  async acquire(key, { ttlSec }) {
    // SET key NX PX → returns 'OK' only if we took the slot
    const ok = await this.redis.set(`idem:${key}`, JSON.stringify({ status: 'PENDING', owner: process.pid }), 'PX', ttlSec * 1000, 'NX');
    if (ok) return { status: 'NEW' };
    const raw = await this.redis.get(`idem:${key}`);
    return raw ? JSON.parse(raw) : { status: 'NEW' };  // race: someone deleted; fall through
  }
  async commitSuccess(key, result) {
    await this.redis.set(`idem:${key}`, JSON.stringify({ status: 'SUCCESS', result }), 'XX');
  }
  async commitFailure(key, err) {
    await this.redis.set(`idem:${key}`, JSON.stringify({ status: 'FAILURE', error: { message: err.message } }), 'XX');
  }
  async waitFor(key, deadlineMs) {
    const end = Date.now() + deadlineMs;
    while (Date.now() < end) {
      const raw = await this.redis.get(`idem:${key}`);
      if (raw) {
        const slot = JSON.parse(raw);
        if (slot.status === 'SUCCESS' || slot.status === 'FAILURE') return slot;
      }
      await new Promise(r => setTimeout(r, 50));
    }
    throw new Error('IdempotencyWaitTimeout');
  }
}

class IdempotencyWrapper {
  constructor(store) { this.store = store; }
  async run(scope, key, fn, { ttlSec = 86400, replayFailure = true } = {}) {
    const scoped = `${scope}:${key}`;
    const slot = await this.store.acquire(scoped, { ttlSec });
    if (slot.status === 'SUCCESS') return slot.result;
    if (slot.status === 'FAILURE') {
      if (replayFailure) { const e = new Error(slot.error.message); e.idempotentReplay = true; throw e; }
      return this.store.runOnRetry?.(scoped, fn);
    }
    if (slot.status === 'PENDING') {
      const finished = await this.store.waitFor(scoped, 30_000);
      if (finished.status === 'SUCCESS') return finished.result;
      const e = new Error(finished.error.message); e.idempotentReplay = true; throw e;
    }
    try {
      const result = await fn();
      await this.store.commitSuccess(scoped, result);
      return result;
    } catch (err) {
      await this.store.commitFailure(scoped, err);
      throw err;
    }
  }
}

// Usage in an HTTP handler
app.post('/charge', async (req, res) => {
  const key = req.headers['idempotency-key'];
  if (!key) return res.status(400).json({ error: 'idempotency-key required' });
  const charge = await wrapper.run(req.tenant.id, key, () => paymentsService.charge(req.body));
  res.json(charge);
});
```

## Step-by-step dry run

Two clients both retry the same charge `key=42, scope=tenant_7`:

```
t=0     client A: POST /charge, key=42
        wrapper.run → store.acquire('tenant_7:42') → Redis SETNX OK → status=NEW
        fn() begins (300ms)

t=50    client B: POST /charge, key=42  (same key, dup request)
        wrapper.run → store.acquire → SETNX fails → GET returns {status: PENDING}
        wrapper waits → polls every 50ms

t=300   client A: fn() returns {chargeId: ch_abc}
        store.commitSuccess → Redis SET XX → {status: SUCCESS, result: ...}
        A receives response

t=310   client B: poll sees {status: SUCCESS, result: {chargeId: ch_abc}}
        wrapper returns same chargeId → B receives identical response

t=400   client A retries (network was lost on response)
        store.acquire → SETNX fails → GET returns {status: SUCCESS, result: ch_abc}
        wrapper returns cached result → no re-charge
```

## How to think aloud in the interview

> "I'll wrap the handler in an idempotency layer. Key is scoped per-tenant. Acquire is atomic — `SETNX` with a TTL — so the first request gets `NEW`, others get `PENDING`/`SUCCESS`/`FAILURE`. PENDING duplicates wait for the in-flight to finish, not execute. On success I commit the result; on failure I commit the error and rethrow with `idempotentReplay: true`. TTL of 24h matches typical retry windows. For payments I'd also add a body fingerprint so a key reuse with different params returns 409."

## Important takeaways

- **Atomic acquire** (`SETNX` or unique constraint). Not check-then-act.
- **Three commit states**: SUCCESS, FAILURE, (deadline) NEW.
- **In-flight dedupe** is the trickiest case — duplicate while the original is running must wait.
- **Replay the same body, headers, status**, not a re-computed answer.
- **Key scoped per-tenant.** Otherwise cross-tenant collisions.
- **Body fingerprint** to detect key reuse with different inputs.

## Variants

- **DB-backed wrapper** — use a unique constraint on `(scope, key)` in a `idempotency_records` table; insert in the same tx as the work for strong durability.
- **HTTP layer wrapper** — a middleware that hashes the response and stores it; replays headers + body bit-for-bit.
- **Outbox pattern integration** — store key + outbox event in the same tx so retries dedupe the publish too.
- **Async (eventual) idempotency** — for queue consumers; key is the message ID; processed-set in Redis with TTL.

## Revision notes

```
IdempotencyWrapper:
  run(scope, key, fn, ttl):
    slot = store.acquire(scope:key) {NX SET with TTL}
    SUCCESS → return cached result
    FAILURE → throw cached error (policy)
    PENDING → wait until SUCCESS/FAILURE (in-flight dedupe)
    NEW     → run fn; on done commit SUCCESS/FAILURE
  
  atomic acquire (SETNX)
  per-tenant scope
  TTL = max retry window (24h Stripe default)
  fingerprint body to catch key reuse with different params
  pair with retry+backoff on client; pair with txn for DB-level guarantee
  crash mid-work → PENDING timeout → next caller picks up
```
