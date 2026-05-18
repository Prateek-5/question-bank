# Self Join — Employees/Managers, Friend Pairs, Gaps

## Source / Origin
- LeetCode #181 "Employees Earning More Than Their Managers", #197 "Rising Temperature", #1378.
- Stratascratch "Manager chain", "Find pairs of users who are friends both ways".
- Real prod: detecting duplicate orders within N seconds, "did the same IP try two cards in a row", message reply-chains.

## Why this question matters in interviews
A self-join is the standard test for whether you can **see one table as two**. It comes up whenever a row has a relationship with *another row in the same table* — employee→manager, message→reply, today→yesterday, pair-of-friends. Candidates who haven't internalised it reach for procedural loops or imagine you need a second table; both are dead-ends.

It also tests your **aliasing discipline**. Every self-join needs two distinct aliases; mixing them up is the #1 cause of silently wrong results. Interviewers will deliberately give you ambiguous schemas (`emp(id, name, mgr_id)`) and watch whether you carefully label `e` (employee) and `m` (manager).

Finally, it's the gateway to **gaps-and-islands**, **consecutive-day puzzles**, and **graph-pathfinding on a single table** — patterns that come up in fraud, billing, and analytics every week.

## Concepts involved

### Syntax to lock in
```sql
-- Employee with their manager's name
SELECT e.name AS employee, m.name AS manager
FROM   emp e
LEFT   JOIN emp m ON e.mgr_id = m.id;   -- LEFT so CEOs aren't dropped

-- Pairs of employees in the same department, no duplicates
SELECT a.name, b.name
FROM   emp a JOIN emp b
  ON   a.dept_id = b.dept_id
  AND  a.id < b.id;                     -- the < is what kills duplicates + self-pairs

-- "Rising temperature" — today warmer than yesterday
SELECT t.id
FROM   temperatures t
JOIN   temperatures y ON t.recordDate = y.recordDate + INTERVAL '1 day'
WHERE  t.temperature > y.temperature;
```

### Edge cases / interview traps
1. **CEO / root rows dropped.** Using INNER JOIN on `mgr_id` excludes the CEO (their `mgr_id` is NULL). Use LEFT JOIN.
2. **Self-pairs `(a,a)`.** Without `a.id <> b.id`, every row joins with itself. Use `<` (not `<>`) to also kill mirror duplicates.
3. **Symmetric pairs `(a,b)` and `(b,a)`.** Same fix: `a.id < b.id`.
4. **Date arithmetic dialect.** Postgres uses `recordDate + INTERVAL '1 day'`; MySQL `DATE_ADD(recordDate, INTERVAL 1 DAY)`; SQL Server `DATEADD(day, 1, recordDate)`.
5. **Mistaking direction.** `e.mgr_id = m.id` (employee's manager) vs `e.id = m.mgr_id` (employee's reports). Swap and your output flips.
6. **Multi-level chains.** A self-join walks **one** edge. Skip-level manager needs a second self-join or a recursive CTE — see `recursive-cte-org-chart.md`.
7. **NULL join key.** Friend pairs where `friend_id IS NULL` won't match. Use `IS NOT DISTINCT FROM` only if you want NULL=NULL.
8. **Performance.** Self-join on a non-indexed column doubles a sequential scan into an `O(n²)` nested loop. Always index the join column.

## Mental Model

```
   emp:  id   name      mgr_id           Read it as TWO copies of the table:
   ───   ──   ────────  ──────
         1    Alice     NULL              ┌────────────────┐    ┌────────────────┐
         2    Bob       1                 │ e (employee)   │    │ m (manager)    │
         3    Carol     1                 │ id  name  mgr  │    │ id  name       │
         4    Dave      2                 │ 1   Alice NULL │ ⋈  │ 1   Alice      │
                                          │ 2   Bob   1    │    │ 2   Bob        │
                                          │ 3   Carol 1    │    │ 3   Carol      │
                                          │ 4   Dave  2    │    │ 4   Dave       │
                                          └────────────────┘    └────────────────┘

   Join condition: e.mgr_id = m.id
   Output rows:  (Bob, Alice) (Carol, Alice) (Dave, Bob)
```

The table is one set on disk; the query gives it two **names** so two cursors can walk it at once.

## Why interviewers care
Self-join probes **relational thinking**. It's the simplest example of "the same set in two roles". Senior candidates also recognise that a self-join is the **algebraic identity** behind: gap-finding, sequential-row diffing, "next event after this one", co-occurrence pairs. A weak grasp here closes the door on every gaps/islands, sessionisation, and friend-graph question downstream.

## Common beginner confusion
- "Don't I need two tables?" — no. SQL aliases let one table appear twice.
- "Why use LEFT JOIN?" — to keep root rows (CEOs, first messages, customers with no prior order).
- "Why `<` not `<>`?" — `<>` keeps both `(a,b)` and `(b,a)`. `<` keeps only one.
- "Self-join vs recursive CTE?" — self-join = one hop. Recursive CTE = arbitrary depth.

