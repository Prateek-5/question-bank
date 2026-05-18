# The Double-Deletion Problem (Cache + DB Write Race)

## Source / Origin
- First codified in the Chinese tech blogosphere (Alibaba, JD.com) as "缓存双删" — "cache double-delete."
- The race itself is described in every distributed systems text discussing cache invalidation; the *fix* (delayed second delete) is the named pattern.
- Companion concept doc: `backend-data-prep/caching/01-caching-strategies.md` — invalidation race section.
- Interview prompt: "Walk me through what happens if you have a slow read concurrent with a write in cache-aside."

## Why this question matters in interviews
This is *the* concurrency question for caching. Even candidates who can describe cache-aside often miss the precise timeline where a slow read repopulates the cache *after* a concurrent write deletes it, leaving the cache permanently stale. The senior signal is being able to (a) draw the T1/T2 timeline on the whiteboard, (b) propose the delayed-second-delete fix, (c) acknowledge the fix is heuristic, not perfect, and (d) offer the better-than-fix alternative (CDC-based invalidation or versioned keys).

## Concepts involved

### Syntax to lock in

The race-prone sequence:
```
# Reader path
val = cache.get(key)
if val is None:
    val = db.read(key)
    cache.set(key, val, ttl)   # ← danger zone
return val

# Writer path
db.write(key, new_val)
cache.del(key)
```

The fix — "double delete" (delete the cache *twice*, once before the DB write, once after a short delay):
```
# Writer path with double delete
cache.del(key)                 # delete #1 — pre-emptive
db.write(key, new_val)
sleep(500ms)                   # delay covers the typical reader's read+set window
cache.del(key)                 # delete #2 — clean up any stale repopulation
```

### Edge cases / interview traps
1. **The slow reader race** — a reader fetches stale DB row, but takes 600ms to write to cache; in the meantime the writer deletes cache, writes DB, and... the reader's stale value lands afterward. Cache permanently stale until TTL.
2. **Delete-before-write race** — if the writer deletes before writing DB, a concurrent reader misses, reads DB (still old), populates cache (old), writer writes DB (new) → cache stale.
3. **Two writers racing** — W1 writes then deletes; W2 writes then deletes. Final state: cache empty, DB = whichever write landed last. Usually OK, but loss-of-update if the writes aren't commutative.
4. **`cache.set` on write** — the most common beginner mistake. Two concurrent writers can land cache.set in opposite order from db.write. Cache and DB drift permanently.
5. **Delay length** — too short, doesn't cover the race window; too long, blocks the writer or holds an async job for too long.
6. **Async second delete** — the delay-then-delete can be enqueued asynchronously to avoid blocking the writer. But now you need a reliable delay queue (Redis Streams, RabbitMQ delayed exchange, etc.).
7. **TTL as safety net** — even if the double-delete fails, the TTL eventually expires the stale entry. Always set a TTL.
8. **Replica lag amplifies it** — if your DB reads come from a lagging replica, the reader can read stale data even after the writer commits. Race window grows from milliseconds to seconds.

## Mental Model

### The bad race (slow read + concurrent write)

```
T   Reader (R)                     Writer (W)            Cache    DB
─── ──────────────                 ──────────             ─────    ─────
 0  cache.get(k) → MISS                                    {}      v=A
10                                  db.write(k, B)          {}      v=B
20                                  cache.del(k)            {}      v=B   (no-op; cache empty)
30  db.read(k) → v=B
    (reader started before W,
     but DB read happened after)
40                                                          {}      v=B
50  cache.set(k, B)                                         {k:B}   v=B   ← consistent!
```

**This case is fine.** But now consider the slow read started *before* W:

```
T   Reader (R)                     Writer (W)            Cache    DB
─── ──────────────                 ──────────             ─────    ─────
 0  cache.get(k) → MISS                                    {}      v=A
 5  db.read(k) → v=A                                        {}      v=A
                                                             (R has stale A in hand)
10                                  db.write(k, B)          {}      v=B
20                                  cache.del(k)            {}      v=B
30                                                          {}      v=B
50  cache.set(k, A)                                         {k:A}   v=B   ← STALE!
```

