# MongoDB

## Intuitive teaching layer — start here

### MongoDB in one sentence

MongoDB is a **JSON-shaped database**. Where SQL forces your data into rigid rows and columns up front, Mongo lets each row (called a **document**) be an arbitrary JSON-like object. If JavaScript's "object literal" felt natural to you, the Mongo data model will feel natural too.

```javascript
// A "row" in Mongo is a document — a tree-shaped object:
{
  _id: ObjectId("..."),
  name: "Prateek",
  orders: [
    { id: "ORD-1", total: 1200 },
    { id: "ORD-2", total: 800 }
  ],
  address: { city: "Bangalore", pin: "560001" }
}
```

Compare that to SQL where you'd need a `users` table, an `orders` table, an `addresses` table, and three JOINs to assemble this. Mongo says: store it as one tree. **Locality of related data = fewer round trips = fast reads.** That's the whole pitch.

### Mental Model: a replica set is a band with one lead singer

A MongoDB **replica set** has 3-7 members. Exactly one is the **PRIMARY** (lead singer — takes all writes). The rest are **SECONDARIES** (backing vocalists — replicate from the primary, can serve reads). If the lead singer loses their voice, the band votes and one of the backing vocalists steps up to mic.

```
                ┌──────────────┐
       writes → │   PRIMARY    │     (the lead singer)
                │   (m1:27017) │
                └──────┬───────┘
                       │ oplog stream (async by default)
              ┌────────┴────────┐
              ▼                 ▼
       ┌──────────────┐  ┌──────────────┐
       │  SECONDARY   │  │   ARBITER    │     (votes only, no data)
       │  (m2:27017)  │  │  (m3:27017)  │
       └──────────────┘  └──────────────┘
              ▲
              │ optional reads (read preference = secondary)
              │
            client
```

The **arbiter** is just a vote-only member — it has no data, but it participates in elections so you can have an odd number of voters without buying a third full-data box. (Production tip: avoid arbiters when you can; 3 full data members is safer.)

### Why interviewers care

When the panel hears "MongoDB," they're testing three things:

1. **Data modeling judgment.** Can you decide when to embed vs reference? This is the deepest signal in Mongo interviews. Bad embedding choices in production = company-wide pain.
2. **Distributed-systems awareness.** Can you reason about replica set failover, write concerns, read preferences? Mongo is a distributed system pretending to be a single database.
3. **Honesty about trade-offs.** Saying "actually, for this use case I'd pick Postgres" is a HUGE positive signal. Tool-fanatics get filtered out.

### Common beginner confusion

| Misconception | Reality |
|---|---|
| "Mongo is schemaless, so it's easier" | NO. The schema still exists — it lives in your application code now. Without discipline, fields drift, types mutate, and you find `age: "25"` and `age: 25` in the same collection. Use schema validation. |
| "Embed everything; joins are bad" | NO. Embedding unbounded arrays kills you (16 MB doc limit, full rewrite on every update). The right answer is "embed when bounded and co-accessed; reference otherwise." |
| "`$lookup` is just a JOIN" | NO. It's a nested-loop join with no real optimizer. On big collections without indexes on the join field, it's O(N×M). SQL joins are far more mature. |
| "Mongo can't do transactions" | OUTDATED. Multi-document ACID transactions since 4.0 (replica sets) and 4.2 (sharded). They work — they're just expensive. |
| "Replica set = HA, done" | Partial truth. The driver must know all members; failover takes 10-30s during which writes pause. Read your application's connection string and timeouts before declaring victory. |

---

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

### Progressive concept building: from one document to a sharded cluster

Build up your mental model in 4 layers:

**Layer 1 — One document.**
A `{ name, email }` JSON-like blob. Atomic to write. Atomic to read. This is the smallest unit Mongo cares about.

**Layer 2 — A collection of documents.**
Like a SQL table, except each document can have different fields. Indexed by `_id` automatically.

**Layer 3 — A replica set.**
3 copies of every collection across 3 machines. One primary, two secondaries. Survives a single-machine failure. (This is the leader-follower model from `03-replication-sharding.md`.)

