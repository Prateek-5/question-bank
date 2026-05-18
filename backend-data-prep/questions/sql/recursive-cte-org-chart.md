# Recursive CTE — Org Chart, BOM Explosion

## Source / Origin
- LeetCode #571 (indirectly), interview-query "find all reports under a manager".
- Real prod: manufacturing BOM explosion, friend-of-friend traversal, threaded comments.

## Why this question matters in interviews
A recursive CTE is the **SQL answer to graph traversal**. The interviewer wants to see: (1) can you express a fixed-point computation declaratively? (2) Do you remember the **anchor + recursive** two-part skeleton? (3) Do you guard against **infinite cycles** in real data?

It's also a senior-vs-mid discriminator. Junior candidates either don't know recursive CTEs exist or write them with subtle infinite loops. Senior candidates produce one with explicit cycle detection and bounded depth.

## Concepts involved

### Syntax to lock in
```sql
WITH RECURSIVE chart AS (
  -- ANCHOR: starting set
  SELECT id, name, mgr_id, 0 AS depth, ARRAY[id] AS path
  FROM   emp
  WHERE  mgr_id IS NULL                 -- root rows
  UNION ALL
  -- RECURSIVE: each iteration adds one more level
  SELECT e.id, e.name, e.mgr_id, c.depth + 1, c.path || e.id
  FROM   emp e
  JOIN   chart c ON e.mgr_id = c.id
  WHERE  NOT e.id = ANY(c.path)          -- cycle guard
)
SELECT * FROM chart ORDER BY depth, id;
```

### Edge cases / interview traps
1. **Forgetting `RECURSIVE`** — `WITH chart AS` without the keyword in Postgres → "table not found" error referring to `chart` inside itself.
2. **Cycle in the data.** If A reports to B and B reports to A (bad data), the recursion never terminates. Always carry a `path` array and check `NOT e.id = ANY(path)`.
3. **`UNION` vs `UNION ALL`.** Use `UNION ALL` for performance; only switch to `UNION` for explicit dedup (which `path` guard already gives you).
4. **No `ORDER BY` inside the recursive term.** Recursion is breadth-first by default; ordering happens in the final SELECT.
5. **Termination depends on the anchor + recursive joining to a strictly smaller set.** If your recursive join can keep producing rows, you have a bug.
6. **MySQL recursive CTEs** arrived in 8.0; before that, no native recursion.
7. **`SEARCH BREADTH/DEPTH FIRST` clause** (Postgres 14+) provides traversal-order control; useful for nested-comment threading.
8. **Performance:** each iteration is a join with `chart`. For deep hierarchies, this is `O(depth × |emp|)`. Index the join column (`mgr_id`).

## Mental Model

```
   emp:  id  name    mgr_id           Build chart iteratively:
   ───   ──  ──────  ──────
          1  CEO     NULL              ITER 0 (anchor):  {CEO}
          2  VP-Eng    1                ITER 1:  + {VP-Eng, VP-Sales}
          3  VP-Sales  1                ITER 2:  + {EM, Lead}
          4  EM        2                ITER 3:  + {SDE-1}
          5  Lead      3                ITER 4:  no new rows → STOP
          6  SDE-1     4
```

A recursive CTE is **fixed-point iteration**: start with a seed set (anchor), repeatedly apply a rule that adds rows derived from the current set, stop when the rule produces zero new rows.

## Why interviewers care
- Recursion in a declarative language is the **last frontier** of SQL skill.
- Tests **cycle awareness** — real prod data is messy.
- Probes whether candidate can sketch a termination argument (every iteration reduces a measure).

## Common beginner confusion
- "I need to know the depth ahead of time" — no, the recursion terminates when no new rows appear.
- "I'll just keep recursing forever" — without `UNION ALL` deduplication or a path guard, cycles cause infinite loops.
- "Recursive CTE = recursive function call" — no, no stack growth, no language-level recursion; just iteration.
- "MySQL has recursive CTEs" — only 8.0+.

## Brute force approach
Application-side traversal: fetch all employees, build the adjacency map, BFS in app code. Works for small datasets but forces a full table fetch and round-trip count proportional to levels.

Or: hard-code N self-joins for up to N levels:
```sql
SELECT e1.name lvl0, e2.name lvl1, e3.name lvl2
FROM emp e1 LEFT JOIN emp e2 ON e2.mgr_id = e1.id
            LEFT JOIN emp e3 ON e3.mgr_id = e2.id
WHERE e1.mgr_id IS NULL;
```
Works only if you know max depth. Brittle.

## Optimal approach
Recursive CTE with anchor + recursive + cycle-guard. Index `mgr_id`. Bounded depth with `WHERE depth < 20` as belt-and-suspenders.

