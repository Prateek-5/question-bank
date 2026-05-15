# NoSQL Fundamentals

## Why this matters in backend interviews

- **Every system design round** at SDE2+ asks a "would you use NoSQL here?" question. The right answer requires you to know the trade-offs by heart.
- **Architectural decision-making** is a senior signal. Cargo-culting "we use Mongo because it scales" gets you rejected; understanding when Postgres would have been simpler gets you hired.
- **Debugging**: NoSQL system failures (replica lag, hot partitions, eventual consistency) come up often.
- **System design**: every read-heavy / global / unstructured-data problem (chat, feed, geolocation, sessions, IoT) involves NoSQL choices.

---

## Core concepts

### What "NoSQL" actually means

Originally "Not Only SQL." A loose category covering databases that:
- Don't fit the relational model (or fit it loosely)
- Often relax ACID for scale (BASE: Basically Available, Soft state, Eventually consistent)
- Are designed around specific access patterns rather than ad-hoc queries
- Typically horizontally scalable (sharded by default)

But: many modern SQL databases (CockroachDB, Spanner, YugabyteDB) scale horizontally with ACID. And many NoSQL stores (MongoDB, DynamoDB) now have transactions. The line is blurred.

### The four families

#### 1. Key-Value (KV)
- Just `key → value` (value can be anything)
- O(1) lookup, no secondary indexes (usually), no queries
- Examples: **Redis**, **Memcached**, **DynamoDB (single-PK)**, **etcd**
- Use cases: cache, session store, leaderboards, feature flags

#### 2. Document
- Stores nested JSON/BSON documents per key
- Secondary indexes, ad-hoc queries
- Examples: **MongoDB**, **Couchbase**, **Firestore**, **DynamoDB (in document mode)**
- Use cases: catalogs, user profiles, content management, semi-structured data

#### 3. Wide-column (column family)
- Rows are keyed; each row has a flexible set of columns grouped into families
- Optimized for huge scale, append-heavy, time-series-like patterns
- Examples: **Cassandra**, **HBase**, **ScyllaDB**, **Bigtable**
- Use cases: time-series, IoT, message storage, ad tech

#### 4. Graph
- Nodes + edges as first-class citizens
- Optimized for traversals (`MATCH (u)-[:FRIEND*1..3]->(f)`)
- Examples: **Neo4j**, **JanusGraph**, **Amazon Neptune**, **Dgraph**
- Use cases: social networks, fraud detection, recommendations, knowledge graphs

(Other useful but specialized stores: **Elasticsearch** for search; **ClickHouse** for OLAP; **InfluxDB / TimescaleDB** for time-series; **Redis Streams / Kafka** for log/event.)

### How NoSQL achieves scale

1. **Horizontal partitioning (sharding)** — data split across many nodes by a partition key
2. **Replication** — each piece of data lives on multiple nodes (quorum reads/writes)
3. **No cross-shard joins** — queries usually target one shard
4. **Eventual consistency** as the default trade-off for availability
5. **Denormalization** — data shaped for read patterns, not write patterns

### When to choose NoSQL

✅ **Choose NoSQL when:**
- Access pattern is fixed and well-known (you can model around it)
- You need single-digit-ms latency at huge scale (Dynamo, Cassandra)
- Data is naturally hierarchical/nested (MongoDB, Firestore)
- You need geo-distributed multi-region writes
- You need a flexible, schemaless extension (often: just use JSONB in Postgres instead)
- Workload is write-heavy time-series / append-only (Cassandra, ScyllaDB)
- You need graph traversals at scale (Neo4j)

❌ **Don't choose NoSQL when:**
- You need ad-hoc analytical queries (use a SQL warehouse)
- Strong ACID across multiple entities is required (use a real RDBMS)
- Your data is highly relational (joins everywhere) — Postgres is faster and simpler
- You're picking it because "Mongo scales" without understanding why
- The schema isn't actually unknown — you just haven't designed it yet
- You can fit in one Postgres instance (most workloads can)

> **Senior take:** Default to Postgres. Add Redis for cache. Add a search engine if needed. Reach for Dynamo/Cassandra only when you genuinely outgrow Postgres at the access-pattern level, not just at row count.

### Schema design philosophy

#### SQL: model your data, then query it
You design tables that reflect entities and relationships. Joins assemble the queries.

