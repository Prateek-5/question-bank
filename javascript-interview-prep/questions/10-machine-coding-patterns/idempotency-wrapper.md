# Idempotency Wrapper — exactly-once from at-least-once retries

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [retry-with-jitter-and-budget.md](./retry-with-jitter-and-budget.md), [cache-stampede-single-flight.md](./cache-stampede-single-flight.md)
>
> **Source:** Stripe's "Idempotent requests" API (2015). Stripe, Razorpay, PayPal, AWS, Booking.

---

## 1. Problem statement

**Signature**
```ts
class IdempotencyWrapper {
  constructor(store: IdempotencyStore);
  run<T>(scope: string, key: string, fn: () => Promise<T>, opts?: { ttlSec?: number; replayFailure?: boolean }): Promise<T>;
}

interface IdempotencyStore {
  acquire(key: string, opts: { ttlSec: number }): Promise<{ status: 'NEW'|'PENDING'|'SUCCESS'|'FAILURE', result?, error? }>;
  commitSuccess(key, result): Promise<void>;
  commitFailure(key, err): Promise<void>;
  waitFor(key, timeoutMs): Promise<{ status, result?, error? }>;
}
```

**Input / Output examples**

| Setup                                              | Behaviour                                              |
|----------------------------------------------------|---------------------------------------------------------|
| First call with key=42                             | acquire returns NEW; run fn; commit SUCCESS            |
| Retry (network lost response)                      | acquire returns SUCCESS; return cached result; no re-run |
| Two clients submit same key concurrently           | first NEW runs; second PENDING waits; both get same result |
| `fn` throws                                        | commit FAILURE; rethrow with `idempotentReplay: true`  |
| Server crashes mid-`fn`                            | slot stays PENDING; deadline expiry → next retry picks up |

**Constraints**
- Atomic acquire (`SETNX` in Redis or unique constraint in DB).
- Key scoped per-tenant.
- TTL covers retry window (Stripe default 24h).
- In-flight dedupe: second concurrent caller MUST wait, not re-execute.
- Replay returns same body/status, not recomputed answer.

---

## 2. Plain-English restatement

Networks lose responses; clients retry. Server now sees the same request twice — if it creates a payment, you double-charge. The idempotency wrapper makes "exactly once" out of "at least once" delivery: the first request takes a slot atomically, runs the work, stashes the result; subsequent requests with the same key replay the stashed result.

---

## 3. Why this matters in interviews

Money correctness. Every payments interviewer asks this. Senior expectation: handle in-flight duplicates (not just completed ones), proper key scoping (per-tenant), reason about TTL vs storage cost, crash-recovery via PENDING expiry.

---

## 4. Mental model