## Solution (SQL)

```sql
CREATE TABLE emp (
  id     INT PRIMARY KEY,
  name   TEXT,
  mgr_id INT REFERENCES emp(id)
);
CREATE INDEX ix_emp_mgr ON emp(mgr_id);

INSERT INTO emp VALUES
 (1,'CEO',NULL),(2,'VP-Eng',1),(3,'VP-Sales',1),
 (4,'EM',2),(5,'Lead',3),(6,'SDE-1',4);
```

```sql
-- All reports below CEO, with depth and path
WITH RECURSIVE chart AS (
  SELECT id, name, mgr_id,
         0                AS depth,
         ARRAY[id]        AS path,
         name             AS chain
  FROM   emp
  WHERE  mgr_id IS NULL                          -- anchor: roots
  UNION ALL
  SELECT e.id, e.name, e.mgr_id,
         c.depth + 1,
         c.path || e.id,
         c.chain || ' > ' || e.name
  FROM   emp e
  JOIN   chart c ON e.mgr_id = c.id
  WHERE  NOT e.id = ANY(c.path)                  -- cycle guard
    AND  c.depth < 20                            -- depth guard
)
SELECT depth, chain FROM chart ORDER BY depth, id;
```

Output:

```
 depth | chain
───────┼───────────────────────────────────
   0   | CEO
   1   | CEO > VP-Eng
   1   | CEO > VP-Sales
   2   | CEO > VP-Eng > EM
   2   | CEO > VP-Sales > Lead
   3   | CEO > VP-Eng > EM > SDE-1
```

## Step-by-step dry run

```
Anchor:        chart = {(1, CEO, NULL, 0)}.
Iter 1:        join emp ON e.mgr_id = c.id.  c.id=1; match: id=2 (VP-Eng), id=3 (VP-Sales).
               Insert (2, VP-Eng, 1, 1), (3, VP-Sales, 1, 1).
Iter 2:        c.id ∈ {2,3}.  Matches: id=4 (mgr=2), id=5 (mgr=3).
               Insert (4, EM, 2, 2), (5, Lead, 3, 2).
Iter 3:        c.id ∈ {4,5}.  Matches: id=6 (mgr=4).
               Insert (6, SDE-1, 4, 3).
Iter 4:        c.id ∈ {6}.  No emp has mgr_id=6 → 0 new rows → STOP.
```

Termination: each iteration produces new chart-rows from a *finite* pool; the unionall result strictly grows; if it stops growing → done. Cycle guard prevents reprocessing in case of bad data.

## How to think aloud in the interview
1. *"This is recursive — depth is unbounded by data. I'll write a `WITH RECURSIVE` CTE."*
2. *"Two parts: anchor (roots — `mgr_id IS NULL`) and recursive (join `emp` to the CTE's previous result on `e.mgr_id = c.id`)."*
3. *"Cycle guard: carry a `path` array and exclude visited ids. Belt-and-suspenders depth cap."*
4. *"`UNION ALL` for performance — duplicates can't occur because of the path guard."*
5. *"Index on `emp.mgr_id` so each iteration's join is O(rows-added × log N) rather than a full scan."*

## Important takeaways
- Two-part skeleton: anchor + recursive, joined with `UNION ALL`.
- Always cycle-guard with a `path` array (`NOT id = ANY(path)`).
- Set a depth cap; production data lies.
- Index the recursive join column.
- See `backend-data-prep/sql/02-advanced-sql.md` "Recursive CTEs" for theory.

## Variants
1. **BOM explosion.** `part(id, name)`, `assembly(parent_id, child_id, qty)`. Compute total quantity of each leaf part needed: recursive CTE multiplying qty along the path.
2. **Threaded comments.** `comments(id, parent_id, text)`. Recursive CTE building the reply tree; use `SEARCH DEPTH FIRST BY ...` for forum-style ordering.
3. **Find common ancestor of two employees.** Build paths from each up to the root, then intersect.

## Revision notes

> **Recursive CTE cram block**
> - `WITH RECURSIVE name AS ( anchor UNION ALL recursive ) SELECT ...`
> - Anchor: starting rows.
> - Recursive: join CTE to base table to extend by one level.
> - **Always** cycle-guard with `path` array.
> - Depth cap belt-and-suspenders: `WHERE c.depth < 20`.
> - `UNION ALL` for speed; `UNION` only if you need set-dedup.
> - Termination: rule produces zero new rows.
> - Index the recursive join column.
> - MySQL ≥ 8.0; pre-8 has no native recursion.
> - Postgres 14+: `SEARCH BREADTH/DEPTH FIRST` for traversal order.
