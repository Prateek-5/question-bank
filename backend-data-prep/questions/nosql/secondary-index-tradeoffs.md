# Secondary Index Tradeoffs in NoSQL — When the "Free Index" Bites Back

## Source / Origin
- Datastax / Cassandra docs on secondary indexes, materialized views.
- DynamoDB GSI/LSI documentation.
- MongoDB compound index best practices.
- Common senior prompt: "We need to query by email AND by phone — just add two indexes, right?"

## Why this question matters in interviews
Junior engineers think indexes are free. Mid-level engineers know they cost write throughput. Seniors know that **in NoSQL, secondary indexes can silently destroy your shard model** because they require either cross-partition reads, asynchronous replication, or hidden tables that re-shard the data. The interviewer wants you to (a) name the actual mechanism behind each NoSQL store's "secondary index" feature, (b) call out which ones are eventually consistent vs synchronous, (c) explain the cost in writes, storage, and operational complexity, and (d) propose alternatives like materialized views or denormalized lookups.

## Concepts involved

### What "secondary index" means in each store

| Store | Secondary index mechanism | Consistency | Write cost |
|-------|---------------------------|-------------|------------|
| **PostgreSQL** | B-tree / GIN / GiST in the same heap | Synchronous (same transaction) | 1 extra disk write per indexed column per row |
| **MongoDB** | B-tree in same replica set, per collection | Synchronous (same write) | Same as Postgres |
| **DynamoDB LSI** | Same partition, different sort key | Synchronous (same partition write) | Same write throughput as the main item |
| **DynamoDB GSI** | Different partition scheme, asynchronous replication | **Eventually consistent** | Separate WCU; can throttle independently |
| **Cassandra 2i** | Local index per node (anti-pattern at scale) | Synchronous local, scatter-gather global | Hidden cross-node read on query |
| **Cassandra SASI** | Local SSTable-attached index | Local sync | Similar to 2i but better text search |
| **Cassandra MV** | Async materialized view with denormalized data | Eventually consistent | 2x writes; known correctness issues |
| **Elasticsearch** | Inverted index, async from primary | Eventually consistent (near-real-time refresh) | Separate cluster cost |

### Syntax to lock in

```sql
-- Postgres / MySQL: just an index
CREATE INDEX users_email_idx ON users(email);
```

```javascript
// MongoDB: same
db.users.createIndex({ email: 1 });
db.users.createIndex({ email: 1, status: 1 });  // compound
```

```python
# DynamoDB LSI (defined at table creation, same partition key)
"LocalSecondaryIndexes": [{
    "IndexName": "by-status",
    "KeySchema": [
        {"AttributeName": "user_id",   "KeyType": "HASH"},   # same as main
        {"AttributeName": "status",    "KeyType": "RANGE"}
    ]
}]

# DynamoDB GSI (different partition key — async, separate WCU)
"GlobalSecondaryIndexes": [{
    "IndexName": "by-email",
    "KeySchema": [
        {"AttributeName": "email",     "KeyType": "HASH"}
    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
}]
```

```cql
-- Cassandra: anti-pattern at scale
CREATE INDEX users_email_idx ON users(email);

-- Better: a manually-maintained inverted table
CREATE TABLE users_by_email (
  email TEXT PRIMARY KEY,
  user_id UUID
);
-- App writes to both tables on insert (idempotent, retryable).
```

### Edge cases / interview traps
1. **DynamoDB GSI is eventually consistent.** You cannot `ConsistentRead=True` on a GSI. A write to the main table is visible on the GSI ~ms later, but during partition or throttling it could lag seconds. Apps must tolerate this.
2. **DynamoDB GSI has its own WCU.** A write to the main table consumes WCU on the main AND on every GSI that includes the changed attribute. 3 GSIs = 4x write cost. Senior trap.
3. **Cassandra secondary indexes scatter-gather across all nodes.** A query on a 2i with low cardinality fans out to every replica in the cluster. Doesn't scale beyond ~1000 nodes; even below that, the latency spike is brutal.
4. **Cassandra materialized views have known consistency bugs.** Officially "experimental" through Cassandra 4.x; many shops ban them in production. Hand-rolled denormalized tables are safer.
5. **MongoDB indexes are synchronous BUT the writeConcern matters.** `w:1` writes return as soon as the primary updates indexes; secondaries lag. `w:majority` waits for index propagation across replicas.
6. **Index cardinality matters.** A boolean index (cardinality 2) is useless — every query reads half the rows anyway. Use partial indexes (Postgres) or composite indexes with higher-cardinality leading columns.
7. **Index-only scans require ALL queried columns in the index.** "Covering index" pattern saves a heap lookup.
8. **Adding an index to a hot live table** is dangerous in any store. Online schema migration tools exist (pg_repack, gh-ost) but plan for it.
9. **Storage cost.** Every index doubles or triples the storage for that column. With 5 indexes on a 1TB table, you have 5-15TB of index data.