**Cache has A, DB has B.** Until TTL expires, every reader sees stale A. This is the race.

### The double-delete fix

```
T   Reader (R)                     Writer (W)            Cache    DB
─── ──────────────                 ──────────             ─────    ─────
 0  cache.get(k) → MISS                                    {}      v=A
 5  db.read(k) → v=A                                        {}      v=A
10                                  cache.del(k) #1         {}      v=A
15                                  db.write(k, B)          {}      v=B
20                                  schedule del @T+520
50  cache.set(k, A)                                         {k:A}   v=B   ← STALE here
520                                 cache.del(k) #2         {}      v=B
600 next read → MISS → db.read=B → cache.set(k, B)         {k:B}   v=B   ← FIXED
```

The second delete cleans up the stale repopulation. The delay must exceed the typical reader's read-to-set window.

## Why interviewers care
- Tests **concurrency timeline reasoning** — can you trace T1/T2 column by column?
- Reveals knowledge of the **classic interviewer-favorite race**.
- The fix (double delete) is heuristic — the senior conversation is "this isn't perfect; here's when you'd graduate to CDC."
- Real production systems hit this at scale; the question filters out candidates who only know cache-aside in the happy path.

## Common beginner confusion
- **"This race is rare."** Not at scale. With high QPS, a slow reader concurrent with a write is *guaranteed*; only the rate varies.
- **"Just `cache.set` on write to prevent this."** That introduces a worse race (two-writer-reorder). See `cache-aside-pattern.md`.
- **"TTL fixes it."** TTL *bounds* the duration of staleness but doesn't prevent the race itself. A 5-minute TTL means 5 minutes of stale data before recovery.
- **"Why not just use a transaction?"** The cache and DB are different systems with no shared transaction context. You can't atomically commit to both.
- **"Lock the key during the write."** Possible, but kills write throughput. Reads also need the lock to be correct, which is even worse.

## Brute force approach
**Brute 1: `cache.set` on write.** Replaces one race with a worse one. Two concurrent writers can land cache.set in opposite order from db.write. Cache drift.

**Brute 2: Distributed lock around every read and write.** Correct but slow. Latency goes from 1ms to 10ms; throughput collapses.

**Brute 3: Short TTL (e.g., 5 seconds).** Bounds staleness to 5 seconds but causes 10× more DB load due to misses. Doesn't solve the race, just minimizes its duration.

## Optimal approach

### Tier 1 — Cache-aside with TTL safety net + delayed second delete
- `cache.del → db.write → schedule async delete after N ms`.
- N = 2× typical reader read-set window (often 200–500ms).
- Heuristic but cheap.

### Tier 2 — Versioned keys (preferred)
- Key is `user:42:v{n}`; `n` lives in a small "version" key.
- Write path: `INCR user:42:version`; new reads see the new version automatically.
- Old version entries die via TTL.
- **No race** — readers and writers never share a key.

### Tier 3 — CDC-based invalidation (Debezium / DynamoDB Streams)
- DB emits change events; a consumer invalidates cache.
- Decouples invalidation from app logic.
- **Eventual consistency**; small lag between DB commit and invalidation.

### Tier 4 — Read-through with stale-while-revalidate
- Trade strict freshness for guaranteed availability.
- The race still exists but is masked: stale reads return a value with a "stale" flag, refresh is asynchronous.

## Solution

### Double-delete writer (Node.js)

```javascript
const Redis = require('ioredis');
const redis = new Redis();

async function updateUser(userId, patch) {
  const key = `user:${userId}`;
  // 1. pre-emptive delete (best-effort; covers most read races)
  await redis.del(key);
  // 2. write DB
  await db.query('UPDATE users SET ... WHERE id = $1', [userId, ...patch]);
  // 3. schedule the second delete
  setTimeout(() => redis.del(key).catch(console.error), 500);
}
```

### Production version — second delete via a delay queue

