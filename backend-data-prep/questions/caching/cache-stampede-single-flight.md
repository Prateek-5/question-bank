# Cache Stampede / Thundering Herd — Single-Flight Mitigation

## Source / Origin
- Documented in Facebook's TAO paper (2013) and Memcached/Mcrouter design.
- Term "thundering herd" comes from Linux kernel accept() wakeups; reused in caching.
- Companion concept doc: `backend-data-prep/caching/01-caching-strategies.md` — "Cache stampede" section.
- Classic interview prompt: "Your top trending video page expires at noon; ten thousand requests hit at noon and one second later, the DB is dead. What happened?"

## Why this question matters in interviews
Stampede is the **production war-story bait** in caching interviews. Any candidate can describe cache-aside; the senior is the one who immediately says "wait — what happens at TTL expiry for a hot key?" The interviewer wants you to (a) identify the race condition unprompted, (b) sketch the timeline of N concurrent misses, (c) propose at least two mitigations (single-flight + probabilistic early expiration), and (d) discuss the tradeoffs of each. Missing this question is the difference between a mid-level and a senior offer.

## Concepts involved

### Syntax to lock in

The naive read path that stampedes:
```
function get(key):
    val = cache.get(key)
    if val is not None: return val
    val = db.read(key)              # ← N concurrent misses all hit here
    cache.set(key, val, ttl=300)
    return val
```

The single-flight fix (in-process):
```
inflight = {}                       # key → Promise

function get(key):
    val = cache.get(key)
    if val is not None: return val
    if key in inflight:
        return await inflight[key]
    inflight[key] = load(key)
    try:
        return await inflight[key]
    finally:
        del inflight[key]
```

The distributed single-flight (Redis SETNX lock):
```
function get(key):
    val = cache.get(key)
    if val is not None: return val
    lock_acquired = redis.set(f"lock:{key}", instance_id, NX=True, EX=10)
    if lock_acquired:
        val = db.read(key)
        cache.set(key, val, ttl=300)
        redis.del(f"lock:{key}")
        return val
    else:
        # someone else is loading — wait briefly
        sleep(50ms)
        return get(key)             # retry the read path
```

### Edge cases / interview traps
1. **In-process single-flight doesn't help across instances** — 100 app instances each running their own `inflight` map = 100 concurrent DB calls. Distributed lock or probabilistic methods needed for cross-instance protection.
2. **Lock holder dies** — TTL on the lock is mandatory. Without it, a crashed loader leaves the cache permanently locked.
3. **Wait-and-retry storm** — if the lock TTL is 10s but the loader takes 100ms, waiters busy-loop. Use exponential backoff or pub/sub notification.
4. **Probabilistic early expiration (XFetch)** — readers stochastically decide to refresh before TTL based on age. Avoids the lock entirely. Tradeoff: some over-refreshing, no clean "single fetch" guarantee.
5. **Negative cache stampede** — many readers asking for a non-existent key all miss + fall through to DB. Same stampede. Cache negatives.
6. **Mass invalidation stampede** — `cache.del` on many keys at once → next read for each key stampedes. Stagger invalidations or use versioned keys.
7. **Cold start after deploy** — every app instance starts with empty cache; first request for any popular key stampedes. Pre-warm.
8. **Stampede asymmetry** — if loader takes 500ms and TTL is 300s, the stampede window is 500ms in a 300,000ms cycle (0.17%). Often "good enough" to ignore. Quantify before optimizing.

## Mental Model

### The stampede timeline

```
T=0     Cache populated, TTL=300s. Hot key getting 1000 req/s.
T=300   Cache expires.
T=300.0 Req#1   → cache miss → starts db.read (50ms)
T=300.0 Req#2   → cache miss → starts db.read
T=300.0 Req#3   → cache miss → starts db.read
...
T=300.0 Req#1000 → cache miss → starts db.read
                                  ▲
                                  │
              1000 simultaneous DB queries on the same row.
              DB CPU spikes, connection pool exhausts, latency explodes,
              all 1000 readers wait, more readers stack up behind them.
              "Thundering herd."

T=300.05 First req completes, populates cache.
T=300.05 But all other 999 are already in flight — wasted work.
```

