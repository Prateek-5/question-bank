# SQL Fundamentals

## Why this matters in backend interviews

- **SQL rounds are non-negotiable** for SDE2 backend roles. Almost every product company (Amazon, Atlassian, Walmart, Razorpay, Swiggy, Flipkart, Microsoft, Google, Uber) has at least one SQL screen.
- **Machine coding rounds** routinely require you to design a schema + write queries for it (e.g., parking lot bookings, order placement, leaderboard).
- **System design** rounds frequently jump from "design Twitter" to "what does your `tweets` table look like?" — you must be ready.
- **Debugging:** Senior engineers are expected to read a query, *predict the plan*, and spot performance issues — without running it.

The fundamentals here aren't about syntax. They're about: **execution order, set semantics, NULL behavior, and the ability to translate a business problem into relational algebra without thinking.**

---

## Core concepts

### Logical execution order (everyone gets this wrong at first)

SQL is written `SELECT … FROM … WHERE … GROUP BY … HAVING … ORDER BY … LIMIT`, but it *executes* in this order:

1. `FROM` (+ JOINs) — produce the cartesian / joined rowset
2. `WHERE` — filter rows
3. `GROUP BY` — bucket rows
4. `HAVING` — filter groups
5. `SELECT` — project columns (aliases born here)
6. `DISTINCT`
7. `ORDER BY` — aliases are visible because SELECT already ran
8. `LIMIT / OFFSET`

This is *why*:
- You can't use a `SELECT` alias in `WHERE` (alias doesn't exist yet)
- You *can* use a `SELECT` alias in `ORDER BY`
- `HAVING` filters aggregates, `WHERE` cannot

### Joins — the algorithms behind them

| Type | Returns | Algorithm options |
|---|---|---|
| INNER | rows matching on both sides | nested loop / hash / sort-merge |
| LEFT | all left + matches | same; right side may be NULL |
| RIGHT | mirror of LEFT | rarely used; prefer LEFT |
| FULL OUTER | union of LEFT + RIGHT | hash full / merge full |
| CROSS | cartesian product | never use without a filter |
| ANTI | left rows with **no** match | `LEFT JOIN … WHERE r.id IS NULL` or `NOT EXISTS` |
| SEMI | left rows that **have** a match (without duplicating) | `WHERE EXISTS (...)` or `IN` |

The planner picks the algorithm:
- **Nested loop** — good when one side is small or there's an index on the inner side
- **Hash join** — good for large, unsorted inputs with an equi-join
- **Sort-merge** — good when both sides are already sorted on the join key

### NULL is not a value — it's "unknown"

- `NULL = NULL` is **NULL**, not true
- `NULL <> NULL` is **NULL**, not false
- `IS NULL` / `IS NOT NULL` are the only valid checks
- `COUNT(*)` counts rows; `COUNT(col)` skips NULLs
- `WHERE col != 'X'` excludes NULLs (this trips up everyone in interviews)
- `NOT IN (subquery)` returns nothing if the subquery has a NULL — use `NOT EXISTS` instead

### GROUP BY semantics

- Every non-aggregated column in `SELECT` must appear in `GROUP BY` (Postgres-strict). MySQL was historically lenient (`ONLY_FULL_GROUP_BY` now defaults on).
- `HAVING` runs *after* `GROUP BY` and can reference aggregates.
- `GROUP BY ()` returns 1 row (the global aggregate).

### Subqueries

- **Scalar subquery** — returns one value: `SELECT (SELECT MAX(x) FROM t)`
- **Correlated subquery** — references the outer row; runs per outer row → often slow → can usually be rewritten as a join
- **Derived table / inline view** — `FROM (SELECT … ) sub` — encapsulation
- **EXISTS / NOT EXISTS** — semi/anti join; *stops at first match*, faster than `IN`

### Common misconceptions

- "`DISTINCT` is free" — no, it forces a sort or hash dedup
- "`COUNT(*)` is slow" — actually fine in Postgres because of MVCC, but in InnoDB it's O(N) without an index hint. Use `COUNT(1)` = `COUNT(*)` (no difference)
- "Subqueries are slower than joins" — modern planners often rewrite them. Write what's clear; check the plan.
- "ORDER BY in a subquery is preserved" — it's not, except when paired with `LIMIT`
- "`WHERE col = 'x'` and `WHERE 'x' = col` are the same" — yes for correctness, but indexes still work the same

### Interview traps

1. **Self-join confusion** — “find pairs of employees in the same department” → join the table to itself with aliases.
2. **`COUNT(DISTINCT)`** — disables many optimizations; in big tables, use approximate count (`HyperLogLog` / `approx_count_distinct`).
3. **NULL in `NOT IN`** — kills the entire result. Always switch to `NOT EXISTS`.
4. **`GROUP BY` + ordering** — grouping does not guarantee order. Add `ORDER BY`.
5. **`UNION` vs `UNION ALL`** — `UNION` deduplicates (sort). Use `UNION ALL` if you don't need dedup.

---

## Real examples

### E-commerce — daily revenue per category

