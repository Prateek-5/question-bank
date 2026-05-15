# Query Optimization

## Why this matters in backend interviews

- **The #1 production debugging skill** for backend engineers — a slow query brings down APIs, causes timeouts, and triggers pages.
- **System design rounds** test whether you can reason about query costs, not just write queries.
- **Senior signal:** Reading an `EXPLAIN` plan and proposing fixes before running anything is the strongest demonstration that you understand the database.
- Companies love asking: *"I have this slow query. What would you do?"* — and they expect a structured diagnostic process, not random guessing.

---

## Core concepts

### The optimizer is a cost estimator

Given a query, the planner generates many possible execution plans (join orders, access methods, algorithms) and picks the one with the **lowest estimated cost**. Cost is based on:

- Row estimates (from statistics: `ANALYZE`)
- I/O cost (seq read vs random read)
- CPU cost (per-row processing, hashing, sorting)
- Memory (work_mem in Postgres, sort_buffer_size in MySQL)

If statistics are stale, estimates are wrong, and the plan is wrong. **`ANALYZE` (Postgres) / `ANALYZE TABLE` (MySQL)** updates statistics.

### How to read `EXPLAIN ANALYZE` (Postgres)

```
Seq Scan on orders  (cost=0.00..1234.56 rows=10000 width=64)
                    (actual time=0.012..3.456 rows=9821 loops=1)
  Filter: (status = 'PAID')
  Rows Removed by Filter: 178
```

- `cost=startup..total` → planner's estimate; not milliseconds
- `actual time=startup..total` → real measured time (ms)
- `rows=` (planner) vs `rows=` (actual) → if they differ by >10x, statistics are wrong or estimates are skewed
- `loops=` → how many times the node ran (nested-loop inner side multiplies)
- `Rows Removed by Filter` → indicates inefficient filter (often missing index)

Use `EXPLAIN (ANALYZE, BUFFERS)` to see buffer hits vs reads — high `read` = disk I/O.

### Access methods

| Method | When |
|---|---|
| **Seq Scan** | No useful index, or planner believes scanning is cheaper |
| **Index Scan** | Index used; heap lookup for selected columns |
| **Index-Only Scan** | Index covers all selected columns; no heap visit (Postgres requires visibility map) |
| **Bitmap Heap Scan** | Multiple index lookups consolidated, then heap fetched in order |

A `Seq Scan` on a tiny table is fine. A `Seq Scan` on a 100M-row table with a selective predicate is a bug.

### Join algorithms

| Algorithm | Best for | Cost |
|---|---|---|
| **Nested Loop** | Small outer + indexed inner | O(N × log M) with index |
| **Hash Join** | Large, unsorted, equi-join | O(N + M), needs RAM for the smaller side |
| **Merge Join** | Both sides already sorted (e.g., index scans) | O(N + M), no RAM hash |

If the planner picks a hash join but the smaller side doesn't fit in `work_mem`, it spills to disk → 10-100x slower.

### Predicate pushdown

The planner pushes filter conditions as deep as possible — into the index scan, into the join condition, into the subquery. **Anything that breaks this is bad.**

Things that break pushdown / index use:
- `WHERE LOWER(email) = 'foo@bar.com'` — function on indexed column → seq scan (fix: functional index)
- `WHERE created_at::date = '2026-01-01'` — cast → seq scan (fix: `WHERE created_at >= ... AND < ...`)
- `WHERE col + 1 = 10` — expression → seq scan (rewrite to `col = 9`)
- `WHERE status = 'PAID' OR amount > 100` — OR can prevent multi-column index use (fix: `UNION ALL` or bitmap-or)
- `WHERE col LIKE '%abc%'` — leading wildcard → seq scan (fix: trigram index, full-text search)
- Data type mismatch: `WHERE varchar_col = 123` → implicit cast → seq scan (fix: cast to varchar)

### Cardinality and selectivity

- **Selectivity** = fraction of rows matching a predicate
- Highly selective (low fraction) → index scan wins
- Low selectivity (e.g., `WHERE active = true` on a 99%-active table) → seq scan wins

