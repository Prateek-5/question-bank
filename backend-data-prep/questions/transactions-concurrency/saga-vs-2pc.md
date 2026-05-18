# Saga vs Two-Phase Commit — Distributed Transaction Tradeoffs

## Source / Origin
- Garcia-Molina & Salem, "Sagas" (1987). The original alternative to long-lived 2PC.
- 2PC: Jim Gray, "Notes on Database Operating Systems" (1978), formalised in X/Open XA.
- Productionised in: Netflix Conductor, Uber Cadence/Temporal, AWS Step Functions, Camunda, Axon Framework.
- Companion doc: `transactions-concurrency/two-phase-commit-walkthrough.md`.
- Interview prompt: "You're booking a flight + hotel + car across three services. Each has its own DB. How do you keep them consistent without holding locks across all three?"

## Why this question matters in interviews
This is the **microservices-era distributed-transaction question** at senior backend rounds. Every candidate has heard "use a saga". Few can articulate when 2PC is actually correct, when sagas are actually correct, and what choreography-vs-orchestration buys you. The interviewer wants you to (a) name the failure modes of 2PC (blocking, coordinator failure), (b) explain why sagas trade atomicity for availability and what "compensating action" means, (c) draw the choreography-vs-orchestration architecture, and (d) reason about idempotency and ordering. Get this right and you're flagged as someone who's actually shipped microservices. Get it wrong and you're flagged as a monolith engineer trying to fake it.

## Concepts involved

### Syntax to lock in

Two-Phase Commit (XA-style):
```
                ┌──────────┐
                │Coordinator│
                └────┬──────┘
                     │
   Phase 1 (PREPARE) │   "Can you commit?"
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     [Bank]      [Inventory]  [Shipping]
       │             │            │
       │── YES ──────│── YES ─────│── YES ──►
                     │
   Phase 2 (COMMIT)  │   "Commit now."
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     COMMIT       COMMIT       COMMIT
```

Saga (orchestration flavour):
```
┌─────────────┐
│ Orchestrator│  ── 1. CreateOrder ───►  [OrderSvc]   ─► OK
└─────┬───────┘  ── 2. ChargeCard ────►  [PaymentSvc] ─► OK
      │           ── 3. ReserveItem ──►  [InvSvc]     ─► FAIL!
      │
      ▼   compensate in reverse:
        ── 3'. CancelCharge ──► [PaymentSvc]
        ── 4'. CancelOrder ───► [OrderSvc]
```

Saga (choreography flavour) — services emit events, peers react:
```
[OrderSvc] ─emit OrderCreated─►  [PaymentSvc]  ─emit PaymentCharged─►  [InvSvc]
                                                                          │
                                          OrderCancelled ◄─emit InventoryFailed
                                          PaymentRefunded ◄─emit OrderCancelled
```

### Edge cases / interview traps

1. **2PC blocks indefinitely if the coordinator dies between phase 1 and phase 2.** Participants are in PREPARED state — holding locks, unable to abort, unable to commit. This is the classic "2PC blocking problem". Recovered coordinator must replay the log to unblock them.
2. **2PC requires XA or equivalent.** Most modern DBs (Postgres, MySQL) support it but rarely in production. Kafka, MongoDB, Redis don't. Microservice DBs often can't participate.
3. **Compensating actions are not "undo".** A compensating action is a *new business action* that semantically reverses the previous one. CancelCharge ≠ DELETE charge row — it's an issued refund with its own ledger entry. The old action is preserved (audit). Sagas leave a forward-only trail.
4. **Sagas are not atomic — they're eventually consistent.** During the saga, an outside reader can observe partial state ("order exists, payment doesn't yet"). The system is in a *valid* state at every step, just not the "final" one.
5. **Orchestration vs choreography.** Orchestration: a central state machine drives the flow. Pro: easy to reason about. Con: orchestrator becomes a coupling point. Choreography: services react to events; no central brain. Pro: loosely coupled. Con: emergent flows are hard to debug; risk of event spaghetti.
6. **Idempotency is mandatory.** Every step (and every compensating step) must be safe to retry. Network blips will replay messages.
7. **Ordering matters in choreography.** "PaymentCharged" arriving before "OrderCreated" (out-of-order event bus) breaks the flow. Sequence numbers, idempotency keys, or strict-ordered partitions (Kafka per-key) required.
8. **Some compensations are impossible.** "Email sent" can't be unsent. Either avoid those steps until after irreversible point-of-no-return, or design semantic compensation (apology email).
9. **2PC's "presumed abort" optimisation** — coordinator can forget aborted transactions immediately; only commits need durable logs. Asked occasionally in DB-internals interviews.
10. **Three-phase commit (3PC)** — adds a PRE-COMMIT phase to bound the blocking window. Theoretically non-blocking under specific failure models. Never actually used in production; cite for completeness only.
11. **Saga timeout.** A step that "hangs" indefinitely should time out and trigger compensation. Don't trust services to fail fast.
12. **Saga reads.** A saga in progress is a "tentative" business object. UIs often need a "pending" state ("Your order is being processed..."). Don't expose half-baked state as final.

