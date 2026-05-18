# Reproduce write skew and explain why only SERIALIZABLE prevents it

## Source / Origin
- The "senior question" of isolation interviews.
- Originated in Berenson et al. "A Critique of ANSI SQL Isolation Levels" (1995).
- Concept reference: `backend-data-prep/sql/07-isolation-levels.md`.

## Why this question matters in interviews
Write skew is the *discriminator* in senior database rounds. Every mid-level engineer knows dirty read, non-repeatable, phantom, lost update. Few can define write skew precisely or explain why snapshot isolation (Postgres RR) doesn't catch it. If you can draw the doctor-on-call timeline, name "two read sets overlap, two write sets disjoint, invariant breaks", and propose the fix, you signal senior-level data correctness reasoning.

## Concepts involved

### Syntax to lock in

```sql
-- The canonical: doctor-on-call invariant (≥1 doctor must be on call)
BEGIN ISOLATION LEVEL REPEATABLE READ;  -- Postgres snapshot isolation
SELECT count(*) FROM oncall WHERE on_duty = true;   -- T1 sees 2 (Alice, Bob)
-- decision: "≥2, so I can go off duty"
UPDATE oncall SET on_duty = false WHERE name = 'Alice';
COMMIT;
-- Meanwhile T2 made the symmetric decision for Bob.
-- Final: 0 doctors on call. Invariant violated.

-- Fix: SERIALIZABLE — PG SSI detects the rw-cycle, aborts one with 40001
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT count(*) FROM oncall WHERE on_duty = true;
UPDATE oncall SET on_duty = false WHERE name = 'Alice';
COMMIT;  -- one of the two raises 40001 → retry
```

### Edge cases / interview traps

1. **Write skew ≠ lost update.** Lost update = two writes to the *same row*. Write skew = two writes to *different rows* whose decisions depend on overlapping reads.
2. **Postgres RR (snapshot isolation) does NOT prevent write skew.** This is the most common slip. Both transactions see the same snapshot, both decide independently, both write to disjoint rows. No row-level conflict; no abort.
3. **MySQL InnoDB RR doesn't prevent write skew either.** Gap locks prevent phantom *inserts*, but write skew involves *updates* to existing rows. Gap locks don't help.
4. **Only SERIALIZABLE (Postgres SSI) prevents it implicitly.** Or you must lock the read set explicitly with `SELECT FOR UPDATE`, or materialise the invariant into a single row that all transactions update.
5. **The "row lock on the read set" trick** — `SELECT * FROM oncall WHERE on_duty = true FOR UPDATE` locks both Alice's and Bob's rows. T2 then blocks on T1's lock; serial execution; invariant held.
6. **The "materialise invariant" trick** — add a `counters(name, val)` row for "oncall_count". Every duty-change UPDATEs that row. Two concurrent updates now conflict on the same row → lost update → row-lock-wait → serial.

## Mental Model

The **"two people leaving a meeting room"** model. Two attendees both check the calendar: "Two of us are scheduled for the 3 PM standup; I can skip." Each individually verified there's coverage. Each leaves. Nobody attends. The *individual decisions* were both correct; the *combination* broke the invariant.

```
   Read set:    {Alice on, Bob on}      ← T1 and T2 both read this
   T1 writes:   Alice = off
   T2 writes:   Bob   = off              ← disjoint write sets!
   Invariant violated:  count = 0 after both commit

   Conflict graph (the SSI insight):
     T1 reads Bob, T2 writes Bob   → T1 → T2 (rw edge)
     T2 reads Alice, T1 writes Alice → T2 → T1 (rw edge)
     CYCLE  ← not serializable; SSI aborts one.
```

There's no row both write — so no row lock fires. The conflict is between **read sets and write sets that overlap on different rows**.

## Why interviewers care

- It's the **anomaly that snapshot isolation specifically doesn't catch** — proves you know the difference between SI and serializability.
- It's the **textbook senior signal** — Berenson et al.'s critique paper introduced this as the gap in ANSI.
- It's the **gateway to SSI internals** — predicate locks, dangerous structures, rw-dependency cycles.

## Common beginner confusion

- "Postgres RR prevents write skew." It doesn't. Snapshot isolation is *not* serializable.
- "Lost update and write skew are the same." Different — same row vs different rows.
- "SERIALIZABLE means single-threaded execution." It means *equivalent to* some serial order. Postgres SSI still runs concurrently; only aborts the loser.
- "If both writes succeed without error, the data is correct." False — write skew commits cleanly and silently corrupts.
- "Add a unique index." Unique indexes work for "no two of these can exist". Write skew is "at least one must exist after both updates" — different shape.

