# Median via window functions — percentile_cont, percentile_disc, and the manual trick

## Source / Origin
- Classic analytics interview. LeetCode #569 "Median Employee Salary" (premium), #571 "Find Median Given Frequency of Numbers".
- Reference: PostgreSQL docs on ordered-set aggregates and `WITHIN GROUP`.
- Companion: `backend-data-prep/sql/04-query-patterns.md`.
- Classic prompt: *"Compute the median salary per department. Then do it without using `PERCENTILE_CONT`."*

## Why this question matters in interviews
Median is the **misleading aggregate**. Candidates default to `AVG` and produce mean-by-mistake; senior candidates know that median requires either a `WITHIN GROUP` ordered-set aggregate or the row-number trick. The interviewer is testing:

1. You **know `AVG ≠ MEDIAN`** and can articulate why.
2. You **know `PERCENTILE_CONT` vs `PERCENTILE_DISC`** — these are different functions with different outputs.
3. You can **fall back to the manual trick** when the database doesn't support `PERCENTILE_*` (older MySQL, distributed engines, etc.).
4. You handle **even-count edge case** correctly: for `[10, 20]` is median 15, 10, or 20?

This is the second-line "are you actually fluent in SQL?" question after top-N-per-group.

## Concepts involved

### Syntax to lock in

```sql
-- The modern answer (Postgres / SQL Server / BigQuery / Snowflake)
SELECT department_id,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median_cont,
       PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY salary) AS median_disc
FROM employees
GROUP BY department_id;

-- The manual trick — works everywhere, including pre-8.0 MySQL
WITH ordered AS (
  SELECT department_id, salary,
         ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary) AS rn,
         COUNT(*)    OVER (PARTITION BY department_id)               AS n
  FROM employees
)
SELECT department_id, AVG(salary)::numeric AS median
FROM ordered
WHERE rn IN ((n+1)/2, (n+2)/2)   -- the middle one or two rows
GROUP BY department_id;
```

### `PERCENTILE_CONT` vs `PERCENTILE_DISC` — get this right

```
Values: [10, 20, 30, 40]    n=4, median at position (4+1)/2 = 2.5

PERCENTILE_CONT(0.5):  interpolates between values at floor(2.5)=2 and ceil(2.5)=3
                       → linear interp between 20 and 30 → 25
                       Returns a NEW VALUE not in the set.

PERCENTILE_DISC(0.5):  picks the actual data value at the floor of the position
                       → returns 20 (or 30 depending on engine — Postgres returns 20)
                       Returns an EXISTING VALUE from the set.
```

For **continuous data** (salary, latency), use `PERCENTILE_CONT`. For **discrete categorical data** (counts, ranks), use `PERCENTILE_DISC`.

### Edge cases / interview traps

1. **`AVG` ≠ median.** `AVG` for `[1, 1, 1, 100]` is 25.75; median is 1. The whole point of asking for median is to avoid the outlier sensitivity that `AVG` has.
2. **Even count.** With 4 values, the "middle" is between positions 2 and 3. `PERCENTILE_CONT` averages them; `PERCENTILE_DISC` picks one; the manual trick averages the two adjacent rows.
3. **NULL handling.** `PERCENTILE_CONT` and `PERCENTILE_DISC` ignore NULLs. Manual trick: filter `WHERE salary IS NOT NULL` explicitly.
4. **Ties.** Multiple rows at the median value — fine for `PERCENTILE_DISC` and the manual trick; `PERCENTILE_CONT` still interpolates between sorted positions, so ties produce themselves.
5. **`WITHIN GROUP (ORDER BY ...)` syntax** — easy to miss; senior candidates type it without thinking.
6. **`(n+1)/2, (n+2)/2`** is the integer-arithmetic trick: for odd n=5 both equal 3 (the single middle row); for even n=4 they're 2 and 3 (the two middle rows). `AVG` over those rows gives the median.
7. **Window-based percentile per row.** `PERCENT_RANK()` and `CUME_DIST()` are different — they give a per-row percentile rank, not the median value.
8. **Streaming median is hard.** If the interviewer asks "median over a stream", that's a heap-based DSA question, not SQL.

