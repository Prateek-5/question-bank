# Reproduce a phantom read and prevent it (Postgres vs MySQL)

## Source / Origin
- Classic ANSI anomaly; routinely asked after dirty/non-repeatable.
- Concept reference: `backend-data-prep/sql/07-isolation-levels.md`.
- Real-world incident pattern: report total disagrees with row count.

## Why this question matters in interviews
Phantom is where the Postgres-vs-MySQL distinction becomes a real interview discriminator. Most candidates blur "REPEATABLE READ prevents phantoms" into one bullet. Senior candidates pull it apart: Postgres RR prevents phantom *reads* via snapshot but allows phantom-driven write skew; MySQL InnoDB RR prevents both via **next-key locks**. If you can draw the difference on a whiteboard, you signal real database literacy.

## Concepts involved

### Syntax to lock in

```sql
-- The classic phantom: same predicate, different row counts
BEGIN;
SELECT count(*) FROM bookings WHERE room=5 AND day='2026-05-16';  -- 0
-- ... T2 inserts a matching row and commits ...
SELECT count(*) FROM bookings WHERE room=5 AND day='2026-05-16';  -- 1  ← phantom
COMMIT;

-- Fix #1 (Postgres / MySQL): REPEATABLE READ
-- Postgres: snapshot blocks the phantom from being read
-- MySQL: next-key locks block the INSERT from happening at all

-- Fix #2 (engine-agnostic): UNIQUE INDEX on the predicate
CREATE UNIQUE INDEX bookings_room_day_uniq ON bookings(room, day);
INSERT INTO bookings (room, day) VALUES (5, '2026-05-16')
  ON CONFLICT (room, day) DO NOTHING;
```

Symbol form: `R1(P), W2(insert into P), C2, R1(P)` where P is a predicate.

### Edge cases / interview traps

1. **Postgres RR prevents the phantom *read* but allows the resulting *write skew*.** This is the gotcha. You read "no booking exists", T2 inserts one, you both insert — Postgres RR doesn't see T2's row in your snapshot, so you happily insert a duplicate (unless a unique constraint catches you).
2. **MySQL InnoDB RR uses next-key locks** = record lock + gap lock. A `SELECT ... WHERE day='2026-05-16' FOR UPDATE` locks not just existing rows but the gap between index keys, blocking T2's INSERT outright.
3. **Phantom requires a predicate, not a single row.** A single-row re-read seeing different values is non-repeatable read. Predicate matching new rows is phantom.
4. **`SELECT ... FOR UPDATE` does *not* prevent phantoms in Postgres** — there's no row to lock! You'd need to lock the *parent* row (e.g., the room row, not the booking row).
5. **UNIQUE constraint is the cheapest fix** for "no two rows match this predicate". The DB physically prevents the second insert. No isolation upgrade needed.
6. **SERIALIZABLE (Postgres SSI)** prevents phantoms by tracking predicate reads and aborting if a write would have made your read inconsistent.

## Mental Model

The **"empty parking spot"** model. You drive into a lot, scan: spot #5 is empty. You park. While you're parking, another driver also scanned, also saw #5 empty, also parked. Two cars in one spot. Each driver's *individual* observation was correct; the *interleaving* broke the invariant.

```
   T1:  see "no booking for room 5 on May 16"  →  INSERT row
   T2:                                              see "no booking for room 5 on May 16"  →  INSERT row
                                                                                       ^ phantom from T1's POV (if T1 re-read)
                                                                                       ^ both rows now exist; double-booking
```

Three weapons to defeat this:
- **Snapshot** (Postgres RR): T1's *read* is fixed; but T1 can still write a colliding row.
- **Gap lock** (MySQL RR): physically blocks T2's INSERT into the range T1 read.
- **Unique constraint**: DB rejects the second INSERT regardless of isolation.

## Why interviewers care

- It's the **first multi-row anomaly** — tests whether you can think about *sets of rows* and not just individual rows.
- It's the **Postgres-vs-MySQL discriminator**: explaining the gap-lock difference signals real engine knowledge.
- It's the **gateway to write skew**: phantoms over a predicate are the most common cause of write skew in production.

