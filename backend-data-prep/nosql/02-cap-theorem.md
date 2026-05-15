# CAP Theorem & Consistency Models

## Why this matters in backend interviews

- **Mandatory** in every distributed systems / system design round at SDE2 and above.
- **A favourite filter question** — "what's CAP?" is asked early; the depth of your answer signals your level.
- **PACELC** is the modern follow-up; knowing it is a senior signal.
- **Architectural decisions** in real systems (DB choice, replication, region setup) hinge on these trade-offs.

---

## Core concepts

### CAP theorem (Brewer)

In the presence of a network **P**artition, a distributed system must choose between **C**onsistency and **A**vailability.

- **C** (Consistency): every read returns the most recent write (or an error)
- **A** (Availability): every request gets a non-error response
- **P** (Partition tolerance): the system keeps working despite network failures

Since partitions in a distributed system are inevitable (networks fail), you can't avoid P. So the real choice is **CP or AP**.

> **Common misunderstanding:** CAP is not "pick two of three." Partitions happen — you must tolerate them. The choice is *what to do during a partition*: serve possibly-stale data (AP) or refuse to serve (CP).

### CP systems

During a partition, the minority side refuses requests rather than serving stale data.
- Examples: **Postgres** (single primary), **MongoDB** (with majority writes), **ZooKeeper**, **etcd**, **HBase**, **Spanner**
- Trade-off: availability dips during failures
- Use when correctness > uptime: money, inventory, locks

### AP systems

During a partition, all nodes still accept reads and writes; conflicts are resolved later.
- Examples: **Cassandra** (default), **DynamoDB** (default), **CouchDB**, **Riak**
- Trade-off: stale reads possible; writes may conflict
- Use when uptime > strict consistency: feeds, sessions, caches, telemetry

### PACELC (the modern version)

**If P**artition: choose **A** or **C**.
**Else** (normal operation): choose **L**atency or **C**onsistency.

This is more useful because it covers the 99.9% of time when there's no partition.

| System | Partition behavior | Normal behavior |
|---|---|---|
| Spanner | PC (consistent) | EC (consistent, sacrifices some latency) |
| Cassandra | PA (available) | EL (low latency, eventual) |
| DynamoDB (default) | PA | EL |
| DynamoDB (strong reads) | PC | EC |
| Postgres + sync replica | PC | EC |
| Postgres + async replica | PC | EL (followers can lag) |

### Consistency model hierarchy (strongest to weakest)

1. **Linearizable** — every operation appears to happen instantaneously at a single point between invocation and response. Real-time ordering is preserved across the whole system. (Spanner; Zookeeper)
2. **Sequential** — operations from each client appear in order; some total order exists across all clients (not necessarily real-time).
3. **Causal** — if write A happened-before write B (causally), all observers see A before B. Concurrent writes can be seen in different orders.
4. **Read-your-writes (Session)** — a client sees its own writes immediately.
5. **Monotonic reads** — never see an older value after seeing a newer one.
6. **Monotonic writes** — your writes are applied in order.
7. **Eventual** — replicas converge "eventually." No order guarantee.

Most "strong consistency" claims in practice mean **linearizable** for single-key operations.

### Quorum (Dynamo-style)

Reads and writes go to multiple replicas. Define:
- N = total replicas
- W = nodes that must acknowledge a write
- R = nodes that must respond to a read

If **R + W > N**, you have strong consistency for single-key reads (any read overlaps with the latest write).

| Setting | Behavior |
|---|---|
| W=N, R=1 | Fast reads, slow writes; tolerate read-only outages |
| W=1, R=N | Fast writes, slow reads |
| W=quorum, R=quorum | Balanced; W=⌈N/2⌉+1, R=⌈N/2⌉+1 |
| W=1, R=1 | Eventual; max availability |

Trade-offs: higher R/W increases latency and reduces availability; lower R/W introduces staleness.

### Conflict resolution (in AP systems)

When concurrent writes happen on different replicas:
- **Last Write Wins (LWW)** — pick the write with the latest timestamp (Cassandra default). Risk: clock skew loses writes.
- **Vector clocks** — track causality between writes; surface conflicts to the application (Dynamo, Riak).
- **CRDTs** (Conflict-free Replicated Data Types) — data structures that converge by construction (counters, sets, maps). Used in Redis Enterprise, Yjs/Automerge.
- **Application merge** — system surfaces both versions; app picks/merges.

### Read-your-writes & session consistency

In leader-follower replication, if a client writes to the leader then reads from a follower, the follower may not have replicated yet. Mitigations:
- **Sticky session**: route reads to the same leader for that user for N seconds after a write
- **Read from leader after recent write**
- **Monotonic read marker**: track the LSN/timestamp the client has seen; require the replica to be at least that current
- **DynamoDB**: request `ConsistentRead: true` for strongly consistent reads

