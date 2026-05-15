# Replication & Sharding

## Why this matters in backend interviews

- **Every system design round at scale** asks about replication and sharding.
- **Production debugging**: replication lag, read inconsistency, hot shards, rebalancing storms — these are real issues SDE2s handle.
- **Architectural choices** with billion-row implications. Picking the wrong shard key = company-ending bottleneck.
- Senior signal: explaining the failure modes (failover, split-brain, lag) and recovery procedures.

---

## Core concepts

### Why replicate?

1. **Availability** — survive node failures
2. **Read scaling** — distribute reads across replicas
3. **Geo-locality** — read from a nearby replica
4. **Backup / DR** — replicas as point-in-time backups

### Why shard?

1. **Write scaling** — beyond what one node can handle
2. **Data size** — beyond one node's disk
3. **Geo-partitioning** — keep data near users
4. **Failure isolation** — one shard's outage doesn't affect others

### Replication models

#### 1. Leader-follower (master-replica, primary-secondary)
- One node accepts writes (leader); others (followers) replicate from it
- Followers serve reads (with lag)
- On leader failure: promote a follower (manual or automatic via Raft/Paxos consensus)
- Examples: Postgres streaming replication, MySQL replication, MongoDB replica sets, Redis replication
- **Most common pattern; default in this category.**

#### 2. Multi-leader (master-master)
- Multiple nodes accept writes; replicate to each other
- Needed for geo-distributed writes
- **Conflict resolution required** — same key written in two places
- Examples: Cassandra (all nodes are equal), CouchDB, multi-region Aurora
- Hard to reason about; usually a step toward AP semantics

#### 3. Leaderless (Dynamo-style)
- No designated leader; clients send to multiple nodes
- Quorum (R, W, N) determines consistency
- Used in DynamoDB, Cassandra, Riak
- Handles partitions gracefully; trade-off is conflict resolution complexity

### Synchronous vs asynchronous replication

- **Synchronous**: leader waits for at least one (or more) follower(s) to ACK before committing. Stronger durability and consistency. Higher write latency. If the sync follower is down, writes stall.
- **Asynchronous**: leader commits immediately, ships WAL/oplog to followers in background. Better write throughput. If leader dies before shipping, writes are lost.
- **Semi-synchronous**: leader waits for at least one follower to receive (not apply) the write. Compromise.

Postgres supports any (`synchronous_commit`, `synchronous_standby_names`). MySQL also supports both. Most production setups: **async with sync to one local replica**.

### Replication mechanisms

- **Statement-based**: ship SQL statements (legacy MySQL). Non-deterministic statements (`NOW()`, triggers) break replication.
- **Row-based**: ship binary row deltas (modern MySQL default). Larger, but deterministic.
- **Logical / WAL streaming**: ship physical WAL pages (Postgres physical replication; very efficient).
- **Logical replication**: per-table subscriptions (Postgres pub/sub style, Debezium CDC). Allows cross-version, partial replication.

### Replication lag

- Time between a write on the leader and its appearance on a follower
- Async replicas: usually < 100 ms; can balloon under load
- Symptoms: stale reads, write-then-read returning old data
- Monitoring: `pg_stat_replication` (Postgres), `SHOW REPLICA STATUS` (MySQL), Mongo `rs.printSecondaryReplicationInfo()`

Mitigations for read-your-writes:
- Read from leader after recent write
- Wait for replica to catch up (LSN tracking)
- Sticky session

### Failover

When the leader dies:
1. Detect (heartbeat; consensus says leader unreachable)
2. Elect new leader (Raft/Paxos; or manual)
3. Redirect writes
4. Old leader rejoins as follower; reconcile divergence (rollback unreplicated writes)

Risks:
- **Split-brain**: two nodes both think they're leader → conflicting writes → data divergence. Use fencing tokens or consensus.
- **Data loss**: async replication means writes on the old leader that hadn't replicated are lost.

### Read-after-write inconsistency

```
Client → Leader: INSERT order
Client → Replica: SELECT order  (replica hasn't caught up → not found!)
```

