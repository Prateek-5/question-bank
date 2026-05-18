# Resolve deadlocks: detection, prevention, retry strategies

## Source / Origin
- Standard follow-up to "construct a deadlock". Tests strategy knowledge.
- Reference: Gray & Reuter "Transaction Processing" (the textbook).
- Companion: `deadlock-construction.md`, `backend-data-prep/sql/08-locks-concurrency.md`.

## Why this question matters in interviews
You produced a deadlock in the previous question. Now what? Interviewers want to hear three strategies — *detection*, *prevention via ordering*, *prevention via timeout* — and have you pick one with reasoning. The candidate who only says "retry on 40P01" is junior. The candidate who maps strategies to scenarios (web request vs batch job vs distributed transaction) is senior.

## Concepts involved

### Syntax to lock in

```sql
-- Detection (Postgres setting)
SHOW deadlock_timeout;             -- default 1 second
SET deadlock_timeout = '500ms';    -- session-local; lower = faster detection

-- Lock-acquisition timeout (avoids waiting forever)
SET lock_timeout = '5s';           -- transaction-level
SELECT * FROM t FOR UPDATE NOWAIT; -- per-statement: error immediately if locked

-- Statement-level wait limit
SET statement_timeout = '30s';

-- Idle-in-transaction limit (kill stuck sessions)
SET idle_in_transaction_session_timeout = '60s';
```

### Edge cases / interview traps

1. **Detection runs periodically, not continuously** in Postgres. After `deadlock_timeout` ms of waiting, the detector runs once. This is why short-lived deadlocks "self-heal" without being detected — both transactions completed before the timeout.
2. **MySQL detects on every lock-wait** — instant detection, slight CPU overhead per wait.
3. **`NOWAIT` and `lock_timeout` are different.** NOWAIT errors immediately if the lock is held; `lock_timeout` waits up to N ms then errors. Combine with care.
4. **Retry budget**: 3 attempts with exponential backoff + jitter is the standard. More than 5 = there's a deeper problem (hot row, inconsistent ordering).
5. **Wait-die / wound-wait** (textbook) — used by distributed DBs like Spanner/CockroachDB; not used in Postgres/MySQL.
6. **Ordering by ID isn't enough if the index used differs across queries.** The effective lock order depends on the access path. Use explain plans to verify.
7. **Don't retry in the same transaction.** Retry the *whole transaction* from a clean BEGIN. The aborted transaction's state is gone.

## Mental Model

The **"three responses to a stalemate"** model:

- **Detect** (DB does the work): let the cycle form, periodically check, kill the loser.
- **Prevent by ordering** (you do the work): structure code so no cycle can form.
- **Prevent by timeout** (the brute force): cap wait time; abort early; retry with luck.

```
   Strategy           Cost                Pro                   Con
   ───────            ────                ───                   ───
   Detect             O(graph) periodic   Lets you write        Slight latency before
                                          natural code           detection fires
   Order              0 runtime           Eliminates cycle       Discipline required
                                          structurally           across all code paths
   Timeout            None                Cheap, simple          False positives
                                                                 (slow ≠ deadlocked)
   Wait-die /         O(timestamp)        Used in distributed    Postgres/MySQL
   wound-wait                                                    don't implement
```

## Why interviewers care

- Tests **strategic thinking**: not just "DB handles it", but *which dial do you turn for which scenario*.
- Probes **operational settings**: `deadlock_timeout`, `lock_timeout`, `statement_timeout` — production-grade knobs.
- Asks about **retry policy**: linear / exponential / jittered backoff.

## Common beginner confusion

- "Just retry." Yes, but with backoff and cap. Naive retry causes livelock.
- "Increase the lock timeout to avoid deadlocks." Wrong direction — longer wait = more chance for a cycle to form.
- "Detection is expensive." DFS on the wait-for graph is cheap; the cost is the wait time *before* detection runs.
- "Distributed DBs don't deadlock." They do — they use wait-die / wound-wait to prevent or abort, but cross-shard transactions still face the same shape.

## Brute force approach

Set `deadlock_timeout` to 100ms and `statement_timeout` to 1s. Aggressive aborts; lots of retries; works but burns CPU. Better than nothing in chaos scenarios.

