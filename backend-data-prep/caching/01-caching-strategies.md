# Caching Strategies

## Why this matters in backend interviews

- **Every system design round** at scale-focused companies asks about caching.
- **Senior signal**: knowing **invalidation strategy** and **stampede prevention** — not just "use Redis."
- Production debugging questions: cache stampede, stale data, hot keys, eviction storms.

> "There are only two hard things in Computer Science: cache invalidation and naming things." — Phil Karlton. Interviewers test the first one.

---

## Intuitive teaching layer — start here if caching feels abstract

Forget databases and Redis for a second. Imagine you're working at a desk.

- The **basement archive** holds every document the company has ever produced. Slow to walk down, but authoritative. **That's your database.**
- Your **desk drawer** holds the few documents you reach for all day. Instant. **That's your cache.**
- Each morning the drawer starts empty. Throughout the day you pull copies from the basement and stash them in the drawer.

Now map the patterns to drawer behavior:

| Pattern | Plain English |
|---|---|
| **Cache-aside** | "I check my drawer first. If it's not there, I walk to the basement, grab it, photocopy it into my drawer, and use it." |
| **Read-through** | "I have an assistant who manages my drawer. I just ask the assistant; they decide when to refill from the basement." |
| **Write-through** | "When I update a document, I update *both* my drawer copy and the basement copy at the same moment." |
| **Write-back** | "I update only my drawer right now. A courier will sync it to the basement later. Risky if the office burns down." |
| **Refresh-ahead** | "Before my drawer copy gets too old, I proactively refresh it from the basement so it's never stale at peak time." |
| **TTL** | "I throw out drawer copies every 5 minutes because someone else might have edited the basement version." |
| **Invalidation** | "When I change the basement copy, I rip up the drawer copy so nobody uses the old one." |
| **Stampede** | "Everyone's drawer copy expires at noon. Now 200 people all walk to the basement at once. Chaos." |
| **Hot key** | "Only one document is so popular that *everyone's* drawer just contains that one. The basement librarian is overwhelmed." |

If at any point in the rest of this doc you feel lost, come back to the desk drawer.

### First principles — why a cache works at all

Two physics-level facts justify the entire caching world:

1. **Locality of reference.** Programs and users don't access data uniformly. The 80/20 rule is conservative — often 1% of keys serve 99% of traffic. A small fast tier near the hot 1% beats scaling the slow tier.
2. **Memory beats disk by orders of magnitude.**
   - L1 cache: ~1 ns
   - RAM: ~100 ns
   - SSD: ~100 µs (1,000x slower than RAM)
   - Network round-trip in datacenter: ~500 µs
   - Spinning disk seek: ~10 ms (100,000x slower than RAM)
   - Cross-region network: ~100 ms (1,000,000x slower than RAM)

The cache exploits both: keep the hot working set in fast memory close to the consumer. Everything else in this doc is engineering around those two facts.

### Why interviewers care

A candidate who says "I'd add Redis" is a junior. A candidate who says "I'd add Redis, but invalidation here is non-trivial because users expect read-your-writes; let me discuss TTL with jitter vs. CDC vs. versioned keys" is a senior. Caching is the cleanest proxy for whether you understand:

- **Performance reasoning** — latency budgets, throughput math, p99 vs. mean.
- **Consistency under cache** — how data goes stale, who notices, what breaks.
- **Distributed-system invalidation** — multi-instance coherence, the hard parts.
- **Failure modes** — cache outage, stampede, hot keys, eviction storms.

That's why every system design round ends up here.

### Common beginner confusion (pin these to your forehead)

