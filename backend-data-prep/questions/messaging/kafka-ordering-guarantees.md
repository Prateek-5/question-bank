# What ordering guarantees does Kafka give — and when do you actually need them

## Source / Origin
- Bread-and-butter Kafka question, often the first deep follow-up after "explain partitions".
- Documented in Kafka design docs and the producer/consumer reference.
- Concept reference: `backend-data-prep/messaging/kafka-ordering.md`.

## Why this question matters in interviews
"Kafka preserves order" is a half-truth most candidates parrot. The signal: do you know order is preserved **per partition**, not per topic? Can you explain why `max.in.flight.requests.per.connection > 1` without idempotence can re-order on retry? Do you understand that consumer-side multi-threading destroys ordering even if Kafka delivered in-order? Senior candidates know about idempotent producer, transactional producer, and the difference between *delivery* order and *processing* order.

## Concepts involved

### Syntax to lock in

```properties
# Producer side
enable.idempotence=true                       # required for safe in-flight > 1 with order
max.in.flight.requests.per.connection=5       # default; with idempotence, order safe up to 5
acks=all                                      # required for idempotence
retries=Integer.MAX_VALUE                     # default; safe with idempotence
```

```java
// Routing key controls partition assignment
producer.send(new ProducerRecord<>("orders", orderId, payload));
// Same key → same partition → ordered relative to other same-key records.
// Different keys may go to different partitions; cross-key order is NOT preserved.

// Manual partition for explicit control
producer.send(new ProducerRecord<>("orders", 3, orderId, payload));
```

```properties
# Consumer side
max.poll.records=500
# Single-threaded poll-loop preserves partition order.
# Multi-threading per partition destroys order unless you serialise per-key.
```

### Edge cases / interview traps

1. **Order is per-partition, not per-topic.** A topic with 8 partitions has 8 independent ordered streams.
2. **Same key, same partition** only as long as partition count is stable. Adding partitions changes the hash-mod assignment for some keys; their history splits across two partitions.
3. **`max.in.flight.requests.per.connection > 1` without idempotence = reorder risk.** Batch B is in flight after Batch A; A fails, retries, lands *after* B. Idempotent producer (with sequence numbers) prevents this.
4. **Idempotence is per-session, per-partition.** It deduplicates retries; it does NOT deduplicate application-level duplicates (e.g., consumer reads and re-publishes).
5. **Transactional producer (EOS)** extends idempotence to multi-partition atomic writes — but only "exactly once" within Kafka, not end-to-end if you write to a DB too.
6. **Consumer multi-threading** is the silent killer. If you fan out records from one partition to a thread pool, processing order is non-deterministic.
7. **Compacted topics may "appear" to reorder** because old values for a key get deleted during compaction. The remaining record per key is still the latest write, but intermediate states vanish.
8. **Multi-partition transactions** are atomic but each partition retains its own per-partition order — you can't get total order across partitions.
9. **Re-partitioning a topic** (mirror to new topic with more partitions) breaks key locality unless you preserve key.

## Mental Model

The **"highway lanes"** model.

```
   Topic "orders" with 4 partitions = 4 lanes on a highway.

   Cars in the same lane (same partition):
     - cannot overtake each other
     - arrive in order they entered
     - same-key cars always pick the same lane

   Cars in different lanes (different partitions):
     - no order guarantee between lanes
     - lane 0 car at t=10 may arrive after lane 2 car at t=20

   Consumer in a group = one driver per lane (with at-most one driver
   per lane). Drives in arrival order.

   If you fan out cars from one lane to multiple processors → you've
   chosen to break in-lane order. Your call, but acknowledge it.
```

## Why interviewers care

- Surfaces understanding that ordering is a *resource* that costs throughput (single-partition processing).
- Tests whether you've debugged "why is event B in the DB before event A" — almost always a key-design or multi-threading bug.
- Differentiates "uses Kafka" from "operates Kafka with awareness of guarantees".

