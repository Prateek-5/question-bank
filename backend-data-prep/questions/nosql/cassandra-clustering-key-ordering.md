# Cassandra: Clustering key ordering — ASC/DESC, range queries

## Source / Origin
- Bread-and-butter Cassandra modeling question. Pairs with partition-key design.
- Concept reference: `backend-data-prep/nosql/05-dynamodb-cassandra.md`.

## Why this question matters in interviews
Clustering keys order rows on disk **physically**. Choose ASC/DESC wrong and "latest 50 messages" becomes a full-partition scan. Senior signal: you understand that `CLUSTERING ORDER BY` is **disk layout**, not query option, and you compose multi-column clustering keys to support several range queries from one table.

## Concepts involved

### Syntax to lock in

```sql
CREATE TABLE messages (
  channel_id  uuid,
  ts          timestamp,
  msg_id      timeuuid,
  body        text,
  sender_id   uuid,
  PRIMARY KEY (channel_id, ts, msg_id)
) WITH CLUSTERING ORDER BY (ts DESC, msg_id DESC);

-- "Latest 50 messages" — uses the on-disk order
SELECT * FROM messages WHERE channel_id = ? LIMIT 50;

-- "Messages since T" — range on clustering column
SELECT * FROM messages
  WHERE channel_id = ?
    AND ts > ?
  LIMIT 50;

-- "Messages in window [a, b]"
SELECT * FROM messages
  WHERE channel_id = ?
    AND ts >= ?
    AND ts <  ?;
```

### Clustering key rules to memorize

1. Multiple clustering columns form a **hierarchical** order: outer column first, then inner.
2. Range predicate (`>`, `<`, `>=`, `<=`, `IN`) allowed on at most **one clustering column at a time**, and only after equality on all preceding ones.
3. `ORDER BY` in a SELECT must match — or reverse — the declared CLUSTERING ORDER. No arbitrary sort.
4. `CLUSTERING ORDER BY (a DESC, b DESC)` and `(a ASC, b ASC)` are mirror images — reversing one column requires reversing all (single-direction ordering rule).
5. Adding a clustering column requires a table rebuild.
6. Static columns are per-partition, not per-row.

### Edge cases / interview traps

1. **Skip-equality on outer clustering** — `WHERE channel_id=? AND msg_id > ?` is illegal without `ts = ?` first.
2. **Reverse iteration cost** — minor extra CPU vs forward; pick the order matching the dominant access.
3. **Tie-break clustering column** — `(ts, msg_id)` handles same-timestamp collisions; missing this causes overwrites if PK isn't unique.
4. **Pagination via clustering** — `WHERE channel_id=? AND ts < lastSeenTs LIMIT 50` is the cursor pattern.
5. **Tombstone scan in middle** — deleting old messages leaves tombstones; range scans pay the cost.
6. **TTL** — per-row; expiry generates tombstones (see tombstone-trap file).
7. **Frozen UDT in clustering key** — possible but limits sort flexibility.
8. **`PER PARTITION LIMIT`** — gets one row per partition (`SELECT ... PER PARTITION LIMIT 1`); senior trick.

## Mental Model

> A partition is a **sorted file on disk**. The clustering key is the sort order. Range queries become **contiguous reads**, like reading a chapter of a book.

```
   Partition (channel=C-1):
     ts DESC                     msg_id DESC
   ┌─────────────────────────────────────────┐
   │  2026-05-17T12:00:01  msg_id=A  body=…  │  ← newest first
   │  2026-05-17T12:00:00  msg_id=B  body=…  │
   │  2026-05-17T11:59:59  msg_id=C  body=…  │
   │   ...                                   │
   │  2026-05-01T08:00:00  msg_id=Z  body=…  │  ← oldest
   └─────────────────────────────────────────┘

   "Latest 50"     → read top 50 of the file → O(50)
   "Since 11:59:55" → read top until ts < 11:59:55 → O(matching)
```

## Why interviewers care

- Tests **disk-layout fluency** — order is physical, not query-time.
- Tests **range-query composition** — composite clustering supports multiple patterns.
- Tests **pagination literacy** — cursor on clustering key.

## Common beginner confusion

- "`ORDER BY` overrides the table's order." Only reverse-of-declared is allowed.
- "Multiple range predicates allowed." Only one range column.
- "Reverse iteration is free." Slight CPU cost; pick the right declared order.
- "Same `ts` in two rows is fine without an `id` clustering." Two rows collapse to one.
- "Cluster by random UUID for uniqueness." Defeats range queries; use `timeuuid` or `(ts, msg_id)`.

## Brute force approach

`PRIMARY KEY (channel_id, msg_id)` with random UUID. "Latest 50" needs reading entire partition + sorting in app. Don't.

## Optimal approach

1. Identify the dominant range query.
2. Pick the clustering column that satisfies it (usually `ts` or `timeuuid`).
3. Declare `CLUSTERING ORDER BY` to match the dominant scan direction.
4. Add a tie-break clustering column (`msg_id`) for uniqueness.
5. Compose additional clustering columns *only if* their range queries don't conflict.

## Solution (CQL)

