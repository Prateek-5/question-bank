# At-Least-Once vs Exactly-Once Delivery — and Why "Exactly Once" Is a Myth Without Idempotency

## Source / Origin
- Classic distributed-systems trap question. Appears on every senior backend rubric (Confluent, Stripe, Uber, Atlassian).
- Foundational reading: Tyler Treat — "You Cannot Have Exactly-Once Delivery" (2015); Kafka's "Exactly Once Semantics" KIP-98 design doc.
- Companion files in this bank: `inbox-pattern-idempotent-consumer.md`, `transactional-outbox.md`, `delivery-semantics-comparison.md`.
- Stock interview prompt: *"Your payment service publishes a `charge_succeeded` event to Kafka. The consumer credits the user wallet. How do you guarantee each charge credits the wallet exactly once?"*

## Why this question matters in interviews
This is the **litmus test** for messaging maturity. A mid-level candidate says "use exactly-once delivery." A senior candidate says "there is no such thing as exactly-once delivery on the wire — only at-least-once + idempotent processing, which together produce exactly-once *effect*." The interviewer is probing whether you understand the Two Generals' Problem at a practical level, whether you've actually shipped systems that survive consumer crashes, and whether you can recognize the marketing-vs-reality gap in Kafka's "EOS" feature.

Get this wrong and the interviewer mentally drops you to mid-level. Get it right with a clean "delivery vs processing" split and a working idempotency story and you've earned 20 minutes of senior-bar runway.

## Concepts involved

### Syntax to lock in

The three delivery semantics in code-level terms:

```
at-most-once  :  send → forget. No retry on failure. Lose messages on crash.
                 producer.send(msg)  // no ack wait, no retry

at-least-once :  send → wait for ack → retry on no-ack. Possible duplicates.
                 producer.send(msg, ack='all', retries=Infinity)

exactly-once  :  at-least-once delivery + idempotent consumer.
                 (or Kafka EOS within Kafka-to-Kafka pipelines only)
```

Kafka producer settings that matter:
```properties
acks=all                    # wait for ISR replication
retries=2147483647          # retry forever on retriable errors
enable.idempotence=true     # producer-side dedupe via producerId+sequenceNumber
max.in.flight.requests.per.connection=5   # required ≤5 with idempotence
transactional.id=...        # opt-in to transactions (EOS within Kafka)
```

Consumer-side idempotency skeleton (the only real "exactly once"):
```python
def handle(msg):
    msg_id = msg.headers["x-message-id"]
    with db.transaction():
        if db.exists("processed_messages", msg_id):
            return                         # already processed, ack and move on
        apply_business_effect(msg)
        db.insert("processed_messages", msg_id, now())
    # ack only after commit succeeds
    consumer.commit(msg.offset)
```

### Edge cases / interview traps

1. **"Kafka has exactly-once" is half-true.** Kafka EOS gives you exactly-once *within a Kafka-to-Kafka pipeline* (consume from topic A, write to topic B + commit offsets atomically). The moment your consumer writes to Postgres or calls a third-party API, EOS doesn't help you — you need idempotency.
2. **At-most-once is almost never what you want.** It's only acceptable for metrics, telemetry, ephemeral notifications where loss is cheaper than duplication.
3. **Duplicates are unavoidable in at-least-once.** Network partition between consumer and broker → consumer processes msg → tries to ack → ack times out → broker re-delivers → second consume.
4. **Idempotency key must be in the payload, not generated on receive.** If you key by `(topic, partition, offset)` you survive Kafka redeliveries but not producer-side retries that create new offsets. Key by a business ID embedded by the producer.
5. **"Exactly once" with HTTP downstream**: idempotency key in header (Stripe-style `Idempotency-Key`). Stripe survives this by storing the response keyed by your idempotency key.
6. **Two Generals' Problem.** It is mathematically impossible to guarantee both sides know a single message was delivered exactly once over a lossy channel without acks → which themselves can be lost. Production systems sidestep this with idempotency.
7. **Commit-then-process vs process-then-commit.** Commit first → at-most-once (crash before processing = lost message). Process first → at-least-once (crash after processing but before commit = re-delivery). You choose between data loss and duplicates — the duplicate path is almost always the right pick.
8. **Idempotency table TTL.** You can't keep `processed_messages` forever. Use a TTL of (max retry window × safety factor) — typically 7-30 days.