Solutions: sticky sessions, monotonic-read tokens, read-from-leader-for-N-seconds, or "consistency tokens" (Mongo `causalConsistency`, Cosmos session tokens).

### Sharding strategies

#### 1. Hash-based sharding
```
shard = hash(key) % N
```
- Even distribution (with a good hash)
- No range queries (queries scatter to all shards)
- Adding shards = rehashing → use **consistent hashing** to minimize disruption

#### 2. Range-based sharding
```
key A-F → shard 1, G-M → shard 2, ...
```
- Range queries efficient
- Hotspot risk (monotonic IDs → all writes go to last shard)
- Splits / merges as data grows (HBase regions, MongoDB chunks)

#### 3. Directory-based
- A lookup service maps key → shard
- Flexible (any mapping), can rebalance gracefully
- Directory is a SPOF / bottleneck
- Used by some custom distributed systems

#### 4. Geo-based
- Partition by user region (EU users on EU shard)
- Good for compliance (GDPR data residency)
- Cross-region queries are slow

#### 5. Composite (partition + sort key)
- DynamoDB / Cassandra style: partition by one key, sort within partition by another
- Combines hash distribution + range scans within partition

### Consistent hashing

Map keys and nodes onto a circle (hash space). Each key goes to the next node clockwise.

When a node is added/removed: only adjacent keys move (≈ 1/N of data), not all keys (as with naive modulo).

Refinements:
- **Virtual nodes (vnodes)**: each physical node owns many vnodes around the ring → smoother distribution
- Used in Cassandra, DynamoDB, Redis Cluster (with slots)

### Shard key choice — the most important decision

A shard key should:
- Have **high cardinality** (millions of distinct values)
- Distribute **uniformly** (no hot keys)
- Align with the **dominant query pattern** (queries hit one shard, not all)
- Be **immutable** (changing shard key = moving the row)

Bad shard keys:
- `country` — low cardinality, skewed (USA dominates)
- `created_at` — monotonic; all writes hit the most recent shard
- `customer_id` if one customer is 80% of traffic

Good shard keys (depend on access pattern):
- `user_id` for per-user data
- `tenant_id + entity_id` for multi-tenant SaaS
- Composite (user_id, hour) for write-heavy time-series within a user

### Rebalancing

When you add a shard, data must move. Strategies:
- **Pre-split**: many small "chunks" mapped to fewer shards initially; move chunks, not data
- **Background migration**: continuously rebalance, slow but online (Mongo, Cassandra)
- **Stop-the-world rehash**: terrible at scale; some legacy systems do this

Migrations are expensive — plan capacity ahead.

### Hot shard mitigation

- Add randomness to the shard key (`user_id#hash(bucket)`)
- Cache the hot key heavily upstream (CDN, app cache)
- Adaptive capacity (DynamoDB) auto-spreads hot partitions
- Restructure data (different shard key)

### Cross-shard operations

- **Cross-shard transactions** are expensive (2PC); most NoSQL stores don't support them
- **Cross-shard queries** scatter and gather; latency = slowest shard
- **Cross-shard joins**: avoid; denormalize or use a search engine

### Common misconceptions

- "Replication = backup" — no, a `DELETE` propagates to replicas too. Use PITR snapshots for backup.
- "Adding a replica scales writes" — replicas only scale reads
- "Sharding is the answer to performance" — only if writes don't fit on one machine; otherwise indexing/caching is cheaper
- "Sharding == NoSQL" — Postgres has Citus, partitioning; MySQL has Vitess
- "Consistent hashing means consistent" — it means stable mapping, not strong consistency

### Interview traps

1. **Lost write after failover** — async replica fails over; some writes are gone. Asked: how do you guarantee no data loss? Answer: sync replica, or quorum writes, or use a system with consensus.
2. **Hot shard** — they'll describe a celebrity user. You should propose: cache, sub-partition, separate hot shard, or rethink the key.
3. **Replication lag** — interviewer hands you a scenario where a user reads stale data. Walk through detection + mitigation.
4. **Adding capacity** — interviewer asks "you double your shards; what happens?" Discuss consistent hashing vs naive modulo.

---

## Real examples

### E-commerce — sharding orders

