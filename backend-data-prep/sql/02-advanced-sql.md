# Advanced SQL

## Why this matters in backend interviews

- Mid-to-senior **SQL screens** almost always include a window-function or CTE problem. (LeetCode-style: "rank users by their N-th purchase", "running 7-day average", "top 3 per group".)
- **Machine coding** problems often need aggregation patterns — running balance, sliding window, gap detection.
- **System design** rounds touch advanced SQL when discussing analytics layers, reporting tables, or read-optimized views.
- **Debugging** — recognising whether a window function or a self-join is the right tool can collapse a 200-line script into 5 lines.

This is the topic that **separates "writes SQL" from "owns the data layer."**

---

## First principles — what's new vs fundamentals

`01-sql-fundamentals.md` ended with: *SQL is "declare the set you want," GROUP BY collapses rows into piles.*

Advanced SQL adds three superpowers that all share one theme — **looking at neighbors without collapsing the row**:

1. **Window functions** — "For each row, also tell me something about its neighbors in some ordering."
2. **CTEs (recursive especially)** — "Define a relation in terms of itself; let the engine iterate until fixpoint."
3. **LATERAL / correlated FROM-clause** — "For each outer row, run this little query and staple the result on."

If GROUP BY is "*collapse* each pile into one row," window functions are "*walk* each pile in order and annotate every row with context." That single distinction is the heart of advanced SQL.

### Why interviewers care

- **Set-based thinking under pressure** — the candidate who reaches for a window function instead of three self-joins is the candidate who can ship the analytics layer.
- **Query planning intuition** — windowing has a cost model (partition + sort). Can you explain when it'll be expensive?
- **Modeling recursion declaratively** — recursive CTEs test whether you can express a fixed-point computation without writing a loop.
- **Recognising patterns** — top-N-per-group, gaps and islands, running totals, sessionisation, retention. These are not memorized queries; they're a vocabulary.

### Real-world analogies that will stick

| Concept | Analogy |
|---|---|
| Window function | Standing in a parade and noting who is to your left and right, without leaving your place in line |
| `PARTITION BY` | Splitting one big parade into separate parallel parades (one per group) |
| `ORDER BY` inside `OVER` | Deciding which direction is "forward" within your parade |
| Frame (`ROWS BETWEEN …`) | Choosing how many neighbors you can see — a sliding cone of vision |
| CTE | Labeling intermediate work on a whiteboard ("call this set `paid_orders`") |
| Recursive CTE | A fractal: define a tree level in terms of the previous level until nothing new appears |
| LATERAL | Running a small custom query *per outer row* — like asking each customer "tell me your last 3 purchases" |
| Pivot | Rotating a long-skinny table into a short-wide spreadsheet |

---

## Core concepts

### Window functions

#### Mental model

Imagine every row of your result set is **standing in line**. A window function lets each row **look around at its neighbors** (rows within the same partition, within a defined frame) and compute something based on what it sees — but the row itself stays put. No row is collapsed.

Three knobs control what each row sees:

```
   OVER (
     PARTITION BY  ── which "queue" am I in?   (rows outside my partition are invisible)
     ORDER BY      ── which direction is "forward" inside my queue?
     ROWS/RANGE …  ── how many neighbors can I see? (the frame — a sliding window)
   )
```

#### GROUP BY vs Window — visual comparison

```
   GROUP BY user_id, SUM(amount)            SUM(amount) OVER (PARTITION BY user_id)
   ───────────────────────────────          ────────────────────────────────────────
   user_id │ amount                          user_id │ amount │ sum_for_user
   ────────┼──────                           ────────┼────────┼─────────────
     1     │  10                               1     │   10   │     30        ← row preserved
     1     │  20                               1     │   20   │     30        ← row preserved
     2     │  50          →   COLLAPSES         2     │   50   │     50
                              into:             ────────┴────────┴─────────────
                            user_id │ sum       (3 rows in, 3 rows out — annotated)
                            ────────┼─────
                              1     │  30
                              2     │  50
                            (3 rows in, 2 rows out)
```

Same aggregate function, totally different output shape. **GROUP BY shrinks. Window functions annotate.**

#### Sliding window frame — ASCII visualisation

For `SUM(amount) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`:

```
   day:    Mon  Tue  Wed  Thu  Fri  Sat  Sun
   amt:    10   20   30   40   50   60   70

   row=Mon:  [10]                              → sum = 10
   row=Tue:  [10  20]                          → sum = 30
   row=Wed:  [10  20  30]                      → sum = 60
   row=Thu:       [20  30  40]                 → sum = 90        ← window slides forward
   row=Fri:            [30  40  50]            → sum = 120       ← window slides forward
   row=Sat:                 [40  50  60]       → sum = 150
   row=Sun:                      [50  60  70]  → sum = 180
                                                ↑ a 3-row "cone of vision" walks across the partition
```

