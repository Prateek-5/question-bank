# Design a dead-letter queue: when to send, how to monitor, how to recover

## Source / Origin
- Standard messaging-systems design question.
- Patterns documented in AWS SQS DLQ, Kafka via separate topic, RabbitMQ via dead-letter exchange.
- Concept reference: `backend-data-prep/messaging/dlq.md`.

## Why this question matters in interviews
DLQ is where junior engineers say "we'll just have a DLQ" and senior engineers know that the DLQ *itself* needs design: when to route there, what metadata to attach, how to alert, how to drain. Interview signal: do you know that DLQ without monitoring is a silent black hole? Can you distinguish *poison messages* (broken forever) from *transient failures* (will recover)? Do you have a re-drive plan? Senior candidates also know about retry topics + DLQ as a tiered pattern.

## Concepts involved

### Syntax to lock in

```yaml
# AWS SQS native DLQ
QueueAttributes:
  RedrivePolicy:
    deadLetterTargetArn: arn:aws:sqs:us-east-1:123:orders-dlq
    maxReceiveCount: 5         # after 5 unsuccessful receives, route to DLQ
```

```yaml
# RabbitMQ dead-letter exchange
queue.declare(name="orders", arguments={
  "x-dead-letter-exchange": "dlx.orders",
  "x-dead-letter-routing-key": "orders.dead",
  "x-message-ttl": 60000   # TTL; expired messages go to DLX
})
```

```java
// Kafka: app-level DLQ (no native concept; just another topic)
try {
  process(record);
  consumer.commitSync();
} catch (PoisonMessageException e) {
  producer.send(new ProducerRecord<>("orders.dlq", record.key(),
    enrichWithMeta(record.value(), e)));
  consumer.commitSync();  // commit past the poison
}

// Enrichment metadata to attach
{
  "original_topic": "orders",
  "original_partition": 3,
  "original_offset": 1234567,
  "original_key": "ord-42",
  "first_failure_ts": "2026-05-17T10:15:00Z",
  "last_failure_ts": "2026-05-17T10:22:00Z",
  "attempt_count": 5,
  "error_class": "JsonParseException",
  "error_message": "...",
  "stack_trace_short": "...",
  "consumer_version": "v2.7.1"
}
```

### Edge cases / interview traps

1. **DLQ without monitoring is worse than no DLQ.** Messages silently disappear from the main flow; on-call doesn't know.
2. **`maxReceiveCount` interacts with visibility timeout** in SQS. If your processing takes longer than visibility timeout, the message reappears and counts as a redelivery even though you're still processing it.
3. **DLQ on Kafka is not native.** No automatic routing on retry exhaustion — your consumer must explicitly publish to DLQ topic and commit offset.
4. **Poison vs transient.** A bad schema is poison; a brief DB outage is transient. Routing both to DLQ on first failure floods it.
5. **Order preservation breaks** when you DLQ a record and continue. The downstream sees the next record, not the failed one. For order-critical streams, you may need to pause the partition instead.
6. **DLQ messages need TTL.** Otherwise they accumulate forever; storage cost and operational confusion.
7. **Re-drive must be idempotent.** Re-publishing a DLQ message to the main topic may produce duplicates downstream.
8. **DLQ schema may drift** from main topic — producers evolve, DLQ messages stay old. Replay tools must handle this.
9. **PII in DLQ** — failed messages may contain payment data that you've already redacted in the main path. Treat DLQ as production data.

## Mental Model

The **"escalation room"** model.

```
   Main topic           Retry topic(s)         DLQ
   ─────────            ─────────────         ────
   normal traffic   →   transient errors  →   poison / exhausted
                        (delay-based retry)   (manual triage)

   Each tier:
     - has its own consumer
     - has its own alerting threshold
     - has a documented re-drive procedure

   DLQ is NOT a graveyard. It is an inbox for humans.
```

## Why interviewers care

- Tests operational maturity: who looks at the DLQ, how often, what's the SLA on draining?
- Surfaces awareness of monitoring/alerting; "DLQ depth > N" alarms.
- Differentiates pattern-knowledge from runbook-knowledge.

## Common beginner confusion

- "DLQ is for retries." No — DLQ is the *terminus* after retries fail. Retry queues handle retries.
- "DLQ should be invisible to the rest of the system." Wrong; metrics, dashboards, and alarms must surface it.
- "Just let the message keep retrying." Without a circuit-breaker, you blow the consumer up, block the partition, and cascade failures.
- "DLQ is automatically populated." On Kafka, you must code it. On SQS/RabbitMQ, configure it.
- "Bigger `maxReceiveCount` is safer." Up to a point. Past ~5-10 you're just wasting compute on a poison message.

