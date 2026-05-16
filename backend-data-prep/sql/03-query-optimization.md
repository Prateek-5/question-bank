# Query Optimization

> **Teaching frame (read this first).** A database query is like asking a librarian "find me all books by an author published after 2010." The librarian has many possible strategies: scan every shelf, use the card catalog, walk the alphabetical index, or pre-sort the answer in their head. The **query optimizer** is that librarian — it picks the strategy. Query optimization, then, is the craft of (a) understanding *why* the librarian chose what they did, (b) giving them the right tools (indexes, statistics, rewritten predicates) so the next choice is better.
>
> Throughout this file we will move from the simplest question ("what is a plan?") to the most senior one ("how do I argue about p99 latency under skewed data when stats are stale?"). Do not skip the analogies; they are the load-bearing scaffolding for the technical detail.

## Mental model: the optimizer as a GPS

Imagine planning a road trip in a navigation app:

- The **map** = your tables and indexes.
- The **traffic data** = statistics (`ANALYZE`) — how many rows match what, hotspots, skew.
- The **routes** = candidate execution plans (different join orders, access methods).
- The **cost** the GPS shows = the optimizer's estimated cost (page reads + CPU + memory).
- The **route chosen** = the final plan.

If traffic data is stale, the GPS picks a "fast" route that's actually clogged. If your map is missing a highway (a missing index), the GPS routes you through neighborhood streets (sequential scan). If two routes look equally good, a single tweak (an `ANALYZE`, a rewritten predicate, a new index) flips the choice.

```
        Query SQL
            |
            v
    +---------------+         +-----------------+
    |   Parser      |-------->|  Rewriter       |  (view expansion, etc.)
    +---------------+         +-----------------+
                                       |
                                       v
                              +-----------------+
                              |  Planner /      |
                              |  Optimizer      | <---- statistics, indexes
                              +-----------------+
                                       |
                                       v
                              Chosen execution plan
                                       |
                                       v
                              +-----------------+
                              |  Executor       |
                              +-----------------+
                                       |
                                       v
                                   Result rows
```

## Why interviewers care

When an interviewer asks "this query is slow, what now?", they are testing five distinct skills at once:

1. **Diagnostic discipline** — do you reach for `EXPLAIN ANALYZE`, or do you guess?
2. **Vocabulary** — can you name access methods, join algorithms, and cost components precisely?
3. **First-principles** — can you reason about I/O vs CPU, pages, selectivity?
4. **Trade-off awareness** — do you propose changes that improve reads *without* destroying writes?
5. **Production sense** — do you know how to roll out the fix safely (CONCURRENTLY, replicas, canaries)?

The strongest signal is when you propose a *hypothesis* from the plan, then say "the way I'd confirm this is...". That is what separates a senior from a mid-level.

## Why this matters in backend interviews

- **The #1 production debugging skill** for backend engineers — a slow query brings down APIs, causes timeouts, and triggers pages.
- **System design rounds** test whether you can reason about query costs, not just write queries.
- **Senior signal:** Reading an `EXPLAIN` plan and proposing fixes before running anything is the strongest demonstration that you understand the database.
- Companies love asking: *"I have this slow query. What would you do?"* — and they expect a structured diagnostic process, not random guessing.

---

## First principles: why I/O dominates

Before any specific concept, internalise this:

- A modern CPU does ~10 billion simple operations per second.
- A RAM access is ~100 nanoseconds.
- A random read from an SSD is ~100 microseconds — **1000x slower than RAM**.
- A random read from a spinning disk is ~10 milliseconds — **100,000x slower than RAM**.

Databases store data in fixed-size **pages** (8 KB in Postgres, 16 KB in InnoDB). Every read is at least one page. So the unit of work is "page reads", not "row reads". An algorithm that reads 1,000 pages will (almost always) beat one that reads 100,000 pages, regardless of CPU steps.

This is why a sequential scan of a 100 GB table is *slow* (12.5M pages × even a fast 10µs read = 125 seconds), and why a B-tree lookup that touches 4 pages is *fast* (40µs). It is also why **buffer pool / shared_buffers cache hit rate** is the single most important DB metric: a page in RAM is ~1000x cheaper than the same page on disk.

