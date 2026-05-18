# Walk through a Kafka consumer-group rebalance and explain how to make it boring

## Source / Origin
- Standard senior Kafka question; surfaces operational scars.
- Kafka Improvement Proposals: KIP-429 (cooperative sticky), KIP-848 (next-gen rebalance).
- Concept reference: `backend-data-prep/messaging/kafka-consumer-groups.md`.

## Why this question matters in interviews
Rebalance is the part of Kafka that bites teams in production. The interview signal: do you know that the default "stop-the-world eager" rebalance halts the entire consumer group for seconds? Can you name **cooperative sticky** as the modern fix and explain *why* it's cheaper? Do you understand `session.timeout.ms` vs `heartbeat.interval.ms` vs `max.poll.interval.ms` and which one triggers which type of leave? Senior candidates also know about static membership and KIP-848.

## Concepts involved

### Syntax to lock in

```properties
# The four critical knobs
session.timeout.ms=45000          # broker considers consumer dead if no heartbeat for this long
heartbeat.interval.ms=3000        # how often client sends heartbeats (~1/3 of session.timeout)
max.poll.interval.ms=300000       # max gap between poll() calls; exceeding triggers leave
max.poll.records=500              # batch size per poll(); large batches risk poll-timeout

# Assignment strategy (the single most impactful setting)
partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor
# Defaults historically: RangeAssignor, RoundRobinAssignor (both EAGER — stop-the-world)
# Modern best: CooperativeStickyAssignor (incremental — only moved partitions pause)

# Static membership (avoids rebalance on brief disconnect/restart)
group.instance.id=consumer-pod-3   # stable identity; broker keeps assignment across restarts
```

```java
// Consumer loop showing the four key timing risks
while (running) {
  ConsumerRecords<K, V> records = consumer.poll(Duration.ofMillis(500));
  // ← if this gap exceeds max.poll.interval.ms, you're kicked out
  for (ConsumerRecord<K, V> r : records) {
    process(r);  // ← slow processing is the #1 cause of unexpected rebalance
  }
  consumer.commitSync();
}
```

### Edge cases / interview traps

1. **`session.timeout.ms` vs `max.poll.interval.ms`** — heartbeats run on a background thread; they keep the session alive. But if `poll()` isn't called within `max.poll.interval.ms`, broker treats you as stuck and rebalances. Slow processing kills you via this knob, not session timeout.
2. **Eager (default until 2.4) vs cooperative sticky** — eager: all consumers revoke all partitions, then reassign. Stops the world. Cooperative: only re-balanced partitions get revoked. Use `CooperativeStickyAssignor`.
3. **Static membership (KIP-345)** — `group.instance.id` makes a consumer's identity survive restarts within `session.timeout.ms`. No rebalance for transient pod restarts.
4. **`partition.assignment.strategy` must match across the group** during upgrade. Mismatch = group fails to form. Migrate via "both strategies listed".
5. **Manual commit and rebalance** — between processing and commit, a rebalance can take your partition. Use `ConsumerRebalanceListener` to commit on revoke.
6. **Cooperative rebalance still has a stop-the-world phase** for the *moved* partitions, just not all of them.
7. **Adding partitions to a topic triggers rebalance.** Same for adding/removing consumers, change in topic subscription, leader broker change.
8. **KIP-848 (Kafka 3.7+)** — moves group coordination to the broker; consumers only get incremental "you now own X" updates. Even cheaper rebalance.

## Mental Model

The **"airline boarding"** model.

```
  Eager rebalance (the old way):
     "Everyone deplane. We're going to reseat you all."
     Empty plane → seat assignment → board → resume.
     All consumers idle during this window. Latency: seconds.

  Cooperative sticky:
     "Rows 12-15 please move to the back. Everyone else, stay seated."
     Only displaced partitions pause; rest of group keeps consuming.

  Static membership:
     "Even if a passenger goes to the lavatory for 30 seconds, we
      keep their seat. No reshuffle."
     Transient consumer restart → no rebalance.

  KIP-848:
     "Plane has assigned-seat live-updates; nobody needs to deplane."
     Per-consumer incremental assignment via heartbeats.
```

## Why interviewers care

- Rebalances cause real outages; surfacing the four knobs and the assignor choice tells the panel you've operated Kafka.
- Cooperative sticky is "easy to enable, huge win" — knowing it tells them you keep up with the ecosystem.
- The interaction with `max.poll.interval.ms` exposes whether you've debugged "my consumer keeps getting kicked out" — the rite of passage.

