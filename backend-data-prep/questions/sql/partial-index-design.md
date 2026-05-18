# Partial Index Design — Index Only Active Rows

## Source / Origin
- Senior Postgres / SQL Server interview at fintech / SaaS roles.
- Real prod: 99% of rows are soft-deleted; a full index wastes 99% of its space.

## Why this question matters in interviews
A partial index is "an index with a WHERE clause". It indexes only the rows that match a predicate — perfect when **most of the table is irrelevant to most queries** (soft-deleted rows, archived orders, retired users, completed jobs). Senior candidates use partial indexes to cut index size and write cost by an order of magnitude while still serving the hot queries.

This question tests whether you've **measured your indexes** in production. Most teams over-index and never look at the size or hit rate. The candidate who proposes a partial index unprompted has read `pg_stat_user_indexes`.

## Concepts involved

### Syntax to lock in
```sql
-- Index only active (non-soft-deleted) rows
CREATE INDEX ix_users_email_active ON users(email)
WHERE deleted_at IS NULL;

-- Index only "ready" jobs
CREATE INDEX ix_jobs_ready ON jobs(priority, created_at)
WHERE status = 'ready';

-- Unique constraint that ignores soft-deleted rows
CREATE UNIQUE INDEX ix_users_email_unique_active ON users(email)
WHERE deleted_at IS NULL;

-- Multiple narrow partial indexes (one per status), if statuses are skewed
CREATE INDEX ix_orders_pending  ON orders(created_at) WHERE status='pending';
CREATE INDEX ix_orders_shipped  ON orders(created_at) WHERE status='shipped';
```

