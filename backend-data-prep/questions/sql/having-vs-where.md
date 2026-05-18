# HAVING vs WHERE — When Each Filters

## Source / Origin
- Universal SQL screen warm-up. LeetCode #182, #511, #586 all stress this.
- Real prod: every "users with > N orders" report, every fraud query.

## Why this question matters in interviews
HAVING vs WHERE is the **fastest way for an interviewer to test logical execution order**. The question looks elementary — until they ask "is `WHERE COUNT(*) > 5` legal?" and watch what you do. Get it wrong and they conclude you don't understand SQL's evaluation pipeline at all.

The skill being tested is: can you separate **row-level predicates** (WHERE — applied before grouping) from **group-level predicates** (HAVING — applied after grouping)? Many candidates also miss the **performance** angle: a WHERE filter that could have run before GROUP BY but was wrongly placed in HAVING reads N× more data.

## Concepts involved

### Syntax to lock in
```sql
-- WHERE filters BEFORE grouping; HAVING filters AFTER.
SELECT department, COUNT(*) AS headcount, AVG(salary) AS avg_sal
FROM   employees
WHERE  is_active = TRUE           -- per-row; cuts input rows
GROUP  BY department
HAVING COUNT(*) > 5               -- per-group; cuts groups
   AND AVG(salary) > 50000;       -- per-group aggregate test
```

### Edge cases / interview traps
1. **`WHERE COUNT(*) > 5` is a syntax error.** Aggregates don't exist yet at the WHERE stage.
2. **`HAVING is_active = TRUE` is legal but wasteful.** Postgres will sometimes push it down, but you should never rely on it.
3. **You can use HAVING without GROUP BY.** `SELECT COUNT(*) FROM t HAVING COUNT(*) > 100` returns 0 or 1 row depending on the predicate — implicit single-group aggregation.
4. **HAVING can reference SELECT aliases** in MySQL but not in standard SQL / Postgres. Repeat the expression: `HAVING SUM(amount) > 1000`, not `HAVING total > 1000`.
5. **HAVING evaluates on grouped rows;** if a column isn't in GROUP BY and isn't aggregated, it's an error.
6. **NULLs in HAVING aggregates** — `COUNT(*)` counts everything; `COUNT(col)` ignores NULLs; `AVG`/`SUM` ignore NULLs. Pick wisely.
7. **The "filter on aggregate of filtered subset" trap.** "Users whose first-purchase total > $100" is *not* `HAVING SUM(amount) > 100`; you need `MIN(amount) FILTER (WHERE ...)` or a derived table.
8. **HAVING on window functions** — illegal. Window functions evaluate later than HAVING; wrap in a subquery and filter outside.

## Mental Model

```
   ┌──────────┐  WHERE   ┌──────────┐  GROUP BY  ┌──────────┐  HAVING  ┌──────────┐
   │   rows   │ ───────→ │  filtered│ ─────────→ │  groups  │ ───────→ │  groups  │
   │   (raw)  │   row    │   rows   │  collapse  │ (1 per  │   group  │  (filtered│
   └──────────┘  filter  └──────────┘            │  key)    │  filter  │   groups)│
                                                  └──────────┘          └──────────┘
                                                                              │
                                                                              ▼
                                                                          SELECT
                                                                          ORDER BY
                                                                          LIMIT
```

WHERE = "should this *row* be in the input?". HAVING = "should this *group* be in the output?".

## Why interviewers care
- Tests **logical execution order** — the single most predictive SQL fundamental.
- Tests **performance instinct** — putting row filters in HAVING wastes the GROUP BY.
- Reveals whether the candidate uses HAVING correctly (only for aggregate predicates) or sprays it everywhere (a common smell).

## Common beginner confusion
- "I can use either" — no, you can't put aggregates in WHERE.
- "HAVING is just WHERE for GROUP BY" — wrong; HAVING is **for aggregates**. Row filters belong in WHERE.
- "If both are legal, do I get the same plan?" — usually yes thanks to predicate pushdown, but never bet on it.
- "I need GROUP BY to use HAVING" — no, HAVING without GROUP BY filters the implicit single group.

## Brute force approach
A subquery that aggregates first, outer query that filters. Works for everything but verbose:
```sql
SELECT * FROM (
  SELECT department, COUNT(*) AS c, AVG(salary) AS a FROM employees GROUP BY department
) t WHERE t.c > 5 AND t.a > 50000;
```
Functionally equivalent to HAVING — and identical in plan after the planner unwraps it.

