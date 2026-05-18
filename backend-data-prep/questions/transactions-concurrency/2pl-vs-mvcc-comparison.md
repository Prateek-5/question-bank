# Compare 2PL and MVCC as concurrency-control strategies

## Source / Origin
- Classic database-internals interview question after MVCC walkthrough.
- Reference: Bernstein, Hadzilacos, Goodman "Concurrency Control and Recovery in Database Systems" — the textbook.
- Concept reference: `backend-data-prep/sql/07-isolation-levels.md`, `08-locks-concurrency.md`.

## Why this question matters in interviews
This is the *theoretical* question that signals you understand *why* modern OLTP databases work the way they do. 2PL (Two-Phase Locking) is the textbook serializability protocol; MVCC (Multi-Version Concurrency Control) is the throughput-friendly alternative. Every Postgres/InnoDB/Oracle engine is *some hybrid* — MVCC for reads, 2PL for writes. If you can articulate the trade-off and explain Postgres SSI as "MVCC + dependency tracking", you sound like you've read a database book, not a blog post.

## Concepts involved

### Syntax to lock in

```
2PL: every transaction has two phases
  Growing phase:  acquire locks (S or X); never release
  Shrinking phase: release locks; never acquire
  Strict 2PL: release all locks atomically at COMMIT/ROLLBACK

MVCC: every write creates a new version
  Reader uses a snapshot: visibility based on xmin/xmax
  Writer creates new tuple; updates old tuple's xmax
  Garbage collection reclaims unreachable versions
```

### Edge cases / interview traps

1. **2PL guarantees serializability** — provable theorem. MVCC alone gives *snapshot isolation*, which is weaker (allows write skew).
2. **MVCC engines still use 2PL for writes.** Postgres takes a row X lock for UPDATE; concurrent writers serialise via this lock. MVCC just removes the read-vs-write blocking.
3. **2PL deadlocks; MVCC livelocks under OCC.** Pure 2PL has deadlocks; MVCC + SSI has abort-and-retry storms under high contention.
4. **Strict 2PL ≠ Strong Strict 2PL.** Strict 2PL releases X locks at commit; SS2PL releases both S and X at commit. SS2PL is what most engines actually implement.
5. **Postgres SERIALIZABLE = MVCC + SSI** (Serializable Snapshot Isolation). Not 2PL. Tracks rw-dependencies, aborts on dangerous cycle.
6. **MySQL SERIALIZABLE = MVCC + S locks on every read.** Closer to 2PL but uses MVCC for the read view.
7. **Optimistic CC** is a third family: read without locks; validate at commit; abort if conflict. SSI is a flavor of optimistic CC.

## Mental Model

The **"library check-out vs photocopier"** model:

- **2PL = check-out**. Reader takes the book; while they hold it, nobody else writes. Writer takes the book; nobody else reads or writes. Single book = single point of contention. Correct, but readers and writers always block each other.

- **MVCC = photocopier**. Reader takes a photocopy (snapshot) and walks away. Writer continues working on the original. The photocopy can be older than the current original; that's fine. Multiple readers + one writer never block each other.

```
   2PL:                              MVCC:
   ──────                            ──────
   Readers block writers             Readers never block writers
   Writers block readers             Writers never block readers (for reads)
   Writers block writers             Writers still block other writers
   Serializable by construction      Snapshot isolation by default
   Deadlocks possible                Deadlocks rare on reads; possible on writes
   Memory: lock table                Memory: version storage + GC

   Operational fingerprint:
     2PL OLTP: lock-wait dashboards, deadlock retries, high p99 under contention
     MVCC OLTP: bloat dashboards, vacuum tuning, snapshot-age tracking
```

## Why interviewers care

- Tests **theoretical foundation**: do you know the textbook proof of serializability under 2PL?
- Tests **engineering insight**: do you understand why MVCC won the OLTP wars?
- Probes **Postgres SSI**: bridges MVCC + serializability — the modern synthesis.

## Common beginner confusion