### Edge cases / interview traps
1. **The query's predicate must imply the index's predicate** for the planner to use it. `WHERE deleted_at IS NULL AND email='x'` uses the partial index; `WHERE email='x'` alone does not (planner can't prove `deleted_at IS NULL`).
2. **Equality predicates in the partial WHERE** are exact; **range predicates** rarely qualify (planner must prove containment).
3. **Functional + partial** — combine `WHERE deleted_at IS NULL` with an expression in the index `(LOWER(email))` for case-insensitive uniqueness on active users.
4. **Updates that flip the predicate** move rows in and out of the index (insert + delete in the index). Costlier than plain index updates.
5. **Cannot index NULL-filtered partial in MySQL** — MySQL has no partial indexes (as of 8.x). SQL Server: "filtered indexes" with similar syntax.
6. **`EXPLAIN` confirmation.** Look for `Index Scan using ix_..._active`. If you see a Seq Scan instead, your query predicate doesn't imply the index predicate.
7. **Selectivity matters.** If the predicate is true for 99% of rows, the index isn't really partial — and you save nothing.
8. **Auto-vacuum still scans full table** — partial index doesn't shrink heap size; only index size.

## Mental Model

```
   users table (100M rows, 95M soft-deleted):

   FULL INDEX on email                       PARTIAL INDEX on email WHERE deleted_at IS NULL
   ──────────────────────────                ─────────────────────────────────────────────
   100M entries in B-tree                    5M entries in B-tree
   ~3GB on disk                              ~150MB on disk
   Insert cost: index every row              Insert cost: index only active rows
   Update of deleted_at: maintain entry      Update of deleted_at: insert OR delete from index

   Query "WHERE email='x' AND deleted_at IS NULL"
   → planner proves predicate ⇒ index predicate; uses partial index.
```

The win is **size + write cost**. Reads see a smaller B-tree (fewer levels). Writes only touch the index when the row qualifies.

## Why interviewers care
- Genuine production optimisation. Big tables with skewed predicates are everywhere.
- Tests **planner inference** — knowing when the optimizer can use the partial index.
- Reveals **storage / write-cost** awareness.

## Common beginner confusion
- "It's just an index with a filter, what's the big deal?" — the big deal is the storage saving and the write-cost saving.
- "Will any query that filters use it?" — only queries whose predicate **implies** the partial's WHERE.
- "MySQL has it" — no, MySQL has prefix indexes but no partial indexes.
- "Partial unique index = full uniqueness" — no, it's uniqueness only among matching rows.

## Brute force approach
Full index on the column. Works, indexes every row, including the 95% that are dead. Storage and write cost are proportional to total rows.

## Optimal approach
Partial index on the column with `WHERE <hot predicate>`. Storage and write cost are proportional to *matching* rows. Queries must explicitly include the partial predicate (or one that implies it) so the planner can match.

## Solution (SQL)

```sql
CREATE TABLE users (
  id          BIGSERIAL PRIMARY KEY,
  email       TEXT,
  deleted_at  TIMESTAMPTZ          -- soft-delete column
);

-- Full index (baseline)
CREATE INDEX ix_users_email_full ON users(email);

-- Partial index targeting only active users
CREATE INDEX ix_users_email_active ON users(email)
WHERE deleted_at IS NULL;

-- Partial UNIQUE for active-user email uniqueness
CREATE UNIQUE INDEX ix_users_email_uniq_active ON users(email)
WHERE deleted_at IS NULL;
```

```sql
-- Query that uses the partial:
EXPLAIN ANALYZE
SELECT * FROM users WHERE email='alice@x.com' AND deleted_at IS NULL;
-- Index Scan using ix_users_email_active

-- Query that does NOT use the partial:
EXPLAIN ANALYZE
SELECT * FROM users WHERE email='alice@x.com';
-- Falls back to ix_users_email_full (or seq scan if full index doesn't exist)
```

A scenario where **only** the partial exists:

```sql
DROP INDEX ix_users_email_full;

-- Reads of active users → partial index (fast)
SELECT * FROM users WHERE email='alice@x.com' AND deleted_at IS NULL;

-- Reads of *any* user (including deleted) → seq scan, because no full index exists.
-- This is a tradeoff: we pay for storage savings with slower deleted-row queries.
```

## Step-by-step dry run

Storage:

```
Full index   on email:    100M entries × ~50 bytes = ~5 GB.
Partial idx  on email:      5M entries × ~50 bytes = ~250 MB.

Savings: 20× smaller; 20× cheaper writes for soft-deleted rows.
```

Plan inference:

```
Query: WHERE email='x' AND deleted_at IS NULL.
Planner checks: does "email='x' AND deleted_at IS NULL" imply "deleted_at IS NULL"?
   Yes (AND-projection). Partial index eligible.
   Cost via partial index ≈ index height + match rows = pick this.

Query: WHERE email='x'.
Planner: does "email='x'" imply "deleted_at IS NULL"?
   No (planner can't know). Partial index NOT eligible.
```

## How to think aloud in the interview
1. *"If 95% of rows are soft-deleted, a full index wastes 95% of its space and 95% of its write cost. Partial index gives me a 20× smaller B-tree."*
2. *"`CREATE INDEX ix ON t(col) WHERE deleted_at IS NULL`. The query must include a predicate that *implies* the partial's WHERE."*
3. *"Partial UNIQUE is also powerful — uniqueness only among active rows, so I can soft-delete and re-create."*
4. *"Trade-off: queries that need all rows (including deleted) can't use it. Make sure your read patterns align."*
5. *"Verify with EXPLAIN ANALYZE — look for `Index Scan using ix_..._active`."*

## Important takeaways
- Partial index = `CREATE INDEX ... WHERE predicate`.
- Stores and maintains only matching rows.
- Query predicate must **imply** the index predicate.
- Massive storage + write-cost saving when matching set is small.
- Partial UNIQUE constraint is the canonical soft-delete uniqueness pattern.
- MySQL has no partial; SQL Server calls them "filtered indexes".
- See `backend-data-prep/sql/04-indexing.md` "Partial indexes".

## Variants
1. **Partial + functional**: `CREATE INDEX ix ON users(LOWER(email)) WHERE deleted_at IS NULL` — case-insensitive uniqueness on active rows.
2. **Multi-value status**: one partial index per status (`status='pending'`, `status='ready'`) if statuses are skewed and queried separately.
3. **NULL-distinct UNIQUE** (Postgres 15+) — `UNIQUE NULLS NOT DISTINCT` as an alternative to partial unique.

## Revision notes

> **Partial index cram block**
> - Syntax: `CREATE INDEX ix ON t(col) WHERE <predicate>`.
> - Only matching rows are stored & maintained.
> - Use case: soft delete (`WHERE deleted_at IS NULL`), status-bucketed tables.
> - Query predicate must **imply** index predicate.
> - Storage + write cost saving = proportional to filter selectivity.
> - Partial UNIQUE = uniqueness within matching rows.
> - MySQL: no support. SQL Server: filtered indexes.
> - Confirm with EXPLAIN ANALYZE.
