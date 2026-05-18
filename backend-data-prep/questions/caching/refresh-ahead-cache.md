# Refresh-Ahead Cache

## Source / Origin
- Originated in Oracle Coherence and Caffeine's `refreshAfterWrite`; adopted by CDN edge caches as "stale-while-revalidate" (RFC 5861) and by Cloudflare Workers `caches.default`.
- Companion concept doc: `backend-data-prep/caching/01-caching-strategies.md` — "Refresh-ahead" section.
- Interview prompt: "Your homepage feed cache misses every 5 minutes and the DB groans. How do you keep latency flat?"

## Why this question matters in interviews
Refresh-ahead is the pattern senior candidates reach for when the interviewer escalates from "design the cache" to "now optimize for p99." It demonstrates that you think in terms of *probability of miss at the worst moment* — not just average hit rate. The senior signal is being able to distinguish refresh-ahead (proactive, asymmetric) from TTL bumping (symmetric, equally stale for everyone) and from stale-while-revalidate (reactive, lazy).

## Concepts involved

### Syntax to lock in

Refresh-ahead with a "refresh window" inside the TTL:
```
TTL = 300s, REFRESH_WINDOW = 60s

get(key):
    entry = cache.get(key)
    if entry is None:
        # cold miss — full load
        value = db.read(key)
        cache.set(key, value, ttl=TTL, written_at=now)
        return value
    age = now - entry.written_at
    if age > TTL - REFRESH_WINDOW:
        # async refresh in background, return current value immediately
        spawn refresh(key)
    return entry.value
```

The key trick: **return the value immediately, refresh in the background**.

### Edge cases / interview traps
1. **Double-refresh storms** — multiple concurrent readers all see "age > TTL - REFRESH_WINDOW" and all spawn refreshes. Need single-flight on the refresh path.
2. **Refresh failure** — what if the background DB read fails? Most implementations *don't* expire the entry — better to serve stale than no data. But you need observability on refresh failure rate.
3. **Refresh queue overflow** — if refresh-ahead is enabled for 10M keys, you can't afford 10M background tasks. Limit to top-N hot keys or use a bounded thread pool.
4. **Stale data window** — between the moment the underlying DB row changed and the next refresh trigger, readers see the old value. Refresh-ahead is *not* a freshness guarantee — it's a latency optimization.
5. **Cold start** — the first reader of a key still pays the full DB latency. Refresh-ahead only helps for *already-warm* keys. Combine with cache warm-up for fully cold systems.
6. **Refresh-on-read vs refresh-on-schedule** — refresh-on-read only triggers if someone reads the key (no traffic = no refresh). A scheduled refresher keeps the key warm independent of traffic.
7. **Per-key refresh tracking** — need to store `written_at` alongside the value. Either as a separate Redis hash field or embedded in the JSON payload.

## Mental Model

```
TTL = 300s, REFRESH_WINDOW = 60s

Age:   0 ──────────────────────── 240 ─────────── 300
        ◄── safe (return cached) ──►◄── refresh ──►◄ expired
                                       window
                                    
       During the refresh window, every read:
        - returns the current (slightly aged) value immediately
        - asynchronously kicks off a refresh
        - the refresh resets `written_at`, sliding the window forward
       
       At T=300 (expiry), if no refresh happened: cold miss next read.
       If refresh succeeded between T=240 and T=300: window resets to T=300, no miss.
```

### Cache-aside vs refresh-ahead — latency profile

```
Time ─►  request1  request2  request3 ... [miss] ... request_k  request_k+1
CACHE-ASIDE:
   p50    1ms      1ms       1ms      ...  150ms  ...  1ms       1ms
                                            ▲
                            every reader at expiry pays the miss

REFRESH-AHEAD:
   p50    1ms      1ms       1ms      ...  1ms    ...  1ms       1ms
                                            ▲
                            miss avoided by background refresh
                            (assuming refresh started in time)
```

## Why interviewers care
- Demonstrates **latency-budget thinking** — flattening the tail, not optimizing the mean.
- Tests whether you understand **proactive vs reactive** cache maintenance.
- Surfaces the **failure-mode question** — what if the refresh itself fails? (A good candidate says "serve stale, alert, retry with backoff.")
- Real-world: this is how CDNs serve hot pages with zero origin spikes; how Coherence handles read-heavy workloads.