## Optimal approach

Layered defense:

1. **Structural prevention**: consistent lock order everywhere. ORDER BY id, ORDER BY (resource_type, id), whatever — pick a canonical order and stick to it.
2. **Detection at sane timeout**: leave deadlock_timeout at 1s (Postgres default). Monitor `pg_stat_database.deadlocks` for trends.
3. **Bounded wait**: set `lock_timeout` on user-facing endpoints (~5s) so a stuck lock doesn't hang the request.
4. **Application retry**: capped (3-5 attempts), exponential backoff with jitter.
5. **Observability**: log every deadlock with both transaction's queries; trend over time.

## Solution

```sql
-- ============================================================
-- Strategy 1: detection (default; let the DB handle it)
-- ============================================================
SHOW deadlock_timeout;  -- 1s
-- Inspect deadlock count
SELECT datname, deadlocks FROM pg_stat_database;

-- ============================================================
-- Strategy 2: prevent by ordering
-- ============================================================
-- Money transfer with canonical lock order
BEGIN;
SELECT id FROM accounts
WHERE id IN (LEAST($from, $to), GREATEST($from, $to))
ORDER BY id FOR UPDATE;     -- always smallest ID first
UPDATE accounts SET balance = balance - $amt
  WHERE id = $from AND balance >= $amt;
UPDATE accounts SET balance = balance + $amt WHERE id = $to;
COMMIT;

-- ============================================================
-- Strategy 3: bounded wait (statement / lock timeout)
-- ============================================================
BEGIN;
SET LOCAL lock_timeout = '5s';        -- waits up to 5s, then 55P03
SELECT * FROM accounts WHERE id=$id FOR UPDATE;
COMMIT;

-- Per-statement variant
SELECT * FROM accounts WHERE id=$id FOR UPDATE NOWAIT;
-- If locked: ERROR: could not obtain lock (SQLSTATE 55P03)

-- ============================================================
-- Strategy 4: kill stuck idle-in-transaction
-- ============================================================
-- session-level
SET idle_in_transaction_session_timeout = '60s';
-- Globally in postgresql.conf
-- idle_in_transaction_session_timeout = 60000
```

App-side retry with full strategy:

```javascript
const RETRIABLE = new Set([
  '40P01',  // deadlock_detected (Postgres)
  '40001',  // serialization_failure (Postgres SSI)
  '55P03',  // lock_not_available (NOWAIT, lock_timeout)
  'ER_LOCK_DEADLOCK',     // MySQL 1213
  'ER_LOCK_WAIT_TIMEOUT', // MySQL 1205
]);

async function txWithStrategy(fn, opts = {}) {
  const attempts = opts.attempts ?? 3;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (e) {
      const code = e.code || e.errno;
      if (!RETRIABLE.has(String(code))) throw e;
      const delay = Math.min(1000, 50 * (2 ** i)) * (0.5 + Math.random());
      await new Promise(r => setTimeout(r, delay));
      // Log for trend
      console.warn('tx-retry', { code, attempt: i + 1, delay });
    }
  }
  throw new Error('TX_RETRY_EXHAUSTED');
}
```

## Step-by-step dry run

T1/T2 timeline with detection (no ordering, default settings):

```
time →

T1: |--BEGIN--|--UPDATE row 1 (X)--|--UPDATE row 2 (waits)----------------------------|--detected as victim 50% chance--|
T2:           |--BEGIN--|--UPDATE row 2 (X)--|--UPDATE row 1 (waits)--|
                                              ^ wait-for cycle forms here
                                                                       1s elapses
                                                                       deadlock detector wakes, finds cycle
                                                                       picks victim (say T1)
                                                                       T1 aborts with 40P01
                                                                       T2 acquires X1, proceeds, commits

T1 app: catches 40P01, sleeps ~50ms, retries; this time row 2 is free → proceeds.
```

T1/T2 timeline with consistent ordering (no deadlock possible):

