# Design a fan-out: one event, many consumers, each with independent semantics

## Source / Origin
- Foundational pub/sub pattern; appears in every messaging system design.
- Notification systems, search indexers, audit trails, derived views.
- Concept reference: `backend-data-prep/messaging/fan-out.md`.

## Why this question matters in interviews
Fan-out separates candidates who think "queue = one consumer" from those who think in event streams. The signal: do you choose Kafka consumer groups, SNS->SQS, or RabbitMQ exchanges based on consumer semantics? Can you explain why each consumer needs its own offset / queue / subscription? Do you handle the slow-consumer problem (one downstream blocks all)? Senior candidates also know about fan-out with filtering and exactly-once-per-consumer concerns.

## Concepts involved

### Syntax to lock in

```bash
# Kafka: each consumer group reads independently, owns its offsets
kafka-console-consumer.sh --topic orders --group analytics-svc
kafka-console-consumer.sh --topic orders --group notifications-svc
kafka-console-consumer.sh --topic orders --group search-indexer
# All three see every record. Each commits its own offset.
```

```yaml
# SNS → SQS fan-out (AWS)
SNS Topic: orders-events
  ├─ SQS subscription: notifications-queue
  ├─ SQS subscription: search-index-queue
  └─ SQS subscription: analytics-queue
# SNS replicates each published message to every subscribed queue.
# Each consumer drains its own queue at its own pace.
```

```bash
# RabbitMQ: fanout exchange
rabbitmqadmin declare exchange name=orders.events type=fanout
rabbitmqadmin declare queue name=notif-q
rabbitmqadmin declare queue name=index-q
rabbitmqadmin declare binding source=orders.events destination=notif-q
rabbitmqadmin declare binding source=orders.events destination=index-q
# Publish to orders.events → message duplicated into all bound queues.
```

```yaml
# Redis Streams + consumer groups (smaller scale)
XADD orders.events * type=created order_id=ord-1
XREADGROUP GROUP notifications c1 COUNT 10 STREAMS orders.events >
XREADGROUP GROUP indexer       c1 COUNT 10 STREAMS orders.events >
```

### Edge cases / interview traps

1. **Consumer group = one logical consumer.** If you put two services in one Kafka group, they split partitions — they don't both see every event.
2. **SNS->SQS gives per-consumer queue durability.** If a consumer is down, its queue accumulates; others unaffected.
3. **RabbitMQ fanout drops messages without bound queues.** Bind before publish, or use mandatory + alternate exchange.
4. **Slow consumer problem.** In a single shared queue, slow consumer holds messages. With fan-out (per-consumer queues), each backs up independently.
5. **At-least-once everywhere.** Fan-out doesn't change delivery semantics; each consumer still needs idempotency.
6. **Event ordering** preserved per-partition in Kafka; per-queue in RabbitMQ; not across consumers.
7. **Schema evolution risk.** Different consumers may be on different deployment versions; producer must add fields backward-compatibly.
8. **Cost of duplication.** SNS->SQS means N storage costs; Kafka is one log shared by all groups (cheaper).
9. **Filtering at fan-out.** SNS message attributes + filter policies; RabbitMQ topic exchange; Kafka uses consumer-side filter (no native filter on the broker).

## Mental Model

The **"newspaper subscription"** model.

```
   Publisher (newspaper) writes one edition.

   Kafka model:        one big bulletin board (log).
                       Each subscriber walks up, reads from their
                       bookmark, advances bookmark independently.
                       Newspaper doesn't track who has read what.

   SNS->SQS model:     publisher prints N copies, drops one into each
                       subscriber's mailbox.
                       Each mailbox fills/empties independently.

   RabbitMQ fanout:    exchange acts as a sorting room; copies the
                       message into every bound mailbox (queue).

   Common property: each subscriber consumes at its own pace, with
   its own retention/visibility, and one slow subscriber does not
   block others.
```

## Why interviewers care

- Surfaces understanding of pub/sub vs queue semantics.
- Tests whether you handle the "slow consumer" failure mode.
- Differentiates message broker choices by use case.

## Common beginner confusion

