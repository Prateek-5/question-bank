# SQL Fundamentals

## Why this matters in backend interviews

- **SQL rounds are non-negotiable** for SDE2 backend roles. Almost every product company (Amazon, Atlassian, Walmart, Razorpay, Swiggy, Flipkart, Microsoft, Google, Uber) has at least one SQL screen.
- **Machine coding rounds** routinely require you to design a schema + write queries for it (e.g., parking lot bookings, order placement, leaderboard).
- **System design** rounds frequently jump from "design Twitter" to "what does your `tweets` table look like?" — you must be ready.
- **Debugging:** Senior engineers are expected to read a query, *predict the plan*, and spot performance issues — without running it.

The fundamentals here aren't about syntax. They're about: **execution order, set semantics, NULL behavior, and the ability to translate a business problem into relational algebra without thinking.**

---

## First principles — why SQL exists at all

Before any syntax, internalize this: **SQL is a declarative language for manipulating sets of tuples.**

Three foundational ideas:

1. **A relation is a set of tuples.** A table is just a (multi-)set of rows. Order is not part of the data; rows have no inherent position. When you write a query, you are describing *which set you want*, not *how to build it*.
2. **Declarative > imperative for data.** You don't say "loop over rows, check this, then accumulate that." You say "give me the set where these conditions hold." The query planner converts your description into an execution plan. This is the same shift as writing math (`{x | x > 0}`) instead of pseudocode (`for x in S: if x > 0 ...`).
3. **Set operations compose.** JOIN, UNION, GROUP BY, subqueries — each takes one or more relations and produces a new relation. Because the output of any query is itself a relation, queries compose like Lego.

### Real-world analogies that will stick

| SQL concept | Mental analogy |
|---|---|
| Table | A spreadsheet (but unordered) |
| Row | A single record / receipt |
| JOIN | Lining up two spreadsheets and matching them by a column |
| WHERE | Throwing away rows that fail a filter |
| GROUP BY | Sorting receipts into piles, one pile per category |
| Aggregate (`SUM`, `COUNT`) | Counting/totaling each pile |
| HAVING | Throwing away whole piles that don't meet a condition |
| Subquery | A miniature query whose result feeds another |
| Index | The alphabetical thumb-tabs in a paper dictionary |

If you keep these analogies in your head while reading the rest of this file, every concept will feel intuitive rather than memorized.

### Why interviewers care about fundamentals

The SDE2 SQL screen is rarely about typing speed. They're probing for:

- **Set-based thinking** — do you reach for `GROUP BY` and joins, or do you mentally loop "for each user, then for each order…"? The former scales, the latter doesn't.
- **Query planning intuition** — can you predict whether the engine will use a hash join, a nested loop, or an index scan, just by reading the query?
- **Declarative reasoning** — do you say *what* you want clearly, or do you over-specify the *how* (procedural temp tables, cursors, unnecessary ordering)?
- **NULL discipline** — three-valued logic trips up almost everyone; if you handle it without prompting, you stand out.

---

## Core concepts

### Logical execution order (everyone gets this wrong at first)

#### Mental model

SQL is written in the order you *think* about the answer (`SELECT what I want…`), but it must be *executed* in the order that lets the engine *produce* the answer. You can't filter a `SELECT` alias before `SELECT` has run; you can't aggregate before grouping. The clause-order vs execution-order mismatch is the single biggest source of beginner confusion.

#### ASCII pipeline view

```
   ┌────────┐   ┌───────┐   ┌──────────┐   ┌────────┐   ┌────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐
   │ FROM + │──>│ WHERE │──>│ GROUP BY │──>│ HAVING │──>│ SELECT │──>│ DISTINCT │──>│ ORDER BY │──>│ LIMIT/  │
   │ JOINs  │   │       │   │          │   │        │   │        │   │          │   │          │   │ OFFSET  │
   └────────┘   └───────┘   └──────────┘   └────────┘   └────────┘   └──────────┘   └──────────┘   └─────────┘
   produce      drop bad    bucket into    drop bad     compute      dedupe         sort           slice
   the row      rows        piles          piles        expressions  rows           rows           result
   universe                                              (aliases
                                                          born here)
```

