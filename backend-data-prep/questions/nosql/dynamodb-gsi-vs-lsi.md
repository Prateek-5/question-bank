# DynamoDB: GSI vs LSI — when to pick which

## Source / Origin
- Asked in every DynamoDB modeling round. Senior signal if you also discuss write amplification.
- Concept reference: `backend-data-prep/nosql/05-dynamodb-cassandra.md`.

## Why this question matters in interviews
GSI and LSI both give you alternate access patterns, but they're **wildly different**: LSI shares the partition (limited scale), GSI is a copy of the table (separate capacity). Picking the wrong one corners you operationally. Senior signal: you cite write amplification, strong vs eventual consistency, the 10 GB-per-PK ceiling for LSI, and the "GSI is the right default" rule.

## Concepts involved

### Syntax to lock in

```javascript
// Global Secondary Index — different PK and/or SK
{
  IndexName: "byEmail",
  KeySchema: [
    { AttributeName: "email", KeyType: "HASH" }
  ],
  Projection: { ProjectionType: "ALL" }    // or KEYS_ONLY, INCLUDE
}

// Local Secondary Index — same PK, different SK
{
  IndexName: "byCreatedAt",
  KeySchema: [
    { AttributeName: "userId",    KeyType: "HASH"  },   // SAME as base
    { AttributeName: "createdAt", KeyType: "RANGE" }
  ],
  Projection: { ProjectionType: "ALL" }
}
```

### GSI vs LSI side-by-side

| Aspect | GSI | LSI |
|---|---|---|
| PK | Different from base | **Same as base** |
| SK | Different (optional) | Different |
| Created when | Anytime | Only at table creation |
| Consistency | Eventual (default) | Strong option available |
| Capacity | Separate WCU/RCU | Shares base table's |
| Limit per table | 20 | 5 |
| Storage cap | Independent | **10 GB per partition** combined with base |
| Cost model | Pay for index size + writes | No extra capacity but inflates partition |
| Replicates on every write | Yes (async) | Yes (sync) |

### Edge cases / interview traps

1. **LSI 10 GB limit per partition.** If a single partition (one PK value) plus all its LSIs exceeds 10 GB, you cannot insert more items into that partition. Hard cap, no migration.
2. **LSI strongly consistent reads** — only LSI gives you strong reads on a non-base SK. GSI is always eventual on reads.
3. **GSI write amplification.** Every base write that touches indexed attributes also writes to each affected GSI. 5 GSIs ⇒ 6× WCU per write.
4. **GSI throttling is separate.** A hot GSI can throttle even when the base is fine.
5. **GSI Projection types** — `KEYS_ONLY` (cheapest), `INCLUDE` (specified attrs), `ALL` (full row). Pick to minimize index size.
6. **Sparse GSI** — items without the indexed attribute are excluded. Useful: `gsi1pk` only set on flagged rows.
7. **LSI can't be added later.** GSIs can.
8. **Both indexes incur eventual-consistency window** on read (especially GSI) — design accordingly.

## Mental Model

> - **LSI** = a second sort order on the same locker.
> - **GSI** = a whole new warehouse with a different locker numbering.

```
   LSI:  same partition, different sort
   ┌───────────────────────────────┐
   │ partition PK=userId           │
   │  base SK: orderId             │
   │  LSI  SK: createdAt           │
   │  → all items co-located here  │
   └───────────────────────────────┘

   GSI: separate physical structure
   ┌─────────────────────┐         ┌─────────────────────┐
   │ BASE TABLE          │  async  │ GSI (byEmail)       │
   │ PK=userId, SK=...   │ ──────▶ │ PK=email            │
   └─────────────────────┘         └─────────────────────┘
                                   (own partitions, own capacity)
```

## Why interviewers care

- Tests **capacity-and-cost reasoning** — GSI write amplification is the most common operational surprise.
- Tests **scaling awareness** — LSI's 10 GB-per-PK cap is the silent killer.
- Tests **modeling-by-access-pattern** — alternate access without rewriting.

## Common beginner confusion

- "LSI is just a cheaper GSI." It's actually *more* restrictive (10 GB cap, must define at creation).
- "GSI gives strong consistency." It doesn't — always eventual.
- "More indexes = more flexibility." Each one multiplies write cost.
- "Projection: ALL is fine for everything." Burns storage and inflates partition size.
- "GSI throttle = base table throttle." Independent capacities; you can throttle one without the other.

## Brute force approach

Project ALL on every GSI, add LSIs liberally. Works for small workloads; costs you 6× WCU and bumps you into 10 GB-per-partition limits at scale.

## Optimal approach

Rules of thumb:
1. **Default to GSI.** Add LSI only when you need strong-consistent reads on an alternate SK.
2. **Minimize Projection.** Start with `KEYS_ONLY`; promote to `INCLUDE` for specific attrs; only `ALL` if the index is the only way you'll fetch the row.
3. **Sparse GSIs** for flagged subsets. Only items with the attribute participate.
4. **No more than ~3 GSIs** unless you've measured write cost.
5. **Never use LSI** if the partition might exceed 10 GB across base + LSIs.

## Solution (DynamoDB JSON)

