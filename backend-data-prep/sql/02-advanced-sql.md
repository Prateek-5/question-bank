# Advanced SQL

## Why this matters in backend interviews

- Mid-to-senior **SQL screens** almost always include a window-function or CTE problem. (LeetCode-style: "rank users by their N-th purchase", "running 7-day average", "top 3 per group".)
- **Machine coding** problems often need aggregation patterns — running balance, sliding window, gap detection.
- **System design** rounds touch advanced SQL when discussing analytics layers, reporting tables, or read-optimized views.
- **Debugging** — recognising whether a window function or a self-join is the right tool can collapse a 200-line script into 5 lines.

This is the topic that **separates "writes SQL" from "owns the data layer."**

---

## Core concepts

### Window functions

A window function computes a value **per row** using a window of other rows — *without* collapsing rows (that's what GROUP BY does).

```
SELECT col,
       window_function() OVER (
         PARTITION BY ...   -- like GROUP BY, but doesn't collapse
         ORDER BY ...       -- ordering inside the partition
         ROWS BETWEEN ...   -- frame: subset of the partition visible to this row
       )
FROM t;
```

#### The functions

| Function | Purpose |
|---|---|
| `ROW_NUMBER()` | Unique sequential number per partition |
| `RANK()` | Ranks with gaps on ties (1,1,3) |
| `DENSE_RANK()` | Ranks without gaps (1,1,2) |
| `NTILE(n)` | Buckets rows into n groups |
| `LAG(col, offset, default)` | Previous row's value |
| `LEAD(col, offset, default)` | Next row's value |
| `FIRST_VALUE / LAST_VALUE` | First/last in frame |
| `SUM / AVG / COUNT / MIN / MAX OVER (...)` | Aggregate over window |

#### Frame specification (critical, often missed)

The default frame for ranking functions is the entire partition. The default for *aggregate* window functions is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.

```sql
-- Running total — frame defaults to all preceding + current row
SUM(amount) OVER (PARTITION BY user_id ORDER BY created_at)

-- 7-day rolling average
AVG(amount) OVER (
  PARTITION BY user_id
  ORDER BY day
  RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW
)

-- Last 5 rows including current
SUM(qty) OVER (ORDER BY created_at ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)
```

`ROWS` = physical rows. `RANGE` = logical (by value). They differ on ties — `ROWS` includes 1 row even if ties exist; `RANGE` includes all ties.

### CTEs (Common Table Expressions)

```sql
WITH paid_orders AS (
  SELECT * FROM orders WHERE status = 'PAID'
),
recent AS (
  SELECT * FROM paid_orders WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT user_id, COUNT(*) FROM recent GROUP BY user_id;
```

- **Readability** — break complex queries into named steps
- **Postgres pre-12**: CTEs were an **optimization fence** (materialized). Now they inline by default.
- **MySQL 8+ and Postgres**: support `RECURSIVE` for graph/tree traversal

#### Recursive CTE — hierarchy / graph traversal

```sql
-- Find all reports under a manager
WITH RECURSIVE reports AS (
  SELECT id, name, manager_id, 1 AS depth FROM employees WHERE id = 42
  UNION ALL
  SELECT e.id, e.name, e.manager_id, r.depth + 1
  FROM employees e JOIN reports r ON e.manager_id = r.id
)
SELECT * FROM reports;
```

Use cases: org charts, comment threads, category trees, dependency graphs, BOM (bill of materials).

### LATERAL joins (Postgres)

A `LATERAL` subquery can reference columns from preceding `FROM` items — useful for **top-N-per-group**, *per-row* aggregation, and unnesting arrays.

```sql
SELECT u.id, last3.body, last3.sent_at
FROM users u
LEFT JOIN LATERAL (
  SELECT body, sent_at FROM messages m
  WHERE m.user_id = u.id
  ORDER BY sent_at DESC
  LIMIT 3
) last3 ON true;
```

This is often the **fastest** way to do top-N-per-group, especially with an index on `(user_id, sent_at DESC)`.

### Pivots / unpivots

PostgreSQL doesn't have a native `PIVOT` keyword. Patterns:

```sql
-- Pivot orders per month
SELECT user_id,
       SUM(CASE WHEN month = 1 THEN amount END) AS jan,
       SUM(CASE WHEN month = 2 THEN amount END) AS feb,
       SUM(CASE WHEN month = 3 THEN amount END) AS mar
FROM monthly_orders
GROUP BY user_id;

-- FILTER clause (cleaner)
SELECT user_id,
       SUM(amount) FILTER (WHERE month = 1) AS jan,
       SUM(amount) FILTER (WHERE month = 2) AS feb
FROM monthly_orders
GROUP BY user_id;
```

`FILTER (WHERE …)` works with any aggregate in Postgres — much cleaner than `CASE WHEN`.

### GROUPING SETS, ROLLUP, CUBE

```sql
-- Subtotals per (region, product) AND per region AND grand total
SELECT region, product, SUM(qty)
FROM sales
GROUP BY ROLLUP (region, product);

-- Same but every dimension combination
GROUP BY CUBE (region, product);

-- Explicit
GROUP BY GROUPING SETS ((region, product), (region), ());
```

Common in reporting/analytics dashboards.

### Set operations

- `UNION` — concat + dedup (sort cost)
- `UNION ALL` — concat
- `INTERSECT` — common rows
- `EXCEPT` (MySQL: `MINUS`) — rows in A not in B

Use these for set logic; often clearer than NOT IN / NOT EXISTS.

### Upserts

```sql
-- Postgres
INSERT INTO inventory (sku, qty) VALUES ('A1', 10)
ON CONFLICT (sku) DO UPDATE SET qty = inventory.qty + EXCLUDED.qty;

-- MySQL
INSERT INTO inventory (sku, qty) VALUES ('A1', 10)
ON DUPLICATE KEY UPDATE qty = qty + VALUES(qty);
```

Used heavily for idempotent writes, leaderboards, counters.

### JSON support

```sql
-- Postgres JSONB
SELECT data->>'email' FROM users WHERE data->>'role' = 'admin';
CREATE INDEX ON users USING gin (data jsonb_path_ops);
SELECT * FROM users WHERE data @> '{"role":"admin"}';

-- MySQL JSON
SELECT data->>'$.email' FROM users WHERE JSON_EXTRACT(data, '$.role') = 'admin';
```

JSONB is queryable and indexable. Don't use it as a replacement for schema — use it for semi-structured extension data.

### Common misconceptions

- "CTEs are always materialized" — only in Postgres < 12. Modern engines inline them.
- "Window functions are slow" — they often **replace** N self-joins; usually a big win.
- "PARTITION BY in `OVER` is the same as GROUP BY" — no; partitioning doesn't collapse rows.
- "DISTINCT before ORDER BY guarantees order" — it doesn't.
- "Recursive CTEs are slow" — they can be fine with proper indexes and depth limits.

### Interview traps

1. `RANK` vs `DENSE_RANK` vs `ROW_NUMBER` — interviewers will ask "what if there's a tie?"
2. **Frame default** — `SUM() OVER (ORDER BY x)` includes all preceding + current. Without `ORDER BY`, the frame is the whole partition.
3. `LAST_VALUE` requires explicit frame — by default frame ends at current row, so `LAST_VALUE` returns the current row's value! Use `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`.
4. Window functions can't be in `WHERE` directly — wrap in a subquery.
5. `GROUP BY ROLLUP` produces NULL for the rolled-up dimension — use `GROUPING(col)` to distinguish "real NULL" from "subtotal NULL".

---

## Real examples

### E-commerce — 7-day rolling revenue
```sql
SELECT day,
       SUM(revenue) OVER (
         ORDER BY day
         RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW
       ) AS rolling_7d
FROM daily_revenue
ORDER BY day;
```

### Top 3 customers by revenue per region
```sql
SELECT region, customer_id, revenue
FROM (
  SELECT region, customer_id, revenue,
         RANK() OVER (PARTITION BY region ORDER BY revenue DESC) AS rk
  FROM customer_revenue
) t
WHERE rk <= 3;
```

### Chat — find conversation gaps > 1 hour (session boundaries)
```sql
SELECT user_id, sent_at,
       sent_at - LAG(sent_at) OVER (PARTITION BY user_id ORDER BY sent_at) AS gap
FROM messages;

-- Sessionize: increment a session counter when gap > 1 hour
SELECT *,
       SUM(CASE WHEN gap > INTERVAL '1 hour' OR gap IS NULL THEN 1 ELSE 0 END)
         OVER (PARTITION BY user_id ORDER BY sent_at) AS session_id
FROM (
  SELECT *, sent_at - LAG(sent_at) OVER (PARTITION BY user_id ORDER BY sent_at) AS gap
  FROM messages
) t;
```

This pattern — `LAG` for gap detection, then a running `SUM` to create groups — is the **session/gaps-and-islands** technique. Comes up in interviews repeatedly.

### Analytics — funnel conversion
```sql
WITH steps AS (
  SELECT user_id,
         MIN(CASE WHEN event = 'view'    THEN ts END) AS viewed,
         MIN(CASE WHEN event = 'cart'    THEN ts END) AS carted,
         MIN(CASE WHEN event = 'checkout' THEN ts END) AS checked,
         MIN(CASE WHEN event = 'paid'    THEN ts END) AS paid
  FROM events GROUP BY user_id
)
SELECT
  COUNT(*) FILTER (WHERE viewed IS NOT NULL) AS viewed,
  COUNT(*) FILTER (WHERE carted IS NOT NULL) AS carted,
  COUNT(*) FILTER (WHERE checked IS NOT NULL) AS checked,
  COUNT(*) FILTER (WHERE paid IS NOT NULL) AS paid
FROM steps;
```

### Payments — running balance per account
```sql
SELECT account_id, txn_id, amount,
       SUM(amount) OVER (PARTITION BY account_id ORDER BY ts) AS balance
FROM transactions;
```

### Inventory — first and last sale per product
```sql
SELECT product_id, sale_id, ts,
       FIRST_VALUE(ts) OVER (PARTITION BY product_id ORDER BY ts) AS first_sale,
       LAST_VALUE(ts)  OVER (PARTITION BY product_id ORDER BY ts
         ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_sale
FROM sales;
```

---

## Common interview questions

1. Difference between `RANK`, `DENSE_RANK`, `ROW_NUMBER`.
2. Write top-N-per-group with a window function.
3. Running total per user.
4. 7-day moving average.
5. Find the longest streak of consecutive login days (gaps and islands).
6. Recursive CTE: traverse an employee hierarchy.
7. Pivot rows into columns without `PIVOT`.
8. What is `LATERAL` and when do you use it?
9. Difference between `ROWS` and `RANGE` in window frames.
10. Find sessions defined by gaps > X minutes.
11. Calculate retention: of users who signed up in Jan, how many came back in Feb?
12. Solve: 2nd, 3rd, ..., Nth highest salary.

---

## Detailed answers

### 1. RANK vs DENSE_RANK vs ROW_NUMBER
For salaries `(100, 100, 90)`:
- `ROW_NUMBER` → 1, 2, 3
- `RANK` → 1, 1, 3 (skip 2)
- `DENSE_RANK` → 1, 1, 2

Use `ROW_NUMBER` when you want exactly one row per group (e.g., latest order per user). Use `DENSE_RANK` for "top N salaries" when ties should share rank without leaving gaps.

### 2. Top-N-per-group
```sql
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
  FROM orders
) t WHERE rn <= 3;
```
With a large dataset and an index on `(user_id, created_at DESC)`, a `LATERAL` variant can be faster:
```sql
SELECT u.id, recent.*
FROM users u
LEFT JOIN LATERAL (
  SELECT * FROM orders WHERE user_id = u.id ORDER BY created_at DESC LIMIT 3
) recent ON true;
```

### 3. Running total
```sql
SUM(amount) OVER (PARTITION BY user_id ORDER BY ts ROWS UNBOUNDED PRECEDING)
```
(`ROWS UNBOUNDED PRECEDING` = same as default `RANGE` for monotonic series, but `ROWS` avoids tie issues.)

### 4. 7-day moving average
```sql
AVG(revenue) OVER (
  ORDER BY day
  RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW
)
```
`RANGE` is preferred here so missing days don't shift the window.

### 5. Longest streak — classic gaps and islands
```sql
WITH steps AS (
  SELECT user_id, login_date,
         login_date - (ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date))::int * INTERVAL '1 day' AS grp
  FROM (SELECT DISTINCT user_id, login_date FROM logins) t
)
SELECT user_id, MIN(login_date), MAX(login_date), COUNT(*) AS streak
FROM steps
GROUP BY user_id, grp
ORDER BY streak DESC LIMIT 1;
```
Trick: subtract row-number-as-days from the date — consecutive dates yield the same difference, so a GROUP BY collapses them into runs.

### 6. Recursive CTE
```sql
WITH RECURSIVE tree AS (
  SELECT id, name, manager_id, 0 AS depth
  FROM employees WHERE manager_id IS NULL
  UNION ALL
  SELECT e.id, e.name, e.manager_id, t.depth + 1
  FROM employees e JOIN tree t ON e.manager_id = t.id
)
SELECT * FROM tree ORDER BY depth, id;
```
Add `WHERE depth < 10` to bound recursion depth in cycles.

### 7. Pivot without PIVOT
Use `CASE WHEN` or `FILTER` aggregates (Postgres). See JSON examples earlier.

### 8. LATERAL
A correlated subquery in the FROM clause — exposes outer columns into the subquery. Essential for top-N-per-group with good index usage and for unnesting per-row.

### 9. ROWS vs RANGE
- `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` → physical 7 rows
- `RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW` → all rows within the value-range

`RANGE` requires an `ORDER BY` on a numeric/date column.

### 10. Sessions by gap
```sql
WITH gaps AS (
  SELECT user_id, ts,
         ts - LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) AS gap
  FROM events
), sessions AS (
  SELECT *, SUM(CASE WHEN gap > INTERVAL '30 min' OR gap IS NULL THEN 1 ELSE 0 END)
              OVER (PARTITION BY user_id ORDER BY ts) AS session_id
  FROM gaps
)
SELECT user_id, session_id, MIN(ts), MAX(ts), COUNT(*)
FROM sessions GROUP BY user_id, session_id;
```

### 11. Retention
```sql
WITH cohorts AS (
  SELECT id, DATE_TRUNC('month', created_at) AS cohort
  FROM users
), active AS (
  SELECT user_id, DATE_TRUNC('month', ts) AS active_month
  FROM events GROUP BY user_id, DATE_TRUNC('month', ts)
)
SELECT c.cohort, a.active_month, COUNT(DISTINCT c.id)
FROM cohorts c JOIN active a ON a.user_id = c.id
GROUP BY c.cohort, a.active_month;
```

### 12. Nth highest salary
```sql
SELECT DISTINCT salary FROM (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rk FROM employees
) t WHERE rk = :n;
```

---

## Practical coding examples

### Customer LTV with revenue percentile
```sql
SELECT customer_id, total,
       NTILE(10) OVER (ORDER BY total DESC) AS decile,
       PERCENT_RANK() OVER (ORDER BY total) AS pct
FROM (
  SELECT customer_id, SUM(amount) AS total
  FROM orders WHERE status = 'PAID'
  GROUP BY customer_id
) t;
```

### Cumulative distinct count (a known hard one)
```sql
-- Not directly supported as a window function; trick using arrays in Postgres
SELECT day, cardinality((
  SELECT array_agg(DISTINCT user_id)
  FROM events e2 WHERE e2.day <= e.day
)) AS cumulative_users
FROM (SELECT DISTINCT day FROM events) e
ORDER BY day;
```

Better in practice: use HyperLogLog (`hll` extension) for approximate cumulative distinct.

### Hierarchical depth-limited fetch
```sql
WITH RECURSIVE tree AS (
  SELECT id, parent_id, 0 AS depth FROM comments WHERE id = :root
  UNION ALL
  SELECT c.id, c.parent_id, t.depth + 1
  FROM comments c JOIN tree t ON c.parent_id = t.id
  WHERE t.depth < 5
)
SELECT * FROM tree;
```

---

## Common mistakes

- Using `WHERE` to filter on a window function (illegal; wrap in subquery)
- Forgetting `ORDER BY` inside `OVER()` for accumulating windows
- Using `LAST_VALUE` without an explicit frame (returns current row)
- Treating recursive CTE as cheap; it iterates and joins each level
- Mixing `RANGE` and `ROWS` when ties matter
- Using `OFFSET` for pagination on a heavy table (use keyset)

---

## Senior engineer discussion points

- **When window functions blow up:** big partitions force big sorts. Without an index on `PARTITION BY, ORDER BY`, you pay an external sort cost.
- **Materialized views** for heavy window-function reports. Refresh on a schedule.
- **CTE inlining behavior** changed in Postgres 12; can pin with `WITH ... AS MATERIALIZED`.
- **LATERAL + index** beats window functions in top-N-per-group when the per-group N is small.
- **Recursive CTE cycle detection** — Postgres 14+ supports `CYCLE` clause.
- **Read replicas for heavy analytics** queries to protect OLTP; or move to OLAP store (ClickHouse, BigQuery).
- **`pg_stat_statements`** to find regressing queries after a deploy.

---

## Revision notes

- `ROW_NUMBER` unique • `RANK` gaps • `DENSE_RANK` no gaps
- Window functions don't collapse rows; GROUP BY does
- Default frame: ranking → entire partition; aggregate → preceding rows + current
- `LAST_VALUE` needs explicit `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`
- `LATERAL` = "for each outer row, run this subquery"
- Gaps & islands trick: subtract `ROW_NUMBER` to find consecutive groups
- Recursive CTE = base case + recursive case + UNION ALL
- `FILTER (WHERE …)` is the cleanest pivot
- Postgres ≥ 12 inlines CTEs unless `AS MATERIALIZED`