## Common beginner confusion
- **"Refresh-ahead is just shorter TTL."** No — shorter TTL means *every* reader at expiry pays the miss. Refresh-ahead pays the miss exactly *zero times* if traffic is high enough.
- **"It avoids stampedes."** Only if you add single-flight on the refresh path. A naive implementation makes the stampede worse — every read in the refresh window spawns its own refresh.
- **"It guarantees freshness."** No. The data can be up to `TTL` stale. Refresh-ahead is a *latency* optimization, not a freshness one.
- **"I'll refresh-ahead everything."** Cost scales with key count × refresh rate. Pick the top N% hottest keys.
- **"Refresh-ahead and stale-while-revalidate are the same."** Closely related — both serve stale + background refresh. The difference: refresh-ahead triggers *before* expiry; stale-while-revalidate triggers *after* expiry but within a grace window.

## Brute force approach
"Just lower the TTL." Now every reader sees fresher data, but every reader at expiry pays the full DB miss. Average latency drops, p99 latency spikes — exact opposite of what we want.

"Schedule a cron job to refresh every key every 60s." Works but doesn't scale beyond a few hundred keys, and refreshes cold keys nobody reads.

## Optimal approach

### When to use refresh-ahead
- **Read-heavy hot keys** (top 1% of traffic).
- **Predictable read patterns** (you can identify which keys are hot).
- **Tolerable staleness** (the data can be a few minutes old).
- **Expensive miss cost** (e.g., joins, derived data, ML scoring).

### Implementation choices
- **In-band, async**: on read, check age; if in refresh window, fire-and-forget a refresh task. Simplest.
- **Out-of-band scheduler**: a background worker iterates the hot-key set and refreshes on a schedule. Decouples refresh from traffic.
- **Hybrid**: in-band for the long tail of moderately-hot keys; out-of-band scheduler for the top 100 hottest.

### Mandatory components
- **Single-flight** — only one refresh task per key at a time.
- **Backoff on refresh failure** — don't hammer DB if refresh fails repeatedly.
- **Refresh queue bound** — limit concurrent refresh tasks.
- **Observability** — track refresh success rate, refresh latency, hit rate at expiry boundary.

## Solution

### Refresh-ahead with single-flight (Node.js + ioredis)

```javascript
const Redis = require('ioredis');
const redis = new Redis();

const TTL = 300;              // seconds
const REFRESH_WINDOW = 60;    // refresh starts when age > 240s

const inflight = new Map();   // key → Promise

async function get(key, loader) {
  const raw = await redis.get(key);
  if (raw === null) {
    // cold miss — synchronous load
    return loadAndStore(key, loader);
  }
  const entry = JSON.parse(raw);
  const ageSec = (Date.now() - entry.writtenAt) / 1000;

  if (ageSec > TTL - REFRESH_WINDOW && ageSec <= TTL) {
    // refresh window — return current value, kick off async refresh
    if (!inflight.has(key)) {
      inflight.set(key, refreshInBackground(key, loader));
    }
  }
  return entry.value;
}

async function loadAndStore(key, loader) {
  if (inflight.has(key)) return inflight.get(key).then(() => get(key, loader));
  const promise = (async () => {
    const value = await loader(key);
    const entry = { value, writtenAt: Date.now() };
    await redis.set(key, JSON.stringify(entry), 'EX', TTL);
    return value;
  })();
  inflight.set(key, promise);
  try {
    return await promise;
  } finally {
    inflight.delete(key);
  }
}

async function refreshInBackground(key, loader) {
  try {
    const value = await loader(key);
    const entry = { value, writtenAt: Date.now() };
    await redis.set(key, JSON.stringify(entry), 'EX', TTL);
  } catch (err) {
    console.error('refresh failed for', key, err);
    // don't expire the entry — let it ride until full TTL
  } finally {
    inflight.delete(key);
  }
}
```

### Probabilistic early expiration (Vasiliev/Vattani algorithm)

A clever alternative — instead of a fixed refresh window, *probabilistically* decide on each read whether to refresh:

```javascript
function shouldEarlyRefresh(ageSec, ttlSec, beta = 1.0) {
  // XFetch algorithm — refresh probability rises as age approaches TTL
  const delta = 0.1;   // expected recompute cost in same time units
  const randomFactor = -Math.log(Math.random());
  return ageSec - delta * beta * randomFactor >= ttlSec;
}
```

This avoids the "all-readers-refresh-in-window" stampede *without* requiring single-flight, by spreading refresh decisions stochastically across readers.