## Mental Model

Think of messaging as **the postal system**, not the telegram. A telegram (in your head) goes once or doesn't. A real postal letter:

- Gets resent if the postman's truck crashes (retry).
- Sometimes arrives twice if the sorting machine duplicates it (duplicate).
- Has a tracking number on the envelope (message_id).
- The recipient writes "received" in a logbook keyed by tracking number (idempotency table).
- If a duplicate letter arrives, the recipient looks it up in the logbook, sees they already filed it, and throws the duplicate away.

That's exactly-once *processing*, achieved on top of at-least-once *delivery*.

```
   PRODUCER                 BROKER                CONSUMER
      │                       │                      │
      │── publish(msg, id=42)─▶│                      │
      │                       │── deliver msg id=42 ──▶│
      │                       │                      │── process msg ──▶ DB tx:
      │                       │                      │                     INSERT processed(42)
      │                       │                      │                     apply effect
      │                       │                      │                     COMMIT
      │                       │◀── ack offset N ─────│
      │                       │                      │
      │                       │── deliver msg id=42 ──▶│  (retry after ack timeout)
      │                       │                      │── process msg ──▶ DB tx:
      │                       │                      │                     SELECT processed(42) ✓ EXISTS
      │                       │                      │                     SKIP effect
      │                       │                      │                     COMMIT
      │                       │◀── ack offset N ─────│
```

The duplicate arrived. The effect was applied once. Exactly-once *effect* on top of at-least-once *delivery*.

## Why interviewers care

- Tests whether you understand that **wire-level guarantees ≠ business-level guarantees**.
- Forces you to choose between data loss and duplicates explicitly — most candidates avoid the choice.
- Opens the door to **idempotency, the inbox pattern, transactional outbox, Kafka EOS internals** — the next 30 minutes of the interview.
- Stripe, PayPal, Square, every payment gateway built their reputation on getting this right; interviewers from those companies will absolutely ask.

## Common beginner confusion

- **"Kafka EOS solves this."** No — it solves the Kafka-to-Kafka case only. Your business effect (DB write, API call, email send) is outside EOS scope.
- **"At-least-once is bad."** It's the *correct default*. Duplicates are cheap to handle (idempotency); loss is catastrophic.
- **"Exactly-once is a delivery property."** It's a *processing* property in real systems. Delivery is at-least-once; processing is made idempotent.
- **"If I use transactions everywhere I get exactly-once for free."** Only if your transaction spans both the message-processing record *and* the business effect in the same atomic unit. Cross-system transactions don't exist in practice — that's what the inbox pattern is for.
- **"Why not just use TCP?"** TCP gives you in-order, no-duplicate delivery on a *single connection*. The moment the connection drops and the application reconnects, TCP can't tell whether the last message was delivered. The duplicate-possible window is at the application layer, not the transport.

## Brute force approach

"Set `acks=all`, retry forever, and trust the broker." This gets you durable at-least-once and is honestly fine for ~80% of business workloads — as long as your consumer is idempotent. The brute force here is *skipping idempotency* and hoping duplicates don't happen. They will. On the day they do, it's a Stripe/PayPal-grade outage.

## Optimal approach

1. **Pick at-least-once delivery.** It's the only honest semantic. Configure `acks=all`, `retries=Inf`, enable producer idempotence to avoid producer-retry-induced duplicates.
2. **Make the consumer idempotent.** Every business effect is keyed by a producer-assigned `message_id` (UUID, business key, or `(aggregate_id, sequence_number)`). Maintain a `processed_messages` table; insert before applying effect, both in the same DB transaction.
3. **Choose process-then-commit ordering.** Process the message first, then commit the offset. On crash mid-processing you'll redeliver; idempotency handles the dupe.
4. **Add a TTL** on the idempotency table sized to your max retry/replay window.
5. **Don't promise exactly-once delivery to downstream consumers.** Promise idempotent processing and let them dedupe too (defense in depth).

