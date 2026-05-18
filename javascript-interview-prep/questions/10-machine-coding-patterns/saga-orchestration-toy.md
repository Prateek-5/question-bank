# Saga (Orchestration) — Toy Implementation

## Source / Origin
- Hector Garcia-Molina & Kenneth Salem, "Sagas" (1987).
- Modern revival: microservices distributed transactions without 2PC.
- Asked at: Razorpay, Stripe, Atlassian, Booking, Uber.
- Concept reference: `backend-data-prep/questions/messaging/saga-orchestration-vs-choreography.md`.

## Why this question matters in interviews
When a single business transaction spans multiple services (reserve inventory → charge payment → create shipment), 2PC is too slow and too coupled. A saga is the alternative: each step runs in its own local transaction, and if a later step fails, you run *compensating* actions to undo the earlier steps. Senior bar: you can articulate (1) forward step + compensation must each be idempotent, (2) the orchestrator vs choreography choice, (3) what happens if a *compensation* itself fails (retry forever until human).

## Concepts involved

### Syntax to lock in
```js
class Saga {
  constructor() { this.steps = []; }
  step(name, doFn, undoFn) { this.steps.push({ name, doFn, undoFn }); return this; }
  async execute(ctx) {
    const done = [];
    try {
      for (const s of this.steps) {
        const out = await s.doFn(ctx);
        done.push({ ...s, out });
      }
      return ctx;
    } catch (err) {
      for (const s of done.reverse()) {
        try { await s.undoFn(ctx, s.out); }
        catch (compErr) { /* log + alert; compensation failures escalate */ }
      }
      throw err;
    }
  }
}
```

### Edge cases / interview traps
1. **Forward step must be idempotent.** Otherwise a retry mid-saga double-applies.
2. **Compensation must be idempotent too.** Crash mid-rollback → retry rollback → must converge.
3. **Compensation can fail.** Don't silently swallow; emit "stuck saga" alert; humans intervene. Some sagas use a durable workflow engine (Temporal, AWS Step Functions) for retries.
4. **Order matters.** Compensations run in *reverse* order of forward steps.
5. **Persistent state.** A toy saga lives in memory and dies if the process restarts mid-flight. Production: persist `{saga_id, completed_steps, status}` after every step.
6. **No isolation.** Other transactions see the partial state. Some sagas use "semantic locks" (e.g., reservation state) to mask it.
7. **Choreography vs orchestration.** Choreography = each service listens to events and decides next step (no central coordinator). Orchestration = one engine drives the sequence. Each has a place.

## Mental Model

A **booking checklist** with a "undo" pen next to every item:

```
   ┌──────────────────────────────────────────────────────────┐
   │ saga: book_trip                                          │
   │   step1: reserve_flight       undo: cancel_flight_hold   │
   │   step2: reserve_hotel        undo: cancel_hotel_hold    │
   │   step3: charge_card          undo: refund_card          │
   │   step4: send_confirmation    undo: send_apology_email   │
   └──────────────────────────────────────────────────────────┘

   Failure scenario: step3 fails (card declined)
        done = [step1, step2]
        run step2.undo → cancel hotel hold
        run step1.undo → cancel flight hold
        throw original error to caller
```

## Why interviewers care

- **Distributed transactions** are senior territory — you must know why 2PC isn't the answer.
- **Idempotency reasoning** at every step.
- **Failure recovery** — what if compensation also fails?

## Common beginner confusion

- **"Saga = rollback."** Not really — there's no transactional rollback. You execute *new* operations that semantically undo prior ones.
- **"Compensation is automatic."** It's hand-written code, one per step.
- **"Saga = 2PC."** No — saga uses local transactions only; 2PC blocks across services with a coordinator.
- **"In-memory saga is enough."** Crash mid-flight loses state. Persist after every step.
- **"Both orchestration and choreography are the same."** They have very different failure modes and observability stories.

## Brute force approach

```js
// no compensation — partial failure leaves the system in a broken state forever
await reserveFlight();
await reserveHotel();
await chargeCard();   // throws → flight + hotel held forever
```

## Optimal approach