## Step-by-step dry run

Scenario: TTL=300, refresh_window=60, hot key getting one request every 5 seconds.

| T (sec) | Read | Cache age | Action | Notes |
|---------|------|-----------|--------|-------|
| 0  | R1 | — | cold load (50ms) | written_at=0, value=V1 |
| 5  | R2 | 5s | hit, return V1 | within safe zone |
| 60 | R12 | 60s | hit, return V1 | still safe |
| 240 | R48 | 240s | hit, return V1, **spawn refresh** | refresh window entered |
| 240.05 | refresh task | — | loader returns V2, written_at=240 | cache now {value:V2, written_at:240} |
| 245 | R49 | 5s (from 240) | hit, return V2 | reset by refresh |
| 480 | R96 | 240s (from 240) | hit, return V2, **spawn refresh** | window again |
| 480.05 | refresh task | — | loader returns V3 | cache rotated forward |

Net: zero readers ever paid the miss latency after the cold start. The DB sees one refresh every ~240s instead of one miss every 300s on every reader.

If R48 and R49 both fire at T=240 (concurrent), single-flight ensures only one refresh task is started.

## How to think aloud in the interview

"So the problem with vanilla cache-aside is that at TTL expiry, the next reader pays the full miss latency — for a hot key that's potentially N concurrent readers all paying it, plus the DB stampede. Refresh-ahead flips this around: I track when each entry was written, and once it's close to expiry — say in the last 20% of its TTL — any read still returns the cached value immediately, but kicks off a background refresh task. By the time TTL would have expired, the entry has been transparently rotated to a fresh value. No reader ever sees a miss.

Critical detail: I need single-flight on the refresh path. Without it, every read in the refresh window spawns its own refresh task, and I'm worse off than vanilla cache-aside — I'm hammering the DB even more, just preemptively. An in-memory `inflight` map keyed on the cache key, or a Redis lock with a short TTL, is enough.

Trade-offs to flag: refresh-ahead doesn't help with cold start — the first reader still pays the miss. Combine with cache warm-up if cold starts matter. And it can be expensive if you apply it to millions of keys, so I'd scope it to the top 1% hot keys, identified via key-access counters in Redis or sampled in the application layer.

If the interviewer pushes me on freshness: refresh-ahead is a *latency* optimization, not a freshness one. The data can still be `TTL` stale. If they need read-your-writes, refresh-ahead doesn't help — they want explicit invalidation or versioned keys."

## Important takeaways

- **Goal:** zero readers pay miss latency at TTL expiry.
- **Mechanism:** during the refresh window inside the TTL, every read triggers an async refresh + returns the cached value.
- **Single-flight is mandatory** on the refresh path or it becomes a self-inflicted DDoS.
- **Trade-off:** does not improve freshness; only flattens latency.
- **Cold start unsolved** — combine with warm-up.
- **Cost-bounded:** apply only to the top N% hot keys; don't refresh-ahead the long tail.
- **Probabilistic XFetch** is a cute alternative that avoids single-flight via randomization.

## Variants

1. **Stale-while-revalidate (SWR)** — same idea but triggers *after* expiry within a grace window. RFC 5861, used by HTTP caches and `swr` React hook.
2. **Probabilistic early refresh (XFetch)** — refresh probability rises as age approaches TTL; spreads refreshes stochastically.
3. **Scheduled refresh** — out-of-band cron refreshes hot keys regardless of traffic. Useful for low-traffic-but-must-be-fresh-on-arrival pages.
4. **Refresh-ahead with hot-key detection** — adaptive: keys exceeding access-rate threshold get refresh-ahead behavior; cold keys revert to plain TTL.
5. **Tiered refresh-ahead** — refresh L1 from L2 on schedule; refresh L2 from DB on schedule. Decouples user-facing latency from DB load entirely.

## Revision notes

> **refresh-ahead — 60 second recap**
> - **Refresh in background before TTL expires; serve cached value to readers.**
> - **No reader pays miss latency** at expiry (assuming traffic continues).
> - Need `written_at` per entry; refresh when `age > TTL - refresh_window`.
> - **Single-flight on the refresh path is mandatory.**
> - On refresh failure: serve stale, alert, retry. Don't expire.
> - Apply only to **top N% hot keys**; cost-bounded.
> - Cold start still hurts — combine with warm-up.
> - **Trap:** thinking it improves freshness (it doesn't); forgetting single-flight (turns it into a stampede generator).