## Mental Model

### The "middle row of the sorted partition" picture

```
Odd count (n=5):  [10, 20, 30, 40, 50]
                          ^
                          median = 30 (single middle row, rn=3, (5+1)/2=3 and (5+2)/2=3)

Even count (n=4): [10, 20, 30, 40]
                       ^   ^
                       rn=2 rn=3
                       (4+1)/2=2, (4+2)/2=3
                       median = AVG(20, 30) = 25
```

The `(n+1)/2, (n+2)/2` trick selects either 1 or 2 rows depending on parity, *without* a `CASE WHEN n % 2`. Both expressions equal `(n+1)/2` when n is odd (because `(n+2)/2 = (n+1)/2` for odd n in integer division). When n is even, they differ by 1.

### Percentile semantics picture

```
Salary distribution per dept (sorted):
  dept=1: [50, 60, 70, 80, 90]      n=5,  median ≈ 70

PERCENTILE_CONT(0.5):
  position p = 0.5 * (n-1) = 2.0      0-indexed
  → exactly at index 2 → value 70

PERCENTILE_CONT(0.75):
  position p = 0.75 * 4 = 3.0
  → exactly at index 3 → value 80

PERCENTILE_CONT(0.6):
  position p = 0.6 * 4 = 2.4
  → between index 2 (70) and 3 (80)
  → interp: 70 + 0.4 * (80-70) = 74

PERCENTILE_DISC(0.6):
  smallest value v such that CDF(v) >= 0.6
  → 80 in Postgres (or 70 in other engines — check docs)
```

## Why interviewers care

- Median is a real production metric (p50 latency, payment median, ARPU median). Confusing it with `AVG` is a junior tell.
- It exposes whether you know `WITHIN GROUP` ordered-set aggregates — a SQL:2003 feature most candidates haven't touched.
- The manual `ROW_NUMBER`-based fallback proves window-function fluency.
- The CONT/DISC distinction tests whether you understand continuous vs discrete distributions — a stats literacy signal.

## Common beginner confusion

- *"`AVG` gives the median."* Hard no. `AVG` is the mean. They're equal only for symmetric distributions.
- *"`SELECT salary FROM employees ORDER BY salary LIMIT 1 OFFSET n/2`."* Works for a single group; fails the moment the interviewer says "per department". And requires you to know n.
- *"`MEDIAN()` is a built-in."* It is in Oracle, Snowflake, BigQuery, Redshift. **Not** standard SQL, **not** in Postgres or MySQL. Use `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY x)`.
- *"`PERCENTILE_CONT` returns one of the data values."* It doesn't. It interpolates.
- *"`PERCENTILE_DISC(0.5)` returns the lower or upper middle for even counts?"* Depends on engine. Postgres returns the lower; SQL Server returns the lower; Oracle returns the upper. Always check the docs.

## Brute force approach

Pull rows to the app, sort, pick middle. Works on small data, dies the moment the result set doesn't fit memory or you need per-group medians. Also: shifts the work out of the database, where the planner has indexes and partial sorts to help.

## Optimal approach

**Decision tree:**

```
Database supports PERCENTILE_CONT / PERCENTILE_DISC?
├── YES (Postgres, SQL Server, BigQuery, Snowflake, Oracle)
│     ├── Continuous data (salary, latency) → PERCENTILE_CONT
│     └── Discrete data (counts, rank)      → PERCENTILE_DISC
└── NO (MySQL < 8.0.18, some distributed engines)
      └── Manual trick: ROW_NUMBER + COUNT + (n+1)/2, (n+2)/2 + AVG
```

For the interview, write both. Lead with `PERCENTILE_CONT` to show you know the modern idiom; immediately offer the manual trick to show you understand what it does under the hood.