**Layer 4 — A sharded cluster.**
Many replica sets, each holding a SLICE of the data. Routed by `mongos`. Now you scale writes and storage horizontally. (This is hash/range sharding from `03-replication-sharding.md`.)

Most production deployments stop at Layer 3. Sharding is only worth it when one machine genuinely can't hold the writes or the data.

### Embedding vs referencing

**Mental Model:** Embedding is like keeping the receipt stapled inside the order folder — everything you need is right there, in one motion. Referencing is like writing a customer ID on the order and keeping the customer profile in a separate filing cabinet — flexible, but you have to walk to the cabinet every time you want their address.

**Common confusion:**
- "Embedding is always faster" — false; once an embedded array grows, every update rewrites the *entire* document, blowing up disk I/O.
- "References mean joins are slow" — references are fine when you don't need the child in every read; you only `$lookup` when you actually need to merge.

```
EMBEDDING (one document, tree-shaped)        REFERENCING (two collections, FK-style)

   order #ORD-7                                 order #ORD-7         user u_42
   ┌──────────────────────────┐                 ┌─────────────┐      ┌──────────────┐
   │ _id, total, status       │                 │ _id, total  │      │ _id: u_42    │
   │ items: [                 │                 │ userId: u_42├─────►│ name, email  │
   │   { sku, qty, price },   │                 │ status      │      │ address      │
   │   { sku, qty, price }    │                 └─────────────┘      └──────────────┘
   │ ]                        │                  one read for order,   second read (or $lookup)
   │ shippingAddress: {...}   │                  separate read for user
   └──────────────────────────┘
   one read returns everything
```

**Interview storytelling tip:** When asked "embed or reference?", say out loud: "I ask three questions — is the child owned by the parent? is it bounded? is it always read together? Three yeses → embed. Any no → reference." That signals you have a checklist, not a hunch.

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

**Mental Model:** An index is the alphabetical thumb-tab on a paper dictionary. Without it, you scan every page (COLLSCAN). With it, you jump directly to "M" then walk a few pages. A **compound index** is like a phone book sorted first by last name, then by first name — you can find "Sharma" instantly, and "Sharma, Anand" almost as fast, but searching by first name *alone* makes the index useless.

**Common confusion:**
- "More indexes = faster" — every index slows down writes (each write updates every index) and costs RAM. Index what you query, nothing more.
- "Compound index `{a,b,c}` helps `{b}` queries" — NO. Only **leftmost prefixes** work: `{a}`, `{a,b}`, `{a,b,c}`. A query on `b` alone falls back to COLLSCAN.

```
Compound index on { userId: 1, createdAt: -1 }  — leftmost-prefix view:

      ┌──────────────────────────────────────────────────┐
      │  userId  │  createdAt  │  → query coverage       │
      ├──────────┼─────────────┼─────────────────────────┤
      │   ✓      │             │  uses index (prefix)    │
      │   ✓      │     ✓       │  uses index fully       │
      │          │     ✓       │  NO — skips userId      │
      └──────────────────────────────────────────────────┘

      ESR layout for { status, createdAt, price }:
      [ Equality: status="PAID" ] [ Sort: createdAt -1 ] [ Range: price < 1000 ]
              ↑                          ↑                      ↑
        narrows fastest             skips sort step       trims final range
```

**Interview storytelling tip:** If asked "how would you speed this query up?", verbalize: "I'd run `explain('executionStats')`, look for COLLSCAN or a bad `totalDocsExamined:totalKeysExamined` ratio, then design a compound index using ESR." That's the senior-shaped answer.

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

**Mental Model:** The aggregation pipeline is a **factory conveyor belt**. Raw documents enter at one end; each station (`$match`, `$unwind`, `$group`, `$sort`) does one transformation and passes the result downstream. Whatever falls off the last station is your output. Put the cheapest, most-discarding station first — there's no point polishing items you'd throw away later.