- **"Just add a cache."** No. Adding a cache turns one problem (slow DB) into three problems (slow DB + invalidation + cache outage handling). Worth it, but don't pretend it's free.
- **"TTL solves staleness."** TTL only *bounds* staleness; it doesn't eliminate it. A 5-min TTL means readers can see 5-min-old data. For "show me my just-saved profile," that's a bug.
- **"Redis is a cache."** Redis is a fast in-memory data store. With AOF + replication, it can be a primary store. Calling Redis "a cache" is the same category error as calling Postgres "a backup tool."
- **"Cache stampede won't happen to me."** It will, on the day your product goes viral. Design for it on day one — the cost is one mutex.
- **"Why not cache everything?"** Cost (RAM is expensive), invalidation surface (every cached thing is a thing to invalidate), cold start (first miss is slow), and serialization (a 10 MB blob you read 1000 times burns CPU on `JSON.parse` 1000 times).

### Progressive concept ladder (build understanding in this order)

1. **Simplest possible cache** — a hashmap in your process: `if (map.has(k)) return map.get(k); else compute and store.` That's it. That's a cache.
2. **Add a size bound** — now you need eviction. Pick LRU and you've reinvented a basic application cache.
3. **Add a TTL** — now you handle data that changes. Now you have staleness questions.
4. **Add explicit invalidation** — now you handle data that *should* change immediately. Now you have correctness questions.
5. **Move it out of process** — many app instances, one shared cache (Redis). Now you have network, serialization, and partial-failure concerns.
6. **Handle the popular key** — one key crushes one Redis shard. Now you need sub-sharding or an L1 in-process tier.
7. **Handle expiry storms** — popular key expires at the same instant on every instance. Now you need singleflight + jitter + stale-while-revalidate.
8. **Handle the cold start** — cache is empty after deploy. Now you need warm-up jobs or refresh-ahead.
9. **Handle the data model** — versioning, tag invalidation, CDC. Now you're a senior engineer.

Most candidates can describe step 1–3. Senior candidates skate to step 7–9 in the interview.

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

#### Mental model — layered caches as concentric circles

Picture each layer as a moat around the database:

```
            Request
              |
              v
   +-----------------------+
   |     Browser cache     |   ~0 ms   (per user)
   +-----------------------+
              |
              v
   +-----------------------+
   |          CDN          |   ~10 ms  (per region, shared by users)
   +-----------------------+
              |
              v
   +-----------------------+
   |  API gateway / proxy  |   ~1 ms   (per datacenter)
   +-----------------------+
              |
              v
   +-----------------------+
   |   App in-process LRU  |   ~0.001 ms (per instance — L1)
   +-----------------------+
              |
              v
   +-----------------------+
   |    Redis / Memcached  |   ~1 ms   (per cluster — L2)
   +-----------------------+
              |
              v
   +-----------------------+
   |       Database        |   ~10-50 ms (the slow truth)
   +-----------------------+
```

Each layer's job is to **absorb traffic so the inner layer sees less of it.** If your CDN hit rate is 95%, only 5% of traffic reaches your app. If your Redis hit rate on that 5% is 95%, only 0.25% reaches the DB. That's how a single Postgres can serve a global product.

> Bridge: the rest of this doc focuses on the **L1/L2/DB triangle** (in-process + Redis + DB) because that's where backend engineers spend their time. CDN and browser caching show up in the frontend/SRE rounds.

### Caching patterns

#### 1. Cache-aside (lazy loading) — most common

##### Mental model

The app is the **librarian**. The cache is dumb storage; the DB is the source of truth. The librarian always checks the cache first, walks to the DB only on a miss, and remembers to drop the cached copy when something changes.

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

##### Step-by-step walkthrough — hit vs miss

```
        HIT path (fast)                       MISS path (slow first time)

  App                                    App
   |  GET key                             |  GET key
   v                                      v
  Cache  ---> value found ---> App      Cache  ---> nil
                                          |
                                          |  GET key
                                          v
                                         DB   ---> value
                                          |
                                          |  SET key=value, TTL=300
                                          v
                                         Cache
                                          |
                                          v
                                          App
```