## Brute force approach

`LOCK TABLE oncall IN EXCLUSIVE MODE` at the start of every transaction. Works; throughput dies. Don't.

## Optimal approach

Four real options ranked by elegance:

1. **`SELECT ... FOR UPDATE` on the read set** — pessimistic row locks on every row the decision depends on. Works at any isolation level.
2. **SERIALIZABLE (Postgres SSI)** — let the engine detect rw-cycles and abort one. Retry on 40001.
3. **Materialise the invariant** into a single row both transactions must UPDATE. Converts write skew into a write-write conflict, which any engine catches.
4. **Constraint trick** — sometimes you can express the invariant as a CHECK or exclusion constraint that physically blocks the bad state.

## Solution

```sql
-- ============================================================
-- Reproduce in Postgres at REPEATABLE READ (snapshot isolation)
-- ============================================================

CREATE TABLE oncall (
  name    TEXT PRIMARY KEY,
  on_duty BOOLEAN NOT NULL
);
INSERT INTO oncall VALUES ('Alice', true), ('Bob', true);

-- Session A (T1)
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT count(*) FROM oncall WHERE on_duty;   -- 2

-- Session B (T2)
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT count(*) FROM oncall WHERE on_duty;   -- 2

-- Session A
UPDATE oncall SET on_duty = false WHERE name = 'Alice';
COMMIT;

-- Session B
UPDATE oncall SET on_duty = false WHERE name = 'Bob';
COMMIT;

-- Final state: 0 doctors. Invariant violated. No error raised.

-- ============================================================
-- Fix #1: SERIALIZABLE — SSI detects rw-cycle
-- ============================================================
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT count(*) FROM oncall WHERE on_duty;
UPDATE oncall SET on_duty = false WHERE name = 'Alice';
COMMIT;
-- One of T1/T2 raises ERROR: could not serialize access (40001).
-- App retries the loser.

-- ============================================================
-- Fix #2: pessimistic FOR UPDATE on the read set
-- ============================================================
BEGIN;  -- RC is fine
SELECT name FROM oncall WHERE on_duty FOR UPDATE;  -- locks Alice & Bob
-- Now T2's FOR UPDATE blocks until T1 commits.
UPDATE oncall SET on_duty = false WHERE name = 'Alice';
COMMIT;
-- T2 wakes, re-reads (Alice is now off, count = 1), and its check rejects the off-duty request.

-- ============================================================
-- Fix #3: materialise the invariant into a single row
-- ============================================================
CREATE TABLE counters (name TEXT PRIMARY KEY, val INT NOT NULL);
INSERT INTO counters VALUES ('oncall', 2);

-- Off-duty request:
UPDATE counters SET val = val - 1 WHERE name = 'oncall' AND val > 1;
-- If rowcount = 0, refuse. Two concurrent UPDATEs serialise on the row X lock.
UPDATE oncall SET on_duty = false WHERE name = 'Alice';

-- ============================================================
-- Fix #4: constraint expressing the invariant (when possible)
-- ============================================================
-- Add a trigger or use a deferred CHECK on the count.
-- Sometimes possible with exclusion constraints (e.g., schedule overlap).
CREATE TABLE bookings (
  room  INT,
  range TSRANGE,
  EXCLUDE USING gist (room WITH =, range WITH &&)
);
```

App-side retry loop for SSI:

```javascript
async function withSSIRetry(fn, attempts = 3) {
  for (let i = 0; i < attempts; i++) {
    try { return await fn(); }
    catch (e) {
      if (e.code === '40001') {
        await new Promise(r => setTimeout(r, 50 * (1 << i)));
        continue;
      }
      throw e;
    }
  }
  throw new Error('SSI_RETRY_EXHAUSTED');
}
```

## Step-by-step dry run

T1/T2 timeline at REPEATABLE READ (broken):

```
time →

T1 (Alice):  |--BEGIN RR--|--SELECT count=2--|----------------|--UPDATE Alice=off--|--COMMIT--|
                          (snapshot fixed)                     (writes different row)
T2 (Bob):       |--BEGIN RR--|--SELECT count=2--|--UPDATE Bob=off--|--COMMIT--|
                             (same snapshot view)

Read sets:   T1={Alice on, Bob on}    T2={Alice on, Bob on}    OVERLAP
Write sets:  T1={Alice}                T2={Bob}                  DISJOINT
Invariant:   on_duty count ≥ 1
After both COMMIT: count = 0. VIOLATED.

Why no error: there's no row both updated; nothing for the row X lock to catch.
RR's snapshot is irrelevant — both made internally consistent decisions; the *interleaving* is the bug.
```

