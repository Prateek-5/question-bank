# Top-N per group — window functions vs LATERAL vs correlated subquery

## Source / Origin
- Canonical SQL interview question. Appears in every senior backend round and many analytics interviews.
- LeetCode #185 "Department Top Three Salaries", #176 "Second Highest Salary".
- Reference: PostgreSQL docs on window functions and `LATERAL`.
- Companion: `backend-data-prep/sql/04-query-patterns.md`.
- Classic prompt: *"Find the top 3 highest-paid employees per department. Show me three ways to write this and pick which one you'd ship to production."*

## Why this question matters in interviews
This question is the **window-function literacy gate**. Mid-level candidates write a correlated subquery; senior candidates write `ROW_NUMBER() OVER (PARTITION BY ...)` without thinking; *staff* candidates know when `LATERAL` beats the window function (small N, indexed sort key, many groups). The interviewer wants:

1. You **know window functions exist** and reach for them first.
2. You can **explain `ROW_NUMBER` vs `RANK` vs `DENSE_RANK`** (and which one the prompt asks for).
3. You can **discuss the LATERAL alternative** for the case where the window function is too expensive.
4. You can **read EXPLAIN** and tell which plan the planner picked.

Getting just (1) and (2) is mid-level. Getting (3) and (4) is senior.

## Concepts involved

### Syntax to lock in

```sql
-- Window function (the default modern answer)
SELECT * FROM (
  SELECT e.*,
         ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rn
  FROM employees e
) ranked
WHERE rn <= 3;

-- LATERAL (the index-friendly alternative for small N)
SELECT d.id AS dept_id, top.*
FROM departments d
CROSS JOIN LATERAL (
  SELECT * FROM employees e
  WHERE e.department_id = d.id
  ORDER BY e.salary DESC
  LIMIT 3
) top;

-- Correlated subquery (the textbook answer; rarely the best)
SELECT * FROM employees e1
WHERE (
  SELECT COUNT(*) FROM employees e2
  WHERE e2.department_id = e1.department_id
    AND e2.salary > e1.salary
) < 3;
```

### Window function variants — pick the right one

| Function | Behaviour on ties (two with same salary) |
|---|---|
| `ROW_NUMBER()` | Arbitrary tie-break; assigns 1, 2, 3, 4 — exactly N rows |
| `RANK()` | Ties get same rank, leaves gap: 1, 2, 2, 4 |
| `DENSE_RANK()` | Ties get same rank, no gap: 1, 2, 2, 3 |

The prompt usually says "top 3"; clarify whether they mean "exactly 3 rows" (`ROW_NUMBER`), "at least 3 distinct salaries" (`DENSE_RANK <= 3`), or "all ties at rank 3 included" (`RANK <= 3`).

### Edge cases / interview traps

1. **Ties.** "Top 3" is ambiguous. Always ask the interviewer or call it out and pick one explicitly.
2. **NULLs in ORDER BY.** `ORDER BY salary DESC` puts NULLs first in Postgres (default `NULLS FIRST` for DESC). Senior candidates add `NULLS LAST` or `WHERE salary IS NOT NULL`.
3. **Window function can't go in WHERE.** You must wrap in a subquery or CTE — `WHERE ROW_NUMBER() OVER (...) <= 3` is a syntax error.
4. **LATERAL needs an index on `(department_id, salary DESC)`** to be efficient. Without it, it does a full scan per group.
5. **Correlated subquery is O(rows × rows-per-group)** — fine for small tables, catastrophic for large ones.
6. **`DISTINCT ON (department_id)`** is Postgres-only sugar for "top 1 per group"; doesn't extend to top N.
7. **Pagination of top N** — combining `WHERE rn <= N` with `OFFSET m` doesn't compose well; use keyset on (group, rank).
8. **Window functions run *after* `WHERE`, *before* `ORDER BY`.** That's why ranking on filtered subset is tricky — filter inside a subquery first.

## Mental Model

Three operators, three execution shapes:

```
Window function:
  Reads ALL rows of employees, partitions by department,
  sorts each partition by salary DESC, assigns row numbers,
  then filters rn <= 3.
  Cost: O(N log N) for the sort.

LATERAL:
  For each row of departments (small table), runs an indexed
  ORDER BY ... LIMIT 3 lookup on employees.
  Cost: O(D * log E) where D = #departments, E = #employees.
  Best when D is small and an index exists.

Correlated subquery:
  For each employee, counts how many employees in the same
  department earn more. Keeps if count < 3.
  Cost: O(E^2 / D) in the absolute worst case.
  Worst plan in almost every realistic scenario.
```

Picture for the window-function shape:

```
departments     employees (sorted within each dept by salary DESC)
                                                           rn
+-------+       dept=1: { Alice 200k, Bob 180k, Cat 170k,    1,2,3,
| 1 Eng |                Dan 160k, Eve 150k }                  4,5
| 2 Sal |       dept=2: { Fox 220k, Gus 190k }                1,2
| 3 Mkt |       dept=3: { Hua 210k, Ian 195k, Jay 188k,       1,2,3,
+-------+                 Kim 175k }                            4

WHERE rn <= 3  →  Alice, Bob, Cat, Fox, Gus, Hua, Ian, Jay.
```

