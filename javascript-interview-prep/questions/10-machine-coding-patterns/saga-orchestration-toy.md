# Saga (Orchestration) — distributed transaction via compensations

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [mini-state-machine.md](./mini-state-machine.md), [idempotency-wrapper.md](./idempotency-wrapper.md)
>
> **Source:** Garcia-Molina & Salem (1987). Microservices answer to 2PC. Razorpay, Stripe, Atlassian, Booking, Uber.

---

## 1. Problem statement

**Signature**
```ts
class Saga {
  constructor(opts: { name: string; persist?(state): Promise<void> });
  step(name: string, doFn: (ctx) => Promise<any>, undoFn: (ctx, out?) => Promise<void>): this;
  execute(ctx: any): Promise<any>;
}
```

**Input / Output examples**

| Setup                                                  | Behaviour                                              |
|--------------------------------------------------------|---------------------------------------------------------|
| All steps succeed                                      | returns ctx; status SUCCEEDED                          |
| Step 3 throws (after step 1, 2 succeeded)              | compensate step 2, then step 1, in reverse; rethrow    |
| Compensation throws                                    | status STUCK + alert; manual intervention              |
| Server crashes mid-saga                                | persisted trace → resume after restart                 |
| Forward step or undo not idempotent                     | retry may double-apply — broken contract               |

**Constraints**
- Forward step **AND** compensation BOTH idempotent.
- Compensations run in **reverse order** of completed forward steps.
- Persist trace after every step.
- Compensation failure → STUCK status, escalate.

---

## 2. Plain-English restatement

A multi-step business transaction across services (reserve flight → reserve hotel → charge card → confirm). No 2PC: each step is a local transaction. On failure of step N, run "compensating" actions for steps N-1, N-2, ... 1, in reverse, to semantically undo. Saga isn't rollback — it's executing **new** operations that undo prior ones.

---

## 3. Why this matters in interviews

Distributed-transaction question — senior territory. Why not 2PC? Too slow, too coupled. Saga is the practical answer. Tests: idempotency at every step, orchestration vs choreography choice, what happens when compensation itself fails.

---

## 4. Mental model

```
   Booking checklist with an "undo" pen next to each:

   saga: book_trip
     step1: reserve_flight       undo: cancel_flight_hold
     step2: reserve_hotel        undo: cancel_hotel_hold
     step3: charge_card          undo: refund_card
     step4: send_confirmation    undo: send_apology_email

   Forward (charge fails at step 3):
     ✓ reserve_flight        → completed=[step1]
     ✓ reserve_hotel         → completed=[step1, step2]
     ✗ charge_card           → THROWS

   Compensate (reverse):
     undo step2: cancel_hotel_hold     ✓
     undo step1: cancel_flight_hold    ✓
     status: COMPENSATED; rethrow original error.

   If compensation step fails (e.g., hotel API also down):
     status: STUCK; alert ops; humans intervene.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why must BOTH forward step and compensation be idempotent?
> 2. What's the difference between a saga rollback and a SQL `ROLLBACK`?
> 3. If compensation itself fails, what should the saga do?

---

## 6. Brute force — walked through

### Wrong attempt 1: no compensation
Partial failure leaves system in inconsistent state (flight held, hotel held, card not charged — forever).

### Wrong attempt 2: 2PC across services
Distributed lock with coordinator. Slow, hard to scale, single point of failure. Practical microservices use saga instead.

### Wrong attempt 3: in-memory saga
Crash mid-flight loses state. Always persist trace after every transition.

---

## 7. The unlocking insight

> **Two function references per step (`do`, `undo`). Execute forward, push each completed step. On any failure, run `undo` for completed steps in reverse. Persist trace after every step. Idempotent forward + idempotent undo. Compensation failure → STUCK.**

Three properties:

1. **`(do, undo)` pair** per step — semantic inverse, not transactional rollback.
2. **Persist trace** — crash recovery requires durable state.
3. **Compensation failure → STUCK** — alert humans; don't silently swallow.

---

## 8. Solution (annotated)

```js
class Saga {
  constructor({ name, persist }) {
    this.name = name;
    this.steps = [];
    this.persist = persist || (async () => {});                      // step 1: trace persistence hook
  }

  step(name, doFn, undoFn) {
    this.steps.push({ name, doFn, undoFn });
    return this;                                                       // chainable
  }