### Single-flight in one picture

```
                    ┌─────────────────┐
Req1 ─► miss ─► is in inflight? NO ─► load() ──┐
Req2 ─► miss ─► is in inflight? YES ─► await ──┤
Req3 ─► miss ─► is in inflight? YES ─► await ──┤
Req4 ─► miss ─► is in inflight? YES ─► await ──┘
                                          │
                                          ▼
                                       single load
                                          │
                                          ▼
                                    all reqs resolve
```

One DB call for N concurrent misses. **The fundamental fix.**

## Why interviewers care
- Real production incidents map directly to this question. Companies have postmortems written about it.
- It tests whether you can think in **concurrency timelines**, not just sequential code.
- It distinguishes between **per-instance** and **cross-instance** mitigations — the cross-instance version forces you to reason about Redis-as-coordination.
- The follow-up "what if the lock holder dies?" leads naturally into Redlock and fencing tokens.

## Common beginner confusion
- **"TTL solves stampede."** It causes stampede. The shorter the TTL, the more often the stampede happens.
- **"Just use a longer TTL."** That delays the stampede; doesn't prevent it. Plus you trade staleness for it.
- **"Stampede only happens at expiry."** Also happens at deploys (cold cache), mass invalidations, and cache flushes. Anywhere the cache transitions from "warm" to "cold" for a hot key.
- **"Single-flight = lock."** Single-flight is the *semantic* (one load per key per concurrent burst). Lock is one *implementation*. Probabilistic methods achieve single-flight semantics without a lock.
- **"In-process inflight Map is enough."** Only for single-instance deployments. With N app instances, you have N concurrent loaders worst case.

## Brute force approach
"Increase TTL to never expire." Works until you need to invalidate. And cache memory fills up.

"Disable cache during high load." Counterintuitive disaster — without cache, the DB sees the full request rate, not just the miss rate.

"Add more DB read replicas." Treats the symptom, not the cause. You can pay for 10x replicas or you can pay for one lock.

## Optimal approach

### Tier 1 — Per-instance single-flight (in-memory)
- `Map<key, Promise>` dedupes concurrent misses *within one process*.
- Free, sub-millisecond, no Redis round-trip.
- **Limit:** each app instance still misses independently. 100 instances = 100 DB calls worst case.

### Tier 2 — Distributed single-flight (Redis SETNX lock)
- One winner per key per concurrent burst across the cluster.
- Lock TTL prevents stuck locks if the holder dies.
- **Limit:** waiters need a strategy — busy-wait, exponential backoff, or pub/sub notification.

### Tier 3 — Probabilistic early expiration (XFetch)
- Stochastic refresh before TTL — readers spread out naturally.
- No lock needed.
- **Limit:** some over-refreshing; not a hard "single load" guarantee.

### Tier 4 — Refresh-ahead
- Keep hot keys warm proactively. The miss never happens. See `refresh-ahead-cache.md`.

### Tier 5 — Stale-while-revalidate
- Serve stale on miss; refresh in background. Latency stays flat even during refresh.

**Realistic stack:** Tier 1 (in-process) + Tier 4 (refresh-ahead for top hot keys) + Tier 5 (stale-while-revalidate as the fallback for everything else).

## Solution

### In-process single-flight (Node.js)

```javascript
const Redis = require('ioredis');
const redis = new Redis();

const inflight = new Map();

async function getWithSingleFlight(key, loader) {
  const cached = await redis.get(key);
  if (cached !== null) return JSON.parse(cached);

  if (inflight.has(key)) {
    return inflight.get(key);
  }
  const promise = (async () => {
    try {
      const value = await loader(key);
      await redis.set(key, JSON.stringify(value), 'EX', 300);
      return value;
    } finally {
      inflight.delete(key);
    }
  })();
  inflight.set(key, promise);
  return promise;
}
```

