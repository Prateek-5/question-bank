# Locks & Concurrency Control

## Intuition first — what a lock really is

Forget the database for a moment.

**The library reading-room analogy.** A university library has a reference book that cannot leave the building. There's a sign-out sheet at the front desk. Multiple students can *read* the book together (huddled around a table) — that's a **shared lock**. But if someone wants to *annotate* the book, they must take it to a private desk, alone — that's an **exclusive lock**. Other students who want to read must wait until the annotator returns it. Other students who want to *also* annotate definitely have to wait.

That is exactly how database locks work. Shared locks are compatible with other shared locks (many readers). Exclusive locks are incompatible with everything (one writer, alone).

**Granularity = scope of the sign-out.** You can sign out:
- The whole library (table lock) — fast to acquire, kills concurrency.
- One shelf (page lock) — moderate.
- One book (row lock) — the typical case; needs more bookkeeping but allows tons of parallel work.
- "Anyone wanting to add a book to history section, please wait" (predicate / gap lock) — protects future inserts.

**Deadlock as the "I'll give you A when you give me B" loop.** Two librarians: one has Encyclopaedia Britannica volume A and wants volume B; the other has volume B and wants volume A. Neither will hand over their book until they receive the other. Both wait forever. The library manager notices and forces one to give up. That's the database's deadlock detector. The lesson is operational: if everyone *always* picks up volume A before volume B, this loop is impossible. **Consistent lock ordering eliminates deadlocks.**

### Progressive build for locks

1. **One transaction, lock something.** No conflicts. Trivial.
2. **Two transactions, same row, both want to read.** Both get shared locks. No blocking.
3. **Two transactions, same row, one reads / one writes.** Writer needs exclusive; either waits depending on order.
4. **Two transactions, same row, both write.** Second one blocks until first commits.
5. **Two transactions, different rows, but each holds what the other wants.** Deadlock. DB picks a victim.
6. **N transactions, hot row, all queuing.** Lock contention; throughput falls; latency goes up. Solution: re-design (counters, queues, optimistic concurrency).
7. **DDL during business hours.** `ALTER TABLE` takes the whole-library lock. Everyone waits. Production incident.

---

## Why this matters in backend interviews

- **Real production debugging** lives here — deadlocks, lock waits, replica stalls, queue starvation.
- **Senior signal**: candidates who can name the lock modes, draw a deadlock graph, and pick the right resolution strategy stand out.
- **System design**: every concurrent-write feature (booking, payments, counters, queues) needs a concurrency strategy.
- **Machine coding**: you'll be asked to make a counter or a queue thread-safe at the DB level.

---

## Why interviewers care

- They want to see you **reason from primitives upward**: from "what is a lock" to "how do you build a job queue without contention" without skipping steps.
- They want to **catch you on the implementation detail** that separates senior from mid. ("Why does `SELECT ... FOR UPDATE SKIP LOCKED` matter for queues?" "What's a gap lock and when can it surprise you?")
- They want to test your **production literacy** — you've debugged a deadlock at 3 AM, you know what `pg_blocking_pids` is for, you've seen an ALTER TABLE freeze a 500M row table.
- They want to evaluate your **tradeoff vocabulary** — when is optimistic better than pessimistic? When do you reach for an advisory lock? When does the DB lock itself become the bottleneck?

## Common beginner confusion

- **"MVCC = no locks at all."** Wrong. MVCC eliminates locks on the read path against writers and vice versa. Writers still take exclusive row locks against each other. Constraints, indexes, and DDL still take various locks.
- **"`SELECT FOR UPDATE` in autocommit is harmless / works."** It's *worse* than useless. In autocommit, the lock is released the moment the SELECT statement finishes. By the time you run the follow-up UPDATE in a *new* implicit transaction, you have no lock. Always wrap in an explicit `BEGIN; ... COMMIT;` block.
- **"My ORM does transactions so concurrency bugs don't happen."** ORMs hide *SQL syntax*, not *concurrency semantics*. A naive `user = User.find(1); user.balance -= 10; user.save()` over RC is a lost-update race in any language, any ORM.
- **"Deadlocks mean my code is broken."** Not necessarily — they're a normal outcome of concurrent updates over inconsistent lock order. The DB handles them by aborting one transaction; your app must retry. The bug only exists if you don't retry or if your lock ordering is fixable and you ignore it.
- **"All `FOR UPDATE` calls are the same."** No. Postgres has four flavors: FOR UPDATE, FOR NO KEY UPDATE, FOR SHARE, FOR KEY SHARE — chosen for different FK / locking semantics. Picking the wrong one can over-lock and cause needless contention.
- **"Advisory locks are slow."** They're not. They're application-defined, in-memory locks keyed by an integer. Sub-millisecond. Cheaper than building a separate locking service like Redis Redlock for many use cases.

---

## First principles — what locking is solving

A lock is a protocol primitive that turns a *concurrent* execution into something *equivalent* to a *serial* execution on some shared resource. Locks don't make the system fast; they make it correct. The art is to use as little locking as possible while preserving correctness.

