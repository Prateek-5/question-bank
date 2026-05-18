# MongoDB: Schema for social feed — fan-out-on-write vs read

## Source / Origin
- Twitter / Instagram feed problem. Asked at every social-product interview.
- Concept reference: `backend-data-prep/nosql/04-mongodb.md`.
- Cross-ref: `backend-data-prep/system-design/02-news-feed.md` (if extending).

## Why this question matters in interviews
Feed design is the **canonical write-vs-read tradeoff** question. The two extremes — fan-out-on-write (push) vs fan-out-on-read (pull) — both have killer failure modes (celebrity hotspot vs read amplification). The senior answer is **hybrid**: push for normal users, pull for celebrities, merge at read. Interviewers use this to test whether you can reason about asymmetric workloads and refuse to give a one-size-fits-all answer.

## Concepts involved

### Syntax to lock in

```javascript
// posts: the source of truth, never duplicated
{
  _id: ObjectId("POST-1"),
  authorId: "U-2",
  text: "hello world",
  media: [...],
  createdAt: ISODate(...),
  likeCount: 42,
  commentCount: 3
}

// followers: directed edge
{ followerId: "U-1", followeeId: "U-2", createdAt: ISODate(...) }

// fanout-on-write: precomputed timelines
// timelines: { userId, items: [{ postId, postedAt, authorId }] }
// indexed { userId: 1, "items.postedAt": -1 }
// or a row-per-entry: timelineEntries { userId, postId, postedAt, authorId }
```

### Edge cases / interview traps

1. **Celebrity hotspot** — pushing a Taylor-Swift post to 100M followers blows up the write path. Pull for celebrities only.
2. **Pull from too many followees** — a user follows 5K accounts; pulling their feed every refresh is 5K cursor reads. Push for normal cases.
3. **Cold-start fan-out** — when a new user joins, their timeline is empty; backfill from followee history.
4. **Post deletion** — fan-out-on-write means the deleted post still sits in N inboxes. Need a tombstone or on-render check.
5. **Edit propagation** — same problem; render against the live post doc (store only postId in timelines, not the full post).
6. **Backfill cost** — at scale (Twitter), fan-out workers run as a queue, not synchronously.
7. **Ranking vs chronology** — chronological merge is straightforward; ranked feeds need a scoring service over a candidate set.
8. **Block / mute** — applied at render, not at write (otherwise you must re-fanout on block changes).

## Mental Model

> Three personas decide the strategy:
> - **Normal user** (≤ 1K followers): cheap to push.
> - **Power user** (1K–100K): hybrid; push but throttled.
> - **Celebrity** (≥ 100K): pull only; their posts live in their timeline; followers merge on read.

```
   POST CREATED by U-2
            │
            ▼
   followers count ≤ 1K?   ──yes──▶  FAN-OUT-ON-WRITE
            │                          push {postId, postedAt} to each follower's timeline
            │
            no
            ▼
   PULL MODE: do nothing. Followers will merge U-2's recent posts at read time.

   READ FEED for U-1:
     timeline_entries  (push side, already merged)              ─┐
                                                                 ├──▶  k-way merge by postedAt  ──▶  page
     for each celebrity U-1 follows: recent N posts by author  ─┘
```

## Why interviewers care

- Tests **asymmetric workload reasoning** — not all users are equal.
- Tests **denormalization budget** awareness — push duplicates a postId N times.
- Tests **knowing when to abandon a strategy** — celebrity hotspot is the canonical example.
- Tests **operational thinking** — fan-out is a queue, not a synchronous write.

## Common beginner confusion

- "Always push" — celebrity fanout is unbounded.
- "Always pull" — 5K followees × every refresh = N+1 from hell.
- "Store the full post in every timeline." Edits/deletes become impossible to keep consistent.
- "Use a SQL JOIN of follows × posts." Doesn't scale — that's the whole point of denormalization.
- "Render-time block filter is too slow." It's a hash-set membership test on a few hundred IDs — fine.

