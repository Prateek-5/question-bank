# Transactional Outbox Pattern — Atomic Database Write + Message Publish

## Source / Origin
- Pattern named by Chris Richardson (`microservices.io/patterns/data/transactional-outbox.html`).
- Refined by Debezium and the change-data-capture (CDC) community.
- Companion: `inbox-pattern-idempotent-consumer.md` (the consumer-side dual to this).
- Interview prompt that lands you here: *"You're writing an order to Postgres and then publishing an `order_created` event to Kafka. What happens if the DB write succeeds but the Kafka publish fails?"*

## Why this question matters in interviews
The **dual-write problem** is the #1 correctness bug in event-driven microservices, and the transactional outbox is the canonical fix. If a senior candidate doesn't immediately recognize the dual-write hazard and reach for an outbox, the interviewer learns that they've never debugged an event-loss incident in production. Conversely, drawing the timeline of "DB committed, broker publish failed, downstream services are now inconsistent" wins immediate senior credibility. This is also the gateway to talking about CDC, Debezium, and event-driven architecture in general — a 30-minute conversation if you handle it well.

## Concepts involved

### Syntax to lock in

The naive dual-write that breaks:
```javascript
await db.transaction(async (tx) => {
  await tx.query('INSERT INTO orders ...');
});
await kafka.publish('orders', orderCreatedEvent);   // ← can fail independently
```

The outbox pattern in one shot:
```sql
-- Step 1: DB write + outbox row in ONE transaction
BEGIN;
INSERT INTO orders (id, user_id, amount, status) VALUES (...);
INSERT INTO outbox (id, aggregate_type, aggregate_id, event_type, payload, created_at)
                  VALUES (uuid(), 'order', :order_id, 'order_created', :json, now());
COMMIT;
-- atomically committed or atomically rolled back.

-- Step 2: a separate relay process polls outbox and publishes to Kafka
SELECT * FROM outbox WHERE published_at IS NULL ORDER BY created_at LIMIT 100;
-- for each row: kafka.publish(...) then UPDATE outbox SET published_at = now() WHERE id = ...
```

### Edge cases / interview traps

1. **The relay must be idempotent at the broker level.** It will sometimes publish then crash before marking `published_at`. On restart it republishes — that's why your consumers need idempotency too (see `inbox-pattern-idempotent-consumer.md`). Outbox + inbox is the full picture.
2. **Polling lag vs CDC.** Polling the outbox every 100ms is the simple form; for low latency, use Debezium to tail the Postgres WAL and stream outbox inserts directly to Kafka — eliminates the polling cycle.
3. **Outbox table grows forever.** Either delete published rows after a TTL or keep them with a partial index `WHERE published_at IS NULL`. The index keeps the relay query fast even if the table is huge.
4. **`SELECT FOR UPDATE SKIP LOCKED`** for multiple relay workers — otherwise two workers race to publish the same row and you get duplicates that consumers must dedupe.
5. **Event ordering within an aggregate.** Use the `aggregate_id` as the Kafka partition key so events for the same order land on the same partition and stay ordered.
6. **The relay is *not* the producer of the business event.** It's the *transport*. Don't put business logic in the relay.
7. **Schema versioning of the payload.** Stored as JSONB or binary in the outbox; consumers must handle multiple versions. See `schema-evolution-with-registry.md`.
8. **Transaction boundary mistake.** People sometimes commit the outbox insert in a separate transaction from the business write — which defeats the entire pattern. Both must be in the same `BEGIN`/`COMMIT`.

## Mental Model

The outbox is a **single source of truth that survives crashes**. Your business state and your intent-to-publish are committed together — there is no moment in time where the order exists but the event doesn't (or vice versa). The relay is then a *replayable*, *crash-safe* projection from outbox rows to broker messages.

