# EXISTS vs IN vs JOIN — semantics, performance, and the NOT IN NULL trap

## Source / Origin
- Classic "do you actually know SQL" interview question. Appears on every senior backend round.
- Reference: PostgreSQL docs on "Subquery Expressions"; Use The Index, Luke! chapter on semi-joins.
- Companion concept doc: `backend-data-prep/sql/04-query-patterns.md`.
- Canonical prompt: *"Find customers who have placed at least one order. Show me three ways to write this and tell me which is fastest and which is wrong."*

## Why this question matters in interviews
This is the **SQL literacy filter**. Every candidate has seen `IN`, `EXISTS`, and `JOIN`; few can articulate that they are **three different relational operators with different semantics** (set membership, semi-join, inner join) that the planner *usually* normalises to the same plan — but not always, and not safely. The interviewer is testing three things in one prompt:

1. Do you know the **NOT IN NULL trap** (the single most common SQL data bug in production)?
2. Can you reason about **duplicates** — `JOIN` produces them, `EXISTS` doesn't?
3. Can you read an `EXPLAIN` and tell when the planner picks a hash semi-join vs a nested-loop anti-join?

Fumble any of these and you read junior. Nail all three and you read senior.

## Concepts involved

### Syntax to lock in

```sql
-- Customers with at least one order — three equivalent forms

-- (a) IN subquery
SELECT c.* FROM customers c
WHERE c.id IN (SELECT customer_id FROM orders);

-- (b) EXISTS correlated subquery
SELECT c.* FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);

-- (c) INNER JOIN with DISTINCT (because JOIN multiplies rows)
SELECT DISTINCT c.* FROM customers c
JOIN orders o ON o.customer_id = c.id;

-- Customers with NO orders — three forms, only two are safe

-- (a) NOT IN  — DANGER if customer_id can be NULL
SELECT c.* FROM customers c
WHERE c.id NOT IN (SELECT customer_id FROM orders);

-- (b) NOT EXISTS — safe, NULL-correct
SELECT c.* FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);

-- (c) LEFT JOIN ... IS NULL — safe, sometimes faster
SELECT c.* FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.id IS NULL;
```

### Edge cases / interview traps

1. **`NOT IN (subquery)` with a single NULL returns zero rows.** If any row of the inner result is NULL, `NOT IN` becomes `x != NULL AND x != ...` which is `UNKNOWN`, filtered out. Silently wrong, no error, no warning. **The most common production SQL bug.**
2. **`IN` and `EXISTS` are semi-joins** — they never duplicate the outer row even if the inner side matches twice. `JOIN` is a full inner join; it does duplicate.
3. **`JOIN` requires `DISTINCT` to match `EXISTS`** — easy to forget, and `DISTINCT` triggers a sort/hash that may dominate cost.
4. **Modern planners (Postgres ≥ 8.4, MySQL ≥ 8.0) usually rewrite `IN`/`EXISTS` to a `HashSemiJoin`** — they often produce identical plans. *Usually* not always.
5. **`NULL = NULL` is `UNKNOWN`** — that's the root cause of the NOT IN trap. `NULL IN (NULL)` is `UNKNOWN`, `NULL NOT IN (NULL)` is `UNKNOWN`.
6. **`EXISTS` short-circuits on the first match** — for large inner tables with selective outer rows, this is the natural fit.
7. **`IN (literal list)` is different from `IN (subquery)`** — the literal-list form is rewritten to `OR`s. Postgres handles up to ~100 literals well; beyond that, use `= ANY(ARRAY[...])` or a `VALUES` table.
8. **Indexes** — `EXISTS` benefits from an index on `orders(customer_id)`; `IN`/`JOIN` typically too. `LEFT JOIN ... IS NULL` benefits from the same index plus a filter.

## Mental Model

Three operators, three set semantics:

