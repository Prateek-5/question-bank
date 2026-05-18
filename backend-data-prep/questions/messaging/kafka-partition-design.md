# Kafka Partition Design — Choosing the Partition Key

## Source / Origin
- Confluent's "Designing Apache Kafka Topics" guide; Jun Rao's original Kafka design paper (2011).
- Companion files: `kafka-ordering-guarantees.md`, `kafka-consumer-group-rebalance.md`, `message-ordering-strategies.md`.
- Common interview prompts:
  - *"You're designing a notifications service. Pick a partition key for the user-notifications topic and justify."*
  - *"What happens to throughput if 90% of your traffic is for one customer?"*
  - *"You have 12 partitions and want to add 12 more. What breaks?"*

## Why this question matters in interviews
Partition design is **where Kafka stops being magic** and starts being a careful choice with tradeoffs. Junior engineers say "round-robin, more partitions = more throughput, done." Seniors ask: what's the ordering scope, what's the consumer parallelism ceiling, what happens on rebalance, and which customer becomes a hot partition? Interviewers use this to test if you've operated a real Kafka cluster — because every wrong choice here shows up as either a 3am pager or a $200k AWS bill. This is also the gateway to discussing skewed workloads, partition counts, and rebalance storms.

## Concepts involved

### Syntax to lock in

Three partitioning modes:
```
Producer.send(topic, key=null, value=...)      → round-robin / sticky-batch
Producer.send(topic, key='user-42', value=...) → hash(key) % numPartitions
Producer.send(topic, key=..., partition=3, value=...)  → manual partition pick
```

Kafka's default partitioner (since 2.4):
```java
if (key == null) {
  // "sticky partitioner" — pick a partition, batch messages, then switch
  return stickyPartition();
} else {
  return murmur2(key) % numPartitions;
}
```

Topic creation:
```bash
kafka-topics.sh --create --topic notifications --partitions 24 --replication-factor 3
```

### Edge cases / interview traps

1. **Ordering is per-partition, not per-topic.** If you care about ordering for an entity (user, order, account), all events for that entity must hit the same partition — which means they must share the same key.
2. **Hash skew = hot partition.** If 90% of your traffic is for `customer-acme-corp`, all that traffic lands on one partition. That partition becomes the bottleneck. One CPU, one disk, one consumer.
3. **Number of partitions is the ceiling on consumer parallelism.** A consumer group can have at most N consumers actively consuming from N partitions. Adding a 13th consumer to a 12-partition topic gives you one idle consumer.
4. **Repartitioning is a major operation.** Adding partitions to an existing topic changes `hash(key) % N` → existing keys now hash to different partitions. Per-key ordering breaks across the boundary. Plan partition count upfront.
5. **Sticky partitioner trap.** With `key=null`, producers in 2.4+ batch into one partition for a few seconds before switching. Great for throughput, but means "round-robin" is *not* what's actually happening at the per-message level.
6. **Compound keys.** If you partition by `customer_id` but want some downstream parallelism *within* a customer, compose the key like `customer_id:hash(order_id) % N_subkeys` — gives you N parallel paths per customer at the cost of cross-order ordering within a customer.
7. **Time-based keys are an anti-pattern** (e.g., partitioning by `today's date`). Creates a single hot partition for "today" and N-1 cold partitions.
8. **Partition count math.** Rule of thumb: target ~10MB/s per partition per consumer thread. If your topic does 100MB/s and you want 4 consumers per group, 40 partitions is reasonable. More partitions = more file handles, more rebalance work, more leader-elections on broker failure.
9. **DefaultPartitioner murmur2 is consistent across clients.** Don't roll your own unless you also re-roll it on every consumer.

## Mental Model

A topic is a set of **independent logs** (partitions), each ordered, each owned by one broker, each consumable by one consumer in a group at a time. The partition key is your **routing decision**: it dictates which log a message lands in, which dictates ordering scope and consumer parallelism.

