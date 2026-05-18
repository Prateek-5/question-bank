# Pagination — OFFSET vs Keyset (cursor) pagination

## Source / Origin
- Markus Winand's *Use The Index, Luke!* — chapter on pagination is the canonical reference.
- Companion concept: `backend-data-prep/sql/04-query-patterns.md` — "Pagination" section.
- LeetCode #1321 "Restaurant Growth", #1393 "Capital Gain/Loss" (both touch pagination indirectly).
- Classic prompt: *"You have a feed with 100 million rows. The `OFFSET 1000000 LIMIT 20` query is taking 4 seconds. What's wrong, and how do you fix it?"*

## Why this question matters in interviews
Pagination is **the most common system-design footgun in production backends**. Every shipping engineer has written `OFFSET ... LIMIT ...`; few have measured what happens at OFFSET 1 million. The interviewer wants to see:

1. You **understand why OFFSET is O(offset + limit)** — not O(limit).
2. You **know the keyset/cursor alternative** and can write it cold.
3. You **can articulate the tradeoffs** — keyset is faster but can't jump to arbitrary pages.
4. You **handle stable ordering**, duplicate sort-keys, and deletions correctly.

Pagination is also a gateway to talking about composite indexes, sort key design, and cursor-based APIs (GraphQL connections, Stripe-style API design).

## Concepts involved

### Syntax to lock in

```sql
-- OFFSET pagination (the one that scales badly)
SELECT id, title, created_at
FROM posts
ORDER BY created_at DESC, id DESC
LIMIT 20 OFFSET 1000000;          -- page 50,001

-- Keyset pagination (the one that scales)
-- Client passes the last seen (created_at, id) tuple as the cursor.
SELECT id, title, created_at
FROM posts
WHERE (created_at, id) < ($1, $2)         -- tuple comparison
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

The tuple comparison `(created_at, id) < ($1, $2)` is the key. It's equivalent to:

```sql
WHERE created_at < $1 OR (created_at = $1 AND id < $2)
```

…but the tuple syntax lets Postgres use a single index seek instead of two-branch logic.

### Edge cases / interview traps

1. **Sort key must be unique** — or you must add a tiebreaker. `ORDER BY created_at` alone is broken if multiple rows share the same timestamp: at the page boundary you'll skip or duplicate rows. Always append the primary key.
2. **Composite index must match sort order exactly.** `CREATE INDEX ON posts (created_at DESC, id DESC)` matches `ORDER BY created_at DESC, id DESC`. Mismatched directions force a full sort.
3. **`OFFSET` reads and discards `offset` rows.** It's not a "jump to row N" operation — it's "read N rows, throw them away, then return the next 20". This is why deep pagination dies.
4. **Inserts/deletes shift pages in OFFSET pagination.** New post inserted between page loads → user sees the same post twice on consecutive pages, or misses one entirely.
5. **Keyset cursor must encode the *full* sort tuple.** If you `ORDER BY x, y, id`, the cursor is `(x, y, id)`. Encode all three.
6. **Direction: forward only, by default.** Going back to the previous page is a separate query with reversed direction. Most production paginations only support forward.
7. **Page numbers are impossible with keyset.** "Jump to page 47 of 1000" requires an index lookup that keyset doesn't support. Keyset gives "next 20" only.
8. **Cursor opacity.** Production APIs base64-encode the cursor (`(timestamp, id)` → opaque string) so clients don't depend on the cursor format.

## Mental Model

### Why OFFSET is slow

```
Query:  ORDER BY created_at DESC LIMIT 20 OFFSET 1,000,000

Postgres execution:
  1. Use index on created_at DESC to scan in order.
  2. Read row #1, #2, #3, ..., #1,000,000 → DISCARD ALL.
  3. Read rows #1,000,001 through #1,000,020.
  4. Return them.

Work done:  1,000,020 row reads.  Wall time: seconds.
                                  ↑
                                  Should be 20 reads. This is the bug.
