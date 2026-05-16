# CAP Theorem & Consistency Models

> **Senior mentor framing.** CAP is the most famous and most *misunderstood* result in distributed systems. Read it once with this analogy in mind: imagine **two identical libraries** in two cities that share a single catalog. A courier syncs new books between them. One day the courier road floods (a **network partition**). A reader walks into library A and asks "do you have the new Murakami?" The librarian has two choices:
>
> - "Yes, here it is" — even though library B may have just received a different newer copy that hasn't synced yet. You answered, but the answer might be **stale**. That is **AP** (Availability under Partition).
> - "Sorry, I can't be sure my catalog is current — come back when the road reopens." You refused to lie, but you also refused to help. That is **CP** (Consistency under Partition).
>
> Everything below — PACELC, quorums, linearizability, eventual consistency, vector clocks — is just the technical vocabulary for that single decision and its consequences.

## Why this matters in backend interviews

- **Mandatory** in every distributed systems / system design round at SDE2 and above.
- **A favourite filter question** — "what's CAP?" is asked early; the depth of your answer signals your level.
- **PACELC** is the modern follow-up; knowing it is a senior signal.
- **Architectural decisions** in real systems (DB choice, replication, region setup) hinge on these trade-offs.

## Why interviewers care

- They are testing **distributed systems fluency** — can you reason precisely about replicas, partitions, and tradeoffs?
- They are testing **tradeoff vocabulary** — can you say *what you give up* when you choose one knob over another?
- They want a candidate who can **defend a design choice** to a skeptical staff engineer: "We chose CP here because the cost of a stale read is greater than the cost of a refused read."
- A weak candidate recites "C, A, P, pick two." A strong candidate says: "In normal operation we get both. Partitions force a choice. Here's what *our* system does, and here's the PACELC profile we picked."

## Progressive build-up — read this if CAP feels abstract

1. **Single node, no replicas.** One database, one process. There is only one copy of the truth. No CAP problem at all — every read is consistent because there is nothing to disagree with.
2. **One leader + one follower (async replication).** Now there are two copies. The follower lags by milliseconds. A read from the follower can be **stale**. You have introduced **eventual consistency** — purely from physics (data takes time to travel).
3. **The network between leader and follower drops.** The follower stops getting updates. Now you must decide: do you keep serving reads from the follower (stale but available → **AP**), or do you stop serving from the follower until it reconnects (consistent but partly unavailable → **CP**)? That decision *is* CAP.
4. **N replicas with quorum reads/writes.** Instead of leader/follower, every node is equal. You vote: "if a majority of replicas agree, that's the truth." This is the Dynamo/Cassandra world. Quorum math (`R + W > N`) is how you tune *where on the CAP-AP spectrum* you sit.
5. **Global, multi-region with bounded clock skew.** Spanner-class systems use synchronized clocks (TrueTime) so they can give you **linearizability globally**. They pay in latency. This is the upper-right corner of the design space.

Each step adds one realistic constraint; the consistency model becomes weaker (or more expensive) at every step.

---

## Core concepts

### CAP theorem (Brewer)

In the presence of a network **P**artition, a distributed system must choose between **C**onsistency and **A**vailability.

- **C** (Consistency): every read returns the most recent write (or an error)
- **A** (Availability): every request gets a non-error response
- **P** (Partition tolerance): the system keeps working despite network failures

Since partitions in a distributed system are inevitable (networks fail), you can't avoid P. So the real choice is **CP or AP**.

> **Common misunderstanding:** CAP is not "pick two of three." Partitions happen — you must tolerate them. The choice is *what to do during a partition*: serve possibly-stale data (AP) or refuse to serve (CP).

#### Mental Model — the CAP triangle, drawn honestly

```
                          C (Consistency)
                              /\
                             /  \
                            /    \
                           /      \
                          /  CP    \      Spanner, etcd, ZooKeeper,
                         /  region  \     HBase, Postgres-sync
                        /            \
                       /  ----------  \
                      / / forbidden   \ \   <-- "CA without P"
                     / /  in a real    \ \      only exists if your
                    / /   distributed   \ \     network never fails
                   / /    system        \ \     (i.e. single node)
                  / /____________________\ \
                 /          AP             \   Cassandra, DynamoDB,
                /          region           \  Riak, CouchDB
               /______________________________\
              A (Availability)              P (Partition tolerance)

Read it as: "If a partition happens, which edge do you slide along —
C-P (stay consistent, give up A) or A-P (stay available, give up C)?"
```

