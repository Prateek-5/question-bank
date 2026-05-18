# Cassandra: Partition key design — token, hash, virtual nodes

## Source / Origin
- Senior Cassandra question at write-heavy shops (Netflix, Discord, Apple).
- Concept reference: `backend-data-prep/nosql/05-dynamodb-cassandra.md`.

## Why this question matters in interviews
Cassandra's partition key picks **which node owns your row**. The Murmur3 hash sends rows around a 64-bit token ring; vnodes spread ownership. A poorly chosen PK gives a hot node, a jumbo partition, or unbalanced load forever (re-keying = rebuild). Senior signal: you talk about the token ring, vnodes, partition-size limits (~100 MB / 100K rows), and why you model **one table per access pattern**.

## Concepts involved

### Syntax to lock in

```sql
-- Partition key: user_id. Clustering key: post_id (ordered DESC).
CREATE TABLE posts_by_user (
  user_id    uuid,
  post_id    timeuuid,
  body       text,
  PRIMARY KEY (user_id, post_id)             -- (PK, clustering)
) WITH CLUSTERING ORDER BY (post_id DESC);

-- Composite partition key: (tenant_id, user_id) → one partition per tenant+user
CREATE TABLE messages (
  tenant_id   uuid,
  user_id     uuid,
  message_id  timeuuid,
  body        text,
  PRIMARY KEY ((tenant_id, user_id), message_id)   -- double parens = composite PK
) WITH CLUSTERING ORDER BY (message_id DESC);

-- Token inspection
SELECT token(user_id), user_id FROM posts_by_user LIMIT 5;
```

### Partition limits to memorize

| Metric | Soft limit | Hard pain point |
|---|---|---|
| Partition size | 100 MB | >250 MB causes compaction issues |
| Rows per partition | 100K | >1M is risky |
| Tombstones per query | 1000 (default `tombstone_warn_threshold`) | 100K = query failure |

### Edge cases / interview traps

1. **Unbounded partition** — `PRIMARY KEY (city, event_id)` for "events in a city" — partition grows forever. Bucket by time.
2. **Hot partition** — celebrity user_id in `posts_by_user`. Bucket-shard.
3. **Token ring imbalance** — pre-vnodes era; vnodes (default 16 or 256) randomize ranges per node.
4. **Murmur3 distribution** — uniform on the hashed key; good for high-cardinality PKs.
5. **`ALLOW FILTERING`** — query without PK; full cluster scan; **production-forbidden**.
6. **Secondary index** — local to each node; reasonable for low-cardinality filters but never for high-cardinality.
7. **Partition keys are immutable** — you can't UPDATE the PK; delete + insert.
8. **No JOINs** — model one table per access pattern.

## Mental Model

> Cassandra is a **ring**. Each node owns one or more arcs (vnodes). Murmur3-hash of your partition key maps to a point on the ring; the owning node and its `RF-1` neighbors store the row.

```
                  token 0
                    │
            Node A  ─┼─  Node B
                ┌───┘   └───┐
        Node D ─┤           ├─ Node C
                └───┐   ┌───┘
                    │   │
                  token 2^63

   hash(user_id) = T  →  walk clockwise from T, first vnode owner stores row
                         next RF-1 nodes (clockwise) hold replicas
```

Vnodes randomize the arc-to-node assignment so adding/removing a node redistributes ~1/N of the data evenly, not all to one neighbor.

## Why interviewers care

- Tests **token-ring fluency** — partition placement is the foundational concept.
- Tests **partition-size discipline** — unbounded partitions are the #1 production bug.
- Tests **table-per-access-pattern thinking** — denormalize aggressively; no joins.

## Common beginner confusion

- "Use the same table for all access patterns." You can't — partition placement serves one access pattern.
- "Partition key = primary key." PK is the partition + clustering combined.
- "Secondary indexes are like Mongo's." Local to each node, hidden cost; rarely the right tool.
- "ALLOW FILTERING is fine for small data." It triggers a full-cluster scan; ban it in code review.
- "Just add more nodes." Re-distributes data but doesn't fix a hot partition.

## Brute force approach

`PRIMARY KEY (user_id)` for users, `PRIMARY KEY (post_id)` for posts. Now "all posts for user X" needs `ALLOW FILTERING` → cluster-wide scan. Don't.

## Optimal approach

For each access pattern, design a dedicated table:
1. Identify the **lookup key** for the access pattern. That's the PK.
2. Identify the **range/sort** within the lookup. That's the clustering key.
3. Bound partition size with **time buckets** if growth is unbounded.
4. For hot-key risk, **shard with a bucket suffix**.

## Solution (CQL)