```sql
-- === Example: messages with chronological scroll ===
CREATE TABLE messages (
  channel_id  uuid,
  ts          timestamp,
  msg_id      timeuuid,
  body        text,
  sender_id   uuid,
  PRIMARY KEY (channel_id, ts, msg_id)
) WITH CLUSTERING ORDER BY (ts DESC, msg_id DESC);

-- Newest 50
SELECT * FROM messages WHERE channel_id = ? LIMIT 50;

-- Page back: pass last seen (ts, msg_id) as cursor
SELECT * FROM messages
  WHERE channel_id = ?
    AND (ts, msg_id) < (?, ?)
  LIMIT 50;

-- Time window
SELECT * FROM messages
  WHERE channel_id = ?
    AND ts >= '2026-05-17 00:00'
    AND ts <  '2026-05-18 00:00';

-- === Example: leaderboard with score DESC, user_id ASC ===
CREATE TABLE leaderboard (
  game_id  uuid,
  score    bigint,
  user_id  uuid,
  PRIMARY KEY (game_id, score, user_id)
) WITH CLUSTERING ORDER BY (score DESC, user_id ASC);

-- Top 10
SELECT * FROM leaderboard WHERE game_id = ? LIMIT 10;

-- Anti-pattern: arbitrary ORDER BY not matching declaration
SELECT * FROM messages WHERE channel_id=? ORDER BY ts ASC;   -- ✓ legal (reverse of declared)
SELECT * FROM messages WHERE channel_id=? ORDER BY body;     -- ✗ illegal

-- === Multi-step clustering ===
CREATE TABLE events_by_user (
  user_id   uuid,
  day       date,
  hour      int,
  event_id  timeuuid,
  payload   text,
  PRIMARY KEY (user_id, day, hour, event_id)
) WITH CLUSTERING ORDER BY (day DESC, hour DESC, event_id DESC);

-- Latest events: equality not required up the hierarchy when leaving inner range open
SELECT * FROM events_by_user
  WHERE user_id = ?
    AND day = '2026-05-17'        -- equality on day
    AND hour > 12;                 -- range on hour (one range column)

-- ILLEGAL: range on day AND range on hour
SELECT * FROM events_by_user
  WHERE user_id = ?
    AND day > '2026-05-01'
    AND hour > 12;                 -- two ranges → CQL refuses

-- === PER PARTITION LIMIT ===
SELECT channel_id, max(ts) FROM messages PER PARTITION LIMIT 1;
```

## Step-by-step dry run

```
Table: messages, clustering (ts DESC, msg_id DESC).
Partition: channel_id = C-1, containing 10K messages.

Query 1: SELECT * WHERE channel_id=C-1 LIMIT 50;
  → seek to start of partition; read first 50 sorted rows by ts DESC.
  → O(50) — single seek + sequential read.

Query 2: SELECT * WHERE channel_id=C-1 AND ts >= '2026-05-17';
  → seek to ts boundary (start of 2026-05-17); read forward (which is "backward in time")
  → O(matching).

Query 3: pagination cursor.
  Last result had (ts='2026-05-17 10:00:00', msg_id=X)
  Next page: WHERE channel_id=C-1 AND (ts, msg_id) < ('2026-05-17 10:00:00', X) LIMIT 50;
  → tuple comparison on composite clustering. CQL respects the order.

Query 4 (ILLEGAL):
  WHERE channel_id=C-1 AND msg_id > X;
  → no equality on outer clustering `ts` → CQL refuses.

Query 5: reverse iteration.
  SELECT * WHERE channel_id=C-1 ORDER BY ts ASC, msg_id ASC LIMIT 50;
  → matches reverse of declared; legal; slight extra CPU.
```

## How to think aloud in the interview

> "Clustering key is the sort order on disk inside each partition. I pick the declaration direction (`CLUSTERING ORDER BY ts DESC`) to match the dominant scan direction — 'latest first'. Range queries on clustering columns are contiguous reads.
>
> Three rules I respect: equality on all outer clustering columns before a range on an inner one; only one range column per query; `ORDER BY` must match or fully reverse the declared order.
>
> Pagination is tuple comparison: `(ts, msg_id) < (lastTs, lastMsgId)`. Cassandra handles this natively. I always include a tie-break column (`msg_id`) when the natural sort column (`ts`) isn't unique.
>
> For multi-pattern tables I compose clustering keys hierarchically (`day, hour, event_id`), but I check that the access patterns don't need ranges on two clustering columns simultaneously — that's illegal and forces a second table."

## Important takeaways

- **Clustering order = on-disk sort.** Physical layout.
- **`CLUSTERING ORDER BY` declares direction;** `ORDER BY` in SELECT must match or fully reverse.
- **Equality on outer clustering before range on inner.**
- **One range predicate per clustering hierarchy.**
- **Tie-break with a unique inner column** (`msg_id`).
- **Pagination = tuple comparison** on the clustering key.
- **`PER PARTITION LIMIT`** for per-partition top-K.

## Variants

1. **Compound clustering with mixed direction** — only legal as `(a DESC, b DESC)` or full mirror; can't mix ASC and DESC freely (CQL `CLUSTERING ORDER BY (a DESC, b ASC)` is legal but limits queries).
2. **`token()` for cross-partition pagination** — `WHERE token(pk) > token(lastPk)` to scroll cluster-wide.
3. **Materialized view with new clustering** — pre-computes alternate sort.
4. **Static column** — partition-level value shared across rows (e.g., channel name).
5. **`ALLOW FILTERING` with PARTITION KEY supplied** — rare exception; needs justification.
6. **Range tombstones** — deleting a range of clustering values creates a range tombstone (see tombstone-trap file).

## Revision notes

> **clustering keys — 60s recap**
> - Declared `CLUSTERING ORDER BY` = on-disk sort, physical layout.
> - `ORDER BY` in SELECT must match or fully reverse.
> - Equality on outer clustering before range on inner.
> - One range predicate per query.
> - Tie-break with unique inner column (msg_id).
> - Pagination = tuple comparison on clustering.
> - `PER PARTITION LIMIT` for per-partition top-K.
> - Compose clustering hierarchically (day, hour, event_id) only if no two ranges needed simultaneously.
> - Forbidden: arbitrary ORDER BY on non-clustering columns.