#### NoSQL: model your queries, then store the data
You list every query you'll ever run, then design tables/collections so each query is a single-key lookup. This is **denormalization on purpose**.

Example: In an e-commerce app, if you frequently load "user + their last 5 orders" together, a SQL design joins users and orders. A document design embeds the last 5 orders in the user document (and writes are duplicated when an order is placed).

### Consistency models

(Detailed in `02-cap-theorem.md`.)

- **Strong**: every read sees the latest committed write
- **Linearizable**: strong + real-time ordering
- **Sequential**: writes ordered consistently across all observers
- **Causal**: if A causally precedes B, every observer sees A first
- **Eventual**: replicas converge "soon"

### Partitioning strategies

- **Hash-based**: hash(key) → shard. Even distribution, but range queries fan out.
- **Range-based**: keys assigned to contiguous ranges. Good for range scans, but hot-spot risk if writes cluster at one end (monotonic IDs).
- **Directory-based**: a lookup service maps key → shard. Flexible, but the directory is a SPOF.
- **Composite**: hash on partition key + sort key for ordering within the partition (Dynamo, Cassandra).

### Replication strategies

- **Leader-follower (master-replica)**: writes go to leader, reads can go to followers (with lag). Mongo replica sets, Postgres streaming replication.
- **Multi-leader**: any node accepts writes; conflicts must be resolved (Cassandra "all leaders", CouchDB, multi-region).
- **Leaderless (Dynamo-style)**: clients send to any N nodes; quorum R + W > N for strong consistency.

### Common misconceptions

- "NoSQL = no schema" — every store has a schema; it just lives in your application code instead of the DB
- "NoSQL is faster" — sometimes; depends on the workload. Postgres can do 50k QPS on commodity hardware.
- "Mongo is schemaless so we don't have to think about indexes" — wrong; Mongo indexes are critical and easy to forget
- "Eventual consistency = data loss" — no, it's a propagation delay; writes are durable
- "Cassandra scales linearly" — it does, but it doesn't help if your data model is wrong; hot partitions kill performance regardless of node count

### Interview traps

1. **"Why would you use Mongo over Postgres?"** — most answers are wrong. Good answer: "I usually wouldn't; I'd use Postgres with JSONB. I'd choose Mongo only if multi-region writes or a truly schemaless document model with millions of nested arrays is required."
2. **"What's the difference between Redis and Memcached?"** — Redis has data structures, persistence, replication, scripting, pub/sub, streams. Memcached is pure KV with simpler eviction.
3. **"What's a good partition key for X?"** — high cardinality, even distribution, matches access pattern. Bad: customer_id where one customer is 80% of traffic.
4. **"Can Mongo do transactions?"** — yes, since 4.0 (single replica set) and 4.2 (sharded). But they're more expensive than a Postgres transaction.

---

## Real examples

### When to use what (production picks)

| Workload | Choice | Why |
|---|---|---|
| User accounts + orders + items + payments | **Postgres** | Relational, ACID, joins, mature |
| Hot session store | **Redis** | Sub-ms latency, TTL, simple data |
| Product catalog with rich filtering | **Postgres + Elasticsearch** | SQL for canonical, ES for search |
| Real-time analytics dashboard | **ClickHouse / BigQuery** | OLAP, columnar |
| Time-series IoT sensor data | **TimescaleDB / Cassandra / InfluxDB** | Time-range queries, compression |
| Multi-region chat messages | **DynamoDB / Cassandra** | Global tables, write availability |
| Social graph (friend-of-friend) | **Neo4j** | Traversal performance |
| User feed (timeline) | **Cassandra / Redis + Postgres** | Fan-out write, sorted reads |
| Rate limiter | **Redis** | Atomic counters, TTL |
| Ad-impressions ingestion | **Kafka → Cassandra / ClickHouse** | Append-heavy, analytics |

### Schema modeling examples

#### Chat messages — Cassandra

```
PRIMARY KEY ((conversation_id), sent_at, message_id)
```
- Partition by `conversation_id` → all messages of a conversation on one node
- Clustering by `sent_at DESC` → newest messages first
- Single query returns latest N messages in one read

#### User feed — DynamoDB

```
Table: user_feed
PK: user_id (partition)
SK: created_at#post_id (sort)
```
- Query: `WHERE user_id = $me ORDER BY created_at DESC LIMIT 50` → one partition read

