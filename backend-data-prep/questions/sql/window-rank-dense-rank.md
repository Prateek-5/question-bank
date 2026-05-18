# Window Rank — RANK vs DENSE_RANK vs ROW_NUMBER

## Source / Origin
- LeetCode #178 "Rank Scores", #184 "Department Highest Salary".
- Stratascratch "top 3 salaries per department", "find the 2nd highest score".
- Real prod: leaderboards, prize-tier assignment, deduplication picks.

## Why this question matters in interviews
The three ranking functions sound the same but rank ties differently. Picking the wrong one corrupts leaderboards and ships subtly wrong "top-3" reports. Interviewers ask because the answer is **a one-line difference in behavior** that's easy to get wrong under pressure.

Beyond syntax, it tests whether you understand that ranking is a **window function**, not an aggregate — it requires `ORDER BY` inside `OVER`, optionally with `PARTITION BY`. The classic follow-up — "give me the 2nd-highest salary per department" — separates candidates who reach for window functions from candidates who write three nested correlated subqueries.

## Concepts involved

### Syntax to lock in
```sql
SELECT name, salary,
  ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn,
  RANK()       OVER (ORDER BY salary DESC) AS rk,
  DENSE_RANK() OVER (ORDER BY salary DESC) AS dr
FROM employees;
```

```
 salary   rn   rk   dr
 ──────   ──   ──   ──
 100      1    1    1
 100      2    1    1
 100      3    1    1
  90      4    4    2   ← rank jumps to 4 (3 tied above);  dense_rank only to 2
  80      5    5    3
```

### Edge cases / interview traps
1. **Tie handling.**
   - `ROW_NUMBER()` — arbitrary tiebreak, every row gets a unique number.
   - `RANK()` — ties share the rank, then the next row jumps (1,1,1,4,5).
   - `DENSE_RANK()` — ties share, no gaps (1,1,1,2,3).
2. **ORDER BY inside OVER is mandatory.** Without it, ranking is undefined / errors.
3. **Top-N per group** = `ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) <= N`. Need a subquery / CTE because WHERE can't see window outputs (see `having-vs-where.md`).
4. **`NTILE(N)`** — splits into N equal buckets (quartiles, deciles). Useful but rarely asked.
5. **DETERMINISTIC tiebreak.** `ROW_NUMBER` on duplicate sort keys is non-deterministic across runs. Add a tie-breaker column like `id` for reproducibility.
6. **MySQL pre-8.0** lacks window functions entirely — fall back to variables `@rank`.
7. **`RANK` on a single window vs partition** — `OVER (PARTITION BY dept ORDER BY salary DESC)` ranks within department. Without PARTITION, ranks globally.
8. **PERCENT_RANK / CUME_DIST** — `PERCENT_RANK()` is `(rank-1)/(N-1)`; `CUME_DIST()` is `nth/total`. Sometimes asked for "top quartile".

## Mental Model

```
   Imagine racers crossing a finish line by score:

   row_number  →  bib numbers, no ties. Each racer gets a unique 1,2,3…
   rank        →  Olympic standings: tied gold medalists are both 1st,
                  next runner is 3rd (silver skipped).
   dense_rank  →  "place" without gaps: 1, 1, 2. The next runner is 2nd.
```

When the question says "top N", you almost always want `ROW_NUMBER()` (one row per rank) or `DENSE_RANK()` (top N distinct salaries, including ties). `RANK()` is the right answer only when you specifically want Olympic-medal semantics.

## Why interviewers care
- Lots of real-world reports get this wrong because the three look interchangeable.
- Tests **understanding of windowing** (PARTITION + ORDER + frame is irrelevant for ranks).
- Probes follow-up skill: "top-N per group" is a guaranteed deep-dive.

## Common beginner confusion
- "Aren't they all 'rank' functions?" — syntactically yes, semantically very different.
- "Why can't I `WHERE RANK() OVER (...) <= 3`?" — window functions run after WHERE. Wrap in CTE.
- "If I have ties, how do I pick one?" — add a tiebreaker column to ORDER BY (e.g. `ORDER BY salary DESC, id`).
- "Will the planner sort once?" — yes, one sort per distinct `OVER (...)` clause.

## Brute force approach
Correlated subquery for rank:
```sql
SELECT salary,
  (SELECT COUNT(DISTINCT salary) FROM employees WHERE salary >= e.salary) AS dr
FROM employees e;
```
Correct but `O(N²)`. Window function is `O(N log N)`.

For "top 3 per department" without window: self-join the table to itself filtering "fewer than 3 higher salaries above me per dept". Same `O(N²)` pain.

## Optimal approach
- `ROW_NUMBER() OVER (PARTITION BY x ORDER BY y DESC)` for "give me row 1, 2, 3 per group".
- `DENSE_RANK()` for "top 3 distinct values per group" (tie-inclusive).
- `RANK()` for Olympic-style rankings (rarely the right semantics).

