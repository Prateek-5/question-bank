# MongoDB: Aggregation pipeline drill — stage ordering matters

## Source / Origin
- Bread-and-butter Mongo skills question. Asked at every Mongo-shop interview as a warm-up.
- Concept reference: `backend-data-prep/nosql/04-mongodb.md` (aggregation section).

## Why this question matters in interviews
A working aggregation pipeline shows you can *think in stages*. Most candidates can name the stages but **mis-order them**, costing 10–100× performance. Senior signal: you put `$match` first to use indexes, `$project` early to shrink documents, `$lookup` late, and you understand that the optimizer is *limited* — order is your responsibility.

## Concepts involved

### Syntax to lock in

```javascript
db.orders.aggregate([
  { $match:   { status: "PAID", createdAt: { $gte: cutoff } } },     // FILTER first — uses index
  { $project: { customerId: 1, total: 1, items: 1 } },                // shrink early
  { $unwind:  "$items" },                                              // explode arrays only when needed
  { $group:   { _id: "$items.sku", units: { $sum: "$items.qty" }, revenue: { $sum: { $multiply: ["$items.qty", "$items.price"] } } } },
  { $sort:    { revenue: -1 } },                                       // sort late, narrow set
  { $limit:   10 },                                                    // top-N
  { $lookup:  { from: "products", localField: "_id", foreignField: "sku", as: "p" } },
  { $unwind:  "$p" },
  { $project: { sku: "$_id", _id: 0, units: 1, revenue: 1, name: "$p.name" } }
]);
```

### Stage-by-stage cheat sheet

| Stage | Purpose | Performance hint |
|---|---|---|
| `$match` | Filter docs | **First** — uses indexes; can be pushed before `$sort` by optimizer |
| `$project` | Reshape / drop fields | Use early to shrink working set |
| `$addFields` / `$set` | Add computed fields | Cheap; combine with project |
| `$unwind` | Explode array to N docs | Expensive — defer until after $match |
| `$group` | Aggregate; the SQL GROUP BY | Memory limit 100 MB unless `allowDiskUse: true` |
| `$sort` | Order results | Uses index only if right after `$match`; otherwise in-memory or `allowDiskUse` |
| `$limit` | Top N | After sort; pushes down with $sort to use top-K |
| `$lookup` | Left join | Expensive, no real optimizer; do AFTER filtering |
| `$facet` | Multiple sub-pipelines in one pass | Useful for dashboards |
| `$out` / `$merge` | Materialize result | Pipeline terminator |

### Edge cases / interview traps

1. **`$match` after `$group`** — you've already done the expensive work; you should have filtered before.
2. **`$sort` before `$match`** — sorts everything, throws most of it away.
3. **`$lookup` before `$match`** — joins the whole world, then filters; catastrophic.
4. **`$unwind` early on a giant array** — N× document explosion; use `$filter` inside `$project` first if you can.
5. **`$group` memory** — 100 MB limit per stage; add `{ allowDiskUse: true }` to the aggregate call.
6. **`$lookup` performance** — no join optimizer; ensure the foreign field is indexed.
7. **Optimizer reorders, but not always** — `$match` can move before `$sort` automatically; `$lookup` can't be reordered. Don't trust; verify with `.explain()`.
8. **`$count` is sugar** for `$group + $project`; cheaper but still scans matched docs.

## Mental Model

> Pipeline = a conveyor belt. Each stage processes one doc at a time, hands the result to the next. Your job: **shrink the belt early**. Filter before transform. Filter before join. Reduce before sort.

```
   Documents
      │
      ▼  $match     ←── INDEX HERE — drop 99% of docs
      ▼  $project   ←── shrink each doc (drop unused fields)
      ▼  $unwind    ←── only if you must process array items
      ▼  $group     ←── reduce to summary; small output
      ▼  $sort      ←── sort the small output, not the input
      ▼  $limit
      ▼  $lookup    ←── enrich the survivors, not the whole input
      ▼
   Result
```

