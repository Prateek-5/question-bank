# Pessimistic locking with `SELECT ... FOR UPDATE`

## Source / Origin
- The "what if you can't afford retries?" question that follows optimistic locking.
- Concept refs: `backend-data-prep/orm/01-orm-internals.md`, `transactions-concurrency/optimistic-vs-pessimistic-decision.md`, `transactions-concurrency/2pl-vs-mvcc-comparison.md`.

## Why this question matters in interviews
Pessimistic locking is the right answer when **conflicts are common** or **retry is expensive**. The interview signal: do you know the exact SQL (`SELECT ... FOR UPDATE`), the ORM syntax in 3 libraries, when to prefer `FOR SHARE`, and how `NOWAIT` / `SKIP LOCKED` change behavior? Senior candidates also articulate the **cost**: connection pool burn while locks held; deadlock potential; blocked replicas.

## Concepts involved

### Syntax to lock in

```sql
-- Vanilla SQL — exclusive row lock until COMMIT/ROLLBACK
BEGIN;
SELECT * FROM accounts WHERE id = $1 FOR UPDATE;
-- ...mutation logic...
UPDATE accounts SET balance = ... WHERE id = $1;
COMMIT;

-- Variants
SELECT ... FOR UPDATE NOWAIT;       -- fail fast if locked (error rather than wait)
SELECT ... FOR UPDATE SKIP LOCKED;  -- skip locked rows (job queue pattern)
SELECT ... FOR SHARE;               -- shared lock — many readers, no writer until commit
SELECT ... FOR KEY SHARE;           -- weaker; prevents key change but allows non-key UPDATEs
```

### ORM syntax across libraries

```typescript
// TypeORM
await mgr.findOneByOrFail(Account, { id }, { lock: { mode: 'pessimistic_write' } });
// QueryBuilder
.setLock('pessimistic_write')                           // FOR UPDATE
.setLock('pessimistic_write_or_fail')                   // FOR UPDATE NOWAIT
.setLock('pessimistic_partial_write')                   // FOR UPDATE SKIP LOCKED (Postgres)
.setLock('pessimistic_read')                            // FOR SHARE

// Prisma — raw escape hatch (no first-class API)
await tx.$queryRaw`SELECT * FROM "Account" WHERE id = ${id} FOR UPDATE`;

// SQLAlchemy
session.scalars(
    select(Account)
    .where(Account.id == id)
    .with_for_update()                  # FOR UPDATE
    # .with_for_update(nowait=True)
    # .with_for_update(skip_locked=True)
    # .with_for_update(read=True)       # FOR SHARE
).one()

// JPA / Hibernate
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("SELECT a FROM Account a WHERE a.id = :id")
Account findForUpdate(@Param("id") Long id);
// Sets PESSIMISTIC_READ / PESSIMISTIC_WRITE / PESSIMISTIC_FORCE_INCREMENT.
```

### Edge cases / interview traps

1. **Locks last until COMMIT/ROLLBACK.** A 5-second business logic block holds the row lock 5 seconds. Throughput on the row caps at 1/wait-time.
2. **Lock order matters** — deadlocks happen when T1 locks A then B, T2 locks B then A. Always lock in consistent order (e.g., `MIN(id)` then `MAX(id)`).
3. **`NOWAIT` errors immediately** with SQL state `55P03`. Fast-fail pattern for "if locked, try later."
4. **`SKIP LOCKED` skips locked rows silently** — used for **job queue dequeue**: many workers can grab disjoint rows.
5. **`FOR UPDATE` on a JOIN** locks all rows from all joined tables. Sometimes you want `FOR UPDATE OF some_table` to lock only specific rows.
6. **Replicas don't lock** — `FOR UPDATE` on a read replica is an error or no-op in many setups. Always route locked reads to the primary.
7. **PgBouncer transaction mode** — locks are transaction-scoped; that's compatible. Session-scoped pooler would break this entirely.
8. **`FOR KEY SHARE` is the modern default for FK target rows** — Postgres 9.3+ uses this implicitly for FK validation. Beware locking conflicts with manual `FOR UPDATE`.
9. **InnoDB's gap locks** under REPEATABLE READ — `SELECT FOR UPDATE WHERE x > 5` locks the *gap*, blocking inserts. Surprising to Postgres users.
10. **Lock timeout** — Postgres `lock_timeout`, MySQL `innodb_lock_wait_timeout`. Set these or queries hang forever.