## Mental Model

### 2PC = "everyone vote, then everyone commit"

```
Phase 1: Prepare
  Coordinator asks every participant: "Can you commit?"
  Each participant:
    - acquires locks
    - writes a "prepared" log record (durable)
    - replies YES or NO
    - DOES NOT release locks until phase 2

Phase 2: Commit (or Abort)
  If all YES → Coordinator writes "commit" log, broadcasts COMMIT.
  If any NO   → Coordinator broadcasts ABORT.
  Each participant: commit (or roll back), release locks.
```

The catch: in phase 1, every participant has its locks held. If the coordinator crashes between phase 1 and phase 2, participants are stuck. This is the **blocking** failure mode of 2PC and the reason it's avoided in microservices.

### Saga = "forward-only flow with compensations"

```
                  step 1
   Action ──────────────────► state A
                                 │
                  step 2          │
   Action ──────────────────► state B
                                 │
                  step 3          │
   Action ──────────FAIL!         │
                                 │
              ◄── compensate 2 ──┘
              ◄── compensate 1
                                 │
                              state Ø (rolled back, but via *forward* actions)
```

Each step is a normal local transaction. There are no held locks between steps. If step 3 fails, we run *new* transactions (compensating actions) that semantically undo the earlier ones.

### Choreography vs orchestration in one picture

```
ORCHESTRATION (centralised)               CHOREOGRAPHY (distributed)
                                                                          
       ┌───────────────┐                  [Order]──event──►[Payment]
       │ Orchestrator  │                                       │
       │  state-machine │                                       │
       └──┬─┬─┬────────┘                              event ◄───┘
          │ │ │                                       │
          ▼ ▼ ▼                                       ▼
       [O][P][I][S]                                [Inventory]──event──►[Ship]

Pro: visible flow, central retry/timeout    Pro: services don't know each other
Con: orchestrator coupling, SPOF risk       Con: emergent behaviour, hard to debug
```

## Why interviewers care

- It tests whether you've actually thought about **microservice consistency** vs just "use sagas because Netflix does".
- It maps onto real production tools: Temporal, Step Functions, Conductor — every senior backend has touched at least one.
- The follow-ups are unbounded: idempotency keys, deduplication, exactly-once semantics, event-sourcing, outbox pattern. Each is a depth probe.
- It surfaces whether you understand the **CAP-flavoured tradeoff**: 2PC chooses C over A; sagas choose A over C.

## Common beginner confusion

- **"Sagas are atomic."** They're not. They're forward-only flows with compensations. There is a window where outside observers see partial state.
- **"2PC scales."** It doesn't well — every commit is a multi-network-round-trip with held locks. Throughput drops with participant count.
- **"Compensating action = SQL rollback."** No. Compensation is a *new business action* that semantically reverses the prior one. CancelCharge creates a refund ledger entry; it doesn't delete the original charge.
- **"Choreography is better than orchestration."** Both have valid use cases. Choreography wins for loosely coupled domains and few-step flows; orchestration wins for complex multi-step flows where centralised observability matters.
- **"Idempotency is optional."** It is mandatory. Every step in a saga will eventually be retried.
- **"Sagas always succeed."** They might exhaust retries and end in a partial-rollback state requiring human intervention. Plan for it.
- **"2PC and sagas are interchangeable."** Not really. 2PC = strict atomicity, with availability cost. Saga = eventual consistency, with complexity cost. Different tools.
- **"Use eventual consistency = use sagas."** Eventual consistency is a *property*; sagas are one *pattern* to achieve it. Outbox + CDC is another. Event sourcing is another.