A common interview question: **"this pipeline is slow, what's wrong?"** The answer is almost always *stage ordering*.

## Why interviewers care

- **Tests query-optimizer literacy.** You know how the engine actually executes.
- **Reveals SQL muscle memory** — translating SELECT/WHERE/GROUP/JOIN/HAVING/ORDER/LIMIT into pipeline order proves you really understand both.
- **Reveals index awareness.** First `$match` that aligns with an index is where the win is.

## Common beginner confusion

- "Order doesn't matter; the optimizer fixes it." Partial truth — only some reorderings are safe; lookups and unwinds aren't moved.
- "$lookup is just a JOIN." It's a nested-loop join with no hash/merge variant.
- "$group with $sum is free." Memory-bounded to 100 MB unless you allow disk.
- "$project after $match is redundant." It cuts shape size moving down the pipeline — saves memory in subsequent stages.
- "$facet doubles cost." Single pass over input; useful for "summary + page" dashboards.

## Brute force approach

`db.orders.find(...)` then process in app code with JavaScript reduce/map/sort. Works for tiny data; explodes on the wire and in memory.

## Optimal approach

Use the pipeline; obey the conveyor-belt rule:
1. `$match` first — must use an index.
2. `$project` to drop unused fields immediately.
3. `$unwind` only on already-filtered docs.
4. `$group` to summarize.
5. `$sort` + `$limit` after group.
6. `$lookup` last (or never, if a denorm is cheaper).

## Solution (Mongo shell) — full SQL-to-pipeline mapping

Question: "Top-10 SKUs by revenue in the last 30 days, with product names."

```sql
-- SQL equivalent
SELECT p.name, oi.sku, SUM(oi.qty) AS units, SUM(oi.qty * oi.price) AS revenue
FROM   orders o
JOIN   order_items oi ON oi.order_id = o.id
JOIN   products p     ON p.sku       = oi.sku
WHERE  o.status = 'PAID' AND o.created_at >= NOW() - INTERVAL '30 days'
GROUP  BY p.name, oi.sku
ORDER  BY revenue DESC
LIMIT  10;
```

```javascript
db.orders.aggregate([
  // 1. WHERE — uses { status: 1, createdAt: 1 } compound index
  { $match: {
      status: "PAID",
      createdAt: { $gte: new Date(Date.now() - 30*24*3600*1000) }
  }},

  // 2. shrink projection
  { $project: { items: 1, _id: 0 } },

  // 3. explode line items
  { $unwind: "$items" },

  // 4. GROUP BY sku
  { $group: {
      _id: "$items.sku",
      units:   { $sum: "$items.qty" },
      revenue: { $sum: { $multiply: ["$items.qty", "$items.price"] } }
  }},

  // 5. ORDER BY + LIMIT
  { $sort: { revenue: -1 } },
  { $limit: 10 },

  // 6. JOIN — small set (10 rows), foreign field is indexed
  { $lookup: { from: "products", localField: "_id", foreignField: "sku", as: "p" } },
  { $unwind: "$p" },

  // 7. final shape
  { $project: { _id: 0, sku: "$_id", name: "$p.name", units: 1, revenue: 1 } }
], { allowDiskUse: true });
```

### Explain plan to ask for

```javascript
db.orders.explain("executionStats").aggregate([ ... ]);
// look for:
//   "stage": "IXSCAN"   ✓
//   "stage": "COLLSCAN" ✗  (need an index)
//   "$lookup" with "indexUsed": "<name>" ✓
```

### Bad pipelines and their fix

```javascript
// BAD: lookup first
[
  { $lookup: { from: "products", localField: "items.sku", foreignField: "sku", as: "p" } },
  { $match: { status: "PAID" } }
]
// FIX: match first, lookup last (as above)

// BAD: sort before match
[
  { $sort: { createdAt: -1 } },
  { $match: { status: "PAID" } }
]
// The optimizer DOES push match before sort here. But don't rely on it.

// BAD: $group before $match on a groupable column
[
  { $group: { _id: "$customerId", n: { $sum: 1 } } },
  { $match: { n: { $gt: 5 } } }
]
// This is correct! HAVING clauses run after GROUP. The bad pattern is when $match
// could have used a row-level predicate — those go first.
```