The "CA without P" corner is a fiction in any real network — it implies you have a perfect, never-failing wire. Brewer's CAP is really a *choice on the bottom edge*, not a free pick among three vertices.

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

#### Step-by-step walkthrough — same writes, two different CAP choices

> Setup: two replicas, A and B, sharing one key `x = 0`. T1 (a writer) talks to A. T2 (a reader) talks to B. A network partition cuts A↔B in half.

```
   time ─────────────────────────────────────────────────────────────►

           ┌──────── replica A ─────────┐      ┌──────── replica B ────────┐
   t0  ─►  x = 0                                x = 0
   t1      T1: write x = 5  (OK on A)           (A→B sync pending)
   t2          ╳╳╳╳  PARTITION  ╳╳╳╳            ╳╳╳╳  PARTITION  ╳╳╳╳
   t3                                           T2: read x = ?
   t4      (still partitioned)                  (still partitioned)
   t5      ════════ PARTITION HEALS ════════
   t6      A and B reconcile                    A and B reconcile
```

**Outcome in a CP system (e.g., Spanner, etcd, MongoDB w:majority):**

- At **t3**, B cannot confirm it has the latest value (it can't reach A). It **refuses** the read or returns an error. The system is **unavailable on the minority side** but never returns a wrong answer.
- After **t5**, B catches up. Reads resume.
- Invariant preserved: *every successful read reflects every prior successful write.*

**Outcome in an AP system (e.g., Cassandra ONE, DynamoDB default):**

- At **t3**, B answers `x = 0`. That is **stale** — T1 already wrote 5 — but the system stayed up.
- After **t5**, A and B reconcile (LWW timestamp, vector clock, CRDT merge, or read repair). Eventually B also reports `x = 5`.
- Invariant preserved: *the system always answers; reads may be stale during partitions and for a short window after.*

The literal CAP choice is "what happens at t3?" Everything else is shared.

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

#### Mental Model — PACELC as a 2x2 matrix

PACELC asks two independent questions. Think of it as a matrix, not a list.

```
                     During Partition →
                   ┌──────────────┬──────────────┐
                   │      PA      │      PC      │
                   │ (available,  │ (consistent, │
                   │ maybe stale) │ refuse some) │
   ┌───────────────┼──────────────┼──────────────┤
   │      EL       │  Cassandra,  │   (rare —    │
   │  (fast reads, │  DynamoDB    │  inconsistent│
   │ accept stale) │  default     │  combo)      │
   │   no part.    │              │              │
   ├───────────────┼──────────────┼──────────────┤
   │      EC       │  (uncommon — │  Spanner,    │
   │  (slow but    │  AP-then-    │  Postgres    │
   │ consistent)   │  strict-when │  sync, etcd, │
   │   no part.    │  healthy)    │  ZooKeeper   │
   └───────────────┴──────────────┴──────────────┘

Read the cell: "When partitioned I choose <P-side>. When healthy I choose <E-side>."
```

The two most common real-world cells are **PA/EL** ("fast and eventually consistent — Cassandra, default DynamoDB") and **PC/EC** ("strict and willing to pay latency — Spanner, etcd").

### Consistency model hierarchy (strongest to weakest)

1. **Linearizable** — every operation appears to happen instantaneously at a single point between invocation and response. Real-time ordering is preserved across the whole system. (Spanner; Zookeeper)
2. **Sequential** — operations from each client appear in order; some total order exists across all clients (not necessarily real-time).
3. **Causal** — if write A happened-before write B (causally), all observers see A before B. Concurrent writes can be seen in different orders.
4. **Read-your-writes (Session)** — a client sees its own writes immediately.
5. **Monotonic reads** — never see an older value after seeing a newer one.
6. **Monotonic writes** — your writes are applied in order.
7. **Eventual** — replicas converge "eventually." No order guarantee.

Most "strong consistency" claims in practice mean **linearizable** for single-key operations.

#### Mental Model — first-principles consistency ladder

Imagine four observers watching the same key change over time. The consistency model controls **how much they can disagree** about the order.

```
  Strongest                                                       Weakest
     ▲                                                                ▼
  ┌──────────────┬────────────────┬─────────────┬───────────────────┐
  │ LINEARIZABLE │  SEQUENTIAL    │   CAUSAL    │     EVENTUAL      │
  ├──────────────┼────────────────┼─────────────┼───────────────────┤
  │ Real-time    │ Some single    │ Cause-and-  │ Replicas will     │
  │ total order. │ total order    │ effect      │ converge if you   │
  │ If write A   │ exists. May    │ writes are  │ stop writing.     │
  │ finishes     │ not match      │ ordered;    │ No order guarantee│
  │ before B     │ wall-clock     │ concurrent  │ — observers may   │
  │ starts, no   │ time, but all  │ writes can  │ permanently       │
  │ observer     │ observers see  │ be seen in  │ disagree on order │
  │ sees B first │ the same       │ different   │ of concurrent     │
  │              │ order          │ orders by   │ writes (until LWW │
  │              │                │ different   │  / merge fires)   │
  │              │                │ observers   │                   │
  └──────────────┴────────────────┴─────────────┴───────────────────┘
   Spanner,         single-node     Mongo causal    DynamoDB default,
   ZooKeeper        Postgres        sessions,       Cassandra ONE,
   on single key    consensus       COPS, Riak      DNS, Redis async
                                    causal-plus
```

**Vector clocks** are the data structure that *encodes* causal ordering: each replica stamps a write with a vector `[A:3, B:1, C:0]`, and you can tell at merge time whether two writes are causally ordered (one dominates) or genuinely concurrent (need conflict resolution).

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

#### Mental Model — quorum math is a voting overlap

Picture N=5 replicas as five seats. A write must "convince" W of them; a read must "ask" R of them. If `R + W > N`, the read set and the write set must share **at least one replica** — and that shared replica has the latest write, so the read can detect or return it.

```
   N = 5 replicas:    [ R1 ][ R2 ][ R3 ][ R4 ][ R5 ]

   W=3, R=3   →  R + W = 6 > N = 5    ✓ strong on single key
   ┌────────────┐
   │ write set  │ → R1  R2  R3                              (W = 3)
   └────────────┘
                                ┌────────────┐
   read set   →                 │            │ R3  R4  R5   (R = 3)
                                └────────────┘
                                     ▲
                                     │ overlap at R3
                                     │ — read sees the new write.

   W=1, R=1   →  R + W = 2 ≤ N = 5    ✗ may miss writes (eventual)
       write   → R1
       read    →                          R4
                           (no overlap; R4 may be stale)
```

Tunable consistency in Cassandra/Dynamo is just **dialing W and R per request** to land on the row of the table above that fits your operation: tight quorum for money, ONE for telemetry.

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

#### Mental Model — eventual vs strong, in plain English

- **Strong consistency** is "the system promises that the moment your write returns OK, every subsequent read — by anyone, anywhere — will see it." Like a referee blowing the whistle: as soon as it's official, *everyone* knows.
- **Eventual consistency** is "the system promises that if you stop writing, everyone will *eventually* agree." Like rumors spreading: the truth gets there, but not instantly. Most production "eventual" systems converge in **single-digit milliseconds**, not minutes — so the word "eventual" is unhelpfully vague.
- **Read-your-writes** is a *useful middle ground*: you may see other people's stale data, but you never see your own writes disappear. Built with sticky sessions / causality tokens, not by upgrading the whole DB to strong.

### Linearizability vs serializability

- **Linearizability**: a single-object guarantee about real-time ordering. "Every operation appears atomic at some moment between invocation and response."
- **Serializability**: a multi-object guarantee about transaction ordering. "Concurrent transactions are equivalent to some serial order."
- They're orthogonal. A system can be one without the other. **Strict serializability** = both.

#### Mental Model — linearizable vs serializable, by analogy

- **Linearizable** = the *clock on the wall* matters. Operations on one object look like they happened in some real-time order. Think of a bank ATM: if you deposit, then your spouse checks the balance, the new amount **must** be visible. Single-object guarantee.
- **Serializable** = the *outcome* matters, not the timing. Concurrent multi-statement transactions are reordered into some serial schedule — any one is fine as long as it's a valid sequence. Think of a chess tournament's pairing algorithm: it doesn't matter in what order games were *physically played*, only that the final standings are consistent with *some* valid round-by-round playthrough.
- **Strict serializable** = both. "There exists a real-time-respecting serial order for all transactions on all objects." This is the gold standard. Spanner gives it globally, with TrueTime as the trick.

## Common beginner confusion — read this twice

> Every CAP misunderstanding I've heard in interviews falls into one of these buckets.

1. **"CAP says pick two of three."** — **Wrong.** Partitions are physics, not a design choice. You don't get to pick `P` away. The real statement is: *when a partition happens*, you must sacrifice either C or A. *Absent a partition*, you keep both. That's why PACELC ("E"lse...) exists.
2. **"CP means the system is never available."** — **Wrong.** CP systems are available almost all the time. They become unavailable *only on the minority side of a partition*. A Spanner cluster has multi-nines availability; it just refuses writes during a rare network split.
3. **"AP means data is wrong."** — **Wrong.** AP means data may be *briefly stale*. Replicas converge — usually in milliseconds. The data is not random; it's lagging.
4. **"Eventual consistency = unbounded staleness."** — **Misleading.** "Eventual" is a worst-case math word. In practice, modern AP systems converge in **single-digit ms** under healthy network conditions. You can measure and bound it.
5. **"Quorum reads guarantee correctness, full stop."** — **Wrong.** They guarantee correctness for *single-key reads*, not for transactions across multiple keys. For multi-key invariants you need transactions, LWT (Paxos), or a CP-with-2PC system.
6. **"Strong consistency means slow."** — **Wrong in the common case.** Single-region Postgres with sync replica is strong *and* fast (sub-ms). It's only **global** strong consistency that pays the latency tax — because of the speed of light, not the algorithm.
7. **"ACID-C and CAP-C are the same C."** — **No.** ACID's C is "invariants hold across a transaction" (single-node, schema-level). CAP's C is "replicas agree on the latest value" (multi-node, replication-level). The letters collide; the meanings don't.

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

## Interview storytelling — answers a senior engineer would give

### "Walk me through what happens during a network partition in a CP system vs AP."

> "Let's say I have three replicas, and a partition isolates one of them. In a **CP system** like etcd, that minority node refuses to serve writes — clients are routed to the majority. Reads from the minority either fail or are explicitly stamped as stale. When the partition heals, the minority catches up via the consensus log. So I trade *availability of a small slice* for *no stale answers ever*.
>
> In an **AP system** like Cassandra at consistency ONE, the isolated replica keeps taking writes. Reads from either side return whatever that side has — possibly stale. When the partition heals, hinted handoffs and read repair reconcile the divergent histories using last-write-wins timestamps. So I trade *brief inconsistency* for *always-on writes*.
>
> The choice depends on the cost of a wrong answer vs the cost of a refused answer."

### "Your read-your-writes is broken — diagnose."

> "Classic case: the user writes through the primary, then refreshes and hits a follower that hasn't replicated yet. Three fixes from cheap to expensive:
> 1. **Sticky-session reads** to the primary for N seconds after a write.
> 2. **LSN/causality token**: the client gets a logical position from the write, attaches it to subsequent reads, replicas wait until they're at or past that position.
> 3. **Read from leader always** for that user's session — simple but kills read scale.
>
> In Mongo you'd use `causalConsistency: true`. In Dynamo you'd `ConsistentRead: true` for the affected reads."

### "Why is PACELC more useful than CAP?"

> "CAP only describes behavior during a partition, which is maybe 0.01% of operating time. PACELC tells you what the system does the other 99.99% of the time — do you favor latency or consistency? That second axis is the one that actually shapes p99 latency and architecture cost in steady state."

---

## Bridge — how CAP connects to the next chapters

- **DynamoDB & Cassandra** (next file): both default to PA/EL — available under partition, low latency in steady state. Their *tunables* (`ConsistentRead`, `LOCAL_QUORUM`) are how you climb the CAP ladder when you need to.
- **MongoDB** (sibling file): the same CAP knobs, but exposed as `writeConcern` and `readConcern`. Same physics, different vocabulary.
- **Replication & sharding** (sibling file): replication strategy *is* where CAP shows up at the storage layer — sync vs async replicas literally pick CP vs AP for you.

If you remember nothing else: **CAP is a behavior question, not a label**. Every DB lets you tune it; what you actually pick is a per-operation decision.

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
