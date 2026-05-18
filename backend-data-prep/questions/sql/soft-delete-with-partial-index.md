# Soft delete with a partial index on `deleted_at IS NULL`

## Source / Origin
- Postgres docs on partial indexes; Markus Winand's *Use The Index, Luke!* — "Partial Indexes" chapter.
- Production lore from any company that has shipped GDPR-compliant data retention.
- Companion: `backend-data-prep/sql/05-indexing.md` — "Partial / functional indexes" section.
- Classic prompt: *"You added a `deleted_at` column for soft deletes; now your query `WHERE deleted_at IS NULL` is slow on a 50M-row table. Fix it."*

## Why this question matters in interviews
Soft delete is the **schema-design pattern every production system eventually adopts** — and the **most commonly mis-indexed**. The interviewer is testing whether you:

1. Recognise the **active-vs-deleted ratio asymmetry** (typically 95% active, 5% deleted, but sometimes the opposite — and the right index depends on which).
2. Know **partial indexes** exist and can write the syntax.
3. Understand that partial indexes also enable **conditional unique constraints** (e.g., "email is unique among non-deleted users").
4. Can articulate **tradeoffs** vs. table partitioning or two-table designs.

It's a small, sharp question that separates engineers who index-by-default from engineers who index-by-data-distribution.

## Concepts involved

### Syntax to lock in

```sql
-- The columns
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ;

-- The partial index — only indexes live rows
CREATE INDEX idx_users_email_active
  ON users (email)
  WHERE deleted_at IS NULL;

-- Conditional unique constraint — unique among live rows only
CREATE UNIQUE INDEX uniq_users_email_active
  ON users (email)
  WHERE deleted_at IS NULL;

-- Query must MATCH the predicate exactly to use the index
SELECT * FROM users WHERE email = 'a@x' AND deleted_at IS NULL;   -- uses index
SELECT * FROM users WHERE email = 'a@x';                          -- does NOT use partial index
```

### Edge cases / interview traps

1. **Query predicate must match the index predicate.** Postgres planner uses partial indexes only when it can *prove* the query's `WHERE` implies the index's `WHERE`. `WHERE deleted_at IS NULL` matches `WHERE deleted_at IS NULL`. `WHERE deleted_at IS NOT NULL` does not. `WHERE deleted_at < NOW()` does not match `IS NULL`.
2. **`NULL` comparisons need `IS NULL`, never `= NULL`.** `WHERE deleted_at = NULL` returns no rows ever. Junior trap.
3. **Foreign keys still see deleted rows.** Soft-deleted rows still exist; FKs from other tables still pin them. You need an application convention or trigger to filter.
4. **Conditional UNIQUE constraint via partial unique index.** "Email is unique among non-deleted users — a deleted user freed up their email." This *only* works with a partial unique index; a regular unique constraint won't allow re-registering the email.
5. **Cascading deletes** — `ON DELETE CASCADE` runs on **hard delete only**. Soft delete won't fire it. Build a trigger or application-level cascade.
6. **MVCC bloat.** Soft delete is a `WHERE` filter on every read. Old soft-deleted rows still occupy heap pages until `VACUUM`. After bulk soft-deletes, run `VACUUM (ANALYZE)`.
7. **Reporting queries.** "Users created in Jan, including deleted" needs to *not* filter `deleted_at IS NULL`. Make sure analytics dashboards know which view to use.
8. **Restore semantics.** "Undelete" is `UPDATE users SET deleted_at = NULL WHERE id = ?`. Hard delete via the same code path is `DELETE FROM users WHERE id = ?`. Two different operations; document clearly.

## Mental Model

### Why partial indexes are the right tool

