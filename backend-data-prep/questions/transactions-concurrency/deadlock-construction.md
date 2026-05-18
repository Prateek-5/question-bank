# Construct a deadlock from two SQL sessions and show the cycle

## Source / Origin
- The canonical "produce one in two psql sessions" interview challenge.
- Concept reference: `backend-data-prep/sql/08-locks-concurrency.md`.
- Real-world: every backend engineer has shipped a deadlock; the senior signal is reproducing one deterministically.

## Why this question matters in interviews
Interviewers love this because it requires you to (a) understand row locks, (b) draw the wait-for graph, (c) reason about lock acquisition order, and (d) explain how the engine detects the cycle. If you can sit at a whiteboard with two columns and walk through the four-step deadlock, you signal real database literacy. If you only know "deadlocks happen, retry them", you signal junior.

## Concepts involved

### Syntax to lock in

```sql
-- Two-row deadlock (classic)
-- Session 1
BEGIN; UPDATE t SET v=v+1 WHERE id=1;   -- holds X lock on row 1
-- Session 2
BEGIN; UPDATE t SET v=v+1 WHERE id=2;   -- holds X lock on row 2
-- Session 1
UPDATE t SET v=v+1 WHERE id=2;          -- waits for session 2
-- Session 2
UPDATE t SET v=v+1 WHERE id=1;          -- waits for session 1 → DEADLOCK
-- DB picks a victim: ERROR: deadlock detected (Postgres SQLSTATE 40P01, MySQL 1213)

-- Inspect blocking (Postgres)
SELECT
  blocked.pid AS blocked_pid, blocked.query,
  blocking.pid AS blocking_pid, blocking.query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
  ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));
```

### Edge cases / interview traps

1. **Postgres deadlock_timeout is 1 second by default.** The deadlock detector doesn't run on every lock-wait — only after a tx has been waiting for `deadlock_timeout` ms. Lower timeout = faster detection but more CPU; default 1s is fine.
2. **MySQL detects on every lock-wait** — instant detection, slightly higher overhead.
3. **The victim choice is implementation-defined.** Postgres usually picks the youngest / least work done; MySQL picks the smallest transaction. Don't depend on which one dies.
4. **3-way deadlocks exist.** T1 → T2 → T3 → T1 wait-for cycle. Same detection, same resolution.
5. **`SELECT ... FOR UPDATE` is the classic ingredient** for deadlocks in payments — two transfers in opposite directions.
6. **DDL deadlocks**: `ALTER TABLE` taking ACCESS EXCLUSIVE behind a long SELECT can deadlock with a writer. Watch out for migration timing.
7. **Index-order matters**: InnoDB locks index records; if your queries use different indexes, the lock order varies even with consistent app-level order. Senior trap.

## Mental Model

The **"two librarians, two books"** model. Librarian A grabs Volume 1, then walks toward Volume 2. Librarian B grabs Volume 2, then walks toward Volume 1. Both stop, frozen, each waiting for the other to put their book back. The library manager walks by, sees the stalemate, taps one on the shoulder: "Put it down. Try again."

```
   Wait-for graph (the canonical cycle):

        Holds row 1
   ┌─────────────────┐
   │      T1         │
   │ wants row 2     │
   └────────┬────────┘
            │ waits for
            ▼
   ┌─────────────────┐
   │      T2         │
   │ holds row 2     │
   │ wants row 1     │
   └────────┬────────┘
            │ waits for
            ▼
        (back to T1)
   CYCLE → deadlock detected → abort victim
```

Three-way deadlock looks identical with one more node: T1 → T2 → T3 → T1.

## Why interviewers care

- Tests your **mechanical understanding** of locks: acquire, wait, cycle.
- Probes your **debugging vocabulary**: pg_blocking_pids, deadlock_timeout, SQLSTATE codes.
- Asks you to **predict the symptom**: which session dies, what error code, how to retry.

## Common beginner confusion

