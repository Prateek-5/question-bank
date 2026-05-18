# Given an anomaly, identify the minimum isolation level that prevents it

## Source / Origin
- Standard senior backend round opener at fintech, marketplaces, payments orgs.
- Variants: "I saw this behaviour in prod — name the anomaly, name the level."
- Companion concept file: `backend-data-prep/sql/07-isolation-levels.md`.

## Why this question matters in interviews
This is the single highest-signal database question for a senior round. It separates engineers who memorised the ANSI table from engineers who can **reason from an observed symptom back to a root cause**. Most production data-corruption tickets arrive as a bug report ("the count was wrong", "the booking double-confirmed"). Your job is to translate that into a known anomaly, then name the smallest isolation level that would have prevented it — and the cheapest fix that doesn't require globally bumping the level.

You will be given a T1/T2 timeline (or a screenshot of a Slack thread) and asked: *what isolation level is this running at, and what should it be?* You have ~60 seconds.

## Concepts involved

### Syntax to lock in

```sql
-- Postgres
BEGIN ISOLATION LEVEL READ COMMITTED;   -- default
BEGIN ISOLATION LEVEL REPEATABLE READ;  -- snapshot isolation
BEGIN ISOLATION LEVEL SERIALIZABLE;     -- SSI (may abort with 40001)

-- MySQL
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;  -- default
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

The anomaly → minimum level table (memorise this exact order):

| Anomaly | Min level that prevents it (Postgres) | Notes |
|---|---|---|
| Dirty read | READ COMMITTED | Postgres has no true RU; RU is aliased to RC. |
| Non-repeatable read | REPEATABLE READ | Snapshot taken at first read. |
| Phantom read | REPEATABLE READ (Postgres) / REPEATABLE READ (MySQL via gap locks) | Postgres RR prevents phantom *reads*; can still produce write skew. |
| Lost update | RC + `FOR UPDATE` / RR / SER | Application-level race; row lock or version column. |
| Write skew | SERIALIZABLE (SSI) | Only SER catches it without explicit `FOR UPDATE`. |
| Read skew (across rows) | REPEATABLE READ | Snapshot consistency across multiple SELECTs. |

### Edge cases / interview traps

1. **Postgres RR ≠ MySQL RR.** Postgres RR is pure snapshot isolation — phantom *reads* are blocked, but write skew over a predicate is still possible. MySQL InnoDB RR uses gap locks, so it also blocks the *insert* that would produce the phantom.
2. **READ UNCOMMITTED in Postgres** silently maps to READ COMMITTED. Saying "set it to RU" buys you nothing.
3. **Lost update is not in the ANSI table** — it's an application-level race. Don't say "RR prevents lost update" without qualifying that Postgres RR will *abort* the second writer with `could not serialize access` (SQLSTATE 40001) — it doesn't silently merge.
4. **Serializable doesn't mean serial execution** — it means equivalent to *some* serial order. The engine still runs them concurrently and aborts on conflict.
5. **`SELECT FOR UPDATE` upgrades a single row's effective isolation** without changing the session level. The trap is to recommend "bump to SERIALIZABLE" when a targeted row lock is cheaper.
6. **Read skew across rows** is what most candidates miss — T1 reads row A (consistent), then row B (already mutated by T2). Foreign-key-coupled rows look inconsistent. Fixed by RR's snapshot.

## Mental Model

Think of it as a **two-column decision card**: left column is "what bad thing happened?", right column is "what's the cheapest dial setting that would have stopped it?". You match the symptom, you read off the level. The trick is the second column also asks: *do I bump the level globally, or do I add a row lock / unique constraint / version column?* Bumping the level is the heavy answer; the senior answer is the targeted fix.

```
   anomaly             cheapest fix          fallback (global)
   ─────────           ────────────          ─────────────────
   dirty read       →  RC (default)       →  any
   non-rep read     →  RR snapshot        →  application-side cache once
   phantom          →  UNIQUE INDEX       →  RR (MySQL) / SSI (PG)
   lost update      →  conditional UPDATE →  FOR UPDATE / version col
   write skew       →  SERIALIZABLE       →  FOR UPDATE on the read set