## Mental Model

### The fundamental tradeoff: read flexibility vs write cost

```
                  No index                           With index
Write cost        1 disk write                       1 + N (N indexes)
Read by key       O(1)                                O(1)
Read by other     O(table scan)                      O(log n)
Storage           1x                                  1x + N * column_size
Consistency       trivially consistent               depends on store!
```

### Where the index lives (the senior framing)

```
SAME partition, sync:                CROSS partition, async:
┌──────────────────┐                  ┌──────────────────┐
│ Partition 1      │                  │ Partition 1      │
│ ─ main row       │                  │ ─ main row       │
│ ─ local index    │ ◄── DynamoDB    │ ─ GSI: writes    │
│                  │     LSI          │   broadcast to   │
│ Postgres index   │     Postgres     │   GSI's own      │
│                  │     index        │   partition set  │
└──────────────────┘                  └──────────────────┘
                                              │
                                              ▼ async
                                      ┌──────────────────┐
                                      │ GSI partition N  │
                                      │ separate WCU pool│
                                      └──────────────────┘

Cassandra 2i:                         Cassandra hand-rolled inverted:
Each node has local index             Separate table, app writes to both
of its own data.                      ┌──────────────┐  ┌──────────────┐
Query → coordinator                   │ users        │  │ users_by_email│
fans out to ALL nodes.                │ pk: user_id  │  │ pk: email     │
                                      └──────────────┘  └──────────────┘
                                      App keeps them in sync (idempotent).
```

## Why interviewers care
- Filters candidates who treat all indexes as Postgres-style "just add one."
- Tests whether you understand **the cost model** of writes in distributed systems.
- The follow-up "what's a GSI hot partition?" leads naturally into DynamoDB capacity planning.
- "Cassandra 2i vs hand-rolled inverted table" is a senior-only conversation.

## Common beginner confusion
- **"Indexes make reads faster."** They make *some* reads faster. Index maintenance makes *all* writes slower. Profile both.
- **"DynamoDB GSI is strongly consistent if I configure it."** No — GSIs are *always* eventually consistent in DynamoDB. LSIs can be strongly consistent because they're in the same partition.
- **"Cassandra has indexes, so I'll just use them."** Cassandra 2i is widely considered an anti-pattern. Materialized views are unstable. Denormalize manually.
- **"Mongo indexes are free."** They cost storage, RAM, and write latency. Each additional index ~30% extra write cost.
- **"More indexes = better."** More indexes = slower writes, more storage, more recovery time, more lock contention. Sweet spot is usually 3-5 per collection/table.

## Brute force approach
"Add an index for every query I might ever want." Storage explodes; writes slow 5x; recovery time 5x. Unmaintainable.

"Never use indexes; just full scan." Reads die at any meaningful scale. Also bad.

## Optimal approach

### The decision tree

1. **Is the query a key-lookup?** Use the primary key. No secondary index needed.
2. **Is the query infrequent / analytical?** Run it on a read replica, or offload to a separate analytics store (ClickHouse, BigQuery).
3. **Is the query frequent and on a fixed attribute (e.g., email)?** Add a secondary index, but:
   - In **Postgres / Mongo**: just create the index.
   - In **DynamoDB**: create a GSI. Accept eventual consistency. Pay the WCU cost.
   - In **Cassandra**: create a denormalized table (`users_by_email`), write to both.
4. **Does the query have multiple filter attributes?** Compound index, leading column = highest cardinality + most restrictive.
5. **Will the result set be small?** Index works.
6. **Will the result set be large?** Consider whether index helps at all; sometimes full scan is faster.
7. **Is the index column also a sort key for paging?** Make the index cover (include) the columns needed.

### Cost back-of-envelope

