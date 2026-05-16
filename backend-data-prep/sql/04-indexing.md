# Indexing

> **Teaching frame (read this first).** Indexes are the *alphabetical thumb-cuts* on a paper dictionary. The dictionary itself (the heap / table) holds the full word definitions in some order — possibly random, possibly grouped by date of entry. The thumb-cuts are a smaller, sorted, navigable structure that tells you *roughly where to flip to*. The dictionary works without thumb-cuts; it is just unbearably slow.
>
> Every concept in this file is a refinement of that picture:
> - A **B-tree** is alphabetical thumb-cuts that get progressively more specific.
> - A **hash index** is a phone book — straight from name to phone, but you can't ask "names starting with M".
> - A **covering index** is a thumb-cut that *also* prints the definitions on the cut, so you never open the dictionary.
> - A **composite index** is "by last name, then first name, then middle initial" — and only useful in that order.
> - A **partial index** is a thumb-cut that *only* indexes the words your team uses ("medical terms only").
>
> Keep this dictionary image in your head. Every confusing edge case becomes obvious through it.

## Mental model: the index as a separate sorted ladder

The single most important picture:

```
   Heap (table)               Index (B-tree on user_id)
   --- unordered ---          --- sorted by user_id ---
   page 17:  ... row(user=42) <--+
   page 99:  ... row(user=7)  <--|----+
   page 03:  ... row(user=42) <--|----|----+
   page 88:  ... row(user=99) <--|----|----|---+
                                 |    |    |   |
                              [ 7 -> (99) ]
                              [ 42 -> (17), (03) ]
                              [ 99 -> (88) ]
```

Two structures, kept in sync. Reads use the small sorted structure; writes have to update *both*.

This single picture explains:
- Why reads get faster: walk a tiny sorted ladder, then one jump.
- Why writes get slower: every insert/update may need to touch *every* index.
- Why a covering index avoids the jump: the answer is already on the ladder.
- Why a clustered index *is* the heap: the ladder *is* the dictionary.

## Why interviewers care

Indexing is the single highest-leverage skill the database tests because it sits at the intersection of:

1. **Data-structure fluency** (B-tree, hash, bitmap — CS fundamentals).
2. **Production performance** (knowing what slows reads vs writes).
3. **Trade-off thinking** (every index is a tax on writes and a discount on reads — explain *which* you're paying for).
4. **System-design judgement** (the index strategy on the OLTP database, the secondary index strategy on the search engine, the partition key on the data warehouse).

A candidate who can sketch a B-tree, explain *why* the leftmost-prefix rule exists, and reason about UUID-v4 page splits — without notes — is unambiguously senior.

## First principles: why O(log N) and not O(N)

Walk through the math once. A B-tree node fits in one page (8 KB or 16 KB). Suppose each node holds ~200 keys + pointers. Then:

- Height 1: 200 keys.
- Height 2: 200 × 200 = 40,000 keys.
- Height 3: 8 million.
- Height 4: 1.6 *billion*.
- Height 5: 320 billion.

So even a *billion-row* index has height ~4. A lookup touches ~4 pages. At 100µs per random SSD page, that's ~400µs — versus a sequential scan of 1 billion rows touching maybe 12 million pages = ~1200 seconds. **Six orders of magnitude.**

This is why every backend engineer needs to internalise: an index turns "minutes" into "microseconds" by collapsing the height of the search.

## Progressive concept building

We will move through indexing in three layers:

1. **The shape:** what is an index physically? (B-tree, leaves, pointers.)
2. **The match:** when can the index be used? (Leftmost-prefix, equality vs range, function on column.)
3. **The economy:** what does it cost? (Write amplification, disk size, cache pressure.)

Confusion at any layer comes from mixing the layers. Keep them straight.

## Why this matters in backend interviews

- **Most-asked database question across all backend SDE2 interviews.** Expect at least one question per round.
- **Machine coding**: you'll need to add the right indexes after writing the schema. Interviewers grade this.
- **System design**: indexing strategy is part of any database design discussion (sharding key, secondary indexes, hot keys).
- **Debugging**: 90% of slow queries are missing-index or wrong-index-used problems.

This file is the single highest-ROI revision file in the kit. Re-read it the night before any interview.

---

## Core concepts

### What an index is

An index is a **separate, sorted data structure** that maps column values to row locations. The table itself is unordered (heap in Postgres) or ordered by primary key (clustered in InnoDB).

#### Mental model — an index is a "shortcut book"

You have a phone book (the heap). It is too big to skim. Your shortcut book lists "letter → starting page". Inside each section, you have a tinier shortcut to letter pairs. That recursive shortcut is a B-tree.

The shortcut book is **independent of the phone book**, but every change to the phone book has to update the shortcut book too — otherwise your shortcuts will point to the wrong page.

Cost / benefit trade-off:
- **Pro:** SELECT becomes O(log N) instead of O(N)
- **Con:** INSERT / UPDATE / DELETE must also update the index — 5–30% write slowdown per index
- **Con:** Disk + memory cost
- **Con:** Sometimes a write touches the indexed column → re-index that row

### B-tree (the default)

A balanced multi-way tree. Each node fits in ~1 disk page (8 KB Postgres / 16 KB InnoDB). Fanout is typically several hundred → height is **3–5 levels even for billions of rows**.

```
              [50 | 100]
             /    |     \
       [..., 50] [..., 100] [..., 200]
       /  |  \     |   \      |   \
      leaf pages with sorted (key, ptr) pairs
      (leaves are doubly linked → range scans are cheap)
```

Key properties:
- Sorted → supports `=`, `<`, `>`, `BETWEEN`, `ORDER BY`, prefix-`LIKE`
- O(log N) lookup
- Range scans walk the leaf level — very efficient

#### Step-by-step: tracing a B-tree lookup for `WHERE id = 137`

Imagine an index of ~1 million IDs.

```
ROOT page:
   keys:   [ 250 | 500 | 750 ]
   ptrs:    A     B     C     D     (4 child pointers; A holds keys <=250)
                                    |
                            id=137 lies in A (137 <= 250)

INTERNAL page A:
   keys:   [ 100 | 200 ]
   ptrs:    a1    a2    a3          a1 holds keys <=100; a2 holds 101..200
                                    |
                            id=137 lies in a2 (101..200)

LEAF page a2 (sorted entries):
   [ 101 -> tid17, 102 -> tid03, ..., 137 -> tid88, ..., 200 -> tid71 ]
   |---------- doubly linked to neighbour leaves ----------|
                                    |
                            id=137 -> heap tuple at TID 88
```

Three page reads, one heap fetch. Total: ~4 page reads. With shared_buffers caching the upper levels (root and internal pages are tiny and hot), the *amortised* cost in production is closer to 1-2 page reads.

For a range query `WHERE id BETWEEN 137 AND 145`, you locate `137` the same way, then **walk the leaf chain rightward** until you exit the range. That's why B-tree range scans are so cheap.

#### ASCII diagram — heap pointers from leaves

```
   Index Leaves                Heap Pages
   ---------------             ----------------------
   ...                         page 17: | r | r | r | r |
   137 -> (page 88, slot 4) -->|               ^         
   138 -> (page 17, slot 3) ---+----------+    |  slot 4
   ...                                    |    |  for tid=(17,3)
                                          v
                              page 88: | r | r | r | row{137} | ...
```

Each leaf entry is `(indexed key, heap TID = (page, slot))`. The "extra hop" from leaf → heap is what an *index-only scan* skips when the index covers the query.

### Hash index

- O(1) equality lookup
- **No range support**, no ordering
- Postgres has hash indexes (rarely used, WAL-logged since v10)
- Mostly useful in in-memory engines (Redis, in-memory tables)

#### Mental model — hash index as a phone book by exact name

A phone book lets you find "Alice Smith" in O(1), but it cannot answer "everyone whose surname starts with S" — the entries are scattered by hash bucket, not sorted alphabetically. That single limitation is *why* B-tree won the default-index war: it can do everything hash can, plus ranges and ordering, at the cost of one extra log-factor on lookups.

Use hash only when:
- You *only* do equality lookups, never ranges or sorts.
- The values don't hash well into a B-tree (e.g., huge text blobs where a hash is much smaller than the value).
- You're in an in-memory engine where O(1) really is faster than O(log N).

### GIN (Generalized Inverted iNdex)

- For multi-valued columns: arrays, JSONB, full-text vectors
- One leaf entry per element value → fast `@>` containment, full-text match
- Slower to update than B-tree

#### Mental model — GIN as "index of words to documents"

A GIN index is *exactly* a search-engine inverted index. If a JSONB document is `{"tags": ["red", "fast"]}`, GIN stores:

```
   "red"  -> [doc1, doc3, doc99, ...]
   "fast" -> [doc1, doc7, ...]
```

So `WHERE tags @> '["red"]'` becomes "look up `red`, get the doc list, done". Each *element* of the array gets an entry, which is why inserts/updates are expensive: a row with 100 tags writes 100 index entries.

### GiST (Generalized Search Tree)

- Spatial data (PostGIS), nearest-neighbor, ranges
- Supports custom operator classes

### BRIN (Block Range INdex)

- Stores summary (min/max) per *range of blocks*
- Tiny disk footprint
- Great for **append-only** tables where data is naturally sorted on disk (time-series, logs)
- Useless if data is randomly distributed

#### Mental model — BRIN as "section summaries"

Imagine a 1000-page diary. A BRIN index says: "pages 1-10 cover Jan 1-10; pages 11-20 cover Jan 11-20; ...". If you ask "find entries from Feb 5", BRIN immediately knows which 10-page section to scan. The index itself is microscopic — a few KB for a 100 GB time-series table — but it only helps if entries are written in time order. Insert a January entry on page 950 and the section summary for that page becomes "Jan-Sep", and BRIN's selectivity collapses.

### Clustered vs non-clustered (MySQL InnoDB)

- **Primary key = clustered index**: the table data is *physically stored* in the order of the PK. Looking up by PK reads the leaf page directly (no extra hop).
- **Secondary index**: stores the PK as the row pointer. Looking up by a secondary index does **2 lookups**: secondary → PK → row.
- → Pick a small, monotonic PK. Random UUIDs as PK = page splits + index bloat.

Postgres has no clustered index by default. All indexes are secondary. `CLUSTER` can physically reorder a table but it's a one-shot operation.

#### ASCII diagram — clustered vs heap+secondary

```
   InnoDB clustered (PK lookup, 1 hop):

       PK B-tree
       ----------
       [ 1 ] [ 2 ] [ 3 ] ... [ 99 ]
         |     |     |          |
         v     v     v          v
       full row stored AT THE LEAF
       (no separate heap)


   Postgres heap + secondary index (2 hops):

       Index B-tree on email
       ---------------------                       Heap
       [ 'a@x' -> tid(17,3) ]  -------- jump --->  page 17, slot 3: { id=42, name=..., ... }
       [ 'b@y' -> tid(99,1) ]


   InnoDB secondary index (2 hops via PK):

       Index B-tree on email
       ---------------------                       Clustered PK tree
       [ 'a@x' -> pk=42 ]  ------- jump --->       walk root->leaf for pk=42  -> full row
```

The "2 hops" of an InnoDB secondary index is why a *covering* secondary index is so valuable in InnoDB: you avoid the second walk into the PK tree.

### Composite indexes

`CREATE INDEX ON orders (user_id, created_at DESC, status);`

Key rule (the **Equality → Range → Sort** rule):
- Columns used with `=` come first
- Then range columns (`>`, `<`, `BETWEEN`)
- Then `ORDER BY` columns (matching direction)

Why: B-tree is sorted by the leading column first, then by the second, etc. A query that uses `user_id = ?` can binary-search to the right block; one that filters only on `created_at` can't (no leading column).

#### Index usage rules
- `WHERE user_id = ?` → uses index ✓
- `WHERE user_id = ? AND created_at > ?` → uses index ✓
- `WHERE user_id = ? AND status = ?` → uses index but can't use `status` until a range column appears
- `WHERE created_at > ?` → **doesn't use index** (no leading column) ✗
- `WHERE status = ?` → doesn't use index ✗

#### Mental model — composite index as a phone book "by last name, then first name"

A phone book sorted by last name then first name supports:
- "Find Smith, John" — fast (binary search by last, then by first).
- "Find all Smiths" — fast (range scan of one Smith block).
- "Find all Johns" — *slow* — the Johns are scattered across every last-name block.

This is the **leftmost-prefix rule** in plain English: you can search by `(last)`, by `(last, first)`, but not by `(first)` alone — the data isn't grouped by first.

#### ASCII diagram — leftmost-prefix matching on `(user_id, created_at, status)`

```
   Index leaves (sorted by user_id, then created_at, then status):

   [ (u=1, t=2025-01-02, 'PAID')  ]
   [ (u=1, t=2025-01-09, 'OPEN')  ]
   [ (u=1, t=2025-02-15, 'PAID')  ]    <-- all u=1 contiguous
   [ (u=2, t=2025-01-05, 'PAID')  ]
   [ (u=2, t=2025-03-10, 'OPEN')  ]    <-- then all u=2 contiguous
   [ (u=3, t=...) ]
   ...

   - WHERE u=1                 :  scan one contiguous block (FAST)
   - WHERE u=1 AND t > '2025-02-01' :  binary-seek inside u=1 (FAST)
   - WHERE t > '2025-02-01'    :  rows scattered across every u=*  (SLOW; index unusable as a seek)
   - WHERE status='PAID'       :  scattered everywhere (SLOW)
```

This picture *is* the leftmost-prefix rule. Internalise it and you will never confuse which composite index a query can use.

#### Common beginner confusion: "ORDER BY uses a different column from WHERE"

Suppose `INDEX(user_id, created_at DESC)`.

- `WHERE user_id = 42 ORDER BY created_at DESC LIMIT 50` → perfect. Index pre-sorts within `user_id=42`.
- `WHERE user_id = 42 ORDER BY created_at ASC LIMIT 50` → in older versions had to do a sort; modern planners can scan backwards.
- `ORDER BY created_at DESC LIMIT 50` (no WHERE) → index *not* helpful for the sort — within each `user_id` block the dates are sorted, but the global order is by `user_id` first.

The fix is either to add `user_id` to the WHERE (the common case) or to create a separate `INDEX(created_at DESC)` for global sorts.

### Covering indexes (index-only scans)

If an index contains *all columns referenced by the query* — including SELECTed columns — the database can answer the query without touching the heap.

```sql
CREATE INDEX idx_orders_cover ON orders (user_id) INCLUDE (total_cents, status);

SELECT total_cents, status FROM orders WHERE user_id = 42;
-- Index-only scan: never touches the table
```

`INCLUDE` columns are stored at the leaf level but not used in the sort key.

Postgres requirement: the visibility map must say the page is "all visible" (no recent writes); otherwise it falls back to heap fetch.

#### Mental model — covering index as "everything in one drawer"

A regular index says "the answer is on shelf 17". A covering index says "the answer *is in this drawer*; don't bother with the shelf". You eliminate the second jump entirely — the heap visit. On hot-path queries (dashboard counters, inventory lookups, auth checks), a covering index is often the difference between 200µs and 10ms.

Cost: the index gets bigger (every included column is duplicated at the leaf level). Don't `INCLUDE` columns that are 10 KB blobs.

#### Step-by-step: index-only scan vs index scan vs sequential scan

For `SELECT total_cents FROM orders WHERE user_id = 42`:

1. **Sequential scan** — read every page of `orders`, filter by `user_id=42`. Touches *all* heap pages. Cost ~ rows / page_size.
2. **Index scan** — walk B-tree on `user_id` → find leaf with `42` → for each matching leaf entry, jump to the heap to read `total_cents`. Cost ~ log(N) + (matching rows × 1 random page).
3. **Index-only scan** — same as (2), but if the index already contains `total_cents` (covering / `INCLUDE`) and the visibility map says "page all visible", *don't* jump to the heap. Cost ~ log(N) + sequential leaf walk.

The performance ladder is roughly:

```
   index-only      :   1x       (baseline: a few page reads)
   index scan      :   5-100x   (heap jumps; depends on rows matched and cache)
   sequential scan :  100-1000x (when selective predicates aren't selective enough)
```

### Partial indexes

Index only rows matching a predicate. Smaller, faster.

```sql
CREATE INDEX idx_orders_open ON orders (created_at) WHERE status = 'OPEN';
```

Good for skewed distributions where most rows have the same value (e.g., 99% `status='ARCHIVED'`).

#### Mental model — partial index as "only the cards we actually flip to"

If 99% of orders are `ARCHIVED` and your hot query is "find OPEN orders for retry", indexing all 100M rows is wasteful — you'd be storing 99M entries you never use. A partial index on `WHERE status = 'OPEN'` stores only the 1M relevant entries: smaller, hotter in cache, faster to update.

### Functional / expression indexes

```sql
CREATE INDEX idx_users_lower_email ON users (LOWER(email));
SELECT * FROM users WHERE LOWER(email) = 'foo@bar.com';  -- uses index
```

Without this, `WHERE LOWER(email) = …` does a seq scan even with an index on `email`.

### Multi-column vs multiple single-column indexes

- A composite index is *much* better than two single-column indexes when you query multiple columns together.
- Multiple single-column indexes can be combined via **Bitmap And/Or** but each lookup is independent and slower than one composite scan.

### Index-organized tables (Oracle / SQL Server clustered)

The data *is* the index. PK lookup is direct. Bigger leaves (whole row) → range scans pay more I/O.

### Indexes don't help when…

1. Predicate has a function on the indexed column (without functional index)
2. Implicit type cast (e.g., `varchar` indexed col compared to integer)
3. `LIKE '%abc%'` (leading wildcard)
4. `<>` or `NOT` on a column
5. The query returns most of the table (low selectivity → seq scan wins)
6. Stats are stale → planner mis-estimates
7. Sort order in `ORDER BY` doesn't match index direction (mixing `ASC`/`DESC`)
8. Boolean columns with skewed distribution (use partial index)

#### Write amplification: the cost no one mentions

Every `INSERT` must add a leaf entry to *every* index on the table. Every `UPDATE` that touches an indexed column must delete the old entry and insert the new one. Every `DELETE` must mark the entries dead (and eventually have them vacuumed).

Concretely, on a table with 8 indexes:

- **1 insert** = 9 page touches (heap + 8 indexes) + WAL writes for each.
- **1 update of an indexed column** = ~2 page touches per affected index + heap.
- **Random-key inserts** (UUID v4) = each insert hits a *random* B-tree leaf → cache misses + page splits.

The classic senior interview move: "I'd add this index, but first let me check how write-heavy the table is and how many indexes already exist. Adding the ninth index will cost ~10% on write p99."

#### When NOT to index

- Tiny tables (under a few hundred rows) — seq scan is free.
- Columns with very low cardinality and no skew (e.g., `gender` with 2-3 values evenly distributed). The index will rarely be selective enough to win.
- Columns that are updated on every row update (very write-heavy hot column). The write penalty dominates.
- Columns the query never filters or joins on. Yes, this is obvious — but ORM-generated indexes and copy-pasted schemas often violate it.
- Wide / large columns (long text). Index entries become big, fanout drops, height grows. Use a hash or functional index instead.

### Common misconceptions

- "More indexes is always better" — no, every index slows writes
- "Index will be used because it exists" — only if predicates align with leading columns
- "Composite index = same as two separate indexes" — no
- "Sequential scan is always bad" — fine on small tables; sometimes faster than millions of random reads
- "Index size doesn't matter" — index size determines how much fits in shared_buffers → cache hit rate

#### Common beginner confusion

- *"I added an index on every column 'just in case'."* → That's 8-15 indexes; you've just made every insert ~10x slower than necessary. Indexes are *deliberate*; design them to match real queries.
- *"My column has a million distinct values, so the index will be highly selective."* → High cardinality is necessary but not sufficient. If you query with a function (`LOWER(col)`) or wildcard prefix, the index still won't help.
- *"My column has only 'true/false', so an index is useless."* → If the distribution is 99% true and your query is `WHERE flag=false`, a *partial index* on `WHERE flag=false` is tiny and perfect.
- *"ORDER BY needs an index in the same direction."* → Not strictly. Postgres can scan B-tree backwards. But mixed-direction `ORDER BY a ASC, b DESC` does need a matching `(a ASC, b DESC)` index (or accept a sort).
- *"Index-only scan means I never touch the heap."* → In Postgres, you still touch the visibility map. If the page isn't marked all-visible (recent writes), it falls back to a heap fetch. Frequent updates can quietly disable index-only scans until the next vacuum.

### Interview traps

1. **Column order in composite index** — interviewer reverses the columns and asks "does the query still use the index?" Equality-first rule.
2. **MySQL clustered PK choice** — they'll ask why UUID v4 is a bad PK in InnoDB. Random insertions cause page splits, write amplification, large secondary indexes (since secondary stores PK).
3. **Index size on disk** — interviewer asks how big a B-tree is. Typically ~2-3% of table size for narrow indexes, can balloon for wide ones.
4. **Why an existing index isn't used** — be ready with the 7 reasons above.
5. **The "include vs key column" distinction** — `INCLUDE` columns don't help with `WHERE` but enable index-only scan.

---

## Interview storytelling: designing indexes for a hot path

When asked "design indexes for the `orders` table", a strong walkthrough sounds like:

1. *"First, what are the top 3-5 queries on this table? Are we read-heavy or write-heavy? Are there any reporting queries that should go to a replica?"*
2. List the queries. For each, write down the WHERE / JOIN / ORDER BY columns and the SELECT columns.
3. Apply Equality → Range → Sort to design composite indexes, *one per query shape*, and prefer fewer indexes that cover multiple shapes via leftmost-prefix.
4. Decide if any are worth making *covering* via `INCLUDE` — only if the SELECT list is small and reads dominate.
5. Sanity-check the write penalty: "we'll have N indexes; on this 10k-write/sec table that's a budget of M extra pages/sec; acceptable?"
6. Mention rollout: `CREATE INDEX CONCURRENTLY`, monitoring `pg_stat_user_indexes` after a week to drop unused ones.

Follow-up the interviewer *will* ask: *"Now there are 100 million rows and 10x the writes. What changes?"* — your answer mentions partitioning, BRIN on cold partitions, replica routing for analytics, async secondary indexes, and possibly moving the FTS / JSONB workload to a dedicated engine.

---

## Real examples

### E-commerce — order lookup hot path
```sql
-- Common queries:
-- 1) recent orders for a user
-- 2) all PAID orders in a date range for finance
-- 3) order detail by id

CREATE INDEX idx_orders_user_created   ON orders (user_id, created_at DESC);
CREATE INDEX idx_orders_paid_created   ON orders (created_at) WHERE status = 'PAID';
-- PRIMARY KEY (id) already gives id lookup
```

### Inventory — stock check with covering index
```sql
CREATE INDEX idx_products_sku_qty ON products (sku) INCLUDE (qty_on_hand);
SELECT qty_on_hand FROM products WHERE sku = 'A1';
-- Index-only scan; no heap fetch
```

### Chat — last messages per conversation
```sql
CREATE INDEX idx_messages_conv_sent ON messages (conv_id, sent_at DESC);
-- Supports:
--   SELECT * FROM messages WHERE conv_id = ? ORDER BY sent_at DESC LIMIT 50;
-- And:
--   SELECT * FROM messages WHERE conv_id = ? AND sent_at > ?;
```

### Audit log — high write, range queries
```sql
-- Append-only, time-ordered
CREATE INDEX idx_audit_brin_ts ON audit_log USING brin (ts);
-- A few KB instead of GB
```

### Search — case-insensitive email
```sql
CREATE UNIQUE INDEX idx_users_lower_email ON users (LOWER(email));
```

### JSONB — Postgres GIN
```sql
CREATE INDEX idx_users_data_gin ON users USING gin (data jsonb_path_ops);
SELECT * FROM users WHERE data @> '{"role":"admin"}';  -- uses GIN
```

---

## Common interview questions

1. How does a B-tree index work?
2. Why is the column order in a composite index important?
3. Difference between clustered and non-clustered index.
4. What is a covering index / index-only scan?
5. When would the database choose NOT to use an index even if one exists?
6. Difference between B-tree, hash, GIN, GiST, BRIN.
7. UUID vs auto-increment PK — pros and cons.
8. How do you index a JSON column?
9. How would you support full-text search?
10. What's a partial index? When useful?
11. How do indexes affect write performance?
12. Why is `LIKE '%abc%'` slow and how to fix it?

---

## Detailed answers

### 1. B-tree
A self-balancing tree where each node fits a disk page. Internal nodes contain keys + pointers to children; leaves contain the indexed values and row IDs (Postgres TID or InnoDB PK). Leaves are doubly linked → range scans are O(range size + log N). Height is small (3-5) → at most a few page reads to find a key.

### 2. Composite index column order
The leading column must be used with equality (or range) for the index to be considered. Inside the index, rows are sorted lexicographically by (col1, col2, col3, …). Always order by:
1. Equality columns
2. Range columns
3. Sort columns matching ORDER BY

Bad: `(created_at, user_id)` for `WHERE user_id = ?` — leading column is wrong.

### 3. Clustered vs non-clustered
- Clustered: table data is physically stored in PK order (InnoDB, SQL Server). PK lookup → 1 read.
- Non-clustered (secondary): separate structure with key → row pointer. 2 reads to fetch row data.
- Postgres heap is unordered; no clustered. Some tables can be physically reordered with `CLUSTER` but it's not maintained.

### 4. Covering / index-only scan
An index that contains all columns the query needs. Database answers the query without touching the heap. Use `INCLUDE` to add non-key columns without growing the sort key.

### 5. Index not used despite existing
- Function on the column without functional index
- Implicit type cast
- Leading wildcard `LIKE '%x'`
- Low selectivity → seq scan cheaper
- Stale statistics
- ORDER BY direction mismatch
- Predicate uses inequality (`<>`)

### 6. Index types
| Type | Use case |
|---|---|
| B-tree | Default; equality + range + sort |
| Hash | Equality only; rarely useful |
| GIN | Multi-valued (JSONB, array, full-text) |
| GiST | Spatial, nearest-neighbor |
| BRIN | Naturally sorted, append-only data |
| Bitmap (planner-internal) | Combine multiple indexes for OR |

### 7. UUID vs auto-increment PK
- **Auto-increment**: small (8 bytes), monotonic → great for B-tree (writes append at right edge), tight clustered storage. Drawback: leaks ordering/count, predictable.
- **UUID v4**: 16 bytes, random → in InnoDB clustered: page splits everywhere, write amplification, fragmented secondary indexes.
- **UUID v7 (timestamp-ordered)**: 16 bytes but mostly monotonic → much better than v4. Recommended modern choice.
- Generally: use BIGINT auto-inc for internal IDs and an external opaque ID (UUID) for public exposure.

### 8. Index a JSON column
Postgres: `CREATE INDEX … USING gin (col jsonb_path_ops)` then `WHERE col @> '{"k":"v"}'`. Or functional index on a specific path: `CREATE INDEX ON users ((data->>'email'))`.

MySQL 8+: generated columns + index on the generated column.

### 9. Full-text search
Postgres: `tsvector` + GIN index, `to_tsvector(...) @@ to_tsquery(...)`. For real production, dedicated engines (Elasticsearch, OpenSearch, Meilisearch, Typesense) scale better. Discuss the trade-off: in-DB FTS = no separate system to sync; dedicated engine = much better ranking, language support, scale.

### 10. Partial index
Index only rows matching a predicate. Useful when most rows share a common value:
```sql
CREATE INDEX ON orders (created_at) WHERE status = 'OPEN';
```
Saves space, faster updates.

### 11. Write penalty
Every INSERT/UPDATE that touches an indexed column triggers an index update — random I/O, possibly page splits. Rule of thumb: 5–15% per index. A table with 10 indexes can be 2x slower to write. **Audit indexes regularly.**

### 12. `LIKE '%abc%'`
- Leading wildcard means the value can be anywhere → no sorted-prefix lookup possible
- Fixes:
  - `LIKE 'abc%'` if business logic allows
  - **Trigram index** (`pg_trgm` + GIN): supports substring matches
  - Full-text search index
  - Search engine (Elasticsearch)

---

## Practical coding examples

### Show index usage
```sql
-- Postgres
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 42;

-- Check index size
SELECT pg_size_pretty(pg_relation_size('idx_orders_user_created'));

-- Unused indexes (run after some time in production)
SELECT relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Concurrent index build (no table lock)
```sql
-- Postgres: avoids blocking writes
CREATE INDEX CONCURRENTLY idx_orders_status ON orders (status);

-- MySQL 5.6+: online DDL by default for most index types
ALTER TABLE orders ADD INDEX idx_status (status), ALGORITHM=INPLACE, LOCK=NONE;
```

### Find missing indexes by examining slow queries
```sql
SELECT query, calls, mean_exec_time, rows
FROM pg_stat_statements
WHERE query LIKE 'SELECT%' AND mean_exec_time > 100
ORDER BY total_exec_time DESC LIMIT 20;
```

### Compute exact selectivity
```sql
SELECT
  COUNT(*) FILTER (WHERE status = 'PAID')::float / COUNT(*) AS selectivity
FROM orders;
-- If < 10%, status is a good index candidate (often combined with other cols)
```

---

## Common mistakes

- Indexing every column "just in case"
- Composite index column order ignoring query shape
- Forgetting to vacuum/analyze → planner skips index
- Building large indexes during peak load (table lock)
- UUID v4 as clustered PK in InnoDB
- Indexing booleans / very low-cardinality columns without partial-index filter
- Missing `CREATE INDEX CONCURRENTLY` in production (blocks writes otherwise)
- Indexing soft-deleted rows; better: partial index `WHERE deleted_at IS NULL`

---

## Senior engineer discussion points

- **Hot vs cold data partitioning** — split a big table by time, BRIN-index the historical partitions
- **Index maintenance windows** — vacuum, reindex (`REINDEX CONCURRENTLY`), monitor bloat
- **Working set in shared_buffers** — hot indexes must fit in RAM
- **Cost of index on a write-heavy table** — measure with `pg_stat_user_tables`
- **Why DB indexes ≠ application indexes** — ORMs often don't manage indexes well; review and tune manually
- **Postgres `bloom` extension** — multi-column lookups where any subset can be queried
- **MySQL adaptive hash index** — InnoDB auto-builds in-memory hash for hot keys
- **Read-replica index strategy** — analytics queries get their own indexes that wouldn't be cost-effective on the primary
- **Online schema change tools** — gh-ost, pt-online-schema-change for MySQL

---

## Bridge back to Query Optimization

You now have both halves of the toolkit:

- The previous file (`03-query-optimization.md`) taught you to **read the plan** — find the bad node, identify the bad estimate, name the missing access method.
- This file taught you to **fix it** — choose the right index type, column order, and trade-off.

In an interview, you will move between them seamlessly: spot a seq scan with high `Rows Removed by Filter` → propose a composite index with the right Equality → Range → Sort order → predict the new plan switches to Index Scan → discuss the write-amplification trade-off → mention `CREATE INDEX CONCURRENTLY` for rollout. That whole arc, said calmly, is what a senior signal looks like.

---

## Revision notes

- B-tree = sorted, balanced, fanout in hundreds, height 3–5 for billions of rows
- **Equality → Range → Sort** column order for composite indexes
- Clustered (InnoDB PK) = table sorted by PK; secondary index has 2 hops
- Covering index = `INCLUDE` columns → index-only scan
- Partial index = `WHERE …` → skewed data
- Functional index = `(LOWER(email))` → matches `WHERE LOWER(email) = …`
- GIN for JSONB/array/full-text, GiST for spatial, BRIN for append-only
- Every index = 5–30% write penalty
- Leading wildcard = no index (use trigram/FTS)
- UUID v4 PK in InnoDB = bad (use v7 or auto-inc)
- `CREATE INDEX CONCURRENTLY` in production
- Validate: `EXPLAIN ANALYZE` after every change