## Common beginner confusion

- "RR prevents phantoms" — depends on engine. Postgres RR: snapshot prevents the phantom *read* but not the phantom write-collision. MySQL RR: gap locks prevent both.
- "Phantom is the same as non-repeatable read" — no. Non-repeatable = same row's value changed. Phantom = predicate matched new rows.
- "I can fix phantom with `FOR UPDATE`" — only if there's a row to lock. For "create if not exists" patterns, there's no row yet; the unique index is the actual fix.
- "Postgres SERIALIZABLE locks rows like MySQL gap locks" — different mechanism. Postgres SSI tracks predicate reads via SIREAD locks, detects dangerous structures, aborts one transaction. No physical gap locking.

## Brute force approach

`LOCK TABLE bookings IN EXCLUSIVE MODE` before every read. Works; kills concurrency for the entire table. Don't do this.

## Optimal approach

Pick the right tool for the shape:

- **"Create unique X if not exists"** → UNIQUE INDEX + `ON CONFLICT DO NOTHING`. Cheapest, engine-agnostic.
- **"Count and decide"** → SERIALIZABLE (Postgres) or RR (MySQL with gap locks).
- **"Read range, then write into the range"** → MySQL RR is enough; Postgres needs SERIALIZABLE or explicit `SELECT FOR UPDATE` on a parent row.

## Solution

```sql
-- ============================================================
-- Reproduce in Postgres at READ COMMITTED (or RR — phantom still drives write skew)
-- ============================================================

CREATE TABLE bookings (
  id    SERIAL PRIMARY KEY,
  room  INT NOT NULL,
  day   DATE NOT NULL
);

-- Session A
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT count(*) FROM bookings WHERE room=5 AND day='2026-05-16';   -- 0

-- Session B
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT count(*) FROM bookings WHERE room=5 AND day='2026-05-16';   -- 0
INSERT INTO bookings (room, day) VALUES (5, '2026-05-16');
COMMIT;

-- Session A
INSERT INTO bookings (room, day) VALUES (5, '2026-05-16');         -- succeeds!
COMMIT;
-- Now: two rows. Postgres RR's snapshot prevented the *phantom read* but
-- allowed the colliding write — this is phantom-driven write skew.

-- ============================================================
-- Fix #1 (cheapest, engine-agnostic): UNIQUE INDEX
-- ============================================================
CREATE UNIQUE INDEX bookings_room_day_uniq ON bookings(room, day);

INSERT INTO bookings (room, day) VALUES (5, '2026-05-16')
ON CONFLICT (room, day) DO NOTHING;
-- Second concurrent INSERT: rowcount=0 → 'already booked'.

-- ============================================================
-- Fix #2 (Postgres): SERIALIZABLE + retry on 40001
-- ============================================================
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT count(*) FROM bookings WHERE room=5 AND day='2026-05-16';
-- decision logic
INSERT INTO bookings (room, day) VALUES (5, '2026-05-16');
COMMIT;
-- One of the two concurrent transactions raises 40001; app retries.

-- ============================================================
-- Fix #3 (MySQL): REPEATABLE READ (default) + FOR UPDATE on the range
-- ============================================================
START TRANSACTION;
SELECT id FROM bookings WHERE room=5 AND day='2026-05-16' FOR UPDATE;
-- Even with 0 rows, InnoDB takes a gap lock on the range.
-- T2's INSERT into the range blocks.
INSERT INTO bookings (room, day) VALUES (5, '2026-05-16');
COMMIT;
```

## Step-by-step dry run

T1/T2 timeline (Postgres at RR — phantom-driven write skew):