```sql
SELECT c.name AS category,
       DATE(o.created_at) AS day,
       SUM(oi.quantity * oi.unit_price) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
JOIN products  p   ON p.id = oi.product_id
JOIN categories c  ON c.id = p.category_id
WHERE o.status = 'PAID'
  AND o.created_at >= NOW() - INTERVAL '30 days'
GROUP BY c.name, DATE(o.created_at)
ORDER BY day DESC, revenue DESC;
```

### Payments — find duplicate-charge candidates

```sql
SELECT user_id, amount, COUNT(*) AS dup_count
FROM payments
WHERE created_at >= NOW() - INTERVAL '5 minutes'
GROUP BY user_id, amount
HAVING COUNT(*) > 1;
```

### Inventory — items low in stock that have pending orders

```sql
SELECT p.sku, p.qty_on_hand, COALESCE(SUM(oi.quantity), 0) AS pending
FROM products p
LEFT JOIN order_items oi ON oi.product_id = p.id
LEFT JOIN orders o       ON o.id = oi.order_id AND o.status = 'PLACED'
WHERE p.qty_on_hand < 10
GROUP BY p.sku, p.qty_on_hand
HAVING p.qty_on_hand - COALESCE(SUM(oi.quantity), 0) < 0;
```

### Chat — last message per conversation

```sql
-- Approach 1: window function (clean)
SELECT conv_id, body, sent_at
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY conv_id ORDER BY sent_at DESC) AS rn
  FROM messages
) t
WHERE rn = 1;

-- Approach 2: correlated subquery (anti-pattern at scale)
SELECT m.* FROM messages m
WHERE m.sent_at = (
  SELECT MAX(m2.sent_at) FROM messages m2 WHERE m2.conv_id = m.conv_id
);

-- Approach 3: LATERAL (Postgres) — often the fastest with right index
SELECT c.id, lm.body, lm.sent_at
FROM conversations c
LEFT JOIN LATERAL (
  SELECT body, sent_at FROM messages m
  WHERE m.conv_id = c.id ORDER BY sent_at DESC LIMIT 1
) lm ON true;
```

---

## Common interview questions

1. Difference between `WHERE` and `HAVING`.
2. Difference between `INNER JOIN` and `LEFT JOIN`. When is `LEFT JOIN` slower?
3. What is an anti-join? Two ways to write it.
4. `NULL` behavior in `=`, `IN`, `NOT IN`, `GROUP BY`, `COUNT`.
5. Find duplicate rows.
6. Find the second-highest salary (3 ways).
7. Difference between `UNION` and `UNION ALL`.
8. `IN` vs `EXISTS` — which is faster and why?
9. Explain logical execution order of SQL.
10. Self-join example.
11. `COUNT(*)` vs `COUNT(col)` vs `COUNT(DISTINCT col)`.
12. What does `GROUP BY` actually do internally?

---

## Detailed answers

### 1. `WHERE` vs `HAVING`
`WHERE` filters **rows before grouping**, can't use aggregates. `HAVING` filters **groups after aggregation**, must operate on aggregate values (or group keys).
```sql
-- Filter orders > 100 first, then group
WHERE total > 100 GROUP BY user_id

-- Group all, then keep only users with > 5 orders
GROUP BY user_id HAVING COUNT(*) > 5
```

### 2. INNER vs LEFT, and when LEFT is slow
LEFT is slow when the planner is forced to keep an unnecessary outer side. If you have `LEFT JOIN ... WHERE r.col = 'x'`, the WHERE turns it back into an INNER JOIN — but the planner sees the LEFT first. Be careful with predicates: put right-side conditions in `ON`, left-side in `WHERE`.

### 3. Anti-join — two ways
```sql
-- Users with no orders
SELECT u.* FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.id IS NULL;

-- Same, cleaner
SELECT u.* FROM users u
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
```
`NOT EXISTS` is preferred — it's NULL-safe and the planner usually picks the same plan.

### 4. NULL gotchas
- `WHERE status != 'PAID'` excludes rows where `status IS NULL`. Often a bug.
- `WHERE id NOT IN (SELECT id FROM blacklist)` — if any blacklist `id` is NULL, you get **zero rows back**. Use `NOT EXISTS`.
- `COUNT(col)` skips NULLs. To count all rows including NULLs, use `COUNT(*)`.

### 5. Find duplicates
```sql
SELECT email, COUNT(*) FROM users
GROUP BY email HAVING COUNT(*) > 1;
```
To get the actual duplicate row IDs:
```sql
SELECT * FROM users WHERE email IN (
  SELECT email FROM users GROUP BY email HAVING COUNT(*) > 1
);
```

### 6. Second-highest salary — three ways
```sql
-- Window function (cleanest)
SELECT salary FROM (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rk FROM employees
) t WHERE rk = 2;

-- Subquery
SELECT MAX(salary) FROM employees WHERE salary < (SELECT MAX(salary) FROM employees);

-- LIMIT/OFFSET (be careful with ties)
SELECT DISTINCT salary FROM employees ORDER BY salary DESC LIMIT 1 OFFSET 1;
```

