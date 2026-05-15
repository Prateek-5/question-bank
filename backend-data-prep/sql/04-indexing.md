# Indexing

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

### Hash index

- O(1) equality lookup
- **No range support**, no ordering
- Postgres has hash indexes (rarely used, WAL-logged since v10)
- Mostly useful in in-memory engines (Redis, in-memory tables)

### GIN (Generalized Inverted iNdex)

- For multi-valued columns: arrays, JSONB, full-text vectors
- One leaf entry per element value → fast `@>` containment, full-text match
- Slower to update than B-tree

### GiST (Generalized Search Tree)

- Spatial data (PostGIS), nearest-neighbor, ranges
- Supports custom operator classes

### BRIN (Block Range INdex)

- Stores summary (min/max) per *range of blocks*
- Tiny disk footprint
- Great for **append-only** tables where data is naturally sorted on disk (time-series, logs)
- Useless if data is randomly distributed

### Clustered vs non-clustered (MySQL InnoDB)

- **Primary key = clustered index**: the table data is *physically stored* in the order of the PK. Looking up by PK reads the leaf page directly (no extra hop).
- **Secondary index**: stores the PK as the row pointer. Looking up by a secondary index does **2 lookups**: secondary → PK → row.
- → Pick a small, monotonic PK. Random UUIDs as PK = page splits + index bloat.

Postgres has no clustered index by default. All indexes are secondary. `CLUSTER` can physically reorder a table but it's a one-shot operation.

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

### Covering indexes (index-only scans)

If an index contains *all columns referenced by the query* — including SELECTed columns — the database can answer the query without touching the heap.

```sql
CREATE INDEX idx_orders_cover ON orders (user_id) INCLUDE (total_cents, status);

SELECT total_cents, status FROM orders WHERE user_id = 42;
-- Index-only scan: never touches the table
```

`INCLUDE` columns are stored at the leaf level but not used in the sort key.

Postgres requirement: the visibility map must say the page is "all visible" (no recent writes); otherwise it falls back to heap fetch.

### Partial indexes

Index only rows matching a predicate. Smaller, faster.

```sql
CREATE INDEX idx_orders_open ON orders (created_at) WHERE status = 'OPEN';
```

Good for skewed distributions where most rows have the same value (e.g., 99% `status='ARCHIVED'`).

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

### Common misconceptions

- "More indexes is always better" — no, every index slows writes
- "Index will be used because it exists" — only if predicates align with leading columns
- "Composite index = same as two separate indexes" — no
- "Sequential scan is always bad" — fine on small tables; sometimes faster than millions of random reads
- "Index size doesn't matter" — index size determines how much fits in shared_buffers → cache hit rate

### Interview traps

1. **Column order in composite index** — interviewer reverses the columns and asks "does the query still use the index?" Equality-first rule.
2. **MySQL clustered PK choice** — they'll ask why UUID v4 is a bad PK in InnoDB. Random insertions cause page splits, write amplification, large secondary indexes (since secondary stores PK).
3. **Index size on disk** — interviewer asks how big a B-tree is. Typically ~2-3% of table size for narrow indexes, can balloon for wide ones.
4. **Why an existing index isn't used** — be ready with the 7 reasons above.
5. **The "include vs key column" distinction** — `INCLUDE` columns don't help with `WHERE` but enable index-only scan.

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