The planner uses histograms (pg_statistic / information_schema.statistics) to estimate selectivity. Skewed data → bad estimates → wrong plan.

### Statistics

- Postgres: `ANALYZE table;` updates statistics. Autovacuum does this automatically.
- MySQL: `ANALYZE TABLE t;` updates index statistics. InnoDB also runs samples.
- For skewed data, increase `default_statistics_target` (Postgres) or use **extended statistics** for correlated columns.

### Common misconceptions

- "Adding more indexes is always good" — every index slows writes and consumes RAM/disk
- "The query planner is always right" — it's heuristic; with bad stats or weird data it fails. Hint via index name or rewrite the query.
- "Slow query = missing index" — sometimes it's join order, sometimes locking, sometimes a network round trip per row (N+1)
- "EXPLAIN runs the query" — `EXPLAIN` doesn't, `EXPLAIN ANALYZE` does (be careful on writes!)
- "Postgres's `EXPLAIN ANALYZE` includes network/client time" — it doesn't; it only times execution

### Interview traps

1. They'll show you a query and say "make it faster." Always ask: *"can I see the EXPLAIN plan and the table sizes?"* — that's the senior move.
2. They'll mention an index exists but the query is slow — look for type mismatches, functions, or stale stats.
3. They'll add a `LEFT JOIN` and then a `WHERE` on the right side — silently turns into INNER, breaks expectations.
4. They'll say "the query is slow but only sometimes" — likely parameter-sniffing / plan caching issue, or replication lag, or cache eviction.

---

## Real examples

### Slow query: "find users who haven't ordered in 30 days"

```sql
-- BAD
SELECT u.*
FROM users u
WHERE u.id NOT IN (SELECT user_id FROM orders WHERE created_at > NOW() - INTERVAL '30 days');
```

Problems:
- `NOT IN` breaks on NULL `user_id`
- Materializes whole subquery
- Probably a hash anti-join with sort

```sql
-- GOOD
SELECT u.*
FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM orders o
  WHERE o.user_id = u.id AND o.created_at > NOW() - INTERVAL '30 days'
);
```
With an index on `orders(user_id, created_at)`, this becomes an indexed anti-join — fast.

### Slow query: dashboard with multiple aggregates

```sql
-- BAD: 5 separate scans
SELECT
  (SELECT COUNT(*) FROM orders WHERE status = 'PLACED') AS placed,
  (SELECT COUNT(*) FROM orders WHERE status = 'PAID') AS paid,
  (SELECT COUNT(*) FROM orders WHERE status = 'SHIPPED') AS shipped,
  ...
```

```sql
-- GOOD: single scan with FILTER
SELECT
  COUNT(*) FILTER (WHERE status = 'PLACED') AS placed,
  COUNT(*) FILTER (WHERE status = 'PAID') AS paid,
  COUNT(*) FILTER (WHERE status = 'SHIPPED') AS shipped
FROM orders;
```

### Slow query: pagination with `OFFSET`

```sql
-- BAD: OFFSET 1,000,000 still scans all preceding rows
SELECT * FROM events ORDER BY created_at DESC LIMIT 50 OFFSET 1000000;

-- GOOD: keyset pagination
SELECT * FROM events
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```
Keyset is O(log N) instead of O(N + OFFSET).

### Slow query: function on indexed column

```sql
-- Indexed: created_at
-- BAD
SELECT * FROM events WHERE DATE(created_at) = '2026-01-01';

-- GOOD
SELECT * FROM events
WHERE created_at >= '2026-01-01' AND created_at < '2026-01-02';
```

### Payments — large IN clause

```sql
-- BAD: 10,000 IDs in IN clause
WHERE id IN (1, 2, ..., 10000)

-- BETTER: VALUES join (Postgres)
WHERE id IN (SELECT id FROM (VALUES (1),(2),...) v(id))

-- BEST: temp table or =ANY(array)
WHERE id = ANY($1::bigint[])
```

---

## Common interview questions