```
customers C = { 1, 2, 3, 4 }
orders.customer_id O = { 1, 1, 2 }       -- customer 1 has 2 orders

EXISTS / IN  (semi-join):   "does C exist in O at all?"
   result = { c | exists o in O with o = c.id }  = { 1, 2 }
   one row per matching outer row, no duplicates.

JOIN  (inner join):          "pair every C with every matching O"
   result = { (1,o1), (1,o2), (2,o3) }
   c=1 appears TWICE. DISTINCT to dedupe.

NOT EXISTS / NOT IN  (anti-join):  "C absent from O"
   result = { 3, 4 }
   one row per non-matching outer row.
   NOT IN: if O contains NULL, result is { } — silently empty.
```

Picture for the NOT IN NULL trap:

```
SELECT id FROM customers
WHERE id NOT IN (1, 2, NULL);

-- expands to:
WHERE id != 1 AND id != 2 AND id != NULL
                                 ^^^^^^^^^
                                 always UNKNOWN
WHERE  T  AND  T  AND  UNKNOWN  =  UNKNOWN  → row filtered out
WHERE  F  AND  T  AND  UNKNOWN  =  FALSE    → row filtered out
WHERE  T  AND  F  AND  UNKNOWN  =  FALSE    → row filtered out

Every single row is filtered out. Zero results.
```

## Why interviewers care

- The NULL trap is the **single most-cited footgun** in SQL training material. Knowing it cold shows production muscle.
- Semi-join vs inner-join is the **conceptual prerequisite** for anti-joins, lateral joins, and correlated subqueries.
- Reading `EXPLAIN` and saying *"the planner converted my IN to a HashSemiJoin"* is the senior signal interviewers want to hear.
- It's a lead-in to **top-N-per-group**, **gaps-and-islands**, and other relational patterns that build on semi-/anti-join.

## Common beginner confusion

- *"`IN` and `EXISTS` are different in speed."* They produce the same plan in modern Postgres and MySQL ~95% of the time. Don't optimise blindly; measure.
- *"`NOT IN` is just the opposite of `IN`."* It is logically the negation, but **only when the inner result has no NULLs**. Mathematically: `NOT IN` is three-valued; one NULL breaks it.
- *"`JOIN` is always fastest."* Often is, but produces duplicates that you then have to `DISTINCT` away — which kills perf for wide rows.
- *"`EXISTS` is slow because it's correlated."* The planner unrolls correlated `EXISTS` into a semi-join in most cases. *Correlated* is not a runtime cost label.
- *"Add `WHERE inner_col IS NOT NULL` inside the subquery."* That fixes `NOT IN` only as a workaround; `NOT EXISTS` is the right answer.

## Brute force approach

`SELECT c.* FROM customers c WHERE c.id NOT IN (SELECT customer_id FROM orders);`

Works on a textbook schema where `customer_id` is `NOT NULL`. Production schemas evolve: someone makes the column nullable for soft-deletes or partial-fill imports. Suddenly your report returns zero customers and nobody notices for a week.

## Optimal approach

**Decision tree:**

```
Need existence check?
├── Returning rows from outer table only
│     ├── At least one match           → EXISTS  (semi-join)
│     └── No match                     → NOT EXISTS (anti-join)
│
└── Returning columns from both sides
      ├── At-most-one match per outer  → JOIN (no DISTINCT needed)
      └── Possibly many per outer      → JOIN + window/aggregation
```

**Defaults to memorise:**

- *Existence:* `EXISTS` / `NOT EXISTS`. Always safe, always semantically clear, planner usually picks the best plan.
- *Need data from both sides:* `JOIN`. Use `DISTINCT` only if you must.
- *Static literal list:* `IN (1, 2, 3)` or `= ANY(ARRAY[...])`.
- *NEVER `NOT IN` on a subquery.* It's a banned pattern in many style guides for this exact reason.

## Solution (PostgreSQL)

