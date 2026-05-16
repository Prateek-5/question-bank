# Replication & Sharding

## Intuitive teaching layer — start here

Before any jargon, lock these two pictures into your head. Almost every distributed-database question boils down to one of them.

### Replication = many copies of the same book in many libraries

Imagine a popular novel. You don't keep ONE copy in ONE library and ask the entire city to walk there to read it. You print it, ship copies to every library in town. Now:

- If one library burns down, the book still exists everywhere else (availability).
- Readers near each library don't have to travel far (low-latency reads).
- But when the author releases a new edition, you have a logistics problem: every library must receive the new pages, and until they do, some readers see the old text (replication lag).
- And only ONE place is allowed to print new pages — the publisher (leader/primary). Otherwise two libraries might invent contradictory chapters (split-brain).

That's replication. Same data, many places.

### Sharding = splitting the phone book A-M and N-Z onto two desks

Now imagine a city phone book the size of a building. One desk can't hold it. So you split it: surnames A-M on Desk 1, N-Z on Desk 2. Now:

- Each desk holds less, so it's faster to search.
- Two clerks can answer queries in parallel — write scaling.
- But asking "give me everyone in the city named Patel" hits one desk (good); asking "give me everyone with phone number ending in 7" hits BOTH desks (scatter-gather, slow).
- And if 80% of the city has surnames starting with "S," Desk 2 is overwhelmed and Desk 1 is bored (hot shard).

That's sharding. Different data, different places.

### The two are orthogonal — and usually combined

A real production system does both:

```
                 SHARD 1                   SHARD 2                   SHARD 3
              (A-M users)                (N-S users)                (T-Z users)
              ┌─────────┐                ┌─────────┐                ┌─────────┐
              │ Primary │                │ Primary │                │ Primary │
              └────┬────┘                └────┬────┘                └────┬────┘
                   │ replicates              │ replicates              │ replicates
              ┌────┴────┐                ┌────┴────┐                ┌────┴────┐
              │ Replica │                │ Replica │                │ Replica │
              │ Replica │                │ Replica │                │ Replica │
              └─────────┘                └─────────┘                └─────────┘
```

Sharding is horizontal; replication is vertical. Both axes scale different things.

### Why interviewers care

Distributed-systems intuition is THE signal that separates a senior engineer from a mid-level. The interviewer is checking three things:

1. **Do you know the trade-offs?** Sync vs async, strong vs eventual, hash vs range. Each answer should come with "but the cost is...".
2. **Can you reason about failure?** What happens at 3 AM when a node dies? Most candidates can describe the happy path; seniors describe the recovery path.
3. **Can you choose a shard key in 30 seconds?** That single decision can save or sink a company. They want to see you ask "what's the dominant access pattern?" before you blurt out an answer.

### Common beginner confusion (read this twice)

| Misconception | Reality |
|---|---|
| "Replication and sharding are the same thing" | NO. Replication = copies of the same data. Sharding = different pieces of data on different nodes. You usually do both. |
| "Sharding is solved — just use consistent hashing" | NO. Hot keys, resharding pain, cross-shard joins, and 2PC are unsolved at the application layer. Consistent hashing only fixes node addition pain, not data skew. |
| "Adding replicas helps with write load" | NO. Replicas ONLY scale reads. The leader still takes every write, plus the cost of shipping them to N replicas. |
| "Replication = backup" | NO. A `DELETE` on the leader replicates to followers in milliseconds. You still need PITR snapshots. |
| "Consistent hashing means consistent reads" | NO. "Consistent" here means stable mapping under node changes. It has nothing to do with read consistency models. |
| "Splitting is always faster" | Only if writes don't fit on one box. For 99% of apps, indexing + caching + a beefier box is cheaper than the operational tax of sharding. |

---

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

## Mental Model: master-slave replication

Picture a newsroom. One reporter (the **leader / primary / master**) types the news. Behind them, two interns (**followers / replicas / slaves**) photocopy every sentence the reporter types. Anyone who wants to READ the news can read from any intern's copy — but only the reporter is allowed to TYPE.

```
            ┌─────────────┐
   write →  │   LEADER    │
            │  (primary)  │
            └──────┬──────┘
                   │  WAL / oplog stream
          ┌────────┼────────┐
          ▼        ▼        ▼
      ┌─────┐  ┌─────┐  ┌─────┐
      │ F1  │  │ F2  │  │ F3  │   ← reads served here too
      └─────┘  └─────┘  └─────┘
```

