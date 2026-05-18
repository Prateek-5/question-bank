# Linearizability vs serializability: the two strong-consistency models

## Source / Origin
- Herlihy & Wing (1990) Linearizability; Papadimitriou (1979) Serializability.
- Production: Spanner (both), Postgres (Serializable), etcd/ZooKeeper (Linearizable).
- Concept reference: `backend-data-prep/distributed-systems/consistency.md`.

## Why this question matters in interviews
This is the question that separates "knows the buzzwords" from "understands what guarantees actually mean". If you can explain that linearizability is about single-object recency and serializability is about multi-object correctness, articulate that you can have one without the other, and name systems that provide each, you signal senior-level grasp of consistency.

## Concepts involved

### Syntax / mechanism to lock in

**Linearizability** (single-object, real-time):
- Each operation appears to take effect at a single point between its invocation and response.
- Once a write completes, any subsequent read (in real time) must see it or later.
- Single-object atomic registers.

**Serializability** (multi-object, transactional):
- Concurrent transactions appear equivalent to *some* serial order.
- No real-time constraint: equivalent order need not match wall-clock order.
- Multi-object, multi-statement.

**Strict Serializability** = Linearizability + Serializability:
- Multi-object transactions in a real-time order.
- Spanner, Calvin, CockroachDB target this.

```
              | single object | multiple objects |
--------------|---------------|------------------|
real-time     | Linearizable  | Strict Serial.   |
no real-time  |   Sequential  | Serializable     |
```

### Edge cases / interview traps

1. **Postgres SERIALIZABLE is not linearizable.** It allows old reads from a snapshot; great for correctness, weak on recency.
2. **etcd / ZooKeeper are linearizable but NOT serializable** in a transactional sense — they offer single-key linearizable ops.
3. **Snapshot isolation is neither linearizable nor serializable.** Allows write skew.
4. **Linearizability is a per-object property.** Two linearizable objects together are not necessarily linearizable as a pair.
5. **You can have serializability without linearizability** — Postgres SSI.
6. **You can have linearizability without serializability** — etcd kv.
7. **Spanner uses TrueTime** to achieve strict serializability across the globe.

## Mental Model

Linearizability = "if I told you yesterday, you must know today". It's about the *real-time order* of operations on a single object.

Serializability = "the result is as if these transactions ran one after another in some order". It's about the *equivalence class* of executions for multi-object transactions, with no real-time constraint.

```
Object register R.

Linearizable timeline:
   Client A: |--write R=5--|
   Client B:                 |--read R--|  must return 5 (real-time after write)

Serializable timeline (transactions):
   T1 reads X, writes Y    T2 reads Y, writes X
   Both commit "in parallel". Result equivalent to T1→T2 OR T2→T1.
   No real-time constraint on which serial order.

Strict serializable: result equivalent to SOME serial order that
   respects real-time happen-before edges.
```

## Why interviewers care
- Tests precise terminology in consistency.
- Bridges to Spanner, CockroachDB, etcd, Postgres SSI internals.
- Reveals whether you can reason about cross-object invariants and recency separately.

## Common beginner confusion
- "Linearizable = SQL SERIALIZABLE." No — different axes (recency vs equivalence).
- "Linearizable is the strongest possible." Strict serializable is stronger (multi-object + recency).
- "Serializable means single-threaded." It means *equivalent to* a serial schedule.
- "Postgres SSI = linearizable." No — it's serializable, not linearizable.

## Brute force approach

Single-node single-threaded execution. Trivially both linearizable and serializable. Doesn't scale.

## Optimal approach

Pick consistency by need:
- Single-key strong recency: use linearizable kv (etcd, ZooKeeper, Raft-replicated state machine).
- Multi-key cross-object invariants: use SERIALIZABLE transactions (Postgres SSI, FoundationDB, Spanner).
- Both global recency and multi-key transactions: Spanner / CockroachDB / FoundationDB.
- Local snapshot reads (no recency need): RR/snapshot isolation; cheaper.

## Solution

### Showing linearizable but not serializable

