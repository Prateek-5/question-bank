# Transactional outbox pattern: atomic DB write + event publish

## Source / Origin
- Pattern catalogued by Chris Richardson (<a href="https://microservices.io/patterns/data/transactional-outbox.html" target="_blank" rel="noopener noreferrer">https://microservices.io/patterns/data/transactional-outbox.html</a>).
- Used by Debezium, Confluent, every modern event-driven microservice stack.
- Concept reference: `backend-data-prep/sql/06-transactions.md`.

## Why this question matters in interviews
"How do you atomically update the DB and publish a Kafka event?" is the single most common distributed-systems interview question after isolation levels. The wrong answers (call Kafka inside the transaction; call Kafka after the transaction) ship dual-write bugs. The right answer is the outbox: write the event row to a table inside the same DB transaction, drain it asynchronously to the broker. Knowing this pattern by heart signals real microservices literacy.

## Concepts involved

### Syntax to lock in

```sql
-- Schema
CREATE TABLE outbox (
  id          BIGSERIAL PRIMARY KEY,
  aggregate   TEXT NOT NULL,             -- e.g. 'order', 'payment'
  aggregate_id TEXT NOT NULL,
  event_type  TEXT NOT NULL,
  payload     JSONB NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now(),
  published_at TIMESTAMPTZ
);
CREATE INDEX outbox_unpublished ON outbox (id) WHERE published_at IS NULL;

-- Producer: atomic business + outbox write
BEGIN;
  UPDATE orders SET status='PAID' WHERE id=$1;
  INSERT INTO outbox (aggregate, aggregate_id, event_type, payload)
  VALUES ('order', $1::text, 'order.paid',
          jsonb_build_object('order_id', $1, 'paid_at', now()));
COMMIT;

-- Drainer: poll + publish + mark
WITH job AS (
  SELECT id, aggregate, aggregate_id, event_type, payload
  FROM outbox
  WHERE published_at IS NULL
  ORDER BY id
  LIMIT 100
  FOR UPDATE SKIP LOCKED
)
UPDATE outbox SET published_at = now()
WHERE id IN (SELECT id FROM job)
RETURNING *;
-- Then publish to Kafka. If publish fails, do NOT update published_at (or rollback).
```

### Edge cases / interview traps

1. **Dual-write problem**: writing to DB then publishing to Kafka in two steps leaves a window where one succeeds and the other doesn't. Outbox eliminates this by making the publish *intent* atomic with the business write.
2. **At-least-once delivery, not exactly-once.** The drainer can publish, crash before marking, then republish on restart. Consumers must be idempotent.
3. **Polling vs CDC**: polling outbox = simple, slight latency (1-5s). CDC via Debezium = sub-second, more infra.
4. **Ordering**: events for the same aggregate must be published in order. Use a partition key (e.g., aggregate_id) and a single drainer per partition.
5. **Outbox table bloat**: published rows accumulate. Either delete after N hours or partition by date.
6. **`SKIP LOCKED` in the drainer** is essential for multiple drainer workers — without it, only one worker can scan at a time.
7. **Transaction scoping**: the business write and the outbox INSERT must be in the *same* transaction. Connection pool gotchas: don't accidentally pick a different connection.

## Mental Model

The **"mailbox in the post office"** model. Inside your transactional safe (DB), you write a letter and put it in your mailbox. The mailbox is *part* of the safe — the letter exists only if the safe acknowledged your transaction. A postal worker (drainer) later picks up letters from the mailbox and delivers them. If the worker drops a letter and goes back for it later, that's at-least-once delivery. The recipient (consumer) must handle duplicates.

```
   ┌──────────────────────────────────────────┐
   │  Database  (ACID boundary)               │
   │                                          │
   │  BEGIN                                   │
   │   UPDATE orders SET status='PAID'        │
   │   INSERT INTO outbox (...) ─────┐        │
   │  COMMIT  (atomic)                │        │
   │                                  │        │
   │                                  ▼        │
   │  outbox table                            │
   └────────────────────┬─────────────────────┘
                        │ async drainer (every 1-5s)
                        │ + SKIP LOCKED for parallel workers
                        ▼
                  ┌──────────┐
                  │  Kafka   │
                  └──────────┘
                        │
                        ▼
                  consumers (idempotent)
```

## Why interviewers care

- It's the **#1 microservices interview question** after isolation.
- They want to see you **identify the dual-write problem** by name.
- They probe **delivery semantics** (at-least-once, ordering, idempotent consumers).
- They want **operational awareness** (drainer crashes, outbox bloat, CDC alternative).

## Common beginner confusion

- "Just publish to Kafka after commit." Network failure between commit and publish = lost event.
- "Use a Kafka transaction + DB transaction with XA." 2PC across heterogeneous systems is unreliable in practice; outbox is the accepted alternative.
- "Outbox guarantees exactly-once." It guarantees *at-least-once*; consumers must dedupe.
- "Just let the consumer poll the DB directly." Tight coupling, no fan-out, no replay; defeats the purpose of a message bus.

## Brute force approach

Publish to Kafka inside the transaction:

```python
with db.transaction():
    db.execute("UPDATE orders ...")
    kafka.publish("order.paid", ...)   # what if this hangs? what if it succeeds but the tx rolls back?
    db.execute(...)
```

Two failure modes: (1) Kafka call hangs → DB lock held forever; (2) Kafka publish succeeds but DB commits later fails → ghost event for a state that doesn't exist.

## Optimal approach

Transactional outbox:

1. **Business write + outbox row** in same DB transaction. Atomic.
2. **Drainer worker** polls outbox (or CDC streams WAL) and publishes to Kafka.
3. **Mark published** on success; row stays unpublished on failure (retry safe).
4. **Consumers idempotent** to handle at-least-once duplicates.
5. **Partitioning by aggregate_id** preserves order per aggregate.

## Solution

```sql
-- ============================================================
-- Schema
-- ============================================================
CREATE TABLE outbox (
  id           BIGSERIAL PRIMARY KEY,
  aggregate    TEXT NOT NULL,
  aggregate_id TEXT NOT NULL,
  event_type   TEXT NOT NULL,
  payload      JSONB NOT NULL,
  created_at   TIMESTAMPTZ DEFAULT now(),
  published_at TIMESTAMPTZ,
  attempts     INT DEFAULT 0
);
-- Partial index: only unpublished rows count for the drainer
CREATE INDEX outbox_unpublished ON outbox (id) WHERE published_at IS NULL;

-- ============================================================
-- Producer: atomic business + intent
-- ============================================================
BEGIN;
UPDATE orders SET status='PAID', paid_at=now() WHERE id=$1;
INSERT INTO outbox (aggregate, aggregate_id, event_type, payload)
VALUES ('order', $1::text, 'order.paid',
        jsonb_build_object('order_id', $1, 'amount', $2));
COMMIT;

-- ============================================================
-- Drainer: claim → publish → mark
-- ============================================================
-- (Run in a worker; multiple workers safe via SKIP LOCKED)
BEGIN;
WITH job AS (
  SELECT id, aggregate, aggregate_id, event_type, payload
  FROM outbox
  WHERE published_at IS NULL
  ORDER BY id
  LIMIT 100
  FOR UPDATE SKIP LOCKED
)
SELECT * FROM job;
-- (publish each event to Kafka here, in code)
UPDATE outbox SET published_at = now(), attempts = attempts + 1
WHERE id = ANY($1::bigint[]);   -- IDs of successfully published rows
COMMIT;
```

Node drainer:

```javascript
async function drainOnce() {
  return await db.tx(async tx => {
    const jobs = await tx.any(`
      SELECT id, aggregate, aggregate_id, event_type, payload
      FROM outbox
      WHERE published_at IS NULL
      ORDER BY id
      LIMIT 100
      FOR UPDATE SKIP LOCKED
    `);
    if (jobs.length === 0) return 0;

    const publishedIds = [];
    for (const j of jobs) {
      try {
        await kafka.produce({
          topic: `${j.aggregate}.events`,
          key: j.aggregate_id,          // partition by aggregate → in-order delivery
          value: JSON.stringify({ type: j.event_type, payload: j.payload, id: j.id }),
        });
        publishedIds.push(j.id);
      } catch (err) {
        // Leave unpublished; next drain cycle will retry
        console.error('publish failed', j.id, err.message);
      }
    }
    if (publishedIds.length > 0) {
      await tx.none(`
        UPDATE outbox SET published_at = now(), attempts = attempts + 1
        WHERE id = ANY($1::bigint[])
      `, [publishedIds]);
    }
    return publishedIds.length;
  });
}

// Loop
async function drainerLoop() {
  while (true) {
    const n = await drainOnce();
    if (n === 0) await sleep(1000);  // backoff when idle
  }
}
```

Janitor:

```sql
-- Hourly: delete published rows older than 7 days
DELETE FROM outbox WHERE published_at < now() - interval '7 days';
```

## Step-by-step dry run

Successful happy path:

```
time →

API:  |--POST /payments--|--BEGIN--|--UPDATE orders--|--INSERT outbox--|--COMMIT--|--HTTP 200--|
                                                       (atomic)
Drainer (1s later):
                                                                                  |--BEGIN--|--SELECT FOR UPDATE SKIP LOCKED--|--produce to Kafka OK--|--UPDATE published_at--|--COMMIT--|
Kafka:                                                                                                                          [order.paid event delivered]
Consumer:                                                                                                                                                 |--receive event--|--idempotent process--|
```

Drainer crashes mid-publish:

```
Drainer: |--BEGIN--|--SELECT 100 rows (X locks held)--|--produce rows 1-50 OK--|--CRASH before UPDATE--|
                                                                                                          ↓
The transaction rolls back; rows 1-50's `published_at` is NULL still.
On restart, the next drainer picks them up and re-publishes 1-50.
=> at-least-once delivery. Consumers must dedupe on the event id.
```

Dual-write bug (the wrong way):

```
API: |--BEGIN--|--UPDATE orders--|--COMMIT--|--call Kafka (network blip; LOST)--|--HTTP 200 to client--|
DB:  orders.status = 'PAID'
Kafka: nothing.
Consumer never learns. Inventory not decremented. Customer not notified.
```

Outbox prevents this by making the publish *intent* part of the committed state.

## How to think aloud in the interview

> "The dual-write problem: a transaction updates the DB and we want to publish a Kafka event. If we publish *after* commit, a network blip leaves the event lost. If we publish *before* commit, a tx rollback leaves a ghost event. The outbox pattern fixes both by writing the event *intent* into an `outbox` table inside the same transaction.
>
> A separate drainer worker polls outbox (or CDC streams WAL via Debezium), publishes to Kafka, and marks the row published. Multiple drainers safe via `FOR UPDATE SKIP LOCKED`. If the drainer crashes mid-publish, the row stays unpublished and the next cycle retries — at-least-once delivery. Consumers must be idempotent.
>
> Ordering: partition Kafka by aggregate_id so events for one order land on one partition in order. One drainer per partition keeps ordering tight.
>
> Operational concerns: outbox table grows; sweep published rows older than 7 days. Drainer lag: monitor `max(id) - max(id WHERE published_at IS NOT NULL)` as a gauge.
>
> Compared to 2PC: 2PC requires a coordinator and is fragile across heterogeneous systems; outbox is local DB only."

## Important takeaways

- Outbox pattern = business write + outbox row in the same DB transaction.
- Drainer publishes asynchronously; marks row published on success.
- `FOR UPDATE SKIP LOCKED` for concurrent drainers.
- **At-least-once** delivery; consumers must be idempotent.
- Partition by aggregate_id for ordering within an aggregate.
- Eliminates the dual-write problem.
- Alternative: CDC via Debezium streams WAL directly; more infra, lower latency.
- Sweep old published rows; monitor unpublished backlog.

## Variants

1. **CDC variant (Debezium)**: Debezium reads the WAL and streams to Kafka without a polling drainer. Lower latency, more ops complexity.
2. **Inbox pattern (consumer side)**: dedupe table on the consumer to enforce idempotency for at-least-once events.
3. **Outbox + sagas**: outbox enables the local commit of each saga step + event emission for orchestration/choreography.
4. **Kafka transactional producer**: Kafka has its own transactions for exactly-once *within Kafka*, but doesn't cover the DB write. Combine carefully or just use outbox.
5. **MySQL outbox**: same pattern; MySQL CDC via Debezium also works.
6. **Outbox vs event sourcing**: event sourcing makes the events the source of truth; outbox keeps the current-state table and emits events as side effects.

## Revision notes

> **transactional-outbox — 60 second recap**
> - Atomic business write + outbox row in one DB transaction.
> - Drainer polls (or CDC streams) outbox → publishes → marks published.
> - Multi-worker drainers via `FOR UPDATE SKIP LOCKED`.
> - At-least-once delivery; consumers must dedupe.
> - Partition by aggregate_id for in-order per aggregate.
> - Sweep published rows; monitor unpublished backlog.
> - Alternative: Debezium CDC (lower latency, more ops).
> - Solves the dual-write problem without 2PC.
> - Companion: inbox pattern on the consumer side.
