# Reproduce a non-repeatable read and prevent it

## Source / Origin
- Standard isolation interview after dirty read.
- Concept reference: `backend-data-prep/sql/07-isolation-levels.md`.
- Real-world incident pattern: "I summed a balance and then re-read it; the totals disagreed."

## Why this question matters in interviews
Non-repeatable read is the **first anomaly that survives Postgres' defaults**. Dirty read is theoretical (Postgres won't reproduce); non-repeatable read happens *every day* in production at READ COMMITTED. Senior engineers must be able to (a) reproduce it in two psql sessions, (b) distinguish it from phantom and from read skew, and (c) prescribe the minimal fix — usually REPEATABLE READ for the duration of a multi-statement read, *not* a global isolation bump.

## Concepts involved

### Syntax to lock in

```sql
-- The anomaly: same SELECT, different results, same transaction
BEGIN;  -- defaults to READ COMMITTED in Postgres
SELECT balance FROM accounts WHERE id = 1;   -- sees X
-- (another tx commits)
SELECT balance FROM accounts WHERE id = 1;   -- sees Y, X ≠ Y
COMMIT;

-- The fix: pin a snapshot
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT balance FROM accounts WHERE id = 1;   -- X
-- ... other writes commit ...
SELECT balance FROM accounts WHERE id = 1;   -- still X (snapshot fixed at BEGIN)
COMMIT;
```

Symbol form: `R1(x), W2(x), C2, R1(x)` — T1 reads x, T2 writes x and commits, T1 re-reads x and sees a different value.

### Edge cases / interview traps

