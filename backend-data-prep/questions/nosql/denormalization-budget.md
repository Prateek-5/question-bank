# Denormalization Budget — How Much Duplication Is Too Much?

## Source / Origin
- DynamoDB single-table design philosophy (Rick Houlihan, AWS re:Invent talks).
- MongoDB schema design guides — "embed vs reference".
- Common senior prompt: "You denormalized 6 places. The product team changes user.display_name. What's your migration plan?"

## Why this question matters in interviews
NoSQL design is fundamentally about **trading writes for reads**. Junior engineers either over-normalize (and then can't get sub-10ms reads) or over-denormalize (and then can't update anything without a migration). The senior signal is having a **budget** — a deliberate, articulated rule for *how much* duplication is acceptable given the workload's read:write ratio, update frequency, and consistency tolerance. The interviewer wants you to explain the cost model, propose a budget, and demonstrate the migration plan when fields change.

## Concepts involved

### The denormalization budget framing

The budget is the answer to: **"How many places can this field live before the maintenance cost exceeds the read benefit?"**

```
Field lives in 1 place:   normalized — clean updates, expensive reads (joins or N+1).
Field lives in N places:  denormalized — fast reads, N-way writes, N-way migrations.

Budget = max N such that:
    (writes-per-second × N × write_cost) + (migration_cost / lifetime) <
    (reads-per-second × read_cost_saved_by_denorm)
```

In plainer terms: denormalize when reads >> writes AND when the field rarely changes.

### Syntax to lock in

```javascript
// Mongo: embed (denormalized)
{
  _id: ObjectId("..."),
  user_id: 42,
  author_name: "Alice",        // ← duplicated from users collection
  author_avatar: "/a.png",     // ← duplicated
  content: "hello",
  created_at: ISODate(...)
}

// Mongo: reference (normalized)
{
  _id: ObjectId("..."),
  user_id: 42,                 // ← lookup users by user_id to get name/avatar
  content: "hello"
}
```

```python
# DynamoDB single-table: same item appears under multiple GSI projections
# Item:
{ "PK": "USER#42", "SK": "POST#100", "author_name": "Alice", "content": "hello" }
# GSI1: PK=POST#100, SK=USER#42 — for "get all posts" query
# author_name is also projected into GSI1 for read self-sufficiency.
```

```cql
-- Cassandra: same data, multiple tables, partitioned differently
CREATE TABLE posts_by_user (user_id UUID, post_id UUID, author_name TEXT, content TEXT, ...);
CREATE TABLE posts_by_id   (post_id UUID PRIMARY KEY, author_name TEXT, content TEXT, ...);
CREATE TABLE feed_by_follower (follower_id UUID, post_id UUID, author_name TEXT, ...);
-- author_name lives in 3 tables. Update fan-out is 3.
```

### Edge cases / interview traps
1. **The "denormalize once, regret forever" trap.** Once a field is in 5 tables, renaming or updating it requires a coordinated migration. Plan the migration *at design time*.
2. **Eventual consistency between denormalized copies.** Two tables both have `author_name`; you update one, the other is stale. Either accept it (chat messages: original name fine) or build dual-write + reconciliation.
3. **The "celebrity update" problem.** User with 10M followers changes display name → 10M denormalized rows to update. Either accept staleness, do lazy migration on read, or read-through the canonical user table for high-value fields.
4. **Write amplification.** Fanning a single logical write to 5 physical writes = 5x WCU cost in DynamoDB; 5x storage; 5x replication traffic.
5. **The "migrate everything" trap.** Schema change after denormalization can require rewriting millions of rows. Plan for online migration (dual-write + backfill + cutover).
6. **The "what's the canonical source of truth?" question.** When `author_name` lives in 6 tables, which one is authoritative? You need ONE canonical source + N read-optimized copies maintained by CDC, change streams, or app-side fan-out.
7. **Read-after-write consistency.** If the app immediately reads its own write, denormalized stores may not be updated yet. Either read from the canonical source for the user's own writes, or wait.
8. **Storage cost.** 5 copies of "Alice" is fine. 5 copies of a 1MB attachment is not.

## Mental Model

### The budget table

```
Field characteristics                  | Budget (max # of copies)
───────────────────────────────────────|─────────────────────────
Immutable (post timestamp, user_id)    | ∞ — copy freely
Rarely changes (display_name, email)   | 3-5 — denorm with migration plan
Occasionally changes (avatar)          | 2-3 — denorm with TTL refresh
Frequently changes (online status)     | 1 — keep canonical, read at query time
Hot-update (counters, likes)           | 1 — use counter table or Redis
```

### The denormalization decision flow

```
                Need this field on the read path?
                          │
                  ┌───────┴───────┐
                  No              Yes
                  │               │
              don't store      How often does it change?
                                  │
              ┌───────────────────┼────────────────────┐
            Rarely             Occasionally          Frequently
              │                  │                    │
        denormalize         denormalize +         keep canonical
        (1-5 copies)        TTL/refresh           (don't denorm)
              │                  │                    │
        Plan migration      Add invalidation     Read at query time
        at design time      hook                 (extra hop is OK)
```