- "Deadlock means my DB is broken." It means two transactions acquired locks in inconsistent order. The DB handled it; the bug is your code's lock-order pattern.
- "Deadlocks happen randomly." They happen *deterministically* given a lock-order pattern + concurrent traffic. They appear random because traffic shape varies.
- "Retry forever." Retry with backoff, capped attempts. Otherwise you'll oscillate.
- "Set the isolation level higher." Doesn't help — deadlocks happen at every level once locks are in play.
- "`SELECT FOR UPDATE` causes deadlocks." Only if acquired in inconsistent order. Same lock, consistent order: no deadlock.

## Brute force approach

Avoid all multi-row transactions. Useless — most business logic touches multiple rows.

## Optimal approach

Two-pronged prevention + recovery:

1. **Consistent lock order.** Always lock rows in deterministic order (e.g., by ID ascending). Eliminates the cycle structurally.
2. **Application-level retry** on deadlock error (40P01 / 1213). Capped retries with backoff.
3. **Shorter transactions** = smaller window for cycles to form.
4. **Use SKIP LOCKED for queues** to avoid head-of-line blocking that can degenerate into deadlocks.

## Solution

```sql
-- ============================================================
-- Reproduce a deterministic 2-row deadlock
-- ============================================================
CREATE TABLE t (id INT PRIMARY KEY, v INT);
INSERT INTO t VALUES (1, 0), (2, 0);

-- Run in two psql sessions side by side
-- ────────────────────────────────────────
-- Session 1                  │  Session 2
-- ────────────────────────────────────────
BEGIN;                        │
                              │  BEGIN;
UPDATE t SET v=v+1            │
  WHERE id=1;                 │  UPDATE t SET v=v+1
                              │    WHERE id=2;
-- Both hold their own row's X lock. Now cross-lock:
UPDATE t SET v=v+1            │
  WHERE id=2;     (waits)     │  UPDATE t SET v=v+1
                              │    WHERE id=1;  (waits)
                              │  -- ~1 sec later:
                              │  ERROR: deadlock detected
                              │  DETAIL: Process 12345 waits for ShareLock
                              │          on transaction 6789;
                              │          blocked by process 23456.
                              │  ROLLBACK
                              │
-- Session 1 proceeds, COMMIT.

-- ============================================================
-- Fix: consistent lock order
-- ============================================================
-- Always lock in id ASC order. Both transactions:
BEGIN;
SELECT id FROM t WHERE id IN (1, 2) ORDER BY id FOR UPDATE;
-- Both grab row 1's lock first; the second one waits. No cycle possible.
UPDATE t SET v=v+1 WHERE id=1;
UPDATE t SET v=v+1 WHERE id=2;
COMMIT;

-- ============================================================
-- Diagnose a stuck deadlock (Postgres)
-- ============================================================
SELECT
  blocked.pid AS blocked_pid,
  blocked.query AS blocked_query,
  blocking.pid AS blocking_pid,
  blocking.query AS blocking_query,
  now() - blocked.query_start AS blocked_for
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking
  ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE blocked.wait_event_type = 'Lock';
```

App-side retry wrapper:

```javascript
async function txWithDeadlockRetry(fn, attempts = 3) {
  for (let i = 0; i < attempts; i++) {
    try { return await fn(); }
    catch (e) {
      if (e.code === '40P01' /* Postgres deadlock */ ||
          e.code === 'ER_LOCK_DEADLOCK' /* MySQL 1213 */) {
        await new Promise(r => setTimeout(r, 50 * (1 << i) * Math.random()));
        continue;
      }
      throw e;
    }
  }
  throw new Error('DEADLOCK_RETRY_EXHAUSTED');
}
```

## Step-by-step dry run

T1/T2 timeline of the 2-row deadlock:

```
time →

T1:  |--BEGIN--|--UPDATE id=1 (X1 acquired)--|--UPDATE id=2 (waits for X2 held by T2)----------|--proceed after T2 dies--|--COMMIT--|
T2:           |--BEGIN--|--UPDATE id=2 (X2)--|--UPDATE id=1 (waits for X1 held by T1)--|--deadlock! abort--|--ROLLBACK--|

Wait-for graph evolution:
  t=0:  empty
  t=1:  T1 holds X1
  t=2:  T2 holds X2
  t=3:  T1 → T2 (T1 wants X2; T2 holds X2)
  t=4:  T1 → T2 → T1 — CYCLE
  t=4+1s (Postgres deadlock_timeout):
        detector wakes, runs DFS on graph, finds cycle
        chooses victim (T2), raises 40P01, rolls back
  t=4+1s+ε:
        T1 proceeds with the (X2 now free) UPDATE id=2
        T1 commits

Application observes:
  T1's call: 4-5s slower than usual (was waiting) → returns OK
  T2's call: error 40P01 → application retries → eventually OK (or surfaces error)
```

Three-way deadlock walk-through:

```
T1: holds A, wants B
T2: holds B, wants C
T3: holds C, wants A

Wait-for graph: T1 → T2 → T3 → T1   (cycle of length 3)
Detector picks one victim (usually youngest), kills it, others proceed.
```

## How to think aloud in the interview

> "Deadlock construction: two sessions, two rows, inconsistent lock order. Session 1 locks row 1 then waits for row 2; session 2 locks row 2 then waits for row 1. Wait-for graph: T1 → T2 → T1, a cycle.
>
> Postgres detects after `deadlock_timeout` (default 1s) by running DFS on the wait-for graph; finds the cycle, picks a victim (usually youngest), aborts with SQLSTATE 40P01. The other transaction proceeds.
>
> Prevention is *consistent lock order*: always acquire row locks in deterministic order, e.g., `ORDER BY id FOR UPDATE`. With consistent order, no cycle can form — both transactions queue on the first lock and serialise.
>
> Recovery is *application retry* on 40P01 with backoff. Three attempts, exponential delay with jitter. Cap to avoid livelock.
>
> The senior gotcha: if you use different indexes in different queries, the *effective* lock order may differ even with app-level ordering. Always check the explain plan."

## Important takeaways

- Deadlock = cycle in the wait-for graph; engine detects and aborts a victim.
- Postgres: `deadlock_timeout` (default 1s) before detector runs; SQLSTATE 40P01.
- MySQL: detects instantly on wait; error 1213.
- **Prevention = consistent lock order.** ORDER BY id FOR UPDATE.
- **Recovery = app retry on 40P01/1213** with backoff.
- 3-way and N-way deadlocks possible; same detection algorithm.
- Index-order can shift effective lock order — check explain plans.

## Variants

1. **DDL-induced deadlock**: `ALTER TABLE` (ACCESS EXCLUSIVE) behind a long SELECT can deadlock with a concurrent UPDATE. Run migrations off-peak; use `lock_timeout` to fail fast.
2. **Foreign-key deadlock**: child INSERT waits for parent lock; parent UPDATE waits for child. Use FOR KEY SHARE in Postgres to allow FK reads.
3. **InnoDB next-key lock deadlock**: gap locks on overlapping ranges can deadlock even with consistent app-level order. Watch for it under REPEATABLE READ.
4. **Self-deadlock** (rare): single transaction with a savepoint can deadlock against itself if it tries to acquire an already-held lock incompatibly. Pathological.
5. **CRDB / Spanner**: no deadlocks; use wound-wait / wait-die. Trade-off: more aborts.

## Revision notes

> **deadlock-construction — 60 second recap**
> - Two sessions, two rows, opposite order = wait-for cycle.
> - Postgres: deadlock_timeout (1s) → DFS → abort victim → 40P01.
> - MySQL: instant detection → abort → 1213.
> - **Prevent: consistent lock order** (`ORDER BY id FOR UPDATE`).
> - **Recover: retry on 40P01/1213** with backoff.
> - Use `pg_blocking_pids` + `pg_stat_activity` to diagnose live waits.
> - 3-way / N-way deadlocks: same detection, same fix family.
> - Gotcha: different indexes → different effective lock order even with app-level ordering.