```
Latency mountain (approx):
  L1 cache       ~1 ns       |
  L2 cache       ~3 ns       | <-- CPU regime
  RAM           ~100 ns      |
  SSD random    ~100 us      | <-- I/O regime (1000x jump)
  HDD random    ~10 ms       | <-- 100,000x jump
  Network RTT   ~0.5-50 ms
```

The optimizer's job is, fundamentally, **to minimise the number of pages read**, especially random ones. Everything else (join order, algorithm choice, index use) flows from that single objective.

## Progressive concept building

We will build up the optimizer in three passes:

1. **Simplest:** "scan the whole table and filter." This is the baseline cost.
2. **Intermediate:** "use an index to jump to the right rows." This is where 80% of wins come from.
3. **Advanced:** "pick the right *order* of joins, with the right *algorithm*, given the statistics." This is what the planner actually does.

If you keep this ladder in mind while reading the next sections, the cost formulas and traps stop feeling magical.

## Core concepts

### The optimizer is a cost estimator

Given a query, the planner generates many possible execution plans (join orders, access methods, algorithms) and picks the one with the **lowest estimated cost**. Cost is based on:

- Row estimates (from statistics: `ANALYZE`)
- I/O cost (seq read vs random read)
- CPU cost (per-row processing, hashing, sorting)
- Memory (work_mem in Postgres, sort_buffer_size in MySQL)

If statistics are stale, estimates are wrong, and the plan is wrong. **`ANALYZE` (Postgres) / `ANALYZE TABLE` (MySQL)** updates statistics.

#### Mental model — rule-based vs cost-based

- **Rule-based optimizer (RBO, historical):** "If there is an index, use it." Deterministic, brittle. Falls apart on skewed data.
- **Cost-based optimizer (CBO, modern):** "Estimate the cost of every plan and pick the cheapest." Needs accurate statistics. All major databases today (Postgres, MySQL 8+, Oracle, SQL Server) are CBO.

Analogy: RBO is a checklist on the wall; CBO is a chess engine that searches and evaluates. CBO is smarter, but it is only as good as the *evaluation function* (the cost model) and the *board state it sees* (the statistics).

#### Why interviewers care about the optimizer

They want to know if you treat the database as a black box ("just write SQL") or as a system with knobs ("I know which knob and why"). A candidate who says "the planner is guessing 1 row but the actual is 200,000 — that's a statistics problem" demonstrates *exactly* the senior signal.

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

#### Step-by-step: reading a plan line by line

Take a fuller example:

```
Limit  (cost=0.43..8.45 rows=1 width=64) (actual time=0.045..0.046 rows=1 loops=1)
  ->  Nested Loop  (cost=0.43..16.50 rows=2 width=64) (actual time=0.044..0.045 rows=1 loops=1)
        ->  Index Scan using idx_users_email on users u  (cost=0.29..8.31 rows=1 width=32)
              (actual time=0.022..0.023 rows=1 loops=1)
              Index Cond: (email = 'foo@bar.com')
        ->  Index Scan using idx_orders_user_id on orders o  (cost=0.14..8.16 rows=2 width=32)
              (actual time=0.018..0.019 rows=1 loops=1)
              Index Cond: (user_id = u.id)
  Planning Time: 0.180 ms
  Execution Time: 0.080 ms
```

Read **bottom-up, inside-out** (like a recipe — sub-steps first):

1. *Inner-most:* `Index Scan on users` using `idx_users_email`, filter `email='foo@bar.com'`. Planner expected 1 row, got 1. Healthy.
2. *Next:* For each row from `users`, do an `Index Scan on orders` with `user_id = u.id`. This is the *inner* side of the nested loop.
3. *Above that:* `Nested Loop` joins them. The `loops=1` on the inner means it only ran once (because outer produced 1 row). If outer had produced 1000 rows, you'd see `loops=1000` on the inner and you'd multiply that side's cost by 1000.
4. *Top:* `Limit 1` — short-circuits after the first match. This often lets the planner pick nested loop over hash join.
5. *Footer:* `Planning Time` (how long the optimizer thought) vs `Execution Time` (how long the executor ran). If planning >> execution, you have many candidate plans or extension overhead.

##### Estimate vs actual — the diagnostic gold

