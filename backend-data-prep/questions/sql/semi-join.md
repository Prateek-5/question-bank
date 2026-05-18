# Semi-Join — EXISTS vs IN vs INNER JOIN-DISTINCT

## Source / Origin
- LeetCode #1148 "Article Views I", #1393, classic interview at Atlassian/Razorpay.
- Stratascratch "Users who purchased at least one premium item".
- Real prod: deduplicating analytics joins, "find sellers who shipped at least once last week".

## Why this question matters in interviews
A semi-join keeps outer rows that **have at least one** match in another table — *without* multiplying rows. Candidates routinely write `INNER JOIN ... GROUP BY` or `INNER JOIN ... DISTINCT`, blow up the result with duplicates, and then patch it. Senior engineers reach straight for `EXISTS`.

The interviewer is also testing whether you understand that `IN` and `EXISTS` are logically equivalent **when no NULLs are involved**, but the planner may pick different physical operators. On large tables `EXISTS` short-circuits on the first match per outer row; `INNER JOIN + DISTINCT` builds a full join then deduplicates — orders of magnitude slower.

## Concepts involved

### Syntax to lock in
```sql
-- 1. EXISTS — semi-join, short-circuits, NULL-safe, no row inflation
SELECT u.* FROM users u
WHERE  EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);

-- 2. IN — same semantics for the no-NULL case; planner often rewrites to EXISTS
SELECT u.* FROM users u
WHERE  u.id IN (SELECT user_id FROM orders);

-- 3. INNER JOIN + DISTINCT — works but worst-of-both-worlds
SELECT DISTINCT u.* FROM users u JOIN orders o ON o.user_id = u.id;
```

### Edge cases / interview traps
1. **Row inflation in plain INNER JOIN.** A user with 50 orders shows up 50 times. The `DISTINCT` patch hides this but pays the multiplication cost first.
2. **NULL inside `IN` subquery is harmless** for semi-join (unlike `NOT IN`). `id IN (1,2,NULL)` is TRUE if `id=1` or `2`; UNKNOWN otherwise — UNKNOWN is treated the same as FALSE by `WHERE`.
3. **`EXISTS (SELECT *) vs SELECT 1`** — the optimiser doesn't care; engines short-circuit either way. Use `SELECT 1` only for style.
4. **Correlated vs uncorrelated subquery cost.** Uncorrelated `IN (SELECT user_id FROM orders)` builds the subquery once; correlated `EXISTS` may evaluate per outer row unless rewritten to a semi-join (Postgres does this).
5. **Multi-column semi-join.** `EXISTS` handles it cleanly: `EXISTS (... WHERE o.user_id=u.id AND o.product_id=p.id)`. `IN` needs row-constructor form `(u.id, p.id) IN (...)` which not every engine supports.
6. **Semi-join with extra columns from the inner side?** Not possible by definition — semi-joins return only outer columns. If you want inner data, you need a JOIN (and to handle duplicates).
7. **MySQL pre-8.0** was famously bad at correlated subqueries — wrote naive nested-loop. Newer versions inline them. Mention if asked about portability.
8. **`SELECT * FROM users WHERE id IN (SELECT id FROM ...)` aliasing trap.** If both columns are called `id` and you reference an unqualified `id` in the subquery, it silently resolves to the outer table — making every row match. Always qualify.

## Mental Model

```
   Outer (users)          Inner (orders)        Semi-join keeps outer rows
                                                with ≥ 1 match — no dupes.
     u1 ─┐                   u1, prod-x  ┐
     u2  │   ─── semi-join   u1, prod-y  │   → {u1, u3}
     u3  │       ←────       u3, prod-z  │
     u4 ─┘                  (nothing for u2/u4)
```

Compare with INNER JOIN: same data produces `{(u1,x),(u1,y),(u3,z)}` — three rows. Semi-join produces two. That difference IS the question.

## Why interviewers care
- Tests whether you reach for the **right physical operator** (semi-join) or the wrong one (inner join + distinct).
- Tests **plan-cost intuition**: short-circuit on first match beats build-then-dedup at scale.
- Tests **NULL discipline**: confirms you remember `IN` is safe for semi-join but `NOT IN` isn't for anti-join.

## Common beginner confusion
- "Just use INNER JOIN and DISTINCT" — works but expensive and signals junior.
- "EXISTS needs a real column in the SELECT" — no, `SELECT 1`, `SELECT *`, `SELECT NULL` all behave identically.
- "IN and EXISTS aren't the same" — for non-NULL inner sets they are, semantically.
- "EXISTS is always faster than IN" — usually true on correlated subqueries; modern planners are flat.