**Two-phase locking (2PL)** is the canonical algorithm:
- *Growing phase*: acquire locks; never release.
- *Shrinking phase*: release locks; never acquire.
- *Strict 2PL*: all locks held until COMMIT/ROLLBACK — the only release point.

**Theorem (textbook):** any schedule produced by strict 2PL is conflict-serializable. That's why every "real" pessimistic concurrency control engine uses strict 2PL for writes.

**Why locks are not enough on their own.** Two issues plague pure 2PL:
1. *Reader-writer contention*: readers block writers, writers block readers. Fatal for OLTP. → solved by MVCC.
2. *Deadlocks*: 2PL doesn't prevent them; you can hold A, want B, while someone else holds B, wants A. → solved by deadlock detection (cycle detection on the wait-for graph) or prevention (timeouts, wound-wait, wait-die, consistent ordering).

**Optimistic concurrency control (OCC)** flips the model: don't lock during read/compute. At commit, check whether the data you read was changed. If yes, abort. Costs: more aborts under contention; benefits: zero blocking, no deadlocks. Used by MVCC engines for serializable mode (Postgres SSI), by version-column patterns, and by HTTP `If-Match: <etag>`.

The decision tree:
- **Conflict probability low** → OCC (version column, SSI).
- **Conflict probability high, transactions short** → pessimistic 2PL (`FOR UPDATE`).
- **Read-mostly workload** → MVCC reads + occasional pessimistic write locks.
- **Hot row** (counters) → re-design (per-shard counter, eventual aggregation).

---

## Core concepts

### Lock granularity

#### Mental model — the zoom dial

Imagine a zoom dial on a microscope. At the lowest zoom you see the whole table; at the highest you see one row. Where you point the lock determines who can simultaneously work next to you.

- **Wide zoom (table lock)**: cheap to track (one entry in the lock manager), but everyone else is frozen out. Great for DDL where you *need* exclusivity.
- **Medium zoom (page lock)**: locks a few KB of rows at once. Some engines (SQL Server) use this; Postgres and InnoDB skip it.
- **High zoom (row lock)**: many small locks in the lock table; high memory cost but maximum concurrency.
- **Predicate / gap**: not a physical lock on rows — a *logical* lock on "rows that don't exist yet but match this condition". The reason InnoDB can prevent phantoms while Postgres can't (without SSI).
- **Advisory**: a lock on a number you made up. The DB doesn't know what it means; only your code does.

```
zoom out  [TABLE]      one entry, everyone waits
          [PAGE]       a few entries, a few rows blocked
          [ROW]        N entries, only the touched rows blocked
zoom in   [PREDICATE]  logical — protects future inserts in a range
```

**Common confusion.** "Smaller lock granularity = always better." False. Row locks consume memory and CPU; with millions of locks, the lock table itself becomes a bottleneck. That's why SQL Server *escalates* row → table when count exceeds a threshold.

| Granularity | Coverage | Use |
|---|---|---|
| **Row** | One row | Most common; default for `UPDATE`/`DELETE` |
| **Page** | A disk page | Some engines; performance-tier optimization |
| **Table** | Whole table | DDL operations (ALTER), some `LOCK TABLE` calls |
| **Predicate / gap** | A range of keys | InnoDB next-key locks; Postgres SSI SIREAD locks |
| **Advisory** | Application-defined logical key | Cross-row coordination (Postgres `pg_advisory_lock`) |

### Lock modes

#### Mental model — readers vs writers

Two questions every lock manager asks: "Are you reading or writing?" and "Are you done yet?" Shared (S) means "I'm just reading — others can read too." Exclusive (X) means "I'm changing this — nobody else, reader or writer, gets close." The Update (U) mode is the half-step: "I'm reading, but I plan to upgrade to X soon." It exists to prevent a specific deadlock: two transactions both holding S, both wanting to upgrade to X — neither can, because each blocks the other. U is incompatible with U, so only one upgrade-intent gets through.

Intention locks (IS/IX) live one level up. They're a *signal* on the table that says "someone holds row locks below." Without them, an `ALTER TABLE` would have to scan every row to check for conflicts.

```
Lock compatibility matrix (extended)
        |  IS  |  IX  |  S   |  SIX |  X
   -----+------+------+------+------+------
    IS  |  Y   |  Y   |  Y   |  Y   |  N
    IX  |  Y   |  Y   |  N   |  N   |  N
    S   |  Y   |  N   |  Y   |  N   |  N
    SIX |  Y   |  N   |  N   |  N   |  N
    X   |  N   |  N   |  N   |  N   |  N
```

**Common confusion.** "FOR SHARE means reads will never block." Wrong — FOR SHARE blocks any *writer* on that row, and is itself blocked by any pre-existing X lock. It's a *pessimistic* read.

#### Walkthrough — what happens when T1 holds X on row 42

1. T2 issues `SELECT * FROM accounts WHERE id=42` — plain SELECT under MVCC. Reads the *old snapshot*; never blocks.
2. T2 issues `SELECT * FROM accounts WHERE id=42 FOR SHARE`. Now T2 *wants* an S lock. S conflicts with T1's X. T2 blocks.
3. T2 issues `UPDATE accounts SET balance=… WHERE id=42`. T2 needs X. Also blocks.
4. T1 commits. T2 wakes up — but under READ COMMITTED, Postgres now re-reads row 42 to see if T2's WHERE clause still matches (it might not!). This is the "EvalPlanQual" dance.