Same timeline at SERIALIZABLE (Postgres SSI):

```
T1 (Alice):  |--BEGIN SER--|--SELECT count=2 (SIREAD lock on predicate)--|--UPDATE Alice (rw edge w/ T2's read)--|--COMMIT--|
T2 (Bob):       |--BEGIN SER--|--SELECT count=2 (SIREAD lock)--|--UPDATE Bob (rw edge w/ T1's read)--|--COMMIT 40001--|

SSI tracks:
  T1 read Bob's row    ⟶ T2 wrote Bob's row    : rw edge T1 → T2
  T2 read Alice's row  ⟶ T1 wrote Alice's row  : rw edge T2 → T1
  CYCLE → dangerous structure → abort one.

App retries the aborted transaction at the new state (count=1) → its check rejects → "can't go off duty, only one on call".
```

Same timeline with FOR UPDATE on read set:

```
T1:  |--BEGIN--|--SELECT FOR UPDATE on {Alice, Bob}--|--UPDATE Alice=off--|--COMMIT--|
T2:   |--BEGIN--|--SELECT FOR UPDATE waits for T1--|......................|--proceeds: SELECT sees count=1--|--check: "1 ≥ 1 but cannot go below"--|--reject or COMMIT depending on check--|
```

Allowed at: RU, RC, RR (both Postgres and MySQL). Prevented at: SERIALIZABLE (Postgres SSI), or RC/RR with `FOR UPDATE` on the read set.

## How to think aloud in the interview

> "Write skew is the senior anomaly. Two transactions read overlapping data, each makes a decision, each writes a *different* row, the combination violates an invariant that neither transaction's individual decision would have broken. The classic is doctor-on-call: both see 'two doctors on duty', both go off duty, invariant 'at least one on call' breaks.
>
> The critical distinction: **snapshot isolation doesn't catch this**. Postgres RR allows it. There's no row both write, so no row lock fires.
>
> Four fixes:
> 1. **SERIALIZABLE (Postgres SSI)** — engine detects rw-cycle, aborts one with 40001; need retry.
> 2. **`SELECT FOR UPDATE` on the read set** — pessimistic lock on every row the decision depends on; second transaction blocks.
> 3. **Materialise the invariant** into a single counter row that both UPDATE — converts to write-write conflict.
> 4. **Express as a DB constraint** (exclusion constraint, CHECK) when possible.
>
> I default to SSI for low-frequency hot paths, FOR UPDATE for high-contention paths where retry cost is prohibitive."

## Important takeaways

- Write skew = overlapping reads, disjoint writes, broken invariant.
- Snapshot isolation (Postgres RR) does *not* prevent it.
- Only SERIALIZABLE prevents it implicitly; otherwise lock the read set or materialise the invariant.
- Postgres SSI = snapshot + dependency tracking; aborts on rw-cycle with 40001.
- MySQL doesn't have SSI; you must use FOR UPDATE or materialise.
- Production examples: doctor on-call, joint account overdraft, meeting-room double-book via different paths.

## Variants

1. **Joint account overdraft.** Two cardholders, balance $100, both withdraw $80 simultaneously. Each individual decision valid. Combined: -$60. Same anomaly, same fixes.
2. **Inventory across multiple SKUs**: rule "total reserved ≤ warehouse capacity"; each booking reserves a different SKU.
3. **MySQL workaround**: no SSI; you must use `FOR UPDATE` or move the invariant to a single row.
4. **Microservices write skew**: each service holds part of the invariant; needs a saga with a guard condition.
5. **`SELECT FOR KEY SHARE`** — lighter lock that prevents the FK target from being deleted but allows non-key updates. Sometimes enough for FK-based invariants.

## Revision notes

> **write-skew — 60 second recap**
> - Overlapping reads, disjoint writes, broken invariant. Two doctors go off; invariant "≥1 on call" breaks.
> - **Postgres RR (snapshot isolation) does NOT prevent it.** Senior trap.
> - **Only SERIALIZABLE (Postgres SSI) prevents implicitly**, with retry on 40001.
> - Alternatives: `FOR UPDATE` on read set; materialise invariant into one row; DB constraint.
> - Conflict graph: rw cycle between T1 and T2 — that's what SSI detects.
> - Distinct from lost update (same row) — write skew is different rows.
> - MySQL: no SSI; must use FOR UPDATE or materialisation.