## Brute force approach
Loop in application code: fetch all employees, build a map `id → row`, then for each employee look up `map[e.mgr_id]`. Works, but defeats the database's planner, doubles the round-trips, and falls over at scale. Mention it only to dismiss it.

## Optimal approach
One SQL statement with a self-join. Two aliases (`e`, `m`). LEFT JOIN if the join key is nullable. Index on the FK column for the inner side. O(n) with a hash join, O(n log n) with a merge join, O(n²) only if the planner has nothing to work with.

## Solution (SQL)

Sample data:

```sql
CREATE TABLE emp (
  id      INT PRIMARY KEY,
  name    TEXT,
  salary  INT,
  mgr_id  INT REFERENCES emp(id)
);
INSERT INTO emp VALUES
 (1,'Alice',150000,NULL),
 (2,'Bob',  90000, 1),
 (3,'Carol',120000,1),
 (4,'Dave', 95000, 2),
 (5,'Eve',  80000, 2);
```

Three canonical queries:

```sql
-- 1) Employees earning more than their manager (LeetCode #181)
SELECT e.name AS employee
FROM   emp e
JOIN   emp m ON e.mgr_id = m.id
WHERE  e.salary > m.salary;
-- Output: Dave (95k > Bob 90k)

-- 2) All (employee, manager) pairs including CEO
SELECT e.name AS employee, m.name AS manager
FROM   emp e
LEFT   JOIN emp m ON e.mgr_id = m.id
ORDER  BY e.id;
-- (Alice, NULL) (Bob, Alice) (Carol, Alice) (Dave, Bob) (Eve, Bob)

-- 3) Pairs of employees with the same manager (peer pairs)
SELECT a.name AS emp1, b.name AS emp2, a.mgr_id
FROM   emp a JOIN emp b
  ON   a.mgr_id = b.mgr_id
  AND  a.id < b.id;
-- (Bob, Carol, 1)  (Dave, Eve, 2)
```

## Step-by-step dry run

Query 1, hash-join semantics:

```
Build hash on m.id:        Probe with e.mgr_id:
m: {1:Alice/150k,          e.mgr_id=NULL  -> skip (NULL probe misses)
    2:Bob/90k,             e.mgr_id=1     -> Alice, salary 150k. e.salary=90k? 90>150? no.
    3:Carol/120k,          e.mgr_id=1     -> Alice. Carol 120>150? no.
    4:Dave/95k,            e.mgr_id=2     -> Bob 90k.  Dave 95>90? YES → emit Dave.
    5:Eve/80k}             e.mgr_id=2     -> Bob 90k.  Eve  80>90? no.
```

Output: just `Dave`. The hash join visits each row of `emp` exactly twice (once to build, once to probe) — O(n) with O(n) memory.

## How to think aloud in the interview
1. *"I'll alias the table twice — `e` for the employee, `m` for the manager. The join key is `e.mgr_id = m.id` because each employee carries the FK to their boss."*
2. *"INNER JOIN would drop the CEO whose `mgr_id` is NULL; I'll use LEFT JOIN to keep them with `manager = NULL`."*
3. *"For peer pairs I add `a.id < b.id` to avoid `(a,a)` self-pairs and `(b,a)` mirror duplicates."*
4. *"At scale I'd want an index on `mgr_id` so the join becomes O(n log n) instead of nested-loop quadratic."*
5. *"If the interviewer asks for skip-level — grand-manager — that's a recursive CTE, not another self-join level."*

## Important takeaways
- Two aliases, one table. Always.
- LEFT JOIN to preserve root rows.
- `a.id < b.id` for symmetric-pair de-dup; `a.id <> b.id` for ordered pairs.
- Self-join is one hop only — chain or recurse for more.
- Index the join column or accept a nested loop.

## Variants
1. **Friend-table** `friendship(user_id, friend_id)` stored one-way: find pairs that are friends in both directions. → `JOIN friendship f2 ON f1.user_id = f2.friend_id AND f1.friend_id = f2.user_id WHERE f1.user_id < f1.friend_id`.
2. **Rising temperature** (LeetCode #197). Join on `recordDate = prev_date + 1 day`. Pitfall: missing dates still get matched if data has gaps; consider `LAG()` instead.
3. **Find people whose manager's manager is also their manager** (loops in the org chart). Two-step self-join `e → m1 → m2` and check `m2.id = e.mgr_id`.

## Revision notes

> **Self-join cram block**
> - One table, two aliases.
> - Pattern: `FROM t a JOIN t b ON <relation>`.
> - LEFT JOIN to keep root/orphan rows.
> - `a.id < b.id` to suppress self + mirror pairs.
> - One-hop only — multi-hop needs recursive CTE.
> - Index the join column.
> - Date-adjacency: `prev_date = curr_date - 1` is a self-join, but `LAG()` is usually clearer.
> - Trap: forgetting LEFT JOIN drops CEO; forgetting `a.id<b.id` doubles or self-pairs rows.
> - Family: self-join → gaps-and-islands → recursive CTE → graph traversal.
