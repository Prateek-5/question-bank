# Query Rewrite for Index — SARGability

## Source / Origin
- Senior SQL screens. "Here's a slow query. Make it fast without adding indexes." or "Why isn't this query using the index?"
- Real prod: a one-character query change going from 30s scan → 30ms index seek.

## Why this question matters in interviews
**SARG** stands for "Search ARGument" — a predicate the engine can rewrite to a range-scan on an index. A query is **SARGable** when its WHERE clause is a function of an indexed column alone, not a function *applied to* the indexed column. Candidates who write `WHERE DATE(created_at) = '2024-01-01'` are the ones whose queries get paged at 3 AM.

This is the highest-leverage skill after "knowing what an index is". Interviewers ask it because (a) it's directly responsible for prod incidents, (b) it's a one-line fix when you spot it, and (c) it tests whether the candidate has ever opened `EXPLAIN`.

## Concepts involved

### Syntax to lock in
```sql
-- NON-SARGable (function on indexed column → cannot seek index)
SELECT * FROM orders WHERE DATE(created_at) = '2024-01-01';
SELECT * FROM users  WHERE LOWER(email)     = 'a@x.com';
SELECT * FROM logs   WHERE EXTRACT(YEAR FROM ts) = 2024;
SELECT * FROM events WHERE id + 0 = 42;            -- ridiculous but seen
SELECT * FROM t      WHERE col LIKE '%foo%';       -- leading wildcard
SELECT * FROM t      WHERE col LIKE '%foo';        -- leading wildcard
SELECT * FROM t      WHERE col::text = 'abc';      -- cast on column

-- SARGable rewrites
SELECT * FROM orders
WHERE  created_at >= '2024-01-01' AND created_at < '2024-01-02';

SELECT * FROM users WHERE email = LOWER('A@X.COM');     -- function on the *constant*
-- or: functional index: CREATE INDEX ix_users_email_lc ON users(LOWER(email));

SELECT * FROM logs WHERE ts >= '2024-01-01' AND ts < '2025-01-01';

SELECT * FROM t WHERE col LIKE 'foo%';                  -- trailing wildcard OK
-- for leading wildcard: GIN trigram index (pg_trgm) or full-text index.
```

### Edge cases / interview traps
1. **Function on the column kills the index.** Move the function to the constant, or build a *functional index* that materializes the function output.
2. **Implicit casts.** `WHERE id = '42'` (id is INT). Postgres usually casts the string to int (SARGable); some engines cast the column to text (not SARGable). Always match types.
3. **Leading wildcard `LIKE '%foo'`** — no index can help; consider trigram (`pg_trgm`) or reversing-and-indexing trick.
4. **`OR` on different columns** — usually defeats indexes (no single index covers both branches). Rewrite as `UNION ALL` or `UNION`.
5. **`NOT` predicates and inequalities** — large selectivity → planner skips the index. Expected, not a bug.
6. **Date truncation.** `DATE_TRUNC('month', ts) = '2024-01-01'` not SARGable. Range form: `ts >= '2024-01-01' AND ts < '2024-02-01'`.
7. **Composite-index column order.** The leftmost-prefix rule: only the prefix of the index columns matters. See `leftmost-prefix-puzzle.md`.
8. **`IN (subquery)` with parameter list** — usually SARGable. `IN` with large lists may switch to a hash anti/semi join.

## Mental Model

```
   The B-tree index is sorted by raw column values:

   index on created_at:    [2024-01-01 00:00] → row 47
                           [2024-01-01 03:11] → row 02
                           [2024-01-01 13:42] → row 88
                           [2024-01-02 00:05] → row 14
                           ...

   "WHERE created_at >= '2024-01-01' AND < '2024-01-02'"
   → seek to first key ≥ '2024-01-01', walk leaves until first key ≥ '2024-01-02'. O(log N + matches).

   "WHERE DATE(created_at) = '2024-01-01'"
   → engine doesn't know how DATE() relates to the index ordering.
   → falls back to a full table scan, calling DATE(...) on every row. O(N).
```

The index is sorted by the **raw value** of the column. Any function on that column scrambles the sort order from the index's perspective, so it can't seek a range.

## Why interviewers care
- Sub-second query → 30-second query → outage. SARGability is *the* prod-pager skill.
- One-line fixes, easy to grade.
- Requires having internalised what an index *physically is*.

## Common beginner confusion
- "But my query has the column in the WHERE!" — yes, but wrapped in a function. The optimizer can't see through it.
- "The optimizer should figure it out" — for some functions (`DATE(ts)`, `LOWER(col)`) it sometimes can in modern engines, but never bet on it. Write SARGable from the start.
- "I'll add an index on `DATE(created_at)`" — that works (functional index in Postgres / generated column in MySQL), but the range-form rewrite is usually simpler.