### Write amplification picture

```
              Logical write: "Alice posts hello"

Normalized (1 write):
  users.posts.insert({author=42, content="hello"})   ← 1 disk write

Denormalized (5 writes):
  users.posts.insert(...)
  feed.bob.insert(...)        ← fan-out to Bob's feed
  feed.carol.insert(...)      ← fan-out to Carol's feed
  feed.dave.insert(...)
  feed.eve.insert(...)
  
  ← 5 disk writes. 5x WCU. 5x replication traffic. 5x storage growth.
  ← But: each follower's read is 1 partition lookup. Sub-ms.

Tradeoff: 5x write cost for 100x read speedup. Worth it when reads >> writes.
```

## Why interviewers care
- Tests whether you understand **the fundamental NoSQL design tension** (read vs write cost).
- Reveals whether you've operated denormalized systems through schema changes.
- The follow-up "user changes display name, what happens?" forces real migration thinking.
- Distinguishes engineers who design for happy-path from those who design for evolution.

## Common beginner confusion
- **"Denormalize everything for performance."** Until the first schema change. Then you have a 6-table migration nightmare.
- **"Never denormalize; just join."** NoSQL stores don't have efficient joins. You'll be doing N+1 queries from the app layer, which is worse than denormalizing.
- **"Denormalization breaks consistency."** Only if you don't engineer for it. Dual-write + reconciliation + CDC patterns exist.
- **"DynamoDB single-table is just denormalization."** Single-table design *exploits* denormalization but the goal is access pattern alignment, not pure duplication.
- **"Eventual consistency is unacceptable."** For most read paths (feed, profile, history), 1-second lag is invisible to users. Be explicit about which fields need strong consistency.

## Brute force approach
"Denormalize every field everywhere it's read." Maintenance nightmare; first migration takes the team down for a week.

"Never denormalize." App becomes 10x slower because every read requires 5 lookups; latency budget blown.

## Optimal approach

### The four-step design ritual

1. **List access patterns** in priority order. For each, what fields are needed?
2. **Classify each field** by mutability:
   - Immutable: copy freely.
   - Rarely-changing: denormalize, plan migration.
   - Frequently-changing: keep canonical, read at query time.
3. **For each denormalized field**, write down:
   - Where the canonical source lives.
   - How updates propagate (sync dual-write, async CDC, lazy on read).
   - What the staleness tolerance is.
   - What the migration plan is when the field changes shape.
4. **Set a hard budget**: e.g., "no field appears in more than 3 tables without team review."

### Update propagation strategies

| Strategy | Latency | Complexity | When |
|----------|---------|------------|------|
| **Sync dual-write** | High (waits for all copies) | Medium | Strong consistency needed |
| **Async CDC** | Low (write to canonical only) | High | Most production systems |
| **Lazy on read** | Zero write cost | Low | Stale fields tolerable |
| **TTL + refresh** | Zero write cost | Low | Truly cacheable fields |
| **Read-through canonical** | Extra hop on read | Low | High-value, rarely-changing fields |

## Solution (worked example: social media post)

### Without budget (everything denormalized)

```
posts_by_user       (user_id, post_id, author_name, author_avatar, author_bio, ...)
posts_by_hashtag    (hashtag, post_id, author_name, author_avatar, content, ...)
posts_by_location   (location, post_id, author_name, author_avatar, ...)
feeds               (follower_id, post_id, author_name, author_avatar, content, ...)
likes_by_post       (post_id, liker_id, liker_name, liker_avatar)
comments_by_post    (post_id, comment_id, author_name, author_avatar, ...)

author_name lives in 6 places. User changes name → 6-way migration.
For a celebrity with 10M followers, feeds alone is 10M row updates.
```

### With budget (max 3 copies of mutable fields)

```
posts                — canonical post data, author_id only.
users                — canonical user data (display_name, avatar).
feed                 — (follower_id, post_id, [author_name SNAPSHOT, author_avatar SNAPSHOT])
                       Author info as it was AT POST TIME — acceptable staleness.

For "show post page":
  posts.get(post_id) → fetch author_id
  users.get(author_id) → fetch CURRENT display_name, avatar
  Two queries, both single-key, ~2ms total. Fine.

For "show feed":
  feed.scan(follower_id, limit=50) → 50 rows with snapshotted author info.
  Single partition scan, ~5ms. Fine.

Update propagation when user.display_name changes:
  - posts table: no update needed (only author_id stored).
  - feed snapshots: NOT updated. Old feeds show old names. ACCEPTED STALENESS.
  - New posts: snapshot the new name at post time.

Result: changing display_name is a 1-row update. Migration painless.
```

### When stronger sync is needed (e.g., email update)

```
email_to_user (email → user_id) is an inverted index.
On email change:
  TXN: update users, insert new email_to_user, delete old email_to_user.
  In stores without txns: dual-write + reconciliation job + idempotency keys.
```

## Step-by-step dry run

**Scenario:** Twitter-like feed at 100M users, 10K posts/sec, 100K feed-reads/sec.

