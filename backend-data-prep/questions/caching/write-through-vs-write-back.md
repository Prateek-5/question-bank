# Write-Through vs Write-Back (Write-Behind) Cache

## Source / Origin
- Textbook caching patterns from CPU caches (Hennessy & Patterson), revived in distributed systems by memcached + MySQL stacks.
- Companion concept doc: `backend-data-prep/caching/01-caching-strategies.md` — "Write-through" and "Write-back" sections.
- Common system-design interview question: "Design a write-heavy counter / metrics ingestion system." The answer hinges on write-back.

## Why this question matters in interviews
Once a candidate clears cache-aside, interviewers ask "how would you make writes faster?" Write-back is the answer — and it's also the most dangerous caching pattern, with explicit data-loss windows. Senior signal is being able to (a) name both patterns precisely, (b) sketch the timing diagrams that show the latency vs durability tradeoff, (c) know which one to pick for ad-impression counters vs banking ledgers, and (d) describe the failure mode honestly: "yes, write-back can lose writes if the cache dies before flush; here's the durability budget I'd negotiate."

## Concepts involved

### Syntax to lock in

**Write-through** — write to cache and DB synchronously, both must succeed:
```
function update(key, value):
    cache.set(key, value)
    db.write(key, value)          # both before returning
    return ack
```

**Write-back (write-behind)** — write to cache only, async flush to DB:
```
function update(key, value):
    cache.set(key, value, dirty=true)
    enqueue_flush(key)            # async, batched
    return ack                    # returns BEFORE DB write
```

### Edge cases / interview traps
1. **Write-through atomicity** — what if `cache.set` succeeds but `db.write` fails? Now cache has new value, DB has old. You must either (a) rollback cache, or (b) accept the cache as "ahead" and reconcile via TTL, or (c) write DB first, then cache (closer to cache-aside semantics).
2. **Write-back loss window** — between the cache.set and the async flush, the data lives only in RAM. Cache crash → data gone. The loss window is the flush interval (typically 1–10s).
3. **Write-back ordering** — if writes for the same key are coalesced (last-write-wins in the flush batch), out-of-order updates can be lost. Most implementations coalesce intentionally — this is a feature for counters but a bug for audit logs.
4. **Backpressure** — write-back queue can grow unbounded under load. Need a queue cap with a fallback to synchronous DB write.
5. **Replay on restart** — write-back caches need a durable journal (AOF in Redis, write-ahead-log) so unflushed writes can be replayed after a restart. Without it, restarting the cache = data loss.
6. **Read-during-flush consistency** — a reader hitting cache during a pending flush gets the *new* value (cache has it). A reader hitting DB directly (analytics, replica) gets the *old* value. This creates dashboard/data-pipeline confusion.

## Mental Model

### Write-through — synchronous, durable, slow
```
Client ─────► App ─────► Cache.set ─────► DB.write ─────► return
              │           ▲                ▲
              │           │                │
              └───── both must succeed ────┘

Latency: max(cache_write, db_write)  ≈ db_write   (10–50ms)
Durability: same as DB                            (strong)
Loss window: 0
```

### Write-back — async, fast, fragile
```
Client ─────► App ─────► Cache.set (dirty) ──► return  (1ms)
                              │
                              ▼
                       Flush queue (in-memory)
                              │
                              ▼ (batched, every N ms or N items)
                          DB.write

Latency: cache_write only                          (~1ms)
Durability: cache durability + flush interval
Loss window: flush_interval  (1s, 10s, configurable)
```

### Timing comparison

```
T=0    Client → write("balance", 100)

WRITE-THROUGH:
T=0    cache.set ─┐
T=20   db.write   ├─ both done
T=20   return ack ┘

WRITE-BACK:
T=0    cache.set
T=1    return ack    ← client gone, data only in cache
T=...  cache batches
T=1000 flush to DB    ← if cache dies between T=1 and T=1000, write is lost
```

## Why interviewers care
- Tests whether you can articulate **latency vs durability** as a conscious tradeoff, not as a buzzword.
- Write-back is the textbook answer for **high-throughput counters, metrics, view counts, like-counts** — workloads where small loss is acceptable for 100x throughput.
- Write-through is the textbook answer for **session state, shopping cart contents, profile updates** — workloads where the cache must always have the latest.
- Knowing **when neither fits** (e.g., banking ledgers — use cache-aside with synchronous DB writes) is the senior signal.

