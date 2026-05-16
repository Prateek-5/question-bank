# DynamoDB & Cassandra

> **Senior mentor framing.** Forget the marketing pages for a minute. Strip both systems down to one idea:
>
> - **DynamoDB** is a *managed gigantic key-value store*. Think of a warehouse with millions of numbered lockers. Your **partition key is the locker number**. If you have a sort key, it's the **page number inside that locker**. AWS handles the warehouse — you only learn the locker numbering scheme.
> - **Cassandra** is a *ring of nodes that each own a slice of the hash space*. Imagine a circular conveyor belt with N stations; a hash of your key tells you which station owns the row, and N-1 neighbours hold the replicas. **Quorum reads and writes are voting protocols** across that ring: "ask the majority, trust the majority."
>
> Both share the same data shape — `(partition_key, sort_key) → value` — but they differ in *who runs the warehouse, who decides what's consistent, and what knobs you get*. Hold those two pictures in your head and the rest of this file is just filling in the labels.

## Why this matters in backend interviews

- **DynamoDB** dominates AWS-based system design rounds (Amazon especially loves it).
- **Cassandra** comes up at companies with extreme write scale (Discord, Netflix, Apple, Instagram once upon a time).
- Both share the **wide-column / partition+sort-key model**; learning one helps with the other.
- Senior signal: explaining the single-table design rationale (DynamoDB) and partition-aware data modeling (Cassandra).

## Why interviewers care

- They want **distributed-systems fluency** — both DBs make you reason about partitions, replication, and access patterns *up front*. There is no "just add an index later."
- They want **tradeoff vocabulary** — "I picked PK = `userId#shardSuffix` because the natural PK was a celebrity-hotspot." That sentence signals seniority.
- They want to see whether you can **resist relational reflexes**. Joins, secondary indexes, ad-hoc filters all bite you here. A strong candidate models for access patterns, not entities.
- DynamoDB shows up in *every* Amazon system-design round; Cassandra shows up at every write-heavy company (Discord, Netflix). Knowing the *shared model* and the *specific differences* is what gets you to L5/SDE-III signal.

## Progressive build-up — from one row to a global table

1. **One row in a hash map**: `map[userId] = userObject`. That's the entire DynamoDB model, at the smallest scale. The "partition key" is just the hash map's key.
2. **Add a sort key**: `map[userId] = sortedList[(timestamp, message)]`. Now each PK owns an ordered list. This is exactly DynamoDB's `(PK, SK)` and Cassandra's `((partition_key), clustering_key)`.
3. **Split the hash map across machines**: hash the PK, modulo the number of machines, and that's where it lives. Welcome to *consistent hashing*. Adding a machine reshuffles only `1/N` of the data.
4. **Replicate each shard 3x**: now you have an AP/CP choice (see the CAP file). DynamoDB hides this behind `ConsistentRead`. Cassandra exposes it as `R`/`W` per request.
5. **Index for alternate access patterns**: GSI/LSI in Dynamo, materialized views or extra tables in Cassandra. Same idea: pre-compute a second copy keyed by a different attribute, because *you cannot ad-hoc query a wide-column store cheaply*.

Each step is a tiny generalization of step 1. If you ever feel lost, mentally collapse the system back to a single hash map and rebuild.

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

#### Mental Model — the partition+sort layout, visualized

Think of a table as a *tree, two levels deep*. The first level groups by **partition key** (which physical machine/partition holds the data). The second level orders rows by **sort key** inside that group.

```
TABLE: messages
│
├── hash("CONV-42") → partition P3
│   ├── SK = "2026-05-14T12:00:00Z#MSG-001"  →  { sender, body }
│   ├── SK = "2026-05-14T12:00:05Z#MSG-002"  →  { sender, body }
│   └── SK = "2026-05-14T12:01:11Z#MSG-003"  →  { sender, body }
│
├── hash("CONV-77") → partition P9
│   ├── SK = "2026-05-14T08:22:30Z#MSG-001"  →  ...
│   └── SK = "2026-05-14T08:22:45Z#MSG-002"  →  ...
│
└── hash("CONV-99") → partition P3   ← same partition as CONV-42 by chance
    └── ...

Query   PK=CONV-42 AND SK BETWEEN x AND y →  walk one partition's sorted list
Query   SK=...    only                    →  must SCAN every partition (slow!)
```

