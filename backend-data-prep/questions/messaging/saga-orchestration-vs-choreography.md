# Saga: orchestration vs choreography — when each wins and how to fail safely

## Source / Origin
- Microservices architecture canonical pattern.
- Hector Garcia-Molina & Kenneth Salem, "Sagas" (1987); revived for microservices by Chris Richardson.
- Concept reference: `backend-data-prep/messaging/sagas.md`.

## Why this question matters in interviews
Sagas are the answer to "we can't have a distributed 2PC, but we need transactional behavior across services". The interview signal: do you know the two flavours (orchestration / choreography) and choose by complexity? Can you articulate that the price is *no isolation* — partial states are observable? Do you design compensating actions correctly (semantic undo, not "DELETE")? Senior candidates also discuss the timeout, idempotency, and observability requirements.

## Concepts involved

### Syntax to lock in

```
Saga = sequence of local transactions T1, T2, ..., Tn with
       compensations C1, C2, ..., C_{n-1}.
       If Tk fails, run C_{k-1}, C_{k-2}, ..., C1 in reverse.
```

```javascript
// Orchestrator (centralised state machine)
class OrderSaga {
  steps = [
    { exec: 'reserve_inventory',  compensate: 'release_inventory' },
    { exec: 'charge_payment',     compensate: 'refund_payment'     },
    { exec: 'ship_order',         compensate: 'cancel_shipment'    },
  ];
  async run(orderId) {
    const completed = [];
    try {
      for (const step of this.steps) {
        await this.invoke(step.exec, orderId);
        completed.push(step);
      }
    } catch (e) {
      for (const step of completed.reverse()) {
        await this.invoke(step.compensate, orderId);
      }
      throw new SagaFailed(e);
    }
  }
}
```

```yaml
# Choreography (event-driven, no central coordinator)
order-service     emits OrderPlaced
inventory-service consumes OrderPlaced → reserves → emits InventoryReserved
payment-service   consumes InventoryReserved → charges → emits PaymentCharged
shipping-service  consumes PaymentCharged → ships → emits OrderShipped

# Failure path:
payment-service fails → emits PaymentFailed
inventory-service consumes PaymentFailed → releases reservation
order-service     consumes PaymentFailed → marks order cancelled
```

### Edge cases / interview traps

1. **Sagas don't give ACID isolation.** Other transactions can observe partial states. You need a "pending" / "tentative" state in your domain model.
2. **Compensations are semantic, not physical undo.** `refund_payment` is not `DELETE` from the payments table — it's a new transaction that reverses business effect.
3. **Compensations must be idempotent and commutative**. Retries are inevitable; compensation may arrive twice; compensation may arrive before the forward action committed (rare race).
4. **No "isolation"** between concurrent sagas. Saga A may read state changed by saga B before B finishes. Solutions: semantic locks, commutative updates, or accept the anomaly.
5. **Choreography → distributed state.** No central place to ask "where is this saga right now?". Hard to debug and visualise. Mitigations: correlation IDs, distributed tracing.
6. **Orchestration → coupling to orchestrator.** The orchestrator knows all participants. Adding a step means changing the orchestrator. Mitigations: state-machine engine (Temporal, Cadence, AWS Step Functions).
7. **Timeouts are first-class.** Every step has a max duration; on timeout, decide compensate or escalate.
8. **Event-loss in choreography.** If a service crashes after consuming an event but before publishing the next, the saga stalls. Outbox pattern is mandatory.
9. **Pivot transactions vs compensatable.** Once you cross a "pivot" (e.g., shipping label printed), some steps cannot be compensated cleanly. Design forward recovery for those.

## Mental Model

The **"relay race"** analogy.

```
   Choreography: each runner hands the baton to the next
                 No referee. Runners know their lane.
                 Easy to add a runner; hard to know the race state.

                 [Order] → [Inventory] → [Payment] → [Shipping]
                  emit       emit          emit        emit
                  event      event         event       event

   Orchestration: a coach directs each runner
                 Coach calls "Order, go", waits for ack, then "Inventory, go".
                 Coach knows the race state. Adding a runner = update coach.

                  [Coach] ──► [Order]
                     ▲          │ ack
                     ├──────────┘
                     ──► [Inventory] (request/reply)
                     ──► [Payment]
                     ──► [Shipping]

   Compensations: if any runner trips, previous runners run backward.
```

## Why interviewers care

- Distributed transactions are a senior topic; sagas are the practical answer.
- Choreography vs orchestration is a real architectural tradeoff with operational consequences.
- Compensation design surfaces understanding of "semantic undo" vs "rollback".