```sql
-- Setup
CREATE TABLE customers (id INT PRIMARY KEY, email TEXT);
CREATE TABLE orders (
  id INT PRIMARY KEY,
  customer_id INT,            -- nullable!
  total NUMERIC(10,2)
);
CREATE INDEX idx_orders_customer ON orders(customer_id);

INSERT INTO customers VALUES (1, 'a@x'), (2, 'b@x'), (3, 'c@x'), (4, 'd@x');
INSERT INTO orders VALUES (10, 1, 50), (11, 1, 75), (12, 2, 30), (13, NULL, 99);
--                                                              ^^^^ guest checkout

-- "Customers with at least one order" — all three work, all safe
SELECT id FROM customers c WHERE EXISTS
  (SELECT 1 FROM orders o WHERE o.customer_id = c.id);
-- → 1, 2

-- "Customers with no orders" — the trap and the fixes

-- WRONG: NOT IN with nullable inner column
SELECT id FROM customers WHERE id NOT IN (SELECT customer_id FROM orders);
-- → 0 rows  (silently wrong; the NULL from guest checkout poisons it)

-- RIGHT: NOT EXISTS
SELECT id FROM customers c WHERE NOT EXISTS
  (SELECT 1 FROM orders o WHERE o.customer_id = c.id);
-- → 3, 4

-- RIGHT: LEFT JOIN ... IS NULL
SELECT c.id FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.id IS NULL;
-- → 3, 4

-- WORKAROUND if you must use NOT IN: filter NULLs in the subquery
SELECT id FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders WHERE customer_id IS NOT NULL);
-- → 3, 4  (but NOT EXISTS is still the better answer)
```

### Comparing plans

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);
```

Typical Postgres output:

```
Hash Semi Join  (cost=... rows=2 width=4)
  Hash Cond: (c.id = o.customer_id)
  ->  Seq Scan on customers c
  ->  Hash
        ->  Seq Scan on orders o
```

Note `Hash Semi Join` — that's the planner saying "I rewrote this; no duplicates produced, short-circuits on first match per outer row."

The same query with `IN (SELECT ...)` produces the identical plan in Postgres 12+. With `JOIN ... DISTINCT`, the planner usually adds a `HashAggregate` to dedupe, which costs extra.

## Step-by-step dry run

Tables:
```
customers:  id | email     orders: id | customer_id | total
            ---+--------           ----+-------------+------
             1 | a@x                10 | 1           | 50
             2 | b@x                11 | 1           | 75
             3 | c@x                12 | 2           | 30
             4 | d@x                13 | NULL        | 99
```

Query trace for `EXISTS`:
```
For each c in customers:
  c=1: probe orders where customer_id=1 → found row 10 → emit c=1, stop scanning inner
  c=2: probe orders where customer_id=2 → found row 12 → emit c=2
  c=3: probe orders where customer_id=3 → no match    → skip
  c=4: probe orders where customer_id=4 → no match    → skip
Result: {1, 2}
```

Query trace for `NOT IN (...)` with NULL in subquery:
```
inner result = {1, 1, 2, NULL}

For each c in customers:
  c=1: 1 != 1?  FALSE  → row filtered
  c=2: 2 != 1?  T, 2 != 1?  T, 2 != 2?  FALSE  → filtered
  c=3: 3 != 1?  T, 3 != 1?  T, 3 != 2?  T, 3 != NULL?  UNKNOWN
       T AND T AND T AND UNKNOWN = UNKNOWN → filtered  ← THE BUG
  c=4: same → UNKNOWN → filtered
Result: {} — zero rows.
```

Query trace for `NOT EXISTS`:
```
For each c in customers:
  c=1: any orders.customer_id = 1?  YES → filtered
  c=2: any orders.customer_id = 2?  YES → filtered
  c=3: any orders.customer_id = 3?  NO  → emit
  c=4: any orders.customer_id = 4?  NO  → emit
