# DynamoDB: Partition key design — even distribution

## Source / Origin
- Asked in every AWS-shop interview, especially Amazon. The single most important DynamoDB question.
- Concept reference: `backend-data-prep/nosql/05-dynamodb-cassandra.md`.

## Why this question matters in interviews
DynamoDB has **no joins, no ad-hoc filters**. You either query by PK or you scan. Pick the wrong PK and you spend 10× the cost or hit `ProvisionedThroughputExceeded` on a single hot partition. Senior signal: you reason about **request distribution**, **partition limits (3000 RCU / 1000 WCU per partition)**, and pick a PK with **high cardinality + even access**.

## Concepts involved

### Syntax to lock in

```javascript
// CreateTable
{
  TableName: "Users",
  KeySchema: [
    { AttributeName: "userId", KeyType: "HASH" }       // partition key
  ],
  AttributeDefinitions: [{ AttributeName: "userId", AttributeType: "S" }],
  BillingMode: "PAY_PER_REQUEST"
}

// GetItem (point lookup)
{ TableName: "Users", Key: { userId: "U-123" } }

// PutItem
{ TableName: "Users", Item: { userId: "U-123", name: "Alice", createdAt: "..." } }
```

### Partition limits (memorize)

| Metric | Limit per partition |
|---|---|
| Throughput | 3000 RCU + 1000 WCU |
| Storage | 10 GB before split |
| Item size | 400 KB max |

If your PK takes >1000 WCU per second, you have a **hot partition** — you don't get the rest of the table's capacity to bail you out.

### Edge cases / interview traps

1. **Low-cardinality PK** — `country`, `status`, `tenantId` if you have 10 tenants. Concentrates traffic.
2. **Monotonic PK** — timestamps, sequence numbers, `createdAt`. New writes pile on one partition.
3. **Celebrity PK** — userId where one user is 1000× the average. Same hot-partition shape.
4. **Adaptive capacity helps but doesn't save you.** AWS will allocate more throughput to a hot partition over minutes, but burst limits still apply.
5. **Burst capacity** — unused capacity is borrowed for up to 5 min. Don't rely on it.
6. **Partition splits on storage > 10 GB OR throughput sustained > limit.** You don't control split timing.
7. **A scan reads every partition.** Avoid in steady-state code.
8. **Composite key (PK + SK)** changes the picture — the *partition* is still by PK; SK orders rows within.

## Mental Model

> DynamoDB is a giant hash map keyed by partition. Each partition is a physical shard with its own capacity. Your PK is the hash input.
>
> Goal: **every request lands on a different partition.** If the PK is uniformly random across many users/devices/orders, that's automatic. If it's `status: "PAID"` and 80% of requests are PAID, three partitions hold the data and one carries 80% of the load.

```
   GOOD: PK = userId (high cardinality, even access)
        ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
   →    │ P1   │ │ P2   │ │ P3   │ │ P4   │     uniform load
        └──────┘ └──────┘ └──────┘ └──────┘

   BAD: PK = status (4 distinct values, skewed)
        ┌──────┐ ┌──────┐ ┌█████┐ ┌──────┐
   →    │ NEW  │ │ SHIP │ │ PAID │ │ CANC │     hot partition
        └──────┘ └──────┘ └█████┘ └──────┘

   BAD: PK = orderId (high cardinality but monotonic — most reads target recent)
        ┌──────┐ ┌──────┐ ┌──────┐ ┌█████┐
   →    │ old  │ │ old  │ │ mid  │ │ NEW │     recent writes/reads cluster
        └──────┘ └──────┘ └──────┘ └█████┘
```

## Why interviewers care

- Tests **distribution reasoning** — the #1 DynamoDB skill.
- Tests **awareness of partition limits** — you've actually read the docs.
- Tests **honesty about hot partitions** — adaptive capacity isn't magic.
- Tests **modeling-by-access-pattern** — you start with the queries, not the entities.

## Common beginner confusion

- "DynamoDB autoscales, so PK doesn't matter." Per-partition limits are absolute.
- "I'll add a GSI to filter by other fields." GSI is a separate table with its own PK; same partition rules.
- "Scan is fine for small tables." It is — until they grow.
- "On-demand mode removes hot partitions." It doesn't; it just doesn't bill you for provisioned capacity.
- "Composite key (PK+SK) avoids hot partitions." Only if the PK is well-distributed. PK + SK with one PK value = one partition.

## Brute force approach

Use `userId` for everything; rely on adaptive capacity. Works for evenly distributed users; fails for celebrity userIds, monotonic IDs, or tables with one tenant dominating.

## Optimal approach

Walk through:
1. **List all access patterns** before picking a key. Write them down: "GetUserById", "ListOrdersForUser", "ListOrdersByStatus", etc.
2. Pick the PK that gives **even distribution AND a targeted query** for the most frequent access pattern.
3. For uneven access patterns, **write-shard** the PK: `userId#bucket(0..7)`.
4. For alternate access patterns, add **GSIs** with different PKs.
5. Verify with **CloudWatch ThrottledRequests** and **ConsumedReadCapacityUnits per partition** (use CloudWatch Contributor Insights for DynamoDB).

## Solution (DynamoDB JSON)