```
time →

T1:  |--BEGIN RR--|--count=0--|----------------------------|--INSERT--|--COMMIT--|
                   snapshot pinned                          ^ no constraint, succeeds
T2:    |--BEGIN--|--count=0--|--INSERT--|--COMMIT--|
                                          ^ visible to subsequent tx; invisible to T1's snapshot

Final state: 2 rows. Both transactions thought they were the first.
This is phantom + write skew. RR's snapshot didn't help — it prevented T1 from *seeing* T2's row,
but didn't prevent T1 from *writing* a colliding row.
```

Same timeline with `UNIQUE(room, day)`:

```
T1:  |--BEGIN--|--count=0--|----------------|--INSERT--|--ERROR unique_violation--|--ROLLBACK--|
T2:   |--BEGIN--|--count=0--|--INSERT--|--COMMIT--|
                                        ^ wins the race
T1 surfaces a 409/duplicate; client retries or accepts T2's booking.
```

Same timeline with SERIALIZABLE (Postgres SSI):

```
T1:  |--BEGIN SER--|--count=0 (SIREAD lock on predicate)--|--INSERT--|--COMMIT 40001--|--retry--|
T2:    |--BEGIN SER--|--count=0--|--INSERT--|--COMMIT OK--|
                                              ^ T2 wins; T1 detects rw-dependency cycle, aborts
```

Allowed at: RU, RC, RR (Postgres only — the write-skew variant). Prevented at: RR (MySQL), SERIALIZABLE.

## How to think aloud in the interview

> "Phantom is when T1 runs a predicate query, T2 inserts a matching row and commits, and T1 sees a different result set on re-read. The subtle case is **Postgres RR**: the snapshot prevents T1 from *seeing* T2's row, but doesn't prevent T1 from inserting a colliding one — that's phantom-driven write skew, and it bites every booking system. Three fixes:
> 1. **UNIQUE INDEX + ON CONFLICT** — cheapest, engine-agnostic, no isolation upgrade.
> 2. **SERIALIZABLE** in Postgres — SSI tracks predicate reads, aborts one with 40001; need retry.
> 3. **MySQL RR** uses next-key locks (record + gap), so the second INSERT blocks until the first commits. More blocking, less retry logic.
> I default to UNIQUE INDEX. The other two are for cases where the constraint can't be expressed as a unique column tuple."

## Important takeaways

- Phantom = same predicate, different row sets across reads in the same transaction.
- Postgres RR prevents phantom **reads** but not phantom **write collisions**.
- MySQL RR prevents both via next-key locks (record + gap lock).
- SERIALIZABLE (Postgres SSI) prevents both via predicate-read tracking.
- **UNIQUE INDEX is the senior answer** for "create if not exists" patterns.
- `FOR UPDATE` doesn't prevent phantoms unless there's a parent row to lock.

## Variants

1. **"Phantom on DELETE" — same anomaly, opposite direction.** T1 counts 5; T2 deletes one; T1 recounts 4.
2. **"Phantom on range query for sum/average".** Same fix family; the answer is RR snapshot or SSI.
3. **"Why does Postgres RR allow phantom write collision when MySQL RR doesn't?"** Engine design choice: Postgres prioritises read throughput (no gap locks → less blocking); MySQL prioritises stronger RR semantics. Postgres recovers correctness via SSI at SER.
4. **Insert-only audit log** — phantoms don't matter; the predicate "events between T0 and T1" is monotonic.
5. **What about `INSERT ... SELECT`?** Postgres takes an X lock on the inserted rows but not on the read set — phantom-on-the-select can still occur.

## Revision notes

> **phantom-read — 60 second recap**
> - R1(P), Insert2 into P, R1(P) — same predicate, different rows on re-read.
> - Postgres RR prevents phantom *reads* (snapshot) but not phantom-write-collision.
> - MySQL RR prevents both via next-key locks (record + gap).
> - SERIALIZABLE (PG SSI) prevents both via predicate-read tracking, aborts with 40001.
> - **Cheapest fix**: UNIQUE INDEX + `ON CONFLICT DO NOTHING`.
> - Phantom-driven write skew = the most common production "double-booking" cause.
> - Single-row re-read with different value = non-repeatable read, *not* phantom.