## Brute force approach

Render-time JOIN: `posts WHERE authorId IN (followees of U)` sorted by `createdAt DESC LIMIT 50`. Fine for a hobby project, dies at production scale because the followee set is large and the post collection is huge.

## Optimal approach

**Hybrid fan-out**:
- For non-celebrities, fan-out-on-write into a `timelineEntries` collection keyed by `userId`.
- For celebrities (flagged), skip the fanout; pull their recent posts at read time.
- At read time, k-way merge the precomputed entries with the celebrity-pulled list, then filter blocks/mutes and hydrate full post data.

## Solution (Mongo shell + worker pseudocode)

```javascript
// === Indexes ===
db.posts.createIndex({ authorId: 1, createdAt: -1 });
db.followers.createIndex({ followerId: 1, followeeId: 1 }, { unique: true });
db.followers.createIndex({ followeeId: 1 });           // reverse lookup for fanout
db.timelineEntries.createIndex({ userId: 1, postedAt: -1 });
db.timelineEntries.createIndex({ userId: 1, postId: 1 }, { unique: true });

// === Author flag ===
db.users.updateOne({ _id: "U-celeb" }, { $set: { isCelebrity: true } });

// === On post create ===
const post = { _id: new ObjectId(), authorId: "U-2", text: "hi", createdAt: new Date() };
db.posts.insertOne(post);

const author = db.users.findOne({ _id: post.authorId }, { isCelebrity: 1 });
if (!author.isCelebrity) {
  // Fanout job: enqueue to worker, do not block the API
  enqueue("fanout", { postId: post._id, authorId: post.authorId, postedAt: post.createdAt });
}

// === Fanout worker ===
async function fanout({ postId, authorId, postedAt }) {
  const cursor = db.followers.find({ followeeId: authorId }, { followerId: 1 });
  const batch = [];
  for await (const f of cursor) {
    batch.push({
      updateOne: {
        filter: { userId: f.followerId, postId },
        update: { $setOnInsert: { postedAt, authorId } },
        upsert: true
      }
    });
    if (batch.length >= 1000) { await db.timelineEntries.bulkWrite(batch); batch.length = 0; }
  }
  if (batch.length) await db.timelineEntries.bulkWrite(batch);
}

// === Read feed for U-1 ===
async function feed(userId, cursor = new Date(), limit = 50) {
  // 1) push-side: precomputed entries
  const pushSide = await db.timelineEntries
    .find({ userId, postedAt: { $lt: cursor } })
    .sort({ postedAt: -1 }).limit(limit).toArray();

  // 2) pull-side: celebrities this user follows
  const celebFollowees = await db.followers.aggregate([
    { $match: { followerId: userId } },
    { $lookup: { from: "users", localField: "followeeId", foreignField: "_id", as: "u" } },
    { $unwind: "$u" },
    { $match: { "u.isCelebrity": true } },
    { $project: { followeeId: 1 } }
  ]).toArray();

  const pullSide = celebFollowees.length === 0 ? [] :
    await db.posts.find({
      authorId: { $in: celebFollowees.map(c => c.followeeId) },
      createdAt: { $lt: cursor }
    }).sort({ createdAt: -1 }).limit(limit).toArray();

  // 3) merge by time
  const merged = mergeByDesc(pushSide.map(e => ({...e, ts: e.postedAt})),
                              pullSide.map(p => ({ postId: p._id, authorId: p.authorId, ts: p.createdAt})),
                              x => x.ts).slice(0, limit);

  // 4) hydrate live post data + apply block/mute
  const ids = merged.map(m => m.postId);
  const posts = await db.posts.find({ _id: { $in: ids } }).toArray();
  const blocks = await db.blocks.find({ userId }).toArray();
  const blockSet = new Set(blocks.map(b => b.targetId));
  return posts.filter(p => !blockSet.has(p.authorId));
}

// === Post deletion: write a tombstone or rely on hydrate filter ===
db.posts.updateOne({ _id: postId }, { $set: { deletedAt: new Date() } });
// Render: skip posts with deletedAt set.
```

