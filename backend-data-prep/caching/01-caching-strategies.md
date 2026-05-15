# Caching Strategies

## Why this matters in backend interviews

- **Every system design round** at scale-focused companies asks about caching.
- **Senior signal**: knowing **invalidation strategy** and **stampede prevention** — not just "use Redis."
- Production debugging questions: cache stampede, stale data, hot keys, eviction storms.

> "There are only two hard things in Computer Science: cache invalidation and naming things." — Phil Karlton. Interviewers test the first one.

---

## Core concepts

### Why cache?

- **Latency**: in-memory access is 10,000x faster than disk
- **Cost**: offload reads from expensive DBs
- **Scale**: serve a hot key from a 1 GB cache instead of 1000 DB reads per second
- **Availability**: serve stale-but-good data when DB is degraded

### Where caches live

| Layer | Examples | Use |
|---|---|---|
| **Browser** | HTTP cache, localStorage | Static assets, idempotent GETs |
| **CDN** | Cloudflare, Fastly, CloudFront | Static + API responses with TTL |
| **API gateway / reverse proxy** | Nginx, Varnish | Whole-response cache |
| **Application** | In-process LRU, Caffeine, Node `lru-cache` | Hot data per instance |
| **Distributed cache** | Redis, Memcached | Shared across instances |
| **Materialized views / read replicas** | DB-side | Precomputed query results |

Closer to the user = lower latency + lower cost.

### Caching patterns

#### 1. Cache-aside (lazy loading) — most common

```
read(key):
  v = cache.get(key)
  if v is None:
    v = db.get(key)
    cache.set(key, v, ttl)
  return v

write(key, value):
  db.write(key, value)
  cache.delete(key)   # invalidate (or update)
```

- App is responsible for cache management
- Only requested data is cached (lazy)
- Risk: first request after invalidation is slow
- Risk: stampede if many requests hit the same cold key simultaneously

#### 2. Read-through

Like cache-aside, but the cache itself talks to the DB on miss:
```
read(key):
  return cache.get_or_load(key, () => db.get(key))
```
- Cache provider abstracts DB access (e.g., Caffeine, AWS DAX)
- Same eviction concerns as cache-aside

#### 3. Write-through

```
write(key, value):
  cache.set(key, value)
  db.write(key, value)
```
- Write to cache and DB together (cache often does the DB write itself)
- Pro: cache is always consistent with DB
- Con: every write pays cache latency; need to handle DB failures

#### 4. Write-behind (write-back)

```
write(key, value):
  cache.set(key, value)
  queue.async(db.write(key, value))
```
- Writes acknowledged immediately by cache
- DB write happens asynchronously
- Pro: very fast writes
- Con: **data loss risk** if cache crashes before DB write
- Con: harder consistency
- Use case: high-volume non-critical writes (analytics counters)

#### 5. Refresh-ahead (proactive)

```
on(near-expiry):
  recompute(key)
  cache.set(key, v, new_ttl)
```
- Refresh keys before they expire
- Pro: no cold-cache spikes
- Con: extra background work; can refresh unused keys

#### 6. Cache-aside + write-through (hybrid)

Read = lazy; write = both cache and DB. Common in practice.

### Eviction policies

| Policy | Behavior | Use |
|---|---|---|
| **LRU** (Least Recently Used) | Evict the one least recently accessed | General default |
| **LFU** (Least Frequently Used) | Evict the least-used historically | Stable popularity workloads |
| **FIFO** | Oldest first | Simple, rarely best |
| **TTL** | Expire after time, no LRU | Time-bounded data |
| **Random** | Random | Memcached's secret weapon (cache-line friendly) |
| **W-TinyLFU** | Hybrid LRU+LFU with admission | Caffeine; very good hit rate |

Redis offers several: `allkeys-lru`, `volatile-lru`, `allkeys-lfu`, `noeviction`, `allkeys-random`, …

### TTL strategies

- **Static TTL**: every key expires at the same horizon (e.g., 5 min)
- **Jittered TTL**: random offset added (`ttl ± 20%`) to avoid synchronized expirations → stampede
- **Sliding TTL**: refresh on access
- **Adaptive TTL**: shorter for hot keys (frequent invalidations), longer for cold