## Common beginner confusion

- "Sagas give ACID across services." No — only Atomicity (eventually), no Isolation, weakened Consistency.
- "Compensation is just rollback." It's a new transaction; database rollback isn't possible after commit.
- "Choreography is always simpler." For 3 steps yes; for 8 steps with conditional branches, orchestration wins.
- "Orchestrator is a single point of failure." Run it HA; persist state; restart safely.
- "I'll use 2PC instead." 2PC blocks resources, has its own failure modes, and most modern stacks don't support cross-service XA.

## Brute force approach

Two-phase commit (XA) across services. Coordinators, prepare/commit, blocking on coordinator failure, no support in most modern databases. Don't.

## Optimal approach

Decision: **orchestration** when the flow has conditional branches, retries, complex state, or you need visibility. **Choreography** for linear flows with few steps and loose coupling.

Either way:
1. Each step is a local DB transaction.
2. Each forward step has a corresponding compensation.
3. All steps + compensations are idempotent.
4. State persisted at each transition (outbox pattern).
5. Timeouts on every step; compensation on timeout.
6. Correlation ID across all events for tracing.

## Solution

```
┌──────────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATION (Temporal / Step Functions)          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│             ┌───────────────────────────┐                            │
│   API ────► │  OrderSaga Orchestrator   │ ◄── persists state          │
│             │  (Temporal Workflow)      │     between steps           │
│             └────┬─────────────┬───────┬┘                            │
│                  │             │       │                             │
│            reserve         charge    ship                            │
│                  ▼             ▼       ▼                             │
│           ┌─────────┐  ┌─────────┐  ┌─────────┐                       │
│           │Inventory│  │Payments │  │Shipping │                       │
│           └─────────┘  └─────────┘  └─────────┘                       │
│                                                                      │
│   If Payments fails:                                                │
│     Orchestrator calls Inventory.release(orderId)                   │
│     Marks saga state = "compensated".                               │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                  CHOREOGRAPHY (event-driven)                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Order ─emits─► OrderPlaced                                         │
│                   │                                                  │
│                   ▼ (consumed by Inventory)                          │
│  Inventory.reserve → emits InventoryReserved                        │
│                              │                                       │
│                              ▼ (consumed by Payments)                │
│  Payments.charge → fail → emits PaymentFailed                        │
│                              │                                       │
│             ┌────────────────┴────────────────┐                      │
│             ▼                                  ▼                     │
│  Inventory.release                Order.markCancelled               │
└──────────────────────────────────────────────────────────────────────┘
```

```typescript
// ===== Orchestrator with Temporal-style workflow =====
async function orderSaga(orderId: string) {
  await runActivity('reserveInventory', orderId);
  try {
    await runActivity('chargePayment', orderId);
  } catch (e) {
    await runActivity('releaseInventory', orderId);  // compensate
    throw e;
  }
  try {
    await runActivity('shipOrder', orderId);
  } catch (e) {
    await runActivity('refundPayment', orderId);
    await runActivity('releaseInventory', orderId);
    throw e;
  }
  // success
}
// Activities are idempotent: keyed by (orderId, step).
// Workflow state persisted at every step. Crash-safe.

// ===== Choreography example: Inventory service =====
inventoryConsumer.on('OrderPlaced', async (event) => {
  await db.tx(async (t) => {
    const inserted = await t.query(
      `INSERT INTO reservations (order_id, sku, qty)
       VALUES ($1, $2, $3)
       ON CONFLICT (order_id) DO NOTHING RETURNING id`,
      [event.orderId, event.sku, event.qty]
    );
    if (inserted.rowCount > 0) {
      // outbox
      await t.query(`INSERT INTO outbox (event_type, payload) VALUES ($1, $2)`,
        ['InventoryReserved', JSON.stringify(event)]);
    }
  });
});

// Compensation handler
inventoryConsumer.on('PaymentFailed', async (event) => {
  await db.tx(async (t) => {
    const updated = await t.query(
      `UPDATE reservations SET status='released'
       WHERE order_id=$1 AND status='reserved' RETURNING id`,
      [event.orderId]
    );
    if (updated.rowCount > 0) {
      await t.query(`INSERT INTO outbox (event_type, payload) VALUES ($1, $2)`,
        ['InventoryReleased', JSON.stringify(event)]);
    }
  });
});
```

## Step-by-step dry run

Order saga, payment fails at step 2:

```
ORCHESTRATION:
  t=0   API → Orchestrator.start(orderId=ord-7)
  t=0   Orchestrator persists state {step: 0, status: 'running'}
  t=1   call Inventory.reserve(ord-7) → success
  t=1   state → {step: 1}
  t=2   call Payments.charge(ord-7) → returns DECLINED
  t=2   Orchestrator enters compensation:
          state → {status: 'compensating'}
          call Inventory.release(ord-7) → success
          state → {status: 'compensated'}
  t=3   API notified: order cancelled.
  Observable: single state row in saga table; debuggable.

CHOREOGRAPHY:
  t=0   Order publishes OrderPlaced(ord-7)
  t=1   Inventory consumes → reserves → publishes InventoryReserved
  t=2   Payments consumes InventoryReserved → tries charge → fails
        publishes PaymentFailed(ord-7)
  t=3   Inventory consumes PaymentFailed → release
  t=3   Order consumes PaymentFailed → mark cancelled
  Observable: distributed; must trace by correlation_id=ord-7 across logs.

Race condition example:
  t=0   Saga A reads Inventory (qty=10), reserves 6 → 4 left
  t=0   Saga B reads Inventory (qty=10), reserves 6 → conflict
  
  Fix: each reservation is a row-level conditional update
       UPDATE inventory SET qty=qty-6 WHERE sku='X' AND qty>=6 RETURNING qty;
       Second saga gets 0 rows; aborts; no compensation needed (no Inventory.reserve happened).
       Or: semantic lock — mark item as "pending" during saga; release on completion/compensation.
```

Pivot point example (cannot compensate cleanly):

```
Saga: reserve → charge → ship → notify-customer
Pivot: once notification email is sent, can't "unsend".
Design: do notify-customer LAST so failures before it are fully compensatable.
For irreversible steps, accept forward recovery only:
  retry, manual escalation, but no automatic compensation.
```

## How to think aloud in the interview

> "Sagas exist because 2PC across services isn't practical. Each saga is N local transactions with N-1 compensations. The price you pay vs ACID: no isolation — partial states are visible — and only eventual atomicity.
>
> Two flavors:
> - **Orchestration** (Temporal, Step Functions, custom workflow engine): centralised state machine. Easy to reason about, debug, visualise. Best when steps have conditional branches or visibility matters.
> - **Choreography** (event-driven, each service consumes & emits): loosely coupled. Best for linear flows with 3-5 steps.
>
> Compensations are *semantic undo*: refund a payment, not delete the row. They must be idempotent and commutative.
>
> Mandatory plumbing:
> - **Outbox pattern** so events publish atomically with the local commit.
> - **Correlation ID** on every event for tracing.
> - **Timeouts** on every step; compensate or escalate.
> - **Semantic locks / pending states** in domain models so partial states don't corrupt.
>
> I'd default to **orchestration** for non-trivial sagas (> 4 steps) — the operational visibility pays for itself. Choreography for simple, linear, decoupled flows."

## Important takeaways

- Sagas = N local TXNs + N-1 compensations; no ACID isolation; eventual atomicity.
- Compensations = semantic undo, not DB rollback; idempotent and commutative.
- Orchestration: centralised, visible, easier debugging; coupling to orchestrator.
- Choreography: distributed, loose coupling; harder to trace.
- Outbox pattern for event publish atomicity; correlation IDs for tracing.
- Identify pivot transactions (irreversible) and design forward recovery.
- Semantic locks / pending states keep concurrent sagas from corrupting each other.

## Variants

1. **Hybrid** — orchestration for the high-level flow, choreography within bounded contexts.
2. **Temporal / Cadence** — orchestration with code-as-workflow; durable execution.
3. **AWS Step Functions** — JSON state machine; managed.
4. **Camunda / Zeebe** — BPMN-based orchestration.
5. **Saga with retries** — orchestrator retries failed steps before compensating.
6. **Long-running sagas** — days/weeks; need durable state, not in-memory.

## Revision notes

> **saga — 60s recap**
> - N local TXNs + N-1 compensations; no isolation; eventual atomicity.
> - Compensations: semantic undo, idempotent, commutative.
> - Orchestration (Temporal/Step Functions): central, visible; default for > 4 steps.
> - Choreography (event-driven): decoupled; for linear simple flows.
> - Outbox pattern is mandatory for event publish atomicity.
> - Correlation IDs + tracing.
> - Pivot transactions: irreversible; design forward recovery.
> - Semantic locks / pending states for concurrent saga safety.