### Linearizability vs serializability

- **Linearizability**: a single-object guarantee about real-time ordering. "Every operation appears atomic at some moment between invocation and response."
- **Serializability**: a multi-object guarantee about transaction ordering. "Concurrent transactions are equivalent to some serial order."
- They're orthogonal. A system can be one without the other. **Strict serializability** = both.

### Common misconceptions

- "CAP is pick two of three" — wrong; partitions are not optional
- "Strong consistency means slow" — depends. Single-region Postgres is fast and strong. Global linearizable systems pay extra.
- "Eventual consistency is dangerous" — it's a trade-off; most internet-scale services (feeds, search, sessions) are perfectly fine with it
- "ACID = CAP-C" — not the same. ACID is about transactions on one node; CAP-C is about replicas across nodes
- "Quorum guarantees consistency in all cases" — only for single-key reads; doesn't help with transactions

### Interview traps

1. **"Is MongoDB CP or AP?"** — it depends on write concern. Default `w:1` is more AP-ish; `w:majority` is more CP. Always ask.
2. **"Cassandra is AP, so it can't be strongly consistent?"** — wrong. Cassandra is tunable; you can achieve linearizable with QUORUM reads + QUORUM writes (with `LIGHTWEIGHT_TRANSACTIONS` using Paxos for true linearizable).
3. **"What about Spanner?"** — globally distributed, externally consistent (linearizable). Uses TrueTime (atomic clocks + GPS) to bound clock skew.
4. **"How do you achieve strong consistency in DynamoDB?"** — request `ConsistentRead: true`; only available on the primary partition's leader.
5. **"PACELC?"** — most candidates haven't heard of it. Drop it unprompted.

---

## Real examples

### E-commerce — cart and order

