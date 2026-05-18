# Reading EXPLAIN ANALYZE Line by Line

## Source / Origin
- Senior SQL screen — "here's a slow query and its EXPLAIN. Diagnose it."
- Real prod: every perf war story starts with "I ran EXPLAIN ANALYZE and saw…".

## Why this question matters in interviews
EXPLAIN ANALYZE is the single most-used SQL debugging tool. Interviewers will paste a real plan and ask you to **read it like a recipe**: which operator runs first, where is the time spent, which estimate is wrong. Candidates who freeze on `Gather Merge` or `Bitmap Heap Scan` haven't worked on a real database.

The deeper goal: can you spot the **classic anti-patterns** — Seq Scan on a big table, row-estimate off by 100×, nested loop with high inner rows? You don't need to memorize all 40 Postgres operators; you need to read the tree top-down, find the expensive node, ask "why is it that way?"

## Concepts involved

### Syntax to lock in
```sql
-- Plain plan (cheap, no execution):
EXPLAIN SELECT * FROM orders WHERE user_id = 42;

-- Plan + actual run (executes query!):
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 42;

-- Verbose, with buffers and timing detail:
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT * FROM orders WHERE user_id = 42;
```

### Edge cases / interview traps
1. **`EXPLAIN` does NOT run the query; `EXPLAIN ANALYZE` does.** Don't `ANALYZE` an `UPDATE` in prod unless wrapped in `BEGIN; ... ROLLBACK;`.
2. **Cost units are arbitrary.** Postgres "cost" is in fictional units (`seq_page_cost`, `cpu_tuple_cost`). Compare relative, not absolute.
3. **Plan tree reads bottom-up but operators execute children-first.** Indent depth indicates child relationship.
4. **`actual rows` vs `rows` (estimated)** — if they're off by > 10×, the planner has bad stats. Run `ANALYZE table` to refresh.
5. **`loops`** — for inner side of nested loops, `actual rows × loops` is total work; raw `actual rows` is per-iteration.
6. **`Buffers` matters more than `rows`.** Shared-hit means cache hit; shared-read means disk read.
7. **Parallel plans** (`Gather`, `Gather Merge`) split work across workers. Read inner operator + multiply.
8. **JIT in Postgres 11+** shows up as a separate timing section. For OLTP it's overhead; turn off for hot small queries.
9. **`Memoize` (Postgres 14+)** caches inner-loop results — great for skewed data, signal of repeated lookup.

## Mental Model

```
                      Gather   (parallel reducer, top)
                        │
                  ┌─────┴─────┐
                  │ Hash Join │
                  └─────┬─────┘
              ┌─────────┴────────┐
        Seq Scan: A           Hash
        (inner side)            │
                          Seq Scan: B  (build side, hashed)

  Read order (data flow):    children first → parents last.
  Time-it-takes order:       child timings *include* their children's by default.
  "Actual" / "loops":        per-iteration counts; multiply for total.
```

EXPLAIN ANALYZE is a **postfix tree** with each node annotated by estimated cost, actual rows, and timing. Find the expensive node by scanning for the highest `actual time` that *isn't dominated by its children*.

## Why interviewers care
- Confirms candidate has actually used Postgres / MySQL in production.
- Tests pattern-recognition: Seq Scan on big table → bad; nested loop with high outer count → bad; hash join with low inner rows → fine.
- Reveals whether the candidate can connect EXPLAIN output back to actionable fixes (add index, rewrite predicate, refresh stats).

## Common beginner confusion
- "Lower cost is faster" — usually, but cost is unitless; trust `actual time` more.
- "I'll just look at the top of the plan" — wrong; the heavy operators are usually deep.
- "Estimated rows and actual rows should match" — they often don't; that's the diagnostic.
- "Parallel is always faster" — for small result sets the parallel startup overhead dominates.

## Brute force approach
Stare at the plan and guess. Most candidates do this. The structured approach:

1. **Read top-down** to identify the operator types.
2. **Find the most-expensive operator** by `actual time` (subtracting children).
3. **Compare estimated vs actual rows** at that operator. Order-of-magnitude diff → stats are stale.
4. **Map operator → cause → fix.** Seq Scan → add index. Hash Join build-side too big → memory; Nested Loop with high inner → missing index on inner side.

## Optimal approach
Treat each node as a question to answer. Below is the cheat sheet:

| Operator                    | Sees                  | Common cause                              | Fix                                   |
|-----------------------------|-----------------------|--------------------------------------------|---------------------------------------|
| `Seq Scan` (big table)      | Full scan             | Missing index / non-SARGable predicate     | Add/rewrite                           |
| `Index Scan`                | Few rows expected     |                                           |                                       |
| `Bitmap Index Scan` + `Heap`| Medium selectivity    |                                           |                                       |
| `Nested Loop` (high outer)  | O(outer × inner)      | Inner side missing index                   | Add index on inner FK                |
| `Hash Join`                 | Medium-large + small  | Sometimes spills to disk if build big      | Increase `work_mem`                  |
| `Merge Join`                | Both sides pre-sorted | Forced sort step (`Sort` child)            | Add matching index, push order down  |
| `Sort` + Disk               | Spilled               | `work_mem` too small                       | Raise `work_mem` for this session     |
| `Materialize`               | Re-reads inner        | Nested loop's inner re-evaluated each iter |                                       |
| `Memoize` (PG14+)           | Caches inner          | Skewed outer keys                          | Often a sign all is well              |