- "Multiple consumers in one Kafka group give me fan-out." Opposite — they split the work.
- "Fan-out means everyone gets every message in real time." It means everyone *can* get every message, but they consume at their own pace.
- "I can fan out to thousands of subscribers." Practical limits: SNS subscription limits, queue cost, broker fan-out throughput.
- "Filtering reduces fan-out load." Yes, but each broker handles it differently — Kafka needs consumer-side filter, SNS has filter policies.
- "Order is preserved across fan-out." Per stream/partition only; cross-consumer there's no shared clock.

## Brute force approach

Producer makes N HTTP calls — one per downstream. Tight coupling, retry storms, cascading failure. Don't.

## Optimal approach

1. **Pick the broker by semantics:**
   - Many consumers, replay possible, log-based: **Kafka**.
   - Per-consumer mailbox isolation, AWS-native: **SNS->SQS**.
   - In-cluster routing flexibility, low volume: **RabbitMQ fanout/topic**.
2. **Each consumer = independent group/queue/subscription** with its own offsets, retries, DLQ.
3. **Producer fires once** to the fan-out point; broker replicates.
4. **Idempotent consumers** (at-least-once delivery is the floor).
5. **Filtering at the broker** when supported (SNS filter policies); consumer-side filter otherwise.

## Solution

```
┌──────────────────────────────────────────────────────────────────────┐
│           Kafka fan-out (single log, multiple groups)               │
├──────────────────────────────────────────────────────────────────────┤
│   producer ─► orders (12 partitions)                                 │
│                  │                                                   │
│                  ├─► group: notifications-svc  (own offsets)         │
│                  ├─► group: search-indexer     (own offsets)         │
│                  ├─► group: analytics-pipeline (own offsets)         │
│                  └─► group: audit-archiver     (own offsets)         │
│                                                                      │
│   - Storage cost: 1× the log (regardless of group count)             │
│   - Retention: producer-side (e.g., 7 days)                          │
│   - Replay: any group can reset offsets to relive history           │
│   - Slow group: ITS lag grows; others unaffected                    │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│           SNS→SQS fan-out (mailbox model)                           │
├──────────────────────────────────────────────────────────────────────┤
│   producer ─► SNS topic: orders-events                              │
│                  │                                                   │
│                  ├─► SQS: notif-queue       ─► notif-consumer       │
│                  ├─► SQS: index-queue       ─► index-consumer       │
│                  └─► SQS: analytics-queue   ─► analytics-consumer   │
│                                                                      │
│   - Each queue can have its own DLQ                                  │
│   - Filter policies on SNS subscription (per-attribute)              │
│   - Each subscriber durability isolated                             │
│   - Storage: N× (one per consumer)                                   │
│   - No replay (SQS is fire-and-forget once delivered)                │
└──────────────────────────────────────────────────────────────────────┘
```

```java
// ===== Kafka: producer fires once =====
producer.send(new ProducerRecord<>("orders", orderId, eventBytes));

// ===== Kafka: each consumer is a different group =====
// Service A (notifications)
Properties pA = base.clone();
pA.put(GROUP_ID_CONFIG, "notifications-svc");
new KafkaConsumer<>(pA).subscribe(List.of("orders"));

// Service B (search index)
Properties pB = base.clone();
pB.put(GROUP_ID_CONFIG, "search-indexer");
new KafkaConsumer<>(pB).subscribe(List.of("orders"));

// Both see every record; commit independently.

// ===== SNS->SQS with filter policy =====
// Publisher
SNSClient.publish(PublishRequest.builder()
  .topicArn("arn:aws:sns:...:orders-events")
  .message(eventJson)
  .messageAttributes(Map.of(
    "event_type", MessageAttributeValue.builder().dataType("String")
        .stringValue("OrderCreated").build(),
    "region",     MessageAttributeValue.builder().dataType("String")
        .stringValue("US").build()))
  .build());

// Subscription filter: only US OrderCreated events
{
  "event_type": ["OrderCreated"],
  "region":     ["US"]
}
```

```yaml
# Terraform sketch for fan-out
resource "aws_sns_topic" "orders" { name = "orders-events" }

resource "aws_sqs_queue" "notif" { name = "notif-queue"; ... }
resource "aws_sqs_queue" "index" { name = "index-queue"; ... }

resource "aws_sns_topic_subscription" "notif" {
  topic_arn = aws_sns_topic.orders.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.notif.arn
  filter_policy = jsonencode({ event_type = ["OrderCreated", "OrderCancelled"] })
}
```