```
   Topic: orders   (12 partitions)
   ┌────────────────────────────────────────────────────────────┐
   │  P0  ►  m m m m m m m m ...      (one log, in order)       │
   │  P1  ►  m m m m m m m m ...                                │
   │  P2  ►  m m m m m m m m ...                                │
   │  ...                                                       │
   │  P11 ►  m m m m m m m m ...                                │
   └────────────────────────────────────────────────────────────┘
       Each partition is its own append-only file on one broker.
       Ordering is GUARANTEED within a partition, NEVER between.
       Consumer group can have up to 12 active consumers (one per partition).

   Choosing key = user_id:
      hash('u-42') = 7   → P7. All u-42 events on P7, in order.
      hash('u-99') = 2   → P2.
      Skewed user → skewed partition.

   Choosing key = null (sticky):
      Batch 1 → P5 for 2 seconds → batch 2 → P11 for 2 seconds → ...
      No per-key ordering. Balanced load when load is uniform.
```

## Why interviewers care

- Forces you to reason about **ordering scope** as a first-class design decision.
- Surfaces whether you can detect **hot-partition risk** in a workload before it bites in production.
- Tests **partition-count sizing math** — a real operational skill.
- Opens up follow-ups on rebalance storms, sticky assignment, and partition rebalancing strategies.

## Common beginner confusion

- **"More partitions = more throughput, always."** Only if your consumers can keep up; otherwise you pay overhead (more file descriptors, more leader elections, slower rebalances) for no gain.
- **"Kafka guarantees global ordering."** No. Per-partition only.
- **"I'll just use UUID as the key."** That gives perfect spread but breaks any per-entity ordering you might have wanted later. Pick the key based on your *ordering scope*, not on randomness.
- **"I can add partitions whenever I want."** You can, but `hash(key) % N` changes — existing per-key ordering is broken across the transition. Pre-size partitions instead.
- **"Hot partitions auto-balance."** They don't. The hot key is sticky to its partition forever (until you change the key strategy).
- **"Consumer parallelism = number of consumers."** It's `min(consumers, partitions)`. Extras sit idle.

## Brute force approach

"Just use `key = null` and let Kafka round-robin." Works for telemetry streams where ordering doesn't matter. Breaks for any event-driven domain with per-entity invariants (orders, payments, user state changes).

"Just use `key = customer_id`." Works until you have one customer doing 70% of traffic. Then that partition is your bottleneck and the other 23 partitions are idle. Frequent enterprise SaaS failure mode.

## Optimal approach

The partition key choice flows from **one question**: *what is the ordering scope I need to preserve?*

1. **No ordering needed** (metrics, telemetry, click stream) → key = null, sticky partitioner, max throughput.
2. **Per-entity ordering** (user, order, account) → key = entity_id. Watch for skew.
3. **Per-tenant ordering with intra-tenant parallelism** → composite key: `tenant_id + ":" + hash(sub_id) % N_subpartitions`. Use when one tenant dominates.
4. **Strict global ordering** → topic with 1 partition. Throughput capped at single-broker write rate. Rarely the right answer.

Partition count sizing:
- Target ~10MB/s per partition per consumer.
- Cap at ~4000 partitions per broker (file descriptor and metadata overhead).
- Plan for 2-3x growth — repartitioning is painful.
- Replication factor = 3 for production (RF-1 broker failures tolerated).

Hot-partition detection: monitor per-partition lag and message rate. If one partition is >2x the others, you have skew. Mitigations: composite keys, dedicated topic for the whale tenant, or app-level sharding.

## Solution

### Picking the key