## Brute force approach

Infinite retries; never DLQ. Eventually a poison message blocks the partition / queue forever. On-call wakes up. Don't.

## Optimal approach

Five-step design:

1. **Classify failures** in the consumer: transient (retryable) vs poison (terminal). Different exception types.
2. **Tiered retry** — N immediate retries; if still failing and exception is transient, publish to a retry topic with delay. If poison or retries exhausted, publish to DLQ.
3. **Enrich on DLQ publish** — original metadata + error context.
4. **Alarm on DLQ depth** and ingest rate. Treat as a Sev event when depth > threshold.
5. **Build a re-drive tool** that re-publishes DLQ messages to the main topic, with batch limits and idempotency keys.

## Solution

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DLQ tiered architecture                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│    main-topic ───► consumer ──┬─► success → commit                  │
│                                ├─► transient err (3 retries)        │
│                                │     ├─► success → commit           │
│                                │     └─► publish to retry-topic-5s  │
│                                │            └─► retry-topic-30s     │
│                                │                  └─► retry-topic-5m│
│                                │                        └─► DLQ    │
│                                └─► poison (schema, validation)      │
│                                       └─► DLQ (skip retries)        │
│                                                                     │
│    DLQ ──► alarm on depth, age                                      │
│         ──► triage tool: read, classify, fix, re-drive              │
│         ──► auto-archive after N days (TTL)                         │
└─────────────────────────────────────────────────────────────────────┘
```

```java
// ===== Kafka consumer with tiered DLQ =====
class TieredConsumer {
  private static final int MAX_INLINE_RETRIES = 3;

  void handle(ConsumerRecord<String, byte[]> r) {
    int attempt = headerInt(r, "x-attempt", 0);
    try {
      process(r);
    } catch (PoisonMessageException e) {
      // Schema invalid, validation failed, business rule unrecoverable
      sendToDLQ(r, e, attempt);
    } catch (TransientException e) {
      if (attempt < MAX_INLINE_RETRIES) {
        // Inline retry (sleep + retry within same poll)
        backoff(attempt);
        handle(rebumped(r, attempt + 1));
      } else {
        // Move to delayed retry topic
        long delayMs = nextDelay(attempt);   // 5s, 30s, 5m, then DLQ
        if (delayMs == Long.MAX_VALUE) sendToDLQ(r, e, attempt);
        else sendToRetryTopic(r, e, attempt + 1, delayMs);
      }
    }
  }

  void sendToDLQ(ConsumerRecord<String, byte[]> r, Exception e, int attempts) {
    Map<String, String> meta = Map.of(
      "original_topic",    r.topic(),
      "original_partition", String.valueOf(r.partition()),
      "original_offset",    String.valueOf(r.offset()),
      "first_failure_ts",   headerStr(r, "x-first-failure", Instant.now().toString()),
      "last_failure_ts",    Instant.now().toString(),
      "attempts",           String.valueOf(attempts),
      "error_class",        e.getClass().getName(),
      "error_message",      truncate(e.getMessage(), 1024)
    );
    ProducerRecord<String, byte[]> dlqRec = new ProducerRecord<>(
      r.topic() + ".dlq", r.partition(), r.key(), r.value());
    meta.forEach((k, v) -> dlqRec.headers().add(k, v.getBytes()));
    dlqProducer.send(dlqRec).get();           // synchronous; can't lose
    Metrics.counter("dlq.publish", "topic", r.topic()).increment();
  }
}
```

```yaml
# ===== Alarms =====
- alert: DLQDepthHigh
  expr: kafka_topic_partition_lag{topic=~".*\\.dlq"} > 100
  for: 5m
  labels: { severity: page }
  annotations: { summary: "DLQ depth > 100 on {{ $labels.topic }}" }

- alert: DLQGrowing
  expr: rate(kafka_topic_messages_in_total{topic=~".*\\.dlq"}[5m]) > 1
  for: 10m
  labels: { severity: warn }
```

```bash
# ===== Re-drive tool =====
# Read DLQ, optionally filter by error_class, republish to original topic.
kafka-dlq-redrive \
  --dlq-topic orders.dlq \
  --target-topic orders \
  --filter "error_class=TransientException" \
  --batch 100 \
  --rate 10/s \
  --dry-run
