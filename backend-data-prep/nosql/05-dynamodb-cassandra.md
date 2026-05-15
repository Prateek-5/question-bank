# DynamoDB & Cassandra

## Why this matters in backend interviews

- **DynamoDB** dominates AWS-based system design rounds (Amazon especially loves it).
- **Cassandra** comes up at companies with extreme write scale (Discord, Netflix, Apple, Instagram once upon a time).
- Both share the **wide-column / partition+sort-key model**; learning one helps with the other.
- Senior signal: explaining the single-table design rationale (DynamoDB) and partition-aware data modeling (Cassandra).

---

## Core concepts

### Common foundation: wide-column / partition+sort

Data model:
- **Partition key (PK)** — determines which node/partition stores the row
- **Sort key (SK)** (optional) — orders rows within a partition
- One row = `(PK, SK)`
- Other attributes are flexible (schemaless within a row)

Queries:
- `WHERE PK = ?` → all rows in that partition (efficient)
- `WHERE PK = ? AND SK = ?` → single row (point lookup)
- `WHERE PK = ? AND SK BETWEEN ? AND ?` → range within partition (efficient)
- `WHERE SK = ?` alone → ❌ requires scan or secondary index

**You must model around your access patterns.**

---

## DynamoDB

### Fundamentals

- Fully managed AWS NoSQL
- Single-digit-ms latency at any scale
- Capacity modes: **on-demand** (pay-per-request) or **provisioned** (WCUs / RCUs)
- Replication automatic (3 AZs); optional global tables (multi-region)
- No relational features; no joins

### Keys & indexes

- **Primary key**: PK alone (simple) or PK + SK (composite)
- **GSI (Global Secondary Index)**: alternate (PK, SK); replicates the table behind the scenes; eventually consistent by default
- **LSI (Local Secondary Index)**: same PK, different SK; defined at table creation only; strongly consistent option
- Max 20 GSIs and 5 LSIs per table (limits change; check current docs)

### Capacity model

- **RCU (Read Capacity Unit)**: 1 strongly consistent read of up to 4 KB / sec, or 2 eventually consistent reads
- **WCU (Write Capacity Unit)**: 1 write of up to 1 KB / sec
- **On-demand**: auto-scaling; cost = per request; great for spiky / unpredictable
- **Provisioned**: you reserve capacity; cheaper at predictable steady state
- **Adaptive capacity**: AWS auto-spreads hot partitions

### Single-table design

Controversial but common at scale. Store **multiple entity types** in one table, using overloaded PK/SK to encode relationships.

Example: e-commerce with users, orders, items in one table:

| PK | SK | type | attrs |
|---|---|---|---|
| `USER#42` | `META` | user | name, email |
| `USER#42` | `ORDER#1001` | order | total, status |
| `USER#42` | `ORDER#1002` | order | total, status |
| `ORDER#1001` | `ITEM#A1` | item | qty, price |
| `ORDER#1001` | `ITEM#B5` | item | qty, price |

Single query `WHERE PK = USER#42` returns the user + all their orders. Avoids cross-table joins.

Pros:
- One round trip
- Cheaper (one table, fewer requests)
- Fits Dynamo's model perfectly