The interviewer will ask: *"what if multiple people share the highest salary?"* Use **DENSE_RANK**, not `LIMIT/OFFSET`.

### 7. UNION vs UNION ALL
`UNION` deduplicates (sort/hash → CPU cost). `UNION ALL` concatenates. **Default to `UNION ALL`** unless you actually need dedup.

### 8. IN vs EXISTS
- `IN` with a small static list: fine, often turned into a hash table by the planner.
- `IN (subquery)` vs `EXISTS`: usually the planner produces identical plans. Differ on NULL semantics and short-circuiting — `EXISTS` stops at the first match.
- For correlated cases, `EXISTS` is usually clearer.

### 9. Logical execution order
FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT.

### 10. Self-join — employees and their managers
```sql
SELECT e.name AS employee, m.name AS manager
FROM employees e
LEFT JOIN employees m ON m.id = e.manager_id;
```

### 11. COUNT variants
- `COUNT(*)` — every row
- `COUNT(col)` — non-NULL values in `col`
- `COUNT(DISTINCT col)` — unique non-NULL values; expensive (requires hashing/sorting)

### 12. GROUP BY internals
The planner either:
- **Hash aggregate** — build a hash table keyed by GROUP BY columns
- **Sort aggregate** — sort by GROUP BY, then aggregate adjacent rows

Hash is faster for unsorted inputs; sort is preferred when the input is already sorted on the group key (e.g., index scan order).

---

## Practical coding examples

### Schema — a tiny e-commerce slice

```sql
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  price_cents INT NOT NULL CHECK (price_cents >= 0),
  qty_on_hand INT NOT NULL DEFAULT 0
);

CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id),
  status TEXT NOT NULL CHECK (status IN ('CART','PLACED','PAID','SHIPPED','CANCELLED')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);

CREATE TABLE order_items (
  order_id BIGINT NOT NULL REFERENCES orders(id),
  product_id BIGINT NOT NULL REFERENCES products(id),
  quantity INT NOT NULL CHECK (quantity > 0),
  unit_price_cents INT NOT NULL,
  PRIMARY KEY (order_id, product_id)
);
```

### Top 3 products by revenue (last 30 days)

```sql
SELECT p.sku, p.name,
       SUM(oi.quantity * oi.unit_price_cents)/100.0 AS revenue
FROM order_items oi
JOIN orders o   ON o.id = oi.order_id
JOIN products p ON p.id = oi.product_id
WHERE o.status = 'PAID'
  AND o.created_at >= NOW() - INTERVAL '30 days'
GROUP BY p.sku, p.name
ORDER BY revenue DESC
LIMIT 3;
```

### Users with no orders in the last 90 days (churn candidates)

```sql
SELECT u.* FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM orders o
  WHERE o.user_id = u.id AND o.created_at >= NOW() - INTERVAL '90 days'
);
```

---

## Common mistakes

- Putting a right-side predicate in `WHERE` after a `LEFT JOIN` (turns it into an inner join silently)
- Using `NOT IN` with a nullable subquery
- Selecting non-aggregated columns without `GROUP BY` (works in old MySQL, fails everywhere else)
- Believing `ORDER BY` is preserved through derived tables
- Using `OFFSET` for pagination on a million-row table (slow — use keyset pagination)
- Forgetting that `LIKE 'abc%'` uses an index but `LIKE '%abc'` doesn't
- Using `SELECT *` in production queries (breaks when schema evolves)

---

## Senior engineer discussion points

- **Logical vs physical execution** — interviewers love when you distinguish "what SQL means" from "how the engine runs it."
- **Why indexes affect joins** — composite indexes can flip the planner from hash to nested loop.
- **Schema choice affects query shape** — over-normalized schemas force more joins; sometimes one denormalized column saves three joins in a hot path.
- **NULL-vs-absent vs sentinel** — should "unknown phone" be NULL, empty string, or '__UNKNOWN__'? NULL preserves SQL semantics; sentinels enable unique constraints; discuss the trade-off.
- **`COUNT(*)` cost** — in Postgres it requires a scan because MVCC tuples aren't centrally counted; in MySQL InnoDB it's the same. For dashboards, cache the count or use approximate methods.
- **Keyset vs offset pagination** — offset = O(N+offset), keyset = O(log N). Mention this unprompted.

---

## Revision notes

- Logical order: FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT
- `NOT IN` ❌ with NULL → use `NOT EXISTS` ✅
- LEFT JOIN with right-side WHERE → becomes INNER JOIN (move to `ON`)
- `UNION ALL` > `UNION` unless dedup needed
- `COUNT(col)` skips NULL; `COUNT(*)` doesn't
- Self-join with aliases for hierarchical data
- Anti-join two ways: `LEFT JOIN ... IS NULL`, `NOT EXISTS`
- Top-N-per-group → `ROW_NUMBER() OVER (PARTITION BY …)` or `LATERAL`
- Pagination on big tables → keyset, not OFFSET