Think of it like the **outgoing mail tray on a secretary's desk**: when you write a letter, you place it on the tray atomically with stapling it into your "letters sent" log. The courier picks up the tray at intervals. If the courier crashes mid-pickup, on restart they re-pickup whatever's still on the tray. Nothing is ever lost; some letters might be delivered twice; downstream offices have their own logbook to dedupe.

```
                          ┌─────────────────────┐
   App code               │   Same DB transaction
                          │  ┌───────────────┐  │
   business operation ────┼─▶│ orders row    │  │
                          │  │ (business)    │  │
                          │  ├───────────────┤  │
                          │  │ outbox row    │  │  ← intent to publish
                          │  │ (published=NULL│  │
                          │  └───────────────┘  │
                          └─────────────────────┘
                                    │
                                    │ COMMIT (atomic)
                                    ▼
                          ┌─────────────────────┐
                          │   Postgres WAL      │
                          └─────────────────────┘
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
              ┌──────────────┐         ┌──────────────────┐
              │  Polling     │  OR     │ Debezium / CDC   │
              │  relay       │         │ tails WAL        │
              └──────┬───────┘         └────────┬─────────┘
                     │                          │
                     └────────────┬─────────────┘
                                  ▼
                          ┌──────────────┐
                          │   Kafka      │
                          └──────────────┘
```

The atomicity boundary in red is the entire pattern. Everything else is delivery.

## Why interviewers care

- It exposes whether you've personally seen the dual-write problem fire in production.
- It tests **transactional reasoning across heterogeneous systems** (DB + broker).
- The follow-up "what if the relay crashes?" leads naturally into idempotency, CDC, and exactly-once-effect.
- It's a real architectural pattern that influences your data model — interviewers want to see if you can design a table that supports it.

## Common beginner confusion

- **"Use 2PC across DB and Kafka."** Kafka doesn't speak XA. Even if it did, 2PC is operationally horrendous and not what anyone uses. Outbox is the practical alternative.
- **"Publish first, write DB second."** Then you can publish events for a thing that doesn't exist. Worse than the other order.
- **"Use a try/catch and roll back the DB if the publish fails."** Doesn't survive process crash between the publish and the rollback. Plus your DB write may already have side-effects observed by other transactions.
- **"Outbox = retry the publish with backoff."** Retry alone helps when the broker is briefly down, but doesn't help when your process crashes mid-flight. Outbox makes the intent durable.
- **"Outbox is overkill — I'll just log errors and replay manually."** Manual replay is an operational nightmare at 3am. Outbox makes replay free and automatic.

## Brute force approach

Naive: publish to Kafka first, then write DB. Failure modes everywhere — Kafka receives the event, DB write fails, downstream services act on a phantom order.

Slightly less naive: write DB, then publish. Failure modes: DB committed, publish failed → silent inconsistency. Most production bugs of this shape ship to prod because the publish failure is rare *but not zero*.

Slightly less naive again: write DB, publish, on publish failure compensate by deleting the DB row. Doesn't survive process crashes; doesn't survive concurrent reads in the window between INSERT and DELETE; doesn't survive cascading reads.

## Optimal approach

1. **Write business state + outbox row in the same DB transaction.** Atomic intent.
2. **Run a relay** (polling or CDC) that publishes outbox rows to Kafka and marks them published.
3. **Idempotent consumers** to absorb the inevitable duplicates from relay re-runs.
4. **Garbage-collect** published outbox rows on a TTL or via partial-index strategy.
5. **Partition by aggregate_id** so per-aggregate ordering is preserved.

If you want the gold standard: replace the polling relay with Debezium streaming the WAL. Latency drops from 50-100ms (polling) to <10ms (CDC) and load on the DB drops significantly.

## Solution

### Outbox table