Choice: shard by `user_id` (hash). Reasoning:
- Each user reads only their own orders → one shard per query
- Even distribution (millions of users)
- Hot user (e.g., a marketplace seller with millions of orders) → sub-partition by `(user_id, hash(order_id) % 8)`

### Chat — sharding messages

Choice: shard by `conv_id` (Cassandra-style).
- All messages of a conversation co-located → single-partition reads (latest N messages)
- Wide conversations may grow huge → time-bucket: PK = `(conv_id, month)`

### Multi-tenant SaaS

Choice: shard by `tenant_id`.
- Strong tenant isolation
- Hot tenant → "noisy neighbor"; consider dedicated shards for top customers
- Cross-tenant analytics → run on a replica or separate warehouse

### Analytics ingestion (high write)

Choice: time-bucketed partitions with hash sub-partitioning.
- Partition: `(yyyy_mm)`
- Sub-partition: `hash(user_id)`
- Old partitions dropped wholesale; new partitions auto-created

### Postgres physical replication setup

```ini
# Primary (postgresql.conf)
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1GB
synchronous_standby_names = 'standby1'
synchronous_commit = on

# Standby (recovery.conf / standby.signal)
primary_conninfo = 'host=primary user=replicator'
```

### Mongo replica set

```javascript
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "m1:27017", priority: 2 },
    { _id: 1, host: "m2:27017", priority: 1 },
    { _id: 2, host: "m3:27017", arbiterOnly: true }
  ]
});
```

### DynamoDB partition key + composite

```javascript
// PK: user_id (partition), SK: created_at#order_id (sort)
// Query: latest 50 orders for a user
await ddb.query({
  TableName: 'orders',
  KeyConditionExpression: 'user_id = :u',
  ExpressionAttributeValues: { ':u': userId },
  ScanIndexForward: false,
  Limit: 50
}).promise();
```

---

## Common interview questions

1. Difference between replication and sharding.
2. Synchronous vs asynchronous replication — trade-offs.
3. What is replication lag? How do you mitigate it?
4. What is consistent hashing? Why is it used?
5. How do you choose a shard key?
6. What's a hot shard / hot partition? How to fix?
7. How do you rebalance shards as data grows?
8. Cross-shard transactions — how, and what's the cost?
9. What is split-brain? How is it prevented?
10. Leader election — how does it work?
11. How does failover work in Postgres / Mongo / MySQL?
12. Geo-partitioning — when and why?

---

## Detailed answers

### 1. Replication vs sharding
- Replication: same data on multiple nodes (availability, read scale)
- Sharding: different data on different nodes (write/storage scale)
- Combined: each shard has multiple replicas

### 2. Sync vs async
- Sync: stronger durability and read consistency; higher write latency; reduces availability if sync replica is down
- Async: better throughput; risk of data loss on leader failure; replicas lag

### 3. Replication lag
The delay between leader commit and follower apply. Mitigate via:
- Sticky sessions
- Read from leader for N seconds after write
- LSN tokens (read-after-write)
- Quorum reads
- Causal consistency tokens (Mongo, Cosmos)

### 4. Consistent hashing
A scheme where adding/removing a node moves only a fraction of keys (1/N), not all of them. Map keys to a circle, each key goes to next node clockwise. Used in Cassandra, DynamoDB, Redis Cluster (via hash slots).

### 5. Shard key choice
High cardinality, even distribution, aligned with primary access pattern, immutable. Match the dominant query — every query should ideally hit one shard.

### 6. Hot shard
Most traffic concentrates on one shard. Causes: bad key choice, celebrity user, viral content. Fix: cache, add sub-partition, separate hot tier, redesign key.

### 7. Rebalancing
- Pre-split into many small chunks; move chunks
- Background migration (Mongo balancer, Cassandra streaming)
- Adding a shard = move ~1/N data with consistent hashing
- Always rate-limit migrations to avoid swamping I/O

### 8. Cross-shard transactions
Possible but expensive:
- 2PC: prepare on all shards, then commit. Blocks if coordinator dies after prepare.
- Saga: app-level compensating actions
- Distributed SQL (Spanner, CockroachDB): built-in via consensus + timestamps
- Avoid by design: pick a shard key that keeps related data co-located

