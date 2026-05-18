# Cache Stampede — Single-Flight (Promise Coalescing)

## Source / Origin
- Russ Cox / Brad Fitzpatrick (memcache thundering herd, 2007); Go's `singleflight` package; Caffeine's loading cache.
- Asked at: Stripe, Pinterest, Cloudflare, Razorpay, Atlassian.
- Concept reference: `backend-data-prep/questions/caching/cache-stampede-single-flight.md` (server-side variant); this file is the *in-process* JS pattern.

## Why this question matters in interviews
Cache miss + concurrent requests = N goroutines/threads recomputing the same expensive thing. If the recompute takes 500ms and you get 100 hits during that window, you've done 100 redundant database queries. The single-flight pattern collapses those 100 misses into one in-flight compute; the other 99 share the result. Senior bar: you reach for this without prompting on the "cache + concurrent reads" question.

## Concepts involved

### Syntax to lock in
```js
class SingleFlight {
  constructor() { this.inflight = new Map(); }     // key → promise

  async do(key, fn) {
    const existing = this.inflight.get(key);
    if (existing) return existing;                  // share the in-flight
    const p = (async () => {
      try { return await fn(); }
      finally { this.inflight.delete(key); }        // clean up either way
    })();
    this.inflight.set(key, p);
    return p;
  }
}
```

### Edge cases / interview traps
1. **Forgetting `finally` to delete the key.** Future misses on the same key are forever served the *first* result (or stuck on a rejected promise). Always remove on both resolve and reject.
2. **Sharing the rejection.** Subscribers to an in-flight call get the same error. That's *fine* — they would have failed anyway. Don't try to "retry per-subscriber"; that defeats the coalescing.
3. **Awaiting the wrong thing.** Naive `.then(fn).catch(_ => map.delete(key))` swallows the error from later callers. Use an IIFE with `try/finally`.
4. **TTL / negative caching.** Single-flight collapses *in-flight* duplicates but doesn't cache after completion. Pair with an actual cache for repeat hits after.
5. **Per-key vs per-process scope.** `SingleFlight` is process-local. For multi-instance, you need distributed coordination (Redis SETNX + poll). Confess the limit explicitly.
6. **Long-tail starvation.** If `fn()` is slow, every late-arriving caller waits the same long time. Add a `maxWaitMs` and fall through to direct fetch if exceeded.
7. **Abort propagation.** If one caller cancels, should the in-flight `fn()` cancel? Default no — others are still waiting. Reject *this caller's* promise but let work continue. Senior follow-up.

## Mental Model

A box-office ticket window with a **"Now serving" sign**:

```
   First customer walks up, asks for "Latest from DB"
        → window posts "Now serving: Latest from DB"
        → fetches from DB

   Customer 2 walks up, asks for "Latest from DB"
        → sees the sign, queues silently behind the first
   Customer 3 walks up, asks for "Latest from DB"
        → also queues

   DB returns → window hands out copies to all queued customers, removes sign
```

The "sign" is the entry in `inflight: Map<key, Promise>`. Promise itself is the carbon-copy mechanism — every subscriber to the same promise receives the same resolution.

## Why interviewers care

- **Concurrency-under-cache reasoning.** Knowing the read path under contention.
- **Operational instinct.** Stampedes are real outages — every senior has lived one.
- **Promise sharing.** You demonstrate you know promises don't re-execute when subscribed multiple times.

## Common beginner confusion

- **"Just check the cache, then fetch if miss."** Race: two reads both see miss, both fetch. Stampede.
- **"Lock and wait."** A mutex in async JS just serializes; you want *coalescing* (share the result), not serial execution.
- **"What about the result?"** Single-flight isn't a cache — it's a deduper of in-flight work. Wrap a real cache around it.
- **"Errors should be retried per-caller."** No — sharing the error is the contract. Late callers can retry on their own time.

## Brute force approach