Two takeaways drilled by interviewers:

- A query that supplies the partition key is **O(matching rows)**: it lands on one machine and walks an index.
- A query that omits the partition key is a **Scan / `ALLOW FILTERING`**: it must visit every partition. This is the single biggest "footgun" in wide-column modeling.

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

#### Mental Model — DynamoDB partitions are storage shards, not "indexes"

> Plain-English: a DynamoDB table is *invisibly* split into many physical partitions (think ~10 GB / 3000 RCU / 1000 WCU each). The split happens automatically. **You don't see partitions; you only feel them when one is hot.**

```
   ┌─────────────────────── table: messages ───────────────────────┐
   │                                                               │
   │   hash(PK) % partitionCount  →  one of the buckets below      │
   │                                                               │
   │  ┌─Partition #0─┐  ┌─Partition #1─┐ ... ┌─Partition #N───┐    │
   │  │ leader (AZ-a)│  │ leader (AZ-c)│     │ leader (AZ-b)  │    │
   │  │ replica (AZ-b│  │ replica (AZ-a│     │ replica (AZ-a) │    │
   │  │ replica (AZ-c│  │ replica (AZ-b│     │ replica (AZ-c) │    │
   │  └──────────────┘  └──────────────┘     └────────────────┘    │
   └───────────────────────────────────────────────────────────────┘

   ConsistentRead=false  →  read any replica (could be slightly behind leader)
   ConsistentRead=true   →  must read from the leader of that partition
```

Each partition has one *leader* (writes go here) and two replicas across AZs. That's where the "single-digit-ms" SLA comes from — the leader serves you, and the data is durable across three AZs synchronously.

#### Step-by-step walkthrough — a Put with PK and SK

> `PutItem({ conv_id: "CONV-42", sk: "...#MSG-001", sender: "USER-1", body: "Hi" })`

