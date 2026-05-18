# Cassandra Quorum Math Drill — R + W > N and Multi-DC Variants

## Source / Origin
- Datastax Cassandra docs on tunable consistency.
- Originated in Dynamo paper (2007) — Cassandra inherited R/W/N quorum vocabulary.
- Standard senior interview prompt: "Given RF=3, what R and W gives you strong consistency, and what's the latency cost?"
- Companion concept doc: `backend-data-prep/nosql/03-cassandra-internals.md` — "Tunable consistency" section.

## Why this question matters in interviews
This is the **single most-asked Cassandra question at senior rounds.** It tests three things in one shot: (a) do you know the quorum overlap formula, (b) can you reason about availability vs latency tradeoffs, and (c) do you understand how multi-DC complicates the picture (`LOCAL_QUORUM` vs `EACH_QUORUM`). Candidates who can rattle off "R + W > N gives strong consistency" but can't draw why on a whiteboard get downgraded. The interviewer wants you to **draw the overlap of read and write replica sets** and explain why one node must be in both.

## Concepts involved

### Syntax to lock in

```cql
-- Per-query consistency level (CQL)
SELECT * FROM users WHERE id = ? USING CONSISTENCY QUORUM;
INSERT INTO users (...) VALUES (...) USING CONSISTENCY LOCAL_QUORUM;

-- Driver-side default (Java DataStax driver)
QueryOptions opts = new QueryOptions()
  .setConsistencyLevel(ConsistencyLevel.LOCAL_QUORUM);
```

The formula:
```
RF = N        (replication factor — number of replicas per partition)
R  = read consistency level (how many replicas must respond to a read)
W  = write consistency level (how many replicas must ack a write)

R + W > N    ⇒  strong consistency (every read sees the latest write)
R + W ≤ N    ⇒  eventual consistency (read may miss a recent write)

QUORUM  = floor(N/2) + 1
```

Common consistency levels in Cassandra:
- `ONE`, `TWO`, `THREE` — fixed count
- `QUORUM` — floor(N/2) + 1 across all DCs
- `LOCAL_QUORUM` — floor(N_local/2) + 1 within the coordinator's DC
- `EACH_QUORUM` — quorum within every DC
- `ALL` — every replica
- `ANY` — hinted handoff is enough (writes only)
- `LOCAL_ONE`, `SERIAL`, `LOCAL_SERIAL` (LWT — Paxos)

### Edge cases / interview traps
1. **`QUORUM` across multi-DC = WAN latency.** If you have RF=3 in each of 2 DCs (N=6), `QUORUM` = 4, and you may need acks from the remote DC. Latency explodes. Use `LOCAL_QUORUM` for client-facing paths.
2. **`LOCAL_QUORUM` reads + `LOCAL_QUORUM` writes ≠ globally strong.** Two DCs both writing locally can diverge. Need `EACH_QUORUM` or app-level conflict resolution.
3. **`R + W > N` gives strong consistency under no failure**, but during a failure (some replicas down), the read may still succeed with stale data if hinted handoff is delayed. Cassandra uses **last-write-wins by timestamp** for conflicts.
4. **Quorum is not Paxos.** Quorum reads/writes are *not* linearizable for read-modify-write. For compare-and-set semantics you need lightweight transactions (`SERIAL` consistency, Paxos round-trip = 4x latency).
5. **Tombstones still need quorum to delete.** A delete at `ONE` consistency leaves the data alive on other replicas; gc_grace_seconds matters.
6. **N is per-partition, not per-cluster.** RF=3 means each partition has 3 replicas, not that the cluster has 3 nodes.
7. **Read repair fires asynchronously.** If the read at `QUORUM` sees divergence, the stale replicas are repaired in the background — read latency includes only the quorum response time.
8. **`ALL` is brittle.** One replica down = all writes fail. Never use `ALL` in production for hot paths.

## Mental Model

### The overlap diagram

