# Locks & Concurrency Control

## Why this matters in backend interviews

- **Real production debugging** lives here — deadlocks, lock waits, replica stalls, queue starvation.
- **Senior signal**: candidates who can name the lock modes, draw a deadlock graph, and pick the right resolution strategy stand out.
- **System design**: every concurrent-write feature (booking, payments, counters, queues) needs a concurrency strategy.
- **Machine coding**: you'll be asked to make a counter or a queue thread-safe at the DB level.

---

## Core concepts

### Lock granularity

| Granularity | Coverage | Use |
|---|---|---|
| **Row** | One row | Most common; default for `UPDATE`/`DELETE` |
| **Page** | A disk page | Some engines; performance-tier optimization |
| **Table** | Whole table | DDL operations (ALTER), some `LOCK TABLE` calls |
| **Predicate / gap** | A range of keys | InnoDB next-key locks; Postgres SSI SIREAD locks |
| **Advisory** | Application-defined logical key | Cross-row coordination (Postgres `pg_advisory_lock`) |

### Lock modes

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
- `FOR UPDATE` — exclusive; blocks any other FOR UPDATE / FOR SHARE / update on same row
- `FOR NO KEY UPDATE` — exclusive but allows FKs from other tables to read
- `FOR SHARE` — shared lock
- `FOR KEY SHARE` — weakest; allows non-FK updates

```sql
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;
```

### Postgres table locks (8 modes)
ACCESS SHARE < ROW SHARE < ROW EXCLUSIVE < SHARE UPDATE EXCLUSIVE < SHARE < SHARE ROW EXCLUSIVE < EXCLUSIVE < ACCESS EXCLUSIVE.

- SELECT acquires ACCESS SHARE
- INSERT/UPDATE/DELETE acquires ROW EXCLUSIVE
- `CREATE INDEX` (not concurrent) acquires SHARE → blocks writes
- `ALTER TABLE` acquires ACCESS EXCLUSIVE → blocks everything
- `VACUUM` acquires SHARE UPDATE EXCLUSIVE → coexists with most reads/writes

Knowing which DDL blocks production traffic is a **senior signal**.

### InnoDB lock modes
- Record lock: on an index record
- Gap lock: on a gap between index records (prevents INSERTs into the gap)
- Next-key lock: record + gap (default in REPEATABLE READ to prevent phantoms)
- Insert intention lock: brief lock during INSERT

### Deadlocks

Two transactions waiting on each other's locks. The DB detects this (Postgres: deadlock_timeout, default 1s; MySQL: deadlock detector) and aborts one with a deadlock error. The other proceeds.

Classic:
```
T1: UPDATE A; -- locks A
T2: UPDATE B; -- locks B
T1: UPDATE B; -- waits on T2
T2: UPDATE A; -- waits on T1 → DEADLOCK
```

**Prevention:**
- Always acquire locks in the same order (e.g., by ID)
- Keep transactions short
- Use `SELECT FOR UPDATE` early to surface conflicts fast
- Application-level retry on deadlock error

### Lock waits (not deadlocks)

A transaction is just waiting because another holds the lock. Usually not detected as deadlock. Symptoms: slow APIs, queue backup. Find via `pg_stat_activity` / `SHOW ENGINE INNODB STATUS`.

### `SELECT FOR UPDATE SKIP LOCKED`

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

### Optimistic concurrency (e-commerce price update)

```sql
UPDATE products
SET price_cents = $new_price, version = version + 1
WHERE id = $id AND version = $expected_version;
-- 0 rows affected → another writer won; refetch and retry
```

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