- "MVCC has no locks." MVCC removes locks from the *read path*. Writes still take X locks.
- "2PL means two locks per transaction." 2PL means two *phases*: growing and shrinking. The number of locks varies.
- "Strict 2PL is what MySQL does." MySQL InnoDB does strict 2PL for write locks but uses MVCC for reads. Hybrid.
- "Serializable = 2PL." Not necessarily. Postgres SERIALIZABLE uses SSI (optimistic + dependency tracking), not 2PL.

## Brute force approach

Pure 2PL everywhere: every read takes S lock, every write takes X lock, all released at commit. Provably correct; throughput collapses under read-heavy workload because readers and writers block each other. This is what 1980s mainframe databases did.

## Optimal approach

Modern hybrid:

- **Reads** use MVCC snapshot — never block.
- **Writes** use SS2PL — X locks on touched rows held until commit. Concurrent writers serialise.
- **Constraint checks** (FK, UNIQUE) use predicate locking or constraint exclusion at commit.
- **Serializable level** uses MVCC + SSI (Postgres) or MVCC + per-row S locks (MySQL).

## Solution

```
============================================================
2PL — the textbook protocol
============================================================

T1: BEGIN
T1: lock(X, A)       ── growing phase
T1: read A
T1: lock(X, B)       ── still growing
T1: write A, B
T1: COMMIT           ── strict 2PL: release all locks here
                       (shrinking phase = one atomic step at COMMIT)

Theorem (textbook):
  Any schedule produced by strict 2PL is conflict-serializable.
  Proof: once a transaction releases a lock, no other transaction
  can acquire-then-conflict with it; the precedence graph is acyclic.

Deadlock risk:
  T1 locks A, T2 locks B
  T1 wants B, T2 wants A → wait-for cycle → deadlock

============================================================
MVCC — the modern OLTP default
============================================================

T1: BEGIN (snapshot S1 = {committed tx IDs at this point})
T1: read A (sees A.v_n where v_n is visible in S1)  -- no lock
T2: BEGIN (snapshot S2)
T2: update A → creates A.v_(n+1); A.v_n.xmax = T2's XID
                                  -- takes X lock on A
T1: read A again → still sees A.v_n (snapshot held)
T2: COMMIT → A.v_(n+1) now visible to new snapshots
T1: COMMIT → done; A.v_n now reclaimable when no snapshot < S1

Concurrent updaters serialize:
T1: update A → X lock on A
T2: update A → waits on T1's X lock
T1: COMMIT → T2 acquires lock; at RC re-reads latest row;
              at RR aborts with 40001 if A was modified

============================================================
Postgres SSI — the synthesis
============================================================

BEGIN ISOLATION LEVEL SERIALIZABLE;
  SELECT count(*) FROM oncall WHERE on_duty;  -- predicate read; SIREAD lock tracked
  UPDATE oncall SET on_duty=false WHERE name='Alice';
COMMIT;
-- Engine tracks rw-dependencies:
--   "this tx read predicate P; that tx wrote into P"
-- If the resulting dependency graph contains a dangerous structure,
-- one tx is aborted with 40001 at commit time.
```

## Step-by-step dry run

Same workload, three protocols, three outcomes:

Workload: T1 reads x, T2 writes x.

```
2PL trace:
  T1: lock(S, x), read x = 100
  T2: lock(X, x) → BLOCKED on T1's S lock
  T1: COMMIT → release S lock
  T2: acquire X, write x = 80, COMMIT

Latency: T2 waits for T1.
Correctness: serializable (T1 before T2).
```

```
MVCC at RC trace:
  T1: BEGIN with snapshot S1
  T1: read x.v1 = 100
  T2: BEGIN with snapshot S2 (after T1 started or before; doesn't matter for writes)
  T2: write x.v2 = 80; X lock on x; T1 doesn't block
  T2: COMMIT → x.v2 visible to new snapshots
  T1: COMMIT → done

Latency: zero blocking for T1.
Correctness: snapshot isolation. T1 sees x=100 throughout; T2 sees x=80 after writing.
Anomaly: at RC, T1's second read would see 80 (snapshot per-statement). At RR, T1 keeps seeing 100 until commit.
```