### Distributed single-flight with Redis lock + pub/sub wakeup

```javascript
async function getDistributed(key, loader) {
  let cached = await redis.get(key);
  if (cached !== null) return JSON.parse(cached);

  const lockKey = `lock:${key}`;
  const lockToken = crypto.randomUUID();
  const acquired = await redis.set(lockKey, lockToken, 'NX', 'EX', 10);

  if (acquired === 'OK') {
    try {
      const value = await loader(key);
      await redis.set(key, JSON.stringify(value), 'EX', 300);
      await redis.publish(`refilled:${key}`, '1');
      return value;
    } finally {
      // safe release — only delete if we still own the lock
      await redis.eval(
        `if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end`,
        1, lockKey, lockToken,
      );
    }
  } else {
    // wait for the lock holder to publish, then re-read cache
    return new Promise((resolve, reject) => {
      const sub = new Redis();
      const timeout = setTimeout(async () => {
        sub.quit();
        // fall back to direct read attempt
        resolve(getDistributed(key, loader));
      }, 500);
      sub.subscribe(`refilled:${key}`);
      sub.on('message', async () => {
        clearTimeout(timeout);
        sub.quit();
        const fresh = await redis.get(key);
        resolve(fresh !== null ? JSON.parse(fresh) : await getDistributed(key, loader));
      });
    });
  }
}
```

### Probabilistic early expiration (XFetch / Vasiliev)

```javascript
function shouldEarlyExpire(writtenAtMs, ttlMs, deltaMs = 100, beta = 1.0) {
  const ageMs = Date.now() - writtenAtMs;
  const xfetch = ageMs + deltaMs * beta * Math.log(Math.random());
  return xfetch >= ttlMs;   // -log(rand) > 0; subtracting brings the trigger earlier
}

async function getWithXFetch(key, loader) {
  const raw = await redis.get(key);
  if (raw === null) return loadAndStore(key, loader);
  const entry = JSON.parse(raw);
  if (shouldEarlyExpire(entry.writtenAt, 300_000)) {
    return loadAndStore(key, loader);
  }
  return entry.value;
}
```

## Step-by-step dry run

**Naive cache-aside, hot key at TTL expiry, 1000 req/s:**

| T (ms) | Event | inflight (Map) | DB queries |
|--------|-------|----------------|------------|
| 0      | TTL expires | — | 0 |
| 0      | Req1 miss → db.read starts | — | 1 |
| 0.5    | Req2 miss → db.read starts | — | 2 |
| 1.0    | Req3 miss → db.read starts | — | 3 |
| ...    | ... | — | ... |
| 50     | Req1000 miss → db.read starts | — | 1000 |
| 50     | Req1 completes, sets cache | — | 1000 |
| 51     | Req1001 — cache hit | — | 1000 |
| 100    | Req1000 completes, sets cache | — | 1000 |

**1000 DB queries for one key.** DB is dying.

**With in-process single-flight (one app instance):**

| T (ms) | Event | inflight | DB queries |
|--------|-------|----------|------------|
| 0      | TTL expires | — | 0 |
| 0      | Req1 miss → not in inflight → start load | `{k:P}` | 1 |
| 0.5    | Req2 miss → in inflight → await P | `{k:P}` | 1 |
| 1.0    | Req3 miss → in inflight → await P | `{k:P}` | 1 |
| ...    | ... | `{k:P}` | 1 |
| 50     | Req1 completes; cache.set; P resolves | `{}` | 1 |
| 50     | All 1000 awaiting reqs resolve simultaneously | `{}` | 1 |

**1 DB query for one key.** Perfect.

**Cross-instance (100 app instances, each with own inflight):**

| Instance | Concurrent misses | DB queries from that instance |
|----------|-------------------|--------------------------------|
| inst-1   | 10                | 1                              |
| inst-2   | 10                | 1                              |
| ...      | ...               | 1                              |
| inst-100 | 10                | 1                              |