Notice the asymmetry: the hit is one hop; the miss is three hops *plus* the DB query. That's why a high hit rate is everything — a 99% hit rate is roughly an order of magnitude better p99 latency than 90%.

- App is responsible for cache management
- Only requested data is cached (lazy)
- Risk: first request after invalidation is slow
- Risk: stampede if many requests hit the same cold key simultaneously

#### 2. Read-through

##### Mental model

Same librarian behavior, but the librarian is **inside the cache library**, not in your app. Your code just asks the cache; the cache fetches from the DB on a miss. You delegated the cache-aside boilerplate to the cache library.

Like cache-aside, but the cache itself talks to the DB on miss:
```
read(key):
  return cache.get_or_load(key, () => db.get(key))
```
- Cache provider abstracts DB access (e.g., Caffeine, AWS DAX)
- Same eviction concerns as cache-aside
- Trade-off: less app code, but you need a cache library that supports "loader" callbacks. Redis itself does not — that's why most server-side caches in practice are cache-aside, not read-through.

#### 3. Write-through

##### Mental model

Every write is a **dual-update transaction**: cache + DB go together. The cache is never older than the DB. The price is that every write is slower (you pay both writes), and partial failure (cache wrote, DB failed, or vice versa) is now your problem.

```
write(key, value):
  cache.set(key, value)
  db.write(key, value)
```
- Write to cache and DB together (cache often does the DB write itself)
- Pro: cache is always consistent with DB
- Con: every write pays cache latency; need to handle DB failures
- Subtle trap: ordering matters. If you set cache first and DB write fails, you've poisoned the cache with data the DB rejected. Safer ordering: write DB, then set cache (or just delete cache and let the next read re-populate).

#### 4. Write-behind (write-back)

##### Mental model

You **lie to the user** in a controlled way: tell them "saved!" the moment the cache has it, then sync to the DB in the background. Massive write throughput, but if the cache crashes between ack and DB write, that data is **gone**. Use for things where loss is tolerable — view counts, analytics — never for orders or payments.

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

##### Mental model

You **don't wait for expiry**. As the TTL gets close to zero, a background task quietly recomputes and replaces the value. From the user's perspective, the cache never expires — it just keeps being warm. Cost: you do work for keys that may never be read again.

```
on(near-expiry):
  recompute(key)
  cache.set(key, v, new_ttl)
```
- Refresh keys before they expire
- Pro: no cold-cache spikes
- Con: extra background work; can refresh unused keys
- Sweet spot: small set of *very* hot keys (homepage, top-N leaderboard) where the recompute is cheap relative to traffic.

#### 6. Cache-aside + write-through (hybrid)

Read = lazy; write = both cache and DB. Common in practice.

### Eviction policies

##### Mental model — eviction is the "who do I kick out?" question

A cache with infinite RAM has no eviction policy. The real world is finite: when memory fills, *something* must go. The eviction policy is your **guess about the future based on the past**. LRU guesses "if you haven't used it recently, you won't use it soon." LFU guesses "if you rarely use it, you won't start now." Each is right most of the time and wrong some of the time, and the wrong cases are how cache wars start.

| Policy | Behavior | Use |
|---|---|---|
| **LRU** (Least Recently Used) | Evict the one least recently accessed | General default |
| **LFU** (Least Frequently Used) | Evict the least-used historically | Stable popularity workloads |
| **FIFO** | Oldest first | Simple, rarely best |
| **TTL** | Expire after time, no LRU | Time-bounded data |
| **Random** | Random | Memcached's secret weapon (cache-line friendly) |
| **W-TinyLFU** | Hybrid LRU+LFU with admission | Caffeine; very good hit rate |

Redis offers several: `allkeys-lru`, `volatile-lru`, `allkeys-lfu`, `noeviction`, `allkeys-random`, …

##### LRU vs LFU on a sample access pattern

Suppose cache capacity = 3. Access sequence: `A B C A A A B D`. Compare what each policy evicts when `D` arrives:

```
Time:    1  2  3  4  5  6  7  8
Access:  A  B  C  A  A  A  B  D

LRU recency rank (most recent → least at t=7):  B, A, C
At t=8 we add D, must evict 1. LRU evicts C (least recently used).
Final cache: { A, B, D }   ← keeps A which is hot, drops C (only seen once long ago). Reasonable.

LFU frequency count at t=7: A=4, B=2, C=1
At t=8 we add D, must evict 1. LFU evicts C (lowest frequency).
Final cache: { A, B, D }   ← same outcome here. Both agree C is loser.

Now consider: A A A A B C D (capacity 3)
LRU keeps { B, C, D } at the end — A has lowest recency.
LFU keeps { A, ?, ? } — A's count is 4, way ahead. A survives.

Lesson: under a sudden traffic shift, LRU adapts faster.
Under stable popularity, LFU has higher hit rate.
```

That's why workloads with stable hot keys (a leaderboard of celebrities) prefer LFU, while bursty workloads (a viral article) prefer LRU.

### TTL strategies

- **Static TTL**: every key expires at the same horizon (e.g., 5 min)
- **Jittered TTL**: random offset added (`ttl ± 20%`) to avoid synchronized expirations → stampede
- **Sliding TTL**: refresh on access
- **Adaptive TTL**: shorter for hot keys (frequent invalidations), longer for cold

### The cache stampede / dog-pile problem

##### Mental model

Imagine 1000 customers showing up at a coffee shop the instant a "free coffee" coupon expires. They all rush the counter simultaneously asking for the *next* deal. One barista, 1000 customers — that barista is the DB after the popular key's TTL hits zero. **Singleflight** is the manager saying "only one of you walks to the counter; the rest of you wait two seconds and I'll hand you the same coffee."

When a popular key expires, *all* clients miss simultaneously, all hit the DB, all populate the cache. DB gets crushed.

##### ASCII — stampede vs singleflight

```
WITHOUT SINGLEFLIGHT (the problem):

  t=0  Cache key "homepage" expires.
  t=1  1000 concurrent requests arrive.

         R1 R2 R3 ... R1000
          \  |  /    /
           \ | /    /
            v v   v
          [ CACHE ]  --> all MISS
            | | | ... |
            v v v ... v
          [ DATABASE ]   <-- 1000 identical queries.
                              CPU pegged, p99 latency explodes,
                              connection pool exhausted.

WITH SINGLEFLIGHT (the fix):

  t=0  Cache "homepage" expires.
  t=1  1000 concurrent requests arrive.

         R1 R2 R3 ... R1000
          \  |  /    /
           \ | /    /
            v v   v
          [ CACHE ]  --> all MISS
              |
              v
       SETNX lock:homepage  (only R1 gets it)
              |
              v
            R1 ----> [ DATABASE ]  <-- 1 query
              |
              v
            SET cache.homepage = value, TTL=300
            DEL lock:homepage

   R2..R1000 either:
     (a) sleep 50ms, retry GET cache -> HIT
     (b) serve stale value if available  (stale-while-revalidate)
```

Mitigations:
1. **Singleflight / mutex**: only one client computes the value; others wait or serve stale
2. **Probabilistic early expiry**: clients re-compute slightly before TTL with probability (paper: "XFetch")
3. **Stale-while-revalidate**: serve the expired value to current request, asynchronously refresh
4. **Pre-warm**: refresh-ahead pattern
5. **Lock with SETNX**: first client acquires lock, recomputes; others wait or serve stale

##### Step-by-step — Redis `SETNX` distributed lock + TTL

Why is `SETNX` (set-if-not-exists) the trick? It's the only Redis command guaranteed atomic across all clients. Without it, two clients could both check "lock missing → set lock" and both proceed. With it, only one client wins the race.

