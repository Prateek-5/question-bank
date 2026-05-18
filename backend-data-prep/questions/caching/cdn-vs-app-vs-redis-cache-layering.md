# CDN vs App vs Redis — Multi-Tier Cache Layering

## Source / Origin
- Standard architecture in modern web stacks: Cloudflare/Fastly edge → app-tier in-process cache (Caffeine, Guava, lru-cache) → Redis → DB.
- Documented in High Performance Browser Networking (Grigorik) and the Cloudflare engineering blog.
- Companion concept doc: `backend-data-prep/caching/01-caching-strategies.md` — multi-tier section.
- Interview prompt: "Walk me through the cache layers between a user's browser and your Postgres."

## Why this question matters in interviews
Multi-tier caching is the **system design backbone**. Senior candidates must be able to (a) name every tier between user and DB, (b) justify what each tier caches, (c) reason about invalidation propagation across tiers, and (d) calculate latency/cost contributions. Missing tiers is a junior mistake; describing them without invalidation strategy is a mid-level mistake; pricing the trade-offs is the senior answer.

## Concepts involved

### Syntax to lock in

The canonical stack:
```
Browser cache (HTTP cache-control)
   │
   ▼
CDN edge (Cloudflare, Fastly, CloudFront)
   │
   ▼
App-tier in-process cache (Caffeine, lru-cache, in-memory Map)
   │
   ▼
Distributed cache (Redis, Memcached)
   │
   ▼
Database (Postgres, MySQL, DynamoDB)
```

HTTP cache headers (browser + CDN):
```
Cache-Control: public, max-age=300, stale-while-revalidate=60
Cache-Control: private, max-age=0, no-cache    (per-user)
Cache-Control: public, max-age=31536000, immutable    (assets)
ETag: "v3-abc123"
```

### Edge cases / interview traps
1. **Invalidation propagation lag** — invalidating Redis doesn't invalidate the CDN. You need a purge API call to the CDN and possibly a wait. Multi-tier invalidation has latency.
2. **Per-user vs shared caches** — CDN and Redis are shared; app-tier in-memory is per-instance. Don't cache per-user data in shared tiers without keying carefully.
3. **TTL stacking** — if browser TTL=300, CDN TTL=600, Redis TTL=900, real freshness is bounded by the *shortest* upstream TTL. Misalignment causes confusing staleness.
4. **L1 (in-process) coherence** — N app instances each with their own L1 cache. After Redis invalidates, L1 still serves stale until L1's own TTL or explicit pub/sub invalidation.
5. **Hot-key amplification at L1** — when a key is hot enough to live in every instance's L1, Redis sees ~1 fetch per L1 refresh per instance. Still cheap.
6. **Cache hierarchy violations** — writing to L1 directly when L2 hasn't been written is a foot-gun. Always write down the stack (DB → L2 invalidate → L1 invalidates via pub/sub).
7. **CDN cache key includes Vary headers** — `Vary: Accept-Encoding, Accept-Language` partitions the CDN cache; bad Vary settings cause every user to be a miss.
8. **Negative caching** — CDNs cache 404s and 500s by default for short periods; this can lock in error pages after a fix is deployed. Set `Cache-Control: no-store` on error responses.
9. **Stampede coordination** — a CDN miss to origin triggers N requests if N CDN edges miss simultaneously. Use "request coalescing" / "shielding" at the CDN (Cloudflare's Tiered Cache, Fastly's Origin Shield).

## Mental Model

### The stack with latencies