## Common beginner confusion

- "If processing takes 2 minutes, set `session.timeout.ms=600000`." Wrong knob. The relevant one is `max.poll.interval.ms`. Session timeout is for the heartbeat thread, which runs independently.
- "Range vs RoundRobin matter most." They affect *which* partitions go where; the *cost* of rebalance is determined by eager vs cooperative.
- "Static membership eliminates rebalance." Only for transient disconnects within `session.timeout.ms`. Real changes (scale up/down, broker failure) still rebalance.
- "Consumer joins immediately get partitions." They go through a join-protocol and only after the leader computes assignment.
- "Auto-commit is fine." Auto-commit commits offsets even if your processing failed downstream of poll. Use manual commit.

## Brute force approach

Set every timeout to 10 minutes; hope rebalances don't happen. They will. When they do, the group is unavailable for 10 minutes.

## Optimal approach

A four-step "make rebalance boring" checklist:

1. **Use `CooperativeStickyAssignor`.** Single biggest reduction in pause duration.
2. **Set `group.instance.id` per pod/instance.** Static membership eliminates rebalance on pod restart / brief disconnect.
3. **Tune `max.poll.interval.ms` to ≥ 2× P99 of your batch processing time.** And ensure `max.poll.records` is small enough that the batch fits.
4. **Implement `ConsumerRebalanceListener`** to commit offsets on partition revoke; idempotent processing.

## Solution

```java
// ===== Java consumer config =====
Properties p = new Properties();
p.put(BOOTSTRAP_SERVERS_CONFIG, "broker1:9092,broker2:9092");
p.put(GROUP_ID_CONFIG, "orders-processor");
p.put(GROUP_INSTANCE_ID_CONFIG, System.getenv("POD_NAME"));   // static membership
p.put(PARTITION_ASSIGNMENT_STRATEGY_CONFIG,
      List.of(CooperativeStickyAssignor.class.getName()));
p.put(SESSION_TIMEOUT_MS_CONFIG, 45_000);
p.put(HEARTBEAT_INTERVAL_MS_CONFIG, 3_000);
p.put(MAX_POLL_INTERVAL_MS_CONFIG, 300_000);  // tune to ≥ 2x P99 batch time
p.put(MAX_POLL_RECORDS_CONFIG, 100);
p.put(ENABLE_AUTO_COMMIT_CONFIG, false);

KafkaConsumer<String, byte[]> consumer = new KafkaConsumer<>(p);

// ===== Rebalance listener: commit on revoke, prepare on assign =====
consumer.subscribe(List.of("orders"), new ConsumerRebalanceListener() {
  @Override
  public void onPartitionsRevoked(Collection<TopicPartition> revoked) {
    // Critical: commit offsets for revoked partitions before they move.
    consumer.commitSync(currentOffsets(revoked));
    LOG.info("Revoked: {}", revoked);
  }
  @Override
  public void onPartitionsAssigned(Collection<TopicPartition> assigned) {
    // Optional: warm caches, seek to specific offsets, etc.
    LOG.info("Assigned: {}", assigned);
  }
  @Override
  public void onPartitionsLost(Collection<TopicPartition> lost) {
    // Cooperative only: partitions taken from us without graceful revoke.
    // Drop in-flight work; do NOT commit.
    LOG.warn("Lost (no revoke): {}", lost);
  }
});

// ===== Processing loop =====
while (running.get()) {
  ConsumerRecords<String, byte[]> records = consumer.poll(Duration.ofSeconds(1));
  for (TopicPartition tp : records.partitions()) {
    List<ConsumerRecord<String, byte[]>> partitionRecs = records.records(tp);
    processBatch(partitionRecs);  // idempotent
    long lastOffset = partitionRecs.get(partitionRecs.size() - 1).offset();
    consumer.commitSync(Map.of(tp, new OffsetAndMetadata(lastOffset + 1)));
  }
}

// ===== Bash: detect rebalance frequency =====
//   kafka-consumer-groups.sh --bootstrap-server $BS \
//     --describe --group orders-processor
//   Look at LAG, CONSUMER-ID, HOST. Frequent CONSUMER-ID changes = rebalance churn.
```

## Step-by-step dry run