**Common confusion:**
- "Stage order doesn't matter, Mongo optimizes it" — Mongo *does* re-order some stages but not all. Putting `$match` before `$lookup` versus after can change runtime by 100x. Be intentional.
- "`$group` uses my index" — once you `$group`, the output documents are *new* documents with no index on them. Subsequent `$sort` will sort in memory (and hit the 100 MB limit).

```
Aggregation pipeline as a conveyor belt:

   orders (raw docs)
       │
       ▼
  ┌─────────────┐   filter: status=PAID, last 30d
  │   $match    │   (uses index on { status, createdAt })
  └─────┬───────┘
        │  N docs (small subset)
        ▼
  ┌─────────────┐   one doc per array element
  │  $unwind    │   1 order × 3 items → 3 docs
  └─────┬───────┘
        │  N*avg(items) docs
        ▼
  ┌─────────────┐   bucket by sku, sum quantity & revenue
  │   $group    │
  └─────┬───────┘
        │  distinct-skus docs
        ▼
  ┌─────────────┐   order by revenue desc
  │   $sort     │
  └─────┬───────┘
        ▼
  ┌─────────────┐   top 10
  │   $limit    │
  └─────┬───────┘
        ▼
     output (10 docs)
```

**Step-by-step walkthrough** of the example below:
1. `$match` — narrow to PAID orders since Jan 1, 2026. Uses the index on `{status, createdAt}`.
2. `$unwind: "$items"` — explode each order into one doc per line item. An order with 3 items becomes 3 docs.
3. `$group` — bucket by `items.sku`. For each sku, sum quantity into `qty`, multiply qty×unitPrice and sum into `revenue`.
4. `$sort` — order by revenue descending.
5. `$limit: 10` — keep only the top 10 sellers.

**Interview storytelling tip:** "I'd structure the pipeline so that anything index-eligible comes first, and I'd put `$limit` before any expensive `$lookup` whenever possible to shrink the working set." That signals real production experience.

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

**Mental Model:** A replica set is a **WhatsApp group of databases**. The primary types messages (writes) into the group; the secondaries see those messages and apply them to their own state. If the primary's phone dies, the group elects a new "admin" — but during the election (~10s) no one can post.

**Common confusion:**
- "Secondaries replicate synchronously" — by default replication is **asynchronous**. The primary acks the client *before* secondaries have applied the write. That's why `w:1` can lose data on primary crash.
- "An arbiter is a hot standby" — no, an arbiter holds *zero* data. It only votes. If your secondary dies in a 1P+1S+1A set, you lose all redundancy and risk rollback. Prefer 3 full data members in prod.

- Group of mongod instances: 1 primary + N secondaries (+ optional arbiters)
- Primary accepts writes; secondaries replicate via oplog
- Failover: secondaries vote (Raft-like) to elect new primary (~10s typical)
- Read preference: `primary` (default), `primaryPreferred`, `secondary`, `nearest`

### Write concern

**Mental Model:** Write concern answers "how many people do I need to nod before I trust the write?" `w:1` is "the lead singer said OK, good enough." `w:"majority"` is "more than half the band confirmed it's in their notebook — even if the lead singer disappears, the song survives."

**Common confusion:**
- "`w:1` means durable" — no. The primary may have it only in memory; if the primary crashes before journaling, that write vanishes. Use `j:true` for journal durability.
- "`w:majority` is slow" — usually only a few extra milliseconds in a healthy LAN replica set. The latency hit is dwarfed by the data-loss prevention. For money, always use majority.

```
Timeline: w:1 vs w:"majority"   (client perspective)

w:1  (default)
  client ───write──► PRIMARY ──ack──► client    ← happy fast path
                       │
                       └─ async ─► S1
                       └─ async ─► S2          (may not have applied yet
                                                — if primary dies now, write lost)

w:"majority" (3-node set: needs 2 acks total)
  client ───write──► PRIMARY ──┬─► S1 ──ack──┐
                               └─► S2 ──ack──┤
                                             ▼
                              PRIMARY ───── ack ─────► client
  (client waits until majority — 1 primary + 1 secondary — confirm. Safe across single-node failure.)
```

