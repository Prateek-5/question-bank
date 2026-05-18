# GROUP BY with GROUPING SETS, ROLLUP, CUBE

## Source / Origin
- Postgres / SQL Server / Oracle / BigQuery — all support; MySQL has ROLLUP only.
- Classic OLAP / data-warehouse interview problem at Amazon, Microsoft, Walmart Labs.
- Real prod: "give me revenue by region, by product, by region+product, AND the grand total — in one query".

## Why this question matters in interviews
This question is the **shibboleth for data-warehouse / BI engineers**. Most candidates know `GROUP BY a, b`, fewer know you can produce multiple grouping levels in one pass with `ROLLUP`, `CUBE`, or `GROUPING SETS`. Without these, candidates write **N separate queries** joined by `UNION ALL` — correct but reads 10× as much data.

Interviewers want to see whether you've ever built a report layer. They're also probing your understanding of the **GROUPING() function** and how NULL is overloaded to mean "all values aggregated here" in rollup output.

## Concepts involved

### Syntax to lock in
```sql
-- Plain GROUP BY: one row per (region, product) pair
SELECT region, product, SUM(amount) FROM sales GROUP BY region, product;

-- GROUPING SETS: explicit list of grouping levels
SELECT region, product, SUM(amount) FROM sales
GROUP BY GROUPING SETS ((region, product), (region), (product), ());

-- ROLLUP: hierarchical totals from finest → grand total
SELECT region, product, SUM(amount) FROM sales
GROUP BY ROLLUP (region, product);
-- Produces: (region, product), (region), () ← grand total. Drops "product alone".

-- CUBE: every subset of the grouping columns (2^N levels)
SELECT region, product, SUM(amount) FROM sales
GROUP BY CUBE (region, product);
-- Produces: (region, product), (region), (product), ()

-- GROUPING() to distinguish "NULL value" from "aggregated-here NULL"
SELECT
  CASE WHEN GROUPING(region)=1 THEN 'ALL' ELSE region END AS region,
  SUM(amount)
FROM sales
GROUP BY ROLLUP(region);
```

### Edge cases / interview traps
1. **NULL ambiguity in output.** ROLLUP/CUBE emit NULL in columns that were "rolled up". If the data itself contains NULL, you can't tell them apart without `GROUPING()`.
2. **`GROUPING()` returns 0 or 1.** Use in `CASE` to label totals. Some engines also support `GROUPING_ID()` for bitmaps.
3. **Order matters in ROLLUP.** `ROLLUP(a,b)` gives `(a,b), (a), ()`. `ROLLUP(b,a)` gives `(b,a), (b), ()`. Different shapes.
4. **CUBE is `2^N` rows per group combination.** With 5 columns that's 32 rollup levels — expensive.
5. **MySQL syntax oddity.** Pre-8.0: `GROUP BY ... WITH ROLLUP` (suffix, not function). MySQL 8.0+: standard `ROLLUP(...)` syntax also works.
6. **ORDER BY with rollup.** Total rows have NULL in their group columns, so they sort first (or last) depending on dialect. `ORDER BY GROUPING(col), col` to push totals to the end.
7. **`HAVING` and rollup interact.** `HAVING SUM(amount) > X` will filter total rows too if not careful.
8. **Aggregate functions over the rollup row** behave as if grouped at that level — `COUNT(*)` at the grand-total row is total rows.

## Mental Model

```
 sales:  region   product   amount
 ─────   ──────   ───────   ──────
         east     widget    100
         east     gadget     50
         west     widget     80
         west     gadget     20

 GROUP BY ROLLUP(region, product) produces a *pyramid*:

     LEVEL 0 (finest):  (east,widget,100) (east,gadget,50) (west,widget,80) (west,gadget,20)
     LEVEL 1 (rollup):  (east,NULL,150)              (west,NULL,100)
     LEVEL 2 (top):                          (NULL,NULL,250)

 CUBE adds the "by product alone" tier too:
                                 (NULL,widget,180)  (NULL,gadget,70)
```

GROUPING SETS lets you pick **exactly** which levels you want — ROLLUP and CUBE are syntactic shortcuts for common patterns.

## Why interviewers care
- BI / analytics teams write rollup queries every day. This question filters in real warehouse experience.
- Tests **understanding of NULL semantics in aggregation** (the overloaded NULL trap).
- Probes **query consolidation skill** — one rollup query vs N UNIONed queries.

## Common beginner confusion
- "I'll just UNION ALL 4 queries" — works, but reads the table 4×. Rollup reads once.
- "NULL means missing data" — in rollup output, NULL means "all values aggregated at this column".
- "ROLLUP and CUBE are the same" — no; CUBE is *every* subset, ROLLUP is the *prefix* hierarchy.
- "GROUPING_ID is the same as GROUPING" — `GROUPING(col)` returns 0/1 for one column; `GROUPING_ID(a,b,c)` returns the bitmap as an integer.