## Common beginner confusion
- **"Write-through is the safe one."** Only for the cache→DB direction. If `db.write` fails after `cache.set` succeeds, you have inconsistency. Sequence matters.
- **"Write-back is the fast one, just always use it."** Until your cache crashes and you lose 10 seconds of writes. Or your flush queue overflows and the app stalls.
- **"Write-back is the same as async DB write."** No — write-back implies the cache holds the *current authoritative value* (DB is behind). Async DB write from cache-aside still treats DB as authoritative; you can't read from cache safely until the write lands.
- **"I'll write to both in parallel."** That's neither pattern — it's a foot-gun. Failure modes are awful: cache succeeds, DB fails (or vice versa), and you have no clean recovery.

## Brute force approach
"Write to DB synchronously on every request." This is the baseline — no cache. Correct, slow.

"Write to DB asynchronously via a queue (e.g., Kafka)." Closer to write-back but without the read-from-cache property. Adds a moving piece (Kafka) and doesn't help read latency. Worth it for write-heavy fire-and-forget workloads, but not "caching" anymore.

## Optimal approach

### Pick write-through when:
- Data must be readable immediately from a different process / instance.
- Loss of recent writes is unacceptable (sessions, carts, settings).
- Write rate is moderate (latency budget can absorb DB write time).
- DB is the source of truth and reads can fall back to DB if cache misses.

### Pick write-back when:
- Workload is write-dominated and many writes collapse to the same key (counters, hot-key increments).
- Some data loss is acceptable (analytics, view counts, "fire-and-forget" metrics).
- You have a durable cache journal (AOF in Redis with `everysec` or `always`).
- You can afford a separate flush worker + queue.

### Hybrid:
- **Write-through for critical fields, write-back for derived counters.** E.g., `user.last_login_at` is write-through; `user.login_count` is write-back.
- **Write-back with a sync fallback** — if queue depth > threshold, write synchronously to shed pressure.

## Solution

### Write-through (Node.js + ioredis + Postgres)

```javascript
const Redis = require('ioredis');
const redis = new Redis();

async function writeThrough(key, value) {
  const ttl = 600;
  // 1. write DB first (source of truth — if cache fails after, TTL bounds drift)
  await db.query('UPDATE items SET value = $1 WHERE key = $2', [value, key]);
  // 2. update cache
  await redis.set(key, JSON.stringify(value), 'EX', ttl);
}

// Alternative ordering: cache-first then DB.
// Drawback: cache shows the new value before DB; readers on cache see "the future."
// Most teams write DB first → cache for simplicity + crash safety.
```

### Write-back (Node.js — batched flush)

```javascript
const Redis = require('ioredis');
const redis = new Redis();

const FLUSH_INTERVAL_MS = 1000;
const dirty = new Map();   // in-memory dirty-tracking; for prod, store in Redis ZSET

async function writeBack(key, value) {
  // 1. write to cache (authoritative for now)
  await redis.set(key, JSON.stringify(value));
  // 2. mark dirty for the flusher
  dirty.set(key, value);
}

// Background flusher
setInterval(async () => {
  if (dirty.size === 0) return;
  const batch = Array.from(dirty.entries());
  dirty.clear();   // optimistic: we'll re-add on failure
  try {
    await db.batchInsert(batch);
  } catch (err) {
    // re-enqueue
    for (const [k, v] of batch) dirty.set(k, v);
    console.error('flush failed; re-enqueued', err);
  }
}, FLUSH_INTERVAL_MS);
```

### Production-grade write-back uses a durable Redis structure:

```lua
-- Lua: atomic increment + dirty-set push
-- KEYS[1] = counter key, KEYS[2] = dirty set key, ARGV[1] = increment, ARGV[2] = timestamp
local new = redis.call('INCRBY', KEYS[1], ARGV[1])
redis.call('ZADD', KEYS[2], ARGV[2], KEYS[1])
return new
```

The flusher reads from the dirty ZSET, batches, writes to DB, and ZREMs the flushed keys.

## Step-by-step dry run

Scenario: counter increment under both patterns, with a cache crash.

**Write-through**, 3 increments, cache crash after T=60:
| T  | Action | Cache | DB |
|----|--------|-------|-----|
| 10 | `inc("views:home")` | `5 → 6` | `5 → 6` |
| 20 | `inc("views:home")` | `6 → 7` | `6 → 7` |
| 30 | `inc("views:home")` | `7 → 8` | `7 → 8` |
| 60 | **cache dies** | `{}` | `8` |
| 70 | next read | miss → DB → `8` | `8` |

