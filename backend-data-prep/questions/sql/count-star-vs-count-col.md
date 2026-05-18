# COUNT(*) vs COUNT(col) vs COUNT(DISTINCT col)

## Source / Origin
- Universal interview probe. LeetCode #1683, #1517 indirectly.
- Real prod: misreported "active users", duplicated KPIs caused by `COUNT(*)` where `COUNT(DISTINCT user_id)` was meant.

## Why this question matters in interviews
"`SELECT COUNT(*) FROM t` — how is that different from `COUNT(user_id)`?" sounds trivial. The trap: most candidates answer "same thing" and walk into the NULL-handling buzzsaw. Interviewers ask this because it reveals whether you understand the **NULL-skipping rule for column aggregates**, and whether you've debugged a wrong-metric incident in production.

It also surfaces understanding of **`COUNT(DISTINCT)`** cost: a `DISTINCT` count requires a sort or hash deduplication, often 10× slower than a plain `COUNT(*)`. Knowing when to reach for `approx_count_distinct` or HyperLogLog is the senior touch.

## Concepts involved

### Syntax to lock in
```sql
-- 1. COUNT(*)      — every row, NULLs included
SELECT COUNT(*) FROM orders;

-- 2. COUNT(col)    — non-NULL values of col
SELECT COUNT(customer_id) FROM orders;        -- rows where customer_id IS NOT NULL

-- 3. COUNT(DISTINCT col) — distinct non-NULL values
SELECT COUNT(DISTINCT customer_id) FROM orders;

-- 4. COUNT(1) / COUNT('x') — equivalent to COUNT(*) on modern planners (legacy idiom)
SELECT COUNT(1) FROM orders;

-- 5. Approximate distinct count (cheap)
SELECT approx_count_distinct(customer_id) FROM orders;   -- BigQuery/Snowflake/Redshift
-- Postgres: HyperLogLog extension or manual
```

### Edge cases / interview traps
1. **`COUNT(col)` skips NULLs in that column.** Beginners assume it's the same as `COUNT(*)`. Spot the difference: `COUNT(*) - COUNT(col) = number of NULL rows in col`.
2. **`COUNT(*) FROM empty_table`** returns `0`, not NULL. But `SUM(col) FROM empty_table` returns NULL. Asymmetry to remember.
3. **`COUNT(1)` vs `COUNT(*)`** — identical in Postgres / MySQL / Oracle. The "COUNT(1) is faster" myth is from Oracle 7 era; long fixed.
4. **`COUNT(DISTINCT col)` cost.** Forces a sort or hash on the column. On 100M rows that's expensive; `approx_count_distinct` is sub-second with ~2% error.
5. **`COUNT(DISTINCT a, b)`** — Postgres requires `COUNT(DISTINCT (a,b))` (row constructor). MySQL accepts `COUNT(DISTINCT a, b)` directly.
6. **`COUNT(*)` over a window**: `COUNT(*) OVER (PARTITION BY ...)` doesn't dedup — it counts all rows in the partition.
7. **`COUNT(*) OVER ()`** with no PARTITION returns total row count next to every row — handy for ratios.
8. **EXPLAIN of `COUNT(*)`** sometimes uses an index-only scan or a `Parallel Aggregate`. `COUNT(col)` may fall back to a heap scan if `col` isn't in the index.

## Mental Model

```
   orders:  id  customer_id   product
            ──  ───────────   ───────
            1   42            apple
            2   42            apple     ← duplicate customer
            3   NULL          banana    ← anonymous order
            4   7             cherry
            5   NULL          banana

   COUNT(*)                  = 5  (all rows)
   COUNT(customer_id)        = 3  (rows where customer_id IS NOT NULL)
   COUNT(DISTINCT customer_id) = 2  (just 42 and 7; NULL skipped)
   COUNT(DISTINCT product)   = 3  (apple, banana, cherry)
   COUNT(*) - COUNT(customer_id) = 2  (anonymous orders)
```

`*` means "any row". A column argument means "non-NULL of this column". `DISTINCT` adds deduplication. That's it.

## Why interviewers care
- **Production metrics** depend on getting this right. "Active users this week" is `COUNT(DISTINCT user_id)`, not `COUNT(*)`.
- Tests **NULL handling** in a non-anti-join context.
- Reveals **cost intuition** for `DISTINCT` aggregates.

## Common beginner confusion
- "`COUNT(*)` and `COUNT(col)` are the same" — only when `col` is `NOT NULL`.
- "`COUNT(1)` is faster than `COUNT(*)`" — myth.
- "`COUNT(DISTINCT a, b)` is the same as `COUNT(DISTINCT a) + COUNT(DISTINCT b)`" — emphatically no. The first counts unique pairs; the second counts each column's uniques.
- "Approx count is wrong and never acceptable" — wrong; it's the default at warehouse scale.

## Brute force approach
`SELECT COUNT(*) FROM (SELECT DISTINCT col FROM t) x` is the long form of `COUNT(DISTINCT col)`. Same plan, more typing.