```
RF = N = 5. W = 3 (quorum write). R = 3 (quorum read).
Partition replicas: {A, B, C, D, E}

Write set chosen by coordinator: {A, B, C}   ← W=3 acks
                                  ░░░░░░░
                                  ░░░░░░░
Read set chosen by coordinator:  {C, D, E}   ← R=3 responses
                                  ░░░░░░░
                                  
Overlap:                          {C}        ← at least one node has the write

Because |W| + |R| = 3 + 3 = 6 > 5 = N,
pigeonhole guarantees ≥1 replica in both sets.
That replica has the latest write → read sees it.
```

```
If W=2, R=2, N=5:
Write set: {A, B}        |W| + |R| = 4 ≤ 5
Read set:  {C, D}        Possible disjoint sets — read misses the write.
                          Eventual consistency.
```

### Latency ladder (single DC, RF=3)
```
CL=ONE        ─ 1 replica responds  ─ p99 ≈ 5ms   (least durable read)
CL=QUORUM     ─ 2 replicas respond  ─ p99 ≈ 8ms   (strong w/ W=QUORUM)
CL=ALL        ─ 3 replicas respond  ─ p99 ≈ 15ms  (slowest replica bound)
CL=SERIAL     ─ Paxos 4 round trips ─ p99 ≈ 40ms  (linearizable)
```

## Why interviewers care
- It's the **canonical Dynamo-style consistency question** — answers reveal whether you understand quorum math or just memorized "R + W > N".
- Multi-DC variants test whether you've **operated** Cassandra in production, not just read about it.
- The follow-up — "what about LWT?" — opens the door to Paxos discussion (the *real* senior signal).
- It's the easiest way to filter candidates who confuse Cassandra (AP system) with Mongo/Spanner (CP-ish systems).

## Common beginner confusion
- **"QUORUM means majority of the cluster."** No — majority of the *replicas for that partition* (`RF`), not the whole cluster.
- **"R + W > N gives linearizability."** It gives strong consistency for single-key reads, *not* linearizability and *not* compare-and-set. Read-modify-write still races.
- **"LOCAL_QUORUM is the same as QUORUM in one DC."** It is — but only when there's exactly one DC. Multi-DC changes everything.
- **"ALL is the safest."** It's the most *consistent* but least *available* — single replica failure breaks it. Quorum is the right default.
- **"Higher CL = always slower."** Approximately, but speculative retry and dynamic snitch can mask it for tail latencies.

## Brute force approach
"Set everything to `ALL`." Strongest consistency, but writes fail any time a single replica is down. Throughput dies, availability dies. Don't.

"Set everything to `ONE`." Fastest reads/writes, but you lose strong consistency. Acceptable for analytics; never for user-facing single-record lookups.

## Optimal approach

The four real configurations you'll see in production:

1. **Strong consistency, single DC** — `RF=3`, `R=QUORUM`, `W=QUORUM`. R+W=4 > 3. Default for OLTP-ish workloads.
2. **Read-heavy, eventually consistent** — `RF=3`, `R=ONE`, `W=QUORUM`. Reads are fast (5ms), writes are durable. Reads may be slightly stale.
3. **Multi-DC strong-local** — `RF=3` per DC, `R=LOCAL_QUORUM`, `W=LOCAL_QUORUM`. Each DC is internally consistent; cross-DC is eventually consistent.
4. **Multi-DC globally strong** — `R=EACH_QUORUM` or `W=EACH_QUORUM`. WAN latency on writes; rarely used.

## Solution

### Drill 1: RF=3, what gives strong consistency?

| R | W | R + W | > N? | Consistency |
|---|---|-------|------|-------------|
| 1 | 1 | 2     | No   | Eventual |
| 1 | 3 | 4     | Yes  | Strong (read at ONE, write at ALL) |
| 3 | 1 | 4     | Yes  | Strong (read at ALL, write at ONE) |
| 2 | 2 | 4     | Yes  | Strong (R=W=QUORUM — the default) |
| 1 | 2 | 3     | No   | Eventual |