```
50 million users.
49 million active (deleted_at IS NULL).
1 million soft-deleted.

Regular index on email (50M entries):
  ├── btree leaf pages: ~ 50M entries / 200 per page = 250k pages
  ├── tree height:  4-5 levels
  └── every WRITE has to update this index, even for deletions

Partial index on email WHERE deleted_at IS NULL (49M entries):
  ├── btree leaf pages: ~ 49M entries / 200 per page = 245k pages
  └── doesn't include the 1M deleted rows → 2% smaller

Now flip it:
50 million users, 49 million SOFT DELETED, 1 million active (an archive table).

Partial index on email WHERE deleted_at IS NULL  (1M entries):
  ├── btree leaf pages: 5k pages — 50x smaller
  ├── tree height: 2-3 levels
  └── lookups: 2-3 page reads vs 4-5. Free perf win.
```

The bigger the skew between included and excluded rows, the bigger the win.

### The "matching predicate" rule

```
Index predicate:  WHERE deleted_at IS NULL

Query predicate that MATCHES (index used):
  WHERE deleted_at IS NULL
  WHERE deleted_at IS NULL AND email = 'a@x'
  WHERE deleted_at IS NULL AND id IN (...)

Query predicate that DOES NOT MATCH (index NOT used):
  WHERE email = 'a@x'                        — no deleted_at predicate
  WHERE deleted_at IS NOT NULL               — opposite predicate
  WHERE deleted_at < NOW()                   — different shape
  WHERE COALESCE(deleted_at, 'infinity') > NOW()   — wrapping in COALESCE blinds planner
```

This is the single most-common debugging exercise with partial indexes: `EXPLAIN` shows a sequential scan, and you discover your query forgot `AND deleted_at IS NULL`.

## Why interviewers care

- Soft delete is **schema dogma** at every company over 50 engineers. Hard delete is now considered "unsafe" without an audit log; soft delete is the default.
- Partial indexes are an underused Postgres feature; knowing them signals **production-grade database literacy**.
- Conditional uniqueness via partial unique index is the **cleanest way to model "unique while alive"** — every other approach (NULL columns, trigger-based, app-level locks) is worse.
- The "index must match query predicate" rule is **the most important fact about partial indexes** and reveals if a candidate understands planner internals.

## Common beginner confusion

- *"Partial index = filtered index."* SQL Server calls it filtered index; Oracle calls it function-based index (in conjunction with `DECODE`). Same idea.
- *"`WHERE deleted_at = NULL` is fine."* It returns no rows. Always `IS NULL`.
- *"Soft delete is just adding a column."* The column is 5% of the work. Indexes, queries, FKs, reports, triggers, undelete semantics — all need consideration.
- *"`SELECT * FROM users` should return live rows."* You'd think so, but plain `SELECT *` returns all rows including soft-deleted. Use a view (`active_users`) or ORM scope to enforce.
- *"Just `DELETE` and keep audit log in a separate table."* Valid alternative; trades append-only audit for foreign-key complexity. Different tradeoff, not better/worse.

## Brute force approach

Two approaches that *look* okay and aren't:

**(a) Regular index on `(email)` plus `WHERE deleted_at IS NULL` filter on every query.**
The full index includes deleted rows. Lookup still does `O(log N)` but on the bigger N (50M vs 49M). Marginal cost when the deleted population is small; massive cost when deletions outweigh active rows (archive-style tables).

**(b) Regular index on `(email, deleted_at)`.**
Better than (a) — index-only scans can short-circuit on deleted. But the deleted_at column adds bytes per index entry, and the index still includes all entries. Still bigger than the partial index.

**(c) Trigger-based "move to deleted table".**
Two-table design: `users` and `deleted_users`. Cleaner queries (no `WHERE deleted_at IS NULL` filter) but breaks FK targets, complicates undelete, and doubles maintenance. Some teams prefer it; just know the tradeoff.

## Optimal approach

**Partial index on `(active_columns) WHERE deleted_at IS NULL`.**

- Index entry count = live row count.
- Smaller btree, faster lookups, less write overhead.
- Pair with a **conditional unique constraint** for "unique among live" semantics.
- Application convention: always `AND deleted_at IS NULL` on read paths. Wrap in a view if your ORM lets you.