```
                                  Typical latency      Hit Rate    Capacity
                                  (one user round-trip)
┌─────────────────────────────┐
│ Browser cache (per-user)    │       0 ms              50-90%      MB
└──────────────┬──────────────┘
               │ on miss
               ▼
┌─────────────────────────────┐
│ CDN edge (shared, geo)      │       10-50 ms          80-95%      TB
└──────────────┬──────────────┘
               │ on miss
               ▼
┌─────────────────────────────┐
│ App-tier L1 (in-process)    │       0.01 ms           60-80%      MB-GB per inst
└──────────────┬──────────────┘
               │ on miss
               ▼
┌─────────────────────────────┐
│ Redis / L2 (distributed)    │       1-2 ms            80-95%      GB-TB
└──────────────┬──────────────┘
               │ on miss
               ▼
┌─────────────────────────────┐
│ Database                    │       5-50 ms            —          TB
└─────────────────────────────┘
```

### Hit-rate compounding

```
If each tier has 80% hit rate:
  Browser: 0.80 served
  CDN:    0.16 served  (80% of remaining 20%)
  L1:     0.032 served (80% of remaining 4%)
  L2:     0.0064 served (80% of 0.8%)
  DB:     0.0016 (16 in 10,000)

→ DB sees 1.6% of original request volume.
   Each layer is a 5× reducer.
```

### Invalidation propagation

```
Write happens:
    DB.write ────► L2 (Redis) .del ────► pub/sub ────► L1 instance 1 .del
                                                  └──► L1 instance 2 .del
                                                  └──► L1 instance N .del
    (synchronously)         (synchronously)             (asynchronously)

    For CDN:
    DB.write ────► CDN purge API call ────► CDN edges async invalidate
                  (or: short CDN TTL + accept staleness)
                  (or: surrogate keys / cache tags)
```

## Why interviewers care
- Multi-tier caching is the **default architecture for any serious web product**.
- It tests **layered reasoning** — knowing what each tier optimizes for and why.
- Invalidation across tiers reveals **eventual-consistency literacy**.
- Latency math is a senior interview staple (p50 vs p99 contribution per tier).

## Common beginner confusion
- **"I'll add Redis."** And then? What about the CDN? The browser cache? The L1? "Add Redis" is the answer to one specific question (in-RAM shared cache); not the whole story.
- **"CDN is for static assets only."** Modern CDNs cache HTML, API responses, GraphQL queries — anything with a stable URL and a Cache-Control header. Cloudflare and Fastly explicitly support API caching.
- **"L1 in-process cache is redundant if I have Redis."** L1 saves the Redis round-trip — 1ms vs 0.01ms. For 10,000 RPS that's 10 seconds of compute saved per second of wall time.
- **"All tiers should have the same TTL."** No. CDN TTL is typically much longer (minutes-hours), Redis medium (minutes), L1 short (seconds-minute). Each tier's TTL reflects its invalidation reach.
- **"Invalidation is instantaneous."** Across CDN + L2 + N L1 instances, invalidation has measurable lag. Plan for eventual consistency.

## Brute force approach
**Single tier (Redis only).** Works for many products. Latency floor is the Redis round-trip (~1ms) × every request. CDN would save the trip entirely for cacheable responses.

**No caching at all.** DB sees full request volume. Works until you're past ~1k QPS.

**Cache everything everywhere with long TTLs.** Now invalidation is broken — you can't get fresh data without waiting hours.

## Optimal approach

### Layered design principles
1. **Cache at the highest tier the data type allows.** Public, infrequently-changing data → CDN. User-specific but stable → L1+L2. Highly dynamic → just L2.
2. **Decreasing TTL as you go down the stack.** CDN 1h, L2 5min, L1 30s. Lower tiers absorb invalidation latency from upper tiers.
3. **Invalidate downstream first, then upstream.** Write DB → invalidate L2 → invalidate L1 (via pub/sub) → purge CDN. Reverse order causes a request to re-populate stale data from upstream.
4. **Use surrogate keys for CDN purging.** Tag responses with `Surrogate-Key: user-42 order-list`; purge by tag.
5. **Stale-while-revalidate at every tier** for graceful degradation.