Always compare `rows=...` (planner) to `actual ... rows=...`.

| Estimate | Actual | Likely cause | Fix |
|---|---|---|---|
| 1 | 200,000 | Stale stats, skew, correlated columns | `ANALYZE`, extended stats |
| 200,000 | 1 | Stats overestimate skew | `ANALYZE`, narrow predicate |
| 100 | 100 | Healthy | — |
| 1 | 1 (but loops=1M) | Nested loop blowup | Force hash join, fix join key |

#### Mental model — the plan is a recipe tree

A query plan is a **tree** of operators. Each operator pulls rows from its children one at a time (the "Volcano model") or in batches. Visualise it as:

```
                  Aggregate
                     |
                    Sort
                     |
                  Hash Join  ----- builds hash from right child
                  /        \
            Seq Scan    Index Scan
            (orders)    (users)
```

If a node says "rows=10000" but its parent says "rows=1", you immediately know: most of the work in the child node is *wasted* — those 9999 rows were thrown away above. That's a flashing arrow at where to add a filter or index.

### Access methods

| Method | When |
|---|---|
| **Seq Scan** | No useful index, or planner believes scanning is cheaper |
| **Index Scan** | Index used; heap lookup for selected columns |
| **Index-Only Scan** | Index covers all selected columns; no heap visit (Postgres requires visibility map) |
| **Bitmap Heap Scan** | Multiple index lookups consolidated, then heap fetched in order |

A `Seq Scan` on a tiny table is fine. A `Seq Scan` on a 100M-row table with a selective predicate is a bug.

#### Mental model — access methods as travel modes

- **Seq Scan** = walking the whole library shelf by shelf. O(N) pages. Only optimal when you need most of the books.
- **Index Scan** = using the card catalog (the index) to find each book, then walking to the shelf to grab it. O(log N) catalog lookups + N random heap reads.
- **Index-Only Scan** = the card catalog has *enough info* on each card to answer your question; you never walk to the shelf. The fastest "lookup" mode.
- **Bitmap Heap Scan** = the librarian first writes down a list of shelf locations from one or more catalogs, sorts that list by aisle, and then walks the aisles in order picking up books. Avoids zigzagging. Excellent when many rows match.

#### Bitmap scans — when and why

A bitmap scan is essentially: "I will use the index *only* to mark which pages I need, then read those pages in physical order." This converts random I/O into (mostly) sequential I/O. The planner picks this when:

- A single predicate returns "medium" rows (too many for plain index scan, too few for seq scan).
- Multiple indexes can be combined (Bitmap And / Bitmap Or).

The "recheck" step at the end re-evaluates the predicate against the actual heap rows in case the bitmap was lossy (compressed by page rather than by row).

### Join algorithms

| Algorithm | Best for | Cost |
|---|---|---|
| **Nested Loop** | Small outer + indexed inner | O(N × log M) with index |
| **Hash Join** | Large, unsorted, equi-join | O(N + M), needs RAM for the smaller side |
| **Merge Join** | Both sides already sorted (e.g., index scans) | O(N + M), no RAM hash |

If the planner picks a hash join but the smaller side doesn't fit in `work_mem`, it spills to disk → 10-100x slower.

#### Mental model — join algorithms as social events

- **Nested Loop** = a small dinner party. For each guest (outer row), the host (planner) personally asks each potential partner (inner row, via index lookup) if they match. Works if the party is small and you have a guest list (index) on the inner side.
- **Hash Join** = a wedding with name-tags. You first build a giant table (hash) of all guests on one side, then everyone from the other side walks past once and finds their match by tag. One-pass over each side; needs RAM for the tags.
- **Merge Join** = a procession where both lines are already sorted by name. The two priests walk down both lines in step. Cheapest if (and only if) both are already in order — typically from an ordered index scan.

#### Structural diagrams

```
Nested Loop (outer drives, inner is probed per row):

   outer ----+----+----+----+----+
             |    |    |    |    |
             v    v    v    v    v
       inner-probe (index) for each outer row
```

```
Hash Join (build smaller side, then probe with the larger):

   smaller ---> [ Build Hash Table in RAM ]
                          |
   larger ---> probe each row --+--> matched output
                                |
                                +--> spills to disk if hash > work_mem
```