## Brute force approach
`SELECT DISTINCT u.* FROM users u JOIN orders o ON o.user_id = u.id`. The build phase joins every (user, order) pair, then a sort/hash deduplicates. For a user with 1000 orders that's 999 wasted joined rows. Correct but inefficient.

## Optimal approach
`EXISTS` with a correlated predicate. Planner compiles to `Hash Semi Join` (Postgres) or short-circuit nested loop. Stops scanning inner side the moment a single match is found per outer row.

## Solution (SQL)

```sql
CREATE TABLE users  (id INT PRIMARY KEY, name TEXT);
CREATE TABLE orders (id INT PRIMARY KEY, user_id INT, total NUMERIC);

INSERT INTO users  VALUES (1,'Alice'),(2,'Bob'),(3,'Carol'),(4,'Dave');
INSERT INTO orders VALUES (10,1,100),(11,1,250),(12,1,75),(13,3,80);
```

```sql
-- BEST: EXISTS — semi-join, short-circuit
SELECT u.id, u.name
FROM   users u
WHERE  EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
-- → Alice, Carol

-- EQUIVALENT: IN — planner usually picks Hash Semi Join here too
SELECT u.id, u.name
FROM   users u
WHERE  u.id IN (SELECT user_id FROM orders);

-- AVOIDABLE: JOIN + DISTINCT — correct but inflates then deduplicates
SELECT DISTINCT u.id, u.name
FROM   users u
JOIN   orders o ON o.user_id = u.id;
```

## Step-by-step dry run

EXISTS plan:

```
Build hash on orders.user_id:  {1, 3}
For each user u:
  u=1: probe hash for 1 → hit → emit Alice. (no further probing of orders)
  u=2: probe hash for 2 → miss → drop.
  u=3: probe hash for 3 → hit → emit Carol.
  u=4: probe hash for 4 → miss → drop.
```

INNER JOIN + DISTINCT plan (for contrast):

```
Hash join produces: (1,Alice,10), (1,Alice,11), (1,Alice,12), (3,Carol,13)  -- 4 rows
Sort/dedup: → (Alice), (Carol)
```

Both correct; the EXISTS plan does strictly less work (no row inflation, early termination).

## How to think aloud in the interview
1. *"This is a semi-join — I want users who have at least one order, not every user-order pair. Reach for `EXISTS`."*
2. *"`IN` would also work and is equivalent semantically here; the planner will probably pick the same physical operator."*
3. *"I'd avoid `INNER JOIN ... DISTINCT` — it builds the full join first, then deduplicates. Wasted work, especially for a user with many orders."*
4. *"On 100M rows I'd verify the planner picked a Hash Semi Join via `EXPLAIN`, and confirm `orders.user_id` has an index."*
5. *"If they want columns from `orders` in the output too, semi-join is the wrong tool — that's a real JOIN with a dedup strategy."*

## Important takeaways
- Default: `EXISTS`. Semantically identical to `IN` for non-NULL cases, plan-wise often identical, and never row-inflating.
- Never use `INNER JOIN + DISTINCT` to fake a semi-join.
- Multi-column semi-join → only `EXISTS` is universally clean.
- Short-circuit-on-first-match is the win at scale.
- See `backend-data-prep/sql/02-advanced-sql.md` "EXISTS vs IN" for planner deep dive.

## Variants
1. **"Users who have purchased ≥ 3 distinct products"** → `EXISTS` won't cut it; needs `GROUP BY` with `HAVING COUNT(DISTINCT product_id) >= 3` or a correlated subquery counting.
2. **"Users who have ordered every product in a list"** → relational division. Use `NOT EXISTS (... NOT EXISTS ...)` (double negation).
3. **MySQL pre-8.0 trap.** Correlated `EXISTS` was notoriously slow. Rewrite as `JOIN ... GROUP BY user_id` if performance is critical there.

## Revision notes

> **Semi-join cram block**
> - Goal: outer rows with ≥1 match, no inflation.
> - **Default:** `EXISTS (correlated subquery)`.
> - `IN (subquery)` — equivalent for non-NULL; same plan in modern Postgres.
> - Never `INNER JOIN + DISTINCT` (builds full join first).
> - Physical op: `Hash Semi Join` or short-circuit nested loop.
> - Multi-column → `EXISTS` is the clean path.
> - `SELECT 1` vs `SELECT *` inside EXISTS — no diff, planner ignores projection.
> - Always qualify column names to avoid silent outer-binding bugs.
> - Cousin: anti-join (`NOT EXISTS`). NEVER `NOT IN` if inner column nullable.
