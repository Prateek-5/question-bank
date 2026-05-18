# Function On Indexed Column Trap

## Source / Origin
- Senior SQL screen at every product company. "Why isn't this query using the index?"
- Real prod: a `DATE(created_at)` filter that ran for 30 seconds; fixed by half-open range.

## Why this question matters in interviews
This is the most-asked **performance debugging puzzle** because the fix is literally one character — and the failure mode is silent (the query returns correct data, just at 1000× the cost). Candidates who pattern-match this in five seconds save companies thousands of dollars in unnecessary scaling.

A close cousin of `query-rewrite-for-index.md`, but here the spotlight is on the **function** specifically, the **functional index** alternative, and the **EXPLAIN** signature you're hunting for.

## Concepts involved

### Syntax to lock in
```sql
-- ANTIPATTERNS:
WHERE DATE(created_at)            = '2024-01-15';
WHERE LOWER(email)                = 'a@x.com';
WHERE SUBSTR(phone, 1, 3)         = '555';
WHERE created_at::date            = '2024-01-15';
WHERE EXTRACT(YEAR FROM ts)       = 2024;
WHERE TRIM(name)                  = 'John';
WHERE name || ''                  = 'John';     -- accidental concat
WHERE id + 0                      = 42;          -- accidental arithmetic
WHERE COALESCE(deleted_at, 'inf') >  now();      -- function on column

-- FIXES:
-- Option A — push function onto the constant:
WHERE created_at >= '2024-01-15' AND created_at < '2024-01-16';
WHERE email      = LOWER('A@X.COM');      -- only if column is already normalized
WHERE phone LIKE '555%';                   -- if leading-prefix LIKE is desired

-- Option B — functional / expression index:
CREATE INDEX ix_users_email_lc ON users (LOWER(email));
CREATE INDEX ix_orders_day     ON orders (DATE(created_at));

-- Option C — generated column + plain index:
ALTER TABLE users ADD COLUMN email_lc TEXT GENERATED ALWAYS AS (LOWER(email)) STORED;
CREATE INDEX ix_users_email_lc2 ON users(email_lc);
```

### Edge cases / interview traps
1. **The function might be invisible.** `WHERE created_at::date = '2024-01-15'` is a cast, which is a function call.
2. **Implicit cast = invisible function.** `WHERE varchar_col = 42` casts the column to int (or 42 to text) — engine-dependent.
3. **Postgres `now()` and `current_date`** on the constant side are fine. On the column side they aren't (`WHERE col + interval ... > now()`).
4. **Functional indexes must match the exact function.** Index on `LOWER(email)`; query `WHERE lower(email)=...` works. Query `WHERE LOWER(TRIM(email))=...` does not.
5. **Index on volatile functions** is illegal. `RANDOM()`, `NOW()` can't be in an index expression.
6. **Generated stored columns** double the storage but make every index plain. Trade-off.
7. **MySQL functional indexes** arrived in 8.0.13. Older MySQL needs generated columns or stored shadow columns.
8. **The "but I'll just add an index on the function" knee-jerk.** Sometimes correct, but the half-open-range rewrite is usually simpler and doesn't add write cost.

## Mental Model

```
   index ix_orders_created on orders(created_at):

   leaf:  [2024-01-15 00:00:00] → row 47
          [2024-01-15 03:11:00] → row 02
          [2024-01-15 13:42:00] → row 88
          [2024-01-16 00:05:00] → row 14

   Query: WHERE DATE(created_at) = '2024-01-15'
   Engine: "I'd love to seek the index, but you've wrapped my column in DATE().
            I have no idea which leaf entries DATE() will return '2024-01-15' for.
            Falling back to scanning every row and computing DATE() on each."

   Query: WHERE created_at >= '2024-01-15' AND created_at < '2024-01-16'
   Engine: "Seek to leftmost key ≥ '2024-01-15'. Walk leaves until I hit '2024-01-16'.
            Done. 12K rows examined out of 10M."
```

The index leaves are sorted by the **raw value**. Any function on the column makes that ordering useless to the engine.

## Why interviewers care
- Single biggest source of one-day-fix prod incidents.
- Tests whether the candidate can read EXPLAIN and pattern-match in seconds.
- Probes deeper: does the candidate know about functional indexes? Generated columns?

## Common beginner confusion
- "But my query is so simple!" — yes, simplicity isn't speed. The function call defeats the index.
- "I'll cast for safety" — that cast is the problem.
- "The optimizer is supposed to figure it out" — modern Postgres can sometimes unwrap `DATE(ts) = 'x'` into a range, but never bet on it.
- "Functional index is always the answer" — no; half-open-range rewrite is cheaper.