#### Catalog — MongoDB

```javascript
{
  _id: "sku-A1",
  name: "Mechanical Keyboard",
  category: ["electronics", "computers", "peripherals"],
  price: 12000,
  attributes: { switches: "MX-Brown", layout: "TKL" },
  variants: [{sku: "A1-RED", color: "red", stock: 12}, ...]
}
```
- Index on `category`, `price`
- One document per product, embedded variants

### Postgres + JSONB alternative

```sql
CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  sku TEXT UNIQUE,
  attrs JSONB,
  price_cents INT
);
CREATE INDEX ON products USING gin (attrs);
SELECT * FROM products WHERE attrs @> '{"color":"red"}';
```

In most cases this is enough — you keep ACID, joins, and SQL — and you skip the Mongo operational complexity.

---

## Common interview questions

1. What are the four NoSQL families? Give examples and use cases.
2. When would you use NoSQL over SQL?
3. SQL vs MongoDB — when does each win?
4. What is sharding? Strategies?
5. What's a good partition key?
6. What is eventual consistency?
7. Schemaless vs schema — pros and cons.
8. How do you model a chat application?
9. Difference between Cassandra and DynamoDB.
10. How does Redis differ from Memcached?
11. What is a hot partition?
12. How do NoSQL databases handle joins?

---

## Detailed answers

### 1. Four families
KV (Redis), Document (Mongo), Wide-column (Cassandra), Graph (Neo4j). Plus specialized: search (ES), OLAP (ClickHouse), time-series (Influx).

### 2. NoSQL over SQL
When: extreme scale per access pattern, geo-distributed writes, flexible nested schema, append-heavy, single-digit-ms latency at scale. Otherwise, default to Postgres.

### 3. SQL vs Mongo
- **SQL wins**: relational data, joins, ad-hoc analytics, ACID, mature ecosystem, lower ops cost at modest scale
- **Mongo wins**: deeply nested documents, schema flexibility (multi-tenant SaaS with varying customer fields), single-document atomic writes on big nested structures
- Postgres JSONB closes most of the gap

### 4. Sharding
Splitting data across nodes by a partition key. Strategies: hash, range, directory, composite. Hash distributes evenly; range supports range scans but risks hotspots; directory is flexible.

### 5. Good partition key
- High cardinality (millions of distinct values)
- Even access distribution (no "celebrity user" hot key)
- Aligned with primary access pattern (one query = one partition)
- Bad: timestamp alone (all new writes hit one partition); single tenant ID where one tenant dominates

### 6. Eventual consistency
After a write, replicas converge to the same value "eventually." Reads from lagging replicas may see stale data temporarily. Most NoSQL systems offer tunable consistency: Cassandra/Dynamo let you choose strong, quorum, or eventual per request.

### 7. Schemaless vs schema
- **Schemaless**: faster iteration, no migrations, but schema lives in app code and breaks silently
- **Schema**: enforced at DB, safer, but migrations required
- Truly "schemaless" is rare — most apps have an implicit schema. Mongo has schema validation; Postgres has JSONB with optional checks. Pick the safety/flexibility point you want.

### 8. Chat app schema
- Cassandra: `((conv_id), sent_at DESC, msg_id)` — partition by conversation, sort by time
- DynamoDB: PK=conv_id, SK=sent_at#msg_id
- Postgres: messages table with `(conv_id, sent_at DESC)` index
Discuss trade-offs: Postgres simpler, Cassandra better for huge global scale.

### 9. Cassandra vs DynamoDB
| | Cassandra | DynamoDB |
|---|---|---|
| Ops | Self-managed (or DataStax) | Fully managed AWS |
| Consistency | Tunable (R, W, ALL, QUORUM) | Eventually consistent by default; strongly available |
| Pricing | Server costs | Pay-per-request or provisioned |
| Schema | CQL tables with clustering keys | PK + SK + GSI/LSI |
| Geo | Multi-DC replication | Global tables |
| Hot spots | Partition-based | Adaptive capacity (auto-rebalance) |
Both wide-column at heart. Dynamo is simpler ops, more constrained query API.

