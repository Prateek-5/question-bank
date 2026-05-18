# Design tiered retry topics for delayed redelivery without blocking the main stream

## Source / Origin
- Uber Engineering blog on retry topics; Confluent best-practices.
- Replaces the naive "loop and sleep" anti-pattern.
- Concept reference: `backend-data-prep/messaging/retry-topics.md`.

## Why this question matters in interviews
Kafka has no native delayed-delivery. Candidates who say "we'll just sleep in the consumer" reveal they've never run Kafka in production — sleeping blocks the consumer, blocks the partition, and trips `max.poll.interval.ms` quickly. The interview signal: do you know the tiered retry topic pattern (5s, 30s, 5m, 1h, DLQ)? Can you explain why it doesn't block the main consumer? Senior candidates also know about timestamp-gating vs separate consumer per tier.

## Concepts involved

### Syntax to lock in

```
Topology:
  orders                  ← main topic, main consumer
  orders.retry.5s         ← consumer reads with 5s delay logic
  orders.retry.30s
  orders.retry.5m
  orders.retry.1h
  orders.dlq              ← terminus
```

```java
// Producer-side: on transient failure, publish to next tier
record.headers().add("x-attempt", String.valueOf(attempt + 1).getBytes());
record.headers().add("x-not-before", String.valueOf(now + delayMs).getBytes());
retryProducer.send(new ProducerRecord<>("orders.retry.5s",
    r.partition(), r.key(), r.value(), record.headers()));

// Retry-tier consumer: gate by timestamp
ConsumerRecords<...> records = consumer.poll(Duration.ofSeconds(1));
for (ConsumerRecord<...> r : records) {
  long notBefore = headerLong(r, "x-not-before", 0);
  long now = System.currentTimeMillis();
  if (now < notBefore) {
    // pause this partition; resume after delay
    consumer.pause(Set.of(new TopicPartition(r.topic(), r.partition())));
    scheduler.schedule(() -> consumer.resume(...), notBefore - now, MS);
    break;  // don't process the rest of this batch yet
  }
  process(r);
}
```

### Edge cases / interview traps

1. **Don't `Thread.sleep()` in the consumer loop.** Trips `max.poll.interval.ms`; broker triggers rebalance.
2. **Use `consumer.pause()` and `resume()`** to halt fetching from specific partitions without losing membership.
3. **Per-tier topic count grows.** 5s, 30s, 5m, 1h is 4 tiers + DLQ = 5 topics per logical stream. Don't go finer than necessary.
4. **Ordering is broken across tiers.** A record retried to tier 2 may be redelivered after later records from the main topic. That's accepted — if order matters, retry inline / pause partition.
5. **Headers carry state**, not the payload — original key/value preserved.
6. **Idempotency is required.** A successful retry may be after a future poison record; processing must be commutative or keyed.
7. **Backpressure on retry topics** — if retries spike (downstream out), retry topics balloon. Set retention; monitor lag.
8. **Same consumer for all tiers vs separate** — separate consumers per tier scale independently and isolate slow retries from main flow.
9. **`max.poll.interval.ms` still applies to retry-tier consumers.** A 1h tier with `notBefore` gating must use pause/resume, not blocking.

## Mental Model

The **"appointment desk"** model.

```
   Main topic:  walk-in customers (real-time)
   orders.retry.5s:  "come back in 5 seconds"
   orders.retry.30s: "come back in 30 seconds"
   orders.retry.5m:  "come back in 5 minutes"
   orders.retry.1h:  "come back in an hour"
   DLQ: "we cannot help you; manager will review"

   Each desk (consumer) is staffed independently. The waiting room
   (topic) holds records until their ticket time. The main desk is
   never blocked by waiting customers.
```

## Why interviewers care

- Tests knowledge that Kafka lacks delayed delivery natively (unlike SQS, RabbitMQ).
- Surfaces awareness of consumer-loop fragility (`max.poll.interval.ms`, partition pause).
- Differentiates "I followed a tutorial" from "I designed for elastic retry traffic in prod".

## Common beginner confusion

- "I'll just `Thread.sleep(5000)` then retry." Blocks the consumer; broker kicks it out.
- "All retries should use one retry topic." Mixing delay tiers in one topic forces fine-grained gating; cleaner with one per tier.
- "Retry topic is the same as DLQ." No — retries may succeed and exit; DLQ is terminus.
- "Kafka has a scheduler." It doesn't. You build it.
- "Exponential delays in code." Yes, but the delay must happen via *waiting in a topic*, not blocking the consumer.

