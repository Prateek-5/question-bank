# Quorum math: R + W > N and friends

## Source / Origin
- Gifford (1979) weighted voting; Amazon Dynamo (2007) tunable quorums.
- Production: Cassandra, DynamoDB, Riak, etcd, ZooKeeper, MongoDB.
- Concept reference: `backend-data-prep/distributed-systems/quorum.md`.

## Why this question matters in interviews
Quorum math is the simplest distributed-systems algebra. If you can recite "R + W > N implies strong consistency", explain why W > N/2 prevents split-brain, and reason about availability under failure for any (N, R, W) triple, you signal you understand the fundamental trade-off between consistency, latency, and availability.

## Concepts involved

### Syntax / mechanism to lock in

```
N = number of replicas per key.
W = number of replicas that must ack a write before client sees success.
R = number of replicas read before returning the answer.

Rules:
  Read-your-writes consistency:        R + W > N
  Tolerate F write failures:           W ≤ N - F   (and need N - F ≥ W to commit)
  Tolerate F read failures:            R ≤ N - F
  Single primary safety:               W > N/2     (no two writes can both quorum)

Common settings:
  N=3, W=2, R=2: strong (R+W=4 > 3), tolerate 1 failure.
  N=3, W=1, R=1: weak, fast, eventual.
  N=5, W=3, R=3: strong, tolerate 2 failures, higher latency.
  N=3, W=3, R=1: read-fast, write-slow, no write tolerance.
  N=3, W=1, R=3: write-fast, read-slow.
```

### Edge cases / interview traps

1. **R + W > N gives strong consistency only if the read sees the latest write's replicas.** Read repair / version vectors complete the story.
2. **W > N/2 is required to prevent split-brain in leader-based replication.** Two majorities cannot exist.
3. **Sloppy quorum** (Dynamo) allows W writes to any nodes, not preference list — gives availability but loses R+W>N guarantee.
4. **Quorum overlap calculation**: any read quorum and any write quorum share at least one replica iff R+W>N.
5. **In Cassandra, EACH_QUORUM applies per-DC**; LOCAL_QUORUM is per local DC.
6. **N is per-key**, not per-cluster. Cluster can have 100 nodes but each key replicates to N of them.
7. **Latency** = max of W (or R) slowest replicas; with W=2 of 3, you wait for the 2nd fastest, not the slowest.

## Mental Model

Quorum is the pigeonhole principle in disguise. If you put W pigeons into N holes for the write and R pigeons into N holes for the read, and W + R > N, then at least one hole has a pigeon from both — that hole is a replica that saw the write and is being read. So the read can see the write.

```
N=5 replicas:    [ r1 r2 r3 r4 r5 ]

Write quorum W=3:  pick any 3 → say { r1, r2, r3 }
Read quorum  R=3:  pick any 3 → say { r3, r4, r5 }

Overlap: { r3 }  ← guaranteed because 3 + 3 > 5.

ASCII overlap diagram (W=3, R=3, N=5):

  W set:  ■ ■ ■ □ □
  R set:  □ □ ■ ■ ■
          ─────────
          overlap at index 3 (or wherever the sets must share ≥1).
```

## Why interviewers care
- Tests algebraic reasoning about consistency models.
- Reveals knowledge of Dynamo, Cassandra, Riak tuning.
- Bridges to consensus quorums (Raft majority = (N/2)+1).

## Common beginner confusion
- "R + W > N gives serializability." It gives single-key read-after-write; not multi-key serializability.
- "Higher W = more durable." Higher W = more synchronously replicated; durability also depends on disk and replication factor.
- "Sloppy quorum is the same as regular." Sloppy includes any node, losing the R+W>N guarantee.
- "W=N gives perfect durability." Yes but you can't tolerate even 1 failure on write.

## Brute force approach

Read and write from all N replicas. Strongest consistency, worst availability and latency. Don't.

## Optimal approach

Pick (N, R, W) to match workload:

| Workload | (N, R, W) | Why |
|----------|-----------|-----|
| Read-heavy strong | (3, 2, 2) | strong; balanced |
| Read-heavy weak | (3, 1, 1) | fastest reads; eventual |
| Write-heavy strong | (3, 2, 2) | same; trade tail latency |
| Counter (durability critical) | (5, 3, 3) | tolerate 2 failures |
| Mostly write, eventual | (3, 1, 1) | LWW + read repair |
| Critical reads only | (3, 3, 1) | every read sees latest; writes risk |

## Solution

Three quick drills with answers:

### Drill 1
> N=3, W=2, R=1. Is read-after-write guaranteed?