Cons:
- Schema is opaque
- Hard to evolve
- Requires deep upfront access-pattern analysis (which you'll be asked to do in interviews)

For most apps, **multi-table is fine and clearer**. Use single-table only when latency / cost demands it.

### Access patterns first (the right Dynamo way)

1. Write down every query (read + write) you'll do
2. For each: what's the PK? What's the SK? Strong or eventual consistency?
3. Add GSIs only for queries that don't fit the main key
4. Validate: no scans on hot paths

### Querying

- **GetItem**: fetch by full primary key
- **Query**: fetch by PK (+ optional SK condition)
- **Scan**: full table scan (expensive; avoid)
- **BatchGetItem**: up to 100 keys per call
- **TransactWriteItems**: ACID across up to 100 items in one call

### Transactions

- Supported (`TransactWriteItems`, `TransactGetItems`)
- Cost: 2x the WCU/RCU of equivalent non-transactional
- Useful for: cross-item updates that need atomicity (e.g., debit + credit)
- Limited to 100 items / 4 MB per transaction

### Hot partition

- A single partition exceeding 1000 WCU / 3000 RCU = throttling
- Caused by: bad PK choice, celebrity user, sequential timestamps
- Mitigation:
  - Hash-prefix the PK (`shardId#userId`)
  - Cache reads upstream
  - Use adaptive capacity (auto)
  - Redesign

### TTL

- Per-item attribute holds expiry epoch
- Items deleted within ~48 hours of expiry (not guaranteed instant)
- Good for sessions, ephemeral data

### Streams + Lambda

- Item-level change stream (last 24h)
- Trigger Lambda on changes
- CDC pattern: stream → projection in other store

### Costs to know

- Reads: roughly $0.25 per million eventually-consistent reads (on-demand)
- Writes: roughly $1.25 per million writes
- Storage: $0.25/GB-month
- Get the calculator out for any design discussion

### Strongly vs eventually consistent reads

- Default: eventually consistent (cheaper, 1/2 RCU)
- `ConsistentRead: true`: strongly consistent (full RCU)
- GSIs are **always eventually consistent**; LSIs can be strongly consistent

---

## Cassandra

### Fundamentals

- Open-source wide-column store (Apache)
- Masterless / leaderless (all nodes equal)
- Linear scalability via consistent hashing + vnodes
- Tunable consistency (R, W: ONE / QUORUM / ALL / LOCAL_QUORUM)
- AP by default; can achieve strong consistency via QUORUM
- Heavy operations: compaction, repair, anti-entropy

### Data model

CQL looks like SQL but isn't:
```sql
CREATE TABLE messages (
  conv_id UUID,
  sent_at TIMESTAMP,
  msg_id  UUID,
  sender  TEXT,
  body    TEXT,
  PRIMARY KEY ((conv_id), sent_at, msg_id)
) WITH CLUSTERING ORDER BY (sent_at DESC);
```

- `((conv_id))` = partition key
- `(sent_at, msg_id)` = clustering keys → sort order within partition
- Queries must include partition key (or use `ALLOW FILTERING` — rarely)

### Wide-row design

Cassandra's superpower: a single partition can have **millions of rows** sorted by clustering key.

Example: each user feed is one partition; events sorted by time. Read 100 latest events → one disk read, predictable latency.

### Replication strategy

```sql
CREATE KEYSPACE app
  WITH REPLICATION = { 'class': 'NetworkTopologyStrategy', 'dc1': 3, 'dc2': 3 };
```
3 copies per data center.

### Consistency tuning

- `ONE`: write/read from any one replica → fastest, weakest
- `QUORUM`: majority of replicas in cluster
- `LOCAL_QUORUM`: majority in local DC (no WAN hop)
- `ALL`: every replica (rarely; loses any availability)
- `EACH_QUORUM`: quorum in every DC (writes only)
- `LOCAL_ONE`: one in local DC

Strong consistency: `R + W > N`. Typical: `LOCAL_QUORUM` for both.

### Lightweight transactions (LWT)

Compare-and-set via Paxos. Used for unique constraints:
```sql
INSERT INTO users (email, ...) VALUES (...) IF NOT EXISTS;
```
Expensive (4 round trips). Use sparingly.

### Anti-patterns

- **Reading from many partitions** (queries without partition key)
- **Large partitions** (> ~100 MB or > 100k rows) → slow reads, GC pressure
- **Tombstones** (deletes leave markers; many deletes = slow reads)
- **Secondary indexes**: limited use; prefer denormalization or materialized views
- **JOINs**: don't exist; denormalize

### Tombstones

A delete creates a tombstone marker. After `gc_grace_seconds` (default 10 days), they're compacted away. If you delete many rows, queries scanning that partition pay the tombstone cost. Avoid heavy delete patterns; prefer TTL.

### Read repair & anti-entropy

- **Read repair**: on a quorum read, if replicas disagree, the latest version is written back
- **Anti-entropy (nodetool repair)**: periodic, ensures all replicas converge; must run weekly to be safe

### Compaction

LSM-tree on disk; new writes go to memtable → flushed as SSTable. Many SSTables → reads slow. Compaction merges SSTables. Strategies:
- **Size-tiered**: merges similarly-sized files; good write throughput
- **Leveled**: leveled hierarchy; good read latency, more write amplification
- **Time-window**: for time-series data

### Common misconceptions

- "Cassandra is faster than Postgres at everything" — no; for random reads of small data, Postgres is often faster
- "Just add nodes" — yes for capacity, but requires repair / streaming
- "Secondary indexes are like SQL indexes" — no; they're partition-local and often inefficient
- "Tunable consistency means easy strong consistency" — comes at latency cost
- "Cassandra has SQL-like JOINs (it has CQL!)" — CQL ≠ SQL; no joins

### Interview traps

1. **Schema design** — given access patterns, design the partition key + clustering. Forgetting clustering order = wrong answer.
2. **Partition size limits** — large feeds (years of activity for one user) need bucketing.
3. **Strong consistency in Dynamo** — only via `ConsistentRead: true` (not on GSIs).
4. **GSI vs LSI** — common confusion. GSI = different partition key; LSI = same PK, different SK.
5. **Single-table design** — interviewer asks why; understand the latency/cost rationale.

---

## Real examples

### DynamoDB: user messages

```javascript
// Table: messages
// PK: conv_id (partition)
// SK: sent_at#msg_id (sort)
// Attributes: sender_id, body

// Insert
await ddb.putItem({
  TableName: 'messages',
  Item: {
    conv_id: { S: 'CONV-42' },
    sk: { S: '2026-05-14T12:00:00Z#MSG-001' },
    sender_id: { S: 'USER-1' },
    body: { S: 'Hi' }
  }
});

// Read latest 50 messages
await ddb.query({
  TableName: 'messages',
  KeyConditionExpression: 'conv_id = :c',
  ExpressionAttributeValues: { ':c': { S: 'CONV-42' } },
  ScanIndexForward: false,
  Limit: 50
});

// GSI: messages by sender
// PK: sender_id, SK: sent_at#msg_id
```

### DynamoDB: single-table for an e-commerce backend

| PK | SK | data |
|---|---|---|
| `USER#42` | `PROFILE` | { name, email } |
| `USER#42` | `ORDER#2026-05-14#1001` | { total, status } |
| `ORDER#1001` | `ITEM#A1` | { qty, price } |
| `ORDER#1001` | `ITEM#B5` | { qty, price } |

Access patterns:
- Get user + their orders: `Query WHERE PK = USER#42`
- Get order items: `Query WHERE PK = ORDER#1001`
- All orders in a status: GSI on `(status, created_at)`

### DynamoDB: idempotency

```javascript
await ddb.putItem({
  TableName: 'payments',
  Item: { idempotency_key: { S: key }, ... },
  ConditionExpression: 'attribute_not_exists(idempotency_key)'
});
// If key already exists → ConditionalCheckFailedException; treat as success
```

### Cassandra: time-series IoT

```sql
CREATE TABLE sensor_readings (
  sensor_id UUID,
  bucket DATE,         -- daily bucket to limit partition size
  ts TIMESTAMP,
  value DOUBLE,
  PRIMARY KEY ((sensor_id, bucket), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

SELECT * FROM sensor_readings
WHERE sensor_id = ? AND bucket = '2026-05-14'
LIMIT 100;
```

### Cassandra: user feed with bucketing

```sql
CREATE TABLE user_feed (
  user_id UUID,
  bucket TEXT,         -- 'YYYY-MM' to cap partition size
  posted_at TIMESTAMPTZ,
  post_id UUID,
  author UUID,
  body TEXT,
  PRIMARY KEY ((user_id, bucket), posted_at, post_id)
) WITH CLUSTERING ORDER BY (posted_at DESC, post_id DESC);
```

Read latest: query the latest bucket; if not enough rows, query the previous one.

---

## Common interview questions

1. Difference between PK and SK in DynamoDB.
2. GSI vs LSI — when to use each.
3. What is single-table design? Pros and cons.
4. How does Dynamo achieve single-digit-ms latency at scale?
5. What is a hot partition? Mitigation?
6. How do you transact in DynamoDB?
7. Cassandra's data model — why does PK choice matter so much?
8. How does Cassandra handle writes? Reads? Deletes?
9. Read repair and `nodetool repair` — difference?
10. What's a tombstone and why is it a problem?
11. When to use Dynamo vs Cassandra vs Mongo?
12. Design messages collection in DynamoDB for a chat app.

---

## Detailed answers

### 1. PK vs SK
PK = partition key, determines node placement. SK = sort key within a partition. Together, the unique row identity. PK alone = "simple" key; PK+SK = "composite."

### 2. GSI vs LSI
- **GSI**: any PK + SK; created/dropped anytime; replicated separately; **eventually consistent** by default
- **LSI**: same PK as base table, different SK; defined at table creation only; **can be strongly consistent**; shares partition with base
- GSI cost: extra WCU/RCU; LSI cost: counts against partition's 10GB limit
- Use GSI for orthogonal access patterns; LSI for alternate sort orders within the same partition

### 3. Single-table design
One table holds multiple entity types; PK/SK encode relationships. Pros: one-shot queries, lower cost. Cons: opaque schema, hard to evolve, requires upfront access-pattern analysis. Common at scale (Amazon retail), questionable for smaller apps.

### 4. Dynamo at scale
- Partition-based storage (consistent hashing); each partition = SSD-backed leader + 2 followers across AZs
- Auto-spreading via adaptive capacity
- Limited query API (PK-only or PK+SK range) — no scans on critical paths
- Single-digit-ms p99 by design (refuse anything that can't be served fast)

### 5. Hot partition
One partition gets disproportionate traffic. Causes: bad PK (low cardinality, skewed), celebrity user, sequential timestamps. Fixes: hash-prefix PK, cache, adaptive capacity, redesign.

### 6. Dynamo transactions
`TransactWriteItems` / `TransactGetItems`: ACID across up to 100 items / 4 MB. Costs 2x normal. Used for cross-item invariants. Conditional writes (single-item) are also a form of atomic operation.

### 7. Cassandra PK choice
Determines partition placement; queries must include PK (or scan all partitions). Bad PK = scatter-gather or hot partition. Good PK = cardinality + even distribution + matches dominant query.

### 8. Cassandra reads/writes/deletes
- Writes: log + memtable; flushed to SSTable later. Very fast.
- Reads: check memtable + SSTables (Bloom filter helps); read repair if quorum read
- Deletes: tombstones; compaction removes after `gc_grace_seconds`

### 9. Read repair vs nodetool repair
- Read repair: on quorum reads, latest version is propagated to lagging replicas
- nodetool repair: explicit anti-entropy run; ensures all replicas converge; must run weekly per `gc_grace_seconds` to prevent zombie data

### 10. Tombstone problem
Each delete = marker entry in SSTable. Queries scanning that partition pay the cost of skipping tombstones. If `gc_grace_seconds` hasn't passed, they're not yet compacted away. Many deletes → slow reads + GC pressure. Solutions: TTL instead of delete; avoid delete-heavy patterns.

### 11. Dynamo vs Cassandra vs Mongo
- **Dynamo**: managed AWS, single-digit-ms latency, simple ops, expensive at scale
- **Cassandra**: self-managed, very write-heavy, tunable consistency, complex ops (compaction, repair)
- **Mongo**: document model, richer queries (aggregation), better for nested data, weaker scaling than Cassandra

Pick:
- Dynamo if AWS-native + you can model around its API
- Cassandra if write-heavy at huge scale + you have ops
- Mongo if you need rich document queries

### 12. Chat in DynamoDB
- Table `messages`: PK = `conv_id`, SK = `sent_at#msg_id`
- Index on conv_id-sent_at for "latest N messages"
- GSI on `sender_id` for "messages sent by user"
- TTL for ephemeral messages
- Streams → Lambda for unread-count updates
Discuss: hot partitions for popular convs (sub-shard by `(conv_id, hash(msg_id) % 4)`).

---

## Practical coding examples

### DynamoDB transactional write (debit + credit)
```javascript
await ddb.transactWriteItems({
  TransactItems: [
    {
      Update: {
        TableName: 'accounts',
        Key: { id: { S: fromId } },
        UpdateExpression: 'SET balance = balance - :a',
        ConditionExpression: 'balance >= :a',
        ExpressionAttributeValues: { ':a': { N: String(amount) } }
      }
    },
    {
      Update: {
        TableName: 'accounts',
        Key: { id: { S: toId } },
        UpdateExpression: 'SET balance = balance + :a',
        ExpressionAttributeValues: { ':a': { N: String(amount) } }
      }
    },
    {
      Put: {
        TableName: 'transactions',
        Item: { id: { S: txId }, idempotency_key: { S: key }, ... },
        ConditionExpression: 'attribute_not_exists(idempotency_key)'
      }
    }
  ]
}).promise();
```

### DynamoDB conditional update for inventory
```javascript
await ddb.updateItem({
  TableName: 'inventory',
  Key: { sku: { S: 'A1' } },
  UpdateExpression: 'ADD qty :neg',
  ConditionExpression: 'qty >= :req',
  ExpressionAttributeValues: { ':neg': { N: '-1' }, ':req': { N: '1' } }
});
```

### Cassandra prepared statement (Node)
```javascript
const prepared = await client.prepare(`
  INSERT INTO messages (conv_id, sent_at, msg_id, sender, body)
  VALUES (?, ?, ?, ?, ?)
`);
await client.execute(prepared, [convId, new Date(), msgId, sender, body], {
  prepare: true,
  consistency: cassandra.types.consistencies.localQuorum
});
```

### Cassandra read latest messages
```sql
SELECT * FROM messages WHERE conv_id = ?
LIMIT 50;  -- ORDER BY sent_at DESC from clustering order
```

---

## Common mistakes

- Choosing PK = `timestamp` or `auto_increment` → hot partition
- Designing without writing down access patterns
- Heavy `Scan` operations on big tables
- Forgetting GSIs are eventually consistent
- Treating CQL like SQL (it isn't; no JOINs, no subqueries)
- Large Cassandra partitions (no bucketing for time-series)
- Heavy deletes in Cassandra without considering tombstones
- Single-table design without the access-pattern document

---

## Senior engineer discussion points

- **PartiQL (Dynamo SQL-like)** — convenience, not new capability; same model underneath
- **DynamoDB cost surprises** — RCU/WCU mismatch, GSI write amplification, large items
- **Dynamo + DAX** — in-memory cache for read-heavy
- **Cassandra → ScyllaDB** — drop-in replacement, C++ rewrite, much faster
- **Cassandra repair pain** — incremental repair, Reaper tool
- **Single-table design** trade-offs at depth — schema evolution, GSI explosion
- **When to migrate off Dynamo** — workload outgrows model (analytics, joins). Hard but possible (export, transform, reload).

---

## Revision notes

- PK (partition) + SK (sort) — wide-column model
- DynamoDB: managed; GSI (any keys, eventually consistent) vs LSI (same PK, can be strong, defined at create time)
- Single-table design: encode entities + relations in one table; access patterns drive design
- Hot partition: bad PK; fix by hash-prefix, cache, redesign
- Dynamo transactions: 100 items / 4 MB; 2x cost
- Cassandra: leaderless, tunable consistency, wide rows
- Cassandra PK = partition; clustering keys order rows within
- Cassandra: bucket time-series; avoid huge partitions and many deletes
- Tunable consistency: `R + W > N` for strong; `LOCAL_QUORUM` typical
- LWT (`IF NOT EXISTS`) = Paxos; slow; use sparingly
- Tombstones: deletes create markers; `nodetool repair` weekly