The sweet spot is `R=QUORUM, W=QUORUM` — balanced latency, balanced availability.

### Drill 2: RF=5, give me R=2, W=?

R + W > 5 ⇒ W ≥ 4. So `W=4` (which is `QUORUM` for RF=5) or `W=ALL=5`. With `W=4`, one replica can be down and writes still succeed.

### Drill 3: Multi-DC, RF=3 in DC1 and RF=3 in DC2 (N=6 total). Client in DC1. What's `QUORUM`?

`QUORUM` = floor(6/2) + 1 = 4. You may need acks from DC2 (WAN). Latency: 50-150ms.

`LOCAL_QUORUM` = floor(3/2) + 1 = 2 acks within DC1 only. Latency: 5-10ms. **Almost always what you want.**

`EACH_QUORUM` = 2 acks in DC1 AND 2 acks in DC2. Latency: WAN-bound. Use only when business demands globally synchronous.

### Drill 4: Availability under failure

RF=3, `QUORUM` (W=2). How many node failures can you tolerate?

- 0 failures: writes succeed at 2/3 ack.
- 1 failure: writes succeed at 2/2 remaining. OK.
- 2 failures: only 1 replica up; can't get 2 acks. Writes fail.

Tolerates **1 replica failure**. With `RF=5, QUORUM=3`, tolerates **2 failures**.

### Drill 5: Compare-and-set semantics

```cql
-- This is NOT atomic at QUORUM:
SELECT balance FROM accounts WHERE id = 1;          -- read 100
UPDATE accounts SET balance = 80 WHERE id = 1;       -- two clients race → lost update

-- Atomic via LWT (Paxos, SERIAL consistency):
UPDATE accounts SET balance = 80
  WHERE id = 1
  IF balance = 100;                                  -- atomic compare-and-set
-- Paxos: 4 round trips. ~4x latency of QUORUM.
```

## Step-by-step dry run

**Scenario:** RF=3, replicas for key `k` are nodes {A, B, C}. Write `v=5` at `QUORUM` (W=2).

```
t=0   Client → Coordinator (node X)
t=1   X forwards write to A, B, C in parallel
t=8   A acks
t=9   B acks                          ← 2 acks reached → success returned to client
t=12  C acks (in background)         ← C now also has v=5

t=20  Client reads at QUORUM (R=2)
t=21  X picks 2 replicas to query: say B and C
t=25  B returns v=5
t=26  C returns v=5                   ← both agree, return v=5 to client. STRONG.
```

**Same scenario, but C was down during the write:**

```
t=0   Write at QUORUM. A and B ack. C is down.
      Hinted handoff: X stores a hint for C.
t=20  C is still down.
      Read at QUORUM (R=2). X picks A and B → both have v=5. STRONG.
      
      What if X picks A and C? It can't — C is down. Driver/coordinator
      picks live replicas first (speculative retry). Read still gets v=5.
      
t=60  C comes back online.
      X delivers the hint. Now C also has v=5.

What if C comes back but the read happens before the hint is delivered?
      Coordinator picks A and C. A=v=5, C=v=old. 
      Quorum sees the divergence, picks newer timestamp → returns v=5.
      Read repair fires async, fixes C.
```

**Bad scenario: write at ONE, read at ONE.**

```
t=0   Write v=5 at ONE. A acks. B, C still have v=old.
t=20  Read at ONE. Coordinator picks B. Returns v=old.    ← STALE.
      R + W = 1 + 1 = 2 ≤ 3 = N. Eventual consistency. Expected.
```

## How to think aloud in the interview