```python
# etcd: linearizable single-key
client.put("/lock", "client_A")           # write returns at t=10
val = client.get("/lock", consistency="linearizable")
# Any later get is guaranteed to return "client_A" or newer.

# But:
client.put("/account_X", 100)
client.put("/account_Y", 200)
# These two are individually linearizable, but no transactional
# guarantee that X+Y=300 across reads. etcd doesn't do that.
```

### Showing serializable but not linearizable (Postgres SSI)

```sql
-- T1: long read transaction, RR snapshot at t=10
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT balance FROM accounts WHERE id = 1;  -- sees t=10 snapshot
-- (T2 commits a new write at t=20 to account 1)
SELECT balance FROM accounts WHERE id = 1;  -- still sees t=10 snapshot!
COMMIT;
-- The result is equivalent to a serial schedule where T1 ran before T2.
-- But the real-time order says T2's write happened first.
-- Hence: serializable YES, linearizable NO.
```

### Strict serializability (Spanner)

```sql
-- Spanner ensures every committed transaction has a TrueTime timestamp
-- and read transactions see all writes with earlier timestamps.
SELECT balance FROM accounts WHERE id = 1;
-- Returns the latest committed value, with multi-object transactional
-- correctness and global real-time ordering.
```

## Step-by-step dry run

Same key X. Two clients:

```
Linearizable scenario:

real time →

ClientA:  |--write X=1 ack at t=5--|
ClientB:                              |--read X start t=10--|--get value--|
                                                              must be 1 (or later)

Conceptual: the write took effect at a single instant in [start, ack].
Any read whose start > ack must see >= that write.

----------------------------------------------------------------------
Snapshot isolation (Postgres RR) scenario — NOT linearizable:

T1 BEGIN RR at t=10; snapshot frozen.
T2: write X=1 at t=15; commit at t=16.
T1: SELECT X at t=20 → returns the OLD value (snapshot at t=10).

T1's read at real time t=20 saw a value older than the write that
committed at t=16. Not linearizable.

But the execution IS equivalent to a serial schedule "T1 before T2".
Hence serializable (or RR), not linearizable.

----------------------------------------------------------------------
Strict serializable scenario (Spanner-like):

T2: BEGIN; write X=1; COMMIT with TS=15.
T1: BEGIN; read X at TS=20 → returns 1.

Multi-object cross-account transactions also see this real-time order.
That's strict serializability.
```

## How to think aloud in the interview

> "Linearizability is a single-object, real-time guarantee: a write is visible to all subsequent reads, in real time, as if the operation took effect at a single instant. Serializability is a multi-object, transactional guarantee: concurrent transactions are equivalent to *some* serial order — no real-time constraint.
>
> They're orthogonal axes. Postgres SSI gives serializable but not linearizable — a long transaction's snapshot can return stale values relative to wall time. etcd gives linearizable single-key operations but no multi-key transactions, so it's not serializable in the SQL sense.
>
> Strict serializability is the conjunction: multi-object transactional correctness *and* real-time order. Spanner and CockroachDB target this using HLC or TrueTime.
>
> The interview trap: 'I want strong consistency' is ambiguous. Pin them down — recency? cross-object invariants? both? — and pick the right system."

## Important takeaways
- Linearizable: single-object, real-time.
- Serializable: multi-object, no real-time required.
- Strict serializable: both.
- Postgres SSI = serializable, not linearizable.
- etcd / ZooKeeper = linearizable, not transactional-serializable.
- Spanner / CockroachDB = strict serializable.

## Variants
1. **Sequential consistency** — same order seen by all, but not necessarily real-time.
2. **Causal consistency** — happens-before preserved; weaker than sequential.
3. **Read committed, RR, snapshot isolation** — non-serializable levels.
4. **Eventual consistency** — convergence, no order guarantee.
5. **Strong eventual consistency** (CRDTs) — convergence to same state once all updates seen.

## Revision notes

> **linearizability-vs-serializability — 60 second recap**
> - Linearizable: single-object, real-time write visible to subsequent reads.
> - Serializable: multi-object, equivalent to some serial order; no real-time.
> - Strict serializable = both.
> - Postgres SSI: serializable, not linearizable.
> - etcd/ZooKeeper: linearizable, not multi-object serializable.
> - Spanner/Cockroach: strict serializable via TrueTime/HLC.