## Brute force approach

Make all services share one database; wrap the whole flow in a single `BEGIN; ... COMMIT;`. This is the "distributed monolith" anti-pattern — works perfectly until you scale, then doesn't.

Alternative brute force: 2PC over XA. Works in theory; in microservices most participants (Kafka, Mongo, Redis, third-party APIs) don't support XA. Effectively non-applicable.

## Optimal approach

### When to use 2PC

- All participants are *XA-compatible* relational databases.
- You can tolerate held locks across the flow.
- The flow is short (milliseconds, not seconds).
- You truly need atomicity, not eventual consistency.

Realistic examples: legacy banking core systems; multi-shard transactions inside one Postgres deployment via `PREPARE TRANSACTION`. **Rare in microservices.**

### When to use sagas

- Participants don't share a DB.
- Some participants are non-transactional (third-party APIs, message brokers).
- The flow is long (seconds to minutes).
- You can design semantic compensations for every step.

Realistic examples: order fulfilment (order + payment + inventory + shipping), trip booking (flight + hotel + car), travel claim processing.

### Choreography vs orchestration decision

- **Choreography** for: 2-3 step flows, loosely coupled domains, eventual addition of new participants without changing existing code.
- **Orchestration** for: 5+ step flows, complex retries/timeouts, regulatory observability requirements, central error-handling and human-in-the-loop steps.

When in doubt, start with **orchestration** — it's easier to debug. Migrate to choreography only when central coordinator becomes a bottleneck.

### Decision matrix

```
Property                    2PC         Saga (orch)    Saga (chor)
──────────────────────────────────────────────────────────────────
Atomic                      YES         NO             NO
Locks during flow           YES         NO             NO
Coordinator SPOF risk       HIGH        MEDIUM         NONE
Coupling                    LOOSE       MED (orchestrator) LOOSE
Debug observability         HIGH        HIGH           LOW
Throughput                  LOW         HIGH           HIGH
Implementation complexity   MED         MED            HIGH
Requires XA                 YES         NO             NO
Compensation logic          NO          YES            YES
Idempotency required        NO          YES            YES
```

## Solution (saga orchestrator pseudo-code)

```python
class BookTripSaga:
    """
    Steps:        action            ↔ compensation
    1. BookFlight  reserve_flight   ↔ cancel_flight
    2. BookHotel   reserve_hotel    ↔ cancel_hotel
    3. ChargeCard  charge           ↔ refund
    4. SendEmail   send_confirm     ↔ send_apology  (no true undo)
    """
    STEPS = [
        ("BookFlight",   "flight.reserve",    "flight.cancel"),
        ("BookHotel",    "hotel.reserve",     "hotel.cancel"),
        ("ChargeCard",   "payment.charge",    "payment.refund"),
        ("SendEmail",    "email.send_confirm","email.send_apology"),
    ]

    def __init__(self, saga_id, request):
        self.saga_id = saga_id
        self.request = request
        self.completed = []      # for rollback

    def run(self):
        for name, action, _ in self.STEPS:
            try:
                self._dispatch(action, self.request, step=name)
                self.completed.append(name)
                self._persist_state("step_done", name)
            except Exception as e:
                self._compensate(reason=str(e))
                return "FAILED"
        return "OK"

    def _compensate(self, reason):
        # Reverse-order, idempotent compensations.
        for name in reversed(self.completed):
            _, _, comp = next(s for s in self.STEPS if s[0] == name)
            try:
                self._dispatch_with_retry(comp, self.request, step=f"comp:{name}")
            except Exception as e:
                # Compensation failed — alert; do not give up.
                metrics.incr("saga.compensation.failed")
                escalate(self.saga_id, name, e)
        self._persist_state("compensated", reason)

    def _dispatch(self, op, payload, step):
        # Idempotency key = saga_id + step
        return rpc.call(op, payload, idempotency_key=f"{self.saga_id}:{step}")

    def _dispatch_with_retry(self, op, payload, step, attempts=5):
        delay = 0.1
        for _ in range(attempts):
            try:
                return self._dispatch(op, payload, step)
            except TransientError:
                time.sleep(delay); delay *= 2
        raise PermanentCompensationFailure()
```