```

### Why keyset is fast

```
Cursor: (last_created_at, last_id) = ('2026-01-15 10:23:45', 9876543)

Query:  WHERE (created_at, id) < ('2026-01-15 10:23:45', 9876543)
        ORDER BY created_at DESC, id DESC
        LIMIT 20

Postgres execution:
  1. Index seek to ('2026-01-15 10:23:45', 9876543) — O(log n).
  2. Read next 20 entries in index order.
  3. Return them.

Work done:  log(n) seek + 20 reads.  Wall time: milliseconds. Constant per page.
```

Visual on the B-tree:

```
Index on (created_at DESC, id DESC):

  [Jan 15 10:23:45.123 / id=9876543]   ← cursor lands here
  [Jan 15 10:23:45.110 / id=9876542]   ← read 1
  [Jan 15 10:23:45.108 / id=9876541]   ← read 2
  [Jan 15 10:23:44.999 / id=9876540]   ← read 3
  ...
  [Jan 15 10:23:42.111 / id=9876523]   ← read 20

  done. Index seeked once; 20 sequential reads from leaf pages.
```

## Why interviewers care

- Deep pagination is the #1 cause of "slow query alerts" in production. Senior candidates have seen it.
- Keyset pagination is the **canonical example of "schema/index design dictates query performance"** — a senior storytelling pattern.
- It's the gateway to **cursor-based APIs** — GraphQL connection model, Stripe-style API design, Twitter's pre-snowflake API.
- The "OFFSET doesn't jump, it scans" insight is a **mental-model checkpoint** — if you don't have it, you'll write slow code forever.

## Common beginner confusion

- *"`OFFSET` uses the index to jump to row N."* It doesn't. It reads and discards.
- *"Keyset pagination is just `id > last_id`."* Only if you sort by `id` alone. For `ORDER BY created_at, id`, you need a tuple comparison.
- *"Pages 1–10 are fine; just don't paginate deep."* True, but at scale every page is the deep page for someone. Robots, exports, hostile users.
- *"Keyset means I can't show page numbers."* True. Show "Next" / "Previous" buttons. Most modern UIs (Twitter, GitHub) do exactly this.
- *"I'll use a `seek_id` column."* Same as keyset, just renamed. Make sure the sort matches the index.

## Brute force approach

`LIMIT N OFFSET M` with no thought about M growing. Works at M < 1000 with an indexed sort column; falls apart at M = 1M. The "fix" of adding more replicas or indexes doesn't help — OFFSET still scans M+N rows.

Equally brutish: `ORDER BY RAND() LIMIT 20` for "random feed". That's a full table sort, even worse.

## Optimal approach

**Tier 1 — Keyset pagination (default for production feeds).**
- Index on the full sort tuple.
- Cursor = the last row's sort tuple.
- Tuple comparison `(a, b, id) < (a₀, b₀, id₀)`.
- O(log n) per page. Constant time regardless of depth.

**Tier 2 — Hybrid (small page numbers via OFFSET, deep navigation via keyset).**
- Pages 1–20 use OFFSET (cheap; users see page numbers).
- Beyond page 20, switch to keyset; URL becomes `?after=...`.

**Tier 3 — Pre-materialised pages.**
- For static rankings (top 100 leaderboard, "popular this week"), compute pages offline; serve as keys in a sorted set.

## Solution (PostgreSQL)

```sql
-- Schema
CREATE TABLE posts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  title TEXT,
  body TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Composite index matching the sort order
CREATE INDEX idx_posts_feed ON posts(created_at DESC, id DESC);

-- ============================================================
-- OFFSET pagination — what NOT to do at depth
-- ============================================================

-- Page 1 (offset 0): fast
SELECT id, title, created_at FROM posts
ORDER BY created_at DESC, id DESC
LIMIT 20 OFFSET 0;