```
Postgres / Mongo:  +30% write latency per additional index (rough).
                   +20-50% storage per indexed column.

DynamoDB GSI:      Each GSI = a copy of indexed attributes, separate WCU pool.
                   If main = 100 WCU and 3 GSIs each project all attrs:
                   total WCU billed ≈ 400 WCU.

Cassandra hand-rolled inverted:
                   2x writes (main table + inverted), 2x storage,
                   1 extra retry path if writes diverge.

Elasticsearch index alongside primary:
                   Separate cluster cost. Near-real-time (1s refresh).
                   Async via Kafka or CDC.
```

## Solution (recipe per store)

### Postgres / MongoDB — straightforward

```sql
-- Postgres: partial index reduces size when most rows are common case
CREATE INDEX users_active_email_idx ON users(email) WHERE active = true;

-- Covering index avoids heap lookup
CREATE INDEX users_email_inc_idx ON users(email) INCLUDE (name, created_at);
```

```javascript
// Mongo: compound + partial
db.users.createIndex(
  { email: 1, status: 1 },
  { partialFilterExpression: { active: true } }
);
```

### DynamoDB — GSI when the access pattern needs a different partition key

```python
# Main table: pk=user_id
# Need: query by email
# Solution: GSI with email as partition key

# Cost: every PutItem to main = 1 WCU for main + 1 WCU for GSI (if email present).
# Read on GSI: 0.5 RCU per 4KB (eventually consistent).

# Anti-pattern: GSI with low-cardinality partition key (e.g., status). Hot partition.
# Fix: compose with a high-cardinality suffix or use sparse GSI (only items with status='active').
```

### Cassandra — hand-rolled inverted table

```cql
CREATE TABLE users (
  user_id UUID PRIMARY KEY,
  email TEXT,
  name TEXT
);

CREATE TABLE users_by_email (
  email TEXT PRIMARY KEY,
  user_id UUID
);

-- App-side: write to both atomically (best effort).
-- If users_by_email write fails, retry; idempotent.
-- Reconciliation job catches stragglers.
```

```cql
-- For higher consistency: BATCH (logged) — writes to both atomically with WAL.
BEGIN BATCH
  INSERT INTO users (user_id, email, name) VALUES (?, ?, ?);
  INSERT INTO users_by_email (email, user_id) VALUES (?, ?);
APPLY BATCH;
-- Cost: batch goes through the batchlog node before applying; ~2x write latency.
```

### Elasticsearch — when full-text or aggregations

```javascript
// Index in Postgres for canonical, ES for search.
// CDC pipeline: Postgres → Debezium → Kafka → ES indexer.
// Tradeoff: ~1-5s lag, but full-text + facets + relevance scoring.
```

## Step-by-step dry run

**Scenario: DynamoDB with a GSI on `email`. 10K writes/sec on main, GSI has 5K WCU provisioned.**

```
t=0   App.PutItem(user_id=42, email="x@y", name="Alice")
       Main partition stores the item. Consumes 1 WCU on main.
t=0   DynamoDB queues an async update to the GSI partition keyed on email="x@y".
       GSI write is best-effort; eventually applied. Consumes 1 WCU on GSI's pool.

t=5ms App.Query(GSI: email="x@y") → may return empty result!
       Item not yet propagated. Eventual consistency.

t=50ms App.Query(GSI: email="x@y") → returns the item.

t=2s   Spike: 20K writes/sec on main. GSI's 5K WCU pool exhausts.
       Main writes succeed (main is at 15K WCU).
       GSI throttles. Backlog builds. Eventual lag grows from 50ms to 30s.
       Queries on the GSI return increasingly stale data.

Fix:   Provision GSI WCU >= main WCU. Or use on-demand mode (auto-scales).
       Or: drop the GSI; use a Lambda + DynamoDB Stream to maintain a separate
       table with strong indexing semantics (more complex but more flexible).
```

**Scenario: Cassandra 2i scatter-gather.**

