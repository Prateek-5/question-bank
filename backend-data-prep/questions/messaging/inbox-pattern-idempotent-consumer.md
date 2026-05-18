# Inbox Pattern — Idempotent Consumer with a Dedupe Table

## Source / Origin
- Companion pattern to the transactional outbox; coined in event-driven microservices literature (Microsoft Cloud Patterns, Chris Richardson).
- Closely related to the database "ledger" pattern and "deferred commit" pattern.
- Reference within this bank: `at-least-once-vs-exactly-once.md`, `transactional-outbox.md`.
- Stock prompt: *"Your consumer crashed after applying a wallet credit but before committing the Kafka offset. The broker redelivers. How do you stop the double credit?"*

## Why this question matters in interviews
This is the **consumer-side mirror** of the outbox question, and where most candidates lose points by either (a) saying "use exactly-once delivery" (which doesn't exist outside Kafka EOS) or (b) describing an idempotency check *outside* the DB transaction (racy, broken). Senior signal: candidate immediately reaches for an inbox table, puts the dedupe check + business effect in one DB transaction, and discusses TTL/GC of the inbox. This question is also the place where interviewers test whether you understand the difference between *processed_messages* (lightweight dedupe table) and *inbox* (full store-and-forward pattern).

## Concepts involved

### Syntax to lock in

The canonical inbox-pattern consumer:
```python
def handle(msg):
    msg_id = msg.headers["x-message-id"]
    with db.transaction() as tx:
        inserted = tx.execute(
            "INSERT INTO inbox (message_id, payload, received_at)"
            " VALUES (%s, %s, now())"
            " ON CONFLICT (message_id) DO NOTHING",
            (msg_id, msg.payload),
        )
        if inserted.rowcount == 0:
            return                         # duplicate; ack and move on
        apply_business_effect(tx, msg.payload)
        # both rows commit together
    broker.ack(msg)
```

Two related styles:

```
LIGHTWEIGHT (most common):
  one table `processed_messages(message_id PK, processed_at)`.
  Check + insert in same tx as business effect.

FULL INBOX (store-and-forward):
  one table `inbox(message_id PK, payload, received_at, processed_at)`.
  Receiver thread: write payload to inbox, ack broker immediately.
  Worker thread: pick unprocessed inbox rows, apply effect, mark processed_at.
```

### Edge cases / interview traps

1. **Check-then-insert in two statements is a race.** Use `INSERT ... ON CONFLICT DO NOTHING` (Postgres) or `INSERT IGNORE` (MySQL). Two consumer threads receiving the same redelivered message must not both pass the check.
2. **The dedupe insert and the business effect must be in the same DB transaction.** Otherwise you can crash between them and lose the effect or duplicate it.
3. **Idempotency key must be producer-assigned**, not consumer-generated. `(topic, partition, offset)` survives broker redeliveries but not producer retries that get new offsets.
4. **Foreign-key cascades.** If the inbox table is on a different DB from the business tables, you can't put them in one transaction. Co-locate them or accept a small race window.
5. **Inbox table grows forever.** TTL + GC job. Size to (max replay window × safety factor). 30 days is typical.
6. **Replay safety.** If you intentionally replay a Kafka topic (recovery / re-process), the inbox will skip every message — defeating the replay. Provide a "replay mode" that bypasses the inbox check (and clears the inbox first).
7. **Two consumer groups, one inbox?** Don't share the inbox table between consumer groups. Each consumer-group's effects are separate; each needs its own inbox (or a composite key `(consumer_group, message_id)`).
8. **Inbox + outbox composition.** A consumer that itself publishes events should write to *its own* outbox inside the same transaction as the inbox insert — chaining the exactly-once-effect.

## Mental Model

The inbox is the **bouncer's clipboard**. Every guest who shows up gets their ID checked against the list. If the name is already there ("we already let you in"), the bouncer politely sends them away. If not, the bouncer writes the name down *and* opens the door — both happen as one atomic action.

The subtlety: the bouncer can't "check then write" in two steps, because a twin showing up at the same time might pass the check before the first one writes. The check-and-write must be a single primitive — `INSERT ON CONFLICT`.

```
                  ┌──────────────────────────────────────┐
   broker ──msg──▶│  Consumer                            │
                  │                                      │
                  │  BEGIN tx                            │
                  │    INSERT inbox(msg_id) ON CONFLICT  │
                  │      ↓                               │
                  │    if conflict → skip business       │
                  │    else        → apply business      │
                  │  COMMIT                              │
                  │                                      │
                  │  ack(msg) ────────────────────────▶  broker
                  └──────────────────────────────────────┘

   Duplicate delivery? Second time through:
   - INSERT inbox(msg_id) → conflict (already present)
   - Skip business effect, ack and move on.
   - Net: effect applied exactly once.
```

```
   Variant: full inbox (store-and-forward)

                  ┌─────────────────────────────────────┐
   broker ──msg──▶│  Receiver thread                    │
                  │    INSERT inbox(msg_id, payload)    │
                  │    ack(broker)         ←─ fast      │
                  └─────────────────────────────────────┘
                                  │
                                  ▼
                  ┌─────────────────────────────────────┐
                  │  Worker thread (pulls inbox rows)   │
                  │    BEGIN tx                         │
                  │      apply business effect          │
                  │      UPDATE inbox SET processed_at  │
                  │    COMMIT                           │
                  └─────────────────────────────────────┘
```

## Why interviewers care

- Tests whether you understand **race-free dedupe** vs naive check-then-act.
- Closes the loop on exactly-once-effect — pairs cleanly with the outbox pattern.
- Forces explicit reasoning about **transaction boundaries across broker + DB**.
- Real systems break here all the time — interviewers from Stripe, Square, etc. have personally debugged this.

## Common beginner confusion

- **"Just check if the message_id exists, then apply the effect."** Race condition: two threads can both pass the check before either inserts.
- **"Use a unique index on message_id and catch the duplicate-key error."** Works, but the business effect has already partially run. You have to wrap both in a transaction so the failed INSERT rolls back the effect too.
- **"Use Kafka's commit-once-after-processing as the dedupe."** That's the **delivery-side** guarantee (you process before committing offset). It doesn't survive broker redeliveries of the same offset to a different consumer in the group after rebalance.
- **"Dedupe in Redis."** Risky — Redis is not always consistent with the DB. If Redis says "new" but the DB tx fails, you're stuck. Use the DB.
- **"Use UPSERT on the business table itself instead of an inbox."** Sometimes valid (e.g., `INSERT ... ON CONFLICT (id) DO NOTHING` directly on the entity table). Works only when the business effect is itself idempotent at the row level. Falls apart for additive effects like "credit wallet by $50" — two `UPDATE wallets SET balance = balance + 50` is still a double credit.

## Brute force approach

Naive: "I'll do `SELECT 1 FROM processed_messages WHERE id = ?`, and if not present, apply the effect and `INSERT`."

Failure: two consumer threads pull the same redelivered message simultaneously. Both `SELECT`, both see "not present", both apply the effect, both `INSERT` (the second `INSERT` errors but the effect is already double-applied).

Slightly less naive: wrap in a transaction. Still broken under `READ COMMITTED` isolation because the second tx's `SELECT` runs after the first tx's `INSERT` but before its `COMMIT` — sees nothing — falls into the same trap.

The race window only closes when (a) the INSERT is the dedupe check itself (via `ON CONFLICT DO NOTHING`), or (b) the isolation level is `SERIALIZABLE` and you accept the retry storm.

## Optimal approach

1. **Use the database as the source of truth for "have I processed this?"** Not Redis, not in-memory, not Kafka offsets.
2. **`INSERT ... ON CONFLICT (message_id) DO NOTHING`** as the dedupe primitive. Returns row count = 0 for duplicates.
3. **Same transaction** for dedupe insert + business effect.
4. **Commit broker offset after DB commit succeeds**, not before.
5. **TTL/GC** the inbox table.
6. **Producer-assigned message_id** in a known header location.

For high-throughput consumers where the business effect is expensive to roll back, switch to the **full inbox pattern**: receiver thread acks the broker immediately after persisting to inbox; worker thread applies effects asynchronously. Decouples broker acks from business processing latency.

## Solution

### Lightweight (`processed_messages` table)

```sql
CREATE TABLE processed_messages (
  message_id   UUID PRIMARY KEY,
  consumer     TEXT NOT NULL,        -- which consumer group processed it
  processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON processed_messages (processed_at);
```

```javascript
const consumer = kafka.consumer({ groupId: 'wallet-credit' });

await consumer.run({
  autoCommit: false,
  eachMessage: async ({ topic, partition, message }) => {
    const msgId = message.headers['x-message-id'].toString();
    const payload = JSON.parse(message.value.toString());

    const isNew = await db.transaction(async (tx) => {
      const res = await tx.query(
        `INSERT INTO processed_messages (message_id, consumer)
         VALUES ($1, $2) ON CONFLICT DO NOTHING`,
        [msgId, 'wallet-credit'],
      );
      if (res.rowCount === 0) return false;       // duplicate

      await tx.query(
        'UPDATE wallets SET balance = balance + $1 WHERE user_id = $2',
        [payload.amount, payload.userId],
      );
      return true;
    });

    // Commit offset regardless — duplicate or not, we're done with this msg.
    await consumer.commitOffsets([{
      topic, partition, offset: (Number(message.offset) + 1).toString(),
    }]);
  },
});
```

### Full inbox (store-and-forward)

```sql
CREATE TABLE inbox (
  message_id   UUID PRIMARY KEY,
  topic        TEXT NOT NULL,
  payload      JSONB NOT NULL,
  received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at TIMESTAMPTZ
);
CREATE INDEX inbox_unprocessed_idx
  ON inbox (received_at) WHERE processed_at IS NULL;
```

Receiver:
```javascript
await consumer.run({
  autoCommit: false,
  eachMessage: async ({ topic, partition, message }) => {
    const msgId = message.headers['x-message-id'].toString();
    const inserted = await db.query(
      `INSERT INTO inbox (message_id, topic, payload)
       VALUES ($1, $2, $3::jsonb) ON CONFLICT DO NOTHING`,
      [msgId, topic, message.value.toString()],
    );
    // Ack regardless — duplicate is already in inbox or skipped.
    await consumer.commitOffsets([{ topic, partition,
      offset: (Number(message.offset) + 1).toString() }]);
  },
});
```

Worker:
```javascript
async function workerLoop() {
  while (true) {
    const rows = await db.query(`
      SELECT message_id, payload FROM inbox
      WHERE processed_at IS NULL
      ORDER BY received_at
      LIMIT 100 FOR UPDATE SKIP LOCKED
    `);
    for (const row of rows.rows) {
      await db.transaction(async (tx) => {
        await applyBusinessEffect(tx, row.payload);
        await tx.query(
          'UPDATE inbox SET processed_at = now() WHERE message_id = $1',
          [row.message_id],
        );
      });
    }
    if (rows.rowCount === 0) await sleep(100);
  }
}
```

### GC

```sql
-- nightly
DELETE FROM processed_messages WHERE processed_at < now() - INTERVAL '30 days';
DELETE FROM inbox WHERE processed_at IS NOT NULL AND processed_at < now() - INTERVAL '7 days';
```

## Step-by-step dry run

Scenario: two consumer instances (a rebalance is in progress) both receive the same message m-A.

```
T=0   Consumer A polls offset 1042. Message m-A (msgId='m-A', credit $50).
T=1   Consumer B (after rebalance) also gets offset 1042 briefly.

T=2   Both start eachMessage handlers concurrently.

      Consumer A                        Consumer B
      ──────────                        ──────────
      BEGIN tx                          BEGIN tx
      INSERT processed_messages         INSERT processed_messages
        ('m-A', 'wallet') ON CONFLICT     ('m-A', 'wallet') ON CONFLICT
      rowCount=1 (winner)               (waits on row lock OR returns rowCount=0)

      UPDATE wallets +50
      COMMIT  ← wallet credited

                                        BEGIN tx (or continues)
                                        INSERT processed_messages('m-A')
                                          ON CONFLICT DO NOTHING
                                        rowCount = 0 (already there)
                                        SKIP credit
                                        COMMIT (no business effect)

      commitOffsets(1043)               commitOffsets(1043)
```

Result: one credit applied, both consumers cleanly ack. The race is closed by the primary-key on `message_id` and the `ON CONFLICT DO NOTHING` semantics.

Compare with naive check-then-insert:

```
T=2   A: SELECT msg_id='m-A' → 0 rows.    B: SELECT msg_id='m-A' → 0 rows.
T=3   A: UPDATE wallets +50.              B: UPDATE wallets +50.
T=4   A: INSERT processed_messages.       B: INSERT processed_messages → unique violation.
T=5   A: COMMIT. B catches the violation and rolls back — but its UPDATE already changed the row in its own tx, which now also rolls back.
                                          (If row-locking didn't serialize them, both updates compound.)
```

Without `ON CONFLICT` semantics being atomic with the update, the race opens. With it, the race is structurally impossible.

## How to think aloud in the interview

> "OK, my consumer crashed mid-processing and Kafka is going to redeliver. I need the wallet credit to apply exactly once even though the message arrives twice. This is the inbox / idempotent-consumer pattern.
>
> The producer needs to put a stable `message_id` in every event — a UUID or a business key, *not* something like the Kafka offset, because retries can land at new offsets. I'll assume that's in a header called `x-message-id`.
>
> On the consumer side I'll create a table `processed_messages(message_id PK, processed_at)`. Every message handler does its work in a DB transaction:
> 1. `INSERT INTO processed_messages (message_id) VALUES (...) ON CONFLICT DO NOTHING`.
> 2. If `rowCount` is zero, this is a duplicate — skip the business effect, ack the broker, done.
> 3. Otherwise, apply the wallet update inside the same transaction.
> 4. COMMIT.
> 5. Commit the Kafka offset *after* the DB commit succeeds.
>
> The key insight is that the dedupe insert and the business effect are in **one DB transaction**. If the consumer crashes between steps, both roll back, and on redelivery we try again from scratch.
>
> If the business effect is expensive — say, a 200ms downstream API call — I'd switch to the **full inbox pattern**: receiver thread acks the broker immediately after persisting to the inbox table; a worker thread asynchronously drains the inbox and applies effects. That decouples broker SLA from processing SLA.
>
> Gotchas I'd flag: I need to TTL the inbox to keep it small; I need to plan for replay mode that bypasses it; and the message_id must be producer-assigned, not derived from broker metadata."

## Important takeaways

- **Inbox = consumer-side dedupe + transactional application.**
- **Primary key on `message_id`** + `INSERT ON CONFLICT DO NOTHING` = race-free dedupe.
- **Dedupe insert and business effect must share one DB transaction.**
- **Producer-assigned message_id** is mandatory.
- **Commit broker offset after DB commit**, never before.
- **TTL** the inbox/processed_messages table.
- **Full inbox** decouples broker-ack from business-processing latency.
- **Replay mode** must bypass the inbox.
- **Pairs with the outbox** to form the full at-least-once + idempotent = exactly-once-effect story.

## Variants

1. **Lightweight (processed_messages):** one tiny table, dedupe only. Best when the business effect runs synchronously.
2. **Full inbox (store-and-forward):** receiver writes to inbox + acks broker; worker processes asynchronously. Best for high-throughput or slow downstreams.
3. **Per-consumer-group inbox.** Composite key `(consumer_group, message_id)` if multiple groups share a table.
4. **Inbox + outbox composition.** Consumer that re-emits events writes its own outbox row in the same tx as the inbox insert. Chains exactly-once-effect across services.
5. **Sequence-number variant.** `last_seen_sequence` per `(aggregate_id, consumer)` — reject any sequence ≤ last seen. Works only when producer guarantees monotonic sequences.
6. **Materialized-view dedupe.** UPSERT on the business table itself, keyed by message_id stored as a column. Works only when the effect is row-idempotent.

## Revision notes

> **inbox pattern / idempotent consumer — 60 second recap**
> - **Problem:** broker redelivers → consumer applies effect twice.
> - **Fix:** `INSERT processed_messages(message_id) ON CONFLICT DO NOTHING` + business effect in *one* DB tx.
> - **Same tx is non-negotiable.** Otherwise race or crash split.
> - **Producer-assigned message_id** in a header. Never derive from broker offset.
> - **Commit offset after DB commit.** Process-then-commit, accept duplicates.
> - **Full inbox** for store-and-forward: receiver acks fast, worker processes lazily.
> - **TTL** the table (e.g., 30 days).
> - **Replay mode** must bypass the dedupe table.
> - **Outbox + inbox = exactly-once-effect** end-to-end.
> - **Trap:** check-then-insert (race). **Trap:** dedupe outside the tx (split).
