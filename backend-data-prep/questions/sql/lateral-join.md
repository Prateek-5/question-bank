# LATERAL Join — Top-N Per Group, Per-Row Subquery

## Source / Origin
- Postgres LATERAL / SQL Server CROSS APPLY / Oracle CROSS APPLY (12c+).
- LeetCode #1741 "Find Total Time Spent by Each Employee", interview-query top-3-per-customer staples.
- Real prod: "latest message per conversation", "top 3 reviews per product", "first order timestamp per user".

## Why this question matters in interviews
LATERAL is the **dividing line between mid and senior SQL fluency**. Junior candidates solve "top 3 per group" with window functions or correlated subqueries; senior candidates know LATERAL is often cleaner, sometimes faster, and the only sane option when you need to **invoke a set-returning function per outer row** (think `jsonb_array_elements`, `regexp_matches`, `generate_series` with row-specific bounds).

Interviewers who ask LATERAL questions are screening for production experience: it's a feature you only reach for after you've tried the alternatives and felt their pain. Naming it confidently signals "I've shipped non-trivial SQL."

## Concepts involved

### Syntax to lock in
```sql
-- "Top 3 orders per customer, newest first"
SELECT c.id, c.name, o.*
FROM   customers c
CROSS  JOIN LATERAL (
         SELECT * FROM orders
         WHERE  customer_id = c.id      -- ← reference to OUTER row, only legal in LATERAL
         ORDER  BY created_at DESC
         LIMIT  3
       ) o;

-- "Expand a JSONB array column"
SELECT u.id, j.value
FROM   users u
CROSS  JOIN LATERAL jsonb_array_elements(u.tags) j;

-- LATERAL with LEFT JOIN — keep outer rows with no inner rows
SELECT c.id, o.*
FROM   customers c
LEFT   JOIN LATERAL (
         SELECT * FROM orders WHERE customer_id = c.id ORDER BY created_at DESC LIMIT 1
       ) o ON TRUE;     -- ← LEFT JOIN LATERAL requires ON TRUE
```

### Edge cases / interview traps
1. **`CROSS JOIN LATERAL` drops outer rows with no inner matches.** Use `LEFT JOIN LATERAL ... ON TRUE` to preserve them.
2. **Forgetting `LATERAL`** — without the keyword, the subquery can't reference outer columns. Error: "column does not exist".
3. **`LATERAL` only works in FROM, never in WHERE or SELECT.**
4. **MySQL got LATERAL only in 8.0.14.** Older MySQL: emulate with window functions or correlated scalar subqueries.
5. **SQL Server uses `CROSS APPLY`/`OUTER APPLY`** — same semantics, different keyword.
6. **Performance trap.** LATERAL runs the inner query **per outer row**. If the outer table has 10M rows and the inner subquery is expensive, you've built a nested loop. Index the correlated column.
7. **Inner subquery with `LIMIT` is the canonical LATERAL pattern.** Without LIMIT, a window function is usually cleaner.
8. **Combining LATERAL with set-returning functions** (`generate_series`, `jsonb_each`, `regexp_split_to_table`) is the second canonical use case. Each outer row gets a different SRF input.

## Mental Model

```
   customers           For EACH customer row, run a tiny subquery:
   c1 ───→             ( SELECT * FROM orders WHERE customer_id = c1.id LIMIT 3 )
   c2 ───→             ( SELECT * FROM orders WHERE customer_id = c2.id LIMIT 3 )
   c3 ───→             ( SELECT * FROM orders WHERE customer_id = c3.id LIMIT 3 )

   Then "staple" the inner result onto the outer row.
```

LATERAL is **a for-each loop expressed declaratively**. It's the FROM-clause version of a correlated subquery — but instead of returning a single value, it can return many rows and many columns.

## Why interviewers care
- Confirms candidate has solved "top-N per group" **multiple ways** and can pick.
- Probes knowledge of set-returning functions and JSONB unnesting — both prod-realistic.
- Reveals whether the candidate can read a nested-loop plan and decide it's intentional.

## Common beginner confusion
- "Isn't this just a subquery in SELECT?" — no; subqueries in SELECT return one row/column; LATERAL returns many.
- "Why `ON TRUE`?" — LATERAL doesn't have a natural join condition because the inner subquery already filters; we need a syntactic placeholder.
- "When over window functions?" — when you want `LIMIT` or set-returning behavior. Window functions can't `LIMIT` per partition cleanly without subquery wrapping.
- "Will the planner combine everything into one scan?" — usually no. LATERAL is a nested-loop semantically; the planner only avoids it for trivial cases.

## Brute force approach
- **Correlated subquery in SELECT** — but you can only return one scalar per row. Multi-column → multiple subqueries → multiple scans.
- **Window function + `WHERE rn <= 3`** — works for top-N but needs the full inner scan. Equivalent in cost when there's no useful index; LATERAL+index wins big.