  async execute(ctx) {
    const trace = { saga: this.name, completed: [], status: 'RUNNING' };
    await this.persist(trace);
    try {
      for (const s of this.steps) {                                    // step 2: forward
        const out = await s.doFn(ctx);
        trace.completed.push({ name: s.name, out });
        await this.persist(trace);                                      // checkpoint after each step
      }
      trace.status = 'SUCCEEDED';
      await this.persist(trace);
      return ctx;
    } catch (err) {                                                    // step 3: forward failed
      trace.status = 'COMPENSATING';
      await this.persist(trace);
      for (let i = trace.completed.length - 1; i >= 0; i--) {           // step 4: REVERSE
        const completed = trace.completed[i];
        const s = this.steps.find((x) => x.name === completed.name);
        try {
          await s.undoFn(ctx, completed.out);
        } catch (cErr) {
          trace.status = 'STUCK';                                        // step 5: stuck
          trace.stuckOn = s.name;
          await this.persist(trace);
          throw new Error(`Saga ${this.name} stuck compensating ${s.name}: ${cErr.message}`);
        }
      }
      trace.status = 'COMPENSATED';
      await this.persist(trace);
      throw err;
    }
  }
}
```

**Try it yourself**

```js
const saga = new Saga({ name: 'book_trip', persist: async (s) => db.upsert('sagas', s) })
  .step('reserve_flight',
        (ctx) => flightApi.hold(ctx.tripId, ctx.flight),
        (ctx) => flightApi.release(ctx.tripId))
  .step('reserve_hotel',
        (ctx) => hotelApi.hold(ctx.tripId, ctx.hotel),
        (ctx) => hotelApi.release(ctx.tripId))
  .step('charge_card',
        (ctx) => payApi.charge(ctx.tripId, ctx.amount),
        (ctx) => payApi.refund(ctx.tripId));

try {
  await saga.execute({ tripId: 't_42', flight: 'AI101', hotel: 'taj', amount: 50000 });
} catch (e) {
  // saga compensated; ctx state semantically rolled back
}
```

---

## 9. Step-by-step dry run

```
Scenario: charge_card fails after both holds succeed.

trace = {saga:'book_trip', completed:[], status:'RUNNING'}
persist(trace)

step reserve_flight → do(ctx) ✓ → trace.completed=[{flight}]; persist
step reserve_hotel  → do(ctx) ✓ → trace.completed=[{flight},{hotel}]; persist
step charge_card    → do(ctx) THROWS 'card declined'
  trace.status='COMPENSATING'; persist
  reverse iteration:
    i=1: undo reserve_hotel → cancel hotel hold ✓
    i=0: undo reserve_flight → cancel flight hold ✓
  trace.status='COMPENSATED'; persist
  rethrow 'card declined'

STUCK scenario (hotel API also down):
  undo reserve_hotel → THROWS 'hotel API down'
  trace.status='STUCK', stuckOn='reserve_hotel'; persist
  throw "Saga book_trip stuck compensating reserve_hotel: hotel API down"
  → alert ops; human re-runs resumeCompensation(saga_id) after fix
```

---

## 10. Common confusion + traps

1. **Forward step not idempotent** — retry mid-saga double-applies.
2. **Compensation not idempotent** — crash mid-rollback → retry → must converge.
3. **Compensation failure swallowed** — saga thinks compensated; system actually inconsistent.
4. **Order wrong** — must reverse, last-completed first.
5. **In-memory trace** — crash loses state.
6. **Saga = SQL rollback** — no. Saga uses local txns + semantic undo.
7. **No isolation** — other transactions see partial state. Mitigate with semantic locks.

---

## 11. Senior follow-ups & variants

### Variant 1 — Pivot transaction
One "point of no return" step; no compensation after it (e.g., legal/audit submit). Retry-forever instead.

### Variant 2 — Choreography
Each service listens to events and triggers its own step + emits next event. No central coordinator. Harder to debug; less observable.

### Variant 3 — Semantic locks
Temporary state (e.g., `flight.status='HELD'`) prevents other transactions from interfering during the saga.

### Variant 4 — Durable workflow engine
Temporal, AWS Step Functions, Cadence. Saga primitives backed by persistent state machine with auto-retry. Production answer.

### Variant 5 — Resumable on restart
On startup, load incomplete sagas from store, continue forward or compensation from last checkpoint.

---

## 12. How to think aloud

> "Saga: each forward step has a compensation that semantically undoes it. Run forward; on failure, run completed compensations in reverse. Forward AND undo both idempotent. Persist trace after each step so crash can resume. Compensation failure → STUCK status + alert; humans intervene. Orchestration vs choreography: I'd lean orchestration for >3 steps because debugging a saga across 6 event topics is operational pain. Production: Temporal or AWS Step Functions, not roll my own. Saga is NOT 2PC and NOT SQL rollback — it's local transactions + semantic undo. Trap: non-idempotent steps; swallowing compensation failure; in-memory state."

---

## 13. 60-second revision

> - **`(do, undo)` pair** per step.
> - **Forward + undo BOTH idempotent.**
> - **Compensate in REVERSE order** of completed steps.
> - **Persist trace** after every step.
> - **Compensation failure → STUCK** + alert.
> - **NOT 2PC; NOT SQL rollback** — local txns + semantic undo.
> - **Orchestration** > choreography for observability (>3 steps).
> - **Production:** Temporal, AWS Step Functions, Cadence.
> - **Trap:** non-idempotent; swallowing comp failure; in-memory; wrong order.

---

**Related:** [mini-state-machine.md](./mini-state-machine.md) · [idempotency-wrapper.md](./idempotency-wrapper.md) · [circuit-breaker.md](./circuit-breaker.md) · [`backend-data-prep/questions/messaging/saga-orchestration-vs-choreography.md`](../../../backend-data-prep/questions/messaging/saga-orchestration-vs-choreography.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
