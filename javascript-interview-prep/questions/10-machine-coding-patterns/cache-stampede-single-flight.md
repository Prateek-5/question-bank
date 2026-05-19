# Single-Flight — coalesce concurrent cache misses

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [memoize.md](./memoize.md), [`04-promises/async-memoize.md`](../04-promises/async-memoize.md)
>
> **Source:** Russ Cox / Brad Fitzpatrick "memcache thundering herd" (2007); Go's `singleflight`; Caffeine's loading cache. Stripe, Pinterest, Cloudflare, Razorpay.

---

## 1. Problem statement

**Signature**
```ts
class SingleFlight {
  do<T>(key: string, fn: () => Promise<T>): Promise<T>;
}
```

**Input / Output examples**

| Setup                                              | Behaviour                                              |
|----------------------------------------------------|---------------------------------------------------------|
| 100 concurrent `sf.do('user:42', fetchUser)` calls | one fetch, 100 satisfied callers                       |
| `fn` rejects                                       | all 100 callers receive same error                     |
| Late caller (after first resolved + cleared)       | new fetch — no stale cache from single-flight         |
| Same key called sequentially (after settling)      | each call runs fresh `fn`                              |

**Constraints**
- `inflight: Map<key, Promise>` — share in-flight work.
- `finally` deletes entry on both resolve and reject.
- Process-local; distributed dedup needs Redis.
- NOT a cache — coalesces in-flight only; pair with a real cache for after-resolution.

---

## 2. Plain-English restatement

When 100 concurrent requests miss the cache, instead of running the fetch 100 times, run it once and **share the in-flight promise** with all 100 callers. After the promise settles, drop the entry so the next miss runs fresh. Single-flight doesn't cache; it just dedupes concurrent in-flight work.

---

## 3. Why this matters in interviews

Cache miss + concurrent traffic = N redundant computes. Single-flight collapses N misses into one. Senior bar: reach for this without prompting on the "cache + concurrent reads" question.

---

## 4. Mental model

```
   Box-office ticket window with a "Now serving" sign:

   t=0  customer A: "Latest from DB"
                    → window posts "Now serving: Latest from DB"
                    → starts DB fetch
   t=1  customer B: "Latest from DB"
                    → sees sign, queues silently
   t=2  customer C-Z: same
   t=500 DB returns → window hands SAME response to all queued customers
                      → removes sign

   inflight: Map<key, Promise>
     - sign present  → return existing promise (shared)
     - sign absent   → start fn, store promise, return it
     - finally       → delete sign (success OR failure)
```

**Different from cache:** no after-resolution storage. The next concurrent miss after settle creates a new in-flight.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If `fn` rejects, what do the other 99 callers see?
> 2. Why use `finally` (not just `.then`) to delete the inflight entry?
> 3. Is single-flight a cache?

---

## 6. Brute force — walked through

### Wrong attempt 1: check cache then fetch
```js
const cached = cache.get(k); if (cached) return cached;
const fresh = await db.fetch(k);   // 100 callers → 100 DB hits
cache.set(k, fresh);
```
Stampede.

### Wrong attempt 2: mutex
Serializes — N callers wait one-by-one. Single-flight COALESCES — all share one fetch.

### Wrong attempt 3: forget `finally`
```js
const p = fn().then((v) => { map.delete(k); return v; });
```
On rejection, `.then` doesn't fire; entry stays forever. Use `finally`.

---

## 7. The unlocking insight

> **`inflight: Map<key, Promise>`. `do(key, fn)`: if entry exists, return it. Else start `fn`, store promise, return. Use `try/finally` inside IIFE so deletion fires on both resolve AND reject.**

Three properties:

1. **Coalesce (not serialize)** — all callers `await` the SAME promise.
2. **`finally` cleanup** — entry removed on success or failure.
3. **Process-local** — distributed dedup needs different machinery.

---

## 8. Solution (annotated)

```js
class SingleFlight {
  constructor() {
    this.inflight = new Map();                                       // step 1: in-flight map
  }

  do(key, fn) {
    const existing = this.inflight.get(key);
    if (existing) return existing;                                    // step 2: share

    const p = (async () => {                                          // step 3: IIFE for try/finally
      try {
        return await fn();
      } finally {
        this.inflight.delete(key);                                    // step 4: clean up either way
      }
    })();

    this.inflight.set(key, p);
    return p;
  }
}

// Combined with a real cache:
const sf = new SingleFlight();
const cache = new Map();

async function get(key) {
  const cached = cache.get(key);
  if (cached) return cached;
  return sf.do(key, async () => {
    const fresh = await db.fetch(key);                                // ONE DB call
    cache.set(key, fresh);
    return fresh;
  });
}
```