```js
// stampedes under concurrent miss
async function get(key) {
  const cached = cache.get(key);
  if (cached) return cached;
  const fresh = await db.fetch(key);   // 100 callers → 100 DB hits
  cache.set(key, fresh, TTL);
  return fresh;
}
```

## Optimal approach

Wrap the fetch in `singleFlight.do(key, () => db.fetch(key))`. Concurrent misses share one in-flight promise. Then store in the real cache.

## Solution (JavaScript)

```js
class SingleFlight {
  constructor() { this.inflight = new Map(); }
  do(key, fn) {
    const existing = this.inflight.get(key);
    if (existing) return existing;
    const p = (async () => {
      try { return await fn(); }
      finally { this.inflight.delete(key); }
    })();
    this.inflight.set(key, p);
    return p;
  }
}

const sf = new SingleFlight();
const cache = new Map();

async function get(key) {
  const cached = cache.get(key);
  if (cached) return cached;
  return sf.do(key, async () => {
    const fresh = await db.fetch(key);     // only ONE DB call even under 100 concurrent get(key)
    cache.set(key, fresh);
    return fresh;
  });
}
```

## Step-by-step dry run

100 concurrent `get('user:42')` calls; cache miss; DB fetch takes 500ms.

```
t=0   c1 → cache miss → sf.do('user:42', fn)
            inflight.get('user:42') = undefined
            create p1 (start fn)
            inflight.set('user:42', p1)
            return p1
t=1   c2 → cache miss → sf.do(...)
            inflight.get('user:42') = p1
            return p1                       (shares!)
t=1..  c3..c100 → all return p1
t=500 fn() resolves with userObj → p1 resolves
            finally: inflight.delete('user:42')
            cache.set('user:42', userObj)
            all 100 callers receive userObj
```

One DB query, 100 satisfied callers.

If `fn()` rejects → `p1` rejects → all 100 callers see the same error. Late callers (t=600) miss the cache, try again — that's correct: a new in-flight is created.

## How to think aloud in the interview

> "I'd add a single-flight layer in front of the cache fetch. `inflight: Map<key, Promise>`. Each `get(key)` first checks the cache; on miss, it calls `sf.do(key, fetchFn)` which either returns the existing in-flight promise or creates a new one. `finally` deletes the entry so the next miss creates a fresh in-flight. This collapses N concurrent misses into one DB call. It's *not* a cache — pair it with one. Process-local only — for multi-instance dedup I'd need Redis."

## Important takeaways

- **Coalesce, don't serialize.** Mutex turns N parallel into N serial; single-flight turns N into 1.
- **`finally` to delete** the inflight entry. Both on success and failure.
- **Share rejections.** Don't try to retry per-caller.
- **Pair with a cache** for repeat hits after completion.
- **Process-local.** Multi-instance dedup needs distributed coordination.
- **Pair with circuit breaker** for downstream failure protection.

## Variants

- **Per-key timeout** — `do(key, fn, { maxMs })` rejects the *caller* if it has waited too long; in-flight continues for others.
- **Negative caching** — store rejections briefly (5s) to avoid re-attempting a known-failing key.
- **Bounded inflight map** — LRU eviction in case of huge keyspace; otherwise memory grows during outage.
- **Distributed single-flight** — Redis `SETNX key 'pending' EX 5` to claim the work; others poll until the key holds the result; carefully time-bound.
- **`Forget(key)`** — explicitly invalidate; subsequent calls re-fetch.

## Revision notes

```
SingleFlight:
  do(key, fn):
    if inflight has key: return inflight.get(key)
    p = (async () => { try return await fn() finally delete inflight.key })()
    inflight.set(key, p)
    return p
  
  coalesces concurrent in-flight duplicates
  NOT a cache (no after-resolution storage)
  share rejection (do not retry per-caller)
  finally delete (both paths)
  pair with cache + circuit-breaker
  process-local only; distributed needs Redis
```