```
Merge Join (both sides pre-sorted on the join key):

   left   sorted: a a b c c d e
   right  sorted:   a   b c   d f
                 \  |  / | |  /
                  match in lockstep, advance the smaller side
```

#### Step-by-step: when does the planner pick which?

1. Are both sides large and the join is equi (`=`)? **Hash Join** is usually best — O(N + M) and one scan each.
2. Is the outer side tiny *and* the inner side has an index on the join key? **Nested Loop with Index Scan** wins — you do (small outer) × log(inner) lookups.
3. Are both sides naturally sorted on the join key (from an index, or a prior sort that you'd pay anyway)? **Merge Join** — no hash memory needed, predictable streaming.
4. Hash Join the obvious choice but small side > `work_mem`? Either bump memory, add filters earlier, or accept the disk spill (and the 10-100x slowdown).

#### Common confusion: "why did Postgres use Nested Loop instead of Hash?"

Usually because of `LIMIT`. With `LIMIT 1`, the planner says "I only need *one* matching row; why bother building a giant hash table?" — and a nested loop short-circuits beautifully. Remove the `LIMIT` and the plan often flips to hash. This is *not* a bug; it's correct behaviour, but it's a surprise.

### Predicate pushdown

The planner pushes filter conditions as deep as possible — into the index scan, into the join condition, into the subquery. **Anything that breaks this is bad.**

Things that break pushdown / index use:
- `WHERE LOWER(email) = 'foo@bar.com'` — function on indexed column → seq scan (fix: functional index)
- `WHERE created_at::date = '2026-01-01'` — cast → seq scan (fix: `WHERE created_at >= ... AND < ...`)
- `WHERE col + 1 = 10` — expression → seq scan (rewrite to `col = 9`)
- `WHERE status = 'PAID' OR amount > 100` — OR can prevent multi-column index use (fix: `UNION ALL` or bitmap-or)
- `WHERE col LIKE '%abc%'` — leading wildcard → seq scan (fix: trigram index, full-text search)
- Data type mismatch: `WHERE varchar_col = 123` → implicit cast → seq scan (fix: cast to varchar)

#### Mental model — why functions break indexes

An index on `email` is sorted by *the raw email value*. The index has no idea what `LOWER(email)` would produce until it computes it for every single row. So to use `WHERE LOWER(email) = ...`, the planner must compute `LOWER` on each row → it has to read each row → seq scan.

A **functional index** says "I want the index to store `LOWER(email)`, not `email`". Then the sort order in the index matches the predicate, and binary search works.

Generalised rule: *the indexed expression must appear in the query exactly as written.* If you indexed `email`, the query must say `email = ...`, not `LOWER(email)` or `email || ''` or `email::text` (under some casts).

#### Common beginner confusion: anti-patterns explained

- *"I added `SELECT *` because I might need the columns later."* → forces the executor to read all heap rows even when the index could cover the answer. Replace with explicit columns to enable index-only scans.
- *"OR is the same as UNION, why is it slower?"* → `OR` between predicates on different columns prevents the planner from choosing a single index (each side of the OR could use a different index). `UNION ALL` lets each side independently use its best index.
- *"LIKE 'foo%' uses an index but LIKE '%foo' doesn't — but they're the same kind of search!"* → indexes are sorted lexicographically. `foo%` is a prefix → binary search works. `%foo` is a *suffix* — no prefix → can't binary-search.

### Cardinality and selectivity

- **Selectivity** = fraction of rows matching a predicate
- Highly selective (low fraction) → index scan wins
- Low selectivity (e.g., `WHERE active = true` on a 99%-active table) → seq scan wins

The planner uses histograms (pg_statistic / information_schema.statistics) to estimate selectivity. Skewed data → bad estimates → wrong plan.

#### Mental model — selectivity as "how rare is this?"

If I tell you "find people named X" — you walk straight to the rare-names section if X is "Zephyrina", but you give up and scan everyone if X is "John". Same with the database: a rare value (high selectivity) → use the index; a common value (low selectivity) → seq scan is cheaper because the index lookups would each trigger a random heap read anyway.

**Rough rule:** if a predicate matches more than ~10-20% of the table, an index probably won't be used (because the random I/O cost dominates over the seq scan).

### Statistics

- Postgres: `ANALYZE table;` updates statistics. Autovacuum does this automatically.
- MySQL: `ANALYZE TABLE t;` updates index statistics. InnoDB also runs samples.
- For skewed data, increase `default_statistics_target` (Postgres) or use **extended statistics** for correlated columns.

#### What's actually inside `pg_statistic`?

For each column the planner tracks (typically):

- **`null_frac`** — fraction of NULLs.
- **`n_distinct`** — number of distinct values (-1 means "as many as rows", i.e., unique).
- **`most_common_vals` + `most_common_freqs`** — the top-K (default K=100) most common values and their frequencies. This is the planner's defence against skew.
- **`histogram_bounds`** — sorted samples that partition the remaining (non-MCV) values into equal-frequency buckets.
- **Correlation** — how close the physical row order matches the logical sort order (informs whether index scan can be near-sequential).

When the planner estimates `WHERE x = 'Z'`, it first checks the MCV list (constant time, exact). If `'Z'` isn't there, it estimates `(1 - sum(MCV freqs) - null_frac) / (n_distinct - len(MCV))`. That's why **extended statistics on correlated columns** (e.g., `(country, city)`) matter — by default Postgres treats columns as independent and multiplies probabilities, badly underestimating when they're correlated.

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

## Buffer pool / shared_buffers — the hidden lever

```
            APPLICATION
                |
                v
       +--------------------+
       |   shared_buffers   |    (Postgres-managed page cache, e.g. 8 GB)
       |   (LRU-ish)        |
       +--------------------+
              |       ^
   page miss  v       | page hit (fast: RAM)
       +--------------------+
       |    OS page cache   |    (kernel-managed, uses remaining RAM)
       +--------------------+
              |       ^
              v       |
       +--------------------+
       |       DISK         |    (SSD/NVMe; 100us+ per random page)
       +--------------------+
```

Two layers of caching:

1. **Postgres shared_buffers** — explicit, fixed-size, LRU. Typically 25% of RAM. `EXPLAIN (ANALYZE, BUFFERS)` shows `Buffers: shared hit=X read=Y` — `hit` is shared_buffers, `read` is anything below it (might still be OS cache).
2. **OS page cache** — uses leftover RAM, kernel-managed, much larger than shared_buffers usually.

Why this matters in interviews: when you say "this query takes 800ms", the *first time* might be 800ms (cold) and *every subsequent run* 5ms (cached). Always state which case you're measuring. Production p99 is closer to the cold case for rarely-touched data; p50 is closer to the warm case for hot data.

---

## Interview storytelling: how to walk through optimising a slow query

When the interviewer says "imagine this query is slow", here is the rehearsed script — say it out loud:

1. *"Before I touch anything, I want to see the query, the parameters, the table sizes, and the existing indexes. Can I assume `EXPLAIN (ANALYZE, BUFFERS)` is available?"*
2. *"From the plan, I'd look at three things: are there sequential scans on big tables? Are planner row estimates close to actual? Are there nested loops with high `loops`?"*
3. State a hypothesis: *"My hypothesis is the predicate on `created_at::date` is preventing the index on `created_at`. I'd rewrite it as a half-open range."*
4. Predict impact: *"I expect the cost to drop from ~50k pages to ~50 pages — about a 1000x improvement on the cold cache."*
5. Then the follow-up: *"Now there are 100M rows. Does the answer change?"* — your answer should mention partitioning (by time), keyset pagination, replica routing, materialised aggregates, and BRIN for cold history.

Practice this script. Senior interviews are won on *process*, not on memorised facts.

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

## Bridge to the Indexing file

Almost every fix in this file relies on indexes being chosen, sized, and ordered well. The next file (`04-indexing.md`) covers:

- *What an index physically is* (B-tree, hash, GIN, GiST, BRIN).
- *How to design composite indexes* using the Equality → Range → Sort rule that we referenced here in the predicate-pushdown section.
- *Covering / index-only scans* — the thing we hinted at in the "Index-Only Scan" row of the access-methods table.
- *The write penalty* — why adding "one more index" to fix a slow read can hurt write p99.

Read the two files together: this file teaches you to *diagnose* with the plan; the next teaches you to *fix* with the right index design.

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