```json
// === Base table + 2 GSIs ===
{
  "TableName": "Users",
  "KeySchema": [
    { "AttributeName": "userId", "KeyType": "HASH" }
  ],
  "AttributeDefinitions": [
    { "AttributeName": "userId",  "AttributeType": "S" },
    { "AttributeName": "email",   "AttributeType": "S" },
    { "AttributeName": "country", "AttributeType": "S" },
    { "AttributeName": "createdAt", "AttributeType": "S" }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "byEmail",
      "KeySchema": [{ "AttributeName": "email", "KeyType": "HASH" }],
      "Projection": { "ProjectionType": "KEYS_ONLY" }
    },
    {
      "IndexName": "byCountry",
      "KeySchema": [
        { "AttributeName": "country",   "KeyType": "HASH" },
        { "AttributeName": "createdAt", "KeyType": "RANGE" }
      ],
      "Projection": {
        "ProjectionType": "INCLUDE",
        "NonKeyAttributes": ["name", "tier"]
      }
    }
  ]
}

// === Base table + LSI (for strong-consistent alt sort) ===
{
  "TableName": "Orders",
  "KeySchema": [
    { "AttributeName": "userId",  "KeyType": "HASH"  },
    { "AttributeName": "orderId", "KeyType": "RANGE" }
  ],
  "AttributeDefinitions": [
    { "AttributeName": "userId",    "AttributeType": "S" },
    { "AttributeName": "orderId",   "AttributeType": "S" },
    { "AttributeName": "createdAt", "AttributeType": "S" }
  ],
  "LocalSecondaryIndexes": [
    {
      "IndexName": "byCreatedAt",
      "KeySchema": [
        { "AttributeName": "userId",    "KeyType": "HASH"  },
        { "AttributeName": "createdAt", "KeyType": "RANGE" }
      ],
      "Projection": { "ProjectionType": "ALL" }
    }
  ]
}
```

### Querying indexes

```javascript
// GSI query (eventual by default)
await ddb.query({
  TableName: "Users",
  IndexName: "byEmail",
  KeyConditionExpression: "email = :e",
  ExpressionAttributeValues: { ":e": "x@y.com" }
});

// LSI strong-consistent read
await ddb.query({
  TableName: "Orders",
  IndexName: "byCreatedAt",
  KeyConditionExpression: "userId = :u AND createdAt > :t",
  ExpressionAttributeValues: { ":u": "U-1", ":t": "2026-05-01" },
  ConsistentRead: true     // legal on LSI; illegal on GSI
});
```

## Step-by-step dry run

```
Workload: 10M users, each user has an email and country.
3 access patterns:
  A1. Get user by userId.
  A2. Get user by email.
  A3. List users in country, newest first.

Design with GSIs:
  Base: PK=userId
  GSI1: PK=email          (KEYS_ONLY)         supports A2
  GSI2: PK=country, SK=createdAt (INCLUDE name, tier)  supports A3

  WCU on insert = 1 base + 2 GSI = 3 WCU per user.
  Cost: ~3× write throughput vs single table.

Workload: orders for a user with multiple sort orders.
  Base: PK=userId, SK=orderId
  Need to query by createdAt with STRONG consistency (race after write).
  → LSI byCreatedAt fits.
  Constraint: every user's data + LSI must stay < 10 GB combined.

Risky: a single big user with 50K large orders may hit 10 GB cap.
  Mitigation: avoid LSI; use GSI byCreatedAt and tolerate eventual reads.
```

## How to think aloud in the interview

> "Default to GSI. I'd reach for an LSI only when I need strong-consistent reads on an alternate SK *and* I'm confident no partition will ever exceed 10 GB. The LSI 10 GB cap is unfixable without a table rebuild.
>
> GSI write amplification is real: every base write that touches an indexed attribute writes to each affected GSI. So I cap myself at ~3 GSIs unless I've measured. I also pick the smallest viable Projection — KEYS_ONLY by default, INCLUDE for specific attrs, ALL only if the GSI is the only way I'll fetch the row.
>
> Sparse GSIs are underused. If only 1% of items have a `flaggedAt` attribute, I make `flaggedAt` the GSI PK; only those 1% participate in the index. That's how I model 'pending review' or 'starred' queues without bloating capacity.
>
> One thing to call out: GSI reads are always eventual. If the access pattern demands strong consistency, it's either LSI or denormalize."

## Important takeaways

- **LSI = same PK, different SK, at table creation only, strong-read option, 10 GB-per-partition cap.**
- **GSI = different PK/SK, anytime, eventual reads only, separate capacity.**
- **Default to GSI.**
- **Write amplification = N GSIs × every relevant base write.**
- **Projection: prefer KEYS_ONLY → INCLUDE → ALL** in that order.
- **Sparse GSI** for flagged subsets — only items with the attribute index.
- **Max: 20 GSIs, 5 LSIs per table.**

## Variants

1. **GSI overloading** — `gsi1pk` and `gsi1sk` as generic attributes; single-table design.
2. **GSI for adjacency list** — `gsi1pk = childId` to walk reverse relationships.
3. **Time-bucketed GSI** — `gsi1pk = yyyy-mm-dd` to scope hot writes per day.
4. **Sparse GSI alarm queue** — `alertAt` attr only set on alerting rows.
5. **DynamoDB Streams + Lambda** as a poor-man's GSI when access patterns shift over time.
6. **LSI for "latest" reads** — `userId` + `lastModified` for read-after-write on the same partition.

## Revision notes

> **GSI vs LSI — 60s recap**
> - LSI: same PK, alt SK, at creation only, strong-read option, 10 GB-per-partition.
> - GSI: any PK/SK, anytime, eventual reads, separate capacity.
> - Default to GSI.
> - Write amp = base + N affected GSI writes per write.
> - Projection: KEYS_ONLY → INCLUDE → ALL.
> - Sparse GSI for subset queries.
> - Limits: 20 GSI, 5 LSI.
> - LSI strong-read = only way to get strong consistency on alt sort.
> - LSI 10 GB cap is unfixable; avoid for any partition that might grow.
