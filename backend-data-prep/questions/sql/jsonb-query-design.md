# Postgres `jsonb` query design — `jsonb_path_ops` vs `jsonb_ops`, GIN choices

## Source / Origin
- Postgres docs: chapter on `jsonb`, GIN operator classes.
- `backend-data-prep/sql/05-indexing.md` — GIN section.
- Classic interview prompt: *"You have a `jsonb` column. Queries like `data @> '{"status": "active"}'` are slow. Walk me through indexing options."*

## Why this question matters in interviews
`jsonb` is now ubiquitous in Postgres (event payloads, audit logs, EAV-style customisation). Every backend team has a `jsonb` column. **Few engineers know GIN well**, and even fewer know `jsonb_path_ops` exists. The interviewer is testing:

1. Do you know **`json` vs `jsonb`** (don't use `json` for queryable data).
2. Do you understand **GIN indexes** — what they index and how.
3. Can you pick between **`jsonb_ops` (default)** and **`jsonb_path_ops`** based on the workload.
4. Do you know **when to extract to a column** instead.

This question is a **gateway to deeper "indexing strategy" conversations** that distinguish a database-fluent engineer from a casual user.

## Concepts involved

### Syntax to lock in

```sql
-- Column types: ALWAYS jsonb for queryable, json for opaque/storage-as-text
CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  payload JSONB
);

-- The default GIN — indexes every key AND every value
CREATE INDEX idx_events_payload_default
  ON events USING gin (payload);
-- Operator class: jsonb_ops (the default if you don't specify)

-- Path-ops GIN — only indexes "path = value" combinations
CREATE INDEX idx_events_payload_path
  ON events USING gin (payload jsonb_path_ops);

-- Expression GIN — index only a sub-path
CREATE INDEX idx_events_status
  ON events USING gin ((payload -> 'status'));

-- Btree on a specific extracted scalar (for equality on one key)
CREATE INDEX idx_events_user_id
  ON events ((payload ->> 'user_id'));
```

### Operators that use the GIN index

```
@>    "contains"          payload @> '{"status": "active"}'           ← always
<@    "is contained by"   payload <@ '{...big spec...}'                ← rare
?     "key exists"         payload ? 'user_id'                          ← jsonb_ops only
?|    "any key exists"     payload ?| ARRAY['a', 'b']                   ← jsonb_ops only
?&    "all keys exist"     payload ?& ARRAY['a', 'b']                   ← jsonb_ops only
@@    "jsonpath predicate" payload @@ '$.status == "active"'            ← both
@?    "jsonpath exists"    payload @? '$.items[*] ? (@.qty > 5)'        ← both
```

### `jsonb_ops` vs `jsonb_path_ops` — the choice

| Aspect | `jsonb_ops` (default) | `jsonb_path_ops` |
|---|---|---|
| Indexes | every key + every value as separate entries | only `(path, value)` pairs as a single hash |
| Index size | Larger (~2x typical) | Smaller (~50% smaller) |
| Supports `?`, `?|`, `?&` (key-exists ops) | YES | NO |
| Supports `@>` (containment) | YES | YES — usually faster |
| Workload sweet spot | Mixed: containment + key-exists checks | Pure `@>` containment lookups |

**Rule of thumb:** if all your queries are `data @> '{...}'`, use `jsonb_path_ops`. If you also do `data ? 'key'`, use the default `jsonb_ops`.

### Edge cases / interview traps

1. **`json` ≠ `jsonb`.** `json` is text-with-validation; `jsonb` is parsed binary. **Always `jsonb`** for anything queryable. `json` only for pure storage where you preserve key order/whitespace verbatim.
2. **`@>` operator requires GIN.** Without an index, every row is parsed and matched — O(N).
3. **Path-ops loses `?` operator.** If you've created a `jsonb_path_ops` index and run `WHERE payload ? 'user_id'`, the index is unused.
4. **Extraction operator semantics.** `->` returns `jsonb`, `->>` returns `text`. Indexes on `->>` are btree-friendly for equality/range; on `->` they're for further containment.
5. **GIN write amplification.** Every insert that touches a jsonb value parses it and writes multiple GIN index entries — typically 5-50x the data row size. Bulk inserts into a jsonb-with-GIN table can be slow; disable + rebuild for ETL.
6. **`fastupdate` and the pending list.** GIN has a pending list optimisation; concurrent reads can miss recently-written entries until the pending list is flushed. `gin_pending_list_limit` tunes this.
7. **Cardinality matters.** GIN works well when value cardinality is high (many distinct values). For boolean-like keys (`active: true/false`), GIN entries are huge bitmap-style lists; consider extracting to a column.
8. **`jsonb_path_ops` hash collisions.** Path-ops hashes the (path, value) pair to ~32 bits. Lookups can return false positives that are rechecked against the heap row — cheap but not free.

## Mental Model

### How GIN indexes jsonb

Imagine a flattened representation. Document `{"user": {"name": "Alice"}, "status": "active"}`:

```
With jsonb_ops (default):
  Index entries (one per key OR scalar):
    "user"
    "name"
    "Alice"
    "status"
    "active"

  → each entry holds a posting list of rows containing that key/value.
  Containment query @>'{"status": "active"}' must intersect posting lists
  for "status" AND "active", then recheck.

With jsonb_path_ops:
  Index entries (one per leaf path-value pair):
    hash("user.name", "Alice")
    hash("status",   "active")

  → containment query @>'{"status":"active"}' hashes the same pair,
  jumps directly to the posting list, rechecks.
  Smaller index, fewer posting lists to intersect, faster @>.
```

Visualised:

```
ROW 1:  {"status": "active", "user": {"name": "Alice"}}
ROW 2:  {"status": "active", "user": {"name": "Bob"}}
ROW 3:  {"status": "deleted", "user": {"name": "Carol"}}

jsonb_ops GIN:
  "status"  → [1, 2, 3]
  "active"  → [1, 2]
  "deleted" → [3]
  "user"    → [1, 2, 3]
  "name"    → [1, 2, 3]
  "Alice"   → [1]
  "Bob"     → [2]
  "Carol"   → [3]

Query payload @> '{"status":"active"}':
  intersect posting lists for "status" AND "active":
  [1,2,3] ∩ [1,2] = [1,2]
  recheck rows 1, 2 → both match. Return.

jsonb_path_ops GIN:
  hash("status","active")  → [1, 2]
  hash("status","deleted") → [3]
  hash("user.name","Alice")→ [1]
  hash("user.name","Bob")  → [2]
  hash("user.name","Carol")→ [3]

Query payload @> '{"status":"active"}':
  hash("status","active") → posting list [1, 2]
  recheck rows 1, 2 → both match. Return.
  Single lookup; no intersection.
```

## Why interviewers care

- `jsonb` is the **flex column** of modern Postgres apps; getting it wrong creates slow queries that span months.
- GIN indexes are the **second-most-important index type** after btree; signals depth beyond surface SQL.
- The path-ops vs jsonb-ops decision is a **classic "know the data" tuning conversation** — interviewers love hearing you measure index size and access patterns.
- The "extract to a column" alternative is the **schema-design call** — knowing when *not* to use jsonb.

## Common beginner confusion

- *"`json` and `jsonb` are interchangeable."* They aren't. `json` is stored as-is text; no indexing of its internals. `jsonb` is parsed binary; supports GIN, `@>`, jsonpath. **Always jsonb** unless you have a specific reason.
- *"GIN works like btree."* GIN is an inverted index — one index entry per token; rows form posting lists per token. Very different cost model.
- *"`@>` is always indexed."* Only if you have a GIN index covering it.
- *"Schema-less = no indexing needed."* The opposite. Schema-less data has *more* needs for thoughtful indexing because the planner has fewer statistics.
- *"Indexing the whole jsonb is best."* For most workloads, indexing a sub-path (`(payload -> 'status')`) is smaller and faster.

## Brute force approach

No index. `WHERE payload @> '{"status":"active"}'` does a sequential scan, parsing every row's jsonb to check. For 1M rows, hundreds of milliseconds; for 100M, infeasible. Some teams discover this only when the table grows.

## Optimal approach

**Decision tree:**

```
What are the actual queries?
├── Mostly `payload @> '{...}'` containment
│     └── jsonb_path_ops GIN (smaller, faster for this op)
├── Mix of `@>`, `?`, `?|`, `?&`
│     └── jsonb_ops (default) GIN
├── A single hot key, equality only (e.g., payload->>'user_id' = '42')
│     └── btree on the extracted expression
├── Range queries on a numeric field inside jsonb
│     └── btree on cast: ((payload->>'amount')::numeric)
└── Full-text inside a jsonb field
      └── GIN on tsvector(payload->>'description')
```

Pair the right index with the right operator. Then *measure*.

## Solution (PostgreSQL)

```sql
-- ============================================================
-- Schema + indexes
-- ============================================================
CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  payload JSONB NOT NULL
);

-- Scenario 1: workload is mostly containment lookups (`@>`)
CREATE INDEX idx_events_payload
  ON events USING gin (payload jsonb_path_ops);

-- Scenario 2: workload needs containment AND key-exists checks
DROP INDEX idx_events_payload;
CREATE INDEX idx_events_payload
  ON events USING gin (payload);              -- default jsonb_ops

-- Scenario 3: single hot key on the equality access path
CREATE INDEX idx_events_user_id
  ON events ((payload ->> 'user_id'));

-- Scenario 4: range on a numeric sub-field
CREATE INDEX idx_events_amount
  ON events (((payload ->> 'amount')::NUMERIC));

-- Scenario 5: index a sub-document (only the user object)
CREATE INDEX idx_events_user_gin
  ON events USING gin ((payload -> 'user') jsonb_path_ops);

-- ============================================================
-- Sample data
-- ============================================================
INSERT INTO events (payload) VALUES
  ('{"type":"order","user_id":"42","status":"active","amount":99}'),
  ('{"type":"refund","user_id":"42","status":"completed","amount":99}'),
  ('{"type":"order","user_id":"77","status":"active","amount":150}'),
  ('{"type":"order","user_id":"42","status":"cancelled","amount":40}');

-- ============================================================
-- Queries that use each index
-- ============================================================

-- Containment — uses jsonb_path_ops or jsonb_ops GIN
EXPLAIN ANALYZE
SELECT * FROM events WHERE payload @> '{"user_id":"42","status":"active"}';
-- Bitmap Heap Scan
--   Recheck Cond: (payload @> '{...}')
--   ->  Bitmap Index Scan on idx_events_payload
--         Index Cond: (payload @> '{...}')

-- Key existence — needs jsonb_ops (default); jsonb_path_ops would seq-scan
EXPLAIN ANALYZE
SELECT * FROM events WHERE payload ? 'refund_reason';

-- Equality on extracted scalar — btree
EXPLAIN ANALYZE
SELECT * FROM events WHERE payload ->> 'user_id' = '42';

-- Range on numeric extracted — btree on cast
EXPLAIN ANALYZE
SELECT * FROM events WHERE (payload ->> 'amount')::NUMERIC > 100;

-- Jsonpath — uses GIN (both classes)
EXPLAIN ANALYZE
SELECT * FROM events
WHERE payload @? '$ ? (@.user_id == "42" && @.amount > 50)';
```

### Sizing comparison

```sql
SELECT pg_size_pretty(pg_relation_size('idx_events_payload')) AS index_size;

-- With jsonb_path_ops:  e.g. 38 MB for 1M rows
-- With jsonb_ops:       e.g. 72 MB for the same data
-- Btree on extracted ((payload->>'user_id')):  e.g. 18 MB (much smaller, single key)
```

## Step-by-step dry run

Query: `WHERE payload @> '{"status":"active","user_id":"42"}'` over 1M rows.

**Without index:**
```
Postgres reads heap row by row.
For each row, parses payload as jsonb, runs containment check.
1M parse+check operations.
Wall time: ~5-15s depending on row size.
```

**With `jsonb_ops` GIN:**
```
1. Planner sees @> can use GIN.
2. GIN lookup for "status" → posting list of rows containing key "status" — say 800k rows.
3. GIN lookup for "active" → 200k rows.
4. GIN lookup for "user_id" → 990k rows.
5. GIN lookup for "42" → 5k rows.
6. Intersect all four posting lists → ~1k rows.
7. Bitmap heap recheck — fetch those 1k rows and rerun @> to filter false positives.
Wall time: ~20-100 ms.
```

**With `jsonb_path_ops` GIN:**
```
1. Planner sees @> can use GIN.
2. GIN lookup for hash("status","active") → 200k rows.
3. GIN lookup for hash("user_id","42")    → 250k rows.
4. Intersect → ~1k rows.
5. Bitmap heap recheck.
Wall time: ~10-40 ms — fewer lookups, fewer posting list intersections.
```

**With btree on `(payload->>'user_id')`:**
```
1. Planner sees equality on the extracted text — btree usable.
2. Btree lookup user_id='42' → ~250k rows.
3. Heap recheck filters by status='active'.
Wall time: depends on selectivity of user_id alone. Good if user_id is selective.
```

## How to think aloud in the interview

> "First, confirm: is this `jsonb` or `json`? `json` is unindexable text; the answer there is 'change the column type to jsonb' before anything else. Assuming `jsonb`:
>
> The default move is `CREATE INDEX ... USING gin (payload)` — the GIN with `jsonb_ops` operator class. It indexes every key and every value, supports `@>` and `?`/`?|`/`?&`.
>
> If queries are *only* `@>` containment — no key-existence checks — I switch to `jsonb_path_ops`. It only indexes leaf path-value pairs as hashes; index is half the size, containment is faster, and write amplification is lower. The cost is losing `?` operator support.
>
> If there's a single hot key — say `payload ->> 'user_id' = '42'` is 80% of queries — I'd extract that to a *real column* or at least an expression btree: `CREATE INDEX ON events ((payload->>'user_id'))`. Btree on a single extracted scalar is much smaller than a full GIN.
>
> Tradeoffs to flag:
> - GIN write amplification: 5-50x storage cost on each insert; bulk loads need `DROP INDEX` + `CREATE INDEX` after.
> - GIN pending list: writes are buffered; concurrent readers may miss recently-written entries until flushed.
> - Cardinality matters: low-cardinality keys (boolean) make terrible GIN entries; extract those.
>
> My typical setup: `jsonb_path_ops` GIN for general containment + a small handful of expression btrees on the hottest single keys."

## Important takeaways

- **Use `jsonb`, never `json`** for queryable data.
- **GIN is the right index** for jsonb containment queries.
- **`jsonb_path_ops`** is smaller and faster for pure `@>` workloads; loses `?`, `?|`, `?&`.
- **`jsonb_ops`** (default) supports the full operator set.
- **Expression btree** on an extracted scalar (`(payload->>'key')`) is much smaller for single-key equality.
- **GIN has 5-50x write amplification** vs the row size.
- **`->` vs `->>`** — jsonb vs text result type. Pick the right one for indexing.
- **Hot single keys belong in real columns** — schema-less is for the long tail.

## Variants

1. **Index a sub-path:** `CREATE INDEX ... USING gin ((payload -> 'metadata') jsonb_path_ops)` — smaller index on a slice of the document.
2. **Functional unique constraint:** `CREATE UNIQUE INDEX ON events ((payload ->> 'tenant_id'), id)` — enforce per-tenant uniqueness without extracting the column.
3. **Generated column:** `tenant_id TEXT GENERATED ALWAYS AS (payload ->> 'tenant_id') STORED` + btree index — cleaner queries, same storage cost.
4. **Multicolumn GIN with btree_gin extension:** `CREATE EXTENSION btree_gin; CREATE INDEX ON events USING gin (tenant_id, payload jsonb_path_ops)` — composite key where one column is text and the other is jsonb.
5. **`gin_pending_list_limit` tuning** for write-heavy tables.
6. **Jsonpath `@@` and `@?`** — SQL/JSON Path support (Postgres 12+); newer than `@>` but expressive.
7. **`jsonb_to_record` / `jsonb_populate_record`** — for cases where you need columnar access in a query without persistent extraction.

## Revision notes

> **jsonb query design — 60 second recap**
> - Always `jsonb`, never `json` (unless storage-only).
> - **GIN with `jsonb_path_ops`** for pure `@>` workloads — smaller, faster.
> - **GIN with `jsonb_ops`** (default) — supports `?`, `?|`, `?&` too.
> - **Btree on `(payload ->> 'key')`** for hot single-key equality.
> - **Expression GIN on `(payload -> 'sub')`** to index a slice.
> - GIN write amplification 5-50x — bulk inserts need drop+recreate.
> - `->` returns jsonb; `->>` returns text — pick deliberately.
> - Hot keys → extract to real columns or generated columns.
> - Measure: `pg_relation_size`, `EXPLAIN ANALYZE` with `BUFFERS`.
