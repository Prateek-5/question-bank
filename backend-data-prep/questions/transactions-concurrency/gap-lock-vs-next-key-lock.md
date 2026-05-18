# Gap Lock vs Next-Key Lock — MySQL InnoDB Specifics

## Source / Origin
- MySQL InnoDB documentation, since 4.x. Refined in 5.7 / 8.0.
- Aurora MySQL inherits the same locking model.
- Companion docs: `transactions-concurrency/phantom-read-scenario.md`, `transactions-concurrency/2pl-vs-mvcc-comparison.md`, `transactions-concurrency/deadlock-construction.md`.
- Interview prompt: "On MySQL InnoDB at REPEATABLE READ, `SELECT * FROM users WHERE age BETWEEN 30 AND 40 FOR UPDATE` — what locks are taken? Could another session INSERT a row with age=35?"

## Why this question matters in interviews
This is the **"do you really know MySQL"** question at senior database interviews. Postgres folks have MVCC + SSI; their isolation story is conceptually clean. MySQL InnoDB at REPEATABLE READ uses a hybrid of MVCC + gap locks to prevent phantoms, and the lock taxonomy — **record lock, gap lock, next-key lock, insert-intent lock** — confuses everyone who hasn't drawn the B-tree picture. Senior MySQL/AWS Aurora candidates are expected to (a) name the four lock kinds, (b) draw the B-tree leaf showing gaps, (c) explain why InnoDB RR prevents phantoms while Postgres RR uses a different mechanism, and (d) decode a real `SHOW ENGINE INNODB STATUS` deadlock trace. This is also where most InnoDB deadlocks come from — gap lock contention on range scans.

## Concepts involved

### Syntax to lock in

The four InnoDB lock types:

```
Record lock      — lock on an index record (one B-tree leaf entry)
Gap lock         — lock on the space *between* two index records (a range, not a row)
Next-key lock    — Record lock + the gap *before* it    (the InnoDB default at RR)
Insert intent lock — a special gap lock acquired by INSERT to signal "I want to insert here"
```

Visualising next-key lock = record + preceding gap:

```
B-tree leaf (sorted by age):
  ...  (gap)  20  (gap)  30  (gap)  40  (gap)  50  (gap)  ...
                ──┬──        ──┬──        ──┬──
                  │             │             │
              next-key       next-key       next-key
              on 20          on 30          on 40
              (gap(15,20] +  (gap(20,30] +  (gap(30,40] +
               record 20)     record 30)     record 40)
```

A next-key lock is **exclusive on (prev_record, this_record]** — half-open interval ending at this record.

Acquiring next-key locks via a range query:
```sql
-- At REPEATABLE READ, this query at MySQL InnoDB
SELECT * FROM users WHERE age BETWEEN 30 AND 40 FOR UPDATE;

-- Locks acquired (assume index records exist at 30 and 40):
-- Next-key lock on (20, 30]:  prevents INSERTs with age in (20, 30]
-- Next-key lock on (30, 40]:  prevents INSERTs with age in (30, 40]
-- Next-key lock on (40, 50]:  the "right side" gap — prevents INSERTs with age in (40, 50]
--
-- Net effect: nothing with age in (20, 50] can be inserted, even though we asked for [30, 40].
```

That last gap — the one extending past the upper bound — is the surprise for newcomers. It's why range scans cause so much locking.

### Edge cases / interview traps

