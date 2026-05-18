# Covering Index Design — INCLUDE Columns, Index-Only Scan

## Source / Origin
- Senior Postgres / SQL Server interview at high-throughput shops.
- Real prod: cut a hot endpoint from 5ms to 0.5ms by adding an INCLUDE column.

## Why this question matters in interviews
A covering index **contains all columns the query needs**, so the engine never visits the heap (the table) at all — only the index. Postgres 11+ exposes this with `CREATE INDEX ... INCLUDE (cols)`. The result is an **index-only scan**: pure B-tree, no random IO to the heap. For hot queries, this is a 5-10× win.

The interviewer wants to see: (1) you know `INCLUDE` exists, (2) you understand the difference between *adding the column to the key* vs *adding it to the payload*, (3) you can reason about the trade-off (bigger index pages, slower writes).

## Concepts involved

### Syntax to lock in
```sql
-- Plain index (key only)
CREATE INDEX ix_users_email ON users (email);
SELECT name, email FROM users WHERE email='a@x.com';
-- Plan: Index Scan on ix_users_email → Heap Fetch for name → return.

-- Covering index with INCLUDE (Postgres 11+, SQL Server 2005+)
CREATE INDEX ix_users_email_cov ON users (email) INCLUDE (name);
SELECT name, email FROM users WHERE email='a@x.com';
-- Plan: Index Only Scan on ix_users_email_cov → return (no heap visit).

-- Same effect with key-only (older Postgres)
CREATE INDEX ix_users_email_name ON users (email, name);
-- But: makes (email,name) the sort key — wastes space if name is large or unstable.
```

### Edge cases / interview traps
1. **`INCLUDE` columns are NOT part of the key.** They aren't searchable; they don't enforce uniqueness; they don't change sort order. They just ride along on the leaf pages.
2. **Index-only scan requires the visibility map to say "all rows on this page are visible to current snapshot"** — see `index-only-scan-conditions.md`. Stale visibility → falls back to heap fetch.
3. **MySQL has no `INCLUDE`.** Emulate with composite indexes; secondary indexes already store the primary key.
4. **Covering an index makes it bigger.** Each leaf entry now stores the key + the included columns. Trade storage for query speed.
5. **Writes update the included columns** in the index too. If you cover columns that change often, write amplification gets worse.
6. **`SELECT *` defeats covering.** Cover the actual columns the query needs; reviewing each query is part of the work.
7. **Unique constraint on covering index.** `CREATE UNIQUE INDEX ... INCLUDE (...)` — uniqueness on key only; included columns can repeat.
8. **TOASTed columns** (large text/jsonb) usually can't be included due to size; check engine limits.

## Mental Model

```
   Plain index (email):                 Covering index (email INCLUDE name):

   leaf:  [a@x.com] → tuple-id          leaf:  [a@x.com, name='Alice']   → tuple-id
          [b@x.com] → tuple-id                 [b@x.com, name='Bob']     → tuple-id
                                                ↑ name rides in the leaf
   Query SELECT name WHERE email=...    Query SELECT name WHERE email=...
   1) seek leaf → tuple-id              1) seek leaf → read name directly.
   2) random IO to heap page for name.  2) DONE. No heap visit.
```

Cover the query's payload. Read fewer pages. Trade index bloat for IO savings.

## Why interviewers care
- Latency-sensitive endpoints live and die by index-only scans.
- Tests **knowledge of physical layout** — leaves vs heap.
- Reveals trade-off reasoning — write cost, storage, vacuum impact.

## Common beginner confusion
- "Why not just add the column to the key?" — pollutes sort order, may make the key column wider for no benefit.
- "Does INCLUDE help searches?" — no, it doesn't affect the key. Use it only to avoid heap fetches.
- "Why is it called covering?" — the index "covers" all the columns the query needs.
- "MySQL has it" — no, but secondary indexes in InnoDB always implicitly include the primary key.

## Brute force approach
Plain index + always fetch from heap. Works, costs one random IO per result row. For 100-row result sets it's fine; for 10K-row hot queries it dominates latency.

## Optimal approach
Profile the hot query. If it returns columns A,B,C and filters on A, make `CREATE INDEX ix ON t(A) INCLUDE (B, C)`. Verify the plan switches to `Index Only Scan`.