No loss. Latency: 3 × ~25ms per call.

**Write-back**, same scenario, flush interval = 60s:
| T  | Action | Cache | DB | Dirty set |
|----|--------|-------|-----|-----------|
| 10 | `inc("views:home")` | `5 → 6` | `5` | `{views:home}` |
| 20 | `inc("views:home")` | `6 → 7` | `5` | `{views:home}` |
| 30 | `inc("views:home")` | `7 → 8` | `5` | `{views:home}` |
| 60 | **cache dies before flush** | `{}` | `5` | — |
| 70 | next read | miss → DB → `5` | `5` | — |

**3 writes lost.** Loss window = flush interval. Latency was 3 × ~1ms per call.

This is the precise tradeoff. The interview answer is "I'd pick write-back for view counts because losing 60 seconds of view increments is acceptable; I'd pick write-through for shopping carts because losing a user's last-added item is not."

## How to think aloud in the interview

"So there are two patterns and they sit on opposite ends of the latency–durability spectrum. Write-through writes to both cache and DB before returning — you get DB-level durability and cache-level read speed, but write latency is bounded by the DB. Write-back writes to cache only and flushes to DB asynchronously — write latency drops to ~1ms but you have a loss window equal to your flush interval.

For this problem — let's say it's an Instagram-style like counter — I'd reach for write-back. Like counts get a million writes per second on a hot post; the DB can't keep up with synchronous writes. Losing a couple seconds of like increments during a cache failure is acceptable; the user experience is 'my like was counted' regardless. Concretely, I'd use Redis with `INCR` for the counter and a ZSET for the dirty-tracking, plus AOF persistence with `appendfsync everysec` so even on cache crash I lose at most ~1s.

Now, if the same interview were about a shopping cart, I'd flip to write-through. The cost of losing 'item added to cart' from a user's perspective is high — they think they bought something and didn't. Cart writes are also low-rate per user, so synchronous DB writes are fine. I'd write to DB first, then cache, with the cache as a read-acceleration layer.

The trap I'd flag: 'parallel writes to cache and DB' is *not* a pattern, it's a bug. If cache succeeds and DB fails, you don't know which one to trust. Always sequence them."

## Important takeaways

- **Write-through** = both writes synchronous. Latency ≈ DB write. Durability = DB durability. Loss window = 0.
- **Write-back** = cache write only; flush async. Latency ≈ cache write. Durability = cache durability. Loss window = flush interval.
- **Order matters in write-through**: prefer DB-first → cache-set, so a cache failure doesn't leave cache "ahead" of DB.
- **Write-back needs a durable journal** (Redis AOF) or you lose writes on cache restart.
- **Write-back needs backpressure** — if flush queue grows, switch to sync mode.
- **Use case mapping**: counters/metrics → write-back. Cart/session/profile → write-through. Banking/payments → cache-aside with synchronous DB.

## Variants

1. **Write-around** — write only to DB, never to cache; let TTL/invalidation populate cache lazily. Useful when written data is rarely read again. See `write-around-pattern.md`.
2. **Write-through with batching** — buffer writes in-process for 10ms, then flush a batch to DB and cache. A middle ground.
3. **Write-back with eventual consistency guarantees** — flush durably to Kafka first, then to DB. Loss-free at the cost of operational complexity.
4. **Write-through with optimistic concurrency** — use CAS / `WATCH` to detect concurrent updates and retry.
5. **Tiered write-back** — L1 (in-process) writes back to L2 (Redis) which writes back to DB. Each tier has its own flush interval.

## Revision notes

> **write-through vs write-back — 60 second recap**
> - **Through:** write cache + DB sync. Slow, safe. Use for sessions, carts, profiles.
> - **Back:** write cache only, flush DB async. Fast, lossy. Use for counters, metrics, hot writes.
> - **Loss window of write-back = flush interval.** Negotiate this with the product team.
> - Write-back **needs a durable cache** (AOF / WAL) or restart loses unflushed writes.
> - **Sequencing in write-through:** DB first, then cache. Avoids "cache ahead of DB."
> - **Parallel cache+DB writes are never the answer** — failures leave you with unrecoverable inconsistency.
> - **Trap:** picking write-back for cart data; picking write-through for million-rps counters.