```

## Why interviewers care

They want to test whether you can **work backwards from symptom to cause**. Anyone can recite the four levels. Few can look at a real timeline and say "that's read skew at READ COMMITTED — bump to REPEATABLE READ or take the FK rows in one snapshot". The interviewer is also probing whether you'll over-prescribe (bump everything to SERIALIZABLE) or under-prescribe (claim the ORM handles it).

## Common beginner confusion

- "Higher isolation is always safer" — yes, but it costs throughput and may convert silent corruption into noisy aborts your app must retry.
- "Postgres RR prevents phantoms" — it prevents phantom *reads* in the snapshot, but it does *not* prevent write skew built from those phantoms.
- "Serializable means one-at-a-time" — it means *equivalent to* some serial order; the engine runs concurrently and aborts the loser.
- "READ UNCOMMITTED is fast" — in Postgres it's the same as RC. In other DBs the speedup is marginal vs the correctness loss.

## Brute force approach

Bump everything to SERIALIZABLE. Done. This is wrong because:
- Postgres SSI aborts with 40001 — your app must retry, which most apps don't.
- MySQL SERIALIZABLE adds an S lock on every read — read-heavy workloads collapse.
- You haven't actually *identified* the anomaly, you've just paid for the worst case.

## Optimal approach

A two-step diagnostic:

1. **Classify the anomaly.** Look at the timeline. Ask:
   - Did T2 read T1's *uncommitted* data? → dirty read.
   - Did T1 read the *same row* twice and see different values? → non-repeatable read.
   - Did T1 run the *same predicate* twice and see new rows? → phantom.
   - Did two writers both decrement and one loss? → lost update.
   - Did two writers read overlapping data, write *different* rows, and break an invariant? → write skew.
   - Did T1 read row A and row B and they're mutually inconsistent? → read skew.
2. **Pick the cheapest fix.** Prefer targeted: unique index, conditional UPDATE, FOR UPDATE, version column. Bump the level only if the constraint can't be expressed as a row-local invariant.

## Solution

```sql
-- Symptom: "I see different values reading the same row twice"
-- Diagnosis: non-repeatable read at READ COMMITTED
-- Fix (targeted):
BEGIN ISOLATION LEVEL REPEATABLE READ;
  SELECT balance FROM accounts WHERE id = 1;   -- 100
  -- ... other work; another tx commits balance=50 ...
  SELECT balance FROM accounts WHERE id = 1;   -- still 100 (snapshot)
COMMIT;

-- Symptom: "two transfers from the same account, end balance is negative"
-- Diagnosis: lost update under RC
-- Fix #1 (cheapest): conditional UPDATE
UPDATE accounts SET balance = balance - $amount
WHERE id = $id AND balance >= $amount;
-- Check rows-affected; if 0 → insufficient funds

-- Fix #2: explicit row lock
BEGIN;
  SELECT balance FROM accounts WHERE id = $id FOR UPDATE;
  -- compute
  UPDATE accounts SET balance = $new WHERE id = $id;
COMMIT;

-- Symptom: "doctor-on-call invariant violated, both went off duty"
-- Diagnosis: write skew at REPEATABLE READ (Postgres snapshot isolation)
-- Fix: SERIALIZABLE + retry on 40001
BEGIN ISOLATION LEVEL SERIALIZABLE;
  SELECT count(*) FROM oncall WHERE status='on';   -- read set
  UPDATE oncall SET status='off' WHERE name='Alice';