## Brute force approach
Add more indexes. Doesn't fix non-SARGable predicates — you'd need a functional index per function. Bloats storage and write amplification.

## Optimal approach
**Rewrite the predicate to expose the bare column to an existing index.** Push functions onto constants. Convert date-of equality to half-open range. Avoid leading wildcards; use trigram for fuzzy.

## Solution (SQL)

```sql
CREATE TABLE orders (
  id          BIGSERIAL PRIMARY KEY,
  user_id     INT,
  created_at  TIMESTAMPTZ
);
CREATE INDEX ix_orders_created ON orders(created_at);
-- 10M rows seeded with random dates over 2 years.
```

```sql
-- BEFORE (non-SARGable, ~30s seq scan):
SELECT * FROM orders WHERE DATE(created_at) = '2024-01-15';

-- AFTER (SARGable range, ~30ms index range scan):
SELECT * FROM orders
WHERE  created_at >= '2024-01-15'
  AND  created_at <  '2024-01-16';

-- Email case-insensitive:
-- BEFORE: WHERE LOWER(email) = 'a@x.com';
-- AFTER option 1 — functional index:
CREATE INDEX ix_users_email_lc ON users (LOWER(email));
SELECT * FROM users WHERE LOWER(email) = 'a@x.com';   -- now SARGable on the functional index

-- AFTER option 2 — store normalized:
ALTER TABLE users ADD COLUMN email_lc TEXT GENERATED ALWAYS AS (LOWER(email)) STORED;
CREATE INDEX ix_users_email_lc2 ON users(email_lc);

-- Fuzzy search:
-- BEFORE: WHERE name LIKE '%john%' (full scan).
-- AFTER: pg_trgm GIN index:
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX ix_users_name_trgm ON users USING gin (name gin_trgm_ops);
SELECT * FROM users WHERE name ILIKE '%john%';  -- uses trigram index
```

## Step-by-step dry run

EXPLAIN diff for the date query:

```
BEFORE:
  Seq Scan on orders  (cost=0.00..183205.00 rows=50 width=…)
    Filter: (date(created_at) = '2024-01-15'::date)
  → reads all 10M rows, calls DATE() on each.

AFTER:
  Index Range Scan using ix_orders_created on orders  (rows=~12000)
    Index Cond: ((created_at >= '2024-01-15') AND (created_at < '2024-01-16'))
  → seeks to first key ≥ 2024-01-15, walks ~12K leaf entries.
```

100M → 12K examined. Three orders of magnitude.

## How to think aloud in the interview
1. *"This query wraps `created_at` in `DATE()`. The B-tree index is sorted by raw `created_at`; any function on the column hides the order. Result: full table scan."*
2. *"Rewrite as a half-open range: `>= '2024-01-15' AND < '2024-01-16'`. Same logical answer, now SARGable."*
3. *"For case-insensitive search I'd build a functional index `LOWER(email)` or store a normalized column."*
4. *"Leading-wildcard LIKE can't use a B-tree at all — switch to pg_trgm GIN or move to a search engine."*
5. *"Always confirm with `EXPLAIN ANALYZE` — read the operator line and the buffer hits."*

## Important takeaways
- **Function on the indexed column = no index seek.** Move the function to the constant, or index the function.
- **Date-of equality → range form.**
- **Implicit cast** on a column kills the index too. Match types in predicates.
- **Leading wildcard** → trigram / full-text.
- `EXPLAIN ANALYZE` is the verification tool. Always.
- See `backend-data-prep/sql/03-query-optimization.md` and `04-indexing.md`.

## Variants
1. **`OR` blowing up.** `WHERE a=1 OR b=2` with separate indexes on `a` and `b` → planner often can't use either. Rewrite as `UNION ALL` of two SARGable queries.
2. **Composite index leftmost prefix.** `INDEX (a,b)` — `WHERE b=...` alone is non-SARGable. See `leftmost-prefix-puzzle.md`.
3. **Postgres "BRIN" for date columns.** If `created_at` correlates with insert order, BRIN gives near-zero storage for date-range filtering.

## Revision notes

> **SARGability cram block**
> - SARGable = engine can seek the index using the predicate.
> - Function on indexed column → no seek. Move function to constant.
> - Implicit cast on column → no seek. Match types.
> - Leading wildcard `LIKE '%foo'` → no B-tree seek. Use trigram/FTS.
> - `OR` across columns → usually full scan; rewrite as UNION ALL.
> - Date equality → half-open range.
> - Functional index materializes `f(col)` → SARGable again.
> - Verify with `EXPLAIN ANALYZE`.
> - One-line fix; 1000× speedup is normal.