### Tier-specific responsibilities
- **Browser**: assets (immutable), per-user pages with short max-age, private profile data with `no-cache, private`.
- **CDN**: public API responses, HTML pages, static assets, *not* per-user data unless keyed by user (rare).
- **L1 (in-process)**: hot reference data (feature flags, config, top products), small enough to live in every instance.
- **L2 (Redis)**: shared user/session data, expensive query results, hot keys with cross-instance coherence requirements.
- **DB**: source of truth.

### Invalidation strategy
- **Write through DB only.** All caches are projections.
- **Explicit invalidation on writes**: DB → L2.del → pub/sub → L1.del. Async CDN purge if needed.
- **TTL safety net** at every tier — even if invalidation fails, staleness is bounded.
- **Versioned keys / surrogate keys** for mass invalidation.

## Solution

### Three-tier read path (Node.js)

```javascript
const Redis = require('ioredis');
const LRU = require('lru-cache');

const redis = new Redis();
const sub = new Redis();
const l1 = new LRU({ max: 10_000, ttl: 30_000 });

// Subscribe to invalidation events for L1 coherence
sub.subscribe('cache:invalidate');
sub.on('message', (_, key) => l1.delete(key));

async function get(key, loader) {
  // L1
  const fromL1 = l1.get(key);
  if (fromL1 !== undefined) return fromL1;

  // L2
  const fromL2 = await redis.get(key);
  if (fromL2 !== null) {
    const parsed = JSON.parse(fromL2);
    l1.set(key, parsed);
    return parsed;
  }

  // DB
  const value = await loader();
  await redis.set(key, JSON.stringify(value), 'EX', 300);
  l1.set(key, value);
  return value;
}

async function invalidate(key) {
  await redis.del(key);
  await redis.publish('cache:invalidate', key);  // all L1 instances delete locally
  // CDN purge (if applicable):
  // await fetch(`https://api.cloudflare.com/purge`, { method: 'POST', body: ... });
}
```

### CDN cache headers (Express middleware)

```javascript
app.get('/api/trending', async (req, res) => {
  const data = await getTrending();
  res.set('Cache-Control', 'public, max-age=300, stale-while-revalidate=60');
  res.set('Surrogate-Key', 'trending');   // for tag-based CDN purge
  res.set('ETag', `"v${data.version}"`);
  res.json(data);
});