1. **Confused with phantom read.** Non-repeatable = the *same row* changed. Phantom = *new rows* match my predicate. Same family, different fix.
2. **Confused with read skew.** Non-repeatable = same row, two reads. Read skew = two related rows, mutually inconsistent after a third tx's update.
3. **Postgres RR pins the snapshot at the *first* statement that touches data, not at `BEGIN`.** This matters: if you `BEGIN` and then wait an hour before SELECTing, the snapshot is taken at the first SELECT, not at BEGIN.
4. **MVCC means RR is cheap for reads.** No locks, just a snapshot ID. The cost is bloat (old tuple versions can't be vacuumed while your transaction is open).
5. **MySQL RR pins the snapshot at the *first SELECT*, same as Postgres.** Don't confuse with consistent-read vs locking-read semantics: `SELECT ... FOR UPDATE` always reads the latest committed row even at RR.
6. **The retry trap.** Some candidates think "I'll just retry the read until I get the same value twice." That's not a fix; it's a livelock waiting to happen.

## Mental Model

The **"polling a price ticker"** model. You glance at the stock price ($100). Five seconds later you glance again ($95). The ticker is right; *the world moved on*. Within a transaction, you want to be **shielded from that motion** — your decisions should be based on one consistent view of the world.

```
   wall clock:        t0          t1            t2
   actual balance:    100         100→50        50

   T1 at RC:         read 100   ...            read 50    ← non-repeatable
   T1 at RR:         read 100   ...            read 100   ← snapshot pinned
                                                            (T2's commit is real, just invisible here)
```

The fix isn't to slow the world down — it's to take a photograph at BEGIN (or first SELECT) and keep looking at the photograph.

## Why interviewers care

- Tests whether you understand **snapshot isolation**, the implementation strategy behind Postgres RR.
- Probes the **default-isolation gotcha**: most engineers assume the DB protects them from this; it doesn't at the default level.
- Tests whether you'll over-fix: many candidates say "use SERIALIZABLE", which is heavier than needed for a pure read pattern.

## Common beginner confusion

- "RR locks rows for the duration of the transaction." It doesn't — Postgres RR is **snapshot-only**, zero read locks. MySQL RR also relies on MVCC for the read; locks only appear on `FOR UPDATE`.
- "Non-repeatable read can't happen if I'm only reading." It can — a third party's write between your two reads is the cause.
- "If I just read once, I'm safe." Only if your business logic doesn't depend on multiple reads being consistent. Computing a sum of related rows requires multi-read consistency.
- "RR means I see stale data." You see *snapshot-consistent* data. The data is correct for the snapshot point in time; other transactions' commits become visible to your *next* transaction.

## Brute force approach

Wrap each multi-read business operation in a lock: `SELECT ... FOR UPDATE` on every row you'll touch. Works, but blocks every writer and over-pessimises a pure read.

## Optimal approach

Use REPEATABLE READ. Snapshot is taken at the first data-touching statement; subsequent reads see the same snapshot. No locks. The only cost is that any concurrent commits won't be visible until your transaction ends — and a long RR transaction in Postgres prevents vacuum of dead tuples newer than your snapshot.

## Solution

```sql
-- ============================================================
-- Reproduce in Postgres (2 psql sessions)
-- ============================================================

-- Setup
CREATE TABLE accounts (id INT PRIMARY KEY, balance INT);
INSERT INTO accounts VALUES (1, 100);

-- Session A (T1)
BEGIN;                                          -- defaults to RC
SELECT balance FROM accounts WHERE id = 1;      -- 100

-- Session B (T2)
UPDATE accounts SET balance = 50 WHERE id = 1;  -- autocommit ON

-- Session A (T1)
SELECT balance FROM accounts WHERE id = 1;      -- 50  ← non-repeatable read
COMMIT;

-- ============================================================
-- Fix #1: REPEATABLE READ
-- ============================================================

-- Session A
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT balance FROM accounts WHERE id = 1;      -- 100  (snapshot pinned here)

-- Session B
UPDATE accounts SET balance = 50 WHERE id = 1;  -- commits

-- Session A
SELECT balance FROM accounts WHERE id = 1;      -- still 100  ← snapshot held
COMMIT;
-- Subsequent transactions in Session A will see 50.

-- ============================================================
-- Fix #2: pessimistic — lock the row at first read
-- ============================================================
BEGIN;  -- RC is fine
SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;   -- 100; blocks T2
-- ... multi-step business logic ...
SELECT balance FROM accounts WHERE id = 1;              -- still 100 (T2 blocked)
COMMIT;  -- releases lock; T2 now proceeds with the new value
```

## Step-by-step dry run

T1/T2 timeline at READ COMMITTED:

```
time →

T1:  |--BEGIN--|--R(bal)=100--|------------------|--R(bal)=50--|--COMMIT--|
                                                  ^ value changed mid-tx!
T2:                |--BEGIN--|--W(bal=50)--|--COMMIT--|
                                            ^ visible to T1's next statement under RC

Inside T1's mind:
  Step 1: balance is 100. Plan: charge $80 fee.
  Step 2: re-check balance... it's 50?! My plan was based on 100.
  Step 3: bug — either underspend (be conservative) or overspend (be optimistic).
```

Same timeline at REPEATABLE READ:

```
T1:  |--BEGIN RR--|--R(bal)=100--|------------------|--R(bal)=100--|--COMMIT--|
                                                     ^ snapshot pinned at first read
T2:                  |--BEGIN--|--W(bal=50)--|--COMMIT--|
                                              ^ committed, but invisible to T1's snapshot

T1's mind: 100, then still 100. Consistent. Decisions on the original balance.
After COMMIT, T1's next transaction will see 50.
```

Allowed at: READ UNCOMMITTED, READ COMMITTED. Prevented at: REPEATABLE READ, SERIALIZABLE.

## How to think aloud in the interview

> "Non-repeatable read is when T1 reads a row twice and gets different values because T2 committed an update in between. The fix is REPEATABLE READ — Postgres takes a snapshot at the first data-touching statement and all subsequent reads come from that snapshot. Zero locks on the read path; T2 is free to commit, T1 just doesn't see it. The cost is that long RR transactions hold the snapshot open and Postgres can't vacuum dead tuples older than that — so keep the transaction short. The pessimistic alternative is `SELECT ... FOR UPDATE` at RC, which blocks T2 entirely. I'd use RR for pure read patterns and FOR UPDATE when I plan to write at the end."

## Important takeaways

- Non-repeatable read = same row, two reads, different committed values.
- Prevented by REPEATABLE READ (snapshot) at zero read-lock cost.
- Snapshot taken at *first data-touching statement*, not at BEGIN — keep RR transactions short.
- Distinguish from phantom (new rows) and read skew (multi-row consistency).
- Pessimistic alternative: `FOR UPDATE` at RC.

## Variants

1. **"What if I'm reading 50 rows in a join?"** Each row could be non-repeatable individually, but more importantly multi-row consistency is *read skew* — same fix (RR), different name.
2. **"Read replicas — can I get non-repeatable read across replicas?"** Yes, but it's a different mechanism (replication lag, not isolation). Pin to the primary or use sticky-session reads.
3. **"My ORM does `find` then `update` — is that a non-repeatable read?"** No, that's the **lost update** pattern. Different anomaly, different fix (conditional UPDATE or version column).
4. **MySQL InnoDB**: same snapshot semantics at RR; gap locks only matter for phantom/range reads, not single-row re-reads.

## Revision notes

> **non-repeatable-read — 60 second recap**
> - R1(x), W2(x), C2, R1(x) — T1 reads x twice, sees two different committed values.
> - Allowed at RU, RC. Prevented at RR, SER.
> - Postgres RR = snapshot pinned at first statement; zero read locks.
> - Long RR transactions in Postgres → vacuum can't reclaim → bloat.
> - Pessimistic alternative: `SELECT … FOR UPDATE` at RC.
> - Distinct from phantom (new rows) and read skew (multi-row).
> - MySQL RR: same snapshot behaviour for re-reads.