```
   Mailbox slot with a sticky note:

   client A: key=42 ─▶ slot[42]: PENDING (A owns), started_at=T
                                                        │ A runs work
                                                        ▼
                       slot[42]: SUCCESS, result={charge: ch_xyz}
                                                        ▲
   client A retry  ───────────────────────────────────  │  reads pinned result;
   (network lost response)                              │  no re-charge.

   State machine:
                       acquire (NEW)
        (no slot) ───────────────────▶ PENDING
                                          │
                                          ├── work succeeds → SUCCESS (cache, return)
                                          ├── work fails    → FAILURE (cache error, throw)
                                          └── deadline expired → NEW (next caller picks up)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is "check then insert" (`if (!exists) insert`) wrong?
> 2. If two requests arrive 50ms apart with the same key, what does each see?
> 3. What happens if the server crashes mid-`fn`?

---

## 6. Brute force — walked through

### Wrong attempt 1: check-then-act
```js
if (!await store.exists(key)) {
  const r = await fn();
  await store.set(key, r);
}
```
Race: both reads see "not exists" → both execute → double-charge. Need ATOMIC acquire.

### Wrong attempt 2: in-memory cache
Single instance only. Production needs shared store (Redis, DB) so replicas agree.

### Wrong attempt 3: ignore in-flight duplicates
Second caller starts a new `fn` while first is still running → double-execute.

---

## 7. The unlocking insight

> **Atomic `acquire(key)` returns one of NEW/PENDING/SUCCESS/FAILURE. NEW runs; PENDING waits; SUCCESS/FAILURE replays. Use Redis `SETNX` + TTL for atomicity, or DB unique constraint coupled with the work transaction.**

Three properties:

1. **Atomic acquire** — `SETNX` or unique constraint, no check-then-act.
2. **Per-tenant scope** — `(tenant_id, key)` avoids collisions.
3. **PENDING wait** — in-flight dedupe; second caller doesn't re-execute.

---

## 8. Solution (annotated)

```js
class RedisIdempotencyStore {
  constructor(redis) { this.redis = redis; }
  async acquire(key, { ttlSec }) {                                   // step 1: atomic
    const ok = await this.redis.set(
      `idem:${key}`,
      JSON.stringify({ status: 'PENDING', owner: process.pid, startedAt: Date.now() }),
      'PX', ttlSec * 1000, 'NX',
    );
    if (ok) return { status: 'NEW' };
    const raw = await this.redis.get(`idem:${key}`);
    return raw ? JSON.parse(raw) : { status: 'NEW' };
  }
  async commitSuccess(key, result) {
    await this.redis.set(`idem:${key}`, JSON.stringify({ status: 'SUCCESS', result }), 'XX');
  }
  async commitFailure(key, err) {
    await this.redis.set(`idem:${key}`, JSON.stringify({ status: 'FAILURE', error: { message: err.message } }), 'XX');
  }
  async waitFor(key, timeoutMs) {                                    // step 2: poll PENDING
    const end = Date.now() + timeoutMs;
    while (Date.now() < end) {
      const raw = await this.redis.get(`idem:${key}`);
      if (raw) {
        const slot = JSON.parse(raw);
        if (slot.status === 'SUCCESS' || slot.status === 'FAILURE') return slot;
      }
      await new Promise((r) => setTimeout(r, 50));
    }
    throw new Error('IdempotencyWaitTimeout');
  }
}