Answer: No. R + W = 3, not > 3. A read can hit a replica that didn't see the write. Need R + W > N → R=2.

### Drill 2
> N=5. You must tolerate 2 simultaneous replica failures on both reads and writes, and maintain R+W>N. Pick (R, W).

Answer: R ≤ 3 and W ≤ 3 (tolerate 2 failures). R + W > 5 means R+W ≥ 6. Both ≤ 3 and sum ≥ 6 → R = W = 3. Verify: tolerate 2 down on write (W=3 of 5; 5-3=2). Same for reads.

### Drill 3
> Cassandra cluster across 3 DCs, RF=3 per DC. Client uses LOCAL_QUORUM. How many replicas must ack?

Answer: LOCAL_QUORUM = (3/2)+1 = 2 acks from local DC. Other DCs replicate async.

### Drill 4
> Why is W > N/2 important for leader election in Raft?

Answer: A majority overlap guarantee. Any two majorities must share a node. If a new leader is elected by W > N/2 votes, no parallel leader could have been elected by any other majority — they would conflict on the shared node. Prevents split-brain.

### Drill 5
> Dynamo with sloppy quorum: N=3, W=2. Two preference-list replicas are down; coordinator writes to two healthy nodes outside the preference list. Is R+W>N maintained for subsequent reads?

Answer: Strictly, no — your write quorum isn't from the preference list, so reads from the preference list may not see the write until hinted handoff completes. Sloppy quorum trades consistency for availability.

## Step-by-step dry run

N=3, W=2, R=2. Client writes K=v1, then reads.

```
Replicas: r1, r2, r3.

t=0   Write K=v1.
        Coordinator → r1, r2, r3 in parallel.
        r1 acks at t=5ms, r2 acks at t=8ms.
        W=2 reached at t=8ms. Client gets OK.
        r3 may ack later (or never if down) — async.

t=10  r3 receives the write, acks (or it's down → hint).

t=20  Client reads K with R=2.
        Coordinator → r1, r2, r3.
        Picks first 2 responses, say r1 (fast) and r3 (recovered).
        r1 has v1; r3 has v1 → return v1.

t=30  Suppose r3 was down throughout and hint not yet replayed.
        Client reads K with R=2.
        Coordinator → r1, r2, r3.
        r3 returns timeout. r1, r2 return v1.
        R=2 reached with r1, r2. Both v1. Return v1. Strong.

t=40  What if W only acked to r1, r2 (r3 down), and now r1 is down?
        Read R=2: r2 (v1) and r3 (no value, miss).
        Two responses but different — r2 has v1, r3 says "not found".
        Coordinator picks latest by timestamp → v1.
        Repair triggers on r3.
```

## How to think aloud in the interview

> "Quorum math says: read quorum R plus write quorum W greater than N guarantees overlap on at least one replica that has the latest write — that gives strong consistency for single-key read-after-write.
>
> Tunable per workload: (3,2,2) is the sweet spot — strong, tolerates 1 failure. (3,1,1) is fast and eventual. (5,3,3) is strong and tolerates 2 failures with higher tail latency.
>
> Subtleties: sloppy quorum breaks R+W>N for availability; W > N/2 is essential for leader election to prevent split-brain (any two majorities overlap); cross-DC requires LOCAL_QUORUM unless you can afford WAN latency on every write.
>
> The math is simple; the production tuning is the senior call. Defaults aren't always right — analyse read/write ratio, latency budget, and failure tolerance for each workload."

## Important takeaways
- R + W > N → read-your-writes strong consistency.
- W > N/2 → no split-brain in leader election.
- Sloppy quorum trades guarantee for availability.
- Latency = max of W (or R) fastest replicas, not slowest of all.
- Per-DC LOCAL_QUORUM in multi-DC deployments.
- N is per-key, not cluster size.

## Variants
1. **Weighted quorums** — different replicas count more.
2. **Flexible Paxos** — separate quorums for prepare and accept phases.
3. **Read-only quorum** — R=N, W=1 for write-fast, read-slow.
4. **Hierarchical quorums** — DC-level then node-level.
5. **Sloppy + hinted handoff** — Dynamo's availability hack.

## Revision notes

> **quorum-math — 60 second recap**
> - R + W > N → strong single-key read-after-write.
> - W > N/2 → no split-brain (Raft).
> - Pigeonhole: any two such quorums overlap on ≥ 1 replica.
> - (3,2,2) common balanced; (5,3,3) for higher tolerance.
> - Sloppy quorum sacrifices R+W>N for availability; relies on hinted handoff.
> - LOCAL_QUORUM ≠ EACH_QUORUM in multi-DC.
