# Reproduce a lost update (read-modify-write race) and fix it three ways

## Source / Origin
- The single most common concurrency bug in production interactive code.
- Not in the original ANSI four — added to the SQL standard later.
- Concept reference: `backend-data-prep/sql/07-isolation-levels.md`, `08-locks-concurrency.md`.

## Why this question matters in interviews
Every ORM tutorial ships this bug. `user = User.find(1); user.balance -= 10; user.save()` is *exactly* a lost-update race. Interviewers ask this because (a) every backend engineer has shipped it at least once, and (b) the three fixes — conditional UPDATE, `FOR UPDATE`, and optimistic version column — map cleanly to "pick your concurrency model". A senior candidate doesn't just name the fixes; they pick the right one based on conflict probability and latency budget.

## Concepts involved

### Syntax to lock in

```sql
-- The race (read-modify-write across two sessions)
SELECT qty FROM inventory WHERE id=5;  -- T1 sees 100
SELECT qty FROM inventory WHERE id=5;  -- T2 sees 100
UPDATE inventory SET qty = 99 WHERE id=5;  -- T1 writes
UPDATE inventory SET qty = 99 WHERE id=5;  -- T2 writes — T1's decrement is lost

-- Fix #1: conditional UPDATE (cheapest)
UPDATE inventory SET qty = qty - 1 WHERE id=5 AND qty > 0;
-- The row lock the engine takes for UPDATE serialises the two writes.

-- Fix #2: pessimistic
BEGIN;
SELECT qty FROM inventory WHERE id=5 FOR UPDATE;
UPDATE inventory SET qty = ... WHERE id=5;
COMMIT;

-- Fix #3: optimistic version column
UPDATE inventory SET qty = $new, version = version + 1
WHERE id=5 AND version = $expected;
-- 0 rows affected → someone else won → refetch + retry
```

### Edge cases / interview traps

1. **Postgres RR does *not* silently merge lost updates.** It aborts the second writer with `could not serialize access` (40001). You still need a retry. RR isn't a "fix that ships" — it's "fix that fires an error you must handle".
2. **`FOR UPDATE` in autocommit is useless** — the lock releases the moment the SELECT returns. Wrap in `BEGIN; ... COMMIT;`.
3. **Conditional UPDATE is not the same as SELECT then UPDATE** even if the WHERE clause is identical. The latter has a race window; the former runs the check inside the UPDATE's row lock.
4. **ORM `find + save` is the canonical bug.** `User.find(1); user.balance -= 10; user.save()` reads in one statement, writes in another, with a network round-trip + business logic in between. Every existing race.
5. **Version column requires a retry loop.** Without it, the user sees "save failed"; with it, the system silently re-applies the logic against the new version.
6. **The "decrement in SQL" trick only works when the math commutes.** `qty = qty - 1` is safe at the SQL level. `qty = some_complex_calc(qty)` is not — push only the commutative operation, then re-check in app.

## Mental Model

The **"two people editing the same Google Doc paragraph"** model. Both copy the paragraph into a draft buffer, both edit, both hit save. Google Docs has OT/CRDT to merge; SQL doesn't. The second `save()` overwrites the first.

```
   t0 — DB: qty = 100
   t1 — T1 reads qty=100; computes 100-30=70
   t2 — T2 reads qty=100; computes 100-50=50
   t3 — T1 writes qty=70
   t4 — T2 writes qty=50      ← T1's decrement is lost
   t5 — DB: qty = 50 (should be 20)
```

Three fixes, three philosophies:
- **Push the math into SQL** (cheapest, requires commutativity).
- **Lock the row before reading** (pessimistic, blocks).
- **Detect the conflict at write time** (optimistic, retries).

## Why interviewers care

- They want to confirm you know the **single most common ORM bug**.
- They want you to **rank the fixes by cost/contention**, not just list them.
- They want you to mention **rowcount==0** as the signal — the most common implementation slip is forgetting to check.

## Common beginner confusion