app.get('/api/me', async (req, res) => {
  const me = await getCurrentUser(req);
  res.set('Cache-Control', 'private, max-age=0, no-cache');  // never CDN-cached
  res.json(me);
});
```

### Surrogate-key based CDN purge on write

```javascript
async function updateTrendingItem(id, patch) {
  await db.query('UPDATE products SET ... WHERE id = $1', [id, ...patch]);
  await invalidate(`product:${id}`);
  await fetch(`https://api.fastly.com/service/${SVC}/purge/trending`, {
    method: 'POST',
    headers: { 'Fastly-Key': KEY },
  });
}
```

## Step-by-step dry run

**Scenario:** API endpoint `/api/trending` (public, list of top 10 items). 10,000 RPS globally distributed.

| Layer        | Hit rate | Requests handled | Latency to user |
|--------------|----------|------------------|------------------|
| CDN (300 edges, max-age=300) | 99%   | 9,900 RPS         | 20 ms (edge response) |
| App tier L1 (in-process LRU)  | 50% of remaining | 50 RPS    | 0.01 ms |
| Redis L2     | 90% of remaining | 45 RPS    | 1 ms |
| Database     | 100% of remaining | 5 RPS    | 20 ms |

DB sees **5 RPS** out of 10,000 — a 2000× reduction. Each tier contributes.

Invalidation of trending list (item moved up the ranking):
1. App writes DB.
2. App calls `INVALIDATE trending` → Redis DEL + pub/sub.
3. All L1 instances receive pub/sub message → DELETE from local LRU.
4. App calls CDN purge API with `Surrogate-Key: trending`.
5. ~1 second later: CDN edges purged.
6. Next request from any user: CDN miss → app → L1 miss → L2 miss → DB → repopulate.

The 1-second CDN lag is the realistic floor for cross-region invalidation. Compensate with stale-while-revalidate so users see *some* response during the window.

## How to think aloud in the interview

"Let me walk through the layers from user to DB. Browser cache is first — for static assets it's basically free, and for API responses I use `Cache-Control` to control whether the browser caches at all. Per-user data gets `private, no-cache`; public data gets a max-age.

Next is the CDN — Cloudflare or Fastly. Public, cacheable responses live here. Each edge serves users near them with sub-50ms latency. The CDN absorbs 90+% of traffic for cacheable endpoints. Invalidation is the trade-off — you either set short TTLs and accept some staleness, or you use surrogate keys and call the CDN's purge API on writes.

Then the app tier. Each app instance has an in-process L1 — Caffeine in Java, lru-cache in Node. This saves the Redis round-trip on hot keys, dropping 1ms to 10μs. The risk is incoherence: each instance's L1 is independent. I solve that with a Redis pub/sub channel — when L2 is invalidated, all L1 instances subscribe and delete locally.

Then Redis — the shared distributed L2. This holds session state, hot query results, anything that needs to be shared across app instances. Reads are ~1ms. Writes flow through here for invalidation.

Then the DB — source of truth.

The math is compounding. If each tier achieves 80% hit rate, the DB sees about 0.16% of original traffic — a 600× reduction. That's the goal: keep the DB out of the per-request path.

Invalidation: I write down the stack. DB write, then L2 delete, then pub/sub to all L1 instances, then CDN purge. Going *up* the stack causes the inverse problem — a request slip-through can repopulate stale data from an upper layer."

## Important takeaways

- **Stack: browser → CDN → app-tier L1 → Redis L2 → DB.**
- **TTLs decrease down the stack:** CDN longest, L1 shortest.
- **Invalidate downstream first** (DB → L2 → L1 → CDN), or you'll re-populate stale.
- **L1 + pub/sub** for cross-instance coherence.
- **CDN cache headers (`Cache-Control`, `Surrogate-Key`, `ETag`)** are the API for tier-1 caching.
- **Never CDN-cache per-user data** without explicit user-keyed CDN keys.
- **Stale-while-revalidate** at every tier for graceful degradation.
- **Latency budget per tier:** ~0ms browser, ~30ms CDN, ~0.01ms L1, ~1ms L2, ~20ms DB.

## Variants

1. **Tiered Cache / Origin Shield (Cloudflare/Fastly)** — adds another regional cache layer to reduce origin requests.
2. **Edge KV (Cloudflare Workers KV, Cloudflare D1)** — programmable cache at the edge with ms-level writes.
3. **Two-tier L2 (sharded Redis Cluster + region-local Redis)** — geo-locality for write-light, cross-region-read workloads.
4. **CDN + smart invalidation via webhooks** — DB CDC pipeline calls CDN purge API.
5. **Service-mesh sidecar cache** — Envoy/Linkerd local cache for inter-service calls.
6. **HTTP-level stale-if-error** — serve stale on origin errors.

## Revision notes

> **multi-tier cache layering — 60 second recap**
> - **Stack:** Browser → CDN → App L1 → Redis L2 → DB.
> - **TTL decreases down the stack.** CDN longest, L1 shortest.
> - **Invalidate downstream first:** DB → L2 → pub/sub L1 → CDN purge.
> - **Each tier ~5× reducer** if hit rate is ~80%.
> - **L1 coherence via pub/sub** to all app instances.
> - **CDN keyed by URL + Vary headers + Surrogate-Key for purge.**
> - **Never CDN per-user data** in shared mode.
> - **Stale-while-revalidate everywhere** for graceful degradation.
> - **Trap:** invalidating upstream first; same TTL everywhere; forgetting L1 coherence.