## Brute force approach

`Thread.sleep()` inside the consumer between retries. Works for tiny delays (<100ms) only; longer and you trip `max.poll.interval.ms`. Don't.

## Optimal approach

Five steps:

1. **Decide tiers** based on expected failure recovery times. Typical: 5s, 30s, 5m, 1h.
2. **One topic per tier**, same partition count as main (for ordering/locality).
3. **Per-tier consumer** that gates by `x-not-before` header using `pause/resume`.
4. **Headers carry**: original topic, attempt number, first failure ts, last error.
5. **Cap attempts**; after the last tier, route to DLQ.

## Solution

```
┌────────────────────────────────────────────────────────────────────┐
│                Retry-topic topology                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────┐   transient failure        ┌────────────────────┐   │
│  │  orders  │ ───────────────────────►   │ orders.retry.5s    │   │
│  └────┬─────┘                            └─────────┬──────────┘   │
│       │ success                                     │              │
│       ▼                                             ▼              │
│   downstream                              ┌────────────────────┐   │
│                                           │ retry-5s consumer  │   │
│                                           │ gate by notBefore  │   │
│                                           │  pause/resume      │   │
│                                           └─────────┬──────────┘   │
│                                                     │              │
│            success ◄────────────────────────────────┤              │
│                                                     │              │
│                                          still failing             │
│                                                     ▼              │
│                                           ┌────────────────────┐   │
│                                           │ orders.retry.30s   │   │
│                                           └────────────────────┘   │
│                                                     │              │
│                                                     ▼ (repeat)     │
│                                           orders.retry.5m         │
│                                                     ▼              │
│                                           orders.retry.1h         │
│                                                     ▼              │
│                                           orders.dlq               │
└────────────────────────────────────────────────────────────────────┘
```

```java
// ===== Main consumer =====
class MainConsumer {
  private final long[] DELAYS = { 5_000, 30_000, 300_000, 3_600_000 };
  private final String[] TIERS = {
    "orders.retry.5s", "orders.retry.30s", "orders.retry.5m", "orders.retry.1h"
  };

  void handle(ConsumerRecord<String, byte[]> r) {
    int attempt = headerInt(r, "x-attempt", 0);
    try {
      process(r);
    } catch (PoisonException e) {
      sendToDLQ(r, e, attempt);
    } catch (TransientException e) {
      if (attempt < DELAYS.length) {
        sendToRetryTier(r, attempt, e);
      } else {
        sendToDLQ(r, e, attempt);
      }
    }
  }

  void sendToRetryTier(ConsumerRecord<String, byte[]> r, int attempt, Exception e) {
    long notBefore = System.currentTimeMillis() + DELAYS[attempt];
    ProducerRecord<String, byte[]> p = new ProducerRecord<>(
      TIERS[attempt], r.partition(), r.key(), r.value());
    p.headers().add("x-attempt",       String.valueOf(attempt + 1).getBytes());
    p.headers().add("x-not-before",    String.valueOf(notBefore).getBytes());
    p.headers().add("x-original-topic","orders".getBytes());
    p.headers().add("x-first-failure",
      headerStr(r, "x-first-failure", Instant.now().toString()).getBytes());
    p.headers().add("x-last-error",    e.getClass().getName().getBytes());
    producer.send(p);
  }
}

// ===== Retry-tier consumer (one per tier) =====
class RetryConsumer {
  KafkaConsumer<String, byte[]> consumer;
  ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);

  void loop() {
    while (running) {
      ConsumerRecords<String, byte[]> records = consumer.poll(Duration.ofMillis(500));
      Set<TopicPartition> toPause = new HashSet<>();
      long earliestResume = Long.MAX_VALUE;

      for (TopicPartition tp : records.partitions()) {
        for (ConsumerRecord<String, byte[]> r : records.records(tp)) {
          long notBefore = headerLong(r, "x-not-before", 0);
          long now = System.currentTimeMillis();
          if (now < notBefore) {
            // first record in partition not ready → pause partition
            toPause.add(tp);
            earliestResume = Math.min(earliestResume, notBefore);
            consumer.seek(tp, r.offset());  // re-read next time
            break;
          }
          mainHandler.handle(r);  // try original processing
        }
      }

      if (!toPause.isEmpty()) {
        consumer.pause(toPause);
        long delay = earliestResume - System.currentTimeMillis();
        scheduler.schedule(() -> consumer.resume(toPause), delay, MILLISECONDS);
      }
      consumer.commitSync();
    }
  }
}
```