### The cache stampede / dog-pile problem

When a popular key expires, *all* clients miss simultaneously, all hit the DB, all populate the cache. DB gets crushed.

Mitigations:
1. **Singleflight / mutex**: only one client computes the value; others wait or serve stale
2. **Probabilistic early expiry**: clients re-compute slightly before TTL with probability (paper: "XFetch")
3. **Stale-while-revalidate**: serve the expired value to current request, asynchronously refresh
4. **Pre-warm**: refresh-ahead pattern
5. **Lock with SETNX**: first client acquires lock, recomputes; others wait or serve stale

#### Singleflight in pseudo-Redis
```python
def get_with_singleflight(key):
    v = redis.get(key)
    if v: return v
    lock = redis.set(f"lock:{key}", 1, NX=True, EX=10)
    if lock:
        try:
            v = compute()
            redis.set(key, v, EX=600)
            return v
        finally:
            redis.delete(f"lock:{key}")
    else:
        # wait or serve stale
        return stale_or_wait(key)
```

### Invalidation strategies

The hard problem. Options:

1. **TTL-only (best-effort)** — accept some staleness; simplest; great for ranked feeds, leaderboards
2. **Explicit invalidation on write** — `cache.delete(key)` in the write path
3. **Versioned keys** — `user:42:v123`; bump version on change. Old keys eventually evict.
4. **Tagged invalidation** — group related keys under a tag; invalidate the tag
5. **CDC-based** — subscribe to DB change stream; invalidate affected keys
6. **Event-driven** — services emit "X changed" events; subscribers invalidate

> **Senior take:** "Cache invalidation" is the polite name; in practice you pick a model that minimizes staleness pain. Most consumer apps tolerate 30s of staleness; banking apps don't.

### Thundering herd vs cache stampede

- **Stampede**: many clients all miss a single expired key → DB overload
- **Thundering herd**: many clients wake up to compete for a resource (e.g., distributed lock)
- Mitigations overlap (singleflight, jitter)

### Cache penetration

Requests for keys that don't exist in DB (e.g., scanning for valid IDs) → every request hits DB.

Mitigations:
- Negative cache: cache "not found" with short TTL
- Bloom filter: probabilistically reject "definitely not in DB" keys
- Validate inputs at API edge

### Cache avalanche

Many keys expire at the same time → mass miss. Caused by uniform TTL.

Mitigation: jitter TTLs.

### Hot key

One key receives disproportionate reads. Symptoms: one Redis shard saturated.

Mitigations:
- Replicate the value across multiple key suffixes (`leaderboard:0..9` → randomized read)
- Use a local in-process cache as L1 (Caffeine + Redis as L2)
- CDN for read-only data
- Read replicas

### Local cache vs distributed cache

- **Local** (in-process): zero network latency; per-instance; cache coherence is a problem (different instances see different data)
- **Distributed**: shared state; one source of truth; ~1 ms network latency

Common pattern: L1 local cache + L2 Redis. Pub/sub or short TTL to invalidate L1 across instances.

### Common misconceptions

- "Just slap Redis in front" — invalidation will haunt you
- "Cache hit ratio is the only metric" — also: tail latency, eviction rate, stampede frequency
- "Memcached is dead" — still excellent for pure KV at scale
- "Cache hides DB issues" — yes, but it creates new failure modes (cache outage = thundering herd on DB)

### Interview traps

1. **"How do you keep cache and DB consistent?"** — strict consistency is hard; pick TTL or invalidation; explain trade-offs. Mention CDC.
2. **"What's wrong with `cache.set` then `db.write`?"** — if cache succeeds and DB fails, you have a phantom value.
3. **"How to handle a hot key?"** — replicate, L1 cache, CDN, sub-sharding.
4. **"What if Redis goes down?"** — fall back to DB (graceful degrade); rate-limit if necessary; pre-warm on recovery.
5. **"Should you cache writes?"** — for write-heavy idempotent counters, yes (write-back); for transactional writes, no (just invalidate).