### 10. Redis vs Memcached
- Redis: rich data structures (lists, sets, sorted sets, hashes, streams), persistence (RDB/AOF), replication, clustering, pub/sub, Lua scripting
- Memcached: pure KV, multi-threaded, simpler, slightly faster for plain GET/SET, no persistence
- Pick Redis by default unless you need extreme simplicity

### 11. Hot partition
A single partition receiving disproportionate traffic (e.g., 90% of reads). Symptoms: latency spikes, throttling on one node. Causes: bad partition key (low cardinality, skewed), "celebrity" users. Mitigation: add randomness/sharding to the partition key, cache reads, redesign.

### 12. NoSQL joins
Most NoSQL stores don't support cross-document/row joins. You either:
- Embed related data (denormalization)
- Do client-side joins (fetch from one store, then another)
- Use a secondary system (e.g., a graph DB for graph queries)
- Pre-compute join results into a "materialized" form

---

## Practical coding examples

### Redis: cache-aside in Node
```javascript
async function getUser(id) {
  const cacheKey = `user:${id}`;
  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached);

  const user = await db.query('SELECT * FROM users WHERE id=$1', [id]);
  await redis.setex(cacheKey, 300, JSON.stringify(user));
  return user;
}
```

### MongoDB: aggregation pipeline
```javascript
db.orders.aggregate([
  { $match: { status: 'PAID', createdAt: { $gte: ISODate("2026-01-01") } } },
  { $group: { _id: "$userId", total: { $sum: "$amount" }, count: { $sum: 1 } } },
  { $sort: { total: -1 } },
  { $limit: 10 }
]);
```

### DynamoDB: query a single partition
```javascript
const out = await ddb.query({
  TableName: "messages",
  KeyConditionExpression: "conv_id = :c AND sent_at > :t",
  ExpressionAttributeValues: { ":c": convId, ":t": since },
  ScanIndexForward: false, // newest first
  Limit: 50
}).promise();
```

### Cassandra: write & query
```sql
CREATE TABLE messages (
  conv_id UUID,
  sent_at TIMESTAMP,
  msg_id  UUID,
  sender  TEXT,
  body    TEXT,
  PRIMARY KEY ((conv_id), sent_at, msg_id)
) WITH CLUSTERING ORDER BY (sent_at DESC, msg_id DESC);

SELECT * FROM messages WHERE conv_id = ? LIMIT 50;
```

---

## Common mistakes

- Choosing NoSQL for "future scale" you haven't measured
- Using Mongo for highly relational data (then complaining about manual joins)
- Picking a partition key that creates hot partitions
- Using auto-increment ID as partition key in Dynamo (every write hits one shard)
- Forgetting to model secondary access patterns (then doing scans)
- Treating Redis as primary durable store without persistence configured
- Ignoring cross-region replication latency
- Building "polyglot persistence" too early — 2 stores instead of 1, with consistency headaches

---

## Senior engineer discussion points

- **Polyglot persistence**: when one DB stops fitting, add another for specific workloads (Redis for cache, Elasticsearch for search). Operational overhead grows superlinearly with store count.
- **CDC** (Debezium) to keep multiple stores in sync from one source of truth
- **The cost of NoSQL ops** — DynamoDB cost surprises, Cassandra repair operations, Mongo replica-set fail-overs
- **Multi-region trade-offs** — global tables are great, but conflict resolution semantics matter
- **DynamoDB single-table design** — controversial, dense, but key to top-tier Dynamo performance
- **Why Mongo lost ground to Postgres** in many shops: JSONB + the SQL ecosystem
- **When to migrate off NoSQL** — usually when you start needing analytics or relational integrity that the chosen store doesn't provide. Plan for it; lock-in is real.

---

## Revision notes

- Families: KV (Redis) / Document (Mongo) / Wide-column (Cassandra/Dynamo) / Graph (Neo4j)
- NoSQL: model your queries → design data shape
- Default = Postgres + Redis; reach for NoSQL when measured
- Sharding strategies: hash / range / directory / composite
- Hot partition = bad partition key
- Eventual vs strong consistency = latency vs correctness
- Redis ≠ Memcached (data structures, persistence)
- Mongo since 4.x has transactions (limited)
- DynamoDB = managed wide-column; partition + sort key; GSI for alternate access patterns
- Cassandra = self-managed; tunable consistency
- Polyglot persistence costs operational complexity — earn it with measurement