## Step-by-step dry run

```
Setup:
  U-1 follows U-2 (normal) and U-celeb (1M followers).
  U-2 has 500 followers including U-1.

t=0  U-2 posts P-100 → fanout job enqueued
t=1  Worker reads 500 followers, bulk-upserts 500 timelineEntries (one row per follower for P-100)
     Timeline of U-1 now has { postId: P-100, postedAt: t=0 }

t=5  U-celeb posts P-200 → no fanout; just lives in posts collection
t=10 U-1 refreshes:
       push-side: read timelineEntries for U-1, get [P-100, ...prior]
       pull-side: find celebs U-1 follows = [U-celeb]
                  fetch recent posts by U-celeb → [P-200, ...]
       merge by ts desc → [P-200(t=5), P-100(t=0), ...]
       hydrate posts; apply block filter
       return page

t=20 U-2 deletes P-100 → posts.deletedAt set.
       Next render: hydrate finds deletedAt, filters out P-100.
       timelineEntries row remains; harmless (lazy cleanup OK).

t=30 U-2 gains a millionth follower → mark them isCelebrity=true.
       Future posts skip fanout. Past entries remain in timelines.
```

## How to think aloud in the interview

> "Two strategies, both broken alone. Fan-out-on-write is fast to read but explodes on celebrities — 100M write amplification. Fan-out-on-read is cheap on write but you pay 5K cursor reads per refresh. So I hybrid: push for normal authors, pull for celebrities flagged by follower count.
>
> Timelines store *postId + timestamp*, never the full post. That way edits and deletes propagate naturally — at render time I hydrate from the live `posts` collection and drop anything `deletedAt`.
>
> Fanout is a queue, not a synchronous write. The author's request returns as soon as the post is persisted; a worker handles the fan-out with bulk writes in batches of 1000.
>
> Block/mute is a render-time filter. Applying it at write time would force a rebuild every time you block someone.
>
> Cost: storage scales with `posts × avgFollowers` on the push side. At 100M users × 200 posts × 200 followers = 4 trillion timeline rows, which is why real Twitter shards aggressively and trims to recent windows."

## Important takeaways

- **Hybrid is the only correct answer.** Push for normal, pull for celebrities.
- **Store postId only in timelines.** Live hydrate from `posts` for edits/deletes.
- **Fanout is asynchronous.** Queue + worker, not synchronous.
- **Block/mute at render time.** Cheaper than rebuilding on every relationship change.
- **Celebrity threshold is a flag**, not a hardcoded number. Tune it.
- **Storage budget**: precomputed timelines are the dominant cost — trim to recent N days.

## Variants

1. **Ranked feed** — replace chronological merge with a scoring service; candidate set from same hybrid.
2. **Stories (24h TTL)** — TTL index on `timelineEntries.postedAt` cleans up automatically.
3. **Reposts/RTs** — store as a separate `repostId` linking to original; preserves attribution.
4. **Mute keywords** — render-time predicate against post text.
5. **Read-after-write within own feed** — write to author's own timeline synchronously even if pull mode.
6. **Sharding** — shard timelineEntries by `userId hashed` for horizontal scale.
7. **Backfill on follow** — on follow, copy recent posts of the new followee into the follower's timeline.

## Revision notes

> **social feed schema — 60s recap**
> - Hybrid fan-out: push for normal, pull for celebrities (flag).
> - Timelines store *postId + timestamp only*; hydrate from `posts` at render.
> - Fanout = async queue, bulk-writes of 1000.
> - Block/mute = render-time filter.
> - Index: `{userId, postedAt: -1}` on timelineEntries; `{followeeId: 1}` for fanout.
> - Deletion = soft via `deletedAt`; hydrate filter drops.
> - Storage cost dominant — trim timelines to recent N days.
> - Read = k-way merge (push entries ⨝ celeb pulled posts), hydrate, filter blocks.