```
Postgres SSI trace (SERIALIZABLE):
  T1: BEGIN SER with snapshot S1; SIREAD lock on the row
  T1: read x = 100
  T2: BEGIN SER
  T2: write x = 80; engine tracks rw-edge T1 → T2
  T2: COMMIT
  T1: COMMIT → no dangerous cycle (T1 only read; no other tx read T1's write)
              → T1 commits cleanly

If T1 had also written something T2 read: cycle → one aborts with 40001.
```

Wait-for graph comparison:

```
2PL (potential deadlock):                    MVCC (no read-wait edges):
                                              ─────────────────────────
  T1 → T2 (T1 wants X held by T2)             T1: no waits on T2 for reads
  T2 → T1 (T2 wants X held by T1)             T2: waits only for X lock conflicts
  cycle → deadlock                            cycle only on multi-row writer paths
```

## How to think aloud in the interview

> "2PL: every transaction acquires locks in a growing phase, releases in a shrinking phase. Strict 2PL releases all locks at COMMIT. Provably serializable. The cost: readers block writers and vice versa, killing throughput on read-heavy OLTP.
>
> MVCC: every write creates a new tuple version tagged with xmin/xmax. Readers consume the version visible to their snapshot; never block. Writers still acquire X locks against other writers — that part is still 2PL. Snapshot isolation, not full serializability.
>
> Postgres: MVCC for reads, strict-2PL for writes, plus SSI (Serializable Snapshot Isolation) at the SERIALIZABLE level — tracks rw-dependencies between concurrent transactions and aborts on a dangerous cycle. Cheap when conflicts are rare; aborts (40001) under high conflict.
>
> MySQL InnoDB: same MVCC + 2PL hybrid; SERIALIZABLE adds S locks on every read (closer to classical 2PL). More blocking, fewer aborts.
>
> Operational fingerprint: 2PL pain = lock-wait p99, deadlocks. MVCC pain = bloat, vacuum, snapshot age. Different dashboards entirely."

## Important takeaways

- 2PL = growing + shrinking phases; strict 2PL releases all locks at commit; guarantees serializability.
- MVCC = versioned tuples with snapshot reads; readers don't block writers.
- Modern engines = MVCC reads + 2PL writes (hybrid).
- Postgres SERIALIZABLE = MVCC + SSI (dependency tracking, abort on cycle).
- MySQL SERIALIZABLE = MVCC + S locks on reads (more blocking, fewer aborts).
- 2PL pain = lock waits and deadlocks. MVCC pain = bloat and snapshot age.
- Pure 2PL is rare in 2025; most engines hybrid.

## Variants

1. **Distributed 2PL** (textbook): cross-node lock manager. Used by older distributed DBs; replaced by Paxos-based protocols in Spanner.
2. **OCC (Optimistic CC)**: read without locks, validate at commit. SSI is an instance.
3. **Timestamp ordering**: each tx gets a TS; reads/writes ordered by TS. Used by Spanner with TrueTime, by some research DBs.
4. **Pessimistic deadlock prevention**: wait-die (younger aborts) / wound-wait (older preempts). Used in distributed DBs.
5. **Hekaton / SQL Server in-memory**: MVCC + OCC + lock-free; no locks at all on the read or write path until commit.

## Revision notes

> **2pl-vs-mvcc — 60 second recap**
> - 2PL: growing + shrinking phases; strict 2PL releases at commit; serializable by construction.
> - MVCC: versioned tuples, snapshot reads, no read-write blocking.
> - Modern engines: MVCC reads + 2PL writes hybrid.
> - Postgres SER = MVCC + SSI (dep tracking, abort on cycle).
> - MySQL SER = MVCC + S locks on reads.
> - 2PL: lock-waits, deadlocks. MVCC: bloat, vacuum, snapshot age.
> - MVCC alone gives snapshot isolation; SSI adds serializability.
> - Pure 2PL = 1980s; pure MVCC = 90s; SSI = 2008+ Postgres innovation.