Equivalent choreography flow (event-driven):

```python
# OrderService
@on_event("CreateOrderRequested")
def handle(req):
    order = db.insert_order(req, status="PENDING")
    outbox.publish("OrderCreated", {"saga_id": req.saga_id, "order_id": order.id})

# PaymentService
@on_event("OrderCreated")
def handle(evt):
    if dedupe_seen(evt.saga_id, "charge"): return
    charge = stripe.charge(evt, idempotency_key=evt.saga_id + ":charge")
    outbox.publish("PaymentCharged", {"saga_id": evt.saga_id, "charge_id": charge.id})

# InventoryService
@on_event("PaymentCharged")
def handle(evt):
    if not inventory.reserve(evt.item, evt.qty):
        outbox.publish("InventoryFailed", {"saga_id": evt.saga_id})
    else:
        outbox.publish("InventoryReserved", evt)

# PaymentService also listens for the failure
@on_event("InventoryFailed")
def compensate(evt):
    stripe.refund(saga_id=evt.saga_id, idempotency_key=evt.saga_id + ":refund")
    outbox.publish("PaymentRefunded", evt)

# OrderService also listens
@on_event("PaymentRefunded")
def compensate_order(evt):
    db.update_order_status(evt.saga_id, "CANCELLED")
```

## Step-by-step dry run

Scenario: book flight + hotel + charge card. Flight succeeds, hotel succeeds, charge fails (card declined).

**2PC**:
```
Phase 1:
  Coord → Flight:  PREPARE  → YES (lock seat)
  Coord → Hotel:   PREPARE  → YES (lock room)
  Coord → Bank:    PREPARE  → NO  (insufficient funds)

Phase 2:
  Coord broadcasts ABORT
  Flight: roll back, release lock
  Hotel:  roll back, release lock
  Bank:   no-op
```

Net effect: nothing persisted. Atomic. **Locks held for ~all of phase 1 + phase 2.**

**Saga (orchestration)**:
```
T=0    Orchestrator → Flight.reserve   → OK     (state: completed=[Flight])
T=200  Orchestrator → Hotel.reserve    → OK     (state: completed=[Flight, Hotel])
T=400  Orchestrator → Payment.charge   → FAIL   (card declined)
T=410  Orchestrator → Hotel.cancel     → OK     (compensate Hotel)
T=600  Orchestrator → Flight.cancel    → OK     (compensate Flight)
T=700  Saga ends in FAILED state. User notified.

Outside observer at T=300 sees: Flight reserved, Hotel reserved, no charge.
That's a *valid intermediate state*; it just doesn't reflect the *final* outcome.
```

**Saga (choreography)**:
```
[Order] OrderCreated ──► [Payment] charge fails ──► PaymentFailed event
                                                        │
                                                        ▼
                              [Inventory] hears PaymentFailed; nothing to do
                                                        │
                              [Order] hears PaymentFailed; updates to CANCELLED
                                                        │
                              [Hotel] hears PaymentFailed; releases room
                              [Flight] hears PaymentFailed; releases seat
```

Notice: in choreography, the failure propagation is implicit in who-subscribes-to-what. Adding a new service later just means subscribing to the right event.

## How to think aloud in the interview