- "Transactions fix this." A transaction alone doesn't — both transactions read the same value before either writes. You need an explicit lock, conditional UPDATE, or version column.
- "Higher isolation fixes this." Only SERIALIZABLE (or RR with abort-on-conflict) — both still need application retry.
- "If the math is `+=` it's atomic." Not in app code. `user.x += 1; user.save()` is read-then-write across the wire. Atomic only if expressed as SQL `SET x = x + 1`.
- "MVCC means writers don't conflict." Wrong. MVCC means readers don't block writers; *writers still take row X locks against other writers*.

## Brute force approach

`SELECT ... FOR UPDATE` everywhere. Works, but hammers throughput on hot rows. For low-conflict workloads it's overkill.

## Optimal approach

Decision tree by conflict probability:

- **Math commutes (counter, decrement)** → conditional UPDATE. `UPDATE t SET x = x - 1 WHERE id=? AND x > 0`. Check rowcount.
- **Complex multi-field decision, high contention** → pessimistic. `SELECT ... FOR UPDATE`.
- **Complex decision, low contention** → optimistic. Version column + retry.

## Solution

```sql
-- ============================================================
-- Reproduce in Postgres at READ COMMITTED
-- ============================================================

CREATE TABLE inventory (id INT PRIMARY KEY, qty INT);
INSERT INTO inventory VALUES (5, 100);

-- Session A
BEGIN;
SELECT qty FROM inventory WHERE id=5;            -- 100

-- Session B
BEGIN;
SELECT qty FROM inventory WHERE id=5;            -- 100

-- Session A
UPDATE inventory SET qty=99 WHERE id=5;          -- thinks 100-1=99
COMMIT;

-- Session B
UPDATE inventory SET qty=99 WHERE id=5;          -- also thinks 100-1=99
COMMIT;

-- Final: qty=99. Two decrements applied, one lost.

-- ============================================================
-- Fix #1: conditional UPDATE (cheapest, no app-side retry)
-- ============================================================
UPDATE inventory SET qty = qty - 1 WHERE id=5 AND qty > 0;
-- The X lock the engine takes serialises concurrent UPDATEs.
-- Each runs against the *latest* committed value.
-- Postgres at RC: this is the canonical pattern.

-- ============================================================
-- Fix #2: pessimistic lock
-- ============================================================
BEGIN;
SELECT qty FROM inventory WHERE id=5 FOR UPDATE;  -- acquires X lock
-- T2's SELECT FOR UPDATE blocks here
-- ... compute new qty ...
UPDATE inventory SET qty = $new WHERE id=5;
COMMIT;  -- releases lock; T2 wakes up, re-reads the latest qty

-- ============================================================
-- Fix #3: optimistic version column
-- ============================================================
ALTER TABLE inventory ADD COLUMN version INT NOT NULL DEFAULT 0;

-- Read
SELECT qty, version FROM inventory WHERE id=5;   -- (100, 7)

-- Write (only succeeds if version unchanged)
UPDATE inventory SET qty = $new, version = version + 1
WHERE id=5 AND version = 7;
-- rowcount == 0 → conflict; refetch and retry
```

Node.js retry wrapper for optimistic:

```javascript
async function updateWithRetry(id, mutator, attempts = 3) {
  for (let i = 0; i < attempts; i++) {
    const { qty, version } = await db.one(
      'SELECT qty, version FROM inventory WHERE id=$1', [id]
    );
    const newQty = mutator(qty);
    const { rowCount } = await db.result(
      `UPDATE inventory SET qty=$1, version=version+1
       WHERE id=$2 AND version=$3`,
      [newQty, id, version]
    );
    if (rowCount === 1) return newQty;
    // someone won the race; retry
  }
  throw new Error('OPTIMISTIC_RETRY_EXHAUSTED');
}
```

## Step-by-step dry run

T1/T2 timeline at READ COMMITTED (the broken version):