## Common beginner confusion

- "Kafka preserves order globally." No — per partition only.
- "If I have one partition, order is guaranteed." Yes — at the cost of zero parallelism. Often a deliberate choice.
- "Idempotent producer prevents duplicates everywhere." Only per-producer-session, per-partition. Producer restart resets sequence; consumer-side duplicates still possible.
- "Transactional producer gives me end-to-end exactly-once." Only between Kafka topics. To DB it's still at-least-once unless you use transactional outbox or Kafka Connect's idempotent sinks.
- "I'll just sort by timestamp on the consumer." Producer timestamps can be skewed; brokers can rewrite timestamps; this only approximates order.

## Brute force approach

One partition, one consumer, single-threaded. Perfect total order. Throughput capped at one consumer's speed. Used legitimately for ledgers, audit logs, leader elections.

## Optimal approach

1. **Pick the right partition key** — entity id (user, order, account). Same-entity events always co-partition.
2. **Enable idempotent producer.** `enable.idempotence=true` + `acks=all`. Free, prevents retry-reordering.
3. **Use transactional producer** if you need atomic writes across multiple topics/partitions.
4. **Consumer: single-thread per partition.** If you need parallelism beyond that, use key-affinity threading (hash key → thread idx) to preserve per-key order while parallelising.
5. **Document the order contract** — "events per user are ordered; events across users are not".

## Solution

```java
// ===== Producer with safe order under retry =====
Properties p = new Properties();
p.put(BOOTSTRAP_SERVERS_CONFIG, "broker1:9092");
p.put(KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
p.put(VALUE_SERIALIZER_CLASS_CONFIG, ByteArraySerializer.class.getName());
p.put(ENABLE_IDEMPOTENCE_CONFIG, true);          // safe order under retry
p.put(ACKS_CONFIG, "all");                       // required with idempotence
p.put(MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 5); // OK with idempotence
p.put(RETRIES_CONFIG, Integer.MAX_VALUE);
KafkaProducer<String, byte[]> producer = new KafkaProducer<>(p);

// Partition by entity id → same-entity events go to same partition → ordered
producer.send(new ProducerRecord<>("orders", orderId /*key*/, serialise(event)));

// ===== Transactional producer (atomic multi-topic) =====
Properties tp = new Properties();
tp.putAll(p);
tp.put(TRANSACTIONAL_ID_CONFIG, "outbox-producer-1");  // stable across restarts
KafkaProducer<String, byte[]> txp = new KafkaProducer<>(tp);
txp.initTransactions();

try {
  txp.beginTransaction();
  txp.send(new ProducerRecord<>("orders", orderId, orderEvent));
  txp.send(new ProducerRecord<>("audit", orderId, auditEvent));
  txp.commitTransaction();
} catch (Exception e) {
  txp.abortTransaction();
}

// ===== Consumer: key-affinity thread pool (preserves per-key order) =====
int numThreads = 8;
ExecutorService[] pools = new ExecutorService[numThreads];
for (int i = 0; i < numThreads; i++) pools[i] = Executors.newSingleThreadExecutor();

while (running) {
  ConsumerRecords<String, byte[]> recs = consumer.poll(Duration.ofMillis(500));
  CountDownLatch latch = new CountDownLatch(recs.count());
  for (ConsumerRecord<String, byte[]> r : recs) {
    int idx = Math.floorMod(r.key().hashCode(), numThreads);
    pools[idx].submit(() -> {
      try { process(r); } finally { latch.countDown(); }
    });
  }
  latch.await();          // wait for batch before commit
  consumer.commitSync();
}
// Per-key order preserved (same key → same thread, single-threaded).
// Cross-key processing is parallel.
```

```bash
# Inspect partition count and current leadership
kafka-topics.sh --bootstrap-server broker:9092 --describe --topic orders

# When adding partitions, document the order-locality break
kafka-topics.sh --bootstrap-server broker:9092 --alter --topic orders --partitions 16
# Old key X's history is on partition (X.hash % 8); new events go to (X.hash % 16) → possibly different partition
```