Every alias you create in `SELECT` is invisible to `WHERE`/`GROUP BY`/`HAVING` (they ran first), but visible to `ORDER BY` (it runs later). This is not a quirk; it's a direct consequence of the pipeline above.

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

#### Mental model

A JOIN is **lining up two spreadsheets side-by-side and stapling rows together wherever a column matches**. You start with two sets of tuples; you end with one set of "combined" tuples. The *type* of JOIN only controls **what happens to rows that have no match on the other side** — keep them (with NULLs), drop them, or include both sides' orphans.

#### Progressive build-up

```sql
-- Level 0: cartesian — every row of A paired with every row of B (rarely useful)
SELECT * FROM users, orders;

-- Level 1: inner — only matched pairs
SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id = u.id;

-- Level 2: left — every user, with NULL for orders if they have none
SELECT u.name, o.id FROM users u LEFT JOIN orders o ON o.user_id = u.id;

-- Level 3: anti-join — users with NO orders (a left join + IS NULL)
SELECT u.name FROM users u LEFT JOIN orders o ON o.user_id = u.id WHERE o.id IS NULL;

-- Interview level: semi-join — "users who have at least one order, but don't duplicate them"
SELECT u.* FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
```

#### ASCII Venn diagrams — visualising each JOIN

```
   INNER JOIN                LEFT JOIN                  RIGHT JOIN                 FULL OUTER JOIN
                                                                                  
       L         R               L         R                L         R               L         R
    ┌────┬─────┐            ┌────┬─────┐                ┌────┬─────┐               ┌────┬─────┐
    │    │█████│            │████│█████│                │    │█████│               │████│█████│
    │    │█████│            │████│█████│                │    │█████│               │████│█████│
    │    │█████│ R-only     │████│█████│   R-only       │    │█████│ ███ R-only    │████│█████│ ████
    └────┴─────┘            └────┴─────┘                └────┴─────┘               └────┴─────┘
                                                                                  
   only the                 all of L plus               all of R plus              everything: rows on
   overlap                  matching R                  matching L                 either side, NULLs
                            (L-only rows                (R-only rows               where no match
                             keep NULLs                  keep NULLs
                             on right)                   on left)


   CROSS JOIN                ANTI-JOIN                  SEMI-JOIN
   (cartesian)               (L without match)          (L with at least one match)

       L  ×  R                  L         R                L         R
    ┌──────────┐             ┌────┐                     ┌────┐
    │ every    │             │████│  (R is              │████│  (R is checked
    │ pair     │             │████│   merely            │████│   merely for
    │ of       │             │████│   probed,           │████│   existence;
    │ rows     │             └────┘   not joined)       └────┘   not duplicated)
    └──────────┘
```

Read the diagrams: shaded = "this region is returned"; unshaded = "this region is dropped". The same Venn diagram with a different shading pattern explains every JOIN.

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

#### Indexed vs unindexed lookups (ASCII)

```
  Unindexed lookup (full scan)            Indexed lookup (B-tree)
  -----------------------------           --------------------------
   ┌──┬──┬──┬──┬──┬──┬──┬──┬──┐                    [50]
   │ 9│42│13│ 7│50│21│ 1│77│33│ scan all          /     \
   └──┴──┴──┴──┴──┴──┴──┴──┴──┘                 [21]    [77]
       ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑                       /   \    /  \
       O(N) comparisons                       [9]  [42][50] [77]
                                              /                \
                                             [1] ...           [99]
                                             O(log N) jumps
```

This is why a nested-loop join becomes a problem on a big inner table without an index: you re-scan the whole inner table for every outer row.

#### Common beginner confusion — JOINs are set-based, not procedural

- **JOIN order doesn't matter to the result** (only to the plan). `A JOIN B` and `B JOIN A` produce the same logical set; the planner chooses the cheaper one.
- **The `ON` clause is a filter on the *combined* row**, not on either side individually. `LEFT JOIN o ON o.status = 'PAID'` is *not* the same as `LEFT JOIN o ... WHERE o.status = 'PAID'`. The first keeps users with no paid orders (status side is NULL); the second silently demotes the LEFT JOIN into an INNER JOIN.
- **A LEFT JOIN does not automatically de-duplicate.** If a user has 5 orders, you get 5 rows for that user.

#### Interview storytelling — how to talk about a JOIN at the whiteboard