```sql
-- === Access pattern A1: posts authored by a user, newest first ===
CREATE TABLE posts_by_user (
  user_id  uuid,
  post_id  timeuuid,
  body     text,
  PRIMARY KEY (user_id, post_id)
) WITH CLUSTERING ORDER BY (post_id DESC);

SELECT * FROM posts_by_user WHERE user_id = ? LIMIT 50;

-- === Access pattern A2: feed by category (likely hot — needs bucketing) ===
CREATE TABLE posts_by_category_day (
  category  text,
  day       date,
  post_id   timeuuid,
  body      text,
  user_id   uuid,
  PRIMARY KEY ((category, day), post_id)        -- composite PK: bucket by day
) WITH CLUSTERING ORDER BY (post_id DESC);

SELECT * FROM posts_by_category_day
WHERE category = 'sports' AND day = '2026-05-17' LIMIT 50;

-- === Hot user (celebrity) — bucket suffix ===
CREATE TABLE posts_by_user_bucketed (
  user_id  uuid,
  bucket   int,
  post_id  timeuuid,
  body     text,
  PRIMARY KEY ((user_id, bucket), post_id)
) WITH CLUSTERING ORDER BY (post_id DESC);

-- Write: pick bucket = hash(post_id) % 8
INSERT INTO posts_by_user_bucketed (user_id, bucket, post_id, body)
VALUES (?, ?, ?, ?);

-- Read: scatter-merge across all 8 buckets
SELECT * FROM posts_by_user_bucketed WHERE user_id = ? AND bucket = 0 ...
                                       UNION (in app) ...

-- === Token inspection (debugging) ===
SELECT token(user_id), user_id, count(*) FROM posts_by_user
GROUP BY user_id LIMIT 20;

-- === Avoid: ALLOW FILTERING in app code ===
-- SELECT * FROM posts_by_user WHERE body = 'hello' ALLOW FILTERING;  -- never
```

### Vnodes & replication

```yaml
# cassandra.yaml
num_tokens: 16            # vnodes per physical node (default 16 in 4.0+)
endpoint_snitch: GossipingPropertyFileSnitch
```

```sql
-- Replication factor per keyspace
CREATE KEYSPACE app
  WITH REPLICATION = {
    'class': 'NetworkTopologyStrategy',
    'dc-east': 3,
    'dc-west': 3
  };
```

## Step-by-step dry run

```
Cluster: 6 nodes, RF=3, num_tokens=16 → ~96 vnodes total.

Insert: user_id=U-7
  Murmur3(U-7) = 0x5F3A...
  Vnode owner = node B; replicas → C, D.
  All 3 acknowledge per W consistency level.

Read: user_id=U-7
  Same hash; routed to node B (or coordinator forwards to replica per CL).
  CL=ONE → response from first replica to answer.
  CL=QUORUM (RF=3) → need 2 of 3 replicas to agree; coordinator reconciles via read-repair.

Hot partition: celebrity user_id=U-CELEB
  All inserts targeting (U-CELEB, *) hash to the same partition on node B.
  Node B compaction queue grows; eventually >100 MB partition warning.
  Fix: posts_by_user_bucketed with (user_id, bucket) → 8 partitions across nodes.

Unbounded partition: (category='sports', *) accumulates years of posts
  → fix with day bucket: ((category, day), post_id).
  Reads paginate across days.

ALLOW FILTERING anti-pattern:
  SELECT * FROM posts_by_user WHERE body = 'x' ALLOW FILTERING;
  → coordinator queries every replica of every partition.
  → on a 100M-row table, minutes-long scan, brings down a node.
```

## How to think aloud in the interview

> "One table per access pattern. The partition key is whatever you look up by; clustering keys handle order within. Murmur3 hashes the PK onto a 64-bit ring; vnodes spread arcs evenly across nodes.
>
> Hard limits to respect: ~100 MB per partition, ~100K rows. If a partition grows unbounded — events in a city, all posts by category — I bucket by time: `((category, day), post_id)`. That gives me 365 partitions a year instead of one.
>
> Hot keys — celebrity user, popular category — I add a bucket suffix to the PK: `((user_id, bucket), post_id)`. 8 buckets disperse writes across 8 nodes. Reads do a scatter merge.
>
> Three things I refuse to ship: `ALLOW FILTERING` in production code, secondary indexes on high-cardinality fields, and partitions designed to grow forever. Code review blockers."

## Important takeaways

- **One table per access pattern.** Denormalize aggressively.
- **Partition key = lookup. Clustering = within-partition order.**
- **Soft limits: 100 MB / 100K rows per partition.**
- **Bucket by time** to bound unbounded partitions.
- **Bucket suffix** for hot keys.
- **`ALLOW FILTERING` is forbidden** in production.
- **Vnodes (16 / 256)** randomize arc ownership; smooth scale-up/down.
- **`token()` for diagnosis.** Reveals partition placement.

## Variants

1. **Composite partition key** — `((tenant, user), msg_id)` co-locates one tenant's user's data.
2. **Hashed prefix manual** — old style; not needed with vnodes.
3. **Materialized views** — server-side reverse projections; risky in production, often DIY tables are better.
4. **Multi-DC** — `NetworkTopologyStrategy` per DC; quorum can be local or global.
5. **Cluster-key range queries** — `WHERE user_id = ? AND post_id > ?` ranges within a partition.
6. **Static columns** — per-partition metadata that doesn't repeat per row.

## Revision notes

> **cassandra partition key — 60s recap**
> - Murmur3 hash → 64-bit token ring → vnode owner + RF-1 replicas.
> - One table per access pattern.
> - PK = lookup; clustering = within-partition order.
> - Hard limits: ~100 MB / 100K rows per partition.
> - Bucket by time for unbounded growth.
> - Bucket suffix for hot keys.
> - `ALLOW FILTERING` = forbidden.
> - Vnodes (num_tokens=16 or 256) randomize ring placement.
> - Composite PK `((a, b), c)` = double parens; co-locates by (a, b).