**Interview storytelling tip:** When asked about payment writes: "I'd use `{ w: 'majority', j: true }` with a transaction and an idempotency key. The few extra ms are worth never losing a debit." Said in that order, you sound like someone who's been on-call.

| Concern | Meaning |
|---|---|
| `w: 1` | Primary ack only (default in many drivers; can lose on primary failure) |
| `w: "majority"` | Majority of replica-set members ack |
| `j: true` | Durable to journal (fsync to disk) |
| `wtimeout` | Max time to wait for ack |

For correctness-sensitive writes: `{ w: "majority", j: true }`.

### Read concern

**Mental Model:** Read concern is the **freshness vs trust** dial. `local` says "give me whatever the node has right now, I'll take my chances on rollback." `majority` says "only show me data that the band has agreed on — even if the primary fails, this won't disappear." `linearizable` says "make absolutely sure no one else writes between my read and the answer."

**Common confusion:**
- "`readConcern:'majority'` reads from majority of nodes" — NO. The query still hits one node, but it only returns data that has been *acknowledged by a majority*. Stronger consistency, same network cost.
- "`linearizable` is just like Postgres SERIALIZABLE" — different. It's about *real-time ordering* of single-document reads on the primary. Slow because it does a noop write to confirm primary status.

| Concern | Meaning |
|---|---|
| `local` | Latest local (may not be majority-committed) |
| `available` | Like local for sharded; faster |
| `majority` | Majority-committed (no rollback) |
| `linearizable` | Serial reads on a single shard primary |
| `snapshot` | Consistent snapshot across docs (for transactions) |

### Transactions

**Mental Model:** A Mongo transaction is like asking a group of waiters to deliver multiple dishes to one table *all at once or not at all*. The kitchen (storage engine) holds the plates back until everyone is ready; if any waiter trips, no dish leaves the kitchen. It works — but it's expensive because every other table waits for that group lock.

**Common confusion:**
- "I should wrap every multi-write in a transaction to be safe" — NO. The right Mongo move is to **model your data so single-document writes are atomic enough** (e.g., embed). Transactions are an escape hatch, not the norm.
- "`TransientTransactionError` means something is broken" — actually expected behavior. Retry the transaction; it's the driver telling you "snapshot conflict, try again."

- Single-document writes are atomic (always)
- Multi-document transactions: supported since 4.0 (replica set), 4.2 (sharded)
- Use `session.startTransaction()` + `commitTransaction()`
- Cost: more expensive than RDBMS transactions; can fail with `TransientTransactionError` → retry
- **Avoid as your default**: model data to make single-doc atomic operations sufficient

### Sharding

**Mental Model:** Sharding is splitting a library across multiple buildings. The **shard key** is the rule that says which book goes to which building — e.g., "fiction A–M at building 1, N–Z at building 2." `mongos` is the receptionist who looks up your request and sends you to the right building. If you ask for a book by *author name* but the key is *title*, the receptionist has to phone every building (scatter-gather) — slow.

**Common confusion:**
- "I'll pick `createdAt` as shard key" — classic hot-shard trap. All new writes hit the *last* chunk, on one shard. Use a hashed key or a compound key starting with something high-cardinality.
- "Chunks split automatically, so the cluster self-balances" — chunks split, yes, but the **balancer** moves them in the background and can fall behind under heavy write load. A bad shard key never balances no matter what.

```
Sharded cluster — request routing:

        client                                config servers
          │                                  ┌──────────────┐
          │   query: find({ userId: 42 })    │  cs1 cs2 cs3 │   (chunk metadata)
          ▼                                  └──────┬───────┘
       ┌────────┐   "userId 42 → chunk B   ┌───────┘
       │ mongos │ ← ─ ─ ─ on shard 2"  ── ─┘
       └───┬────┘
           │  targeted query (one shard)
           ▼
  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
  │  Shard 1    │  │  Shard 2    │  │  Shard 3    │     each shard is itself
  │ (replica    │  │ (replica    │  │ (replica    │     a full replica set
  │  set)       │  │  set)       │  │  set)       │
  │ chunks A    │  │ chunks B    │  │ chunks C    │
  └─────────────┘  └─────────────┘  └─────────────┘

  Query WITHOUT shard key → scatter-gather to ALL shards (slow):
       mongos ──► Shard 1 ─┐
              ──► Shard 2 ─┼──► merge results
              ──► Shard 3 ─┘
```