Group of 4 consumers (C1-C4), topic with 8 partitions, EAGER vs COOPERATIVE on scale-up to 5.

```
EAGER (default pre-2.4):
  t=0   C5 joins → group coordinator triggers rebalance
  t=0   All consumers receive "revoke ALL partitions"
  t=0   All consumers stop processing; commit current offsets
  t=1   Coordinator computes assignment: 8 partitions / 5 consumers
  t=2   All consumers receive new assignment, fetch metadata, seek
  t=4   All consumers resume polling
  → ~4 seconds of zero throughput for entire group

COOPERATIVE STICKY:
  t=0   C5 joins
  t=0   Coordinator decides: take 1 partition from C1, 1 from C2,
        give both to C5; rest unchanged
  t=0   C1 revokes p3 → commit p3 offset → done with p3
        C2 revokes p7 → commit p7 offset → done with p7
        C3, C4 keep all partitions, NEVER PAUSE
  t=1   C5 receives {p3, p7}; starts polling
  → only p3 and p7 paused (~1s); C3, C4 fully uninterrupted

STATIC MEMBERSHIP, C2 pod restart within session.timeout.ms:
  t=0   C2 pod killed; new pod starts with same group.instance.id
  t=2   New C2 sends JoinGroup with same group.instance.id
  t=2   Coordinator recognises identity; no rebalance triggered
  t=2   C2 receives ITS PREVIOUS assignment; resumes polling
  → ZERO disruption to other consumers
```

Failure scenarios:

```
Slow processing kills consumer:
  poll() returns 500 records, batch takes 6 minutes.
  max.poll.interval.ms=300000 (5 min) → next poll() throws
  "CommitFailedException: rebalance happened while processing".
  Fix: reduce max.poll.records OR raise max.poll.interval.ms OR
       process async and pause()/resume() partitions.

Long GC pause:
  Heartbeat thread paused during 60s GC → session.timeout fires →
  consumer kicked out. Fix: tune GC, increase session.timeout
  (but not too high; you want fast failure detection).
```

## How to think aloud in the interview

> "Rebalance is the Kafka cliff. Three things make it boring:
>
> 1. **Cooperative sticky assignor** — only the partitions being moved pause; the rest of the group keeps consuming. Single biggest win.
> 2. **Static membership** (`group.instance.id`) — pod restarts within session timeout don't trigger rebalance at all.
> 3. **Tune `max.poll.interval.ms` and `max.poll.records` to match your batch latency.** Slow processing is the #1 trigger of unexpected rebalance.
>
> I always implement `ConsumerRebalanceListener` to commit offsets on revoke — otherwise, between processing and commit, a rebalance can hand the partition to another consumer who reprocesses; idempotency saves you but commits-on-revoke avoid the reprocess.
>
> Newer Kafka (3.7+) ships KIP-848 server-side group coordination, which is even cheaper. For now, cooperative sticky + static membership covers ~95% of operational pain."

## Important takeaways

- Default rebalance is eager / stop-the-world; switch to cooperative sticky.
- `group.instance.id` for static membership; survives pod restarts.
- `max.poll.interval.ms` (not `session.timeout.ms`) is the slow-processing trap.
- Commit offsets on `onPartitionsRevoked` to avoid reprocessing.
- Processing must be idempotent regardless.
- KIP-848 (Kafka 3.7+) further reduces rebalance cost.

## Variants

1. **Streams app rebalance** — Kafka Streams uses cooperative since 2.4 by default; state-store restoration on assignment is the new pain.
2. **Connect rebalance** — incremental cooperative rebalance for connectors; tasks redistribute.
3. **Multi-tenant cluster** — one rogue consumer can monopolise the coordinator; quotas help.
4. **Custom assignor** — for stickiness-with-rack-awareness or workload-balancing.
5. **EOS (exactly-once) + rebalance** — transactional consumer must abort in-flight transactions on revoke.

## Revision notes

> **kafka rebalance — 60s recap**
> - Default eager = stop-the-world. Switch to `CooperativeStickyAssignor`.
> - `group.instance.id` = static membership; no rebalance on restart.
> - `max.poll.interval.ms` is the slow-batch killer (NOT session.timeout).
> - Commit on `onPartitionsRevoked`; processing must be idempotent.
> - Triggers: consumer add/remove, topic partition add, subscription change, broker leader move.
> - KIP-848 (3.7+) = server-side coord; further reduction.