**Try it yourself**

```js
const sf = new SingleFlight();

// Simulate 100 concurrent callers
const promises = Array.from({ length: 100 }, () =>
  sf.do('user:42', async () => {
    console.log('FETCHING');                                          // logs ONCE
    await new Promise((r) => setTimeout(r, 500));
    return { id: 42, name: 'Prateek' };
  })
);
const results = await Promise.all(promises);
// All 100 get the same { id: 42, name: 'Prateek' }. Only ONE 'FETCHING' log.
```

---

## 9. Step-by-step dry run

```
100 concurrent get('user:42'); cache miss; fetch takes 500ms.

t=0    c1 → cache miss → sf.do:
              inflight.get(42) = undefined
              p1 = (async () => { try { return await fetch() } finally { inflight.delete(42) } })()
              inflight.set(42, p1)
              return p1
t=1    c2-c100 → cache miss → sf.do:
              inflight.get(42) = p1
              return p1 (SHARED!)

t=500  fetch resolves with userObj → p1 fulfills.
       finally: inflight.delete(42).
       cache.set(42, userObj) (in the wrapper).
       All 100 callers receive userObj.

If fetch had rejected:
  p1 rejects with err.
  finally: inflight.delete(42).
  All 100 callers see same err.

Late caller at t=600:
  cache.get(42) → userObj (cache hit). Single-flight not consulted.

Later cache invalidation at t=10s, then concurrent miss at t=10001ms:
  inflight.get(42) undefined → new p2 starts. Same coalescing pattern.
```

---

## 10. Common confusion + traps

1. **Mutex instead of coalescing** — turns N parallel into N serial; defeats purpose.
2. **No `finally`** — rejected entry stays forever.
3. **Treat as a cache** — no after-resolution storage. Pair with real cache.
4. **Retry-per-caller on rejection** — defeats coalescing. Late callers can retry themselves.
5. **Distributed assumption** — process-local only. Multi-instance needs Redis SETNX + poll.
6. **Negative-cache rejection forever** — if `fn` always fails, every concurrent miss creates a new in-flight. Add brief negative cache if needed.
7. **Long-tail starvation** — slow `fn` blocks late callers; add `maxWaitMs` per-caller if needed.

---

## 11. Senior follow-ups & variants

### Variant 1 — Per-caller timeout
`do(key, fn, { maxMs })` rejects the caller's promise after `maxMs`; in-flight continues for others.

### Variant 2 — Negative caching
Cache rejections briefly (5s) so we don't re-attempt known-failing keys.

### Variant 3 — Bounded inflight map
LRU eviction in case of huge keyspace; otherwise memory grows during outage.

### Variant 4 — Distributed single-flight
Redis `SETNX key 'pending' EX 5` to claim work; others poll until key holds result. Time-bound carefully.

### Variant 5 — `forget(key)`
Explicit invalidation; subsequent calls re-fetch.

### Variant 6 — Pair with circuit breaker
On downstream failure, breaker short-circuits; single-flight prevents the few attempted recoveries from amplifying.

---

## 12. How to think aloud

> "Single-flight is a coalesce primitive, not a cache. `inflight: Map<key, Promise>`. `do(key, fn)`: if entry exists, return it (share). Else IIFE that runs `fn` inside `try/finally`, with `finally` deleting the entry on both resolve and reject. Store promise, return. Process-local. For multi-instance dedup I'd need Redis. NOT a cache — pair with one for after-resolution storage. Trap: mutex instead of coalescing (serializes); no `finally` (stuck entry on reject); treat as cache (no storage)."

---

## 13. 60-second revision

> - **`inflight: Map<key, Promise>`** — share in-flight.
> - **Coalesce, don't serialize** (mutex serializes; SF dedupes).
> - **`finally` deletes** entry on success AND failure.
> - **NOT a cache** — no after-resolution storage. Pair with real cache.
> - **Share rejection** — don't retry per-caller (defeats SF).
> - **Process-local;** distributed needs Redis SETNX + poll.
> - **Variants:** per-caller timeout, negative caching, bounded map, distributed.
> - **Trap:** mutex (serialize); no finally (stuck entry); treat as cache.

---

**Related:** [memoize.md](./memoize.md) · [`04-promises/async-memoize.md`](../04-promises/async-memoize.md) · [request-deduplication.md](./request-deduplication.md) · [idempotency-wrapper.md](./idempotency-wrapper.md) · [circuit-breaker.md](./circuit-breaker.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