## Brute force approach
Sequential scan + recomputing the function on every row. That's exactly what you get when you leave the antipattern in. Correct but linear-time on millions of rows.

## Optimal approach
1. **Rewrite the predicate** to expose the bare column. Half-open ranges, prefix LIKE, normalized-constant comparisons.
2. **If rewrite is impossible**, build a functional / expression index that materializes the function's output.
3. **Verify with EXPLAIN ANALYZE** — look for `Index [Range] Scan` instead of `Seq Scan` on a large table.

## Solution (SQL)

```sql
CREATE TABLE orders (
  id          BIGSERIAL PRIMARY KEY,
  user_id     INT,
  created_at  TIMESTAMPTZ
);
CREATE INDEX ix_orders_created ON orders(created_at);
-- imagine 10M rows.
```

```sql
-- BEFORE (Seq Scan, ~30s):
EXPLAIN ANALYZE
SELECT * FROM orders WHERE DATE(created_at) = '2024-01-15';

-- After (Index Range Scan, ~30ms):
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE  created_at >= '2024-01-15'
  AND  created_at <  '2024-01-16';

-- If the report needs DATE-bucketed queries (often):
CREATE INDEX ix_orders_day ON orders ((DATE(created_at)));
EXPLAIN ANALYZE
SELECT * FROM orders WHERE DATE(created_at) = '2024-01-15';   -- now uses ix_orders_day
```

For email normalization:

```sql
CREATE TABLE users (id INT, email TEXT);
CREATE UNIQUE INDEX ix_users_email_lc ON users (LOWER(email));

INSERT INTO users VALUES (1, 'Alice@x.com');
-- forced uniqueness regardless of case via functional unique index.

SELECT * FROM users WHERE LOWER(email) = LOWER('ALICE@X.COM');
-- index hit because the predicate exactly matches the index expression.
```

## Step-by-step dry run

Postgres EXPLAIN (10M rows, ~12K matching):

```
BEFORE:
  Gather  (cost=1000.00..184333.00 rows=50000 width=33)
    Workers Planned: 2
    ->  Parallel Seq Scan on orders
        Filter: (date(created_at) = '2024-01-15'::date)
        Rows Removed by Filter: 4,996,000
  Execution Time: 28,210 ms

AFTER:
  Index Scan using ix_orders_created on orders
    Index Cond: ((created_at >= '2024-01-15') AND (created_at < '2024-01-16'))
  Execution Time: 32 ms
```

900× faster. Same answer. One-character rewrite.

## How to think aloud in the interview
1. *"`DATE(created_at)` is a function applied to an indexed column — that defeats the B-tree's sort order, so the planner falls back to a sequential scan."*
2. *"Two fixes: rewrite as a half-open range (`>= '2024-01-15' AND < '2024-01-16'`), or build a functional index on `DATE(created_at)`."*
3. *"I'd start with the rewrite — same answer, no extra storage, no write amplification."*
4. *"If the app emits date-of queries a lot and rewrites aren't practical, then the functional index is justified."*
5. *"Validate with `EXPLAIN ANALYZE`. The signature I'm hunting for is `Seq Scan` becoming `Index Scan` and execution time dropping orders of magnitude."*

## Important takeaways
- Function on column = no index seek.
- Cast counts as a function. Implicit cast counts too.
- Fix priority: (1) rewrite predicate, (2) functional index, (3) generated column.
- Functional index must exactly match the function in the predicate.
- Always validate with `EXPLAIN ANALYZE`.
- See `backend-data-prep/sql/03-query-optimization.md` "SARGability".

## Variants
1. **`TIMEZONE` quirk.** `WHERE created_at AT TIME ZONE 'UTC' >= ...` applies a function — non-SARGable. Store one canonical TZ.
2. **MySQL old `DATE(col) = ...`** had a special-case optimizer rule. Modern MySQL still benefits from the rewrite — don't rely on the special-case.
3. **`COLLATE` mismatch.** `WHERE col COLLATE "C" = 'x'` doesn't use an index built with default collation. Match collations.

## Revision notes

> **Function-on-column trap cram block**
> - Wrapping indexed column in a function → no index seek.
> - Casts and implicit conversions count as functions.
> - Fix #1: rewrite to half-open range / LOWER-on-constant / prefix LIKE.
> - Fix #2: functional / expression index — must match the predicate exactly.
> - Fix #3: generated stored column + plain index.
> - Postgres: `CREATE INDEX ix ON t ((expr))`; MySQL ≥ 8.0.13.
> - No indexes on volatile functions (`NOW()`, `RANDOM()`).
> - Verify with `EXPLAIN ANALYZE`: Seq Scan → Index Scan signal.
> - One-character fix; 1000× speedup pattern.