> "Two distinct patterns for distributed transactions. Let me name them, then decide.
>
> **2PC** is the strict-atomicity option. A coordinator runs PREPARE on every participant, gets YES/NO, then broadcasts COMMIT/ABORT. Atomic, but every participant holds locks from PREPARE to COMMIT, and if the coordinator dies between phases, participants are stuck in PREPARED. Plus you need XA support across all participants — not realistic when one of them is Kafka or a third-party API.
>
> **Saga** is the eventual-consistency option. Each step is a local transaction; if step N fails, run compensating actions for steps 1..N-1 in reverse. No held locks between steps. Outside observers can see intermediate states. Compensation is a *new business action*, not a SQL rollback — e.g., CancelCharge is a refund, not a delete.
>
> Two flavours of saga:
> - **Orchestration**: a central state machine (Temporal, Step Functions) drives steps. Easy to debug, central retry/timeout, but the orchestrator is a coupling point.
> - **Choreography**: services emit events, peers react. Loosely coupled, but the flow is implicit and hard to debug.
>
> My default: orchestration for any flow with more than 3 steps or with regulatory observability needs; choreography for simple two-party flows.
>
> Three non-negotiables:
> 1. **Idempotency keys** on every action and compensation — retries will happen.
> 2. **Compensation must be possible.** If a step is irreversible (send email, ship package), gate it behind the point-of-no-return.
> 3. **Timeouts** on every step — a hung service should trigger compensation, not block forever.
>
> 2PC has its place — within a single Postgres deployment doing `PREPARE TRANSACTION` across shards, or in legacy banking cores. In a typical microservice stack, sagas dominate."

## Important takeaways

- **2PC: atomic but blocking.** Coordinator failure between phases leaves participants stuck. Requires XA.
- **Saga: eventually consistent, never blocks.** Each step is local; compensations are forward-only business actions.
- **Compensation ≠ rollback.** It's a new transaction with audit value.
- **Orchestration** for complex flows; **choreography** for simple, loosely coupled flows.
- **Idempotency keys are mandatory.** Every action will retry.
- **Some steps cannot be compensated** (sent emails, shipped goods); gate them behind point-of-no-return.
- **Timeouts on every step** — don't trust services to fail fast.
- **The intermediate state is visible** during a saga; design UIs and APIs to expose "pending" states.
- **Production tools**: Temporal (Uber), Cadence, AWS Step Functions, Netflix Conductor, Camunda, Axon.

## Variants

1. **Outbox pattern** — write the event to a local "outbox" table in the same transaction as the business write; a separate publisher relays events. Eliminates the "wrote DB but failed to publish" gap. See `transactional-outbox.md`.
2. **Event sourcing + saga** — each saga step is a domain event; replay-driven. The system has perfect audit but is harder to query.
3. **Routing slip** — a variant of choreography where the message carries its own remaining steps. Used in pipelines.
4. **Process manager** — alias for orchestrator in DDD lingo. Same thing.
5. **TCC (Try-Confirm-Cancel)** — explicit reservation API per participant: Try reserves, Confirm finalises, Cancel releases. A halfway-house between 2PC and saga. Used at Alibaba.
6. **3PC** — adds a PRE-COMMIT phase to bound blocking. Theoretically non-blocking under specific failure models. Cited but not deployed.
7. **MySQL / Postgres prepared transactions** — both support `XA`/`PREPARE TRANSACTION`. Postgres requires `max_prepared_transactions > 0` in config (default 0!). Mention this — it's a known gotcha.

## Revision notes

> **saga vs 2PC — 60 second recap**
> - **2PC**: PREPARE all, then COMMIT all. Atomic. Blocking on coordinator failure. Requires XA.
> - **Saga**: forward-only flow of local txns; failures trigger compensating actions in reverse.
> - **Compensation ≠ undo** — it's a new business action that semantically reverses.
> - **Orchestration**: central state-machine. Easier to debug. Couples on orchestrator.
> - **Choreography**: services emit events. Loosely coupled. Hard to debug emergent flows.
> - **Idempotency keys + timeouts** are non-negotiable.
> - **2PC use cases**: single-deployment multi-shard, legacy banking. Rare in microservices.
> - **Saga use cases**: order fulfilment, multi-party booking, travel claims.
> - **Trap**: thinking sagas are atomic; they aren't — observers can see intermediate state.
> - **Trap**: irreversible steps (email, shipping) need point-of-no-return gating.
> - **Tools**: Temporal, Cadence, Step Functions, Conductor, Camunda.