## Mental Model

```
   Optimistic                          Pessimistic
   ─────────                           ──────────

   Read → compute → CAS write          BEGIN
                                       SELECT ... FOR UPDATE  ─┐
   Retry on conflict                   compute                 │ lock held
                                       UPDATE                  │ on the row
                                       COMMIT  ────────────────┘ lock released

   Cost when no conflict: zero          Cost: serializes everyone touching the row
   Cost when conflict:    a retry       Risk: deadlocks, lock-wait timeouts, queue
```

The rule of thumb:
- Conflict rate < 5% → optimistic.
- Conflict rate > 5%, contention bursty → pessimistic.
- Long-running work in TX → never pessimistic (release the lock or split the TX).

### Variants at a glance

```
   FOR UPDATE          : exclusive row lock; blocks all other locks
   FOR NO KEY UPDATE   : like FOR UPDATE but allows FOR KEY SHARE
   FOR SHARE           : shared read lock; blocks writers
   FOR KEY SHARE       : weakest; only blocks key changes (FK reference)
   NOWAIT              : raise error 55P03 if locked
   SKIP LOCKED         : silently skip locked rows
```

## Why interviewers care

- Tests **lock semantics** vocabulary: row vs gap, shared vs exclusive, key-share vs full update.
- Tests **operational awareness**: locks held during business logic = throughput collapse.
- Tests **deadlock prevention**: lock ordering is a foundational pattern.
- Distinguishes "I read about FOR UPDATE" from "I've used SKIP LOCKED to build a job queue."

## Common beginner confusion

- **"`FOR UPDATE` locks the whole table."** No — only the rows returned (and possibly gaps under MySQL RR).
- **"Pessimistic locking is always safer."** It serializes; throughput drops; deadlocks become possible. Choose based on conflict rate.
- **"The lock is released after the UPDATE."** No — held until COMMIT/ROLLBACK. The UPDATE itself doesn't release locks.
- **"`SKIP LOCKED` is the same as `NOWAIT`."** Different: `NOWAIT` errors; `SKIP LOCKED` returns the next available rows.
- **"I can `FOR UPDATE` on a read replica."** Replicas usually error or no-op. Lock reads belong on the primary.
- **"`FOR UPDATE` blocks reads."** Plain SELECTs without lock still see the latest committed row (MVCC). Only other `FOR UPDATE` / `FOR SHARE` block.
- **"Postgres has the same gap-lock behavior as MySQL."** No — Postgres uses predicate locks only in SSI (SERIALIZABLE). MySQL InnoDB RR has gap locks by default.

## Brute force approach

`LOCK TABLE accounts IN EXCLUSIVE MODE;` at the start of each transaction. Correct but kills concurrency for the entire table. Use only for one-off admin operations.

## Optimal approach

1. Issue `SELECT ... FOR UPDATE` on the specific rows you'll mutate.
2. Keep the TX short — fetch, decide, write, commit. No I/O.
3. Lock rows in consistent order (e.g., by ID asc) to prevent deadlocks.
4. Set `lock_timeout` / `innodb_lock_wait_timeout` to a sane value (e.g., 3s) and handle the error.
5. For job-queue patterns, use `SKIP LOCKED` to let many workers dequeue concurrently.
6. For fast-fail / try-later, use `NOWAIT` and handle `55P03`.
7. Monitor lock contention (`pg_locks`, `pg_stat_activity` waiting state).

## Solution

