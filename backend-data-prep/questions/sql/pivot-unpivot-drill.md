# Pivot / Unpivot — Long-to-Wide and Back

## Source / Origin
- Classic BI / analytics interview. LeetCode #1179 "Reformat Department Table".
- Stratascratch "build a daily revenue pivot by region".
- Real prod: building dashboard data, exporting CSV reports.

## Why this question matters in interviews
Pivoting (long → wide) and unpivoting (wide → long) come up every time someone exports a report. The SQL-standard way uses `FILTER (WHERE ...)` aggregates, which most candidates have never written. Dialect-specific operators (`PIVOT`/`UNPIVOT` in SQL Server, `crosstab` in Postgres extension) are also fair game.

The interviewer wants to see (1) the **conditional-aggregate idiom** (the universal pivot), (2) recognition that pivot column names must be known in advance (no truly dynamic pivot in pure SQL), and (3) unpivot via `UNION ALL` or `unnest(ARRAY)`.

## Concepts involved

### Syntax to lock in
```sql
-- LONG (input):
-- region | quarter | revenue
-- east   | Q1      | 100
-- east   | Q2      | 150
-- west   | Q1      | 80

-- PIVOT to wide (portable, standard SQL):
SELECT region,
  SUM(revenue) FILTER (WHERE quarter='Q1') AS q1,
  SUM(revenue) FILTER (WHERE quarter='Q2') AS q2,
  SUM(revenue) FILTER (WHERE quarter='Q3') AS q3,
  SUM(revenue) FILTER (WHERE quarter='Q4') AS q4
FROM sales
GROUP BY region;

-- Pre-`FILTER` (works in MySQL):
SELECT region,
  SUM(CASE WHEN quarter='Q1' THEN revenue END) AS q1,
  SUM(CASE WHEN quarter='Q2' THEN revenue END) AS q2,
  ...
FROM sales
GROUP BY region;

-- UNPIVOT (wide → long) via UNION ALL:
SELECT region, 'Q1' AS quarter, q1 AS revenue FROM wide
UNION ALL SELECT region, 'Q2', q2 FROM wide
UNION ALL SELECT region, 'Q3', q3 FROM wide
UNION ALL SELECT region, 'Q4', q4 FROM wide;

-- Postgres: unpivot via VALUES + LATERAL
SELECT region, q, rev
FROM wide
CROSS JOIN LATERAL (VALUES ('Q1',q1),('Q2',q2),('Q3',q3),('Q4',q4)) AS u(q, rev);
```

### Edge cases / interview traps
1. **Pivot column list must be hardcoded.** Postgres doesn't support truly dynamic pivot (column names known only at query time) without PL/pgSQL or `crosstabN`.
2. **`FILTER (WHERE ...)`** is standard SQL but unavailable in older MySQL — fall back to `SUM(CASE WHEN ... THEN x END)`.
3. **Missing combinations.** If region X has no Q3 row, the pivoted `q3` cell is NULL (or 0 if you `COALESCE`). Decide which.
4. **Pivot with multiple aggregates.** Want sum AND count? Two columns per pivot value — quickly unwieldy.
5. **SQL Server `PIVOT` syntax** is its own DSL: `SELECT ... FROM source PIVOT (SUM(rev) FOR quarter IN ([Q1],[Q2])) p`. Quoted identifiers because column names start with a digit.
6. **Postgres `crosstab` extension** (`tablefunc`) is fast but requires same column types and a deterministic categories list.
7. **Unpivot preserves NULLs.** If `q3` is NULL in source, the long-form row has NULL revenue — often dropped via `WHERE revenue IS NOT NULL`.
8. **Performance:** pivots are one pass + GROUP BY. Unpivots via `UNION ALL` scan N times; via LATERAL VALUES scan once.

## Mental Model

```
   LONG ←→ WIDE rotation:

   long:                    wide:                       Rotate 90° via:
   region quarter rev       region  q1  q2  q3  q4        SUM(rev) FILTER (WHERE quarter=...)
   ───── ─────── ───        ───── ─── ─── ─── ───
   east   Q1     100        east   100 150  ?   ?
   east   Q2     150        west    80  ?   ?   ?
   west   Q1      80
                            ← UNPIVOT via UNION ALL or LATERAL VALUES
```

Pivot is **conditional aggregation**: for each group, pick which rows feed each output cell. Unpivot is **row expansion**: each column in a wide row becomes its own row.

## Why interviewers care
- Reporting / BI work needs this every day; tests practical SQL.
- `FILTER` idiom is a senior signal — junior candidates default to `CASE WHEN`.
- Identifies whether candidate knows the limits (no dynamic pivot in pure SQL).

## Common beginner confusion
- "I'll use a stored proc to generate dynamic columns" — possible but not pure SQL.
- "FILTER and CASE WHEN are different" — they aren't, semantically; `FILTER` is just cleaner standard syntax.
- "Pivot can produce more rows" — no, pivot reduces rows (rows → columns).
- "Unpivot keeps wide row's PK" — yes, but you get one row per unpivoted column.

## Brute force approach
Self-join the source N times, one per pivot category. Works but explodes for wide pivots (12 months × 4 metrics = 48 self-joins).