## Solution

### Producer side (Node.js / kafkajs)

```javascript
const { Kafka } = require('kafkajs');
const { v4: uuid } = require('uuid');

const kafka = new Kafka({
  clientId: 'payments-api',
  brokers: ['broker-1:9092', 'broker-2:9092'],
});

const producer = kafka.producer({
  idempotent: true,        // producer-side dedupe (producerId + seq #)
  maxInFlightRequests: 5,  // required ≤ 5 with idempotent
  retry: { retries: Number.MAX_SAFE_INTEGER },
});

async function publishCharge(charge) {
  const messageId = uuid();   // stable id, embedded in payload
  await producer.send({
    topic: 'charges',
    acks: -1,                 // -1 == acks=all
    messages: [{
      key: charge.userId,     // partition key for ordering per user
      value: JSON.stringify(charge),
      headers: { 'x-message-id': messageId },
    }],
  });
  return messageId;
}
```

### Consumer side (idempotent — the real exactly-once)

```javascript
const consumer = kafka.consumer({ groupId: 'wallet-credit-worker' });

await consumer.run({
  autoCommit: false,        // commit only after DB tx succeeds
  eachMessage: async ({ topic, partition, message }) => {
    const msgId = message.headers['x-message-id'].toString();
    const payload = JSON.parse(message.value.toString());

    await db.transaction(async (tx) => {
      const seen = await tx.query(
        'SELECT 1 FROM processed_messages WHERE message_id = $1',
        [msgId],
      );
      if (seen.rowCount > 0) return;        // dedupe: already applied

      await tx.query(
        'INSERT INTO processed_messages(message_id, processed_at) VALUES ($1, now())',
        [msgId],
      );
      await tx.query(
        'UPDATE wallets SET balance = balance + $1 WHERE user_id = $2',
        [payload.amount, payload.userId],
      );
    });

    await consumer.commitOffsets([{
      topic, partition, offset: (Number(message.offset) + 1).toString(),
    }]);
  },
});
```

### The processed_messages table

```sql
CREATE TABLE processed_messages (
  message_id   UUID PRIMARY KEY,
  processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON processed_messages (processed_at);

-- nightly job
DELETE FROM processed_messages WHERE processed_at < now() - INTERVAL '30 days';
```

## Step-by-step dry run

Scenario: $50 charge → wallet credit. Network blip causes consumer to crash after applying credit but before committing offset.

```
T=0      Producer.send({userId:'u1', amount:50, messageId:'m-A'})
         ─────────────────────────────────────────────────────────
         broker writes msg at (topic=charges, p=3, offset=1042)
         ack returned to producer.

T=10     Consumer polls partition 3, gets offset 1042.
         BEGIN DB TX
           SELECT 1 FROM processed_messages WHERE message_id='m-A'  → 0 rows
           INSERT processed_messages('m-A', now())
           UPDATE wallets SET balance = balance + 50 WHERE user_id='u1'
         COMMIT  ← wallet now $50 higher; processed_messages has m-A
T=20     Consumer crashes BEFORE calling commitOffsets.

T=30     Consumer restarts. Group coordinator reassigns partition 3.
         Last committed offset for this consumer-group on p=3: 1041.
         Broker redelivers offset 1042 (the same message m-A).

T=35     BEGIN DB TX
           SELECT 1 FROM processed_messages WHERE message_id='m-A'  → 1 row ✓
           RETURN (skip effect)
         COMMIT
         consumer.commitOffsets([{p:3, offset:1043}])  ← now committed
         Wallet balance: still $50 higher. No double credit.
```

Without the idempotency check, the wallet would have been credited twice ($100 instead of $50). That single line — `SELECT 1 FROM processed_messages` — is the entire difference between "we lost a customer's trust" and "we shipped a correct system."

## How to think aloud in the interview