## Solution (SQL)

Sample query:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT u.name, COUNT(*) AS n
FROM   users u
JOIN   orders o ON o.user_id = u.id
WHERE  o.created_at >= '2024-01-01'
GROUP  BY u.name
ORDER  BY n DESC
LIMIT  10;
```

Sample EXPLAIN ANALYZE output:

```
 Limit  (cost=23415..23415 rows=10 width=18) (actual time=412..412 rows=10 loops=1)
   ->  Sort  (cost=23415..23420 rows=2000 width=18) (actual time=412..412 rows=10 loops=1)
         Sort Key: (count(*)) DESC
         Sort Method: top-N heapsort  Memory: 25kB
         ->  HashAggregate  (cost=23360..23380 rows=2000 width=18) (actual time=380..410 rows=1832 loops=1)
               Group Key: u.name
               ->  Hash Join  (cost=270..18000 rows=600000 width=10) (actual time=12..240 rows=587412 loops=1)
                     Hash Cond: (o.user_id = u.id)
                     ->  Index Scan using ix_orders_created on orders o
                         (cost=0.4..16500 rows=600000 width=4)
                         (actual time=0.05..150 rows=587412 loops=1)
                         Index Cond: (created_at >= '2024-01-01')
                     ->  Hash  (cost=180..180 rows=10000 width=14) (actual time=11..11 rows=10000 loops=1)
                           Buckets: 16384  Batches: 1  Memory Usage: 720kB
                           ->  Seq Scan on users u
                               (cost=0..180 rows=10000 width=14) (actual time=0..7 rows=10000 loops=1)
 Planning Time: 0.4 ms
 Execution Time: 414 ms
```

## Step-by-step dry run

Walk it bottom-up:

```
1. Seq Scan on users        — 10K rows in 7ms. Acceptable (whole table is small).
2. Hash (build side)        — 10K rows hashed into 16K buckets, 720kB. One batch, no spill ✓.
3. Index Scan on orders     — 587K rows via ix_orders_created. ~150ms. Selectivity ~6%; reasonable.
4. Hash Join (probe)        — 587K probes × O(1) hash lookup = 240ms cumulative.
5. HashAggregate            — 1832 distinct names from 587K rows. ~30ms.
6. Sort (top-N heapsort)    — only keeps top-10. 25kB. Fine.
7. Limit                    — emits 10 rows.

Hot spot: Index Scan on orders (150ms). Already using the index — speed up only by narrower predicate or smaller table.
Estimates vs actual: rows=600000 vs actual=587412 — close. Stats are healthy.
```

Conclusion: query is well-planned. If we wanted < 100ms, we'd materialize a daily aggregate or use a covering index `(user_id, created_at)` so the hash join's inner side avoids the heap fetch.

## How to think aloud in the interview
1. *"I read EXPLAIN bottom-up because data flows children-first. Top of the plan is the last operator."*
2. *"I scan for the highest `actual time` that isn't accumulated from children. That's where the work is."*
3. *"Then I compare estimated vs actual rows — if they're off by 10× or more, stats are stale and I'd run `ANALYZE table`."*
4. *"Seq Scans on big tables and Nested Loops with thousands of outer rows are the classic red flags."*
5. *"Buffers tells me cache vs disk. Shared-read on a hot query means I'm missing in cache; consider warming or indexing."*

## Important takeaways
- `EXPLAIN` plans; `EXPLAIN ANALYZE` plans **and runs**.
- Read bottom-up; time accumulates upward.
- Mismatch estimate vs actual = stale stats → `ANALYZE`.
- Operator playbook: Seq Scan → index; Nested Loop high-outer → index inner; Sort spill → `work_mem`.
- BUFFERS shows cache vs disk reads.
- See `backend-data-prep/sql/03-query-optimization.md` "EXPLAIN" for theory.

## Variants
1. **`EXPLAIN (ANALYZE, FORMAT JSON)`** — programmatic parsing. Useful for CI plan-stability tests.
2. **Auto-explain extension** — logs slow-query plans automatically. Senior touch.
3. **MySQL EXPLAIN FORMAT=TREE / ANALYZE** — different output but same concepts.

## Revision notes

> **EXPLAIN ANALYZE cram block**
> - EXPLAIN = plan; EXPLAIN ANALYZE = plan + run (don't ANALYZE UPDATE in prod unless in tx).
> - Read **bottom-up**; data flows children-to-parent.
> - Hot spot = highest `actual time` not from children.
> - Estimate vs actual off > 10× → stale stats → `ANALYZE table`.
> - Operators to know: Seq Scan, Index Scan, Bitmap Index/Heap, Nested Loop, Hash Join, Merge Join, Sort, HashAggregate, Gather, Memoize.
> - BUFFERS section: hit = cache, read = disk.
> - Parallel: Gather/Gather Merge — multiply inner workers.
> - `loops` matters for inner of NL: total = actual × loops.
> - One-line fixes often follow: add index, raise `work_mem`, rewrite predicate.