```
time →

T1:  |--BEGIN--|--R(qty)=100--|------------|--compute 99--|--W(qty=99)--|--COMMIT--|
T2:           |--BEGIN--|--R(qty)=100--|------------|--compute 99--|--W(qty=99)--|--COMMIT--|

Operations applied: -1, -1
Net effect:         -1
DB final state:     qty = 99 (should be 98)
```

Same timeline with conditional UPDATE (fix #1):

```
T1:  |--BEGIN--|--UPDATE qty=qty-1 (X lock acquired)--|--COMMIT--|
T2:           |--BEGIN--|--UPDATE qty=qty-1 (waits for T1's lock)--|--re-reads after T1 commits--|--applies -1 to 99 = 98--|--COMMIT--|

DB final state: qty = 98. Correct.
The trick: at RC, an UPDATE waiting on a row lock RE-READS the row after the lock releases.
This is called "EvalPlanQual" in Postgres — the UPDATE sees the latest committed value.
```

Same timeline with optimistic version column (fix #3):

```
T1:  |--R(qty=100, ver=7)--|--UPDATE WHERE ver=7 (1 row)--|--COMMIT--|
T2:    |--R(qty=100, ver=7)--|--UPDATE WHERE ver=7 (0 rows!)--|--detect conflict--|--re-read (qty=99, ver=8)--|--retry--|
```

Allowed at: RU, RC. Prevented at: RR (with abort on conflict — Postgres), SER. Best fixes are pattern-level, not isolation-level.

## How to think aloud in the interview

> "Lost update is the read-modify-write race. T1 and T2 both read the same value, both compute a new value in app code, both write. The second write silently obliterates the first. Three fixes ranked by cost:
> 1. **Conditional UPDATE in SQL** — if the math commutes, push it: `UPDATE t SET qty = qty - 1 WHERE id=? AND qty > 0`. The X lock UPDATE takes serialises the two writers. Check rowcount.
> 2. **`SELECT FOR UPDATE`** — when the decision is complex, lock the row before reading. Blocks the second reader behind the first writer.
> 3. **Optimistic version column** — read `(value, version)`, write `WHERE version = $expected`. On rowcount=0, retry. Best when conflicts are rare.
> I default to fix #1 for counters and decrements, fix #2 for transfers, fix #3 for last-write-wins on high-cardinality records like product edits."

## Important takeaways

- The most common ORM bug. `find + mutate + save` is a race at RC.
- Push commutative math into SQL with conditional UPDATE.
- Pessimistic = `FOR UPDATE` in a transaction.
- Optimistic = version column + retry loop.
- Always check **rowcount==0** — that's how you detect the conflict.
- Postgres RR aborts the loser with 40001 — still need retry.

## Variants

1. **"Same problem with money transfer between two accounts."** Add lock ordering: always lock `LEAST(from, to)` first to avoid deadlock.
2. **"Counter row is a hotspot, retries thunder."** Re-design: per-shard counters with periodic aggregation, or move to Redis INCR with periodic DB flush.
3. **Compare-And-Swap analogy.** Optimistic version column is exactly the database equivalent of CAS in concurrent programming.
4. **`UPSERT` race.** Same anomaly, different shape: SELECT-then-INSERT-or-UPDATE races; fix with `INSERT ... ON CONFLICT DO UPDATE`.
5. **Distributed lost update.** Microservices each holding a copy of the value — needs a single source of truth + idempotency key, not just a DB-level fix.

## Revision notes

> **lost-update — 60 second recap**
> - Read-modify-write race; T2's write overwrites T1's. Two decrements → one effect.
> - Allowed at RC. Not in ANSI four; added later.
> - **Fix #1 (cheapest)**: conditional UPDATE pushing math into SQL. Row X lock serialises writers.
> - **Fix #2**: `SELECT ... FOR UPDATE` inside an explicit transaction.
> - **Fix #3**: optimistic version column + retry on rowcount=0.
> - ORM `find + save` is the canonical occurrence. Every backend has shipped this once.
> - Postgres RR aborts second writer with 40001 — fix #3 in disguise, still need retry.