## Step-by-step dry run

Producer publishes OrderCreated for ord-7:

```
Kafka:
  t=0   producer.send → broker stores at orders/partition-3/offset-1000
  t=1   notifications-svc group: poll → reads offset 1000 → sends email
                                     commits offset 1001 in __consumer_offsets
  t=1   search-indexer group:     poll → reads offset 1000 → indexes to ES
                                     commits offset 1001 (separate row)
  t=5   analytics-pipeline (slow): poll → reads offset 1000 → batch process
                                     commits offset 1001 at t=10
  Broker storage: one copy; offsets are just per-group cursors.

SNS->SQS:
  t=0   producer publishes to SNS
  t=0   SNS replicates: enqueues to notif-queue, index-queue, analytics-queue
  t=1   notif-consumer dequeues from notif-queue; processes; deletes
  t=1   index-consumer dequeues from index-queue; processes; deletes
  t=5   analytics-consumer slower; still draining its queue
  If analytics-consumer down for 10 minutes:
       analytics-queue depth grows; notif/index unaffected.
       SQS retention (default 4 days) protects backlog.
```

Slow-consumer scenario:

```
Kafka:
  search-indexer is slow; its lag grows.
  notifications-svc keeps up at offset 5000.
  search-indexer at offset 2000. Lag = 3000.
  
  → operator alarm on consumer-group lag > N.
  → scale search-indexer consumers; rebalance assigns more partitions to new pods.
  → other groups unaffected.

SNS->SQS:
  index-queue depth grows (visible in CloudWatch).
  → scale Lambda concurrency or ECS task count.
  → notif-queue/analytics-queue unaffected.

Single shared queue (NOT fan-out, anti-pattern):
  All consumers compete for the same queue.
  Slow consumer holds messages; others starve. Head-of-line blocking.
  This is why fan-out uses per-consumer queues.
```

## How to think aloud in the interview

> "Fan-out = one event reaches N consumers. Three idiomatic implementations depending on stack:
>
> 1. **Kafka with multiple consumer groups** — single log, each group owns offsets. Best when replay matters or N is large. One storage cost.
> 2. **SNS→SQS** — SNS replicates to per-consumer queues. AWS-native. Each consumer durability is isolated; supports filter policies. N storage cost.
> 3. **RabbitMQ fanout/topic exchange** — broker copies into bound queues. Good for in-cluster routing flexibility.
>
> The non-negotiable principle: each consumer must have its own offset (Kafka) or its own queue (SQS/Rabbit). A slow consumer should affect only its own backlog, not others.
>
> Idempotency is required everywhere because all three are at-least-once.
>
> Filtering: SNS has subscription filter policies (broker-side, cheap); Kafka has no broker filter — consumers ignore irrelevant events; Rabbit can use topic exchanges with routing keys.
>
> The trap is putting multiple services in one Kafka consumer group — that's load balancing, not fan-out."

## Important takeaways

- Fan-out = one event, N independent consumers, each with own pace.
- Kafka: separate consumer groups; one log.
- SNS->SQS: separate queues; broker replicates.
- RabbitMQ: fanout exchange or topic exchange with bindings.
- Slow-consumer isolation is the core property — never share a queue across services.
- Idempotency required; at-least-once is the floor.
- Filtering: SNS filter policies, Rabbit topic exchange, Kafka consumer-side filter.

## Variants

1. **Hybrid fan-out** — Kafka topic ingested by a bridge that fans out to SNS for cross-account/region delivery.
2. **Cross-region fan-out** — MirrorMaker (Kafka) or SNS multi-region.
3. **Schema-based fan-out** — different consumers consume different fields; producer publishes superset.
4. **Time-windowed fan-out** — batch records, fan out aggregates instead of singletons.
5. **Materialised-view fan-out** — each consumer maintains a derived store (read model).

## Revision notes

> **fan-out — 60s recap**
> - One event, N independent consumers, each at own pace.
> - Kafka: consumer groups + one log.
> - SNS→SQS: per-consumer mailbox; broker replicates.
> - RabbitMQ: fanout/topic exchange with bindings.
> - Critical: per-consumer offset/queue → slow-consumer isolation.
> - At-least-once everywhere → idempotency required.
> - Filtering: SNS policies, Rabbit topic, Kafka client-side.