## Solution (PostgreSQL)

```sql
-- Setup
CREATE TABLE employees (
  id INT PRIMARY KEY,
  department_id INT,
  salary NUMERIC(10, 2)
);
INSERT INTO employees VALUES
  (1, 1, 50000), (2, 1, 60000), (3, 1, 70000), (4, 1, 80000), (5, 1, 90000),
  (6, 2, 100000), (7, 2, 120000), (8, 2, 140000), (9, 2, 160000);
-- dept 1: n=5, median=70000.  dept 2: n=4, median=130000 (avg of 120k & 140k).

-- Modern: PERCENTILE_CONT
SELECT department_id,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median
FROM employees
GROUP BY department_id;
-- dept=1 → 70000.0
-- dept=2 → 130000.0  (interpolates between 120k and 140k)

-- PERCENTILE_DISC
SELECT department_id,
       PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY salary) AS median_disc
FROM employees
GROUP BY department_id;
-- dept=1 → 70000   (exact middle row)
-- dept=2 → 120000  (lower of the two middles in Postgres)

-- Manual trick — works everywhere
WITH ordered AS (
  SELECT department_id, salary,
         ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary) AS rn,
         COUNT(*)    OVER (PARTITION BY department_id)                  AS n
  FROM employees
  WHERE salary IS NOT NULL
)
SELECT department_id, AVG(salary)::numeric AS median
FROM ordered
WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
GROUP BY department_id;
-- dept=1 → 70000.0
-- dept=2 → 130000.0
```

### MySQL 8.0+ alternative

MySQL added `PERCENTILE_CONT` only as part of `WITHIN GROUP` in late 8.0 versions. The manual trick is the portable answer:

```sql
WITH ordered AS (
  SELECT department_id, salary,
         ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary) AS rn,
         COUNT(*)    OVER (PARTITION BY department_id)                  AS n
  FROM employees
)
SELECT department_id, AVG(salary) AS median
FROM ordered
WHERE rn IN (FLOOR((n + 1) / 2), FLOOR((n + 2) / 2))
GROUP BY department_id;
```

### Pre-8.0 MySQL (no window functions)

Variable-based "row numbering" — historic; mention it only if asked:

```sql
SELECT department_id, AVG(salary) AS median
FROM (
  SELECT e.*,
         @r := IF(@d = department_id, @r + 1, 1) AS rn,
         @c := COUNT_OVER_DEPT,
         @d := department_id
  FROM employees e
  CROSS JOIN (SELECT @r := 0, @d := NULL) v
  ORDER BY department_id, salary
) ranked
JOIN (SELECT department_id, COUNT(*) AS n FROM employees GROUP BY department_id) cnt
  ON cnt.department_id = ranked.department_id
WHERE rn IN ((n+1) DIV 2, (n+2) DIV 2)
GROUP BY ranked.department_id;
```

Junior signal in 2026 — included only for completeness.

## Step-by-step dry run

For department 1 with salaries `[50000, 60000, 70000, 80000, 90000]`, n=5:

```
After ORDER BY salary:
  rn  salary
  1   50000
  2   60000
  3   70000     ← middle
  4   80000
  5   90000

n=5, so (n+1)/2 = 3, (n+2)/2 = 3.
WHERE rn IN (3, 3) → only the middle row.
AVG(70000) = 70000. ✓
```

For department 2 with salaries `[100000, 120000, 140000, 160000]`, n=4:

```
rn  salary
1   100000
2   120000   ← lower middle
3   140000   ← upper middle
4   160000

n=4, so (n+1)/2 = 2, (n+2)/2 = 3.
WHERE rn IN (2, 3) → two middle rows.
AVG(120000, 140000) = 130000. ✓
```

The arithmetic `(n+1)/2` and `(n+2)/2` automatically expand to one row when odd and two rows when even, no `CASE` needed.