# After validation, drop --dry-run.
# Producer uses idempotent send + original partition + same key.
```

## Step-by-step dry run

Order processor receives an event with a malformed JSON payload:

```
t=0   poll() returns record r=(key=ord-7, value=<bad json>, offset=500)
t=0   process(r) throws JsonParseException → classified POISON
t=0   sendToDLQ(r, ..., attempts=1):
        ├─ produces to orders.dlq with all headers
        ├─ awaits ack (synchronous)
        └─ commits orders offset 501
t=0   continue with next record. Main flow not blocked.
t=60s DLQ depth metric ticks 1.
t=10m Operator alert: "DLQ.orders depth=1 (new)".
t=15m Operator inspects:
       kafka-dlq-redrive --dlq-topic orders.dlq --print --limit 5
       → sees the malformed payload, x-error-class=JsonParse, source=upstream-svc-v3
t=20m Operator opens ticket with upstream team to fix payload format.
t=2d  Upstream fix deployed. DLQ message no longer relevant → archive.

Transient case:
t=0   DB down → DAOException → TransientException
t=0   inline retry 1, 2, 3 (sleep 100ms, 500ms, 2s) — still failing
t=2s  publish to retry-topic-5s (delay header)
t=7s  consumer of retry-topic-5s polls, processes — DB still down
t=7s  publish to retry-topic-30s
t=37s consumer polls, processes — DB recovered → success
       message never reaches DLQ.
```

Order-preserving alternative (when DLQ-on-failure would break a stream):

```
For partition with order-critical events:
  on transient failure → pause(partition); sleep with backoff; resume(partition)
  on poison → still DLQ (the stream is already broken for this key)
  Trade: one bad key blocks its key's stream, but doesn't reorder others.
```

## How to think aloud in the interview

> "DLQ design has three parts:
>
> 1. **When to send.** Classify exceptions: poison goes straight to DLQ; transient gets tiered retries via delay topics, then DLQ.
> 2. **What to attach.** Original topic/partition/offset, first-failure timestamp, attempt count, error class, short stack trace. Without this metadata the DLQ is unreplay-able.
> 3. **What happens after.** Alarms on depth and growth rate; a re-drive tool with dry-run; idempotent producers so re-drive doesn't duplicate downstream.
>
> The most common failure mode is DLQ-as-graveyard — messages pile up, nobody looks, problem festers. I treat DLQ depth as a Sev3 if growing, Sev2 over 100, Sev1 if main-flow blocked.
>
> One subtlety I always raise: DLQ breaks order. If your stream is order-sensitive (financial ledger), I pause the partition instead, with circuit-breaker semantics, so the bad key blocks its own key but not the rest.
>
> Kafka has no native DLQ — you build it. SQS and RabbitMQ have first-class support; configure `maxReceiveCount` carefully against visibility timeout."

## Important takeaways

- DLQ is the terminus; retries happen before it (tiered delay topics).
- Enrich messages with origin + error metadata.
- Monitor DLQ depth and ingest rate; alarm aggressively.
- Build a re-drive tool with idempotency, batch limits, dry-run.
- Order-critical streams: pause partition instead of DLQ-and-skip.
- TTL on DLQ to prevent eternal accumulation; archive cold messages.
- PII / sensitive data in DLQ is still production data.

## Variants

1. **Per-error-class DLQ topics** — `orders.dlq.schema`, `orders.dlq.timeout` — easier triage.
2. **SQS DLQ + Lambda re-drive** — managed re-drive in AWS console.
3. **DLQ → S3 cold storage** — after N days, move to object storage; cheaper.
4. **Parking-lot topic** (intermediate) — between retry and DLQ; humans review and decide.
5. **Schema-aware DLQ** — message includes its schema-id; replay tool can translate to current schema.

## Revision notes

> **dlq design — 60s recap**
> - Tiered: inline retry → delay retry topics → DLQ.
> - Classify exceptions: poison vs transient.
> - Enrich: original metadata, error class, attempts, timestamps.
> - Monitor depth + ingest rate; alarm.
> - Re-drive tool: idempotent, batch-limited, dry-run.
> - Order-critical: pause partition instead of DLQ-and-skip.
> - Kafka: app-level DLQ; SQS / RabbitMQ have native support.
> - TTL & archive; treat PII carefully.