1. **Router** computes `partition = hash("CONV-42") % partitionCount` → say partition `P3`.
2. **Endpoint** forwards the put to `P3`'s **leader** replica.
3. Leader **appends to its log + memory state**, then synchronously copies to the other two AZ replicas (it doesn't return success until at least a quorum acks — this is why writes feel fast but durable).
4. AWS returns 200 to the client.
5. **GSIs** that depend on changed attributes get a *separate* async write. This is why GSIs are eventually consistent: they're a second table, populated by a downstream pipeline.

#### Step-by-step walkthrough — a Query missing the partition key

> `Query` where you forget to specify `conv_id`, only `sender_id = "USER-1"`.

- Dynamo refuses a `Query` without the partition key. Your two options become:
  - **Scan** the entire table — every partition, every row. Cost scales with table size, not result size. *Avoid in production.*
  - Build a **GSI** keyed on `sender_id` so that the access pattern becomes a normal `Query` on the index.

The number-one lesson Amazon interviewers want you to internalize: **if your query plan ends in "Scan," you've modeled wrong.**

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

#### Mental Model — the Cassandra ring + virtual nodes

> Imagine the entire keyspace as a *circle of token positions*, 0 to 2^64. Each node "owns" a contiguous arc on that circle. Hash a row's partition key — that's its token. The node that owns that arc is the primary; the next RF-1 nodes clockwise are the replicas.

```
                token range 0
                       ▲
              ┌────────┴────────┐
        N5 ──/                   \── N1
            /    ▲ writes hashed   \
           /     │  here go to N2   \
          /      │  (primary), then  \
         /       │  N3, N4 as RF=3   \
        │        x                    │
        │   "hash(key)=Tx"           │
        │                             │
         \                           /
          \                         /
           \                       /
        N4  \                     /  N2
              \                  /
               └────────┬───────┘
                        ▼
                token range max
              (wraps back to 0)
```

**Virtual nodes (vnodes)**: instead of each physical node owning one big arc, it owns *many small arcs* sprinkled around the ring (default 256 vnodes/node). This makes adding/removing a node *cheaper* — it picks up many small slices instead of one giant slice, so rebalancing is smoother.

With **RF=3**, every row exists on **three consecutive nodes** in the ring. Reads and writes are coordinated by *any* node (the "coordinator") that fans the request out to the RF replicas.

#### Mental Model — quorum reads/writes as voting on the ring

```
   RF = 3, W = QUORUM (= 2), R = QUORUM (= 2)
                                            R + W = 4 > N = 3  ✓ strong

   write x = 5:                  ┌──coordinator──┐
                                 │   (any node)  │
                                 └───┬───┬───┬───┘
                                     │   │   │
                                     ▼   ▼   ▼
                              [N2]  [N3] [N4]      ← three replicas
                               OK    OK    (slow)
                       ack returned when 2 of 3 ack.

   later read at QUORUM:                read overlaps with at least
                                        one node that has x = 5,
   read x:                              so the read sees x = 5
                              [N2]  [N3] [N4]      and triggers read
                              x=5   x=5  x=?       repair on N4.
```

The coordinator gathers the responses, picks the most recent timestamp, returns that value, and sends a **read-repair** update to any replica that was behind. This is how Cassandra "self-heals" while staying available.

#### Step-by-step walkthrough — a write with RF=3, W=QUORUM

> `INSERT INTO messages (...) VALUES (...)` from a client.

1. Client connects to **any** Cassandra node — call it the **coordinator**. (Often the driver token-aware routes directly to one of the replicas.)
2. Coordinator hashes the partition key → token → identifies the **three replica nodes** (RF=3).
3. Coordinator sends the write to all three in parallel. Each replica:
   - appends to its **commit log** on disk (durable)
   - inserts into the in-memory **memtable**
   - acks the coordinator
4. As soon as **2 of 3** replicas ack (W = QUORUM), the coordinator returns success to the client.
5. The third replica's ack may arrive later. If it never arrives, the coordinator records a **hinted handoff** so the missing replica can catch up when reachable.
6. Eventually, the memtable is flushed to disk as an immutable **SSTable**.

#### Step-by-step walkthrough — a read at QUORUM showing reconciliation

> `SELECT body FROM messages WHERE conv_id = ?`

1. Coordinator identifies the 3 replicas for that partition key.
2. Coordinator sends **a full read to one replica** and **digest reads to the other QUORUM-1 = 1**. (Digest = a hash of the row, much smaller.)
3. If the digests *match* the full read → return the result. Done in one round trip's worth of latency.
4. If the digests *disagree*: coordinator fetches full rows from all replicas, picks the one with the **latest timestamp**, returns it to the client, and writes the latest value back to the stale replicas (**read repair**).
5. Client sees the correct value; cluster quietly converges in the background.

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

#### Mental Model — the LSM-tree write path

> Cassandra (and ScyllaDB, RocksDB, LevelDB) is built on an **LSM-tree**: writes never *update in place*; they *append*. Reads merge versions. Compaction throws away the old ones.

```
   CLIENT WRITE
       │
       ▼
   ┌─────────────────┐    sync, durable
   │  COMMIT LOG     │  ◀── crash-recovery source
   │ (append-only)   │
   └─────────────────┘
       │
       ▼
   ┌─────────────────┐    in-memory, sorted
   │   MEMTABLE      │  ◀── reads check here first
   │  (per CF)       │
   └─────────────────┘
       │   (when full / time-triggered)
       ▼
   ┌─────────────────┐    immutable on disk
   │  SSTable L0  #1 │     sorted by key + bloom filter + index
   ├─────────────────┤
   │  SSTable L0  #2 │
   ├─────────────────┤
   │  SSTable L0  #3 │
   ├─────────────────┤    COMPACTION
   │  SSTable L0  #4 │ ───────────────► merge + dedupe +
   └─────────────────┘                  drop tombstones past
                                        gc_grace_seconds
        ▼                                       │
   ┌──────────────────────────────────────────┐ │
   │  SSTable L1 (bigger, fewer files)        │◀┘
   └──────────────────────────────────────────┘

   READ PATH:
       check memtable → check bloom filter on each SSTable
                       → fetch from any SSTable that *might* match
                       → merge by timestamp → return latest
                       → trigger read-repair if replicas disagree
```

Two consequences interviewers love:

- **Writes are blazing fast** (append + memory, no random seek). This is why Cassandra is *king* of write-heavy workloads.
- **Reads can be slow on a partition with many SSTables and tombstones** — every SSTable that might contain the key must be checked. Compaction is the cleanup process that keeps this tractable.

#### Mental Model — gossip protocol (how nodes find each other)

Cassandra nodes don't have a master directory. Instead, every second each node picks a few random peers and **gossips** its view of the cluster: "Here's who I know, when I last heard from them, and what state they're in." Within a handful of rounds (log(N) gossip rounds), every node converges on the same membership view.

- Used for: node up/down detection, schema version propagation, token ranges.
- Failure detector: a *phi-accrual* algorithm — a continuous suspicion score rather than a binary "alive/dead." This avoids false positives during transient network blips.

#### Mental Model — anti-entropy = scheduled gossip *for data*

- **Gossip** keeps *membership* in sync.
- **Read repair** opportunistically fixes data when reads disagree (only the rows you actually read).
- **Anti-entropy / `nodetool repair`** is the *scheduled, full* version: nodes exchange Merkle trees of their data ranges, find branches that differ, and stream the differences. This catches rows that *no one ever reads* (cold data), so deletes can be safely compacted away after `gc_grace_seconds`.

Run anti-entropy weekly (or use Reaper) — skipping it is the #1 way to resurrect deleted data ("zombie data").

### Common misconceptions

- "Cassandra is faster than Postgres at everything" — no; for random reads of small data, Postgres is often faster
- "Just add nodes" — yes for capacity, but requires repair / streaming
- "Secondary indexes are like SQL indexes" — no; they're partition-local and often inefficient
- "Tunable consistency means easy strong consistency" — comes at latency cost
- "Cassandra has SQL-like JOINs (it has CQL!)" — CQL ≠ SQL; no joins

## Common beginner confusion (DynamoDB + Cassandra)

> The most frequent wrong intuitions I correct in interview prep.

1. **"DynamoDB scales infinitely."** — **Misleading.** Each *partition* still has a hard ceiling (~1000 WCU / 3000 RCU). A single hot partition key (a celebrity user, a "trending" hash) will throttle even though the *table* has plenty of capacity. Real scale = distribute the load across partition keys (write-sharding, hash-suffix PKs).
2. **"Cassandra is just an open-source DynamoDB."** — **Wrong.** Surface similarities (wide-column, PK+SK) hide deep differences:
   - **Consistency knobs**: Cassandra exposes `R`/`W` per request; DynamoDB exposes a single boolean `ConsistentRead`.
   - **Write path**: Cassandra is a classic LSM-tree (commit log + memtable + SSTable + compaction) that you run and tune; DynamoDB hides storage internals entirely.
   - **Operations**: Cassandra needs `nodetool repair`, compaction tuning, GC tuning. DynamoDB is "pay AWS, click button."
   - **Multi-DC**: Cassandra is natively multi-DC with `NetworkTopologyStrategy`; DynamoDB uses Global Tables (different replication semantics, different cost).
3. **"GSIs are free."** — **No.** Every write to the base table that touches indexed attributes pays an extra WCU on the GSI. A poorly indexed table can pay 5x writes.
4. **"`ALLOW FILTERING` is fine if it works in the test."** — **No.** It scans every partition. It will detonate at scale.
5. **"Single-table design is always better."** — **No.** It's optimal when you have a fixed set of access patterns and you've written them down. For evolving products with unclear patterns, multi-table is friendlier — easier to migrate, easier to read.
6. **"Tombstones are just deleted rows."** — **No.** They are *markers that shadow* rows during reads. A partition with 100k tombstones makes reads slow even if you only want one live row. Use TTL instead of bulk deletes; partition with bucketing so old buckets just expire instead of being deleted.
7. **"Read at QUORUM = guaranteed correctness."** — Only for *that key*, after the read merges replica versions. Multi-key transactions still need LWTs (Paxos) or external coordination.

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

## Interview storytelling — answers a senior engineer would give

### "Your DynamoDB partition is hot — what do you do?"

> "First I confirm it's actually a hot partition and not a hot *table*: I check CloudWatch for `ThrottledRequests` localized to one partition (look at `WriteThrottleEvents` per partition key with contributor insights). Once confirmed, three lines of action, cheapest first:
>
> 1. **Write-sharding the partition key**. If my PK is `userId` and one user is huge, I change it to `userId#shardSuffix` where `shardSuffix = random(0..N)`. Reads then need to fan out to all N shards, but writes are spread. Pick N to be just enough.
> 2. **Caching the read hot spot** with DAX or an in-process LRU — most "celebrity" reads are repeated.
> 3. **Adaptive capacity** kicks in automatically for short bursts, but it's not a substitute for fixing the model.
>
> If the hot pattern is *sequential timestamps* (everyone writes to today's date), I add a high-entropy prefix to the PK so the writes spread across partitions. The rule is: **partition keys should look random, even if the access pattern isn't**."

### "Design a Cassandra schema for a chat app."

> "Two queries dominate: (1) latest N messages in a conversation, (2) the conversation list for a user.
>
> Table 1 — `messages_by_conv`:
> ```sql
> CREATE TABLE messages_by_conv (
>   conv_id     UUID,
>   bucket      TEXT,          -- 'YYYY-MM' to cap partition size
>   sent_at     TIMESTAMP,
>   msg_id      TIMEUUID,
>   sender_id   UUID,
>   body        TEXT,
>   PRIMARY KEY ((conv_id, bucket), sent_at, msg_id)
> ) WITH CLUSTERING ORDER BY (sent_at DESC, msg_id DESC);
> ```
> Partition key = `(conv_id, bucket)` — bucketed so a 10-year-old conversation doesn't grow unboundedly. Clustering = `(sent_at DESC, msg_id DESC)` so a `SELECT ... LIMIT 50` is a single seek.
>
> Table 2 — `convs_by_user`:
> ```sql
> CREATE TABLE convs_by_user (
>   user_id        UUID,
>   last_message_at TIMESTAMP,
>   conv_id        UUID,
>   peer_id        UUID,
>   preview        TEXT,
>   PRIMARY KEY ((user_id), last_message_at, conv_id)
> ) WITH CLUSTERING ORDER BY (last_message_at DESC);
> ```
> Both updated on every message (denormalized — Cassandra prefers more writes over a join). `LOCAL_QUORUM` for writes; `LOCAL_QUORUM` for reads if I want consistent unread counts, `ONE` if I want fastest feeds.
>
> Edge cases I'd raise: super-active conversations (sub-bucket by `(conv_id, bucket, shard)`), unread counts (counter table — beware counter consistency), and deletes (TTL on disappearing messages, not explicit `DELETE`, to avoid tombstones)."

### "When would you pick Cassandra over DynamoDB?"

> "Three signals: (1) my workload is *write-saturated* at scale where DynamoDB WCUs become the dominant cost line; (2) I need *multi-DC active-active* with native control over per-DC consistency (`LOCAL_QUORUM`, `EACH_QUORUM`); (3) I'm OK paying *operational tax* — compaction tuning, repair scheduling, JVM GC, capacity planning. If any of those isn't true, DynamoDB is the safer bet."

---

## Bridge — how this chapter connects

- **From CAP**: Cassandra defaults to PA/EL and exposes the entire R/W quorum dial; DynamoDB defaults to PA/EL and gives you the `ConsistentRead` upgrade. Everything you read in the CAP file lives *literally* in these knobs.
- **To Replication & Sharding**: the partition-key choice in this file *is* the sharding strategy in the next file. Hot partitions = bad shards.
- **To Caching**: DAX (DynamoDB cache) and read-through caches in front of Cassandra exist exactly because read latency is the expensive direction in these systems.

The thread tying it all together: **wide-column DBs make you do the modeling work upfront so the database can stay simple and fast at the bottom. Every "weird" rule (partition keys, no joins, no `WHERE` without PK) is the price of single-digit-ms latency at petabyte scale.**

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