```sql
CREATE TABLE outbox (
  id              UUID PRIMARY KEY,
  aggregate_type  TEXT NOT NULL,           -- 'order', 'payment', 'user'
  aggregate_id    TEXT NOT NULL,           -- partition key for Kafka
  event_type      TEXT NOT NULL,           -- 'order_created', etc.
  payload         JSONB NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  published_at    TIMESTAMPTZ              -- null = not yet published
);

-- Partial index keeps the relay query fast even at billions of historical rows
CREATE INDEX outbox_unpublished_idx
  ON outbox (created_at) WHERE published_at IS NULL;
```

### Producer side — write business + outbox atomically

```javascript
async function createOrder(order) {
  await db.transaction(async (tx) => {
    await tx.query(
      'INSERT INTO orders (id, user_id, amount, status) VALUES ($1, $2, $3, $4)',
      [order.id, order.userId, order.amount, 'pending'],
    );
    await tx.query(
      `INSERT INTO outbox
        (id, aggregate_type, aggregate_id, event_type, payload)
       VALUES ($1, $2, $3, $4, $5::jsonb)`,
      [uuid(), 'order', order.id, 'order_created', JSON.stringify(order)],
    );
  });
  // No kafka.publish() here. Relay handles it.
}
```

### The polling relay

```javascript
async function relayLoop() {
  while (true) {
    const rows = await db.query(`
      SELECT id, aggregate_id, event_type, payload
      FROM outbox
      WHERE published_at IS NULL
      ORDER BY created_at
      LIMIT 100
      FOR UPDATE SKIP LOCKED
    `);

    for (const row of rows.rows) {
      await producer.send({
        topic: row.event_type,
        messages: [{
          key: row.aggregate_id,                  // ordering per aggregate
          value: JSON.stringify(row.payload),
          headers: { 'x-message-id': row.id },    // idempotency key for consumer
        }],
        acks: -1,
      });
      await db.query(
        'UPDATE outbox SET published_at = now() WHERE id = $1',
        [row.id],
      );
    }
    if (rows.rowCount === 0) await sleep(100);
  }
}
```

### Debezium / CDC variant (production-grade)

```yaml
# Debezium config snippet
"name": "outbox-connector",
"config": {
  "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
  "transforms": "outbox",
  "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
  "transforms.outbox.table.field.event.id": "id",
  "transforms.outbox.table.field.event.key": "aggregate_id",
  "transforms.outbox.table.field.event.type": "event_type",
  "transforms.outbox.table.field.event.payload": "payload",
  "transforms.outbox.route.topic.replacement": "${routedByValue}"
}
```

Debezium tails the WAL, sees the INSERT into `outbox`, routes by `event_type`, partitions by `aggregate_id`, and publishes — without ever polling the DB.

### GC for published rows

```sql
-- Run hourly
DELETE FROM outbox
WHERE published_at IS NOT NULL AND published_at < now() - INTERVAL '7 days';
```

## Step-by-step dry run

Crash scenario: relay publishes but dies before marking row.

```
T=0    User submits POST /orders
       App opens DB tx:
         INSERT orders (id=o-7, ...)
         INSERT outbox (id=ob-1, agg='o-7', type='order_created', payload=...)
       COMMIT  ← business + intent durable

T=10   Relay's next poll picks up outbox row ob-1.
       FOR UPDATE SKIP LOCKED claims it.

T=11   Relay calls kafka.publish(topic='order_created', key='o-7', value=...)
       Broker writes message; ack returned.

T=12   Relay process is OOM-killed BEFORE the UPDATE outbox SET published_at...
       Row ob-1 still has published_at = NULL.

T=20   Relay restarts.
       Next poll selects outbox rows with published_at IS NULL.
       ob-1 is in the result set again.

T=21   Relay publishes ob-1 to Kafka AGAIN.
       Broker writes a SECOND copy of the message at a new offset.

T=22   Relay updates: UPDATE outbox SET published_at = now() WHERE id = ob-1.

   Net: business state correct in DB. Two Kafka messages with header
        x-message-id = ob-1.
   Consumer dedupes by x-message-id (see inbox-pattern-idempotent-consumer.md).
   Final effect: exactly-once.
```