## Brute force approach
```sql
SELECT region, product, SUM(amount) FROM sales GROUP BY region, product
UNION ALL
SELECT region, NULL,    SUM(amount) FROM sales GROUP BY region
UNION ALL
SELECT NULL,   product, SUM(amount) FROM sales GROUP BY product
UNION ALL
SELECT NULL,   NULL,    SUM(amount) FROM sales;
```
Four passes over `sales`. Correct, ugly, expensive.

## Optimal approach
One pass with `GROUPING SETS`, `ROLLUP`, or `CUBE`. The planner sorts/hashes once and emits all grouping levels from the same scan.

## Solution (SQL)

```sql
CREATE TABLE sales (region TEXT, product TEXT, amount NUMERIC);
INSERT INTO sales VALUES
 ('east','widget',100),('east','gadget',50),
 ('west','widget',80), ('west','gadget',20);
```

```sql
-- Rollup with labeled totals
SELECT
  COALESCE(region,  '— ALL —')  AS region,
  COALESCE(product, '— ALL —')  AS product,
  SUM(amount)                   AS revenue,
  GROUPING(region)              AS grp_region,   -- 1 = rolled up
  GROUPING(product)             AS grp_product
FROM   sales
GROUP  BY ROLLUP (region, product)
ORDER  BY GROUPING(region), region,
          GROUPING(product), product;

/* Output:
 region  | product | revenue | grp_region | grp_product
─────────┼─────────┼─────────┼────────────┼────────────
 east    | gadget  |   50    |     0      |     0
 east    | widget  |  100    |     0      |     0
 east    | —ALL—   |  150    |     0      |     1
 west    | gadget  |   20    |     0      |     0
 west    | widget  |   80    |     0      |     0
 west    | —ALL—   |  100    |     0      |     1
 —ALL—   | —ALL—   |  250    |     1      |     1
*/
```

## Step-by-step dry run

The planner sorts by `(region, product)` once. As it scans:

```
Group (east,gadget):   emit row, accumulate east-total=50, grand=50
Group (east,widget):   emit row, east-total=150, grand=150
End of east region:    emit (east, NULL, 150)
Group (west,gadget):   emit row, west-total=20, grand=170
Group (west,widget):   emit row, west-total=100, grand=250
End of west region:    emit (west, NULL, 100)
End of input:          emit (NULL, NULL, 250)
```

One pass, three "tiers" of output. With CUBE, the planner does an extra pass (or multiple hash buckets) to compute the by-product-alone tier too.

## How to think aloud in the interview
1. *"They want multiple aggregation levels in one result. Default to GROUPING SETS for explicit control, or ROLLUP for hierarchical totals."*
2. *"Output will contain NULL in the rolled-up columns — I'll use `GROUPING()` to label them and avoid confusing them with actual NULL data."*
3. *"This compiles to one pass with a sort or hash, vs N UNIONed queries that each scan the whole table."*
4. *"For ordering, `ORDER BY GROUPING(col), col` puts the totals where the consumer expects them."*
5. *"If the dataset is huge and many rollup levels are needed, materialize the daily fine-grained aggregate first and roll up from there."*

## Important takeaways
- Three flavours: **GROUPING SETS** (explicit), **ROLLUP** (hierarchical prefix), **CUBE** (every subset).
- NULL in rollup rows is **overloaded** — use `GROUPING()` to disambiguate.
- One pass replaces N UNIONed queries.
- MySQL has `WITH ROLLUP` suffix syntax (and standard syntax in 8.0+).
- See `backend-data-prep/sql/02-advanced-sql.md` "Aggregations" for theory.

## Variants
1. **`GROUPING_ID()`** returns a bitmap so you can `ORDER BY` the rollup level numerically.
2. **`FILTER (WHERE ...)` per aggregate** — fine-grained conditional aggregation alongside rollup.
3. **Materialized rollup table** — store rollup output in its own table for fast dashboard reads; refresh nightly.

## Revision notes

> **ROLLUP/CUBE/GROUPING SETS cram block**
> - **GROUPING SETS** `((a,b),(a),())` — explicit list of levels.
> - **ROLLUP(a,b)** — `(a,b),(a),()`. Hierarchical prefix.
> - **CUBE(a,b)** — every subset: `(a,b),(a),(b),()`. 2^N rows.
> - Rolled-up columns appear as **NULL** — overloaded!
> - `GROUPING(col)` → 0/1 to tell rollup-NULL from data-NULL.
> - `GROUPING_ID(a,b,c)` → integer bitmap.
> - MySQL: `GROUP BY ... WITH ROLLUP` (pre-8.0) or standard syntax (8.0+). No CUBE.
> - One pass beats N UNIONs.
> - `ORDER BY GROUPING(col), col` for clean totals placement.