| Mode | Conflicts with |
|---|---|
| **Shared (S)** / read | Exclusive |
| **Exclusive (X)** / write | Shared, Exclusive |
| **Update (U)** | Exclusive; converts to X (used internally) |
| **Intention Shared / Intention Exclusive** (IS/IX) | Table-level signals for row locks |

Compatibility matrix (simplified, InnoDB):

|   | S | X |
|---|---|---|
| S | ✓ | ✗ |
| X | ✗ | ✗ |

### Postgres lock modes (row level)

#### Mental model — strength gradient

Think of the four flavors as a strength dial. KEY SHARE is the lightest touch ("don't change my identity"); UPDATE is the strongest ("don't touch me at all"). The middle two exist almost entirely to make foreign-key checks not block ordinary updates — a design lesson in caring about *which fields* a lock protects.

```
   weaker -------------------------------------------> stronger
   KEY SHARE  <  SHARE  <  NO KEY UPDATE  <  UPDATE
   FK reads      reads     non-key writes    everything
```

**Common confusion.** "FOR NO KEY UPDATE is a weaker FOR UPDATE I should use by default." No — Postgres picks the *right* one for you on plain `UPDATE`s. The `FOR NO KEY UPDATE` keyword is mostly internal; the four flavors matter when you're *explicitly* taking row locks via SELECT.

- `FOR UPDATE` — exclusive; blocks any other FOR UPDATE / FOR SHARE / update on same row
- `FOR NO KEY UPDATE` — exclusive but allows FKs from other tables to read
- `FOR SHARE` — shared lock
- `FOR KEY SHARE` — weakest; allows non-FK updates

```sql
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;
```

### Postgres table locks (8 modes)

#### Mental model — operational impact