### 9. Split-brain
Two nodes both believe they're the leader, both accept writes. Causes divergence. Prevent via:
- Consensus (Raft/Paxos) for leader election
- Fencing tokens (any operation includes the leader's term/epoch)
- Quorum-based decisions (must have majority to be leader)

### 10. Leader election
Raft: nodes have terms; on missed heartbeats, candidates request votes; majority elects new leader. Paxos: similar in spirit, more general. ZooKeeper: ZAB protocol. Production systems use these as building blocks.

### 11. Failover
- **Postgres**: streaming replicas; manual or via Patroni / repmgr / pg_auto_failover for automatic with consensus
- **Mongo**: replica set with arbiter; automatic election in 10-30s typically
- **MySQL**: built-in async; HA via Orchestrator, MHA, or Group Replication (Paxos-like)

### 12. Geo-partitioning
Partition by user region for:
- Data residency (GDPR)
- Latency (read locally)
- Failure isolation
Trade-off: cross-region queries hit the WAN.

---

## Practical coding examples

### Detect Postgres replication lag
```sql
SELECT client_addr,
       state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes,
       extract(epoch from (now() - reply_time)) AS lag_seconds
FROM pg_stat_replication;
```

### Mongo: wait for write to be replicated
```javascript
await db.collection('orders').insertOne(order, {
  writeConcern: { w: 'majority', wtimeout: 5000 }
});
```

### Cassandra: tunable consistency
```javascript
client.execute("INSERT INTO ...", [...], {
  consistency: cassandra.types.consistencies.localQuorum
});
```

### Redis Cluster slot calculation
```
slot = CRC16(key) % 16384
```
Each node owns a range of slots. Adding nodes → move slots. Use `{}` to force keys onto the same slot for multi-key operations: `user:{42}:profile`, `user:{42}:cart`.

### DynamoDB GSI for alternate access
```javascript
{
  TableName: 'orders',
  IndexName: 'by_status_created',
  KeyConditionExpression: '#st = :s AND created_at > :t',
  ExpressionAttributeNames: { '#st': 'status' },
  ExpressionAttributeValues: { ':s': 'PAID', ':t': since }
}
```
GSI = secondary index with its own partition + sort key; eventually consistent by default.

---

## Common mistakes

- Treating replication as backup (it isn't; deletes propagate)
- Choosing a monotonic shard key (timestamps, auto-increment IDs)
- Forgetting cross-shard queries cost
- Ignoring failover testing (the failover that doesn't work)
- Adding replicas to scale writes
- Async-only replication on critical data → silent loss after failover
- Skipping quorum tuning in Cassandra/Dynamo

---

## Senior engineer discussion points

- **Patroni / pg_auto_failover / Stolon** for Postgres HA
- **Citus / Hyperscale** for sharded Postgres
- **Vitess** for sharded MySQL
- **Aurora's storage-decoupled replication** — replicas don't replay WAL, they read shared storage; very fast failover
- **Spanner / CockroachDB / YugabyteDB** — distributed SQL with consensus per shard
- **CDC + outbox** for cross-store sync
- **Disaster recovery RPO/RTO** — define both; design replication accordingly
- **Cost of cross-region** — replicas add WAN egress; sync replicas add latency to every write
- **Why most companies don't shard** — they can't even use their primary's full capacity; vertical scale + read replicas suffice

---

## Revision notes

- Replication = availability + read scale; sharding = write/storage scale
- Sync = stronger; async = faster
- Replication lag → read-your-writes problem; sticky sessions or LSN tokens fix it
- Consistent hashing: moves 1/N keys on rebalance
- Shard key: high cardinality, even distribution, matches access pattern, immutable
- Hot shard fix: cache, sub-partition, redesign
- Split-brain prevention: consensus (Raft/Paxos), fencing tokens
- Cross-shard transactions = 2PC (slow) or sagas (eventually consistent)
- Aurora: shared storage replication; Spanner: TrueTime
- Postgres HA: Patroni; Mongo: replica sets; MySQL: Orchestrator / Group Replication