LATERAL shape:

```
For each row d of departments:
  d=1: indexed lookup employees WHERE department_id=1 ORDER BY salary DESC LIMIT 3
       → Alice, Bob, Cat
  d=2: → Fox, Gus
  d=3: → Hua, Ian, Jay

Index used:  CREATE INDEX ON employees(department_id, salary DESC);
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                          critical — without this, LATERAL is no faster than the window.
```

## Why interviewers care

- Window functions are the **canonical senior SQL primitive** introduced in SQL:2003 and widely deployed by 2015. If you don't reach for them, you're stuck in 1999.
- LATERAL is the **planner-bypass tool** when you know better than the optimiser. Senior candidates know when to bypass; juniors trust the planner blindly.
- The choice between window and LATERAL forces a discussion of **cardinality** (D vs E) and **indexes**, which is the senior-level vocabulary for query tuning.
- Top-N-per-group generalises to gaps-and-islands, sessionisation, leaderboards, recent-activity feeds, and dozens of other production patterns.

## Common beginner confusion

- *"`LIMIT 3` solves this."* `LIMIT 3` gives you top 3 *globally*, not per group. Most common slip.
- *"`GROUP BY department_id` plus aggregate."* You can get the max salary per dept, but not the row of the employee earning that salary, and certainly not the top 3.
- *"`HAVING ROW_NUMBER() <= 3`."* `HAVING` runs before window functions; doesn't work. Wrap in subquery.
- *"Window functions and aggregations are the same."* Aggregations collapse rows; window functions add a column without collapsing.
- *"`SELECT * FROM employees ORDER BY salary DESC LIMIT 3 PER department_id`."* No such syntax in standard SQL. Don't invent it.

## Brute force approach

The correlated subquery:

```sql
SELECT * FROM employees e1
WHERE (
  SELECT COUNT(*) FROM employees e2
  WHERE e2.department_id = e1.department_id
    AND e2.salary > e1.salary
) < 3;
```

For each of E rows, run an aggregate over a sub-partition. Without an index, O(E²); with a good index, O(E · log E). It works on small datasets and gives clean ties-aware semantics (similar to `DENSE_RANK <= 3`), but it's the slowest of the three for any non-trivial table.

## Optimal approach

**Decision tree:**

```
How many groups (D) vs rows per group (avg E/D)?
├── D small, E/D large, indexed (dept_id, salary DESC) → LATERAL
├── D large, no index, or you want ROW_NUMBER/RANK     → Window function
└── Both tables small (<10k rows)                       → either works
```

**Default for the interview:** window function with `ROW_NUMBER`. It's the modern idiom; explain clearly; mention LATERAL as the optimisation if N is small and an index supports it.

## Solution (PostgreSQL)

```sql
-- Setup
CREATE TABLE departments (id INT PRIMARY KEY, name TEXT);
CREATE TABLE employees (
  id INT PRIMARY KEY,
  department_id INT REFERENCES departments(id),
  name TEXT,
  salary NUMERIC(10,2)
);
CREATE INDEX idx_emp_dept_sal ON employees(department_id, salary DESC);

-- Window function — the default
WITH ranked AS (
  SELECT e.*,
         ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC NULLS LAST) AS rn
  FROM employees e
)
SELECT id, department_id, name, salary
FROM ranked
WHERE rn <= 3
ORDER BY department_id, rn;

-- LATERAL — the optimisation when D is small and the index exists
SELECT d.id AS dept_id, d.name AS dept_name, top.id, top.name, top.salary
FROM departments d
CROSS JOIN LATERAL (
  SELECT * FROM employees e
  WHERE e.department_id = d.id
  ORDER BY e.salary DESC NULLS LAST
  LIMIT 3
) top
ORDER BY d.id, top.salary DESC;

-- Ties variant — include all employees at the third-highest salary
WITH ranked AS (
  SELECT e.*, DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS dr
  FROM employees e
)
SELECT * FROM ranked WHERE dr <= 3;

-- "Top 1 per group" Postgres shortcut
SELECT DISTINCT ON (department_id) *
FROM employees
ORDER BY department_id, salary DESC NULLS LAST;
```

### Comparing plans (Postgres EXPLAIN ANALYZE)

```
Window function plan:
  WindowAgg
    -> Sort (department_id, salary DESC)
       -> Seq Scan on employees
  Cost ~ sort cost on full table.

LATERAL plan (with index):
  Nested Loop
    -> Seq Scan on departments
    -> Limit
       -> Index Scan using idx_emp_dept_sal on employees
  Cost ~ D * log(E/D) — much better when D << E.
```

## Step-by-step dry run

Data:
```
employees:
  (Alice, dept=1, 200k)  (Bob, dept=1, 180k)  (Cat, dept=1, 170k)  (Dan, dept=1, 160k)
  (Eve, dept=2, 220k)    (Fox, dept=2, 190k)
  (Gus, dept=3, 210k)    (Hua, dept=3, 195k)  (Ian, dept=3, 188k)  (Jay, dept=3, 175k)
```