```
1. Client A:  SET lock:homepage <ownerA> NX EX 10
              -> returns "OK"  (A is now the leader, lock held 10s)

2. Client B:  SET lock:homepage <ownerB> NX EX 10
              -> returns nil   (B is a follower)

3. A computes the value, writes cache, deletes the lock with a Lua
   script that checks ownership ("only delete if value == ownerA").
   Why Lua? If A pauses (GC), the TTL expires, C acquires the lock,
   then A wakes up and DELs C's lock. The ownership check prevents
   that "phantom unlock".

4. B retries the cache, gets a HIT, returns.
```

Three traps to call out in an interview:
- **No TTL on the lock** → if the leader crashes, the key is held forever.
- **Plain `DEL`** without owner check → the phantom-unlock bug above.
- **One Redis node assumed safe under failover** → Redlock and the Kleppmann debate live here.

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

## Interview storytelling — how to *narrate* the answer

Most candidates list facts. Senior candidates tell a story with trade-offs. Below are three classic prompts with how to walk through them.

### Story 1 — "Design caching for a hot product page (Amazon style)"

Walk the interviewer down this path, **out loud**:

1. **Clarify the workload.** "How read-heavy? Pricing updates per second? Do we need read-your-writes for the seller editing price?" — establishing constraints before answering shows seniority.
2. **Pick the layers.** Browser/CDN for the static parts (images, description). Application-tier L1 + Redis L2 for the dynamic parts (price, stock, ratings).
3. **Choose a pattern.** Cache-aside on Redis. Why? Most flexible; Redis isn't a read-through cache.
4. **Key design.** `product:{sku}:v{schemaVersion}`. Schema version lets you do mass invalidation by deploying a new version.
5. **TTL.** 60s with ±20% jitter → caps staleness, prevents avalanche.
6. **Stampede.** Singleflight + stale-while-revalidate. Justify: a single product page can do 10k RPS at peak.
7. **Hot key.** Sub-shard the popular SKU across `product:{sku}:0..9` and round-robin reads.
8. **Invalidation.** On seller edit, explicit `DEL` + publish an event to invalidate L1 across instances.
9. **Failure mode.** Redis down → circuit breaker, fall back to DB with rate limiting, serve last-known-good from L1. Pre-warm on recovery.

The interviewer doesn't need you to be right about every number. They need to see **you reason about trade-offs in order**.

### Story 2 — "The cache went down. What happens?"

Don't say "we fall back to the DB." Say *why* that's dangerous and how to make it safe:

- Without the cache, every request is a DB query. If the cache normally absorbs 99% of reads, the DB now sees **100x its baseline load**. It melts in seconds.
- Mitigations: **circuit breaker** at the cache client; **request coalescing** (singleflight against the DB); **adaptive rate limiting** at the API gateway; **degraded responses** (serve last-known-good from local memory, or a stripped-down version of the page); **read replicas** for the DB so the primary survives writes.
- Recovery: pre-warm the cache from a snapshot or with a background sweep before reopening the floodgates.

### Story 3 — "Design a rate limiter on Redis"

- Clarify: per-user? per-IP? per-endpoint? **Burst** or **steady-state**?
- Algorithms in order of sophistication:
  - **Fixed window** — simplest: `INCR + EXPIRE`. Edge case: 2x burst at window boundaries.
  - **Sliding window log** — sorted set of timestamps; precise; uses memory proportional to limit.
  - **Sliding window counter** — two fixed windows interpolated; cheap and decent.
  - **Token bucket** — most flexible; allows bursts up to bucket size; needs Lua for atomicity.
- Make it atomic. Lua script, not application-side check-then-set.
- Distributed concerns: clock skew across servers, Redis Cluster (keep all user's keys on same slot via hashtag `{user:42}`).
- Failure mode: if Redis is down, **fail open or fail closed**? For login attempts, fail closed (security > availability). For ad serving, fail open (revenue > correctness).

Each of these stories is a 4-minute monologue. Practice them out loud until they're muscle memory.

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