---

## Real examples

### E-commerce product page

- Cache key: `product:{sku}:v{schema_version}`
- TTL: 10 min with jitter
- Invalidation: `cache.delete` on price/stock update; PubSub to invalidate L1 on other instances
- Penetration: bloom filter for valid SKUs; "not found" with 30s TTL

### Session store

- Pure cache-aside, but Redis is the source of truth (no DB)
- TTL: sliding, refreshed on access
- Eviction: `allkeys-lru` is fine
- Persistence: RDB snapshots; AOF for stricter

### Leaderboard

- Redis sorted set (`ZADD`, `ZRANGE`)
- Updated on every score change (write-through)
- TTL: none, or very long
- Hot key: top 100 read constantly; replicate across multiple shards or cache locally

### Feed timeline

- Pre-computed per-user (fan-out write)
- Cache the list as Redis list / sorted set
- New post → push to followers' caches
- Cold user → recompute lazily on read

### Rate limiter

- Redis token bucket / sliding window via sorted set
- Atomic Lua script for check-and-decrement
- No staleness concerns; key is the rate state itself

---

## Common interview questions

1. Explain cache-aside, write-through, write-behind, refresh-ahead.
2. What's the cache stampede problem? How do you prevent it?
3. LRU vs LFU vs TTL.
4. How do you invalidate cache?
5. What's a hot key? Mitigation?
6. How do you keep cache and DB consistent?
7. When would you use write-behind?
8. What happens if Redis goes down?
9. Cache penetration vs avalanche vs stampede.
10. Multi-tier caching (L1 local + L2 Redis).
11. How to cache list responses with pagination?
12. How would you cache user profile with frequent updates?

---

## Detailed answers

### 1. Patterns
- **Cache-aside**: app reads from cache, falls back to DB, populates cache. Most common.
- **Write-through**: writes go to cache + DB synchronously. Cache always consistent.
- **Write-behind**: cache writes async to DB. Fast, risky on cache crash.
- **Refresh-ahead**: refresh before expiry to avoid cold-cache spikes.

### 2. Stampede
Many concurrent requests miss a popular key → DB overload. Fix: singleflight (lock + compute + populate), probabilistic early refresh, stale-while-revalidate, jittered TTL.

### 3. Eviction
- LRU: time-based recency
- LFU: frequency over time
- TTL: time bound, ignores access
Picks depend on workload — LRU for general use, LFU for stable popularity, TTL for time-bounded data.

### 4. Invalidation
- TTL (best-effort)
- Explicit `cache.delete` on write
- Versioned key (`user:42:v123`)
- Tag-based (groups of related keys)
- CDC / event stream
Choose by staleness tolerance.

### 5. Hot key
A key receiving > 10x normal traffic. Mitigation: L1 in-process cache, key sub-sharding (`product:42:#{shardId}`), CDN, read replicas.

### 6. Cache + DB consistency
You don't get strict consistency without coordination. Options:
- TTL: accept brief staleness
- Read-after-write: serve from primary briefly
- Distributed lock during update
- CDC: stream DB changes → invalidate
- Versioned keys: bump version on write; readers always get current
Discuss the trade-off: stronger consistency = more latency.

### 7. Write-behind
For high-volume writes where some delay/loss is acceptable (analytics counters, click counts). Risk: cache failure = data loss. Mitigate with replicated cache + AOF persistence.

### 8. Redis down
- Application detects via timeouts / circuit breaker
- Fallback: serve from DB (with rate limiting to avoid DB overload)
- Pre-warm on recovery
- Failover to replica if using Redis Sentinel / Cluster
Design app to **degrade gracefully** — many require cache to function = bad architecture.

### 9. Three terms
- **Stampede**: many requests for the same expired key
- **Avalanche**: many keys expire simultaneously (uniform TTL)
- **Penetration**: requests for nonexistent keys

### 10. Multi-tier
L1 = in-process LRU (Caffeine, Node `lru-cache`); L2 = Redis. Reads check L1 → L2 → DB. Invalidate L1 via short TTL or pub/sub. Reduces Redis load and tail latency.