```javascript
// Using a Redis sorted set as a delay queue
async function updateUserDurable(userId, patch) {
  const key = `user:${userId}`;
  await redis.del(key);
  await db.query('UPDATE users SET ... WHERE id = $1', [userId, ...patch]);
  // schedule via ZSET keyed on execute-at timestamp
  const executeAt = Date.now() + 500;
  await redis.zadd('cache:delayed_dels', executeAt, key);
}

// Worker
async function delayedDeletionWorker() {
  while (true) {
    const now = Date.now();
    const due = await redis.zrangebyscore('cache:delayed_dels', 0, now, 'LIMIT', 0, 100);
    if (due.length === 0) {
      await new Promise(r => setTimeout(r, 100));
      continue;
    }
    for (const key of due) {
      await redis.del(key);
      await redis.zrem('cache:delayed_dels', key);
    }
  }
}
```

### Versioned-key approach (preferred at scale)

```javascript
async function getUserVersioned(userId) {
  const v = await redis.get(`user:${userId}:version`) || '1';
  const key = `user:${userId}:v${v}`;
  const cached = await redis.get(key);
  if (cached !== null) return JSON.parse(cached);

  const row = await db.query('SELECT * FROM users WHERE id = $1', [userId]);
  await redis.set(key, JSON.stringify(row), 'EX', 300);
  return row;
}

async function updateUserVersioned(userId, patch) {
  await db.query('UPDATE users SET ... WHERE id = $1', [userId, ...patch]);
  await redis.incr(`user:${userId}:version`);
  // Old user:42:v3 entry decays via TTL. New reads write user:42:v4.
}
```

## Step-by-step dry run

**Scenario:** Two concurrent operations on `user:42`. DB row is `{name: "Alice"}`. Writer updates to `{name: "Bob"}`.

### Bad path (no double delete, reader started before writer)

| T (ms) | Reader (R)                      | Writer (W)                | Cache         | DB              |
|--------|---------------------------------|---------------------------|---------------|-----------------|
| 0      | cache.get(k) → MISS              |                           | {}            | {Alice}         |
| 1      | db.read(k) → {Alice}             |                           | {}            | {Alice}         |
| 2      |                                   | db.write({Bob})           | {}            | {Bob}           |
| 3      |                                   | cache.del(k)              | {}            | {Bob}           |
| 50     | cache.set(k, {Alice})            |                           | **{k:Alice}** | {Bob}           |
| 60     | next reader → cache hit Alice    |                           | {k:Alice}     | {Bob}           |
| ...    | every reader for next 300s sees Alice |                       | {k:Alice}     | {Bob}           |

**Stale until TTL.** Bad outcome.

### Good path (double-delete with 500ms delay)

| T (ms) | Reader (R)                      | Writer (W)                       | Cache         | DB      |
|--------|---------------------------------|----------------------------------|---------------|---------|
| 0      | cache.get(k) → MISS              |                                  | {}            | {Alice} |
| 1      | db.read(k) → {Alice}             |                                  | {}            | {Alice} |
| 2      |                                   | cache.del(k) #1                  | {}            | {Alice} |
| 3      |                                   | db.write({Bob})                  | {}            | {Bob}   |
| 4      |                                   | schedule second del @ T=504      | {}            | {Bob}   |
| 50     | cache.set(k, {Alice})            |                                  | {k:Alice}     | {Bob}   |
| 60     | next reader → cache hit Alice    |                                  | {k:Alice}     | {Bob}   |
| 504    |                                   | cache.del(k) #2                  | {}            | {Bob}   |
| 600    | next reader → MISS → db → {Bob}  |                                  | {k:Bob}       | {Bob}   |

**Staleness window bounded to ~500ms.** Acceptable for most use cases.

### Best path (versioned keys, no race)