## Solution (SQL)

```sql
CREATE TABLE users (
  id      BIGSERIAL PRIMARY KEY,
  email   TEXT,
  name    TEXT,
  status  TEXT,
  bio     TEXT      -- big; don't include
);

-- Hot endpoint:
-- SELECT name, status FROM users WHERE email = $1;

-- BEFORE (Index Scan + Heap Fetch)
CREATE INDEX ix_users_email ON users(email);

-- AFTER (Index Only Scan)
CREATE INDEX ix_users_email_cov ON users(email) INCLUDE (name, status);

-- Verify
EXPLAIN ANALYZE
SELECT name, status FROM users WHERE email='alice@x.com';
-- → Index Only Scan using ix_users_email_cov on users
--     Index Cond: (email = 'alice@x.com')
--     Heap Fetches: 0     ← the magic number
```

For a unique constraint with extra payload:

```sql
CREATE UNIQUE INDEX ix_users_email_uniq_cov ON users(email) INCLUDE (name, status);
-- Uniqueness on email; name/status hitch a ride.
```

## Step-by-step dry run

Heap page model:

```
Heap pages (random IO ~100µs each):
  page 17: row(email='a@x.com', name='Alice', status='active', bio=...)
  page 99: row(email='b@x.com', name='Bob',   status='inactive', bio=...)

Plain index leaf:
  ('a@x.com', page=17/offset=3)

Query: SELECT name, status WHERE email='a@x.com'
  Step 1: descend B-tree to leaf → 4 page reads (depth-4 tree). Some cached.
  Step 2: random IO to heap page 17 → 1 more page read for name+status.
  Total: 5 page reads.

Covering index leaf:
  ('a@x.com', name='Alice', status='active', page=17/offset=3)

  Step 1: descend B-tree → 4 leaf reads, name+status already there.
  Step 2: NO heap fetch.
  Total: 4 page reads (and they're all sequential B-tree pages, often cached).
```

Latency drop is more than the page-count math suggests because heap pages are colder.

## How to think aloud in the interview
1. *"Hot endpoint returns name, status; filters by email. Pull the heap fetch out by covering with `INCLUDE(name, status)`."*
2. *"INCLUDE columns aren't part of the key — no sort-order pollution, no uniqueness change."*
3. *"Watch for index-only-scan **conditions**: visibility map must be up to date, otherwise the engine falls back to heap fetch. Run VACUUM."*
4. *"Trade-off: bigger index, marginal write cost increase. Worth it for read-heavy endpoints."*
5. *"Verify with `EXPLAIN ANALYZE`: look for `Index Only Scan` and `Heap Fetches: 0`."*

## Important takeaways
- `INCLUDE` columns ride on leaf pages without affecting key.
- Index-only scan = no heap visit = big latency win on hot queries.
- Bigger index, slightly slower writes — explicit trade.
- Postgres 11+, SQL Server 2005+. MySQL implicit via PK in secondary index.
- Verify with EXPLAIN ANALYZE; `Heap Fetches: 0` is the success signal.
- See `backend-data-prep/sql/04-indexing.md` "Covering indexes".

## Variants
1. **MySQL InnoDB covering** — `INDEX (email, name, status)` (as key); InnoDB stores PK implicitly so SELECTs of those covered columns + PK never hit heap.
2. **JSONB column covering** — usually too large to include; rely on GIN + functional indexes instead.
3. **Covering + partial** — `CREATE INDEX ON t(x) INCLUDE (y) WHERE deleted_at IS NULL` for narrow hot slice.

## Revision notes

> **Covering index cram block**
> - `CREATE INDEX ix ON t(key_cols) INCLUDE (payload_cols)`.
> - INCLUDE columns sit on leaves; not part of key.
> - Goal: Index Only Scan → no heap fetch.
> - Need visibility-map current → run VACUUM in Postgres.
> - Bigger index, slower writes — measured trade-off.
> - MySQL: no INCLUDE; InnoDB secondary indexes include PK by default.
> - Validate: `Heap Fetches: 0` in `EXPLAIN (ANALYZE, BUFFERS)`.
> - Avoid `SELECT *` — cover the exact columns the query needs.
> - Don't INCLUDE high-churn or TOASTed columns.