Window function trace:
```
Step 1: Scan employees, project (e.*, dept_id, salary)
Step 2: Sort by (dept_id, salary DESC):
    dept=1: Alice 200, Bob 180, Cat 170, Dan 160
    dept=2: Eve 220, Fox 190
    dept=3: Gus 210, Hua 195, Ian 188, Jay 175
Step 3: WindowAgg assigns rn within each partition:
    dept=1: Alice(1), Bob(2), Cat(3), Dan(4)
    dept=2: Eve(1), Fox(2)
    dept=3: Gus(1), Hua(2), Ian(3), Jay(4)
Step 4: Outer query filters rn <= 3:
    {Alice, Bob, Cat, Eve, Fox, Gus, Hua, Ian}
```

LATERAL trace (with index `(department_id, salary DESC)`):
```
For each row of departments:
  dept=1: index scan jumps to (1, +inf), reads first 3 in salary-DESC order
          → Alice(200), Bob(180), Cat(170). Stop.
  dept=2: → Eve(220), Fox(190). Stop (only 2 rows).
  dept=3: → Gus(210), Hua(195), Ian(188). Stop.
Total inner reads: 3+2+3 = 8 rows. (vs. full table scan + sort for the window.)
```

For the ties case — suppose Dan also earned 170k. With `ROW_NUMBER`, Dan gets rn=4 and is excluded. With `DENSE_RANK`, Dan and Cat both get dr=3 and both are returned. The interviewer cares that you can switch between these.

## How to think aloud in the interview

> "Top-N-per-group. My default is a window function: `ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC)` in a subquery, then `WHERE rn <= 3` in the outer query. I have to wrap it because window functions can't go in `WHERE` directly — they're evaluated after `WHERE` and before `ORDER BY`.
>
> One question first: how do you want ties handled? `ROW_NUMBER` gives exactly 3 rows, breaking ties arbitrarily. `RANK` includes all rows tied at rank 3 but skips ranks. `DENSE_RANK` is 'top 3 distinct salaries' — usually what people mean.
>
> Performance: the window function sorts the whole table — O(N log N). If `departments` has, say, 50 rows and `employees` has 10 million, that's a lot of wasted sort work. The LATERAL alternative is `CROSS JOIN LATERAL (SELECT ... FROM employees WHERE dept_id = d.id ORDER BY salary DESC LIMIT 3)` — with an index on `(department_id, salary DESC)` it does 50 indexed range scans of 3 rows each, which is dramatically faster.
>
> I'd ship LATERAL if the index exists and the cardinality favours it; window function otherwise. Correlated subquery — count employees who earn more — is the textbook answer but it's O(E²/D); I'd reject it for any production table over a few thousand rows."

## Important takeaways

- **Window function is the default** modern answer. `ROW_NUMBER()` for exactly N rows; `DENSE_RANK()` for "top N distinct values".
- **Window functions can't appear in `WHERE`** — wrap in CTE/subquery.
- **LATERAL + index is faster** when groups are few and the sort key is indexed; gives O(D · log E) vs O(N log N).
- **Correlated subquery is the slowest** but the most explicit about tie semantics.
- **Always clarify ties** — "exactly 3", "all of top 3 distinct", "all tied at 3rd"?
- **Always handle NULLs** in `ORDER BY` — `NULLS FIRST`/`NULLS LAST`.
- **`DISTINCT ON`** is Postgres sugar for "top 1 per group"; doesn't extend to N > 1.

## Variants

1. **Most recent N events per user** — same pattern: `ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_time DESC)`. Used for activity feeds, audit trails.
2. **Top N with ties (RANK ≤ N)** — different semantics; e.g. "top 10 players including ties at rank 10".
3. **Second-highest salary per department** — `ROW_NUMBER = 2` or `DENSE_RANK = 2`.
4. **Top N within a sliding time window** — combine partition with a date filter; or use `RANGE BETWEEN` windowing.
5. **Top N per group with pagination** — keyset on `(group, rank)`; `OFFSET` over the ranked set is fine but doesn't scale.
6. **Cross-database support** — window functions standard since SQL:2003. MySQL added them in 8.0; older MySQL must use the correlated subquery or self-join trick.
7. **`SELECT DISTINCT ON`** — Postgres-only top-1-per-group shorthand; clean syntax but inflexible.

## Revision notes

> **top-N-per-group — 60 second recap**
> - Default: `ROW_NUMBER() OVER (PARTITION BY g ORDER BY k DESC)` in subquery, filter `rn <= N`.
> - Ties: `ROW_NUMBER` (exact N), `DENSE_RANK` (top N distinct), `RANK` (with gaps).
> - **Always clarify tie semantics** — the prompt is ambiguous.
> - **Window functions can't appear in WHERE** — wrap.
> - LATERAL optimisation: `CROSS JOIN LATERAL (SELECT ... LIMIT N)` with index on `(group, key DESC)`; O(D log E) vs O(N log N).
> - Correlated count-greater-than subquery: textbook, slowest, ties-aware.
> - `DISTINCT ON (g) ... ORDER BY g, k DESC` for top-1 only (Postgres).
> - Handle NULLs in ORDER BY explicitly.