```
Cluster: 100 nodes, RF=3.
CREATE INDEX users_email_idx ON users(email);
SELECT * FROM users WHERE email = 'x@y';

Coordinator:
  Doesn't know which node has email='x@y' — the 2i is LOCAL to each node.
  Fans out the query to ALL 100 nodes (one per RF group = ~34 nodes).
  Each node checks its local 2i.
  Most return empty. One returns the row.
  Aggregate result, return.

Latency: bounded by the SLOWEST node in the fan-out. p99 = the p99 of all 34 nodes.
At scale: catastrophic tail latency.

Mitigation: hand-rolled inverted table (users_by_email).
  Same query becomes: SELECT user_id FROM users_by_email WHERE email='x@y' → 1 node, 1 partition.
  Then: SELECT * FROM users WHERE user_id = ? → 1 node, 1 partition.
  Two single-partition queries vs one cluster-wide fan-out. 100x latency improvement.
```

## How to think aloud in the interview

> "Secondary indexes look free in single-node systems like Postgres and Mongo — they're synchronous, in the same transaction, and the cost is just disk I/O and storage. But in distributed NoSQL stores, the picture changes dramatically.
>
> In DynamoDB, an LSI lives in the same partition as the main item — synchronous, strongly consistent, but locked to the same partition key. A GSI has a different partition key, which means writes have to be replicated to a different partition scheme asynchronously. So GSI reads are *always eventually consistent*. And each GSI consumes its own WCU pool — three GSIs means four times the write capacity. The hot trap is provisioning the main table generously and forgetting the GSIs throttle independently.
>
> In Cassandra, the official secondary index is local to each node — a query fans out to every node holding any replica. At 100 nodes that's a scatter-gather across ~34 replica groups, and your p99 is bounded by the slowest one. It doesn't scale. The senior pattern is a hand-rolled inverted table: `users_by_email` with email as the partition key, app writes to both tables, reconciliation job catches drift.
>
> Materialized views in Cassandra exist but have known consistency bugs through Cassandra 4. Most production shops ban them.
>
> For full-text search or analytics, I'd offload to Elasticsearch via CDC — accept the ~1s lag in exchange for the query flexibility.
>
> Decision rule: if the query is by primary key, no index. If by a fixed attribute with cardinality, secondary index in single-node stores; in distributed stores, denormalize a lookup table. If full-text or analytics, offload."

## Important takeaways

- **Postgres / Mongo indexes are synchronous and reasonably cheap** — still profile, still cap to ~5 per table.
- **DynamoDB LSI = same partition, sync.** **GSI = different partition, async, separate WCU.**
- **Cassandra 2i is an anti-pattern at scale** — hand-roll inverted tables instead.
- **Cassandra materialized views are unstable** — avoid in production.
- **Every index = write cost + storage cost.** Trade flexibility for throughput.
- **Eventual consistency** on GSIs / MVs is the senior trap — apps must tolerate stale reads.
- **Compound indexes**: leading column should be highest cardinality + most restrictive.
- **Covering indexes** (Postgres INCLUDE, Mongo projection) save heap lookups.
- **Offload search to Elasticsearch** via CDC when the access pattern is text or analytical.

## Variants

1. **Sparse index** — index only rows where the column is present. Mongo: `partialFilterExpression`. Postgres: `WHERE col IS NOT NULL`.
2. **Partial index** — index only rows matching a predicate (e.g., `WHERE active=true`). Massive size savings.
3. **Functional / expression index** — index on `lower(email)` or computed values.
4. **Multi-column / composite index** — order matters; the leading column dictates which queries it supports.
5. **Covering index** — includes extra columns to satisfy queries without heap lookups.
6. **GSI projection types** — KEYS_ONLY, INCLUDE, ALL. Tradeoff: index size vs read flexibility.
7. **CDC-fed external index** — Postgres → Debezium → Kafka → Elasticsearch. Decoupled, eventually consistent, infinitely flexible.

## Revision notes

> **secondary index tradeoffs — 60 second recap**
> - **Postgres / Mongo:** sync, in-table, cheap-ish. ~30% write penalty per index.
> - **DynamoDB LSI:** same partition, sync, strong reads. Limited to same partition key.
> - **DynamoDB GSI:** different partition, async, eventually consistent reads, separate WCU.
> - **Cassandra 2i:** scatter-gather across all nodes — anti-pattern at scale.
> - **Cassandra MV:** experimental / buggy — avoid.
> - **Senior fix in Cassandra:** hand-rolled inverted table with app-side double-write.
> - **Elasticsearch via CDC:** for full-text and analytics; near-real-time.
> - **Compound index:** lead with highest cardinality + most restrictive.
> - **Trap:** thinking GSIs are free; thinking 2i scales; forgetting eventual consistency.
