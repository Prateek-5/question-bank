# Nested Loop vs Hash vs Merge — Join Algorithm Recognition

## Source / Origin
- Classic senior SQL interview at Oracle, Amazon, Atlassian.
- "Given the data shape and the EXPLAIN, which physical join algorithm did Postgres pick and why?"

## Why this question matters in interviews
Knowing the three physical join algorithms — nested loop, hash, merge — and when each is optimal is the difference between **reading a plan** and **predicting a plan**. Interviewers ask because the planner's choice has 100× perf implications, and being able to explain "the optimizer chose hash because the inner side fits in `work_mem` and there's no usable index" demonstrates real DB knowledge.

The deeper probe: can you anticipate when the **plan will switch** (e.g. when the data volume crosses a threshold, when an index is dropped, when `work_mem` shrinks)? That's the senior signal.

## Concepts involved

### Syntax to lock in
```sql
-- Same query, different physical plans depending on data + indexes:
SELECT * FROM customers c JOIN orders o ON o.customer_id = c.id;
```

| Algorithm     | Trigger                                                                                           | Cost                          |
|---------------|---------------------------------------------------------------------------------------------------|--------------------------------|
| Nested Loop   | Outer is small + inner has an index on the join key                                              | O(outer × log(inner))         |
| Hash Join     | Inner fits in `work_mem`; no useful index; join is equi-join                                      | O(outer + inner) + build cost |
| Merge Join    | Both inputs already sorted by join key (or both have an index that gives them in sorted order)    | O(outer + inner) + sort cost  |

### Edge cases / interview traps
1. **Nested Loop with no inner index** is `O(outer × inner)` — quadratic. Catastrophic at scale.
2. **Hash Join build side too big** spills to disk in batches. Look for `Batches: > 1` in EXPLAIN.
3. **Merge Join requires sorted inputs.** If neither side is sorted, a sort step is added — often nullifies the merge's benefit.
4. **Only equi-joins** can use hash join. `ON a.x < b.x` falls back to nested loop.
5. **Anti / semi joins** have hash/merge variants too — same rules apply.
6. **Memoize (Postgres 14+)** wraps the inner of a nested loop with a cache; great for skewed outer keys.
7. **MySQL** had only Nested Loop until 8.0; 8.0.18 introduced Hash Join for inner joins.
8. **`enable_hashjoin = off`** etc. lets you experiment in a session — useful for diagnosing planner choices.

## Mental Model

```
┌───────────────────────────────────────────────────────────────────────────┐
│ NESTED LOOP                                                                │
│   for each outer row r:                                                    │
│       seek index of inner where key = r.key  →  yield matches              │
│   Cost: |outer| × log|inner|  (with index)  or  |outer| × |inner|  (no idx)│
│   Best when:  outer is SMALL.                                              │
└───────────────────────────────────────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────────────────────┐
│ HASH JOIN                                                                  │
│   Phase 1 (build): hash inner side into a table  H[k] = list of rows       │
│   Phase 2 (probe): for each outer row r, look up H[r.key]                  │
│   Cost: |inner| + |outer|                                                  │
│   Best when:  no useful index; inner fits in memory.                       │
│   Spill if inner > work_mem  → multi-batch hash.                           │
└───────────────────────────────────────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────────────────────┐
│ MERGE JOIN                                                                 │
│   Both sides sorted by key. Walk in parallel:                              │
│   if r.key < s.key: advance r; if >: advance s; if =: emit matches.        │
│   Cost: |outer| + |inner| + sort costs if not pre-sorted                   │
│   Best when:  both sides already sorted (indexed merge join).              │
└───────────────────────────────────────────────────────────────────────────┘
```

The planner picks based on its cost estimate for each strategy given current stats, `work_mem`, and available indexes. The candidate's job is to predict that pick.

## Why interviewers care
- Connects EXPLAIN reading to data-shape reasoning.
- Tests **memory model** (work_mem, sort spill).
- Reveals whether candidate understands **when adding an index changes the plan** — and when it doesn't.

## Common beginner confusion
- "Hash Join is always faster" — no; nested loop with index beats hash join for small outer + indexed inner.
- "Merge Join needs ORDER BY" — no, it needs the inputs to already be in sort order (e.g. via index scan).
- "MySQL has all three" — only since 8.0.18 (hash); merge join is rare or absent.
- "Spill to disk is fine" — it's correct but slow; consider raising `work_mem` for the session.

## Brute force approach
Always nested loop. MySQL pre-8.0 literally did this. Works for small data; quadratic at scale.

