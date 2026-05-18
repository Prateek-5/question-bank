# Anti-Join — Find Rows NOT In Another Table

## Source / Origin
- LeetCode #183 "Customers Who Never Order", #1141, #607.
- Stratascratch "Find users with no transactions in 2023".
- Real prod: detecting orphaned records, churn cohorts, "items in inventory never sold".

## Why this question matters in interviews
The anti-join question is the **single best test of NULL discipline and three-valued logic** in SQL. Three syntactic forms look equivalent but behave differently when NULLs are present: `NOT IN`, `NOT EXISTS`, and `LEFT JOIN ... IS NULL`. Pick the wrong one and your query returns **zero rows** silently — a class-A production bug that's nearly invisible in code review.

This question also probes whether you understand that the planner translates each form into a different physical operator. Senior candidates can sketch the cost of each on a 100M-row table and recommend `NOT EXISTS` as the default.

## Concepts involved

### Syntax to lock in
```sql
-- Three semantically-similar idioms (but they differ on NULLs):

-- 1. NOT EXISTS (safe, recommended)
SELECT c.id FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);

-- 2. LEFT JOIN ... IS NULL (also safe; explicit)
SELECT c.id FROM customers c
LEFT  JOIN orders o ON o.customer_id = c.id
WHERE  o.customer_id IS NULL;

-- 3. NOT IN (BROKEN if the inner table can contain NULL!)
SELECT c.id FROM customers c
WHERE c.id NOT IN (SELECT customer_id FROM orders);
```

### Edge cases / interview traps
1. **The `NOT IN` NULL trap.** If `orders.customer_id` contains *any* NULL, `NOT IN` returns **zero rows** for everyone. Reason: `x NOT IN (a, b, NULL)` becomes `x<>a AND x<>b AND x<>NULL` — and `x<>NULL` is UNKNOWN, which is never TRUE.
2. **Subquery returns empty set.** `NOT IN ()` is TRUE for all; `NOT EXISTS` is TRUE for all. Both are safe here.
3. **LEFT JOIN antipattern.** `LEFT JOIN o ... WHERE o.col = 'foo' AND o.col IS NULL` — you accidentally filtered the joined rows before the IS NULL check. Move predicates into ON.
4. **Multi-column anti-join.** Need `(c.id, c.region)` not in `(orders.customer_id, orders.region)` — `NOT IN` supports tuple form in Postgres but few engines; `NOT EXISTS` always works.
5. **Performance:** Postgres turns both `NOT EXISTS` and `LEFT JOIN IS NULL` into the same `Anti Join` operator (hash or nested loop). `NOT IN` cannot be antijoined because of NULL semantics → slow.
6. **EXCEPT/MINUS** is set-based and applies to whole rows: `SELECT id FROM customers EXCEPT SELECT customer_id FROM orders`. Distinct-by-default; mind that.
7. **Correlated `NOT EXISTS` performance** depends on an index on the correlated column. Without it, you fall back to a full inner scan per outer row.
8. **Empty FROM-clause table** (no customers): all idioms return zero rows — but `NOT EXISTS` does it fastest.

## Mental Model

```
   customers           orders                  Want: customers with no order

   c1 ─┐               c1, prod-a
   c2  │   ANTI-JOIN   c1, prod-b      →   {c2, c4}
   c3  │     ←──       c3, prod-c
   c4 ─┘               (no row for c2 or c4)
```

An anti-join is **the complement of a semi-join**. Semi-join keeps outer rows that **have** a match; anti-join keeps outer rows that **don't**. NULL is what breaks `NOT IN`: NULL in the inner column means "match status unknown for everyone", which the engine conservatively treats as "no answer is provably false" → zero anti-join output.

## Why interviewers care
- Tests **NULL literacy** at production scale. The `NOT IN` trap is a real-world outage pattern (e.g. "billing job emitted zero invoices on Sundays").
- Tests **query-planner intuition**: anti-join is a first-class physical operator. Knowing which SQL forms compile to it is senior-engineer territory.
- Tests **defensive coding**: prefer `NOT EXISTS`, validate `WHERE col IS NOT NULL` on inner side if you must use `NOT IN`.

## Common beginner confusion
- "All three forms are the same" — they aren't. NULL on the inner side breaks `NOT IN`.
- "I can fix `NOT IN` by adding `WHERE col IS NOT NULL` inside the subquery" — yes, but only if you remember. Easier: use `NOT EXISTS`.
- "Why does NULL break it?" — three-valued logic: `x NOT IN (NULL,...)` evaluates to UNKNOWN, which is never TRUE.
- "Won't the planner figure it out?" — it can't. The two queries have **different semantics**, not just different syntax.

## Brute force approach
Application-side: pull all customer IDs, pull all order customer_ids, build a set, do `customers - order_set`. Works but pumps gigabytes through the wire. The right tool is one SQL statement.

The other brute force — using `NOT IN` without checking for NULLs — looks elegant, runs fine in dev where the inner column happens to be NOT NULL, and silently breaks in prod. The interviewer will reward you for **not** falling for this.