> "I want every user, plus their most recent order if any. So it's a LEFT JOIN — I keep all users. The join condition is the user-id equality. Because I want 'most recent', I need a tiebreaker, which I'll do with a window function or LATERAL. The right-side predicate `status = 'PAID'` goes in the `ON` clause, not `WHERE`, otherwise I'd lose users who never paid — which would silently turn this into an INNER JOIN."

That paragraph alone scores you points; it shows declarative thinking *and* JOIN-vs-WHERE awareness.

### NULL is not a value — it's "unknown"

#### Mental model

Think of `NULL` as the answer **"I don't know."** Two unknowns aren't equal — they might be the same, they might be different, we don't know. That's why `NULL = NULL` is itself `NULL`, not `TRUE`. SQL's logic isn't two-valued (true/false); it's **three-valued (TRUE / FALSE / UNKNOWN)** and `WHERE` only keeps rows whose predicate evaluates to `TRUE`. `UNKNOWN` rows fall off the side.

#### Truth table — the source of every NULL bug

```
   AND │ T │ F │ N             OR  │ T │ F │ N             NOT
   ────┼───┼───┼───            ────┼───┼───┼───            ─────
    T  │ T │ F │ N              T  │ T │ T │ T             T → F
    F  │ F │ F │ F              F  │ T │ F │ N             F → T
    N  │ N │ F │ N              N  │ T │ N │ N             N → N
```

Every weird NULL behaviour falls out of this table. For example: `col NOT IN (1, 2, NULL)` expands to `col<>1 AND col<>2 AND col<>NULL`. The last term is always `NULL` → the whole expression is at best `NULL`, never `TRUE` → zero rows.

#### Common beginner confusion — `COUNT(*)` vs `COUNT(col)` vs `COUNT(DISTINCT col)`

- `COUNT(*)` — "how many rows in the bucket?" — counts everything, even all-NULL rows.
- `COUNT(col)` — "how many *non-NULL* values of `col` in the bucket?" — silently drops NULLs.
- `COUNT(DISTINCT col)` — same, but de-duplicates first; expensive.

Useful trick: `COUNT(*) - COUNT(col)` gives you the number of NULLs in `col` — handy for data-quality queries.

- `NULL = NULL` is **NULL**, not true
- `NULL <> NULL` is **NULL**, not false
- `IS NULL` / `IS NOT NULL` are the only valid checks
- `COUNT(*)` counts rows; `COUNT(col)` skips NULLs
- `WHERE col != 'X'` excludes NULLs (this trips up everyone in interviews)
- `NOT IN (subquery)` returns nothing if the subquery has a NULL — use `NOT EXISTS` instead

### GROUP BY semantics

#### Mental model

`GROUP BY` is **sorting your receipts into piles**, one pile per unique combination of the group-by columns. Each pile collapses into a single output row. Aggregate functions (`SUM`, `COUNT`, `AVG`, `MIN`, `MAX`) operate *per pile*.

```
   Raw rows:                     After GROUP BY category:
   ┌────────────┬───────┐         ┌──────────┬──────────────┐
   │ category   │ price │         │ category │ SUM(price)   │
   ├────────────┼───────┤         ├──────────┼──────────────┤
   │ books      │  20   │   →     │ books    │     50       │  ← pile of 2 books rows collapsed
   │ books      │  30   │         │ shoes    │    175       │  ← pile of 2 shoes rows collapsed
   │ shoes      │ 100   │         └──────────┴──────────────┘
   │ shoes      │  75   │
   └────────────┴───────┘
```

Once the piles exist, you can either:
- ask the engine to *describe* each pile (an aggregate column in `SELECT`), or
- ask it to *throw away* piles you don't like (`HAVING`).

You **cannot** ask for a non-grouped detail column directly, because the row no longer exists — the pile collapsed.

#### Common beginner confusion — `WHERE` vs `HAVING`

| | WHERE | HAVING |
|---|---|---|
| Runs… | **before** GROUP BY | **after** GROUP BY |
| Operates on… | individual rows | piles (groups) |
| Can use aggregates? | No | Yes |
| Can use group key? | Yes | Yes |

