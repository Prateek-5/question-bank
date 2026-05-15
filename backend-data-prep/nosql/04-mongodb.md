# MongoDB

## Why this matters in backend interviews

- Most-used document database; will appear in interview discussion any time NoSQL is mentioned.
- Senior signal: knowing **when not to use Mongo** (and being honest about it) is more valuable than knowing every operator.
- Real production debugging questions: aggregation slowness, missing indexes, replica set failover, schema sprawl.

---

## Core concepts

### Data model

- **Database** → **Collection** → **Document** (BSON; binary JSON with more types)
- No schema enforcement by default; can add **schema validation** (JSON Schema)
- `_id` is the primary key; ObjectId by default (12 bytes: 4 timestamp + 5 random + 3 counter)
- Documents are atomic — a single-document write is always atomic, even with nested arrays

### Embedding vs referencing

The central modeling decision.

#### Embed when:
- Child data is owned by the parent (lives and dies with it)
- Always queried together
- Small, bounded size (< 16 MB document limit; practical: keep < 1 MB)
- 1:few relationship (not 1:billions)

#### Reference when:
- Child is independent (shared across parents)
- Large or unbounded growth (a user's all-time messages)
- Need to query child without loading parent

#### Examples

```javascript
// Embed: order with items
{
  _id: ObjectId("..."),
  userId: ObjectId("..."),
  status: "PAID",
  items: [
    { sku: "A1", quantity: 2, unitPrice: 1200 },
    { sku: "B5", quantity: 1, unitPrice: 500 }
  ],
  total: 2900,
  createdAt: ISODate("2026-05-14T12:00:00Z")
}

// Reference: comments on a post (could be thousands)
// posts: { _id, title, body, ... }
// comments: { _id, postId: ObjectId("..."), body, ... }
```

Rule of thumb: **"6 rules of thumb" from Mongo docs** — embed by default unless the relationship is many-to-many or unbounded.

### Indexes

- B-tree (same as SQL)
- Single field, compound, multikey (on arrays), text, geospatial, hashed, partial, TTL, wildcard
- `_id` index is automatic and unique
- Compound index supports prefix queries: index on `(a, b, c)` supports queries on `(a)`, `(a, b)`, `(a, b, c)`

```javascript
db.orders.createIndex({ userId: 1, createdAt: -1 });
db.orders.createIndex({ "items.sku": 1 });  // multikey
db.orders.createIndex({ createdAt: 1 }, { expireAfterSeconds: 86400 });  // TTL
db.users.createIndex({ email: 1 }, { unique: true });
```

ESR rule: **Equality, Sort, Range** — design compound indexes in this order.

### Aggregation pipeline

A series of stages transforming documents. Each stage's output is the next's input.

Common stages:
- `$match` — filter (use early; uses indexes)
- `$project` — reshape (rename, compute fields)
- `$group` — aggregate
- `$sort` — order (use index when possible)
- `$limit`, `$skip`
- `$lookup` — join to another collection (use sparingly; expensive)
- `$unwind` — array → multiple docs
- `$facet` — multiple sub-pipelines in parallel

```javascript
db.orders.aggregate([
  { $match: { status: "PAID", createdAt: { $gte: ISODate("2026-01-01") } } },
  { $unwind: "$items" },
  { $group: {
      _id: "$items.sku",
      qty: { $sum: "$items.quantity" },
      revenue: { $sum: { $multiply: ["$items.quantity", "$items.unitPrice"] } }
  }},
  { $sort: { revenue: -1 } },
  { $limit: 10 }
]);
```

Performance tips:
- Put `$match` first (uses index)
- Sort by an indexed field early
- Avoid `$lookup` on huge collections; denormalize instead
- `$facet` runs sub-pipelines on the same input, great for dashboards

### Replica sets

- Group of mongod instances: 1 primary + N secondaries (+ optional arbiters)
- Primary accepts writes; secondaries replicate via oplog
- Failover: secondaries vote (Raft-like) to elect new primary (~10s typical)
- Read preference: `primary` (default), `primaryPreferred`, `secondary`, `nearest`

### Write concern

| Concern | Meaning |
|---|---|
| `w: 1` | Primary ack only (default in many drivers; can lose on primary failure) |
| `w: "majority"` | Majority of replica-set members ack |
| `j: true` | Durable to journal (fsync to disk) |
| `wtimeout` | Max time to wait for ack |

For correctness-sensitive writes: `{ w: "majority", j: true }`.

### Read concern

| Concern | Meaning |
|---|---|
| `local` | Latest local (may not be majority-committed) |
| `available` | Like local for sharded; faster |
| `majority` | Majority-committed (no rollback) |
| `linearizable` | Serial reads on a single shard primary |
| `snapshot` | Consistent snapshot across docs (for transactions) |

### Transactions

- Single-document writes are atomic (always)
- Multi-document transactions: supported since 4.0 (replica set), 4.2 (sharded)
- Use `session.startTransaction()` + `commitTransaction()`
- Cost: more expensive than RDBMS transactions; can fail with `TransientTransactionError` → retry
- **Avoid as your default**: model data to make single-doc atomic operations sufficient

### Sharding

- Shard cluster: `mongos` (router) + config servers (metadata) + multiple shards (each a replica set)
- Choose a shard key — hash or range
- Documents distributed by shard key; queries that include the shard key target a single shard
- Queries without the shard key broadcast to all shards (scatter-gather)
- Chunks migrate between shards as data grows (balancer)

Shard key picks the same trade-offs as elsewhere: cardinality, even distribution, immutable, aligned with reads.

### Common misconceptions

- "Mongo is schemaless, so it's easier" — schema lives in app code; bugs become silent
- "Embed everything" — runaway documents; 16 MB hard limit; updates rewrite whole doc
- "`$lookup` is a real join" — slower than SQL joins, no full optimizer; use sparingly
- "Mongo doesn't have transactions" — outdated; it does since 4.0
- "Replica set = HA out of the box" — yes, but client must use connection string with all members; failover takes 10–30s

### Interview traps

1. **"Embed or reference?"** — answer depends on relationship cardinality and access pattern. Don't pick one universally.
2. **Document size limit** — 16 MB. Comes up when embedded arrays grow (e.g., comments on a viral post). Use bucketing (10K comments per bucket doc).
3. **Index on array (multikey)** — index entries per array element. Can blow up index size if arrays are large.
4. **Hot shard** — choose a shard key that distributes; never `createdAt` alone for a write-heavy collection.
5. **`$lookup` performance** — interviewer asks how it works under the hood. It's basically a nested-loop join; without index on join field, it's O(N×M).

---

## Real examples

### E-commerce — order model (embed items)
```javascript
{
  _id: ObjectId(),
  userId: ObjectId(),
  status: "PAID",
  items: [{ sku, quantity, unitPriceCents, name }],
  shippingAddress: { line1, city, country, postal },
  paymentMethod: { type, last4 },
  totalCents: 2900,
  createdAt: ISODate(),
  paidAt: ISODate()
}
```

Index: `{ userId: 1, createdAt: -1 }` for user order history.

### Catalog — denormalize category path
```javascript
{
  _id: "sku-A1",
  name: "Mechanical Keyboard",
  categoryPath: ["electronics", "computers", "peripherals"],
  price: 12000,
  attrs: { switches: "MX-Brown", layout: "TKL" }
}
```
Index on `categoryPath` (multikey) supports any-level filtering.

### Chat — bucketed messages
```javascript
// One document per (conv_id, time bucket)
{
  _id: { convId: ObjectId(), bucket: "2026-05-14T12" },  // hourly buckets
  count: 87,
  messages: [
    { msgId, senderId, body, sentAt },
    ...
  ]
}
```
Prevents document growth beyond limits; supports range queries by bucket.

### Activity feed — fan-out write
```javascript
// Per user, a "feed" collection storing the latest 100 items
{
  _id: { userId, postId },
  authorId, body, createdAt
}
```
Index: `{ userId: 1, createdAt: -1 }`. TTL or periodic prune to keep size bounded.

### Aggregation: top sellers last 30 days
```javascript
db.orders.aggregate([
  { $match: { status: "PAID", createdAt: { $gte: new Date(Date.now() - 30*24*3600*1000) } } },
  { $unwind: "$items" },
  { $group: { _id: "$items.sku", units: { $sum: "$items.quantity" } } },
  { $sort: { units: -1 } },
  { $limit: 10 }
]);
```

### Transaction example
```javascript
const session = client.startSession();
try {
  await session.withTransaction(async () => {
    await accounts.updateOne(
      { _id: fromId, balance: { $gte: amount } },
      { $inc: { balance: -amount } },
      { session }
    );
    await accounts.updateOne(
      { _id: toId },
      { $inc: { balance: amount } },
      { session }
    );
    await transactions.insertOne(
      { fromId, toId, amount, key },
      { session }
    );
  }, {
    readConcern: { level: "majority" },
    writeConcern: { w: "majority" },
    readPreference: "primary"
  });
} finally {
  session.endSession();
}
```

### Replica set status
```javascript
rs.status();
rs.printSecondaryReplicationInfo();
```

---

## Common interview questions

1. Embed vs reference — when?
2. Document size limit; how to handle large nested arrays?
3. How does the aggregation pipeline work?
4. What is the ESR rule for indexes?
5. How does Mongo achieve consistency?
6. Replica set failover — walk through it.
7. How does sharding work?
8. Difference between `find` and `aggregate`.
9. What is `$lookup`? When is it inefficient?
10. How do you index nested fields and arrays?
11. Write concern levels — which would you use for payments?
12. When would you not pick Mongo?

---

## Detailed answers

### 1. Embed vs reference
Embed: owned, always queried together, bounded, 1:few. Reference: independent, unbounded, shared, queried separately. Mixed strategies are common (embed summary, reference detail).

### 2. 16 MB limit
Use bucketing (split into many smaller docs by time/range). Use GridFS for files > 16 MB. For unbounded growth (logs, messages), separate collection with reference.

### 3. Aggregation pipeline
Stages that transform documents sequentially. First stages (typically `$match`, `$sort`) leverage indexes; later stages run in memory (with 100 MB limit by default; `allowDiskUse: true` for more). Pipeline stages can short-circuit (e.g., `$limit` after sort).

### 4. ESR rule
Compound index column order: **Equality, Sort, Range**. Mongo uses one index per query (usually); equality predicates use prefix; sort uses index direction; range uses last. Mirrors SQL composite index rules.

### 5. Mongo consistency
- Default: read primary, write `w:1` — read-your-writes for one client; stale-read possible from secondaries
- `w:majority` writes + `readConcern:majority` reads ≈ linearizable for single-doc
- `linearizable` read concern: stronger but slower; only on primary

### 6. Replica set failover
Heartbeats every 2s; if primary unreachable for 10s, secondaries call an election (Raft-based). Majority votes elect new primary. Old primary rejoins as secondary; any unreplicated writes are rolled back (visible in rollback files). Total time: 10–30s typical.

### 7. Sharding
`mongos` routes queries via shard key. Each shard is a replica set. Config servers store metadata (chunk ranges). Queries hitting the shard key target one shard; otherwise scatter-gather. Chunks split when too large (default 64 MB); balancer migrates them.

### 8. find vs aggregate
- `find()` is a single-stage query with projection, sort, limit
- `aggregate()` is a pipeline of transformations; can do joins, group, unwind
- For simple queries, `find` is lighter; for analytics, `aggregate` is necessary

### 9. `$lookup`
Joins another collection. Essentially nested-loop join. Inefficient when:
- Right collection has no index on the join key
- Both collections are huge
- Used inside large pipelines
Better: denormalize or do client-side join with caching.

### 10. Index nested/array
- Nested: index by dotted path (`"address.city"`)
- Array: multikey index (one entry per element)
- Arrays of objects: index `"items.sku"`
- Watch index size growth with large arrays

### 11. Write concern for payments
`{ w: "majority", j: true }` and read concern `"majority"`. Use transactions for multi-doc atomicity. Add idempotency key.

### 12. When not Mongo
- Highly relational data (use Postgres)
- Ad-hoc analytics with joins (use a warehouse)
- Strict ACID across many docs at high QPS (use RDBMS or Spanner)
- Single-region modest scale (Postgres + JSONB is often enough)
- Small team without Mongo ops expertise

---

## Practical coding examples

### Schema validation
```javascript
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["userId", "status", "items", "totalCents"],
      properties: {
        status: { enum: ["CART", "PLACED", "PAID", "SHIPPED"] },
        totalCents: { bsonType: "int", minimum: 0 }
      }
    }
  }
});
```

### Upsert + atomic increment
```javascript
db.inventory.updateOne(
  { sku: "A1" },
  { $inc: { qty: -1 }, $setOnInsert: { createdAt: new Date() } },
  { upsert: true }
);
```

### TTL index for session cleanup
```javascript
db.sessions.createIndex({ lastActiveAt: 1 }, { expireAfterSeconds: 3600 });
// Docs deleted automatically when lastActiveAt is > 1 hour old
```

### Partial index (skewed boolean)
```javascript
db.orders.createIndex(
  { createdAt: 1 },
  { partialFilterExpression: { status: "OPEN" } }
);
```

### Explain plan
```javascript
db.orders.find({ userId: ObjectId("...") }).explain("executionStats");
// Look at: executionStages.stage = IXSCAN or COLLSCAN
// totalDocsExamined / totalKeysExamined ratio
```

### Bulk write
```javascript
db.collection.bulkWrite([
  { updateOne: { filter: { _id: 1 }, update: { $set: { x: 1 } } } },
  { insertOne: { document: { _id: 2, x: 2 } } }
], { ordered: false });
```

---

## Common mistakes

- Embedding unbounded arrays (large doc rewrites on every update)
- No index on common query fields; finding via `COLLSCAN`
- `$lookup` heavy use → effectively SQL joins but without optimizer maturity
- Using transactions for everything (expensive; redesign for single-doc atomic)
- Default write concern `w:1` for payments
- Ignoring `explain()` output
- One huge document for a user's profile + activity (rewritten on every event)
- Reads from secondary without expecting stale data

---

## Senior engineer discussion points

- **Why Mongo lost ground**: Postgres JSONB + ecosystem, plus Mongo's costly Atlas pricing
- **Atlas search** (Lucene-based) bolted on; not as mature as Elasticsearch
- **Change streams** for CDC-like event processing
- **Online resharding** added in 5.0
- **Time-series collections** added in 5.0 (compressed, optimized)
- **Schema migrations** in Mongo: pattern is "lazy" (update on read), versioned docs, or scripted backfill
- **Why some workloads are still a great fit**: highly nested config-like data, multi-tenant flexible schemas, content management
- **Cost of "schemaless"**: production data slowly diverges; add validators early

---

## Revision notes

- Document model; collections; BSON; `_id`
- Embed vs reference: ownership, cardinality, bounded size, access pattern
- 16 MB doc limit → bucketing
- Indexes: B-tree; ESR rule; multikey; partial; TTL; text; geospatial
- Aggregation: pipeline of stages; `$match` first; avoid `$lookup` on huge collections
- Replica set: primary + secondaries + arbiter; Raft elections
- Write concern `w:majority, j:true` for correctness
- Transactions since 4.0; use sparingly; design for single-doc atomic ops
- Sharding: shard key drives placement; pick wisely; chunks migrate
- Default to Postgres if data is relational