## Optimal approach
`NOT EXISTS` with a correlated predicate. The planner turns it into a `Hash Anti Join` (or `Nested Loop Anti Join` with the right index). On the inner side you only need one column, and you can `SELECT 1` — the engine doesn't care.

## Solution (SQL)

```sql
CREATE TABLE customers (id INT PRIMARY KEY, name TEXT);
CREATE TABLE orders    (id INT PRIMARY KEY, customer_id INT, total NUMERIC);

INSERT INTO customers VALUES (1,'Alice'),(2,'Bob'),(3,'Carol'),(4,'Dave');
INSERT INTO orders    VALUES (10,1,100),(11,1,250),(12,3,80),(13,NULL,50);
--                                                            ^^^^ NULL booby trap
```

```sql
-- RECOMMENDED: NOT EXISTS — safe regardless of NULLs
SELECT c.id, c.name
FROM   customers c
WHERE  NOT EXISTS (
         SELECT 1 FROM orders o WHERE o.customer_id = c.id
       );
-- → Bob, Dave   (3 columns, 2 rows)

-- EQUIVALENT: LEFT JOIN ... IS NULL — same plan, more verbose
SELECT c.id, c.name
FROM   customers c
LEFT   JOIN orders o ON o.customer_id = c.id
WHERE  o.customer_id IS NULL;
-- → Bob, Dave

-- WRONG: NOT IN with a NULL in the inner set
SELECT c.id, c.name
FROM   customers c
WHERE  c.id NOT IN (SELECT customer_id FROM orders);
-- → (empty set — silently broken!)
```

## Step-by-step dry run

For `NOT IN`, the engine expands the inner set to `{1, 1, 3, NULL}` and evaluates per outer row:

```
Bob (id=2):   2 <> 1 = T,  2 <> 1 = T,  2 <> 3 = T,  2 <> NULL = UNKNOWN
              T AND T AND T AND UNKNOWN = UNKNOWN  → row NOT emitted (NOT IN false-ish)
Dave (id=4):  4<>1=T, 4<>1=T, 4<>3=T, 4<>NULL=UNKNOWN → UNKNOWN → not emitted
```

Result: zero rows. Bug.

For `NOT EXISTS`, per outer row the engine probes `orders` by `customer_id = c.id`. NULLs in `customer_id` never match any non-NULL `c.id` and so don't influence the predicate at all. Bob and Dave correctly emit.

## How to think aloud in the interview
1. *"Anti-join — 'customers with no orders'. Three idioms; I'll go with `NOT EXISTS` because it's NULL-safe."*
2. *"If you wanted, I could write it as a LEFT JOIN ... IS NULL — same physical plan in Postgres (`Hash Anti Join`)."*
3. *"I'd avoid `NOT IN` — if `orders.customer_id` has any NULL, the subquery silently returns zero rows. Classic production bug."*
4. *"For performance on 100M rows, I want an index on `orders.customer_id` so the anti-join is hash or merge, not nested loop."*
5. *"If the question becomes multi-column, only `NOT EXISTS` cleanly scales."*

## Important takeaways
- **Default to `NOT EXISTS`** for anti-join. It's NULL-safe, plan-friendly, multi-column-friendly.
- `LEFT JOIN ... IS NULL` is equivalent and sometimes clearer in joins where you also want columns from the inner side.
- `NOT IN` is a footgun unless you're certain the inner column is NOT NULL.
- The physical operator is `Anti Join`; check with `EXPLAIN`.
- Cross-reference: `backend-data-prep/sql/02-advanced-sql.md` "EXISTS vs IN vs JOIN" for deeper theory.

## Variants
1. **Anti-join with extra filter on inner side.** "Customers with no orders *in 2024*." Put the filter in `EXISTS`'s WHERE: `NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id AND o.created_at >= '2024-01-01')`.
2. **Multi-column anti-join.** "Find `(user_id, product_id)` pairs in `wishlist` that aren't in `purchases`." Switch to `NOT EXISTS` with two-column correlation.
3. **`EXCEPT`/`MINUS`.** `SELECT id FROM customers EXCEPT SELECT customer_id FROM orders` — set-based; auto-distinct; works only when both sides are the same shape.

## Revision notes

> **Anti-join cram block**
> - Goal: rows in A with NO match in B.
> - **Use:** `NOT EXISTS` (default).
> - **Equivalent:** `LEFT JOIN B ... WHERE B.k IS NULL`.
> - **DANGEROUS:** `NOT IN` — one NULL in inner subquery → zero rows.
> - Postgres compiles all safe forms to `Hash/Nested-Loop Anti Join`.
> - Index inner-side join column for sub-second performance.
> - `EXCEPT` for whole-row set difference; auto-distinct.
> - Multi-column: only `NOT EXISTS` is clean.
> - When in doubt, prefer `NOT EXISTS`. Memorize the NULL trap story.