## Optimal approach
Let the planner pick — but design your indexes and `work_mem` to give it good options:
- For point-lookup joins (1 outer × many inner): nested loop + index on inner.
- For full-table joins (millions × millions): hash join with build side on the *smaller* table.
- For range joins or pre-sorted sources: merge join after a pre-aggregating subquery.

## Solution (SQL)

```sql
CREATE TABLE customers (id INT PRIMARY KEY, name TEXT);
CREATE TABLE orders (
  id INT PRIMARY KEY,
  customer_id INT REFERENCES customers(id),
  total NUMERIC
);
-- Scenario A: 100K customers, 10M orders, index on orders.customer_id.
-- Scenario B: same data, but no index on orders.customer_id.

-- Query:
SELECT c.name, COUNT(*) FROM customers c JOIN orders o ON o.customer_id = c.id
GROUP BY c.name;
```

Scenario A (with index):

```
Hash Join                                          ← Postgres picks Hash because
  Hash Cond: (o.customer_id = c.id)                    full-table join over 10M rows.
  ->  Seq Scan on orders  (10M rows)
  ->  Hash  (build side, 100K rows, 8 MB)
        ->  Seq Scan on customers
```

Scenario A but with a `WHERE c.id IN (5,7,42)`:

```
Nested Loop                                        ← only 3 outer rows; index seek
  ->  Seq Scan on customers (filter 3 rows)              on orders.customer_id wins.
  ->  Index Scan using ix_orders_cust on orders
        Index Cond: customer_id = c.id
```

Scenario B (no index on orders.customer_id):

```
Hash Join                                          ← same as A; index doesn't matter for full-table hash.
```

But scenario B with `WHERE c.id IN (5,7,42)`:

```
Hash Join                                          ← no inner index, falls back to hash even for small outer.
  ->  Seq Scan on orders (10M rows)                ← bad: scans whole orders table.
  ->  Hash  (3 rows)
```

## Step-by-step dry run

Imagine the data is staged in memory:

```
NESTED LOOP (Scenario A small outer):
  outer = [{id=5}, {id=7}, {id=42}]
  for each c in outer:
    index seek orders.customer_id = c.id  →  e.g. 100 rows for c.id=5
    emit (c.name, count) — actually counts later in HashAggregate

HASH JOIN (Scenario A full outer):
  Build: hash table H[id] = (id, name) for all 100K customers. ~8MB.
  Probe: scan 10M orders, look up H[customer_id], emit (name, ...).

MERGE JOIN (alternative if both indexed):
  Use ix_customers_id (PK) and ix_orders_cust to read both in sorted order.
  Walk both cursors; emit matches. No build phase needed.
```

## How to think aloud in the interview
1. *"Three physical algorithms — nested loop, hash, merge. Each is optimal in a different regime."*
2. *"Nested loop dominates when the outer side is small and the inner side has an index on the join key — `O(outer × log inner)`."*
3. *"Hash join dominates for full-table equi-joins. Build the smaller side; probe with the larger. Watch out for `work_mem` spill."*
4. *"Merge join needs both sides sorted — usually free if both have indexes on the join key. Common after pre-sorted subqueries."*
5. *"I'd predict the plan from the data: scenario A with `WHERE id IN (3 values)` → nested loop. Scenario A full join → hash."*

## Important takeaways
- Three algorithms; planner picks based on cost & memory.
- Nested loop = small outer + indexed inner.
- Hash join = full-table equi-join, no usable index.
- Merge join = both sides sorted (via index).
- Only equi-joins → hash. Theta-joins fall back to NL.
- Watch `Batches: > 1` for hash spill; consider raising `work_mem`.
- See `backend-data-prep/sql/03-query-optimization.md` "Join algorithms" for theory.

## Variants
1. **`Memoize` over nested loop** (PG14+) — adds an inner-side cache; helps when outer keys repeat.
2. **Parallel hash join** — workers each build local hash, then probe — sub-linear scaling.
3. **MySQL 8.0.18 hash join** — only for inner joins; older versions force nested loops.

## Revision notes

> **Join algorithm cram block**
> - Nested loop: O(outer × log inner) with index; quadratic without.
> - Hash join: O(outer + inner) + work_mem; equi-join only.
> - Merge join: O(outer + inner) + sort; both sides sorted.
> - Outer-small + indexed-inner → NL.
> - Full × full → Hash.
> - Both pre-sorted → Merge.
> - Hash spill: `Batches: > 1`; raise `work_mem`.
> - Theta-join (`<`, `>`) → no hash, no merge → NL only.
> - MySQL has hash only since 8.0.18.
> - Predict plan from data + indexes.