**Interview storytelling tip:** "Sharding is a last resort — I'd vertically scale, optimize indexes, and use read replicas first. If I have to shard, I pick a key with high cardinality, even write distribution, and alignment with the most common query pattern." That's the textbook answer they want.

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

**Mental Model:** Schema validation is a **bouncer at the collection's door**. By default Mongo lets every shape of document walk in; once you attach a `$jsonSchema` validator, the bouncer checks each insert/update against the rules and rejects malformed docs. It doesn't make Mongo "relational" — it just stops your team from accidentally writing `age: "twenty-five"` into a numeric field.

**Common confusion:**
- "Adding a validator retroactively fixes existing bad docs" — NO. It only blocks future writes. Existing dirty data stays unless you migrate.
- "`validationLevel: 'strict'` is the only safe mode" — there's also `'moderate'` (only validate docs that already match), useful when adding validation to a populated collection without breaking legacy reads.

**Step-by-step walkthrough** of the example below: the validator requires every order document to have `userId`, `status`, `items`, and `totalCents`. The `status` field is restricted to one of four enum values (rejecting typos like `"paid"` lowercase). The `totalCents` field must be a 32-bit integer ≥ 0 (catching float drift and accidental negatives).

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

**Mental Model:** A TTL index is a **self-cleaning shelf**. You stamp every doc with a date field; a background sweeper visits the shelf about once a minute and throws out anything older than the TTL. Great for sessions, OTPs, rate-limit windows, and CDC scratch tables.

**Common confusion:**
- "Docs are deleted exactly at the TTL boundary" — NO. The TTL monitor runs every ~60s; expect up to a minute of lag.
- "TTL works on any field" — the field must be a BSON Date (or array of Dates). Strings/numbers won't expire.

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

### Change streams — the oplog as an event firehose

**Mental Model:** A change stream is a **live news ticker** on top of the replica set's oplog. Your app subscribes and receives a notification every time a document is inserted/updated/deleted — just like Postgres logical replication, Kafka CDC, or DynamoDB Streams.

**Common confusion:**
- "Change streams work on standalone mongod" — NO. They require a replica set (oplog must exist).
- "If my consumer crashes, I lose events" — only if you don't persist `resumeToken`. Always store the last token; on restart, pass it to `watch({ resumeAfter })` to replay from that point.

```
Change stream — tailing the oplog:

  primary's oplog (capped collection)
  ┌──────────────────────────────────────────────────────────────┐
  │ ... | insert u1 | update u2 | delete u3 | insert u4 | ...    │
  └──────────────────────────────────────────────────────────────┘
                  ▲                                       ▲
                  │ secondaries tail to replicate         │
                  │                                       │
                  └──────────────┬────────────────────────┘
                                 │ change-stream cursor (long-lived)
                                 ▼
                          ┌─────────────┐
                          │ your app    │   ──► Kafka / search index / cache
                          │ watch()     │
                          └─────────────┘
                          stores resumeToken after each batch
```

**Interview storytelling tip:** "For CDC I'd use change streams with a persisted resume token and idempotent downstream writes — if the consumer crashes mid-batch, it replays safely."

### Time-series collections

**Mental Model:** Time-series collections are a **specialized warehouse** for metrics/sensor data. Mongo groups documents with the same `metaField` into compressed buckets per time window, so 10,000 temperature readings become a handful of physical documents. Storage shrinks 5-10x; range scans get much faster.

**Common confusion:**
- "I can update time-series docs freely" — historically restricted (until 5.0+); even now updates are limited to the metaField and require care.
- "Use it for any write-heavy workload" — only when the data really is time-series shaped (immutable, append-only, queried by time range). For a fast-mutating log of business events, a regular capped or TTL collection is simpler.

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