## Solution (PostgreSQL)

```sql
-- ============================================================
-- Schema setup
-- ============================================================
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL,
  name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ      -- NULL = active
);

-- ============================================================
-- Partial indexes
-- ============================================================

-- Lookup by email, only among active users
CREATE UNIQUE INDEX uniq_users_email_active
  ON users (email)
  WHERE deleted_at IS NULL;

-- Composite for compound queries
CREATE INDEX idx_users_active_created
  ON users (created_at DESC)
  WHERE deleted_at IS NULL;

-- For the rare "undelete by email" path, an index on deleted
CREATE INDEX idx_users_email_deleted
  ON users (email)
  WHERE deleted_at IS NOT NULL;

-- ============================================================
-- View — enforces "always filter deleted" at query level
-- ============================================================
CREATE VIEW active_users AS
  SELECT * FROM users WHERE deleted_at IS NULL;

-- Application code reads from active_users, not users.

-- ============================================================
-- Soft delete + undelete
-- ============================================================
-- Delete
UPDATE users SET deleted_at = NOW() WHERE id = $1;

-- Undelete
UPDATE users SET deleted_at = NULL WHERE id = $1;

-- Hard delete (audit purge — rare)
DELETE FROM users WHERE id = $1 AND deleted_at < NOW() - INTERVAL '90 days';

-- ============================================================
-- Conditional uniqueness in action
-- ============================================================
INSERT INTO users (email, name) VALUES ('a@x', 'Alice');    -- ok
INSERT INTO users (email, name) VALUES ('a@x', 'Other');    -- conflict — unique index
UPDATE users SET deleted_at = NOW() WHERE email = 'a@x';    -- soft delete Alice
INSERT INTO users (email, name) VALUES ('a@x', 'Other');    -- ok now — partial unique allows
```

### Query plan comparison

```sql
EXPLAIN SELECT * FROM users WHERE email = 'a@x' AND deleted_at IS NULL;
-- Index Scan using uniq_users_email_active on users
--   Index Cond: (email = 'a@x')
-- (planner notes both predicates match the partial index)

EXPLAIN SELECT * FROM users WHERE email = 'a@x';
-- (no partial-index match because deleted_at predicate missing)
-- Seq Scan on users  ← BAD, full table scan
--   Filter: (email = 'a@x')
```

Yes — forgetting `AND deleted_at IS NULL` *literally* turns an O(log n) lookup into a sequential scan. This is the #1 lurking bug in production code that uses partial indexes.

## Step-by-step dry run

Suppose `users` has 50M rows, 49M with `deleted_at IS NULL`, 1M soft-deleted.

```
Query A:  SELECT * FROM users WHERE email = 'a@x' AND deleted_at IS NULL;

Planner steps:
  1. Look up indexes on users.
  2. Find idx_users_email_active with predicate "deleted_at IS NULL".
  3. Check: does query's WHERE imply index's WHERE?
     query: email = 'a@x' AND deleted_at IS NULL
     index: deleted_at IS NULL
     yes — index's predicate is implied. Index usable.
  4. Use Index Scan. Lookup: O(log 49M) = ~26 comparisons.
  Result: 0 or 1 row.

Query B:  SELECT * FROM users WHERE email = 'a@x';

Planner steps:
  1. Find idx_users_email_active with predicate "deleted_at IS NULL".
  2. Check: does query's WHERE imply index's WHERE?
     query: email = 'a@x'
     index: deleted_at IS NULL
     query doesn't constrain deleted_at — could match deleted rows too.
     NO — index unusable.
  3. Find no other usable index.
  4. Seq Scan, 50M rows scanned, ~30s.
  Result: 0, 1, or 2 rows (active + previously-deleted with same email).
```

The fix is in the application code: always add `AND deleted_at IS NULL`, or read from the `active_users` view.

## How to think aloud in the interview