## Optimal approach
One pass with `GROUP BY` + `FILTER (WHERE ...)` aggregates. Each pivot column is just another aggregate alongside the group key. For unpivot, prefer LATERAL VALUES over N-way UNION ALL (one scan vs N).

## Solution (SQL)

```sql
CREATE TABLE sales (
  region   TEXT,
  quarter  TEXT,
  revenue  NUMERIC
);
INSERT INTO sales VALUES
 ('east','Q1',100),('east','Q2',150),('east','Q3',120),('east','Q4',90),
 ('west','Q1', 80),('west','Q2',110),('west','Q3', 95),('west','Q4',70);
```

```sql
-- PIVOT: revenue per region × quarter
SELECT region,
  COALESCE(SUM(revenue) FILTER (WHERE quarter='Q1'), 0) AS q1,
  COALESCE(SUM(revenue) FILTER (WHERE quarter='Q2'), 0) AS q2,
  COALESCE(SUM(revenue) FILTER (WHERE quarter='Q3'), 0) AS q3,
  COALESCE(SUM(revenue) FILTER (WHERE quarter='Q4'), 0) AS q4,
  SUM(revenue)                                          AS year_total
FROM sales
GROUP BY region;

/* Output:
 region | q1  | q2  | q3  | q4 | year_total
────────┼─────┼─────┼─────┼────┼────────────
 east   | 100 | 150 | 120 | 90 |     460
 west   |  80 | 110 |  95 | 70 |     355
*/

-- UNPIVOT back: one row per (region, quarter)
WITH wide AS (
  SELECT * FROM (
    -- imagine this is the wide table
    VALUES ('east',100,150,120,90), ('west',80,110,95,70)
  ) v(region, q1, q2, q3, q4)
)
SELECT region, q, revenue
FROM   wide
CROSS  JOIN LATERAL (
  VALUES ('Q1',q1),('Q2',q2),('Q3',q3),('Q4',q4)
) AS u(q, revenue)
ORDER BY region, q;
```

## Step-by-step dry run

Pivot:
```
GROUP BY region:
  east group (4 rows):
    sum filter Q1: only row with Q1 contributes → 100.
    sum filter Q2: → 150.
    sum filter Q3: → 120.
    sum filter Q4: → 90.
    sum total:     → 460.
  west group: same logic → 80, 110, 95, 70, 355.
```

Unpivot (LATERAL VALUES):
```
For each row of wide (2 rows), produce 4 child rows via the VALUES tuple.
Output: 8 rows: (east,Q1,100), (east,Q2,150), ..., (west,Q4,70).
```

## How to think aloud in the interview
1. *"Long-to-wide is the conditional-aggregate idiom: `GROUP BY region`, then one `SUM(...) FILTER (WHERE quarter=...)` per output column."*
2. *"I use FILTER over `CASE WHEN` because it's standard SQL and reads cleaner. MySQL pre-8 needs `CASE WHEN`."*
3. *"Column names must be hardcoded — there's no truly dynamic pivot in pure SQL. For dynamic, generate the SQL in the app layer."*
4. *"Missing pivot cells default to NULL — I'll `COALESCE` to 0 if the dashboard wants zeroes."*
5. *"For unpivot, LATERAL VALUES gives me one pass; UNION ALL would scan the wide table N times."*

## Important takeaways
- Pivot = `GROUP BY` + `FILTER` aggregates (or `CASE WHEN` pre-FILTER).
- Pivot columns are static — dynamic pivot needs app-layer codegen.
- Unpivot via LATERAL VALUES (one scan) or UNION ALL (N scans).
- SQL Server has a dedicated `PIVOT`/`UNPIVOT` DSL.
- Postgres `crosstab` (tablefunc) is the fast path at scale.
- See `backend-data-prep/sql/02-advanced-sql.md` "Pivot/Unpivot".

## Variants
1. **Pivot with multiple aggregates per category.** Two output columns per quarter (sum and count). Use two FILTER aggregates per quarter or pivot twice and join.
2. **Heatmap data.** Pivot day-of-week × hour-of-day for traffic heatmap. 7 × 24 = 168 columns — usually keep long and let app pivot.
3. **`tablefunc.crosstab` in Postgres** — `SELECT * FROM crosstab('select ...') AS ct(region text, q1 numeric, ...)`. Faster but stricter input contract.

## Revision notes

> **Pivot/Unpivot cram block**
> - Pivot (long→wide): `GROUP BY key, SUM(x) FILTER (WHERE cat='A') AS col_a, ...`.
> - Pre-FILTER fallback: `SUM(CASE WHEN cat='A' THEN x END)`.
> - Pivot columns are **static**; no pure-SQL dynamic pivot.
> - Missing cells = NULL; `COALESCE(..., 0)` if you want zeros.
> - Unpivot (wide→long): `CROSS JOIN LATERAL (VALUES (...))` — one scan.
> - SQL Server: dedicated `PIVOT (agg FOR col IN (...))` DSL.
> - Postgres: `tablefunc.crosstab` for performance.
> - Pivot reduces rows; unpivot expands rows.