1. How do you debug a slow query?
2. What does `EXPLAIN ANALYZE` show? Walk through one.
3. Difference between nested loop, hash, and merge join. When does the planner pick each?
4. When does Postgres choose Seq Scan over Index Scan even when an index exists?
5. What's an index-only scan? Why might it not be used despite a covering index?
6. How would you optimize an `OR` query?
7. What is parameter sniffing? How do you fix it?
8. Why is `NOT IN` slow? What's better?
9. How do you paginate a 100M-row table?
10. Explain query plan stability and the role of stats.
11. When do you denormalize for performance?
12. How would you find which queries to optimize first?

---

## Detailed answers

### 1. Debugging a slow query — process
1. Get the exact query + parameters
2. Run `EXPLAIN (ANALYZE, BUFFERS)` — never optimize without it
3. Look for:
   - Seq Scans on big tables
   - Row estimate mismatches (planner vs actual)
   - Nested loops with high `loops`
   - Filter removing many rows
   - High `Rows Removed by Index Recheck`
4. Check indexes: `SELECT * FROM pg_indexes WHERE tablename = '...'`
5. Check stats: `ANALYZE table`
6. Rewrite predicates, add/adjust indexes, denormalize if necessary
7. Validate: re-run `EXPLAIN ANALYZE`, confirm improvement
8. If still slow: connection pool? Lock contention? Cache miss?

### 2. EXPLAIN ANALYZE walkthrough
```
Nested Loop  (cost=0.43..16.50 rows=1 width=64) (actual time=0.025..0.030 rows=1 loops=1)
  -> Index Scan using idx_users_email on users  (cost=0.29..8.31 rows=1 width=32)
       Index Cond: (email = 'foo@bar.com')
  -> Index Scan using idx_orders_user_id on orders  (cost=0.14..8.16 rows=2 width=32)
       Index Cond: (user_id = users.id)
```
Reads from the leaves up. The planner expects 1 row from users (cheap index lookup) and joins with orders via indexed lookup. Estimates match actual → good plan.

### 3. Join algorithms
- **Nested loop**: best when outer side is tiny (≤ a few thousand rows) and inner has a usable index. Postgres often picks this for LIMIT queries.
- **Hash join**: builds in-memory hash of smaller side. Best for big un-sorted equi-joins.
- **Merge join**: both sides come pre-sorted on the join key (typically from index scans). Cheap if sorted.

### 4. Seq Scan despite an index
- Predicate selects most of the table (low selectivity)
- Stats stale → planner over-estimates selectivity
- Implicit cast or function disables index use
- Table is small (under ~50 pages); seq scan is cheaper
- `random_page_cost` too high → index scan looks expensive
- Index is invalid / not yet built (concurrent index build interrupted)

### 5. Index-only scan
Postgres needs the **visibility map** to confirm the tuple is visible without a heap visit. If the page hasn't been vacuumed, the planner falls back to index scan + heap fetch. Mitigation: ensure `autovacuum` runs frequently on hot tables.

### 6. Optimizing OR
```sql
-- BAD: OR prevents single-index use
WHERE status = 'PAID' OR user_id = 42

-- GOOD: UNION ALL each branch using its own index
SELECT ... WHERE status = 'PAID'
UNION ALL
SELECT ... WHERE user_id = 42 AND status <> 'PAID';
```
Postgres can sometimes do BitmapOr; depends on planner.

### 7. Parameter sniffing
When a parameterized query gets a plan based on the first param value and that plan is bad for other values. Postgres uses **plan caching with custom plan / generic plan switching**. Fix:
- Use `set plan_cache_mode = 'force_custom_plan'` for problematic queries
- Or inline the literal value (loses caching benefit)
- Or use `pg_hint_plan` / SQL Server `OPTION (RECOMPILE)`

### 8. NOT IN
- NULL-unsafe: a single NULL in subquery → empty result
- Often hash anti-join, but with NULL handling overhead
- `NOT EXISTS` is faster and NULL-safe