Result: {3, 4}
```

`NOT EXISTS` evaluates `c.id = NULL` as `UNKNOWN`, which is also "not matched", so the NULL row in orders correctly contributes nothing to the anti-join. Three-valued logic works *in our favor* with `NOT EXISTS`.

## How to think aloud in the interview

> "Three forms; all three return the same answer for the *positive* case (customers with orders), assuming I add `DISTINCT` to the `JOIN` to avoid duplicates from multi-order customers. In modern Postgres, `IN` and `EXISTS` both compile to a `HashSemiJoin`; `JOIN + DISTINCT` adds a `HashAggregate` that's typically slower for wide outer rows.
>
> For the *negative* case — customers with no orders — `NOT IN` has a famous trap: if `customer_id` is nullable and contains even a single NULL, `NOT IN` returns zero rows because `x != NULL` is `UNKNOWN`, which the `WHERE` clause filters out. This isn't an error; it just silently produces an empty result. Many production data bugs trace to exactly this.
>
> So my rule is: existence checks always use `EXISTS` / `NOT EXISTS`. I reach for `JOIN` only when I need columns from both sides, and even then I prefer `LEFT JOIN ... IS NULL` over `NOT IN` for anti-joins.
>
> Performance-wise, the planner makes them roughly equivalent for positive checks; for anti-joins, `NOT EXISTS` and `LEFT JOIN ... IS NULL` typically tie, and `NOT IN` is both slower and dangerous."

## Important takeaways

- **`EXISTS`/`NOT EXISTS` for existence checks — always safe.**
- **`NOT IN` on a subquery is banned by default** — NULL trap silently drops all rows.
- **`JOIN` produces duplicates** — needs `DISTINCT` or aggregation to match `EXISTS` semantics.
- **Modern planners unify `IN` and `EXISTS`** to `HashSemiJoin`; perf parity is the norm.
- **`LEFT JOIN ... IS NULL`** is the JOIN-equivalent of `NOT EXISTS`; safe with NULLs.
- **Three-valued logic** is the root cause of the NULL trap; `NULL != NULL` is `UNKNOWN`.
- **Always index the foreign key** referenced by `EXISTS`/`IN`/`JOIN` — `orders(customer_id)` here.

## Variants

1. **`IN (literal list)`** — different beast; rewritten to `OR`s. For ≥1000 literals, prefer `VALUES` table or `= ANY(ARRAY[...])`.
2. **`EXISTS` with multiple columns** — `WHERE (a,b) NOT IN (SELECT x,y FROM ...)` has the same trap, multiplied. Always prefer multi-column `NOT EXISTS`.
3. **Anti-join with NULL semantics required** — sometimes you *want* `NULL` to count as a match (e.g., GDPR data lineage). Use `IS NOT DISTINCT FROM`.
4. **`EXCEPT` operator** — set-difference; equivalent to `NOT EXISTS` on full row tuples. Quietly de-duplicates.
5. **`LATERAL` join with `LIMIT 1`** — replaces `EXISTS` when you need the matched inner row's columns.
6. **MySQL specifics** — pre-8.0, `NOT EXISTS` could outperform `NOT IN` by 100x due to materialisation. 8.0+ uses a hash anti-join.

## Revision notes

> **exists/in/join — 60 second recap**
> - `EXISTS`/`IN` = semi-join (no duplicates). `JOIN` = inner join (duplicates → need DISTINCT).
> - **`NOT IN` on a nullable subquery returns zero rows** — banned pattern; use `NOT EXISTS`.
> - Root cause: `x != NULL` is `UNKNOWN`; `WHERE UNKNOWN` filters the row.
> - Postgres/MySQL planners rewrite `IN`/`EXISTS` → `HashSemiJoin`; perf usually identical.
> - Index the FK referenced by the existence check.
> - `LEFT JOIN ... IS NULL` is the JOIN-equivalent of `NOT EXISTS`; safe with NULLs.
> - Senior signal: name three forms, name the NULL trap, pick `EXISTS`/`NOT EXISTS` as default.