COMMIT;  -- may raise 40001; app retries
```

## Step-by-step dry run

**Scenario given by interviewer:** "We have two payment endpoints. They both run `SELECT balance; if balance >= amount then UPDATE balance = balance - amount`. Two concurrent calls at $100 each, balance starts at $150. End state: balance = -$50."

Trace:
```
time →
T1:  |--BEGIN--|--SELECT bal=150--|--check 150>=100 ✓--|--UPDATE bal=50--|--COMMIT--|
T2:           |--BEGIN--|--SELECT bal=150--|--check 150>=100 ✓--|--UPDATE bal=-50--|--COMMIT--|
```

Diagnosis (out loud): "Both transactions read 150, both passed the application check, both wrote. The second write was a *lost update*: T2's UPDATE doesn't know T1 changed the row. At READ COMMITTED with a read-then-update pattern, this is expected. The fix is **not** to bump isolation — it's to push the check into the UPDATE: `UPDATE accounts SET balance = balance - 100 WHERE id = 1 AND balance >= 100`. The row lock for UPDATE serialises the two writers; the second one gets rowcount=0 and errors as 'insufficient funds'."

## How to think aloud in the interview

> "OK, two transactions, both saw balance 150, both wrote. The classic anomaly is **lost update** — neither saw the other's write. Three fixes ranked by cost:
> 1. **Push the check into the UPDATE** with `WHERE balance >= 100`. The row lock that UPDATE takes serialises the two writers. Cheapest, no isolation bump.
> 2. **`SELECT … FOR UPDATE`** before the read. Blocks the second reader behind the first writer.
> 3. **SERIALIZABLE** — works but costs more (Postgres SSI will abort one with 40001; need retry).
> I'd ship fix #1. It's a one-line change, no retry logic, works at the default RC."

For write skew: "Both read overlapping set, both wrote different rows, invariant broke. Only SERIALIZABLE catches this without explicit row locks on the read set. Cost is retry on 40001."

For dirty read: "Postgres doesn't even allow this — RU maps to RC. So I'd ask what DB. If MySQL or SQL Server, prevent with RC default."

## Important takeaways

- **Anomaly → level table is not the answer**; it's the lookup. The answer is "anomaly → cheapest targeted fix; level is the fallback."
- **Postgres RR = snapshot isolation**, not the same as MySQL RR. Always specify the engine.
- **Lost update is not an ANSI anomaly** — it's an application race fixed by row lock, conditional UPDATE, or version column.
- **Write skew is the senior question.** Only SERIALIZABLE prevents it implicitly; otherwise you must lock the read set or materialise the constraint.
- The senior signal is choosing the **smallest fix** that works, not the strongest level.

## Variants

1. **"Same anomaly in MySQL — different answer?"** Yes — MySQL RR uses gap locks, so it blocks phantoms (Postgres RR doesn't). Be ready to switch engines mid-question.
2. **"What if I use `FOR UPDATE` at RC — is that as strong as SERIALIZABLE?"** Only for the locked row(s). For multi-row invariants you need to lock every row in the read set.
3. **"Show me the SQL state codes."** Postgres: `40001` serialization_failure, `40P01` deadlock_detected. MySQL: `1213` deadlock, `1205` lock wait timeout.
4. **"Spanner/CockroachDB do SERIALIZABLE by default — why?"** They use HLC + Paxos so the abort cost is low; they trade aborts for simpler app reasoning.

## Revision notes

> **identify-isolation — 60 second recap**
> - Dirty read → RC (free in Postgres)
> - Non-repeatable read → RR
> - Phantom → RR (PG: snapshot; MySQL: gap locks) or UNIQUE INDEX
> - Lost update → conditional UPDATE / FOR UPDATE / version column
> - Write skew → SERIALIZABLE (only) or FOR UPDATE on read set
> - Read skew across rows → RR snapshot
> - Postgres SSI: retry on `40001`. MySQL RR: gap locks may surprise INSERTs.
> - **Senior answer = smallest fix that works.** Bump level only when no row-level invariant captures the rule.