```
T1: |--BEGIN--|--ORDER BY id FOR UPDATE on {1,2}--|--lock row 1, lock row 2--|--UPDATEs--|--COMMIT--|
T2:            |--BEGIN--|--ORDER BY id FOR UPDATE on {1,2}--BLOCKED on row 1--|--lock row 1, lock row 2--|--UPDATEs--|--COMMIT--|

Both queue on row 1's lock. T2 waits for T1; T2 then waits for nothing (T1 done). Serial execution, no cycle, no deadlock.
```

T1/T2 with `lock_timeout` (bounded wait):

```
T1: |--BEGIN--|--UPDATE row 1--|--UPDATE row 2 (waits 5s, then 55P03)--|--ROLLBACK--|
T2:           |--BEGIN--|--UPDATE row 2--|--UPDATE row 1 (waits 5s, then 55P03)--|--ROLLBACK--|

Both lose. App-side retry policy kicks in: each retries with random jitter.
If the workload is high-contention, this strategy thrashes. If it's transient, this works.
```

## How to think aloud in the interview

> "Three strategies, layered:
>
> 1. **Structural prevention by ordering.** Always acquire row locks in canonical order (`ORDER BY id FOR UPDATE`). With consistent order, no wait-for cycle can form. Eliminates deadlocks at their source.
>
> 2. **Detection** with Postgres' default `deadlock_timeout` of 1s. Detector runs DFS, picks a victim, aborts with 40P01. Cheap and correct.
>
> 3. **Bounded wait** via `lock_timeout` so user-facing endpoints fail fast (e.g., 5s) rather than hang. Combined with `statement_timeout` and `idle_in_transaction_session_timeout` for hygiene.
>
> 4. **Application retry** on 40P01, 40001, 55P03 with capped attempts, exponential backoff + jitter.
>
> Don't pick one — combine. Order to eliminate, detect as backstop, timeout for sanity, retry for transients. Monitor `pg_stat_database.deadlocks` for trend; a sudden spike means a new code path violates ordering."

## Important takeaways

- **Detection**: DB handles it; Postgres after `deadlock_timeout` (1s); SQLSTATE 40P01.
- **Prevention by ordering**: canonical lock order eliminates cycle structurally.
- **Prevention by timeout**: `lock_timeout`, `NOWAIT`, `statement_timeout` — bounded waits.
- **Retry policy**: cap attempts (3-5), exponential backoff, jitter.
- **Retriable codes**: 40P01 (deadlock), 40001 (serialization), 55P03 (lock unavailable); MySQL 1213, 1205.
- **Wait-die / wound-wait**: distributed-DB-only (Spanner, CockroachDB); not used in Postgres/MySQL.
- Monitor `pg_stat_database.deadlocks` and trend it.

## Variants

1. **Distributed deadlock** across services: no global wait-for graph; rely on timeouts + saga rollback.
2. **Spanner / CockroachDB**: wait-die — younger tx aborts; older tx waits. Wound-wait — older preempts younger. Both prevent deadlocks without detection.
3. **Long batch jobs**: skip retry; surface deadlock to operator who can re-run.
4. **Streaming pipelines**: deadlock at sink → message redelivered → eventual progress.
5. **Postgres `lock_timeout` vs `statement_timeout`**: lock_timeout caps lock-wait specifically; statement_timeout caps overall statement.
6. **Spinlock / busy-wait retry**: don't. CPU-burn; use sleep-based backoff.

## Revision notes

> **deadlock-resolution — 60 second recap**
> - Detect: Postgres `deadlock_timeout` (1s default); SQLSTATE 40P01. MySQL: instant; 1213.
> - Prevent by ordering: `ORDER BY id FOR UPDATE`, canonical lock order everywhere.
> - Prevent by timeout: `lock_timeout`, `NOWAIT`, `statement_timeout`.
> - Hygiene: `idle_in_transaction_session_timeout` to kill stuck sessions.
> - Retry: cap 3-5, exponential backoff, jitter. Retriable: 40P01, 40001, 55P03; MySQL 1213, 1205.
> - Distributed: wait-die / wound-wait (Spanner, CRDB).
> - Monitor `pg_stat_database.deadlocks` for trend.
> - Don't retry in the same tx — retry from BEGIN.