| T (ms) | Reader                                       | Writer                                | Cache state                           | DB      |
|--------|----------------------------------------------|---------------------------------------|---------------------------------------|---------|
| 0      | read version=1 → key user:42:v1 → miss        |                                       | {}                                    | {Alice} |
| 1      | db.read → {Alice} → cache.set("v1", Alice)    |                                       | {user:42:v1:Alice}                    | {Alice} |
| 2      |                                                | db.write({Bob})                       | {user:42:v1:Alice}                    | {Bob}   |
| 3      |                                                | INCR version → 2                      | {user:42:v1:Alice}                    | {Bob}   |
| 4      | new reader: read version=2 → key user:42:v2 → miss |                                  | {user:42:v1:Alice}                    | {Bob}   |
| 5      | db.read → {Bob} → cache.set("v2", Bob)        |                                       | {user:42:v1:Alice, user:42:v2:Bob}    | {Bob}   |
| 305    | TTL expires user:42:v1                        |                                       | {user:42:v2:Bob}                       | {Bob}   |

**Zero stale reads.** The cost is a small extra `GET` of the version key per read (cacheable in-process for further optimization).

## How to think aloud in the interview

"OK so the question is what goes wrong when a read and a write race in cache-aside. Let me trace it. Reader checks cache — miss. Reader reads DB — gets the old value. Now the reader pauses for whatever reason — GC, network blip, slow JSON parse, doesn't matter. Meanwhile a concurrent writer writes the new value to DB and deletes the cache. Now the reader resumes and finishes its work by writing the old value into the cache. Cache now has stale data; DB has new data. Until TTL, every reader hits stale.

The classic fix is the double delete pattern. Writer deletes cache first — best-effort cleanup. Then writes DB. Then schedules a second cache delete a few hundred milliseconds later. The delay covers the typical reader's read-and-set window. After the second delete, the next reader misses again, reads the fresh DB value, populates cache correctly.

It's heuristic. The delay is a tunable based on your read latency distribution. If a reader takes longer than the delay, you still get stale data — but the chance shrinks linearly with the delay. In practice 500ms covers >99% of real read latencies.

The cleaner answer at scale is versioned keys. Store the user under `user:42:v3`. A version counter `user:42:version` lives separately. On write, increment the version. New reads compose the new key and miss, then populate correctly. Old entries decay via TTL. No race possible because readers and writers never touch the same key.

The even cleaner answer is CDC — Debezium reads the DB binlog and emits invalidation events. App code never touches cache invalidation. Trade-off: eventual consistency with sub-second lag.

If they push: TTL alone doesn't fix this — TTL just bounds the staleness duration. The race itself is independent of TTL."

## Important takeaways

- **The race exists in vanilla cache-aside.** Slow reader + concurrent write = stale cache.
- **Double-delete fix:** `cache.del → db.write → delayed cache.del`. Heuristic.
- **Versioned keys eliminate the race entirely.** Readers and writers don't share keys.
- **CDC invalidation is the cleanest async solution.** Decouples app from cache logic.
- **TTL is the universal safety net** — bounds staleness even when other mechanisms fail.
- **Never `cache.set` on write.** Introduces a worse two-writer race.
- **Replica lag amplifies the race window** — reads from replicas can be seconds stale.

## Variants

1. **Async double-delete via delay queue** — durable second delete survives process restart.
2. **Versioned keys with global namespace bump** — `acme:_v` increment invalidates everything cheaply.
3. **CDC + invalidation pipeline** — Debezium → Kafka → cache invalidator service.
4. **Read-your-writes via primary pinning** — for N seconds post-write, route reads to primary DB only.
5. **Pessimistic locking** — distributed lock around cache+DB writes. Correct, slow, rarely worth it.
6. **TTL-only "good enough" mode** — accept some staleness, don't bother with double delete. Valid for low-stakes data.

## Revision notes

> **double-deletion problem — 60 second recap**
> - **The race:** slow reader reads stale DB, writer updates DB + deletes cache, reader writes stale to cache. Cache stale until TTL.
> - **Fix:** `cache.del → db.write → delayed cache.del` (500ms typical).
> - **Better fix:** versioned keys (`user:42:v3` with a counter); no shared key, no race.
> - **Best fix:** CDC-based invalidation pipeline.
> - **TTL is the safety net** — always set one.
> - **Never `cache.set` on write.**
> - **Replica lag worsens the race window.**
> - **Trap:** thinking TTL alone fixes it; thinking the race is rare (it's guaranteed at scale).