> "Right — Cassandra is a Dynamo-style AP system with tunable consistency. The fundamental rule is `R + W > N` gives you strong consistency, where N is the replication factor for that partition, not the cluster size.
>
> If I have RF=3, the typical setup is `R=QUORUM, W=QUORUM` — that's 2+2=4 > 3. Quorum reads see quorum writes because the write set and read set must share at least one replica by pigeonhole. That replica carries the latest timestamp, and Cassandra resolves with last-write-wins.
>
> A few traps. First, this doesn't give linearizability — read-modify-write can still race. For compare-and-set you need lightweight transactions, `SERIAL` consistency, which is Paxos, four round trips, ~4x the latency. Use sparingly.
>
> Second, multi-DC changes everything. `QUORUM` across 2 DCs with RF=3 each is N=6, quorum=4, which probably means waiting for a WAN ack. Don't do that for user-facing paths — use `LOCAL_QUORUM`, which is quorum within the local DC. Each DC is internally strongly consistent; across DCs, eventually consistent. If the business needs globally synchronous, `EACH_QUORUM` on writes, but you pay WAN latency every write.
>
> For availability: `RF=3, QUORUM` tolerates 1 replica failure. `RF=5, QUORUM=3` tolerates 2 failures and gives better tail latency because the coordinator can pick the 3 fastest of 5. The cost is 5x storage instead of 3x.
>
> My defaults: `RF=3 per DC, LOCAL_QUORUM` for both reads and writes, LWT only where business invariants demand it."

## Important takeaways

- **R + W > N** is the strong-consistency formula. Memorize. Derive on the whiteboard.
- **QUORUM** = floor(N/2) + 1.
- **LOCAL_QUORUM** for multi-DC client-facing paths; `EACH_QUORUM` only when globally synchronous is required.
- **Quorum is NOT linearizability.** Use LWT (`SERIAL`) for CAS.
- **RF=3 + QUORUM tolerates 1 replica failure.** RF=5 + QUORUM tolerates 2.
- Cassandra resolves conflicts with **last-write-wins by timestamp** — clock skew matters; use coordinator-side timestamps or driver-side from a synced source.
- **Read repair fires asynchronously** during quorum reads when replicas diverge.
- **ALL is brittle**; **ONE is unsafe for OLTP**; **QUORUM is the default**.

## Variants

1. **Lightweight transactions (LWT)** — `IF NOT EXISTS`, `IF col = ?`. Paxos-backed, linearizable, 4x latency. Use for unique-username, idempotency keys, leader election.
2. **`ANY` consistency for writes** — write succeeds if hinted handoff accepts it (no replica acks needed). Maximum availability, eventual durability. Niche.
3. **Speculative retry** — coordinator pre-emptively queries an extra replica past `R` to mask tail latency. Configured per-table.
4. **Dynamic snitch** — coordinator picks the historically-fastest replicas for `R`-of-N reads. Reduces p99.
5. **`SERIAL` reads** — reads through Paxos; ensures you see all committed LWT writes. Rare.
6. **Comparison: DynamoDB eventually-consistent reads vs strongly-consistent reads** — same idea, different vocabulary; strongly-consistent reads cost 2x RCU.
7. **Quorum systems in Mongo** — `w: majority` is the analogous primitive; `readConcern: majority` plus `writeConcern: majority` gives the same R+W>N guarantee.

## Revision notes

> **cassandra quorum math — 60 second recap**
> - **Formula:** R + W > N ⇒ strong consistency (per-partition).
> - **QUORUM** = floor(N/2)+1. Pigeonhole guarantees overlap.
> - **Default:** RF=3, R=QUORUM, W=QUORUM. Tolerates 1 replica down.
> - **Multi-DC:** `LOCAL_QUORUM` for app paths; `EACH_QUORUM` only when global synchrony required.
> - **NOT linearizable** — for compare-and-set use LWT (`SERIAL`, Paxos, 4x latency).
> - **Conflicts** resolved by last-write-wins timestamp; clock sync matters.
> - **Read repair** fires async on quorum read divergence.
> - **Trap:** confusing `QUORUM` and `LOCAL_QUORUM` in multi-DC; using `ALL` in prod; treating quorum reads as CAS-safe.