## Optimal approach
LATERAL + index on the correlated column + `LIMIT`. Cost is `O(outer × log(inner) + outer × N)`. For 10K customers × top-3 orders with an index, it's ~30K index lookups — sub-second.

## Solution (SQL)

```sql
CREATE TABLE customers (id INT PRIMARY KEY, name TEXT);
CREATE TABLE orders (
  id           INT PRIMARY KEY,
  customer_id  INT REFERENCES customers(id),
  total        NUMERIC,
  created_at   TIMESTAMPTZ
);
CREATE INDEX ix_orders_cust_date ON orders(customer_id, created_at DESC);

INSERT INTO customers VALUES (1,'Alice'),(2,'Bob'),(3,'Carol');
INSERT INTO orders VALUES
 (10,1,100,'2025-01-01'),
 (11,1,250,'2025-02-01'),
 (12,1, 75,'2025-03-01'),
 (13,1, 50,'2025-04-01'),
 (14,3, 80,'2025-01-15');
```

```sql
-- Top 2 most-recent orders per customer (Bob excluded — no orders)
SELECT c.id AS cust_id, c.name, o.id AS order_id, o.total, o.created_at
FROM   customers c
CROSS  JOIN LATERAL (
         SELECT * FROM orders
         WHERE  customer_id = c.id
         ORDER  BY created_at DESC
         LIMIT  2
       ) o;
-- Alice → order 13 (2025-04-01), order 12 (2025-03-01)
-- Carol → order 14
-- (Bob dropped — CROSS JOIN LATERAL drops outer rows with no inner results)

-- Same query with LEFT JOIN LATERAL to keep Bob
SELECT c.id, c.name, o.id, o.total
FROM   customers c
LEFT   JOIN LATERAL (
         SELECT * FROM orders WHERE customer_id = c.id
         ORDER BY created_at DESC LIMIT 2
       ) o ON TRUE;
```

## Step-by-step dry run

For each customer, the planner uses the `(customer_id, created_at DESC)` index:

```
c=1 (Alice):  index seek to (1, +inf) → walk back 2 entries → orders 13, 12. Emit.
c=2 (Bob):    index seek to (2, +inf) → 0 entries. CROSS LATERAL: skip Bob.
                                         LEFT LATERAL: emit (Bob, NULL, NULL).
c=3 (Carol):  index seek to (3, +inf) → 1 entry → order 14. Emit.
```

Three index seeks total, not three table scans. That's the LATERAL+index magic.

## How to think aloud in the interview
1. *"Top-N per group — three options: window function with `ROW_NUMBER`, correlated subquery, or LATERAL. I'll go with LATERAL because we want a hard `LIMIT 3` and we have an index on `(customer_id, created_at DESC)`."*
2. *"LATERAL is FROM-clause-only. The subquery references the outer `c.id`, which is only legal because of the `LATERAL` keyword."*
3. *"CROSS JOIN LATERAL drops customers with zero orders. If we need them, switch to LEFT JOIN LATERAL ... ON TRUE."*
4. *"The plan is a nested loop with index seeks — exactly what we want for selective top-N. With 10K customers and a good index, microseconds per seek."*
5. *"In SQL Server I'd write CROSS APPLY; in MySQL 8.0.14+ same syntax as Postgres; older MySQL — fall back to row_number()."*

## Important takeaways
- LATERAL = per-row subquery in the FROM clause. Reference outer columns freely.
- `CROSS JOIN LATERAL` vs `LEFT JOIN LATERAL ... ON TRUE` mirrors INNER vs OUTER semantics.
- Canonical use cases: **top-N per group** with LIMIT, **set-returning function expansion** (JSONB, regexp, generate_series).
- Cost = `outer rows × inner cost`; index the correlated column.
- See `backend-data-prep/sql/02-advanced-sql.md` "LATERAL" for full theory.

## Variants
1. **`generate_series` per row** — explode a date range into one row per day, with the range varying by user. `LEFT JOIN LATERAL generate_series(u.signup_date, u.churn_date, '1 day') d ON TRUE`.
2. **JSONB array unnest** — `CROSS JOIN LATERAL jsonb_array_elements(t.tags)` to flatten array columns.
3. **First & last** — pull the first and last orders per customer in **one** LATERAL subquery returning two rows, vs two LATERAL subqueries — discuss.

## Revision notes

> **LATERAL cram block**
> - Per-row subquery in FROM, can reference outer columns.
> - Pattern: `CROSS JOIN LATERAL ( ... ) alias`.
> - Use `LEFT JOIN LATERAL ... ON TRUE` to keep outer rows with no matches.
> - Canonical: top-N per group with LIMIT; SRF unnesting.
> - SQL Server = `CROSS APPLY` / `OUTER APPLY`.
> - MySQL has LATERAL only ≥ 8.0.14.
> - Cost = nested loop; index the correlated column.
> - Alternative for top-N: `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...) ≤ N`. Slower if you have an index that LATERAL can seek.
> - Forget the `LATERAL` keyword → "column does not exist".