-- Page 50,001 (offset 1,000,000): slow — reads 1M rows
SELECT id, title, created_at FROM posts
ORDER BY created_at DESC, id DESC
LIMIT 20 OFFSET 1000000;
-- EXPLAIN ANALYZE: "Rows Removed by Filter: 0" but
-- "Index Scan" returns 1,000,020 tuples.

-- ============================================================
-- Keyset pagination — the production answer
-- ============================================================

-- First page: no cursor
SELECT id, title, created_at FROM posts
ORDER BY created_at DESC, id DESC
LIMIT 20;
-- → return rows + the last row's (created_at, id) as the cursor.

-- Subsequent page: client sends back the cursor
SELECT id, title, created_at FROM posts
WHERE (created_at, id) < ($1::timestamptz, $2::bigint)
ORDER BY created_at DESC, id DESC
LIMIT 20;
-- $1 = last seen created_at, $2 = last seen id.

-- ============================================================
-- Cursor encoding (Node)
-- ============================================================
```

```javascript
// Encode: opaque base64 of (created_at, id)
function encodeCursor(row) {
  const raw = JSON.stringify({ t: row.created_at, i: row.id });
  return Buffer.from(raw).toString('base64url');
}

function decodeCursor(cursor) {
  if (!cursor) return null;
  const { t, i } = JSON.parse(Buffer.from(cursor, 'base64url').toString());
  return { createdAt: t, id: i };
}

async function fetchFeed({ cursor, limit = 20 }) {
  const c = decodeCursor(cursor);
  const sql = c
    ? `SELECT id, title, created_at FROM posts
       WHERE (created_at, id) < ($1::timestamptz, $2::bigint)
       ORDER BY created_at DESC, id DESC LIMIT $3`
    : `SELECT id, title, created_at FROM posts
       ORDER BY created_at DESC, id DESC LIMIT $1`;
  const params = c ? [c.createdAt, c.id, limit] : [limit];
  const { rows } = await pg.query(sql, params);
  const last = rows[rows.length - 1];
  return {
    edges: rows.map(r => ({ node: r, cursor: encodeCursor(r) })),
    pageInfo: {
      hasNextPage: rows.length === limit,
      endCursor: last ? encodeCursor(last) : null,
    },
  };
}
```

### EXPLAIN comparison

```sql
EXPLAIN (ANALYZE, BUFFERS)
  SELECT * FROM posts ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 1000000;
-- Limit  (actual rows=20 loops=1)
--   ->  Index Scan Backward using idx_posts_feed on posts
--       (actual rows=1000020 loops=1)
--       Buffers: shared hit=22000
-- Execution Time: 1842 ms  ← bad

EXPLAIN (ANALYZE, BUFFERS)
  SELECT * FROM posts WHERE (created_at, id) < ('2026-01-15', 9876543)
  ORDER BY created_at DESC, id DESC LIMIT 20;
-- Limit (actual rows=20 loops=1)
--   ->  Index Scan Backward using idx_posts_feed on posts
--       (actual rows=20 loops=1)
--       Buffers: shared hit=24
-- Execution Time: 0.3 ms  ← good
```

## Step-by-step dry run

Suppose the table has 100M rows and the user is on page 50,001 (offset 1,000,000):

```
OFFSET 1,000,000 LIMIT 20:
  Step 1: Postgres uses idx_posts_feed (DESC).
  Step 2: Reads index entries in order, fetches heap rows (or index-only scan).
  Step 3: Counts to 1,000,000. Discards all.
  Step 4: Returns the next 20.
  Total: 1,000,020 row reads. ~1.8s.

Keyset (cursor = '2026-01-15 10:23:45.123', 9876543):
  Step 1: Index seek to (2026-01-15 10:23:45.123, 9876543). O(log n).
  Step 2: Walk backward 20 entries in the index.
  Step 3: Fetch heap rows for those 20.
  Total: 20 row reads. ~0.3 ms.