> Rule of thumb: if your condition could be evaluated **on a single row in isolation**, it's a `WHERE`. If it needs to look at the whole pile (`COUNT(*) > 5`, `SUM(amount) > 1000`), it's a `HAVING`.

- Every non-aggregated column in `SELECT` must appear in `GROUP BY` (Postgres-strict). MySQL was historically lenient (`ONLY_FULL_GROUP_BY` now defaults on).
- `HAVING` runs *after* `GROUP BY` and can reference aggregates.
- `GROUP BY ()` returns 1 row (the global aggregate).

### Subqueries

#### Mental model

A subquery is **a query whose answer is fed into another query**. Since every SQL query produces a relation (a set), and most SQL clauses accept a relation as input, subqueries compose anywhere a relation can sit: `FROM`, `WHERE`, `SELECT`, `HAVING`.

Two flavors that look similar but execute very differently:

- **Non-correlated** — independent of the outer query. The engine runs it *once* and reuses the result. Cheap.
- **Correlated** — references a column from the outer row. Conceptually re-runs *per outer row*. Often expensive, but the planner may rewrite it into a join.

```
   Non-correlated (run once):                  Correlated (run per outer row):
   ┌────────────────────┐                      ┌──────────┐    ┌──────────────┐
   │ outer query        │                      │ outer    │───>│ inner runs   │
   │  uses pre-computed │<── single result ──  │ row 1    │    │ for row 1    │
   │  inner result      │   (one execution)    ├──────────┤    ├──────────────┤
   └────────────────────┘                      │ outer    │───>│ inner runs   │
                                               │ row 2    │    │ for row 2    │
                                               └──────────┘    └──────────────┘
```

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

## Bridge — from concepts to queries

The next section is examples. Don't just read them; *trace them* using the FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT pipeline. For each query ask:

1. What's the starting universe of rows after the joins?
2. What does `WHERE` throw away?
3. What are the piles after `GROUP BY`?
4. Which piles does `HAVING` drop?
5. What does the engine project in `SELECT`?

Once you can verbally narrate any query through those five questions, you're at the SDE2 level.

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

#### Walk-through (the way you'd narrate this to an interviewer)

1. **FROM + JOINs.** Start with `orders`, staple `order_items` to it by `order_id`, then `products` by `product_id`, then `categories` by `category_id`. The result is one row per *order-line*, fattened with category info.
2. **WHERE.** Keep only paid orders from the last 30 days. Anything else evaporates.
3. **GROUP BY.** Pile rows by `(category, day)`. Every pile = "everything sold in this category on this day."
4. **SELECT.** For each pile, emit the category, the day, and `SUM(quantity * unit_price)` — the pile's revenue.
5. **ORDER BY.** Sort newest-first; within a day, highest revenue first.

Notice we never wrote a loop. We described the set we wanted; the engine figured out the loops.

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

> **Pattern recognition:** "Per X, give me the latest/highest/top-1 Y" is the **top-N-per-group** pattern. Memorize the three idioms below — interviewers love this exact shape because there's no single "best" answer; the right choice depends on data shape and indexes.

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

## How to talk through SQL at the whiteboard

When asked "walk me through what this query returns," the high-signal answer follows a fixed script:

1. **Identify the row universe.** Say out loud what the FROM/JOIN produces. "After the joins, each row is one order-line plus its product, category, and parent order."
2. **State the filter.** "We keep only paid orders from the last 30 days."
3. **State the grouping.** "We pile by `(category, day)`, so each output row is one (category, day) pair."
4. **State the aggregation.** "We sum `quantity * price` over each pile — that's revenue for that bucket."
5. **State the ordering / limiting.** "Most recent days first; within a day, the biggest revenue first."

If they ask about performance, jump to:
- "Index on `orders(status, created_at)` cuts the filter cost."
- "If `order_items` is huge, the planner probably hash-joins it."
- "I'd watch for skew if one category dominates."

That structure works for almost any SQL question.

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

## One-line summary of fundamentals

> **SQL is "declare the set you want." Filters reduce rows, joins combine relations, GROUP BY collapses piles, NULL is unknown, and the engine — not you — decides the loops.**

If everything above clicks, you have the mental scaffolding. The next file (`02-advanced-sql.md`) layers window functions, CTEs, and recursion on top of these same primitives — same set-based thinking, sharper tools.

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