```javascript
// Wrong: random UUID — kills per-user ordering
producer.send({ topic: 'notifications', messages: [{
  key: uuid(),  // ← every message a different partition
  value: JSON.stringify(notif),
}]});

// Right (most cases): the entity whose ordering you care about
producer.send({ topic: 'notifications', messages: [{
  key: notif.userId,            // all events for a user → one partition → ordered
  value: JSON.stringify(notif),
}]});

// Right (skew mitigation): composite key for whale tenants
function partitionKey(notif) {
  const subBucket = murmurhash3(notif.id) % 8;     // 8 sub-buckets per tenant
  return `${notif.userId}:${subBucket}`;
}
```

### Custom partitioner for sophisticated routing

```java
public class TenantAwarePartitioner implements Partitioner {
  @Override
  public int partition(String topic, Object key, byte[] keyBytes,
                       Object value, byte[] valueBytes, Cluster cluster) {
    int numPartitions = cluster.partitionCountForTopic(topic);
    String k = (String) key;
    if (k.startsWith("whale:")) {
      // dedicated 4-partition slice for whale tenants
      int sub = Math.abs(murmur2(keyBytes)) % 4;
      return numPartitions - 4 + sub;
    }
    // remainder of the keyspace uses the rest of the partitions
    return Math.abs(murmur2(keyBytes)) % (numPartitions - 4);
  }
}
```

### Sizing the partition count

```
throughput target  : 100 MB/s
per-partition rate : ~10 MB/s sustainable
partitions needed  : 10  (minimum)
consumer parallelism wanted: 8 active consumers
partitions needed  : ≥ 8
growth headroom    : 2x → 16

Final: create with 24 partitions.
Replication factor: 3.
Min in-sync replicas: 2.
```

### Detecting hot partitions

```bash
# Per-partition lag
kafka-consumer-groups.sh --bootstrap-server $BROKER \
  --describe --group wallet-credit | sort -k 6 -n

# Per-partition message rate
kafka-run-class.sh kafka.tools.JmxTool \
  --object-name 'kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic=notifications,partition=*'
```

If partition 7 sees 4x the rate of partition 4, you have skew. Either accept it (if traffic justifies dedicated capacity) or split the key.

## Step-by-step dry run

Scenario: notifications topic, 6 partitions, key = `user_id`, three users: u-1 (light), u-2 (heavy), u-3 (light).

```
hash('u-1') % 6 = 4    → P4
hash('u-2') % 6 = 1    → P1
hash('u-3') % 6 = 4    → P4
(collision: u-1 and u-3 share P4)

Throughput per partition during a steady burst:
   P0:  0 msg/s
   P1: 50 msg/s   ← all u-2 traffic
   P2:  0 msg/s
   P3:  0 msg/s
   P4:  3 msg/s   ← u-1 + u-3
   P5:  0 msg/s

Consumer parallelism: 6 consumers in the group.
Active work:
   c0 (P0)  idle
   c1 (P1)  drowning
   c2 (P2)  idle
   c3 (P3)  idle
   c4 (P4)  light
   c5 (P5)  idle

5 idle consumers paying full cost; 1 consumer is the bottleneck.
```

Fix: composite key for u-2 only.
```
key = 'u-2:0', 'u-2:1', ..., 'u-2:7'  (eight buckets)
hash distributes those across P0..P5.
Result: u-2 throughput spread over up to 6 partitions; intra-u-2 ordering relaxed (we now have ordering only within a `u-2:N` bucket).
```

Tradeoff: u-2's events are no longer in a single global order. If your business logic depends on per-user ordering, this trade isn't free — you need to either redesign for partial ordering or carve u-2 onto a dedicated topic.

### Add a partition mid-flight

```
T=0    Topic has 6 partitions. hash('u-1') % 6 = 4 → u-1 on P4.
T=1    kafka-topics.sh --alter --partitions 12
T=2    hash('u-1') % 12 = 2 → u-1 now on P2.

   Net: u-1's events are split across P4 (old) and P2 (new).
   In the transition window, a consumer pulling from P2 sees a u-1 event
   while a consumer pulling from P4 still has older u-1 events queued.
   Per-key ordering is broken until P4's old u-1 events drain.
```