> "Right, before I answer 'how do we guarantee exactly-once', I want to make a distinction that always trips people up: there is no such thing as exactly-once delivery on the wire. The Two Generals' Problem says you can't both send and confirm receipt over an unreliable channel without acks-of-acks ad infinitum. What we *can* do is **at-least-once delivery plus idempotent processing**, which gives the user-visible effect of exactly-once.
>
> So my answer is: I'd configure the producer for at-least-once with `acks=all`, infinite retries, and enable Kafka's producer-side idempotence so retries during a broker reconnect don't get duplicated. On the consumer, I'd assign every message a stable `message_id` at publish time — embedded as a header — and on the consumer side maintain a `processed_messages` table. The consumer's transaction would (a) check whether the `message_id` is already there, (b) apply the business effect, (c) insert the `message_id` — all in one DB transaction. Only after that commits do I commit the Kafka offset.
>
> One gotcha: Kafka EOS is real, but only within Kafka-to-Kafka pipelines — it commits offsets and writes to output topics atomically. The moment my consumer writes to Postgres or calls a third-party API, EOS doesn't span that boundary; I'm back to needing idempotency.
>
> If the interviewer pushed: I'd talk about choosing the `message_id` key carefully — must be producer-assigned, must survive producer retries — and the TTL on the dedupe table sized to my replay window."

## Important takeaways

- **There is no exactly-once delivery.** There is at-least-once delivery + idempotent processing.
- **At-least-once is the default for any system you care about.** Loss is catastrophic; duplicates are cheap.
- **Idempotency requires a stable, producer-assigned message_id.** Not `(topic, partition, offset)`.
- **The idempotency check and the business effect must be in the same DB transaction.** Otherwise you have a TOCTOU race.
- **Commit offsets after the DB commit, not before.** Process-then-commit, accept duplicates on crash.
- **Kafka EOS = Kafka-to-Kafka only.** Doesn't extend to external systems.
- **Stripe-style idempotency keys** are the same pattern at the HTTP layer.

## Variants

1. **Idempotency at the HTTP layer (Stripe pattern).** Client sends `Idempotency-Key` header; server stores response keyed by it; repeated requests return the original response. Same pattern, different transport.
2. **Sequence-number idempotency.** Producer attaches `(aggregate_id, sequence_number)`; consumer rejects out-of-order or duplicate sequences. Used by event-sourced systems and CRDTs.
3. **Inbox pattern.** Persist incoming message to an `inbox` table first, ack the broker, then process from the inbox in a separate worker. Decouples broker-ack from business-effect timing. See `inbox-pattern-idempotent-consumer.md`.
4. **Outbox pattern (producer-side dual-write fix).** Atomic DB+message via a single transaction writing to an `outbox` table; a relay publishes from outbox to broker. See `transactional-outbox.md`.
5. **Read-your-writes idempotency.** Some APIs let you do `INSERT … ON CONFLICT DO NOTHING RETURNING id` — the absence of returned id tells you it's a dupe.
6. **At-most-once for telemetry.** Skip retries, accept loss, prefer freshness. Valid for metrics, click streams, log shipping.

## Revision notes

> **at-least-once vs exactly-once — 60 second recap**
> - **Three semantics:** at-most-once (drop), at-least-once (retry → dupes), "exactly-once" (only via idempotency).
> - **Exactly-once delivery is impossible** (Two Generals). Achievable: at-least-once + idempotent processing = exactly-once *effect*.
> - **Producer config:** `acks=all`, `retries=Inf`, `enable.idempotence=true`, `max.in.flight≤5`.
> - **Consumer recipe:** producer-assigned `message_id` → `processed_messages` table → check+apply+insert in one DB tx → commit offset after DB commit.
> - **Kafka EOS:** Kafka-to-Kafka only. Doesn't span Postgres/HTTP.
> - **Trap:** keying by `(topic, partition, offset)` (survives broker redelivery, not producer retries).
> - **Trap:** committing offset before DB commit → message-loss window on crash.
> - **HTTP analog:** Stripe `Idempotency-Key` header.