1. **Next-key lock = record + preceding gap.** Many candidates know "InnoDB takes next-key locks" but can't say exactly *which* range. It's `(prev_index_value, this_index_value]` — open on the left, closed on the right.
2. **Gap-only locks happen at the edges.** Beyond the last record in the index, there's a "supremum" gap. A SELECT scanning to the end locks the right tail. Same for the head.
3. **REPEATABLE READ is the only level where gap locks fire.** At READ COMMITTED, MySQL InnoDB takes record locks only (no gaps). This is a major reason teams switch RC for high-throughput OLTP: fewer phantom protection, fewer deadlocks.
4. **Locks are on index records, not rows.** If you `WHERE age = 30` and there's no index on `age`, InnoDB locks the clustered index (full row scan), effectively locking everything it scans. Always index the WHERE columns of FOR UPDATE queries.
5. **Insert-intent locks**: when you INSERT into a gap that another transaction holds a gap lock on, you block. This is the most common phantom-prevention mechanism people don't articulate by name.
6. **Unique index inserts** acquire a stronger lock briefly (to check uniqueness). Deadlocks during INSERT often trace to this.
7. **`FOR UPDATE` vs `LOCK IN SHARE MODE`**. `FOR UPDATE` = X lock. `LOCK IN SHARE MODE` = S lock. Both take gaps at RR.
8. **`READ COMMITTED` disables gap locks**, including on FK references. If you really need RC throughput, you accept some phantom risk.
9. **Postgres doesn't have gap locks.** Postgres prevents phantoms at RR via *snapshot isolation* (MVCC visibility filter), not locks. Different mechanism, similar outcome. Knowing both is a senior signal.
10. **Deadlock origin**: two transactions doing range scans on overlapping ranges in opposite orders deadlock on gap locks. Show this in `SHOW ENGINE INNODB STATUS`.
11. **`innodb_locks_unsafe_for_binlog`** historical flag: turned off gap locks. Removed in 8.0. Mention only if asked about legacy.
12. **`SELECT ... LOCK IN SHARE MODE`** spelling change in 8.0: now `SELECT ... FOR SHARE`. Same semantics.
13. **`SKIP LOCKED` + range scan**: each row is either locked or skipped, but gap locks still propagate normally for the rows you do lock.
14. **`WHERE PRIMARY KEY = literal`** with a matching record only takes a **record lock** (no gap) — the gap is unnecessary because the predicate is point-equality on a unique index.

## Mental Model

### The "spaces between rows are also lockable" insight

Postgres locks rows. MySQL InnoDB locks *rows and the gaps between them*. The gap lock is what makes RR phantom-free in InnoDB.

```
Without gap locks (Postgres-style RR or InnoDB RC):
  T1: SELECT * FROM t WHERE age BETWEEN 30 AND 40;  → [Alice(30), Bob(35)]
  T2: INSERT INTO t VALUES ('Carol', 33);            ← succeeds; no lock to stop it
  T1: SELECT * FROM t WHERE age BETWEEN 30 AND 40;  → [Alice, Bob, Carol]   ← PHANTOM

With gap locks (InnoDB RR):
  T1: SELECT * FROM t WHERE age BETWEEN 30 AND 40 FOR UPDATE;
       → locks records at 30 and 35, plus gaps (20,30], (30,35], (35,40], (40,50]
  T2: INSERT INTO t VALUES ('Carol', 33);
       → wants to insert in gap (30,35] → BLOCKED by T1's gap lock
  T1: SELECT * FROM t WHERE age BETWEEN 30 AND 40 FOR UPDATE;  → [Alice, Bob] unchanged
```

### B-tree leaf with locks drawn

```
Initial state (age index):

    ──◀ ──── 20 ──── 30 ──── 40 ──── 50 ──── ▶──
            Alice   Bob    Dave    Eve
              (record locks shown as ●; gap locks shown as ▒)

After T1: SELECT * FROM users WHERE age BETWEEN 30 AND 40 FOR UPDATE:

    ──◀ ──── 20 ──── 30 ──── 40 ──── 50 ──── ▶──
            Alice   Bob    Dave    Eve
                    ●●●    ●●●
                  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
                  (20,30]  (30,40]  (40,50]
                   gap     gap+rec  gap+rec
                          next-key  next-key
                                    
    ▒▒▒▒▒▒ = locked region; INSERTs into this region block
```

The right-side gap `(40, 50]` is the surprise. You queried up to 40 but the lock extends *past* 40 to the next existing record. This is so that `INSERT 41, 42, ...` cannot create a row that should have been part of your range.

### Next-key = record + preceding gap

```
Lock on record 30 alone (no gap) — used at READ COMMITTED:

           ──── 20 ──── 30 ──── 40 ────
                        ●

Gap lock on (20, 30) alone — used between records:

           ──── 20 ──── 30 ──── 40 ────
                ▒▒▒▒▒▒▒▒

Next-key lock = (20, 30] = both combined — InnoDB default at RR:

           ──── 20 ──── 30 ──── 40 ────
                ▒▒▒▒▒▒▒▒●
```

### Insert intent: "I want this gap"