Always wrap in a CTE/subquery and filter on the window output in the outer query.

## Solution (SQL)

```sql
CREATE TABLE employees (
  id        INT PRIMARY KEY,
  name      TEXT,
  dept      TEXT,
  salary    INT
);
INSERT INTO employees VALUES
 (1,'Alice','eng',150),(2,'Bob','eng',150),(3,'Carol','eng',120),
 (4,'Dave','eng',100),(5,'Eve','eng', 95),
 (6,'Frank','sales',80),(7,'Grace','sales',70);
```

```sql
-- All three ranks per department
SELECT
  dept, name, salary,
  ROW_NUMBER() OVER w AS rn,
  RANK()       OVER w AS rk,
  DENSE_RANK() OVER w AS dr
FROM   employees
WINDOW w AS (PARTITION BY dept ORDER BY salary DESC);

-- Top 3 distinct salaries per department (tie-inclusive)
WITH ranked AS (
  SELECT *, DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS dr
  FROM employees
)
SELECT * FROM ranked WHERE dr <= 3;

-- Strictly top 3 rows per department (tie-exclusive, deterministic)
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC, id) AS rn
  FROM employees
)
SELECT * FROM ranked WHERE rn <= 3;

-- 2nd-highest salary per department (handle ties → 2nd distinct salary)
WITH ranked AS (
  SELECT *, DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS dr
  FROM employees
)
SELECT dept, MAX(salary) FROM ranked WHERE dr = 2 GROUP BY dept;
```

## Step-by-step dry run

For department `eng`, sorted by salary DESC:

```
 row  salary    rn  rk  dr
 ───  ──────    ──  ──  ──
  1   150 (A)    1   1   1
  2   150 (B)    2   1   1     ← tie with row 1
  3   120 (C)    3   3   2     ← rank jumps to 3; dense_rank to 2
  4   100 (D)    4   4   3
  5    95 (E)    5   5   4

"Top 3 distinct salaries" via DENSE_RANK ≤ 3 → Alice, Bob, Carol, Dave.
"Top 3 rows" via ROW_NUMBER ≤ 3 → Alice, Bob, Carol.
"Top 3 by RANK ≤ 3" → Alice, Bob, Carol. (Skips position 3 entirely... no row has rank=3 here.)
```

Notice how `RANK ≤ 3` and `DENSE_RANK ≤ 3` differ subtly when there's a tie.

## How to think aloud in the interview
1. *"I'll use ROW_NUMBER for strict top-N (one row per rank), DENSE_RANK for top-N distinct values, RANK only if Olympic-medal semantics are needed."*
2. *"Wrap in a CTE — can't `WHERE rank <= 3` directly because window functions run after WHERE."*
3. *"For ties, ROW_NUMBER picks arbitrarily; I'll add `, id` to ORDER BY for reproducibility."*
4. *"Partition by department; one sort per distinct OVER clause. Three identical OVER clauses share."*
5. *"At scale, an index on `(dept, salary DESC)` makes the partition+sort free."*

## Important takeaways
- Three flavours, three behaviors: ROW_NUMBER (unique), RANK (gaps), DENSE_RANK (no gaps).
- ORDER BY in OVER is mandatory.
- WHERE can't reference window outputs → wrap in CTE.
- Add a tie-breaker for determinism.
- MySQL pre-8.0 has no window functions; emulate with `@variable`.
- See `backend-data-prep/sql/02-advanced-sql.md` "Window functions" for theory.

## Variants
1. **"Nth highest salary"** — `DENSE_RANK = N` is the safe semantic for tie-aware "Nth distinct value". `ROW_NUMBER = N` if you want the Nth row.
2. **NTILE buckets** — `NTILE(4)` splits into quartiles. Edge case: rows / 4 not integer → first buckets get one more row.
3. **PERCENT_RANK / CUME_DIST** — `PERCENT_RANK()` for percentile-style; useful in stats reports.

## Revision notes

> **Rank functions cram block**
> - ROW_NUMBER → unique, arbitrary tiebreak. "Top-N rows."
> - RANK       → ties share, gap after. (1,1,1,4,5.) "Olympic medals."
> - DENSE_RANK → ties share, no gap. (1,1,1,2,3.) "Top-N distinct values."
> - `OVER (PARTITION BY p ORDER BY o)` mandatory; ORDER BY is required.
> - `WHERE rank <= 3` is ILLEGAL — wrap in CTE.
> - Add `, id` to ORDER BY for deterministic tie-breaking.
> - MySQL ≥ 8.0 only; older MySQL emulate with `@vars`.
> - Index on `(partition_col, order_col DESC)` to free the sort.
> - Pick the right flavour based on **tie semantics**.