The outbox guarantees **no message is ever lost**. The consumer-side idempotency guarantees **no message is ever applied twice**. Together they form the at-least-once-delivery + idempotent-processing = exactly-once-effect story.

## How to think aloud in the interview

> "OK so the question is asking about the dual-write problem. Without thinking I'd write `INSERT INTO orders` and then `kafka.publish`, but those are two systems with two failure modes. The DB write could succeed and the Kafka publish could fail — now I have an order in my DB that nobody downstream knows about. Or the reverse: I publish first, the DB write fails, I've told the world about an order that doesn't exist.
>
> There's no distributed transaction that solves this between Postgres and Kafka. So the canonical pattern is the **transactional outbox**: I put an `outbox` table in the same database, and inside my business transaction I insert *both* the order row *and* an outbox row. They commit atomically. There is no moment where one exists and not the other.
>
> Then a separate relay process polls the outbox, publishes each row to Kafka, and marks it published. The relay can crash, double-publish, or lag — all fine, because the consumer is idempotent on the `x-message-id` header I put in each outbox row.
>
> For low latency I'd skip the polling relay and use Debezium to tail the Postgres WAL — every outbox INSERT becomes a Kafka message within a few milliseconds, without putting load on the DB. I'd partition by aggregate_id so events for the same order stay in order, and I'd GC published rows on a TTL to keep the table small.
>
> Common mistakes I'd flag: people sometimes put the outbox insert in a separate transaction, which kills the pattern. And people forget that the relay is at-least-once — consumer idempotency is mandatory."

## Important takeaways

- **Dual-write problem:** DB write + broker publish can't be made atomic without a single source of truth.
- **Outbox:** put the publish-intent in a DB table inside the same business transaction.
- **Relay:** separate process polls or CDC-tails the outbox and publishes to broker.
- **Outbox is at-least-once.** Consumers must be idempotent.
- **Partition key = aggregate_id** for per-aggregate ordering.
- **Debezium > polling** for production deployments — lower latency, lower DB load.
- **GC published rows** on a TTL (e.g., 7 days) — keep the table fast.
- **Partial index** on `published_at IS NULL` keeps the relay query O(unpublished).

## Variants

1. **Polling relay** — simplest, ~100ms latency, OK for non-realtime systems.
2. **Debezium CDC relay** — production gold standard, single-digit ms latency, near-zero DB load.
3. **Outbox + inbox combo** — outbox on producer side, inbox on consumer side. Closes the loop on exactly-once-effect.
4. **Single-table outbox (no separate `published_at`)** — delete-after-publish; simpler but loses replay history.
5. **Multi-topic routing from one outbox table** — use `event_type` to route to different Kafka topics (Debezium's `EventRouter` SMT).
6. **Outbox with TX log piggybacking** — instead of a separate table, use the DB's binlog / WAL directly (full CDC, no application-level outbox). Riskier — couples business code to physical storage format.
7. **Avro / Protobuf payload in outbox.** Store binary-encoded payload to match schema-registry expectations on the broker side.

## Revision notes

> **transactional outbox — 60 second recap**
> - **Problem:** dual-write (DB + broker) can't be atomic. Either order, you can lose or fabricate events.
> - **Fix:** insert business row + outbox row in *the same DB transaction*. Atomic intent.
> - **Relay:** separate process publishes outbox rows to broker, then marks them published.
> - **Partial index** on `published_at IS NULL` keeps relay queries fast.
> - **FOR UPDATE SKIP LOCKED** lets multiple relay workers parallelize without duplicating.
> - **At-least-once delivery** — consumer must be idempotent (inbox pattern dual).
> - **Debezium** is the production-grade relay — tails Postgres WAL, no polling.
> - **Partition key = aggregate_id** for per-aggregate ordering.
> - **Trap:** outbox insert in a separate tx = pattern broken.
> - **Trap:** forgetting to GC the outbox table.