The 8 table lock modes form a ladder from "barely there" to "freezes the whole table." For interviews and ops, you mostly need to know **which DDL takes ACCESS EXCLUSIVE** (because that's what causes 3 AM incidents) and **which operations coexist** (because that determines whether your VACUUM blocks readers).

```
ACCESS SHARE         |  SELECT
ROW SHARE            |  SELECT FOR UPDATE / SHARE
ROW EXCLUSIVE        |  INSERT / UPDATE / DELETE
SHARE UPDATE EXCL    |  VACUUM (non-FULL), ANALYZE, CREATE INDEX CONCURRENTLY
SHARE                |  CREATE INDEX (non-concurrent)
SHARE ROW EXCLUSIVE  |  CREATE TRIGGER, some ALTER variants
EXCLUSIVE            |  REFRESH MATVIEW CONCURRENTLY
ACCESS EXCLUSIVE     |  ALTER TABLE, DROP, TRUNCATE, REINDEX, VACUUM FULL
                        ^^^^^ this one blocks even plain SELECTs ^^^^^
```

**Common confusion.** "VACUUM blocks everything." Almost the opposite — plain `VACUUM` takes SHARE UPDATE EXCLUSIVE, which is *compatible* with reads and writes. `VACUUM FULL` is the one that takes ACCESS EXCLUSIVE and locks everyone out.

ACCESS SHARE < ROW SHARE < ROW EXCLUSIVE < SHARE UPDATE EXCLUSIVE < SHARE < SHARE ROW EXCLUSIVE < EXCLUSIVE < ACCESS EXCLUSIVE.

- SELECT acquires ACCESS SHARE
- INSERT/UPDATE/DELETE acquires ROW EXCLUSIVE
- `CREATE INDEX` (not concurrent) acquires SHARE → blocks writes
- `ALTER TABLE` acquires ACCESS EXCLUSIVE → blocks everything
- `VACUUM` acquires SHARE UPDATE EXCLUSIVE → coexists with most reads/writes

Knowing which DDL blocks production traffic is a **senior signal**.

### InnoDB lock modes

#### Mental model — locks live on the index, not on the row

This is the single most counter-intuitive InnoDB fact. When you `UPDATE … WHERE name='Alice'` and there's no index on `name`, InnoDB locks *every row scanned* — including ones that don't match — because it can only lock index records. With an index, only matching index entries are locked.

Then the gap lock concept: locks aren't only on existing entries, but on the *spaces between them*. If you `SELECT … WHERE id BETWEEN 10 AND 20 FOR UPDATE` and rows 10, 15, 20 exist, InnoDB also locks the gaps (10,15), (15,20), and the next gap after 20 — so a concurrent INSERT of id=18 will block. That's how it prevents phantoms at REPEATABLE READ.

```
   index keys:    [10]   [15]   [20]   [...]
                   ^      ^      ^
   record locks   ###    ###    ###
   gap locks       <======><=====>(<====>
                   gap     gap    gap before next key
   next-key       [=== record + gap before it ===]
```

**Common confusion.** "If I use REPEATABLE READ in MySQL my INSERTs won't be blocked by reads." False — gap locks on a read range *will* block your INSERT. This is the most common source of surprising MySQL deadlocks.

#### Walkthrough — gap-lock deadlock

1. T1: `SELECT * FROM t WHERE id BETWEEN 10 AND 20 FOR UPDATE;` — locks records 10, 15, 20 *and the gaps between*.
2. T2: `INSERT INTO t (id) VALUES (12);` — needs an insert-intention lock in the gap (10,15). Blocks behind T1's gap lock.
3. T1 doesn't commit yet, tries `INSERT INTO t (id) VALUES (13);` — also wants gap (10,15), but now T2's insert-intention is queued there. Deadlock detected; one is killed.

- Record lock: on an index record
- Gap lock: on a gap between index records (prevents INSERTs into the gap)
- Next-key lock: record + gap (default in REPEATABLE READ to prevent phantoms)
- Insert intention lock: brief lock during INSERT

### Deadlocks

#### Mental model — the wait-for graph

The DB internally maintains a directed graph: edge from T1 → T2 means "T1 is waiting on a lock held by T2." A deadlock is a *cycle* in this graph. Detecting deadlocks = detecting cycles, an O(V+E) DFS run periodically (Postgres) or on each wait (MySQL).

```
   Two-transaction deadlock:

      T1 ────waits for────▶ T2
      ▲                      │
      └──────waits for──────┘

   Three-transaction deadlock:

      T1 ───▶ T2 ───▶ T3
       ▲              │
       └──────────────┘
```

When a cycle is found, the engine picks a **victim** (usually the youngest / least work done / explicit DEADLOCK_PRIORITY) and aborts it with a deadlock error. The remaining transactions can then proceed.

**Common confusion.** "Deadlock = bug." Not necessarily — deadlocks are an *outcome* of the lock-acquisition pattern. The bug is one of (a) inconsistent lock ordering, (b) no application retry, or (c) transactions that hold too many locks for too long. A retry loop turns "deadlock" into "transient blip."

#### Walkthrough — the classic 2-transaction deadlock

Two transactions waiting on each other's locks. The DB detects this (Postgres: deadlock_timeout, default 1s; MySQL: deadlock detector) and aborts one with a deadlock error. The other proceeds.

Classic:
```
T1: UPDATE A; -- locks A
T2: UPDATE B; -- locks B
T1: UPDATE B; -- waits on T2
T2: UPDATE A; -- waits on T1 → DEADLOCK
```

Step-by-step:
1. T1 acquires X on row A. Wait-for graph: empty.
2. T2 acquires X on row B. Wait-for graph: empty.
3. T1 requests X on row B → blocks. Graph: T1 → T2.
4. T2 requests X on row A → blocks. Graph: T1 → T2 → T1. Cycle.
5. Detector wakes (after `deadlock_timeout`, default 1s in Postgres; immediate in MySQL). Picks T2 as victim, raises `40P01` (Postgres) / `1213` (MySQL). T1 proceeds.

**Prevention:**
- Always acquire locks in the same order (e.g., by ID)
- Keep transactions short
- Use `SELECT FOR UPDATE` early to surface conflicts fast
- Application-level retry on deadlock error

### Lock waits (not deadlocks)

#### Mental model — the silent killer

Deadlocks are loud — they show up in logs, they fire alarms. Lock *waits* are silent: your API just gets slower as a single long transaction blocks everyone behind it. The wait-for graph has *no cycle*, just a long chain: T1 → T2 → T3 → … → T_N. Throughput collapses but nothing errors out. This is the more common production pathology.

**Common confusion.** "If there's no deadlock error my locking is fine." No — chronic lock waits show up as p99 latency spikes, not errors. Monitor `pg_locks` joined with `pg_stat_activity` to catch them.

A transaction is just waiting because another holds the lock. Usually not detected as deadlock. Symptoms: slow APIs, queue backup. Find via `pg_stat_activity` / `SHOW ENGINE INNODB STATUS`.

### `SELECT FOR UPDATE SKIP LOCKED`

#### Mental model — the deli-counter ticket system

Imagine 10 workers all asking the deli counter "what's next?". With plain `FOR UPDATE`, only worker 1 gets served; workers 2-10 stand in line for the *same* sandwich. With `SKIP LOCKED`, each worker is told "Anything you can grab? Take it" — worker 1 takes sandwich A, worker 2 sees A is taken and grabs B, etc. No queueing at the head of the line. Throughput scales linearly with worker count.

**Common confusion.** "SKIP LOCKED breaks ordering — I won't get FIFO." Mostly false. The locked rows are skipped, but the SELECT still scans in ORDER BY order, so workers see the next *available* row in priority order. The order is "FIFO among unclaimed jobs," which is exactly what queues want.

#### Walkthrough — the queue SQL below

```sql
SELECT * FROM jobs
WHERE status='pending'
ORDER BY created_at
LIMIT 10
FOR UPDATE SKIP LOCKED;
```

1. Worker A runs this. Scans `jobs` ordered by `created_at`. Acquires X locks on the first 10 unlocked pending rows.
2. Worker B runs the same query concurrently. Sees the same 10 rows but they're locked → SKIP. Continues scanning. Acquires locks on rows 11-20.
3. No contention, no blocking, no deadlock. Both workers commit their UPDATEs to mark the jobs `running`.

Postgres ≥ 9.5 and MySQL ≥ 8: don't wait for the lock, just skip rows that are locked. Essential for **DB-backed queues**.

```sql
SELECT * FROM jobs
WHERE status='pending'
ORDER BY created_at
LIMIT 10
FOR UPDATE SKIP LOCKED;
```

Multiple workers can pull jobs concurrently without contention.

### `NOWAIT`

Throw an error immediately if the lock can't be acquired:
```sql
SELECT * FROM x WHERE id=1 FOR UPDATE NOWAIT;
```

Use when you'd rather fail fast than wait (interactive endpoints).

### Advisory locks (Postgres)

#### Mental model — borrowing the lock manager

Postgres already runs a high-quality, deadlock-detecting, MVCC-aware lock manager. Advisory locks let *your application* register named mutexes inside it, identified by an integer of your choosing. You're saying: "Postgres, please remember that key 12345 is currently 'mine'; block anyone else who asks for it."

There's no row, no table, no constraint involved. It's a pure synchronization primitive that happens to live in your DB connection. Two flavors:
- **Session-scoped** (`pg_advisory_lock`): released only when you explicitly unlock or your connection dies. Survives across transactions.
- **Transaction-scoped** (`pg_advisory_xact_lock`): released automatically on COMMIT/ROLLBACK. Safer because connection leaks can't leak locks.

**Common confusion.** "Advisory locks work across separate Postgres instances." No — they're cluster-local. For cross-cluster mutex you need Redis/ZooKeeper/etcd. Also: they don't work cleanly through pgbouncer transaction-pooling mode, because the lock is tied to the *session* but the session is recycled between transactions.

Application-defined locks keyed by an integer (or two). Not tied to a row.

```sql
-- Acquire
SELECT pg_advisory_lock(12345);
-- ... critical section ...
SELECT pg_advisory_unlock(12345);

-- Or transaction-scoped (auto-released on commit/rollback)
SELECT pg_advisory_xact_lock(12345);
```

Use cases:
- Singleton job execution (only one worker runs at a time)
- Coordinating across rows (e.g., "this user is being processed by one worker")
- Application-level mutex without a separate locking service

### Optimistic vs pessimistic concurrency

#### Mental model — two philosophies for the same problem

Two classes of customers walk into a clothing store:

- **Pessimist**: takes the shirt off the rack into the changing room and locks the door. While inside, nobody else can take that shirt. Total guarantee, but if they spend 20 minutes deciding, the shirt is unavailable to everyone else.
- **Optimist**: takes the shirt, tries it on at home, comes back to buy. At checkout the clerk says "hmm, someone else already bought this color, let me re-check." If unsold, deal closes. If sold, the optimist goes home empty-handed — they bet on low conflict and lost.

OCC is great when conflicts are rare; under high contention it degrades into a livelock of retries. Pessimistic locking is the opposite — its cost is paid up front whether or not the conflict materializes.

**Common confusion.** "Optimistic locking is always better because no blocking." Only true when conflict probability is *very* low. Under contention, OCC produces a thundering herd of retries: 1 winner, N-1 retries, half of those retry-and-conflict again. At that point pessimistic locking has lower total latency.

#### Walkthrough — the OCC version-column update

```sql
UPDATE products SET price=10, version=version+1
WHERE id=1 AND version=$expected_version;
```

1. Reader fetches `(id=1, price=8, version=7)` into the app.
2. App computes new price = 10 and issues the UPDATE with `WHERE version=7`.
3. Case A: nobody else updated → 1 row affected, version is now 8. Commit.
4. Case B: someone else got there first and bumped version to 8 → WHERE clause matches 0 rows. App sees `rowcount=0`, refetches, re-applies its logic, retries.
5. After K retries (typically K ≤ 3), give up with a 409 Conflict to the user.

**Pessimistic** (lock first):
```sql
SELECT … FOR UPDATE;
-- modify
COMMIT;
```
- Strong guarantees
- Contention under load
- Risk of deadlocks

**Optimistic** (version check):
```sql
UPDATE products SET price=10, version=version+1
WHERE id=1 AND version=$expected_version;
-- If 0 rows affected → conflict; retry
```
- High concurrency
- App must handle retries
- No locks held; great for low-conflict workloads

### Two-phase locking (2PL)

#### Mental model — climb up, then climb down

Picture a transaction's lock count over time. With ordinary 2PL it rises monotonically through the *growing phase*, hits a peak (the lock point), then falls monotonically through the *shrinking phase*. The crucial invariant: once you release any lock, you can never acquire another. This is what guarantees serializability.

```
   #locks   ─────────────────────────
            │      growing │ shrinking
        4 ──┤         ▲     ▲
        3 ──┤      ┌──┘     └──┐
        2 ──┤   ┌──┘           └──┐
        1 ──┤┌──┘                 └──┐
        0 ──┘─────────────────────────────▶ time
                       lock point
```

**Strict 2PL** moves the entire shrinking phase to a single point: COMMIT. All locks held until commit, then all released at once. This is what every real production engine uses — it also guarantees recoverability (no cascading aborts).

**Common confusion.** "2PL prevents deadlocks." It doesn't — 2PL is a *serializability* protocol, not a deadlock-avoidance protocol. Deadlocks can absolutely happen under 2PL; you handle them by detection + abort or by external ordering rules.

Theoretical foundation:
- **Growing phase**: acquire locks
- **Shrinking phase**: release locks (after the last lock is acquired, no more can be acquired)

Strict 2PL: all locks held until commit. Standard in pessimistic systems. **MVCC engines use 2PL only for writes.**

### Lock escalation

Some engines (SQL Server) escalate many row locks to a table lock to save memory. Postgres and InnoDB don't escalate.

### Common misconceptions

- "MVCC = no locks" — writers still acquire row locks
- "Deadlock = system failure" — it's normal; the DB resolves it; app retries
- "FOR UPDATE in a SELECT also locks the rows it joined to" — no; only the rows from the targeted table (use `FOR UPDATE OF table_name`)
- "Postgres advisory locks are slow" — they're cheap, sub-millisecond
- "ALTER TABLE is fast" — it can take ACCESS EXCLUSIVE on huge tables for a long time
- "READ COMMITTED has no locks" — writes still hold X locks

### Interview traps

1. **"What's the difference between `FOR UPDATE` and isolation level?"** — `FOR UPDATE` is per-row pessimistic locking; isolation is the global concurrency rule.
2. **"How do you build a job queue in Postgres?"** — `FOR UPDATE SKIP LOCKED`.
3. **"How do two workers coordinate so only one runs?"** — Advisory lock OR a row lock on a singleton row.
4. **"What's a gap lock?"** — InnoDB lock on key range to prevent phantoms. Watch out: small inserts can block under RR.
5. **"Online schema migration?"** — pt-online-schema-change, gh-ost (MySQL); `CREATE INDEX CONCURRENTLY` (Postgres). Plain `ALTER` can block prod.

---

## Real examples

### Mental model for this section

Each example below is a *recipe* for a real production pattern. Don't memorize the SQL — internalize the *shape*:
- **Payments** = pessimistic lock + consistent ordering.
- **Job queue** = `FOR UPDATE SKIP LOCKED` for concurrent workers.
- **Singleton job** = advisory lock used as a mutex.
- **Price update** = optimistic concurrency via version column.

In an interview, when a system-design question lands, ask "is this read-heavy, write-heavy, or contention-heavy?" then pick the recipe.

### Payments — race-free debit

```sql
BEGIN;
SELECT balance_cents FROM accounts WHERE id = $from FOR UPDATE;
-- Compute and validate in app
UPDATE accounts SET balance_cents = balance_cents - $amount
  WHERE id = $from AND balance_cents >= $amount;
-- If 0 rows: ROLLBACK + error
UPDATE accounts SET balance_cents = balance_cents + $amount WHERE id = $to;
COMMIT;
```

Lock order: always `LEAST(from, to)` first, then `GREATEST`. Same direction across all callers → no deadlock.

Step-by-step:
1. `BEGIN` opens an explicit transaction — required, because we need the lock from step 2 to survive past the SELECT.
2. `SELECT … FOR UPDATE` acquires an X lock on the `from` account row. Any other transaction trying to debit/credit this account waits.
3. App computes the new balance and re-checks the invariant (`balance_cents >= $amount`) inside the SQL itself — defense-in-depth in case the app forgot.
4. If 0 rows updated, the balance was insufficient (or the row vanished). Rollback and signal an error.
5. Credit the destination. Same lock-ordering rule prevents a `from=A, to=B` and `from=B, to=A` pair from deadlocking each other.
6. `COMMIT` releases all X locks atomically.

### Job queue with multiple workers

```sql
BEGIN;
WITH job AS (
  SELECT id FROM jobs
  WHERE status='pending' AND run_at <= NOW()
  ORDER BY priority DESC, created_at
  LIMIT 1
  FOR UPDATE SKIP LOCKED
)
UPDATE jobs SET status='running', started_at=NOW()
WHERE id = (SELECT id FROM job)
RETURNING *;
COMMIT;
```

Each worker grabs one available job; no two workers see the same row.

Step-by-step:
1. The CTE `job` runs a `FOR UPDATE SKIP LOCKED` selecting the highest-priority pending job. Locked rows (jobs being processed by other workers) are skipped entirely.
2. The outer `UPDATE` writes `status='running'` for that one row, atomically transitioning it out of the pending pool.
3. Because the SELECT and UPDATE are in the same transaction, the row's lock is held until COMMIT — no other worker can grab it in between.
4. If the worker process crashes mid-job, the transaction rolls back and the row's status reverts to `pending`. A janitor process or NOWAIT-claimer can recover.

### Singleton periodic job (advisory lock)

```javascript
// At startup or on schedule
const result = await db.query("SELECT pg_try_advisory_lock(42) AS got");
if (!result.rows[0].got) {
  console.log("Another worker is running this; skip.");
  return;
}
try {
  await doWork();
} finally {
  await db.query("SELECT pg_advisory_unlock(42)");
}
```

Step-by-step:
1. `pg_try_advisory_lock(42)` is the *non-blocking* variant — it returns `true` if the lock was acquired, `false` if someone else has it. The blocking variant would just wait.
2. If we didn't get the lock, another worker is already running this job. Bail out — no work to do.
3. The `try/finally` is critical. If `doWork()` throws, we still need to release the lock; otherwise the next invocation will think a worker is still running and skip itself forever.
4. Pitfall: if this process *crashes* (not throws — actually dies), the lock is automatically released when the DB connection closes. That's why advisory locks are safer than table-row-as-mutex patterns where you have to remember to clean up.

### Optimistic concurrency (e-commerce price update)

```sql
UPDATE products
SET price_cents = $new_price, version = version + 1
WHERE id = $id AND version = $expected_version;
-- 0 rows affected → another writer won; refetch and retry
```

Step-by-step:
1. Earlier: read `(price=8, version=7)` and present to the user.
2. User submits new price. We attempt to UPDATE *gated on the version we read*.
3. Postgres acquires a brief X lock to evaluate the WHERE, finds version still=7, updates to price=$new, version=8. 1 row affected. We're done — and we know nobody else has clobbered our edit.
4. If someone else got there first, version is 8 and our WHERE clause doesn't match. 0 rows affected — we treat that as a 409 and have the client refetch.

### Detecting current blocking (Postgres)

```sql
SELECT
  blocked.pid AS blocked_pid, blocked.query AS blocked_query,
  blocking.pid AS blocking_pid, blocking.query AS blocking_query,
  now() - blocked.query_start AS blocked_for
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
  ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));
```

### Reproducing a deadlock (Postgres, 2 psql sessions)

```sql
-- Session 1
BEGIN; UPDATE t SET x=1 WHERE id=1;

-- Session 2
BEGIN; UPDATE t SET x=1 WHERE id=2;
UPDATE t SET x=1 WHERE id=1;  -- waits

-- Session 1
UPDATE t SET x=1 WHERE id=2;  -- deadlock detected; one TX aborted
```

---

## Common interview questions

1. Difference between optimistic and pessimistic locking.
2. What is `SELECT FOR UPDATE`? When do you use it?
3. What is a deadlock? How does the DB detect it? How do you prevent it?
4. How would you implement a job queue in Postgres?
5. Difference between row, page, and table locks.
6. What is `SKIP LOCKED`?
7. What is an advisory lock? Use case?
8. How would you safely add a NOT NULL column to a 100M-row table in production?
9. Difference between Postgres and MySQL locking models.
10. What is a gap lock?
11. How do you implement a distributed lock without a separate locking service?
12. What's the impact of a long-running transaction on the system?

---

## Detailed answers

### 1. Optimistic vs pessimistic
- Pessimistic: lock first, then modify. Strong, but blocks under contention.
- Optimistic: version-check on write. Concurrent-friendly; app must retry.
- Choose by conflict probability and latency budget.

### 2. SELECT FOR UPDATE
Acquires an exclusive row lock; other transactions trying to write or `FOR UPDATE` the same row wait. Use when you need to read-then-write atomically (transfer, inventory reservation).

### 3. Deadlock
Cycle of waits where A waits for B's lock, B waits for A's lock. Engine detects (Postgres `deadlock_timeout`, MySQL deadlock detector) and aborts one TX. Prevent: consistent lock ordering, short transactions, advisory locks for critical sections.

### 4. Postgres job queue
`SELECT … WHERE status='pending' ORDER BY priority, created_at LIMIT 1 FOR UPDATE SKIP LOCKED;` then `UPDATE … SET status='running'`. Workers don't contend; throughput scales linearly.

### 5. Lock granularity
- Row: fine-grained, high concurrency
- Page: groups of rows; some engines
- Table: coarse; used by DDL
- Engines may also have predicate/gap locks for range protection

### 6. SKIP LOCKED
Don't block on rows that are locked; skip them. Essential for queue workers; prevents the head-of-line blocking that hurts plain `FOR UPDATE` queues.

### 7. Advisory lock
Application-defined integer-keyed lock. Cheap. Use cases: singleton job, per-user processing serialization, distributed mutex (within a single Postgres cluster).

### 8. Add NOT NULL column safely
1. `ALTER TABLE … ADD COLUMN x INT;` (no default → fast in Postgres 11+)
2. Backfill in batches: `UPDATE … WHERE x IS NULL AND id IN (range)`
3. `ALTER TABLE … ALTER COLUMN x SET NOT NULL;` — locks briefly
4. Postgres 12+: can validate constraint separately via `NOT VALID` + `VALIDATE`
5. For MySQL: `pt-online-schema-change` or `gh-ost` to avoid blocking

### 9. Postgres vs MySQL locking
- Postgres uses MVCC with no gap locks; SSI at SERIALIZABLE
- MySQL InnoDB uses MVCC + next-key locks at RR; more blocking
- Postgres: writes don't block reads; MySQL: gap locks can block INSERTs in unrelated ranges

### 10. Gap lock
InnoDB lock on a gap between index records. Prevents phantoms at REPEATABLE READ. Side effect: large gaps can be locked when not needed, causing surprising blocks in INSERT-heavy workloads.

### 11. Distributed lock without separate service
- Postgres advisory lock — works within one cluster
- DB row with TTL (`UPDATE locks SET held_by=$me, expires=$ts WHERE name=$n AND (held_by IS NULL OR expires < NOW())`)
- Redis (Redlock or simple SETNX with TTL) — most common cross-service
- ZooKeeper / etcd — strong consistency

### 12. Long transaction impact
- Locks held → blocks others
- Postgres: dead tuples can't be vacuumed → table/index bloat
- Snapshot held → other long-running queries can rely on it but the planner sees fewer cleanups
- WAL accumulates if needed for replication
- **Set `idle_in_transaction_session_timeout`** to kill stuck transactions

---

## Practical coding examples

### Mental model — defensive patterns

The snippets below are the "every senior engineer should reach for these" toolkit. The retry-on-deadlock loop is mandatory in any pessimistic-locking codebase; the consistent-ordering trick eliminates an entire class of bugs; advisory locks turn cross-row coordination into a one-liner; and the diagnostic queries are how you debug at 3 AM.

**Common confusion.** "Retry-on-deadlock means hiding bugs." No — deadlocks under concurrent updates are *expected*; the retry is part of correctness. The bug is failing to retry, not the deadlock itself.

### Lock ordering for transfer
```sql
BEGIN;
SELECT * FROM accounts WHERE id IN (LEAST($a,$b), GREATEST($a,$b))
ORDER BY id FOR UPDATE;
-- (now both rows are locked in id order)
COMMIT;
```

### Application-level retry on deadlock
```javascript
async function txWithRetry(fn, attempts = 3) {
  for (let i = 0; i < attempts; i++) {
    try { return await fn(); }
    catch (e) {
      if (e.code === '40P01' || e.code === '40001') {  // deadlock or serialization
        await sleep(50 * (i + 1) * Math.random());
        continue;
      }
      throw e;
    }
  }
  throw new Error('TX_RETRY_EXHAUSTED');
}
```

Step-by-step:
1. Wrap your business logic `fn` (which contains its own BEGIN/COMMIT) and run it up to N times.
2. Catch only the two retryable errors: `40P01` (deadlock) and `40001` (serialization failure under SSI). Any other error is unrelated to concurrency — re-throw.
3. Exponential-ish backoff with random jitter spreads retries; without jitter, two retrying transactions will collide again at the same instant.
4. After N failed attempts, surface a final error. In production this is rare; it indicates a hot row or pathological access pattern that needs a redesign.

### Implement a rate-limited critical section
```sql
SELECT pg_advisory_xact_lock(hashtext('rate-limit:' || $user_id));
-- ... do rate-limited work ...
-- lock auto-released on COMMIT/ROLLBACK
```

### Spot long-running locks (Postgres)
```sql
SELECT pid, usename, state, query,
       now() - xact_start AS xact_age,
       now() - state_change AS state_age
FROM pg_stat_activity
WHERE state <> 'idle' AND xact_start IS NOT NULL
ORDER BY xact_age DESC;
```

### MySQL — see lock waits
```sql
SELECT * FROM performance_schema.data_lock_waits;
```

---

## Common mistakes

- Not handling deadlock errors in application code
- Acquiring locks in inconsistent order across code paths → deadlocks at random
- Holding a transaction open while making an HTTP call
- Using `FOR UPDATE` without `SKIP LOCKED` in a queue (workers serialize)
- DDL during business hours on big tables — ACCESS EXCLUSIVE blocks reads too
- Long transactions blocking VACUUM → silent performance decay
- Using app-level locks (e.g., Node mutex) for cross-process coordination — useless across multiple instances

---

## Senior engineer discussion points

- **Connection pool sizing** vs `max_connections` — over-pooled apps create lock-wait amplification
- **pgbouncer transaction pooling** + features that need session state (advisory locks) — be careful
- **Lock-free patterns**: CRDTs, append-only logs, idempotency keys with unique constraints
- **Index design impacts locking**: a write touching many secondary indexes acquires more locks
- **Lock waits as a leading indicator** of throughput issues — monitor them
- **DDL with `CREATE INDEX CONCURRENTLY`** + `VALIDATE CONSTRAINT` for low-impact schema changes
- **Online schema change tools** for MySQL: gh-ost, pt-online-schema-change
- **Cross-DB locking**: 2PC vs sagas; or DB-backed distributed locks via Postgres advisory or Redlock — discuss trade-offs

---

## Revision notes

- Lock granularity: row / page / table / predicate(gap) / advisory
- Lock modes: S, X (and IS, IX as intention)
- Deadlock: cycle; resolved by aborting one; retry app-side
- **Consistent lock order** prevents deadlocks
- `FOR UPDATE SKIP LOCKED` = queue worker pattern
- `pg_advisory_xact_lock` = transaction-scoped logical mutex
- Optimistic = version column; pessimistic = `FOR UPDATE`
- Postgres has no gap locks (no phantom blocking); MySQL RR does
- DDL on big tables → block writers; use CONCURRENTLY / gh-ost
- Long transactions = bloat (Postgres), held locks, replica lag
- Monitor `pg_stat_activity` + `pg_blocking_pids`