```typescript
// ============================================================
// Account transfer with pessimistic locking + ordered lock
// (TypeORM)
// ============================================================
async transfer(fromId: number, toId: number, amt: number) {
  return this.ds.transaction(async (mgr) => {
    // Lock in consistent order to avoid deadlock
    const [firstId, secondId] = [fromId, toId].sort((a, b) => a - b);
    const first  = await mgr.findOneOrFail(Account, {
      where: { id: firstId }, lock: { mode: 'pessimistic_write' },
    });
    const second = await mgr.findOneOrFail(Account, {
      where: { id: secondId }, lock: { mode: 'pessimistic_write' },
    });
    const from = first.id === fromId ? first : second;
    const to   = first.id === fromId ? second : first;

    if (from.balance < amt) throw new InsufficientFundsError();
    from.balance -= amt;
    to.balance   += amt;
    await mgr.save([from, to]);
  });
}

// ============================================================
// Job queue dequeue with SKIP LOCKED (raw SQL)
// ============================================================
const job = await prisma.$transaction(async (tx) => {
  const rows = await tx.$queryRaw<Job[]>`
    SELECT * FROM jobs
    WHERE  status = 'PENDING'
    ORDER BY created_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED
  `;
  if (rows.length === 0) return null;
  const j = rows[0];
  await tx.$executeRaw`UPDATE jobs SET status='RUNNING', worker=${WORKER_ID} WHERE id=${j.id}`;
  return j;
});

// 10 workers can run this concurrently and each picks a different job — no blocking.

// ============================================================
// Fast-fail with NOWAIT
// ============================================================
try {
  const row = await mgr.findOneOrFail(Inventory, {
    where: { sku }, lock: { mode: 'pessimistic_write_or_fail' },  // → FOR UPDATE NOWAIT
  });
  // ... mutate ...
} catch (e: any) {
  if (e.code === '55P03') {
    return res.status(409).send('Item busy, retry shortly.');
  }
  throw e;
}

// ============================================================
// SQLAlchemy version
// ============================================================
def claim_next_job(session):
    job = session.scalars(
        select(Job)
        .where(Job.status == "PENDING")
        .order_by(Job.created_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    ).one_or_none()
    if job:
        job.status = "RUNNING"
        session.commit()
    return job
```

## Step-by-step dry run

### Scenario A: account transfer, two concurrent transactions

State: `Account#1.balance = 100`, `Account#2.balance = 100`.

```
T1 (transfer 1 → 2, amt 50):                  T2 (transfer 2 → 1, amt 30):
  BEGIN                                         BEGIN
  SELECT id=1 FOR UPDATE  ◄── lock 1            SELECT id=1 FOR UPDATE  ◄── BLOCKED (T1 has lock)
  SELECT id=2 FOR UPDATE  ◄── lock 2
  balance check, debit/credit
  UPDATE id=1 SET balance=50
  UPDATE id=2 SET balance=150
  COMMIT  ◄── locks released
                                                ─► lock 1 acquired
                                                SELECT id=2 FOR UPDATE  ◄── lock 2
                                                balance check, debit/credit
                                                UPDATE id=1 SET balance=80
                                                UPDATE id=2 SET balance=120
                                                COMMIT
```

Both succeed. Without the lock ordering rule, T2 could lock `2` first, T1 has `1`, then both wait — **deadlock**, one gets killed.

### Scenario B: job queue with SKIP LOCKED

State: 5 pending jobs in `jobs` table. 3 workers polling.

```
t=0:
  Worker A: SELECT ... FOR UPDATE SKIP LOCKED → row #1; sets RUNNING. (locks #1)
  Worker B: SELECT ... FOR UPDATE SKIP LOCKED → SKIPS #1 (locked), gets #2; sets RUNNING. (locks #2)
  Worker C: SELECT ... FOR UPDATE SKIP LOCKED → SKIPS #1,#2; gets #3.

t=1: All three workers committed; #1,#2,#3 locks released; status RUNNING.
t=2: Worker A polls again → gets #4. Worker B → #5. Worker C → nothing returned.
```

No worker blocks, none takes a duplicate job. This is the canonical Postgres job-queue pattern.

### Scenario C: NOWAIT for hot inventory row

State: SKU `WIDGET-1` row is being checked out by another session.