Orchestrator with `step(name, do, undo)` definitions. Execute forward, push completed steps onto a stack. On failure, pop and compensate in reverse. Persist after every transition.

## Solution (JavaScript) — orchestration

```js
class Saga {
  constructor({ name, persist }) {
    this.name = name;
    this.steps = [];
    this.persist = persist || (async () => {});       // (state) => void  — optional checkpoint
  }
  step(name, doFn, undoFn) {
    this.steps.push({ name, doFn, undoFn });
    return this;
  }
  async execute(ctx) {
    const trace = { saga: this.name, completed: [], status: 'RUNNING' };
    await this.persist(trace);
    try {
      for (const s of this.steps) {
        const out = await s.doFn(ctx);
        trace.completed.push({ name: s.name, out });
        await this.persist(trace);
      }
      trace.status = 'SUCCEEDED';
      await this.persist(trace);
      return ctx;
    } catch (err) {
      trace.status = 'COMPENSATING';
      await this.persist(trace);
      for (let i = trace.completed.length - 1; i >= 0; i--) {
        const s = this.steps.find(x => x.name === trace.completed[i].name);
        try {
          await s.undoFn(ctx, trace.completed[i].out);
        } catch (cErr) {
          trace.status = 'STUCK';
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

// Usage
const saga = new Saga({ name: 'book_trip' })
  .step('reserve_flight', (ctx) => flightApi.hold(ctx.tripId, ctx.flight), (ctx) => flightApi.release(ctx.tripId))
  .step('reserve_hotel',  (ctx) => hotelApi.hold(ctx.tripId, ctx.hotel),  (ctx) => hotelApi.release(ctx.tripId))
  .step('charge_card',    (ctx) => payApi.charge(ctx.tripId, ctx.amount), (ctx) => payApi.refund(ctx.tripId));

await saga.execute({ tripId: 't_42', flight: 'AI101', hotel: 'taj', amount: 50000 });
```

## Step-by-step dry run

Scenario: charge fails after both holds succeed.

```
forward
  step1 reserve_flight  → success  trace.completed=[{flight}]
  step2 reserve_hotel   → success  trace.completed=[{flight},{hotel}]
  step3 charge_card     → throws "card declined"

compensation (reverse)
  undo step2 cancel hotel hold  → success
  undo step1 cancel flight hold → success

state: COMPENSATED; throw original error to caller
```

If during compensation the hotel API is also down → status=STUCK; alert; human re-runs `saga.resumeCompensation(saga_id)`.

## How to think aloud in the interview

> "Saga: each forward step has a compensation that semantically undoes it. Run forward; on failure, run completed compensations in reverse. Forward and undo are both idempotent. Persist trace after every step so a crash can resume. Compensation failure → STUCK status + alert. For my system I'd lean orchestration over choreography because debugging a saga across 6 event topics is operational pain. For real production I'd use Temporal or AWS Step Functions, not roll my own."

## Important takeaways

- **Idempotent forward + idempotent undo.** Mandatory.
- **Compensate in reverse order.**
- **Persist after each transition.**
- **Compensation can fail** → STUCK → human escalation.
- **Orchestration vs choreography** is a real decision; pick orchestration when you have >3 steps or need observability.

## Variants

- **Pivot transaction** — one "point of no return" step after which there's no compensation, only retry-forever. Useful for legal/auditing actions.
- **Choreography** — each service listens to events and triggers its own step + emits next event. No central coordinator; harder to debug.
- **Semantic locks** — temporary state (e.g., `flight: HELD`) prevents other transactions from interfering during the saga.
- **Durable workflows** (Temporal, Cadence) — saga primitives backed by a persistent state machine with auto-retry.

## Revision notes

```
Saga (orchestration):
  step(name, do, undo)
  execute(ctx):
    forward: for each step: do(ctx); persist trace
    on failure: for each completed step in reverse: undo(ctx, out); persist
    compensation failure → STUCK; alert
  
  forward + undo are BOTH idempotent
  compensate in reverse order
  persist after every step
  variants: pivot, choreography, semantic locks, Temporal/Cadence
  not 2PC — local txns only, semantic undo not rollback
```