> "Soft delete with a `deleted_at` column. The key insight: a regular index on `email` includes deleted rows too, so the index is bigger than it needs to be, and every soft-delete still updates the index. The right move is a partial index — `CREATE UNIQUE INDEX uniq_users_email_active ON users(email) WHERE deleted_at IS NULL`. Two wins: the index only contains live rows, and you get conditional uniqueness for free — Alice soft-deletes her account, someone else can register `a@x`.
>
> Critical caveat: the planner uses a partial index only when it can *prove* the query's `WHERE` implies the index's `WHERE`. So every read path needs `AND deleted_at IS NULL` explicitly. Easiest enforcement is a view — `CREATE VIEW active_users AS SELECT * FROM users WHERE deleted_at IS NULL` — and read from the view everywhere. Forgetting the predicate is the #1 bug; you'll see a sequential scan in `EXPLAIN`.
>
> Tradeoffs vs alternatives:
> - **Hard delete + audit table.** Cleaner queries but breaks FK targets and complicates undelete.
> - **`is_deleted BOOLEAN`.** Loses the timestamp, which you almost always end up wanting for GDPR retention windows ('purge after 90 days').
> - **Partitioning by deleted/active.** Heavy machinery for the same effect; only worth it at very large scale.
>
> I'd combine the partial index with a view for query hygiene, a scheduled VACUUM after bulk soft-deletes, and a separate `users_purged` job that hard-deletes after the retention window."

## Important takeaways

- **Partial index `WHERE deleted_at IS NULL`** is the canonical soft-delete pattern.
- **Query predicate must match index predicate** for the planner to use it — `AND deleted_at IS NULL` in every read path, or use a view.
- **Conditional unique constraint** via partial unique index gives "unique while alive" semantics.
- **`= NULL` is never true** — always `IS NULL`.
- **FKs ignore soft delete** — application or trigger must cascade.
- **`ON DELETE CASCADE`** fires on hard delete only, not on `UPDATE deleted_at`.
- **Bloat** — schedule `VACUUM` after bulk soft-deletes.
- **Indexes don't shrink automatically** when rows are soft-deleted; partial index helps because deletes update fewer entries.

## Variants

1. **Conditional uniqueness** — `CREATE UNIQUE INDEX ON users(email) WHERE deleted_at IS NULL` — uniqueness only among live rows.
2. **TTL-based hard purge** — scheduled job to hard-delete after retention window: `DELETE FROM users WHERE deleted_at < NOW() - '90 days'`.
3. **Soft delete + audit shadow table** — keep the row + write to an audit log on update.
4. **Generated column for `is_active`** — `is_active BOOLEAN GENERATED ALWAYS AS (deleted_at IS NULL) STORED` — index on `is_active`; same effect with cleaner queries.
5. **Per-tenant partial indexes** — large multi-tenant SaaS: `WHERE tenant_id = 42 AND deleted_at IS NULL` — index per tenant if the workload demands.
6. **MySQL InnoDB equivalent** — no partial indexes in standard MySQL; emulate via a `status` column with `'active' | 'deleted'` and indexes on `(status, email)`. Less elegant; mention this if the prompt is MySQL.
7. **Functional partial index** — `WHERE deleted_at IS NULL AND lower(email) = lower(...)` — for case-insensitive uniqueness among live rows.

## Revision notes

> **soft-delete partial index — 60 second recap**
> - Pattern: `deleted_at TIMESTAMPTZ` (nullable) — `NULL` = active.
> - **Partial index** `CREATE INDEX ... WHERE deleted_at IS NULL` — only indexes live rows.
> - **Conditional UNIQUE**: `CREATE UNIQUE INDEX ... WHERE deleted_at IS NULL`.
> - Query predicate **must match** index predicate — `AND deleted_at IS NULL` everywhere.
> - Use a view (`active_users`) to enforce.
> - `= NULL` never true — `IS NULL`.
> - FKs ignore soft delete; cascade in app or trigger.
> - `VACUUM` after bulk soft-deletes.
> - MySQL: emulate with status enum.