**100 DB queries total.** Better than 1000, but still bad. This is why distributed single-flight (Redis SETNX lock) exists.

## How to think aloud in the interview

"Right, this is a classic cache stampede. Let me walk through what happened. The page has a TTL of 5 minutes; at the moment of expiry, you have say 1000 requests per second hitting it. Request #1 misses, starts the DB query, and while that 50ms query is in flight, requests #2 through #N all also miss because the cache hasn't been repopulated yet. They all fire their own DB queries. So instead of one DB query, you get N — possibly hundreds — all for the same row, exhausting the DB connection pool, spiking CPU, and cascading into request timeouts.

The fix has layers. The cheapest layer is in-process single-flight: in each app instance, keep a map of `key → in-flight Promise`. When a request misses, check the map; if there's already a promise, await it instead of starting a new query. This reduces N-per-instance to one-per-instance.

But that's still N queries if you have N app instances. For cross-instance protection, I'd use a Redis lock: `SET lock:key uuid NX EX 10`. The winner does the load and publishes a notification when done; losers either subscribe to the pub/sub channel or briefly retry the read. The lock TTL is critical — without it, a crashed loader would permanently block the key.

A clever alternative is probabilistic early expiration — readers stochastically decide to refresh slightly before TTL based on a randomized function of age. This avoids the lock entirely and spreads refreshes out naturally. Less precise but lock-free.

For top hot keys I'd combine this with refresh-ahead: proactively refresh in the background so the miss never happens at the user-visible path. And I'd flag that mass-invalidation events — `cache.del` on many keys at once — cause the same stampede; either stagger them or use versioned keys."

## Important takeaways

- **Stampede happens at every cache-miss boundary for hot keys.** TTL expiry, deploy cold start, mass invalidation.
- **Single-flight is the canonical fix:** one loader per key per concurrent burst.
- **In-process map** is free and stops per-instance stampedes; doesn't help across instances.
- **Redis SETNX lock with TTL + safe release** stops cross-instance stampedes.
- **Probabilistic early expiration** is a lock-free alternative that spreads refreshes stochastically.
- **Refresh-ahead** makes the miss never happen — best for top hot keys.
- **Always cache negatives.** A non-existent key still stampedes the DB without negative caching.
- **The lock must have a TTL** or a crashed holder kills the system.

## Variants

1. **In-process single-flight only** — sufficient for many systems; cheap, no Redis dependency.
2. **Redis lock + pub/sub wakeup** — distributed single-flight with low-latency waiter notification.
3. **Redis lock + polling** — simpler than pub/sub, slightly higher waiter latency.
4. **XFetch (probabilistic)** — no lock; randomized early refresh.
5. **Refresh-ahead** — completely sidesteps the miss for hot keys. See `refresh-ahead-cache.md`.
6. **Stale-while-revalidate** — serve stale on miss, refresh in background. See `cdn-vs-app-vs-redis-cache-layering.md`.
7. **Sharded hot key** — split the hot key into N replicas (`trending:v1`, `trending:v2`, etc.) so each instance's stampede only hits one shard. See `hot-key-mitigation.md`.

## Revision notes

> **cache stampede / single-flight — 60 second recap**
> - **Problem:** N concurrent misses → N DB calls for one key.
> - **Where it happens:** TTL expiry, cold deploy, mass invalidation.
> - **Fix tier 1:** in-process `Map<key, Promise>` (per-instance single-flight).
> - **Fix tier 2:** Redis `SET lockkey id NX EX 10` (cross-instance lock); winner loads, losers wait/retry.
> - **Fix tier 3:** XFetch — randomized early expiration, lock-free.
> - **Fix tier 4:** refresh-ahead — miss never happens.
> - **Always cache negatives.** Always TTL the lock.
> - **Trap:** in-process only when you have N instances; no lock TTL; no safe lock release.