```
T1 (checkout in progress):
  BEGIN
  SELECT * FROM inventory WHERE sku='WIDGET-1' FOR UPDATE;  -- locked
  ... user paying ...

T2 (different user):
  BEGIN
  SELECT ... FOR UPDATE NOWAIT;
  → ERROR 55P03 "could not obtain lock on row"
  → app returns 409 to user, suggests retry in 30s
```

Without NOWAIT, T2 would wait up to `lock_timeout` seconds before erroring or proceeding.

## How to think aloud in the interview

> "Pessimistic locking via `SELECT ... FOR UPDATE` is the right tool when **conflicts are common** or **retries are expensive** (long-running business logic, multiple-row invariants). It acquires a row lock until COMMIT.
>
> Key variants:
> - `FOR UPDATE` — exclusive; blocks writers and other lockers.
> - `FOR SHARE` — shared; multiple readers can hold; blocks writers.
> - `NOWAIT` — error 55P03 if locked. Fast-fail pattern.
> - `SKIP LOCKED` — silently skip locked rows. Job queue pattern.
>
> Three discipline rules:
> 1. **Keep TX short** — locks are held until commit; long TX = throughput collapse.
> 2. **Lock in consistent order** — sort IDs, lock low-to-high. Prevents the classic A-then-B vs B-then-A deadlock.
> 3. **Set lock_timeout** — never let a transaction wait indefinitely; fail and retry at the app layer.
>
> ORM syntax: TypeORM `lock: { mode: 'pessimistic_write' }`; SQLAlchemy `with_for_update()`; JPA `@Lock(PESSIMISTIC_WRITE)`. Prisma needs `$queryRaw` because there's no first-class API.
>
> When *not* to use: read-mostly workloads, low contention (optimistic is cheaper), workflows with external I/O inside the TX (locks held during HTTP calls is a recipe for disaster)."

## Important takeaways

- `SELECT ... FOR UPDATE` locks rows until COMMIT — the entire TX duration.
- Variants: `FOR SHARE`, `FOR KEY SHARE`, `NOWAIT`, `SKIP LOCKED`.
- Choose pessimistic when conflict rate > 5–10% or retry cost is high.
- Lock in consistent order to prevent deadlocks; sort by ID.
- Set lock_timeout / innodb_lock_wait_timeout; handle the error.
- `SKIP LOCKED` is the canonical Postgres job-queue dequeue pattern.
- Replicas can't lock — route lock reads to primary.
- MySQL InnoDB RR uses gap locks by default; surprising to Postgres users.

## Variants

1. **Hierarchical locking** — lock the parent (e.g., `Order`) row, then mutate children. Avoids per-child locking on a known-bounded set.
2. **`FOR UPDATE OF`** — when joining tables but only locking some.
3. **Advisory locks** — `pg_advisory_lock(key)` for cross-row coordination (e.g., "only one process can run this nightly job"). Separate page: `advisory-lock-use-cases.md`.
4. **MySQL gap-locks** — `WHERE x BETWEEN 10 AND 20 FOR UPDATE` locks the *range* to prevent inserts.
5. **Read locks (`FOR SHARE`)** — useful when you need to read a row and ensure no one updates it before you finish (e.g., checking a balance before issuing a refund).
6. **Job queue at scale** — `SKIP LOCKED` + partial index + `LIMIT 1` is the entire pattern.
7. **Compound lock + version** — pessimistic lock for atomicity, version column for cross-session optimism. Belt-and-suspenders for high-value writes.

## Revision notes

> **pessimistic-locking-select-for-update — 60 second recap**
> - `SELECT ... FOR UPDATE` holds row lock until COMMIT.
> - Variants: `FOR SHARE`, `NOWAIT`, `SKIP LOCKED`.
> - Use when conflicts > 5–10% or retry cost is high.
> - Keep TX short (locks held during business logic = bad).
> - Lock in consistent order to prevent deadlock.
> - Set lock_timeout; handle the error.
> - `SKIP LOCKED` = job-queue dequeue.
> - MySQL RR uses gap locks; Postgres doesn't (except SSI).
> - Replicas can't lock; route to primary.