For `PERCENTILE_CONT(0.5)` on dept 2:
```
n=4, sorted [100000, 120000, 140000, 160000]
position = 0.5 * (n-1) = 1.5  (0-indexed)
interpolate between index 1 (120000) and index 2 (140000):
  fraction = 1.5 - floor(1.5) = 0.5
  value = 120000 + 0.5 * (140000 - 120000) = 130000.  ✓
```

For `PERCENTILE_DISC(0.5)` on dept 2:
```
Cumulative distribution:
  100000 → 0.25
  120000 → 0.50    ← smallest CDF value >= 0.5
  140000 → 0.75
  160000 → 1.00
Returns 120000.
```

## How to think aloud in the interview

> "Median per group. The modern answer in Postgres or any SQL:2003-compatible engine is the ordered-set aggregate: `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median`, grouped by `department_id`. That handles odd and even counts cleanly — for an even count it interpolates between the two middle values.
>
> I want to flag one distinction: `PERCENTILE_CONT` interpolates and may return a value not in the data; `PERCENTILE_DISC` returns an actual data value. For salary I want `CONT`; for something like 'median product rating' I might want `DISC` since rating values are discrete.
>
> If the database doesn't have these — older MySQL, certain distributed engines — I use the manual trick: `ROW_NUMBER` within partition ordered by the metric, `COUNT` over the partition as `n`, then filter rows where `rn IN ((n+1)/2, (n+2)/2)` and average. The arithmetic automatically gives one middle row for odd n and two for even, no `CASE` needed.
>
> Edge cases: filter NULLs explicitly. Ties at the median are fine for both forms. And remind myself that `AVG` is not median — easy slip under time pressure."

## Important takeaways

- **`AVG` ≠ median.** Different statistics; different outlier sensitivity.
- **Modern idiom:** `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY x)`.
- **`PERCENTILE_CONT` interpolates** (returns a value not in the data) for even counts.
- **`PERCENTILE_DISC` picks** an existing data value.
- **Manual trick:** `ROW_NUMBER` + `COUNT` + `WHERE rn IN ((n+1)/2, (n+2)/2)` + `AVG`. Works everywhere with window functions.
- **`(n+1)/2, (n+2)/2`** is the parity-free way to pick 1 or 2 middle rows.
- **Filter NULLs** — `PERCENTILE_*` does this automatically; manual trick should do it explicitly.

## Variants

1. **p95 latency** — same shape, `PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)`. Manual: `WHERE rn = CEIL(0.95 * n)`.
2. **Weighted median** — each row carries a weight; need to compute cumulative weight per row and find where cumulative crosses 50%. Pure window function: `SUM(weight) OVER (ORDER BY value)` + filter at the crossover.
3. **Median across multiple metrics** — call `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY x)` once per column; cheap if the planner reads the table once.
4. **Median with grouping by date bucket** — `GROUP BY date_trunc('hour', ts), service` to compute hourly medians.
5. **`MEDIAN()` function** — works in Oracle, Snowflake, BigQuery, Redshift; not in Postgres or MySQL.
6. **Approximate median** — `t-digest` extensions (Postgres has the `tdigest` extension, BigQuery has `APPROX_QUANTILES`). Worth O(log n) per insert vs O(n log n) per query. Useful for billions of rows.
7. **Streaming median** — heap-based DSA problem (two heaps), unrelated to SQL but the interviewer may ask for it as a follow-up.

## Revision notes

> **median-via-window — 60 second recap**
> - `AVG` is the mean, not the median. Don't confuse.
> - Modern: `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY x)` per group.
> - **CONT interpolates** (new value); **DISC picks** an existing value.
> - Manual: `ROW_NUMBER` + `COUNT` + `WHERE rn IN ((n+1)/2, (n+2)/2)` + `AVG`. Parity-free.
> - Even count → two middle rows averaged.
> - Filter NULLs explicitly in the manual version.
> - Approximate: `tdigest`/`APPROX_QUANTILES` for billions of rows.
> - Streaming: two-heap DSA — different problem, not SQL.