That's literally a sliding window. `ROWS` counts physical rows; `RANGE` counts logical values (so a gap day wouldn't be included even if it's the previous-physical-row, because its date-value falls outside the range).

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

#### Common beginner confusion — window functions

- **"`PARTITION BY` is GROUP BY."** — No. GROUP BY collapses. PARTITION BY only fences off the visible neighbors for the per-row computation.
- **"Window functions work in `WHERE`."** — No. They run *after* `WHERE`/`GROUP BY`/`HAVING` (they're effectively part of `SELECT`). To filter on a window result, wrap in a subquery or CTE.
- **"`LAST_VALUE` returns the last row of the partition."** — No, not by default. The default frame ends at the *current row*, so `LAST_VALUE` is just the current row's value. You must spell out `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`.
- **"`ROWS` and `RANGE` are interchangeable."** — Not when there are ties. With `ORDER BY day`, if two rows share the same day, `ROWS 1 PRECEDING` includes exactly 1 prior row; `RANGE 1 PRECEDING` includes all rows with the same prior date-value.

#### Progressive build-up — window functions

```sql
-- Level 0: just rank rows globally
SELECT name, salary, RANK() OVER (ORDER BY salary DESC) AS rk FROM employees;

-- Level 1: rank per department (partition)
SELECT name, dept, salary,
       RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rk_in_dept
FROM employees;

-- Level 2: running total per user
SELECT user_id, ts, amount,
       SUM(amount) OVER (PARTITION BY user_id ORDER BY ts) AS running_total
FROM transactions;

-- Level 3: 7-day moving average per user (explicit frame)
SELECT user_id, day, revenue,
       AVG(revenue) OVER (
         PARTITION BY user_id
         ORDER BY day
         RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW
       ) AS revenue_7d
FROM daily_user_revenue;

-- Interview level: gaps & islands using LAG + cumulative SUM (sessionisation)
-- (see "Real examples" below)
```

### CTEs (Common Table Expressions)

#### Mental model

A CTE is **labeling intermediate work**. Instead of nesting subqueries five levels deep, you give each step a name and read top-to-bottom. The CTE doesn't change *what* runs (modern planners inline it); it changes *what you see when you read the query*.

```
   WITHOUT CTE (nested):                          WITH CTE (named steps):
                                                  ─────────────────────────
   SELECT ... FROM (                              WITH paid_orders AS (...),
     SELECT ... FROM (                                 recent       AS (...)
       SELECT ... FROM (                          SELECT ... FROM recent;
         SELECT ... FROM orders ...
       )                                          Reads like a recipe:
     )                                            "first compute X,
   );                                              then compute Y from X,
                                                   then return Z."
   You read inside-out.                           You read top-to-bottom.
```

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

##### Mental model

Recursive CTEs are how SQL expresses **"keep doing this until nothing new appears."** They have exactly the same shape as recursion in any language: a **base case** + a **recursive case**, glued by `UNION ALL`. The engine runs the base case, feeds its rows back into the recursive case, appends new rows, repeats — until a step produces zero rows. Then it stops and returns the accumulated result.

```
   Base case        ──┐
   (depth 0 rows)     │
                      ├──> UNION ALL ──> grow set ──> recursive case sees new rows ──┐
   Recursive case ────┘                                                              │
   (depth N + 1 rows                                                                 │
    derived from                                                                     │
    depth N rows)                                                                    │
                      ◄──────────────────────  feed back until no new rows  ─────────┘
```

This is **fixed-point iteration**, expressed declaratively. Use cases: org charts, comment threads, category trees, dependency graphs, BOM (bill of materials), shortest-paths.

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

#### Mental model

A normal subquery in `FROM` is sealed: it can't see the outer row. `LATERAL` punches a hole in that seal — **the subquery is re-evaluated for each outer row, with that row's columns visible inside**. Think of it as "for each customer, please run this little query and bring back what you found."

This is precisely the **correlated subquery pattern, but in the FROM clause**, which means you can return multiple columns and multiple rows per outer row — something a scalar correlated subquery can't.

```
   For each user u:                       The result of the LATERAL is stapled to u.
   ┌──────┐    ┌─────────────────────┐    Outer row 1 ┐── inner rows for user 1
   │ u    │ ──>│ SELECT … FROM msg   │    Outer row 2 ┤── inner rows for user 2
   │ row  │    │  WHERE msg.uid=u.id │    Outer row 3 ┤── inner rows for user 3
   └──────┘    │  ORDER BY ts DESC   │
               │  LIMIT 3            │
               └─────────────────────┘
```

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

#### Mental model

A pivot **rotates** a tall narrow table into a short wide one. Each *distinct value* in some "category" column becomes its own *column* in the output. Unpivot is the reverse: take many columns and stack them back into rows.

```
   LONG (tidy) form:                       WIDE (pivoted) form:
   ──────────────────                      ────────────────────────────────
   user │ month │ amount                   user │ jan │ feb │ mar
   ─────┼───────┼────────                  ─────┼─────┼─────┼─────
    A   │   1   │  10                       A   │ 10  │ 20  │  0
    A   │   2   │  20                       B   │  5  │  0  │ 30
    B   │   1   │   5
    B   │   3   │  30
```

The trick in SQL (since standard SQL has no `PIVOT`) is to **GROUP BY the row-key and use conditional aggregates** (`SUM(CASE WHEN month = 1 THEN amount END)`). The `CASE` keeps only matching rows in each sum; the rest become NULL and `SUM` ignores NULLs.

`FILTER (WHERE …)` is just syntactic sugar over the same idea, and it's much cleaner in Postgres.

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

#### Mental model

Set operations treat two query results as **pure mathematical sets of tuples** and apply elementary set algebra.

```
   UNION (dedup)            UNION ALL (multiset concat)    INTERSECT              EXCEPT (A − B)
                                                                                  
       A ∪ B                  A ⊎ B (bag)                    A ∩ B                  A \ B
   ┌────────────┐            ┌─────────────────┐            ┌───┬───┬───┐          ┌────────┬───┐
   │ a, b, c, d │            │ a, b, b, c, d, d│            │   │ x │   │          │ a, b   │   │
   └────────────┘            └─────────────────┘            └───┴───┴───┘          └────────┴───┘
   (duplicates                (everything kept,
    removed)                   even repeats)
```

Practical rules:

- Same number of columns in each query, with compatible types, in the same order.
- `UNION` sorts to dedup → CPU cost; prefer `UNION ALL` unless you actually need uniqueness.
- `EXCEPT`/`INTERSECT` dedup too — that's part of their set semantics.

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

#### Step-by-step walk-through (sessionisation)

Imagine messages from one user at times `t1, t2, t3, t4` with `t3 - t2 > 1 hour`:

```
   ts:       t1   t2   t3   t4         ← raw rows
   LAG(ts):  -    t1   t2   t3
   gap:      NULL small BIG  small
   new?:      1     0    1     0       ← (gap > 1h OR NULL) → 1, else 0
   session:   1     1    2     2       ← running SUM of "new?" inside the partition
```

The cumulative `SUM` of the boolean "starts a new session here?" flag becomes the **session id**. Same trick, generalised: any time you want to *bucket consecutive rows*, build a boolean "new bucket starts here", then `SUM(...) OVER (ORDER BY ...)` to label them.

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

## How to talk through an advanced query at the whiteboard

For window-function questions, follow this script:

1. **Identify the per-row output you need.** "I want each row annotated with the running total / its rank / the previous row's value."
2. **Choose `PARTITION BY`.** "I want this annotation reset for each user → `PARTITION BY user_id`." If you don't say `PARTITION BY`, the window is the entire result.
3. **Choose `ORDER BY`.** "Inside each user's partition, I want chronological order → `ORDER BY ts`."
4. **Choose the frame, *if* aggregating.** "Running total → `ROWS UNBOUNDED PRECEDING`. 7-day average → `RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW`."
5. **Mention cost.** "This needs a sort of each partition; if I have an index on `(user_id, ts)` the engine can stream it for free."

For recursive CTEs:

1. **Base case** — "Start at the root (or a known seed set)."
2. **Recursive case** — "Each step joins the previous level back to the table to find children."
3. **Stop condition** — "When the recursive case returns zero rows, we stop. I'll add `WHERE depth < N` for safety."
4. **Mention cycles** — "If the graph might cycle, I need an explicit visited-set or the `CYCLE` clause in Postgres 14+."

For "top-N-per-group" framing, always offer two options:

- `ROW_NUMBER()` + filter — clear, costs a full partition sort.
- `LATERAL` with `LIMIT` — fastest with `(group, order_key)` index; per-row probing.

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

## One-line summary of advanced SQL

> **Window functions annotate without collapsing; CTEs label intermediate work; recursion is fixed-point iteration; LATERAL is "for each outer row, run this query." Recognise the pattern (top-N-per-group, gaps & islands, running totals, sessions, retention), and the query writes itself.**

If the fundamentals file gave you the *grammar* of SQL, this file gave you the *idioms*. Interviewers test idioms.

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