## Step-by-step dry run

```
Collection: orders (10M docs over last year)
Index: { status: 1, createdAt: -1 }

Query: top-10 SKUs by revenue, last 30 days, PAID only

Stage 1: $match → IXSCAN on {status, createdAt} → 600K docs
Stage 2: $project → still 600K docs, but each smaller (only `items` field)
Stage 3: $unwind → 3M item rows (avg 5 items/order)
Stage 4: $group → 12K SKUs, each with units/revenue
Stage 5: $sort → in-memory sort of 12K rows by revenue desc
Stage 6: $limit → 10 rows
Stage 7: $lookup → 10 round trips into products (PK index)
Stage 8: $unwind → 10 enriched rows
Stage 9: $project → final shape

Total work dominated by stage 3 (3M ephemeral rows) — that's the optimization target if needed.
Speed-up: precompute SKU rollups into a daily summary collection; the live pipeline becomes
a $match + $group over 30 small docs.
```

## How to think aloud in the interview

> "Stage order is the whole game. The pipeline is a conveyor belt — every doc that survives a stage costs memory and CPU in the next. So I start with `$match` to use an index, then `$project` to drop everything I won't touch later. `$unwind` is expensive — N× explosion — so I defer until after filtering. `$group` is the reducer; output is small. Sort and limit operate on the reduced set. `$lookup` last, joining only the 10 survivors.
>
> The two performance traps are `$lookup` and `$unwind` early — both blow up the working set before you've filtered it. I always run `.explain('executionStats')` and look for `IXSCAN` at stage 1 and reasonable `nReturned` along the way.
>
> For dashboards that hit this pipeline every page load, I'd precompute a daily rollup with `$out` or `$merge` to a `sku_daily` collection, then aggregate over 30 small docs at query time."

## Important takeaways

- **`$match` first, always.** Hit an index.
- **`$project` early.** Smaller docs = less memory downstream.
- **`$lookup` last.** It's a nested loop with no real optimizer.
- **`$unwind` only after filtering.** It's a doc-count multiplier.
- **`$group` is memory-bounded.** Use `{ allowDiskUse: true }` for big aggregations.
- **`$sort` near an index is free; otherwise expensive.** Top-K with `$sort + $limit` is the cheap pattern.
- **`$facet`** runs multiple sub-pipelines in one pass — great for dashboard summary + page.
- **Materialize with `$out`/`$merge`** when the same pipeline runs often.

## Variants

1. **`$bucket` / `$bucketAuto`** — histogramming; numeric or date buckets.
2. **`$facet` for summary + paged results** — "give me total count and the current page" in one pass.
3. **`$graphLookup`** — recursive joins; org chart, friend-of-friend.
4. **`$merge` for incremental rollups** — daily ETL into a precomputed collection.
5. **`$setWindowFields`** — windowed aggregations (running totals, rank); Mongo 5.0+.
6. **`$lookup` with pipeline form** — filter foreign rows before join; reduces working set.
7. **`$densify` + `$fill`** — fill missing time buckets for time-series.

## Revision notes

> **aggregation pipeline — 60s recap**
> - Order: `$match` → `$project` → `$unwind` → `$group` → `$sort` → `$limit` → `$lookup` → final `$project`.
> - `$match` MUST hit an index. Run `.explain('executionStats')` to verify IXSCAN.
> - `$project` early shrinks each doc through the pipeline.
> - `$lookup` is a nested loop — always last.
> - `$unwind` multiplies doc count — defer.
> - `$group` 100MB cap → use `allowDiskUse: true`.
> - `$sort + $limit` together = top-K optimization.
> - Precompute hot dashboards with `$out`/`$merge` rollups.
> - Optimizer reorders SOME stages; don't rely on it.