### 9. Paginating 100M rows
- **Keyset pagination** using a unique-tiebreak key
- Cursor-based with a sortable + unique key
- Pre-compute pages for very hot queries (e.g., top 100 leaderboard cached every 5s)
- Avoid `COUNT(*)` for total — use approximate or pre-computed counts

### 10. Stats and plan stability
The planner relies on statistics (histograms, MCV — most common values, ndistinct) to estimate row counts. After bulk imports or skewed data growth, stats are stale → wrong plan. `ANALYZE` rebuilds them. `default_statistics_target` controls sample size (default 100).

### 11. When to denormalize
- Read >> write ratio
- Joins span 3+ tables on hot path
- Computed values change rarely (e.g., user.total_orders)
- Reporting/dashboard tables
- Always document the duplication and the source of truth.

### 12. Finding queries to optimize
- Postgres: `pg_stat_statements` extension — top queries by total/avg time, calls, rows
- MySQL: slow query log + `performance_schema.events_statements_summary_by_digest`
- APM tools: Datadog, NewRelic, Honeycomb — query traces
- Look at: p99 latency, total time consumed (not just avg), queries with high stddev

---

## Practical coding examples

### Enable & query pg_stat_statements
```sql
CREATE EXTENSION pg_stat_statements;

SELECT query, calls, total_exec_time, mean_exec_time, rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC LIMIT 20;
```

### Force a plan via index hint (Postgres uses pg_hint_plan; MySQL has native hints)
```sql
-- MySQL
SELECT /*+ INDEX(orders idx_orders_user_created) */ * FROM orders WHERE user_id = 5;

-- Postgres (with extension)
/*+ IndexScan(orders idx_orders_user_created) */
SELECT * FROM orders WHERE user_id = 5;
```

### Rewrite OR as UNION ALL
```sql
-- Slow OR
SELECT * FROM users WHERE email = 'x' OR phone = 'y';

-- Fast UNION ALL (using each index)
SELECT * FROM users WHERE email = 'x'
UNION ALL
SELECT * FROM users WHERE phone = 'y' AND email IS DISTINCT FROM 'x';
```

### Detect slow queries in production
```sql
-- Postgres: queries running > 30s
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > INTERVAL '30s'
ORDER BY duration DESC;
```

---

## Common mistakes

- Optimizing without `EXPLAIN ANALYZE` — fixing what's not broken
- Adding indexes blindly — each one slows writes by 5-30%
- Ignoring stats — `ANALYZE` after bulk imports
- Optimizing average case when p99 is the problem
- Using `SELECT *` and then complaining about network bandwidth
- Doing JOINs in the app layer ("ORM said so") instead of in SQL
- Forgetting that `LIMIT 1` can dramatically change the plan (planner switches to early-stop)

---

## Senior engineer discussion points

- **Workload characterization** — OLTP vs OLAP vs hybrid. Different optimizations apply.
- **Plan cache management** — when does Postgres switch from custom to generic plan?
- **Read replicas for analytics** — protect OLTP from heavy reports
- **Materialized views** with incremental refresh
- **Partitioning** for time-series data — pruning whole partitions in a query
- **Vacuum/bloat** — index and table bloat from MVCC overwrites can silently slow queries
- **TOAST in Postgres** — large columns stored out-of-line; affects scan speed
- **Connection pooling** — too many connections = thrashing; PgBouncer in transaction mode
- **Workload isolation** — separate analytics user with lower priority, statement timeouts

---

## Revision notes

- Start with `EXPLAIN ANALYZE` — never guess
- Look for: Seq Scans, row estimate mismatch, high loops, filter-after-scan
- Statistics matter — `ANALYZE` after bulk loads
- Function on indexed column → index unused (use functional index or rewrite)
- `OR` often kills single-index use; consider `UNION ALL`
- Keyset > OFFSET for pagination
- `NOT EXISTS` > `NOT IN` (NULL-safe + indexable)
- `pg_stat_statements` / slow query log to find offenders
- Hash join needs `work_mem` to avoid spill
- LIMIT changes the plan — nested loop becomes attractive