```
Naive normalized:
  Read feed = SELECT posts WHERE author IN (followed users) ORDER BY time DESC LIMIT 50
  ↳ scan ~1000 followed users' posts, sort, limit. ~500ms p99. UNACCEPTABLE.

Denormalized fan-out-on-write:
  On post by Alice: insert into feed table for each of Alice's 10M followers.
  Read feed = SCAN partition for follower_id ORDER BY time DESC LIMIT 50.
  ↳ Single partition scan. ~5ms p99. GREAT.
  ↳ But write cost: 1 logical post = 10M physical writes. CATASTROPHIC for celebs.

Hybrid:
  Non-celebrities (<10K followers): fan-out-on-write.
  Celebrities (>10K followers): fan-out-on-read (queue celebrities' recent posts, query at read time).
  Combined feed = union of pushed posts + pulled celebrity posts.
  
  Denormalization budget: feed stores author_name SNAPSHOT.
  When user changes name: old snapshots unchanged. New posts have new snapshot.
  Reads from feed never re-query users table.
  
  Cost: 1 write/sec celebrity + 10K writes/sec non-celebrity fan-out.
  Storage: ~50KB/follower-day of feed snapshots. 100M users * 50KB = 5TB feed.
  Latency: feed reads 5-20ms p99. Acceptable.
```

**Scenario:** User changes their email.

```
Before:
  Email lives in: users (canonical), email_to_user (inverted), posts (snapshotted at post time).

Update flow:
  1. Validate new email available (UPSERT email_to_user with IF NOT EXISTS, fail if exists).
  2. Update users.email to new value.
  3. Delete old email_to_user row.
  4. Posts table: do NOT update. Email in posts is historical snapshot; users see "what was the author's email at post time".

If step 3 fails: zombie row in email_to_user. Reconciliation job catches it.
If step 2 fails after step 1: old email_to_user still points to user_id; user can't change again. 
  Compensating action: delete the new email_to_user row (saga rollback).

Whole flow: 3 writes for an email change. Acceptable.
```

## How to think aloud in the interview

> "Denormalization in NoSQL is a tool, not a default. I think about it as a budget: how many places can a field live before the maintenance cost exceeds the read benefit.
>
> My rule of thumb: immutable fields can be copied freely. Rarely-changing fields can live in 3-5 places with a documented migration plan. Frequently-changing fields stay canonical — read with an extra hop, don't denormalize.
>
> For each denormalized field, I write down four things: where canonical lives, how updates propagate, what staleness is tolerable, what the migration plan is when the field's shape changes.
>
> Update propagation has four flavors: synchronous dual-write (slow but consistent), async via CDC (fast, eventually consistent, complex), lazy on read (zero write cost, computes on demand), and TTL refresh (good for cacheable fields).
>
> The hot question is celebrity updates. If 10M followers have Alice's old display name embedded in their feeds, a name change is a 10M-row migration. The senior answer is to **snapshot** the name at post-time — feeds show the name as it was when the post was made, which is what users actually expect anyway. Profile pages always query users canonically. That way, name changes are a 1-row update.
>
> The trap is over-denormalizing without a migration plan. The first schema evolution after you've denormalized 6 places is a multi-week project. Budget the duplication."

## Important takeaways

- **Denormalization budget:** explicit, documented limit on how many copies of a mutable field exist.
- **Classify fields by mutability** — immutable, rare, occasional, frequent.
- **Frequently-changing fields stay canonical** — don't denormalize even if reads suffer slightly.
- **Snapshot semantics** for "what was true at event time" — feeds, audit logs, history views.
- **Update propagation:** sync dual-write, async CDC, lazy on read, TTL refresh.
- **Plan migrations at design time**, not after the first rename.
- **Celebrity problem** is real — fan-out-on-write breaks for high-follower users; hybrid model.
- **Storage cost** is usually cheap; **maintenance cost** is the killer.

## Variants

1. **Single-table design (DynamoDB)** — extreme denormalization with strict budget enforcement.
2. **Materialized views (Postgres)** — denormalized read-only copies maintained by the DB.
3. **CDC + read store** — Postgres canonical, Elasticsearch denormalized read store.
4. **Snapshotted vs live join** — feeds use snapshots; profile pages live-join. Same data, different stores.
5. **Lazy reconciliation** — denormalized copies fixed on read if stale.
6. **Versioned records** — denormalized rows carry a version; lazy migration brings them current on access.

## Revision notes

> **denormalization budget — 60 second recap**
> - **Trade writes for reads.** Denormalize when reads >> writes AND field rarely changes.
> - **Budget** = max # of copies allowed for a field. Immutable: ∞. Frequent change: 1.
> - **Snapshot semantics** for historical views (feeds, audit). Live-join for profiles.
> - **Update propagation:** sync dual-write / async CDC / lazy on read / TTL refresh.
> - **Celebrity problem:** fan-out-on-write breaks for high-follower users; hybrid fan-out.
> - **Plan migrations at design time** — denormalized schema changes are expensive.
> - **One canonical source of truth per field.** N read-optimized copies maintained by CDC.
> - **Trap:** over-denormalizing without a budget; ignoring schema evolution cost.