```yaml
# ===== Topic provisioning =====
for t in orders orders.retry.5s orders.retry.30s orders.retry.5m orders.retry.1h orders.dlq; do
  kafka-topics.sh --bootstrap-server $BS --create --topic $t \
    --partitions 12 --replication-factor 3 \
    --config retention.ms=$([ "$t" = "orders.dlq" ] && echo 1209600000 || echo 86400000)
done
# DLQ: 14 days; retries: 1 day (long enough for the longest tier)
```

## Step-by-step dry run

Order event, downstream DB intermittently failing:

```
t=0     main consumer polls record r (key=ord-7, attempt=0)
t=0     process(r) throws TransientException (DB unavailable)
t=0     publish to orders.retry.5s with x-not-before = t+5000, x-attempt=1
t=0     main consumer commits orders offset; moves on

t=1     retry-5s consumer polls; sees r; now=t+1, notBefore=t+5 → not ready
t=1     pause partition; schedule resume for t+5
t=5     scheduler resumes partition; next poll picks up r
t=5     process(r): DB still down → throws Transient
t=5     publish to orders.retry.30s with x-not-before = t+35, x-attempt=2

t=10    retry-30s consumer polls; pauses
t=35    resume; process: DB recovered → success
t=35    commit orders.retry.30s offset; record exits the retry chain

Counter-scenario: poison record
t=0     main consumer polls; process throws JsonParseException (POISON)
t=0     direct publish to orders.dlq with metadata; commit main; done
        Skip all retry tiers — no point retrying a malformed payload.
```

What if downstream is down for 1.5 hours?

```
Record passes: main → 5s → 30s → 5m → 1h tier.
At 1h tier, still failing → publish to DLQ.
Operator alarm: "DLQ depth growing fast on orders.dlq".
Operator triages: confirms downstream incident; pauses re-drive until
recovery. After recovery: re-drive DLQ → main topic.
```

## How to think aloud in the interview

> "Kafka has no native delayed delivery, so retries with sleep block the consumer and trip `max.poll.interval.ms`. The pattern is **tiered retry topics**: 5s, 30s, 5m, 1h, then DLQ. On transient failure, the consumer republishes to the next tier with `x-not-before` timestamp and attempt headers, then commits the main offset.
>
> A per-tier consumer reads its topic, checks `notBefore`, and if too early, **pauses the partition** and schedules a resume — never sleeps the consumer thread. This keeps the consumer in the group and frees other partitions to make progress.
>
> Headers carry state: original topic, attempt count, first-failure timestamp, last error class. This makes DLQ messages replayable.
>
> Critical practical details: idempotent processing (retries are by definition redelivery); cap attempts (don't retry forever); separate consumer per tier so slow retries don't starve the main flow; alarm on retry-topic lag.
>
> The pattern is from Uber's blog; Confluent has a tutorial. It's industry-standard."

## Important takeaways

- Kafka has no built-in delayed delivery; retry topics provide it.
- Use `pause/resume` on partitions; never `Thread.sleep` in the loop.
- One topic per delay tier; same partition count as main.
- Headers carry: attempt, not-before, original topic, first-failure, last-error.
- Idempotency required for safe retries.
- Cap attempts; route exhausted to DLQ.
- Separate consumer per tier for isolation.

## Variants

1. **Spring Kafka's `@RetryableTopic`** — annotation generates topics and consumers automatically.
2. **Confluent Parallel Consumer** — different angle; key-ordered parallelism with built-in retry.
3. **Single retry topic + scheduling service** — alternative: one topic, a sidecar service that re-injects when notBefore arrives.
4. **Retry only certain error classes** — exception classification matters; not all transient errors deserve retry.
5. **Exponential backoff with jitter** — pick `delay * (1 + rand(0..0.5))` to avoid synchronized retry storms.

## Revision notes

> **retry topic pattern — 60s recap**
> - Tiers: 5s, 30s, 5m, 1h, DLQ.
> - On transient failure: republish to next tier with `x-not-before`.
> - Retry-tier consumer: gate by header, pause/resume partition (never sleep).
> - Headers: attempt, not-before, original topic, first-failure, last-error.
> - Cap attempts; idempotent processing.
> - Separate consumer per tier; isolation + independent scaling.
> - Uber / Confluent canonical pattern.