For "active users" people often do `COUNT(*) FROM (SELECT user_id FROM events GROUP BY user_id)`. That's `COUNT(DISTINCT)` in disguise — verbose but correct.

## Optimal approach
Match the function to the question:
- "How many rows?" → `COUNT(*)`.
- "How many non-NULL values?" → `COUNT(col)`.
- "How many distinct values?" → `COUNT(DISTINCT col)`, or `approx_count_distinct` at warehouse scale.

For `COUNT(*)` performance, ensure the smallest index can be index-only-scanned (Postgres needs the visibility map up to date — run `VACUUM`).

## Solution (SQL)

```sql
CREATE TABLE orders (
  id          SERIAL PRIMARY KEY,
  customer_id INT,      -- nullable: anonymous orders allowed
  product     TEXT,
  amount      NUMERIC
);
INSERT INTO orders (customer_id, product, amount) VALUES
 (42,'apple',5),(42,'apple',5),(NULL,'banana',3),(7,'cherry',7),(NULL,'banana',3);
```

```sql
-- KPI dashboard query: 4 metrics in one shot
SELECT
  COUNT(*)                       AS total_orders,            -- 5
  COUNT(customer_id)             AS attributed_orders,       -- 3
  COUNT(*) - COUNT(customer_id)  AS anonymous_orders,        -- 2
  COUNT(DISTINCT customer_id)    AS unique_customers,        -- 2
  COUNT(DISTINCT product)        AS unique_products,         -- 3
  SUM(amount)                    AS total_revenue
FROM orders;

-- Window: count per partition without losing rows
SELECT id, customer_id,
       COUNT(*) OVER (PARTITION BY customer_id) AS orders_for_this_customer
FROM   orders;
```

## Step-by-step dry run

For our 5-row table:

```
Iteration: for each row, accumulate:
  total_orders++       always.
  attributed_orders++  if customer_id IS NOT NULL.
  unique_customers     hash-set of non-NULL customer_id values.
  unique_products      hash-set of non-NULL product values.
  total_revenue        += amount (NULLs skipped).
```

Final state: `{total:5, attributed:3, anon:2, customers:{42,7}=2, products:{apple,banana,cherry}=3, revenue:23}`.

A planner with an index on `customer_id`:
- `COUNT(*)` → Parallel Index Only Scan on the smallest index.
- `COUNT(DISTINCT customer_id)` → Sort + Unique, or Hash Aggregate.

## How to think aloud in the interview
1. *"Three flavours: `COUNT(*)` for rows, `COUNT(col)` for non-NULL values in that column, `COUNT(DISTINCT col)` for unique values."*
2. *"The difference between `COUNT(*)` and `COUNT(customer_id)` here is exactly the number of anonymous orders — three NULL rows means a gap."*
3. *"`COUNT(DISTINCT)` is expensive — sort or hash on the column. At warehouse scale I'd reach for `approx_count_distinct` (HLL)."*
4. *"`COUNT(1)` and `COUNT(*)` produce identical plans on any modern engine. Style preference only."*
5. *"For multi-column distinct: `COUNT(DISTINCT (a,b))` in Postgres; `COUNT(DISTINCT a, b)` in MySQL. Subtle dialect difference."*

## Important takeaways
- `COUNT(*)` counts rows including NULL rows.
- `COUNT(col)` counts rows where `col IS NOT NULL`.
- `COUNT(DISTINCT col)` deduplicates non-NULL values; costly.
- `COUNT(1) == COUNT(*)` always; the "faster" myth is dead.
- `SUM`/`AVG`/`MIN`/`MAX` ignore NULL; `COUNT(*)` does not.
- See `backend-data-prep/sql/01-sql-fundamentals.md` "Aggregates" for theory.

## Variants
1. **`FILTER (WHERE ...)`** — conditional counts in one row: `COUNT(*) FILTER (WHERE status='paid')`. Standard SQL; Postgres; not in older MySQL.
2. **`approx_count_distinct`** — BigQuery / Snowflake. Postgres needs `hll` extension or `count_estimator`.
3. **`COUNT(*) OVER ()`** — total rows next to every row. Useful for "show row X of Y" pagination footers.

## Revision notes

> **COUNT cram block**
> - `COUNT(*)`        → all rows (NULLs included).
> - `COUNT(col)`      → non-NULL values of col.
> - `COUNT(DISTINCT col)` → unique non-NULL values.
> - `COUNT(*) - COUNT(col)` = NULL count for that column.
> - `COUNT(1) == COUNT(*)` — myth-buster.
> - On empty table: `COUNT(*) = 0`, but `SUM(col) = NULL`.
> - DISTINCT count is expensive — sort/hash.
> - Warehouse: `approx_count_distinct` (HLL).
> - Multi-column: PG `(a,b)`; MySQL `a, b`.
> - Conditional count: `FILTER (WHERE ...)` or `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`.
> - Window: `COUNT(*) OVER (PARTITION BY x)` doesn't dedup.