```

The 5000x speedup is real. It's not "optimisation"; it's correcting an algorithmic mistake.

Edge case: 5 posts share `created_at = '2026-01-15 10:23:45.000'`. With `ORDER BY created_at DESC` alone, the page boundary is ambiguous — page 1 might return 3 of them, page 2 might return 2 of them plus 18 new ones, or vice versa. Adding `id DESC` as a tiebreaker — and including `id` in the cursor — fixes it deterministically.

## How to think aloud in the interview

> "First question: how big is the table and how deep do users typically paginate? If it's small or shallow, OFFSET is fine and simpler. If it's 10M+ rows and users can go deep — feeds, exports, robots — OFFSET is the bug. It reads and discards `offset` rows; the cost is O(offset + limit), not O(limit). At offset 1M that's 50k× more work than the user is asking for.
>
> The fix is keyset pagination. Sort by `(created_at, id)` — including the primary key as a tiebreaker is critical, otherwise rows with identical timestamps cause page-boundary glitches. The cursor is the last row's `(created_at, id)` tuple. The next-page query is `WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT 20`. Tuple comparison in Postgres uses the composite index efficiently — one index seek, 20 reads, regardless of depth.
>
> Index design matters: `CREATE INDEX ON posts (created_at DESC, id DESC)`, exactly matching the `ORDER BY` direction so Postgres reads the index forward instead of doing a sort.
>
> Tradeoff: keyset can't jump to page 47 of 1000. If the UX needs page numbers I'd do a hybrid — page numbers for the first N pages via OFFSET, then 'load more' via cursor beyond that. Production APIs base64-encode the cursor so clients don't take a dependency on the format."

## Important takeaways

- **OFFSET is O(offset + limit)**, not O(limit). It reads and discards.
- **Keyset pagination is O(log n)** via index seek; constant time per page regardless of depth.
- **The sort key must be unique** — append the primary key as tiebreaker.
- **Use tuple comparison** `(a, b) < ($1, $2)` — lets the planner use the composite index.
- **Composite index must match `ORDER BY`** direction exactly.
- **Cursor encoding** — base64-opaque for production APIs.
- **Keyset = forward-only**; "jump to page N" is unsupported by design.
- **OFFSET pagination is unstable** under concurrent inserts/deletes; keyset is stable.

## Variants

1. **Bidirectional pagination** — support `before` cursor in addition to `after`. Swap the comparison direction and reverse the result rows.
2. **Compound cursor with `WHERE` filter** — feed filtered by user, tag, etc. Index becomes `(user_id, created_at DESC, id DESC)`; tuple stays the same.
3. **Cursor across joins** — join with users; cursor still on `(posts.created_at, posts.id)`; the join doesn't change the sort.
4. **`ORDER BY (random_seed % N)`** — sharded "infinite scroll" with per-user random order. Cursor includes the seed.
5. **Page numbers via `count_estimate`** — `SELECT reltuples FROM pg_class WHERE relname = 'posts'` for an approximate row count without a full `COUNT(*)`.
6. **GraphQL Connection spec** — the standard cursor pattern `{ edges: [{node, cursor}], pageInfo: { hasNextPage, endCursor } }`.
7. **Snowflake/MySQL specifics** — the same approach works; `MySQL ROW_FORMAT` and prefix indexes have nuances around composite index scans.

## Revision notes

> **pagination keyset — 60 second recap**
> - **OFFSET is O(offset + limit)** — reads and discards N rows. Dies at deep pages.
> - **Keyset is O(log n)** — index seek to cursor, read LIMIT rows.
> - Sort by `(sortkey, primary_key)` to make the key unique.
> - Cursor = the last row's full sort tuple, base64-encoded.
> - Tuple comparison `(a, b) < ($1, $2)` lets Postgres use the composite index.
> - Composite index direction must match `ORDER BY` direction.
> - Forward-only; jump-to-page-N is unsupported by design.
> - GraphQL Connection spec is the canonical API shape.
> - Hybrid: small page numbers OFFSET, deep nav keyset.