## Optimal approach
Use WHERE for per-row predicates (the planner can push them into the scan, often using an index). Use HAVING for predicates that reference aggregates. Don't mix.

## Solution (SQL)

```sql
CREATE TABLE employees (
  id INT, name TEXT, department TEXT, salary INT, is_active BOOL
);
INSERT INTO employees VALUES
 (1,'Alice','eng',150000,TRUE),(2,'Bob','eng',90000,TRUE),(3,'Carol','eng',120000,FALSE),
 (4,'Dave','eng',95000,TRUE),(5,'Eve','eng',85000,TRUE),(6,'Frank','eng',110000,TRUE),
 (7,'Grace','sales',75000,TRUE),(8,'Henry','sales',60000,TRUE);
```

```sql
-- "Active engineering-ish departments with >5 active employees and avg salary > 90k"
SELECT department,
       COUNT(*)        AS headcount,
       AVG(salary)::int AS avg_sal
FROM   employees
WHERE  is_active = TRUE         -- per-row: drops Carol before grouping
GROUP  BY department
HAVING COUNT(*) > 4             -- per-group: drops 'sales' (only 2 active)
   AND AVG(salary) > 90000;     -- per-group aggregate
-- Output: eng | 5 | 106000   (Alice+Bob+Dave+Eve+Frank)
```

## Step-by-step dry run

```
Step 1 (FROM):     read 8 employees.
Step 2 (WHERE):    is_active=TRUE → drops Carol → 7 rows.
Step 3 (GROUP BY): bucket by department → eng={A,B,D,E,F} (5), sales={G,H} (2).
Step 4 (HAVING):   COUNT(*)>4 keeps eng, drops sales. AVG(sal)>90k → eng's avg=106k ✓.
Step 5 (SELECT):   emit eng | 5 | 106000.
```

If you mistakenly write `HAVING is_active = TRUE` instead of WHERE, Postgres may push it down (because `is_active` is in GROUP BY scope only if you also added it there). Without it in GROUP BY: error "column must appear in GROUP BY or aggregate". You either get a wrong plan or a syntax error — but never "silently wrong results" for this particular slip.

## How to think aloud in the interview
1. *"Row-level filter (`is_active`) goes in WHERE — it runs before grouping and the planner can push it down to the index."*
2. *"Aggregate-level filter (`COUNT(*) > 4`, `AVG(salary) > 90000`) goes in HAVING — these don't exist until after GROUP BY runs."*
3. *"If I tried `WHERE COUNT(*) > 4`, it'd be a syntax error. SQL's execution order is FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT."*
4. *"As a sanity check, I'll think about row counts at each step: 8 → 7 (WHERE) → 2 groups → 1 group (HAVING)."*
5. *"Performance: cramming `is_active` into HAVING would still group all rows first, wasting the filter. Keep WHERE for row filters."*

## Important takeaways
- **WHERE filters rows; HAVING filters groups.**
- Aggregates (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`) only exist *after* GROUP BY → can only be referenced in HAVING (and SELECT/ORDER BY of the same query level).
- Standard SQL doesn't let HAVING use SELECT aliases (MySQL does). Repeat the expression.
- HAVING without GROUP BY filters the implicit single-group result.
- Cross-reference: `01-sql-fundamentals.md` "Execution order" diagram.

## Variants
1. **Window function "having".** Wrap in subquery: `SELECT * FROM (SELECT *, RANK() OVER (...) r FROM t) x WHERE r <= 3`.
2. **`FILTER (WHERE ...)` per-aggregate.** "Active count and total count in one row" → `COUNT(*) FILTER (WHERE is_active), COUNT(*)`. Postgres + standard SQL.
3. **`QUALIFY` clause.** BigQuery / Snowflake / Teradata have `QUALIFY` for window-function filters — same idea as HAVING but for windows.

## Revision notes

> **WHERE vs HAVING cram block**
> - WHERE  = row-level, **before** GROUP BY, no aggregates.
> - HAVING = group-level, **after** GROUP BY, aggregates allowed.
> - Execution: FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT.
> - `WHERE COUNT(*) > 5` = syntax error.
> - HAVING without GROUP BY = filter the implicit single group.
> - Standard SQL forbids HAVING with SELECT aliases; MySQL allows.
> - Performance: row filters in WHERE → planner can push to index. Same predicate in HAVING → wasted GROUP BY work.
> - Window-function "having" → subquery + WHERE outside (or `QUALIFY` in BQ/Snowflake).