When session B does `INSERT INTO users VALUES('Carol', 33)`:
1. B navigates the B-tree to find the slot — between 30 and 35 (between Bob's adjacent records, say).
2. B requests an **insert-intent lock** on that gap.
3. If A already holds a gap lock there, B *blocks* until A commits/rolls back.
4. If no conflict, B inserts; the inserted row gets an X record lock until B's transaction ends.

## Why interviewers care

- Maps to **real production**: InnoDB is the most-deployed transactional engine in the world (MySQL + Aurora + MariaDB).
- It's where **most InnoDB deadlocks come from** in real systems. Knowing this means you can debug `LATEST DETECTED DEADLOCK` output.
- It distinguishes **conceptual knowledge** (Postgres RR ≠ InnoDB RR ≠ SQL standard RR) from rote facts.
- It naturally extends to **performance tuning**: switching to RC halves the deadlock rate at the cost of phantom risk.
- It's the **canonical engine-internals question** at AWS, Google, Meta interviews where teams run their own MySQL.

## Common beginner confusion

- **"InnoDB locks rows."** It locks index records *and* the gaps between them. The gaps are the trick.
- **"Postgres and MySQL behave the same at RR."** They don't. Postgres uses snapshot isolation (MVCC visibility filter); MySQL InnoDB uses gap locks. Both prevent phantoms but via different mechanisms.
- **"`WHERE id = 5 FOR UPDATE` locks a gap."** Not if `id` is a unique index with an exact match. Point lookups on unique indexes get a record-only lock, no gap.
- **"The gap lock extends only as far as my WHERE clause."** It extends to the *next index record*. Past your range boundary if necessary.
- **"At RC there are no gap locks."** Correct, *except* for foreign-key checks and a few specific cases (duplicate-key detection on UNIQUE). Always test.
- **"Gap locks always cause deadlocks."** They cause more than RC does, but a properly indexed schema rarely hits them in practice.
- **"`SHOW ENGINE INNODB STATUS` shows row locks."** It shows lock metadata in a notoriously cryptic format. Decoding it takes practice.
- **"Insert intent is a separate kind of lock."** It is a special *gap* lock used by INSERT. Same family.
- **"InnoDB next-key is just a record lock with a hyphen."** No — it's record + preceding gap.

## Brute force approach

"`LOCK TABLES users WRITE`." Yes, prevents phantoms. Also prevents anyone else from doing anything to the table. Don't.

"Use SERIALIZABLE." InnoDB SERIALIZABLE is RR + auto-`LOCK IN SHARE MODE` on every SELECT. Even more locking. Sometimes correct; often unnecessary.

"Use READ COMMITTED everywhere; accept phantoms." Reasonable for high-throughput OLTP if you handle the consequences. Many e-commerce companies (e.g., Shopify, GitHub) run RC.

## Optimal approach

### Reasoning about what locks a query takes

Step by step:

1. **Identify the index used.** Use `EXPLAIN`. The lock is on the index, not the row.
2. **Identify the rows scanned.** Even rows not matching the WHERE are visited and may be locked.
3. **Identify the boundaries.** What's the leftmost and rightmost index record touched?
4. **Apply the rule.** At RR: next-key lock on every visited record + a gap lock past the last one to the next existing record. At RC: record locks only.

Example walkthrough:

```sql
CREATE TABLE users (
  id INT PRIMARY KEY,
  age INT,
  KEY age_idx (age)
);
INSERT INTO users VALUES (1, 20), (2, 30), (3, 40), (4, 50);

-- At RR:
SELECT * FROM users WHERE age BETWEEN 30 AND 40 FOR UPDATE;
-- Index used: age_idx
-- Records visited: 30, 40 (via age_idx); plus PK records 2 and 3
-- Locks taken on age_idx:
--   next-key (20, 30]  — record 30 + preceding gap
--   next-key (30, 40]  — record 40 + preceding gap
--   gap lock (40, 50)  — to prevent insertions past the upper bound but before next record
-- Locks taken on PK (clustered index): record locks on PK=2 and PK=3
```

### When to use RC vs RR in InnoDB

- **RC**: high-throughput OLTP, mostly point updates, infrequent range queries, can tolerate phantoms.
- **RR**: reporting workloads, range-heavy logic, need stable snapshots, need phantom prevention. Default in InnoDB.

### How to minimise gap-lock pain at RR

1. **Index every column in WHERE** of FOR UPDATE — otherwise InnoDB locks the entire clustered index range.
2. **Narrow the predicate.** `WHERE id = 5 FOR UPDATE` (unique match) = record lock only. `WHERE age = 30 FOR UPDATE` (non-unique) = next-key lock.
3. **Avoid open-ended ranges.** `WHERE created_at > $now` locks the entire right tail.
4. **Process in small batches.** Smaller WHERE ranges = smaller locked ranges = fewer conflicts.
5. **Consider switching to RC** for the hot table if range queries are rare and phantoms are tolerable.

## Solution (production debug pattern)

### Reading `SHOW ENGINE INNODB STATUS` for a deadlock

```
*** (1) TRANSACTION:
TRANSACTION 4392, ACTIVE 5 sec inserting
mysql tables in use 1, locked 1
LOCK WAIT 3 lock struct(s), heap size 1136, 2 row lock(s)
INSERT INTO users (age) VALUES (33)
*** (1) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS space id 5 page no 4 n bits 72 index age_idx of table `db`.`users`
trx id 4392 lock_mode X locks gap before rec insert intent waiting
                         ↑↑↑
                         this is the insert-intent lock waiting
                         for T2's gap lock

*** (2) TRANSACTION:
TRANSACTION 4393, ACTIVE 8 sec
... holds gap lock (30, 35] on age_idx ...
also wants to INSERT (37)
```

Translation: T1 holds a gap lock on `(30, 35]`. T2 holds a different gap lock and wants to insert into T1's gap. T1 wants to insert into T2's gap. Cycle → deadlock → InnoDB picks one to abort.

### Fix patterns

```sql
-- 1. Ensure the index exists
CREATE INDEX IF NOT EXISTS age_idx ON users(age);

-- 2. Narrow the lock by using a unique-index point lookup where possible
SELECT * FROM users WHERE id = $1 FOR UPDATE;  -- record-only lock

-- 3. Use SKIP LOCKED if you can tolerate skipping locked rows
SELECT * FROM users WHERE age BETWEEN 30 AND 40 LIMIT 1 FOR UPDATE SKIP LOCKED;

-- 4. Drop to READ COMMITTED for the session if phantoms are tolerable
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- 5. Use a deterministic lock order across transactions
-- Always lock rows in ascending PK order in every transaction.
```

## Step-by-step dry run

Schema as above. Two concurrent transactions at RR:

```
T=0   T1: BEGIN; SELECT * FROM users WHERE age BETWEEN 25 AND 45 FOR UPDATE;
                Locks on age_idx:
                  next-key (20, 30] — record 30 + preceding gap
                  next-key (30, 40] — record 40 + preceding gap
                  gap (40, 50)      — right-side gap

T=1   T2: BEGIN; INSERT INTO users(id, age) VALUES (99, 33);
                T2 wants insert-intent on gap (30, 40].
                T1 holds gap lock on (30, 40].
                T2 BLOCKS.

T=2   T2 still waiting.

T=3   T1: COMMIT.
                Locks released.
                T2's insert-intent lock granted.
                Row (99, 33) inserted.

T=4   T2: COMMIT.
```

If T1 had used RC instead:

```
T=0   T1 (RC): SELECT ... FOR UPDATE
                Locks: record locks on age=30 and age=40 only. No gaps.

T=1   T2: INSERT (99, 33) → no conflict with record locks on existing rows.
                INSERT succeeds immediately.

T=2   T1 re-runs SELECT → sees (99, 33) → PHANTOM ROW. RR's gap locks are what prevented this.
```

### Deadlock dry run

```
T=0   T1: BEGIN; SELECT * FROM users WHERE age BETWEEN 30 AND 40 FOR UPDATE;
                T1 holds gap (30, 40].

T=1   T2: BEGIN; SELECT * FROM users WHERE age BETWEEN 50 AND 60 FOR UPDATE;
                T2 holds gap (40, 50] + (50, 60].

T=2   T1: INSERT INTO users(id, age) VALUES (100, 55);
                T1 wants insert-intent in T2's gap (50, 60].
                T1 BLOCKS.

T=3   T2: INSERT INTO users(id, age) VALUES (101, 35);
                T2 wants insert-intent in T1's gap (30, 40].
                T2 BLOCKS.

T=4   InnoDB deadlock detector: cycle detected.
       Picks the cheaper transaction to abort (usually the one with fewer locks).
       Returns ERROR 1213 to that transaction.
       Other transaction proceeds.
```

This is the most common shape of InnoDB deadlock. Postgres at RR wouldn't deadlock here — it doesn't take gap locks; the inserts would just succeed (creating eventual write skew, which is a different problem).

## How to think aloud in the interview

> "InnoDB locks index records, but at REPEATABLE READ it also locks the *gaps between* index records. That's the key insight that distinguishes MySQL from Postgres at RR.
>
> Four lock types:
> 1. **Record lock** — on an index record.
> 2. **Gap lock** — on the space between two index records.
> 3. **Next-key lock** — record + preceding gap. The InnoDB default at RR.
> 4. **Insert intent lock** — a special gap lock acquired by INSERT, blocking when another tx holds the gap.
>
> For `SELECT * FROM users WHERE age BETWEEN 30 AND 40 FOR UPDATE` at RR:
> - Locks next-key `(20, 30]` — record 30 plus the gap before it
> - Locks next-key `(30, 40]` — record 40 plus its preceding gap
> - Locks gap `(40, 50)` — the right-side gap, extending to the next existing record
>
> So no INSERT with age in `(20, 50]` can succeed until T1 commits. The right-side gap is the surprise — it extends *past* the WHERE upper bound, because otherwise an INSERT just above 40 would be a phantom for T1's range.
>
> Why does Postgres not need gap locks at RR? Postgres uses snapshot isolation — T1's view is frozen at transaction start; new rows are invisible. Locks aren't required; visibility is. Different mechanism, similar outcome (no phantoms at RR), but InnoDB's mechanism has different deadlock characteristics.
>
> Three production hazards:
> - **Deadlocks**: two transactions doing range scans + INSERTs in opposite orders. Drop to RC or use deterministic lock order.
> - **Lock inflation on unindexed columns**: `WHERE age = 30` without index on `age` locks the clustered index row by row across the whole table.
> - **`READ COMMITTED` switch**: disables gap locks; trades phantom prevention for throughput. Common at high-traffic shops.
>
> To debug, read `SHOW ENGINE INNODB STATUS` — specifically the `LATEST DETECTED DEADLOCK` section, which names the index and gap involved."

## Important takeaways

- **Four InnoDB lock kinds**: record, gap, next-key (record + preceding gap), insert intent.
- **Next-key lock = `(prev_record, this_record]`** — half-open interval ending at this record.
- **Gap locks fire only at RR**; RC disables them.
- **Range scans lock past the upper bound** — to the next existing record.
- **Unique-index point match takes record-only lock** (no gap).
- **Postgres RR uses snapshot isolation**, not gap locks; different mechanism, similar outcome.
- **Most InnoDB deadlocks come from gap-lock contention** on range scans.
- **Always index the WHERE columns** of FOR UPDATE — otherwise InnoDB locks the entire scanned range.
- **`SHOW ENGINE INNODB STATUS`** is your debug tool; `LATEST DETECTED DEADLOCK` shows the cycle.
- **`READ COMMITTED` is a valid choice** for high-throughput OLTP — drops gap locks, accepts phantoms.

## Variants

1. **`LOCK IN SHARE MODE` / `FOR SHARE`** — S lock; same gap behaviour but multiple readers can hold simultaneously.
2. **SERIALIZABLE in InnoDB** — RR + automatic `LOCK IN SHARE MODE` on plain SELECTs. Stronger gap locking. Rarely used.
3. **Foreign-key checks at RC** — still take gap locks despite the RC isolation, to prevent dangling references.
4. **`UPDATE` and `DELETE`** — take the same next-key locks as `SELECT ... FOR UPDATE` would for the same WHERE.
5. **MariaDB**: identical model; same `SHOW ENGINE INNODB STATUS` format.
6. **Aurora MySQL**: same locking; lock service is logically the same as InnoDB.
7. **MySQL 5.6 vs 5.7 vs 8.0**: lock messages in status output evolved; lock kinds are the same.
8. **`READ COMMITTED` + `binlog_format=ROW`** — historical reason RC became viable in production for many shops.
9. **Postgres equivalent**: there isn't one. Postgres prevents phantoms at RR via MVCC visibility. Predicate locks (SIREAD) at SERIALIZABLE detect rw-conflicts; closer to SSI than to gap locks.
10. **`SKIP LOCKED` interaction**: SKIP LOCKED skips already-locked rows; gap locks for rows you actually lock still propagate.

## Revision notes

> **gap lock vs next-key lock — 60 second recap**
> - **Record lock**: on an index record.
> - **Gap lock**: on the space between records.
> - **Next-key lock** = record + preceding gap = `(prev, this]`. InnoDB default at RR.
> - **Insert intent**: special gap lock used by INSERT; conflicts with held gap locks.
> - **Range SELECT FOR UPDATE at RR** locks all next-keys in range PLUS the gap past the upper bound to the next record.
> - **Point lookup on unique index** = record-only lock, no gap.
> - **RC disables gap locks** (except FK checks).
> - **Postgres RR prevents phantoms via MVCC**, not gap locks.
> - **InnoDB deadlocks** most often come from gap-lock contention.
> - **Debug**: `SHOW ENGINE INNODB STATUS` → `LATEST DETECTED DEADLOCK`.
> - **Mitigation**: index the WHERE column; narrow the predicate; consider RC for hot tables.
> - **MySQL 8.0**: `LOCK IN SHARE MODE` is now `FOR SHARE`; same semantics.