## Step-by-step dry run

Producer writes 4 events for orderId="A":

```
e1: OrderCreated     → key="A" → hash(A) % 4 = 2 → partition 2, offset 100
e2: PaymentReceived  → key="A" → partition 2, offset 101
e3: Shipped          → key="A" → partition 2, offset 102
e4: Delivered        → key="A" → partition 2, offset 103

Consumer for partition 2 reads in order: e1, e2, e3, e4. ✓
Even if consumer is in a group of 4, each partition has exactly one
consumer; partition-2's consumer reads them in order.

Counter-example: producer with idempotence OFF, in-flight=5
  send(A) → batch B1 in flight
  send(B) → batch B2 in flight
  B1 fails (NETWORK), client retries → B1' in flight after B2
  Broker stores: B2 first, then B1' → REORDERED on this partition

  With idempotence: each batch carries (producer_id, epoch, seq).
  Broker rejects out-of-order sequence; producer retries within order.
```

Consumer-side break:

```
Single partition, single consumer, multi-threaded processor:
  records = [r1 (key=A), r2 (key=A), r3 (key=A)]
  thread pool: t1, t2, t3 each get one record
  t2 runs faster than t1 → r2 processed before r1 → ORDER BROKEN

Fix: key-affinity thread pool (above) OR single-threaded processing per partition.
```

## How to think aloud in the interview

> "Kafka guarantees order per partition. Two practical implications:
>
> 1. **Picking the right key is the whole game.** Same-entity events → same key → same partition → ordered. Cross-entity order is impossible to guarantee.
> 2. **Idempotent producer is mandatory** if you want retries to be safe with multiple in-flight requests. It's free now; turn it on.
>
> The trap is the consumer side. If you fan out records from one partition to a thread pool, you've broken order even though Kafka delivered it correctly. I use key-affinity threading: hash key → thread index; same key always lands on the same thread; parallel across keys but ordered within key.
>
> For cross-topic atomicity, transactional producer with `transactional.id` + read_committed consumers. That gives exactly-once *within* Kafka. For end-to-end EOS to a database, I pair with idempotent consumer keys or transactional outbox.
>
> One subtle point: adding partitions to a topic breaks per-key history locality for some keys. If order continuity matters, plan partition counts up front."

## Important takeaways

- Order is per-partition, not per-topic.
- Key selection determines co-partitioning, which determines order locality.
- `enable.idempotence=true` is the safe default; allows in-flight>1 without reorder.
- Consumer multi-threading without key affinity breaks order even when Kafka delivered in-order.
- Transactional producer for atomic multi-partition writes.
- Adding partitions later breaks key history continuity.

## Variants

1. **Streams app order** — Kafka Streams co-partitions joined topics by key; relies on per-partition order. Requires same partition count and same partitioner on both sides.
2. **Global compacted topic for config** — single partition, one consumer per consumer, used as a "config table". Total order trivially holds.
3. **Multi-DC ordering** — MirrorMaker 2 preserves per-partition order; order across topics in different DCs is not guaranteed.
4. **Out-of-order with watermarks** — for stream processing, accept some reorder and reconcile with event-time watermarks (Flink-style).
5. **Time-bucketed ordering** — sometimes "order within 1s window" is enough; cheaper than strict per-key order.

## Revision notes

> **kafka ordering — 60s recap**
> - Per-partition only. Same key → same partition → ordered.
> - `enable.idempotence=true` + `acks=all` for safe retries; in-flight up to 5 OK.
> - Transactional producer for cross-partition atomicity (EOS within Kafka).
> - Consumer multi-threading needs key-affinity to preserve order.
> - Adding partitions breaks key history continuity.
> - Order is a *resource* — costs throughput; pick what you need.