This is why **partition count is a one-shot decision**. Plan ahead, or pre-create more partitions than you need and let them stay empty.

## How to think aloud in the interview

> "First question for me is: what's the ordering scope? For a notifications topic I'd guess we want per-user ordering — if you mark a notification read then unread, those events better arrive in that order to whoever's denormalizing. So the partition key is `user_id`.
>
> Next: what's the traffic shape? If it's roughly uniform across users, `user_id` hashes evenly and we're done. If we have whale tenants — say one Slack workspace with a million users while most workspaces have 10 — we'll get a hot partition. To mitigate I'd compose the key for known whales: `user_id:hash(notif_id) % 8`, which spreads a whale's load across 8 sub-buckets at the cost of cross-notification ordering for that user. Or I'd carve whales onto a dedicated topic with their own partition count.
>
> For partition count: I'd size based on throughput. ~10MB/s sustainable per partition, multiply by 2-3 for headroom, and aim for at least as many partitions as I expect consumers in a group. For 100MB/s and 8 consumers I'd start at 24 partitions with RF=3.
>
> Critical gotcha: adding partitions later breaks per-key ordering during the transition because `hash(key) % N` changes. So I'd over-provision upfront rather than plan to scale partition count later. Adding *brokers* is easy; adding *partitions* breaks ordering.
>
> One more thing: if I expected `key=null`, modern Kafka uses a sticky partitioner — batches go to one partition for a few seconds before switching. Great for throughput, but not even per-message round-robin. I'd flag that for the interviewer."

## Important takeaways

- **Partition key determines ordering scope** (ordered within partition, never between).
- **Partition count is the ceiling on consumer parallelism** within a group.
- **Hash skew = hot partition** — common failure mode for tenant-keyed topics.
- **Adding partitions breaks per-key ordering** in the transition window. Pre-size.
- **Sticky partitioner (Kafka 2.4+)** batches `key=null` messages to one partition at a time.
- **Composite keys** trade per-entity ordering for hot-spot mitigation.
- **Custom partitioners** are powerful but must be consistent across producers and rebalances.
- **Replication factor 3, min-ISR 2** is the production default.

## Variants

1. **Custom partitioner for whale tenants.** Carve out a sub-range of partitions for known heavy tenants.
2. **Two topics for one logical stream.** `orders-whale` and `orders-rest`, different partition counts.
3. **Hash-then-modulo with consistent hashing.** Used by some non-Kafka systems to soften the cost of partition-count changes.
4. **Sticky partitioner explained.** Default since 2.4 — improves batching and broker throughput at the cost of per-message round-robin.
5. **Header-based routing (KIP-808).** Newer Kafka feature: route on headers without key. Niche but interview-worthy trivia.
6. **Single-partition topic for strict global ordering.** Throughput capped at one broker's write rate. Reserved for control planes, not data planes.
7. **Time-based partitioning is an anti-pattern.** Creates daily hot partitions.

## Revision notes

> **kafka partition design — 60 second recap**
> - **Ordering** is per-partition, not per-topic. Pick key = entity whose ordering you need.
> - **Consumer parallelism** = `min(consumers in group, partitions)`. Plan partitions ≥ desired consumer fanout.
> - **Hash skew → hot partition.** Composite key or dedicated topic for whales.
> - **Adding partitions later breaks per-key ordering.** Pre-size at 2-3x.
> - **Sticky partitioner** is the default for `key=null` — batches to one partition for seconds at a time.
> - **Sizing rule:** ~10 MB/s per partition; cap at ~4000 partitions per broker.
> - **Replication factor 3 + min-ISR 2** for production.
> - **Trap:** UUID key (no ordering, wasted parallelism opportunity).
> - **Trap:** time-based key (today's hot partition).
> - **Trap:** repartitioning to "scale" (breaks ordering, expensive rebalance).