### 11. Paginated lists
- Cache by `(filter, page, size)` — but TTLs explode for many filter combos
- Better: cache the underlying objects, fetch list keys from DB, then `MGET` from cache
- Or: cache only the first page (most common)

### 12. Frequent updates
- Short TTL (~30s) + lazy invalidation
- Or write-through on each update
- Or CDC: stream `users` table changes to cache via Debezium

---

## Practical coding examples

### Cache-aside with stampede mitigation
```javascript
async function getWithSingleflight(key, compute) {
  const v = await redis.get(key);
  if (v) return JSON.parse(v);

  const lockKey = `lock:${key}`;
  const gotLock = await redis.set(lockKey, '1', 'NX', 'EX', 10);
  if (gotLock) {
    try {
      const fresh = await compute();
      const ttl = 600 + Math.floor(Math.random() * 60);  // jitter
      await redis.set(key, JSON.stringify(fresh), 'EX', ttl);
      return fresh;
    } finally {
      await redis.del(lockKey);
    }
  } else {
    await sleep(50 + Math.random() * 50);
    return getWithSingleflight(key, compute);
  }
}
```

### Stale-while-revalidate
```javascript
async function get(key, compute) {
  const cached = await redis.get(key);
  const meta = await redis.get(`${key}:meta`);
  const exp = parseInt(meta || '0', 10);
  const stale = Date.now() > exp;

  if (cached && !stale) return JSON.parse(cached);

  if (cached && stale) {
    refreshInBackground(key, compute);  // fire-and-forget
    return JSON.parse(cached);
  }
  return await refreshNow(key, compute);
}
```

### Versioned key invalidation
```javascript
// On write
await db.update(user);
await redis.incr(`user:${user.id}:version`);

// On read
const v = await redis.get(`user:${id}:version`);
const cached = await redis.get(`user:${id}:v${v}`);
```

### Negative cache (penetration mitigation)
```javascript
const cached = await redis.get(key);
if (cached === '__MISS__') return null;
if (cached) return JSON.parse(cached);

const v = await db.get(key);
if (v === null) await redis.setex(key, 30, '__MISS__');
else await redis.setex(key, 600, JSON.stringify(v));
return v;
```

### Atomic counter (Redis)
```javascript
const newCount = await redis.incrby('orders:count', 1);
```

---

## Common mistakes

- Uniform TTL → cache avalanche
- No stampede protection → DB melts on popular key expiry
- Caching huge objects (every read pays serialization)
- Failing to invalidate on write (stale forever)
- Treating Redis as durable (it isn't, by default — configure persistence!)
- L1 cache without invalidation across instances
- Caching at every layer redundantly (pay cost N times)
- Ignoring metrics (hit ratio, eviction rate, latency)

---

## Senior engineer discussion points

- **Stale-while-revalidate** (RFC 5861) for HTTP; same principle in app caches
- **Probabilistic early refresh** ("XFetch" paper) — elegant stampede solution
- **CDC for cache invalidation** — Debezium → Kafka → cache invalidator
- **Read-your-writes via short cache TTL on write** — write path sets a shorter TTL temporarily
- **Cost of cache layer ops** — monitoring, capacity, failures
- **Cache as a first-class part of the data model**, not an afterthought — design with invalidation in mind
- **Why some teams skip distributed cache** — local cache + replicas suffice for moderate scale

---

## Revision notes

- Patterns: cache-aside / write-through / write-behind / refresh-ahead
- Eviction: LRU (default), LFU (stable hot keys), TTL, W-TinyLFU
- TTL with jitter to avoid avalanche
- Singleflight + early refresh + stale-while-revalidate → no stampede
- Negative cache + bloom filter → no penetration
- Hot key: L1, sub-shard, CDN, replicas
- Invalidation: TTL / explicit / versioned / tagged / CDC
- Multi-tier (L1 in-process + L2 Redis) reduces Redis load
- Redis down → graceful fallback to DB, rate-limit
- Cache + DB consistency is best-effort; embrace bounded staleness