class IdempotencyWrapper {
  constructor(store) { this.store = store; }
  async run(scope, key, fn, { ttlSec = 86400, replayFailure = true } = {}) {
    const scoped = `${scope}:${key}`;                                // step 3: tenant scoping
    const slot = await this.store.acquire(scoped, { ttlSec });

    if (slot.status === 'SUCCESS') return slot.result;
    if (slot.status === 'FAILURE') {
      if (replayFailure) {
        const e = new Error(slot.error.message); e.idempotentReplay = true; throw e;
      }
      // policy: rerun (not implemented here)
    }
    if (slot.status === 'PENDING') {                                  // step 4: in-flight wait
      const finished = await this.store.waitFor(scoped, 30_000);
      if (finished.status === 'SUCCESS') return finished.result;
      const e = new Error(finished.error.message); e.idempotentReplay = true; throw e;
    }

    // status === 'NEW' — we own it
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
```

**Try it yourself**

```js
app.post('/charge', async (req, res) => {
  const key = req.headers['idempotency-key'];
  if (!key) return res.status(400).json({ error: 'idempotency-key required' });
  const charge = await wrapper.run(req.tenant.id, key, () => paymentsService.charge(req.body));
  res.json(charge);
});
```

---

## 9. Step-by-step dry run

```
Two clients retry same key=42, scope=tenant_7:

t=0    A: POST → wrapper.run('tenant_7', 42, chargeFn)
       store.acquire('tenant_7:42'): SETNX OK → status=NEW.
       fn() starts (300ms).

t=50   B: POST → wrapper.run('tenant_7', 42, chargeFn)
       store.acquire: SETNX fails (key exists). GET → {status:PENDING}.
       wrapper.waitFor: poll every 50ms.

t=300  A: fn() returns {chargeId: ch_abc}.
       store.commitSuccess → Redis SET XX → {status:SUCCESS, result:...}.
       A receives ch_abc.

t=310  B: poll sees {status:SUCCESS, result:ch_abc}.
       wrapper returns ch_abc. Same result; no second charge.

t=400  A retries (network lost original response):
       store.acquire: SETNX fails. GET → {status:SUCCESS, result:ch_abc}.
       wrapper returns cached ch_abc. No re-charge.

Crash mid-fn:
  t=0  A: PENDING; server dies at t=50.
  t=200 B comes in: GET → PENDING. waitFor times out at t=30s.
       After PX TTL expires (or PENDING deadline elapses), next caller's SETNX OK → NEW.
```

---

## 10. Common confusion + traps

1. **Check-then-act** — race; both reads see miss; double-execute.
2. **In-memory cache** — single instance only; replicas disagree.
3. **Ignore in-flight duplicates** — second concurrent caller re-executes.
4. **Same body, different params, same key** — client bug; reject 409 or fingerprint body.
5. **TTL forever** — storage bloat. 24-72h covers retries.
6. **Cross-tenant key collision** — `'42'` in tenant A vs B collide. Scope per tenant.
7. **GET requests** — inherently safe; keys are for POST/PUT/DELETE.

---

## 11. Senior follow-ups & variants

### Variant 1 — DB-backed wrapper
Unique constraint on `(scope, key)` in `idempotency_records` table; insert in same tx as the work. Strong durability.

### Variant 2 — HTTP middleware
Hash full response (status + body + relevant headers); replay bit-for-bit.

### Variant 3 — Body fingerprint
Hash request body; store with slot. Same key + different body → 409 Conflict (client bug).

### Variant 4 — Outbox pattern
Store key + outbox event in same tx so retries dedupe the publish too.

### Variant 5 — Async (queue) idempotency
For queue consumers: key = message ID; processed-set in Redis with TTL.

### Variant 6 — Strict mode (no failure replay)
Cache only successes; failures don't replay so transient errors can re-run.

---

## 12. How to think aloud

> "Atomic acquire via `SETNX` + TTL — NEW, PENDING, SUCCESS, or FAILURE. NEW runs the work; PENDING waits for the in-flight to finish; SUCCESS replays cached result; FAILURE replays cached error (policy-dependent). Per-tenant scoping. TTL 24h matches retry window. Body fingerprint for client-bug detection. Crash mid-work: PENDING expires via TTL, next retry picks up. DB-backed variant uses unique constraint coupled with the work in the same transaction for strong durability. Trap: check-then-act race; in-memory cache; ignoring in-flight duplicates; cross-tenant collisions."

---

## 13. 60-second revision

> - **Atomic acquire** (`SETNX` or DB unique constraint).
> - **Four states:** NEW (run), PENDING (wait), SUCCESS (replay result), FAILURE (replay error).
> - **In-flight dedupe** is the trickiest case — PENDING must wait, not re-execute.
> - **Per-tenant scope** — `(tenant_id, key)`.
> - **TTL** matches retry window (Stripe default 24h).
> - **Body fingerprint** to catch key reuse with different params.
> - **Crash mid-work** → PENDING TTL → next retry picks up.
> - **Variants:** DB-backed (durable); HTTP middleware; outbox; async/queue.
> - **Trap:** check-then-act; in-memory cache; cross-tenant collision; replaying wrong response.

---

**Related:** [retry-with-jitter-and-budget.md](./retry-with-jitter-and-budget.md) · [cache-stampede-single-flight.md](./cache-stampede-single-flight.md) · [request-deduplication.md](./request-deduplication.md) · [`backend-data-prep/questions/transactions-concurrency/idempotency-key-design.md`](../../../backend-data-prep/questions/transactions-concurrency/idempotency-key-design.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