If the reporter has a heart attack, the interns elect one of themselves to become the new reporter (failover / leader election). Until that election finishes, NO new news can be typed — the newsroom is unavailable for writes. Reads from any intern still work.

The whole field of "high availability for databases" is just: how do we elect a new reporter quickly and safely, without two interns both claiming to be the new reporter (split-brain)?

## Mental Model: multi-master (multi-leader)

Now picture TWO newsrooms — one in Tokyo, one in New York — and BOTH are allowed to type new stories. Each newsroom faxes its stories to the other. This is great when:

- Tokyo writers need low write latency from Tokyo.
- New York writers need low write latency from New York.

But what happens when BOTH newsrooms simultaneously decide to publish a story titled "Headline of the Day" with different content? Now there are two truths. You need a **conflict resolution policy**:

- "Last write wins" (lossy — one update is silently dropped).
- "Merge them" (CRDTs — only works for some data types like counters and sets).
- "Ask the user to resolve" (Google Docs comment conflicts).

This is why most teams do not use multi-master unless they MUST (geo-distributed writes, offline-first apps).

## Mental Model: async vs sync replication

Two ways the leader can tell the client "write succeeded":

```
ASYNC (most common):
  Client → Leader: "save this"
  Leader writes locally, replies "OK" immediately.
  Leader (in background) ships the write to followers.
  ↳ Risk: leader dies before shipping → write is LOST.
  ↳ Reward: fast writes.

SYNC (durability-critical):
  Client → Leader: "save this"
  Leader writes locally, ships to followers, waits for ACK.
  Only then does leader reply "OK" to client.
  ↳ Risk: if a sync follower is slow or dead, all writes stall.
  ↳ Reward: durable — write survives leader failure.

SEMI-SYNC (compromise):
  Leader waits for follower to RECEIVE (not apply) the write.
  Postgres + MySQL both support this pattern.
```

The mental shortcut: **async = fast & lossy on failover; sync = safe but fragile**. Production reality: async to most replicas, sync to one nearby replica. You get speed AND a durability anchor.

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

### Step-by-step: how a write actually propagates

This is the walkthrough an interviewer wants to hear when they ask "what happens when I do an INSERT?"

```
T=0ms   Client sends INSERT to Leader.
T=1ms   Leader appends to its WAL (write-ahead log) on local disk.
        ↳ This is the "durability anchor" on the leader.
T=2ms   Leader applies the change to its in-memory page cache.
T=3ms   Leader returns "OK" to client (if async).
        ─── client thinks it's done ───
T=4ms   Leader's replication thread reads the new WAL entry.
T=5ms   Leader ships the WAL entry over the network to Follower A.
T=8ms   Follower A receives, appends to its own WAL, ACKs leader.
T=9ms   Follower A's apply thread replays the WAL entry on its data files.
        ↳ Now reads from Follower A see the write.
T=15ms  Follower B (slow, perhaps in another region) finally catches up.
```

Key insights to drop in an interview:

- The "OK" to the client and the "follower has applied it" are TWO DIFFERENT events. The gap between them is **replication lag**.
- If you do `INSERT` and then immediately `SELECT` from Follower A, you may get the OLD value. This is the read-after-write inconsistency problem.
- "Receive" (durable on the follower's disk) and "apply" (visible to readers on the follower) are also two different events.
- Sync replication makes step T=3ms wait for step T=8ms. Faster durability, slower client.

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

## Mental Model: range sharding vs hash sharding vs directory sharding

Three flavors. The trade-off is always the same: **how easy are range queries vs how even is the distribution**.

```
RANGE SHARDING (phonebook A-M, N-Z):
  ┌──────┬──────┬──────┐
  │ A-F  │ G-M  │ N-Z  │      ← keys grouped by natural order
  └──────┴──────┴──────┘
  + range queries are FAST (one shard)
  - hot spots: if today's writes all have key "Z..." (timestamps!), Shard 3 is on fire

HASH SHARDING (throw keys in a blender):
  ┌──────┬──────┬──────┐
  │  H1  │  H2  │  H3  │      ← shard = hash(key) % N
  └──────┴──────┴──────┘
  + perfectly even distribution
  - range queries are SCATTER-GATHER (hit all shards)

DIRECTORY SHARDING (a lookup table decides):
   ┌─────────────────────┐
   │  DIRECTORY SERVICE  │      ← arbitrary "key → shard" map
   └─────────┬───────────┘
             │
   ┌─────────┼─────────┐
   ▼         ▼         ▼
  Shard1   Shard2   Shard3
  + flexible: rebalance gracefully, move any key anywhere
  - directory itself is a SPOF / extra hop
```

Most modern systems lean **hash + virtual nodes + consistent hashing** because the math gracefully handles node failures and additions.

### Step-by-step: how a query is routed to the correct shard

```
Client query: "find user 12345"
   │
   ▼
┌──────────────────┐
│  Router / Proxy  │     (mongos, Vitess vtgate, Citus coordinator, app code)
└──────────────────┘
   │
   │ shard_id = hash("12345") % N   OR   range lookup
   ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Shard 1 │  │ Shard 2 │  │ Shard 3 │
└─────────┘  └─────────┘  └─────────┘
                ▲
                │ "I own user 12345"
                │
            user found → returned to router → returned to client
```

If the query has NO shard key (e.g., "find all users named Alice"), the router has to fan out the query to EVERY shard and merge results. This is the **scatter-gather** problem. Latency = slowest shard's latency. This is why aligning your shard key with your dominant query pattern is non-negotiable.

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

### ASCII: consistent hashing ring with virtual nodes

The hash space is a circle (0 to 2^32 - 1 wrapping back to 0). Each physical node is sprinkled onto the ring at many positions (its **virtual nodes / vnodes**). Each KEY also hashes to a position on the ring. The key is owned by the next vnode CLOCKWISE.

```
                       hash = 0  /  2^32
                            ▲
                            │
                       ┌────┴────┐
                       │   B1    │             ← B's vnode #1
                       │   A2    │             ← A's vnode #2
        K3 ←───┐       │         │
               │       │         │
               │       │   C1    │
            ┌──┴──┐    └─────────┘
            │ ring│         ↑
            │     │      ┌──┴──┐
            └──┬──┘      │     │   ← clockwise traversal
               │         │  B2 │   K3 hashes here →
               │         └──┬──┘     owner = next clockwise = C1
               ▼            │
           ┌─────────┐      ▼
           │   A1    │   ┌─────────┐
           │   C2    │   │   A3    │
           └─────────┘   │   B3    │
                         └─────────┘

Physical nodes: A, B, C
Virtual nodes per physical: 3 (in real systems: 100-256)
Why vnodes? Without them, 3 physical nodes = 3 positions on a huge ring,
and one node randomly ends up owning 60% of the keys (bad).
With 256 vnodes each, the law of large numbers gives near-perfect spread.

Node addition (D arrives with vnodes D1, D2, D3):
  ↳ Only the keys between D's vnodes and the previous (counter-clockwise)
    vnode move. About 1/N of keys total.

Node removal (B fails):
  ↳ B's vnodes are taken over by their clockwise neighbors.
  ↳ Replication factor 3 = each key was already on 3 distinct physical nodes,
    so no data is lost — just rebalanced.
```

This is the SINGLE most important diagram in distributed databases. If you can draw this and explain it, you've signaled senior distributed-systems intuition.

## First principles: consistency models

When interviewers ask "what consistency does your system give?" they're testing whether you know this ladder, strongest at the top.

```
LINEARIZABLE
  "All operations appear to happen in a single global order, matching real time."
  Mental model: as if there is ONE machine answering everyone.
  Cost: every read/write coordinates with consensus. Slow.
  Examples: Spanner, etcd, ZooKeeper.

SEQUENTIAL
  "All clients see ops in the SAME order, but that order may not match real time."
  Mental model: there's a single global order, but a fresh write may not be
  visible to a reader who started before it.

CAUSAL
  "If event A caused event B, every observer sees A before B. Independent
  events may appear in any order."
  Mental model: WhatsApp message order — reply always comes after original.
  Examples: MongoDB causal consistency sessions, Cosmos session tokens.

READ-YOUR-WRITES
  "Your own writes are visible to you, but other clients may see older data."
  Mental model: sticky session.

EVENTUAL
  "If writes stop, all replicas eventually converge."
  Mental model: DNS propagation.
  Cheapest. Most NoSQL defaults to this.
```

Most "distributed-systems" interview confusion comes from candidates not realizing these are SEPARATE knobs. You can have linearizable single-key but eventual across keys. You can have causal between sessions but eventual across replicas.

## First principles: quorum math (R + W > N)

The quorum equation is the math behind Cassandra/Dynamo-style strong reads:

```
N = total replicas of a key
W = replicas that must ACK a WRITE before it's "done"
R = replicas the client must READ from before returning

If R + W > N, then any READ overlaps with the latest WRITE on at least
one replica → the client can detect the latest version → STRONG CONSISTENCY.

Examples (N = 3):
  W=1, R=1 → fast, eventual (no overlap guarantee)
  W=2, R=2 → strong (2 + 2 = 4 > 3) ← typical QUORUM
  W=3, R=1 → strong reads, slow writes (need all replicas)
  W=1, R=3 → strong reads, fast writes, slow reads
```

Why this works: any two majorities of 3 must share at least one member (pigeonhole). That shared replica has the latest write, and the client picks the newest version it sees during the read.

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

## Interview storytelling: "Design Twitter's storage"

A senior interviewer drops "design the storage for Twitter" on the table. Here's how to think through it using everything above.

**Step 1 — what are the dominant access patterns?**
- Post a tweet (high write).
- Read your home timeline (very high read).
- Read a user's profile timeline.
- Search (separate concern — Elasticsearch).

**Step 2 — pick the shard key per workload.**
- `tweets` table: shard by `user_id` (hash). All of one user's tweets co-located. The "celebrity user" problem is real → sub-partition celebrities' tweets by `(user_id, time_bucket)`.
- `timeline` (denormalized feed): shard by `viewer_id` (hash). Each user's feed lives on one shard — single-shard read for "show my timeline."

**Step 3 — replication?**
- Replication factor 3 across AZs for durability.
- Reads from local replicas with read-your-writes session token (or read primary for writes that just happened, e.g., your own tweet must show in your feed immediately).

**Step 4 — describe the failure modes.**
- Leader of one shard dies → 10-30s election, that shard's writes pause, reads from replicas continue.
- A celebrity tweets → that shard's WCU spikes → adaptive capacity / hash-suffix mitigates.

**Step 5 — what would you NOT do?**
- Shard by `tweet_id` (hash). Even distribution, sure, but every "show my timeline" becomes a scatter-gather. Wrong key.

### Interview storytelling: "Your DynamoDB partition is hot — what do you do?"

The disciplined 4-step answer:

1. **Confirm it's actually a hot partition** — CloudWatch shows throttling on a single partition while others idle. Don't fix what isn't broken.
2. **Quick mitigation** — bump on-demand mode or raise WCU/RCU temporarily. Buy time.
3. **Short-term redesign** — add a hash suffix to the PK: `USER#42` becomes `USER#42#3` where `3 = hash(item_id) % 8`. Reads now scatter to 8 sub-partitions (small scatter-gather acceptable).
4. **Long-term redesign** — re-examine the access pattern. Maybe a separate "hot keys" table with a different model. Maybe DAX (read-through cache) absorbs the read storm. Maybe the celebrity user just needs their own table.

The signal: you didn't jump to "rewrite everything." You bought time, then attacked the root cause.

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

---

## Learning bridge — where to go from here

Everything above is the THEORY. The next two files apply it to specific products.

- **04-mongodb.md** is "replication and sharding, but in a document database." Mongo replica sets = the master-slave model from this file, with Raft-style elections. Mongo sharding = hash or range sharding from this file, routed through `mongos`. The shard-key advice carries over verbatim.
- **05-dynamodb-cassandra.md** is "replication and sharding, but leaderless wide-column style." DynamoDB hides everything; Cassandra exposes the quorum knobs (R, W, N) you saw in the first-principles section. The consistent-hashing ring above IS Cassandra's data placement diagram.

Carry these mental models forward:

1. The leader-follower diagram → MongoDB replica set.
2. The consistent hashing ring → Cassandra topology + DynamoDB partition tree.
3. The quorum equation (R + W > N) → Cassandra's tunable consistency.
4. The shard-key checklist (cardinality, even distribution, immutable, aligned with reads) → applies to MongoDB shard key AND DynamoDB partition key AND Cassandra partition key. Same rules, three names.