```json
// === Users: high cardinality, even access ===
{
  "TableName": "Users",
  "KeySchema": [{ "AttributeName": "userId", "KeyType": "HASH" }],
  "AttributeDefinitions": [{ "AttributeName": "userId", "AttributeType": "S" }],
  "BillingMode": "PAY_PER_REQUEST"
}

// === Orders: PK = userId, SK = orderId (composite) ===
{
  "TableName": "Orders",
  "KeySchema": [
    { "AttributeName": "userId",  "KeyType": "HASH"  },
    { "AttributeName": "orderId", "KeyType": "RANGE" }
  ]
}
// Query: { userId: "U-123" } → all orders for user, ordered by orderId
// Anti-pattern: if 1 user dominates writes, switch to write-sharded PK.

// === Write-sharded PK for celebrity-safe events ===
function shardedPK(userId) {
  return `${userId}#${Math.floor(Math.random() * 10)}`;   // 10 buckets
}
// PutItem: { PK: shardedPK("U-celeb"), SK: timestamp, ... }
// Query: scatter-gather across 10 buckets:
//   for s in 0..9: Query({ PK: "U-celeb#" + s, SK BETWEEN ... }) → merge
```

```javascript
// === Detect hot partition in CloudWatch ===
// Use Contributor Insights:
aws dynamodb update-contributor-insights \
  --table-name Orders \
  --contributor-insights-action ENABLE

// Then inspect top contributors by partition key in the AWS console.
```

### Adaptive vs write-sharding decision

```
Access pattern: 1 celebrity user = 80% of writes, total 5000 WCU
  Without sharding:  one partition tries to absorb 4000 WCU; hits 1000 WCU cap → throttle.
  With sharding (10 buckets):  each bucket absorbs 400 WCU; safe.

Read amplification cost:
  Without sharding:  Query(PK=userId) hits 1 partition.
  With sharding:     Query × 10 buckets → 10× read cost, but each bucket is small.
```

## Step-by-step dry run

```
Workload: 1M users, evenly active. Plus 1 celebrity = 80% of writes.

PK = userId   (no sharding)
  1M users distributed across ~64 partitions → ~16K users/partition.
  Celebrity userId lands on partition P-celeb.
  Celebrity writes = 4000 WCU sustained.
  P-celeb cap = 1000 WCU → throttle 75% of celebrity writes.

PK = userId#bucket(rand0..9)
  Celebrity writes split across 10 buckets → 400 WCU each → OK.
  Read for celebrity = 10 parallel Queries → merge results in app.
  Cost: 10× the read units but no throttling.

PK = bucketHash(userId) % 100  (always sharded)
  100 buckets per user. Even celebrity. But reads always 100-way merge → expensive.
  Only worth it if everyone is potentially a celebrity (chat platforms, hashtag streams).

PK = orderId (monotonic, e.g., timestamp-based)
  Every new order goes to the partition holding the highest orderId range.
  Hot partition for writes; cold for old data.
  FIX: PK = orderId#shard(0..n) where shard = hash(payload) % n.
```

## How to think aloud in the interview

> "Three properties: high cardinality, even access, not monotonic. I list every access pattern before picking the key. The PK has to give a targeted query — never a Scan — for the dominant pattern.
>
> Per-partition limits are 1000 WCU / 3000 RCU. Adaptive capacity helps over minutes but won't save you from a sustained celebrity. So I write-shard: `userId#bucket(0..9)`. Writes scatter to 10 buckets; reads do a 10-way merge.
>
> For monotonic IDs like `orderId` based on timestamp, I always add a hash suffix. Otherwise the newest writes pile up on one partition.
>
> Composite key `(PK, SK)` doesn't change the partition story — partition is still by PK; SK orders within. So the question 'what's my PK' is independent of 'what's my SK'.
>
> I monitor Contributor Insights for hot partition keys. If one PK is more than 10% of consumed capacity, I plan a re-shard."

## Important takeaways

- **PK = partition. Per-partition limit = 1000 WCU / 3000 RCU.** Hard ceiling.
- **High cardinality + even access + non-monotonic.** Three properties to hit.
- **Write-sharding for celebrity / monotonic PKs.** `key#bucket(0..n)`.
- **GSIs are separate tables; same partition rules apply.**
- **Adaptive capacity ≠ unlimited.** Burst over minutes, not seconds.
- **Composite key (PK+SK) doesn't change partition rules.**
- **Monitor with Contributor Insights** — top contributors by partition key.

## Variants

1. **GSI overload** — single PK pattern with `gsi1pk`/`gsi1sk` for alternate access (covered in single-table design file).
2. **Write-sharded GSI** — apply same trick to GSI for alternate-access hot keys.
3. **Sparse index** — only index items with a specific attribute, drastically reduces GSI size.
4. **Time-based sharding** — for telemetry, `PK = deviceId#yyyy-mm-dd` distributes both by device and day.
5. **Zone-based shards** — `PK = country#userId` for data sovereignty.
6. **On-demand capacity** — same partition limits but no provisioning; useful for unpredictable load.

## Revision notes

> **dynamodb PK design — 60s recap**
> - PK = partition. Per-partition limit: 1000 WCU + 3000 RCU + 10 GB.
> - Need: high cardinality + even access + non-monotonic.
> - Celebrity → write-shard suffix `userId#bucket(0..9)`.
> - Monotonic ID → add hash suffix.
> - Composite (PK+SK) doesn't help with hot partition; PK still defines shard.
> - GSI is a separate table with its own PK; same rules.
> - Adaptive capacity = minutes; doesn't fix sustained celebrity.
> - Monitor: CloudWatch Contributor Insights → top contributors by partition.
> - List access patterns BEFORE picking a key.