| Operation | Consistency need | Choice |
|---|---|---|
| Add to cart | Eventual is fine | Cache (Redis), low-cost |
| Place order | Strong (don't oversell) | Postgres ACID transaction |
| Display product price | Eventual (cached) | Redis with 60s TTL |
| Update inventory | Strong | Postgres + row lock |
| Order history | Read-your-writes | Read from primary or sticky-session |

### Social media — feed

| Operation | Consistency | Choice |
|---|---|---|
| Post a tweet | Read-your-writes | Show poster's own tweet immediately |
| Fan-out to followers | Eventual | Queue, propagate in background |
| Like count | Eventual (approximate) | Counter cache; periodic correction |
| Follower count | Eventual | Cache; non-critical accuracy |

### Banking — PACELC choice

- **Single-region**: Postgres primary, sync replica. PC + EC. High consistency, modest latency.
- **Multi-region**: hard. Use Spanner-style (CP + EC) or split: per-region accounts with global ledger.

### Distributed lock service

ZooKeeper, etcd, Consul: CP. During partition, the minority side cannot acquire locks. **You want this**: a lock that returns "available" during a partition is worse than one that says "unavailable."

### IoT telemetry ingestion

Cassandra: AP + EL. Drop a few writes during partition? No — Cassandra keeps accepting writes; hinted handoffs / read repair fix conflicts. Ideal for high-volume append.

---

## Common interview questions

1. State the CAP theorem precisely.
2. CP vs AP — examples?
3. What is PACELC?
4. What is eventual consistency?
5. Quorum reads and writes — explain.
6. Linearizability vs serializability.
7. How does Spanner achieve global consistency?
8. How does DynamoDB / Cassandra resolve concurrent writes?
9. What is read-your-writes consistency? How to achieve it across replicas?
10. Is MongoDB CP or AP?
11. What is "strict serializability"?
12. Why is "pick two of three" a misleading way to think about CAP?

---

## Detailed answers

### 1. CAP precisely
"In a system with replicas across a network, when a network partition occurs, you must choose between consistency (all reads see the latest write) and availability (every request gets a response). Partition tolerance isn't optional in a distributed system, so the practical choice is CP vs AP."

### 2. CP vs AP examples
- CP: Spanner, etcd, ZooKeeper, HBase, MongoDB with `w:majority`, Postgres with synchronous replica
- AP: Cassandra, DynamoDB, Riak, CouchDB

### 3. PACELC
Extends CAP: during Partition choose A or C; Else (normal operation) choose L (latency) or C (consistency). Most useful classification framework.

### 4. Eventual consistency
After a write, replicas converge to the same value given enough time and absence of new writes. No bound on time. In practice, milliseconds to seconds. Reads may see stale data briefly.

### 5. Quorum
- N replicas. Read requires R, write requires W.
- If R + W > N → strong consistency (overlap)
- Tunable per request in Cassandra/Dynamo
- Common: W=quorum, R=quorum for balance

### 6. Linearizable vs serializable
- Linearizable: real-time ordering on single object
- Serializable: transactions appear to run in some serial order
- Spanner: both → "strict serializable"
- Postgres SERIALIZABLE: serializable within single-node; not necessarily linearizable across replicas

### 7. Spanner global consistency
- TrueTime: atomic clocks + GPS bound clock uncertainty (~few ms)
- Each transaction picks a commit timestamp within the uncertainty window and waits it out → externally consistent
- Paxos for replicated state; two-phase commit for cross-shard

### 8. Conflict resolution
- Cassandra: LWW by default (latest timestamp). Optional `IF` lightweight transactions for compare-and-set (Paxos-backed).
- DynamoDB: LWW; conditional updates for safety
- Dynamo (paper): vector clocks → app reconciles
- Modern Dynamo / DynamoDB: LWW + conditional writes

### 9. Read-your-writes across replicas
- Route reads to primary
- Sticky session for N seconds after write
- Replica position marker: client tracks the latest LSN; reads wait until replica catches up
- Causal consistency tokens (Mongo `causalConsistency`)

### 10. MongoDB CP or AP?
Tunable. Default `w:1, readConcern: 'local'` is closer to AP and read-stale-possible. `w:majority, readConcern: 'majority'` + `readPreference: primary` is CP. Sharded clusters with replication are CP for individual keys with proper write/read concerns.

### 11. Strict serializability
Linearizable + serializable. Transactions appear to execute in a serial order consistent with real-time. Spanner offers this globally; Postgres offers it within a single node.

### 12. CAP not "pick two"
You can't opt out of P; networks fail. The decision is **during a partition**, do you sacrifice C or A? In normal operation, you can have both. "Pick two" implies a static choice that doesn't match reality.

---

## Practical coding examples

### DynamoDB strong vs eventual read
```javascript
// Eventually consistent (default; cheaper)
await ddb.getItem({ TableName: 't', Key: { id: '1' } }).promise();

// Strongly consistent (twice the cost)
await ddb.getItem({ TableName: 't', Key: { id: '1' }, ConsistentRead: true }).promise();
```

### Cassandra tunable consistency
```javascript
// LOCAL_QUORUM: majority in the local DC
client.execute("SELECT * FROM users WHERE id=?", [id], { consistency: cassandra.types.consistencies.localQuorum });

// ONE: any replica (fastest)
// ALL: every replica (strongest, least available)
```

### MongoDB write concern
```javascript
await db.collection('orders').insertOne(order, { writeConcern: { w: 'majority', j: true } });
// w: majority → majority of replicas ack
// j: true → durable to journal (fsync)
```

### Postgres synchronous replication
```ini
# postgresql.conf
synchronous_standby_names = 'replica1'
synchronous_commit = on  # wait for sync replica
```
Writes block until the replica confirms. CP-style for the cluster.

### Detect replication lag (Postgres)
```sql
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
FROM pg_stat_replication;
```

---

## Common mistakes

- Stating "CAP says pick two of three"
- Calling Mongo "AP" without qualifying write concern
- Assuming eventual consistency = data loss
- Picking AP for a system that needs invariants (banking, locks)
- Misusing quorum: R+W not > N → silently eventual
- Ignoring clock skew when using LWW conflict resolution
- Believing async replication is fine for read-your-writes (it isn't)

---

## Senior engineer discussion points

- **Hybrid logical clocks (HLC)** — used by CockroachDB to bound causality without TrueTime
- **CRDTs in practice** — Redis Enterprise, Yjs/Automerge for collaborative editing
- **Multi-region trade-offs** — single-region strong vs global eventual vs Spanner-style
- **Tunable consistency per operation** — common in modern DBs; choose per query
- **Geo-partitioning** — keep user data in their home region for fast strong reads
- **Eventual-by-default with strong-by-request** — Dynamo `ConsistentRead`, Cassandra `ALL`
- **The hidden cost of "strong"** — sync replicas slow writes; quorum reads cost throughput
- **Calvin / FaunaDB approach** — deterministic transactions with pre-ordering (no locks)
- **Why Postgres is "good enough"** for most companies: vertical scale + single-region works to 50–100k QPS

---

## Revision notes

- CAP: during partition, choose C or A (P is forced)
- PACELC: + Else choose L or C (latency vs consistency)
- CP examples: Spanner, etcd, ZK, Postgres-sync
- AP examples: Cassandra, Dynamo, Riak, Couch
- Quorum: R + W > N → strong (single key)
- Linearizable = real-time single-object; serializable = transaction order
- Spanner: TrueTime → strict serializable globally
- Cassandra/Dynamo: tunable consistency per request
- LWW = simplest conflict resolution, sensitive to clock skew
- CRDTs converge by construction
- Read-your-writes: leader reads, sticky sessions, LSN tracking
- Mongo `w:majority` ≈ CP, default `w:1` ≈ more AP
