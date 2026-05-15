# TTL Map with auto-eviction (setTimeout vs lazy)

## Source
- Real backend pattern: every session store, in-memory cache, rate limiter, and idempotency-key tracker uses some form of TTL Map.
- Inspired by Redis `EXPIRE`, `node-cache`, `lru-cache` (with `maxAge`), and Cloudflare Workers' KV TTL semantics.

## Why this question matters in interviews
TTL Map sits at the intersection of three senior-level concerns: **timer management** (when do you set / clear / fire?), **memory pressure** (active timers vs lazy expiry), and **API design** (`get` returns `undefined` when expired vs throws vs returns the stale value with a flag). Interviewers love it because there's no single right answer — they want to hear you **compare two implementations** and articulate when each wins. For backend roles it's directly applicable: session stores, JWT blacklists, rate limiters, dedup windows, idempotency keys, OTP caches. If you've ever built a "delete after N seconds" feature, you've built a TTL Map (or you should have).

## Concepts involved

### Syntax to lock in
```js
// Lazy expiry — check timestamp on read.
class LazyTTLMap {
  #store = new Map();                          // key -> { value, expiresAt }
  constructor(defaultTtl = 60_000) { this.defaultTtl = defaultTtl; }

  set(key, value, ttl = this.defaultTtl) {
    this.#store.set(key, { value, expiresAt: Date.now() + ttl });
  }
  get(key) {
    const entry = this.#store.get(key);
    if (!entry) return undefined;
    if (Date.now() >= entry.expiresAt) {
      this.#store.delete(key);                 // opportunistic cleanup
      return undefined;
    }
    return entry.value;
  }
}
```

### Runtime / engine behavior
- **Active eviction (per-entry setTimeout):** every `set()` schedules a timer; expiry happens automatically. The timer holds a reference to the Map and the key — the Node event loop keeps the process alive unless `timer.unref()` is called.
- **Lazy eviction (check on read):** no timers; entries linger until accessed. Memory can grow unbounded if entries are written and never read. Best paired with a periodic sweep or a max-size cap.
- `Date.now()` returns ms since epoch. Don't use `performance.now()` for TTLs — it's high-resolution monotonic but **relative**, and resets between processes / windows.
- `setTimeout` in Node returns a Timeout object; in browsers it's a number. Both go to `clearTimeout`. Active eviction must `clearTimeout` the previous timer on overwrite, or you'll get phantom deletions.
- Hidden cost: **timer churn**. If a key is overwritten 1000 times per second, naive active eviction creates and clears 1000 timers/sec. V8's timer code is fast but not free; lazy eviction has zero such cost.

### Edge cases (these are the interview traps)
1. **Overwriting an existing key** — active eviction MUST clear the prior `setTimeout` before scheduling a new one. Otherwise the old timer fires and deletes the *new* value.
2. **`ttl = 0` or negative** — by spec, an immediately-expired entry. Lazy: returns `undefined` on first read. Active: `setTimeout(fn, 0)` defers to next tick — actually wrong, you'd want to delete synchronously. Decide and document.
3. **Process keep-alive** — long-lived active timers keep Node from exiting. Use `timer.unref()` if appropriate.
4. **Clock drift / system time changes** — `Date.now()` jumps if the user changes their clock. For TTLs short enough not to care, ignore. For long TTLs (hours+), consider monotonic time + offset.
5. **Memory bound** — lazy eviction without a periodic sweep can leak memory. Pair it with a max-size LRU bound or a background sweep timer.
6. **Read-on-expiry timing** — `Date.now() >= entry.expiresAt` (inclusive) is the safe comparison. Strict `>` lets the boundary millisecond return a stale value.
7. **Mass eviction on shutdown** — active eviction leaves timers in flight; `clear()` must walk and `clearTimeout` each one.
8. **Iteration during expiry** — `for...of map.entries()` during a sweep that mutates the map: in V8, deleting current key is safe; deleting future keys mid-iteration may skip them. Use `Array.from(map.keys())` to snapshot first.
9. **`has(key)` semantics** — should `has()` honor TTL? Yes, but it requires the same expiry check as `get()`. Otherwise `has(k) === true && get(k) === undefined` is observable, which is confusing.

## Brute force approach
Plain `Map` + a single global `setInterval` that walks every entry and deletes expired ones. **Works** but O(n) per sweep regardless of how many entries are actually expired. Fine for small n; wasteful otherwise. Use it as a baseline you'd refine. (It's actually a viable production pattern with `setInterval(sweep, 1000)` for low-throughput caches.)

## Optimal approach
There are **two production-grade approaches** and the interviewer wants to hear both, plus when to pick which.

**A. Active eviction (per-entry `setTimeout`)** — eager. Each `set()` schedules a timer that deletes the key when TTL elapses. Memory is tight (no expired entries linger). Cost: one timer per entry, plus timer churn on overwrites. Good for low-write-rate caches with many reads — session stores, OTPs.

**B. Lazy eviction (check timestamp on read)** — `get()` checks `Date.now() >= expiresAt` and returns `undefined` for expired entries. Zero timers. Memory may grow if entries are never read. Good for high-write-rate caches where most entries naturally get overwritten — rate limiters, dedup windows.

**Hybrid:** lazy expiry on read + periodic background sweep (e.g. every 60s, walk the Map and delete expired). Best general-purpose answer.

## Solution (JavaScript)

```js
/**
 * (A) Active eviction — per-entry setTimeout.
 * Pros: tight memory; auto-clean.
 * Cons: timer per entry; churn on overwrites.
 */
class ActiveTTLMap {
  #store = new Map();                          // key -> value
  #timers = new Map();                         // key -> timeout handle

  constructor(defaultTtl = 60_000) { this.defaultTtl = defaultTtl; }

  set(key, value, ttl = this.defaultTtl) {
    // Critical: clear any prior timer for this key.
    if (this.#timers.has(key)) clearTimeout(this.#timers.get(key));

    this.#store.set(key, value);
    const timer = setTimeout(() => {
      this.#store.delete(key);
      this.#timers.delete(key);
    }, ttl);
    if (typeof timer.unref === 'function') timer.unref();   // don't block process exit
    this.#timers.set(key, timer);
  }

  get(key) { return this.#store.get(key); }
  has(key) { return this.#store.has(key); }

  delete(key) {
    if (this.#timers.has(key)) clearTimeout(this.#timers.get(key));
    this.#timers.delete(key);
    return this.#store.delete(key);
  }

  clear() {
    for (const t of this.#timers.values()) clearTimeout(t);
    this.#timers.clear();
    this.#store.clear();
  }

  get size() { return this.#store.size; }
}

/**
 * (B) Lazy eviction — check on read.
 * Pros: zero timers; cheap writes.
 * Cons: expired entries linger until read or swept.
 */
class LazyTTLMap {
  #store = new Map();                          // key -> { value, expiresAt }

  constructor(defaultTtl = 60_000) { this.defaultTtl = defaultTtl; }

  set(key, value, ttl = this.defaultTtl) {
    this.#store.set(key, { value, expiresAt: Date.now() + ttl });
  }

  get(key) {
    const entry = this.#store.get(key);
    if (!entry) return undefined;
    if (Date.now() >= entry.expiresAt) {
      this.#store.delete(key);                 // opportunistic cleanup
      return undefined;
    }
    return entry.value;
  }

  has(key) { return this.get(key) !== undefined; }

  delete(key) { return this.#store.delete(key); }
  clear() { this.#store.clear(); }

  /** Optional periodic sweep — call from setInterval. */
  sweep() {
    const now = Date.now();
    for (const [k, { expiresAt }] of this.#store) {
      if (now >= expiresAt) this.#store.delete(k);
    }
  }

  get size() { return this.#store.size; }
}
```

## Step-by-step dry run

```js
const ttl = new LazyTTLMap(100);              // default 100ms

ttl.set('a', 1);                              // expiresAt = t=100
ttl.set('b', 2, 500);                         // expiresAt = t=500

// t=50
ttl.get('a');                                 // entry exists, 50 < 100 → returns 1
ttl.get('b');                                 // returns 2

// t=150
ttl.get('a');                                 // 150 >= 100 → delete + return undefined
ttl.get('b');                                 // 150 < 500 → returns 2

// t=600
ttl.get('b');                                 // 600 >= 500 → delete + return undefined
ttl.size;                                     // 0
```

Active version: at `t=100`, the `setTimeout` for `'a'` fires and deletes it from `#store` and `#timers`. No `get` needed. At `t=500`, same for `'b'`.

## Important takeaways

**Syntax to memorize**
- Lazy: store `{ value, expiresAt }`; check `Date.now() >= expiresAt` in `get`.
- Active: pair Map of values with Map of timer handles; **always clear the prior timer on overwrite**.
- `timer.unref()` keeps active eviction from blocking process exit.

**Patterns to reuse**
- **Per-entry timer + handle Map** is the same skeleton used by: idempotency-key TTL, JWT blacklist with auto-cleanup, scheduled-event dispatcher.
- **Timestamp + lazy check** is the skeleton used by: rate limiter (timestamp of last token grant), cache-with-stale-while-revalidate, "show notification for N seconds."
- **Hybrid (lazy + periodic sweep)** is the production-grade default. Used by `node-cache`, Redis (active expiry + sampled lazy expiry), browser caches.

**Common mistakes**
- Forgetting to `clearTimeout` the prior timer on overwrite → ghost deletions.
- Lazy `has()` that doesn't check expiry → `has(k) && get(k) === undefined` paradox.
- Using `>` instead of `>=` in the expiry check → boundary-ms staleness.
- Allowing unbounded lazy growth without a sweep or size cap → memory leak.
- Active eviction with `setTimeout` that captures the whole Map in closure → if you `delete` the cache reference but timers are still pending, the Map stays alive until the last timer fires.
- Using `performance.now()` for TTLs — high-resolution but doesn't survive process restart; use `Date.now()`.

**When to pick which**
| Workload                              | Better choice         | Why                                  |
|---------------------------------------|-----------------------|--------------------------------------|
| Few keys, long TTLs, mostly reads     | Active                | Tight memory; cheap reads            |
| Many writes, frequent overwrites      | Lazy                  | No timer churn                       |
| Very high cardinality + low read rate | Lazy + periodic sweep | Cap memory without timer-per-key     |
| Need exact "fire callback at expiry"  | Active                | Lazy can't notify on expiry          |
| Read-heavy, predictable access        | Lazy                  | Reads do the work that gets used     |

State the tradeoff. Interviewers love hearing "it depends, and here's the rubric."

**Related questions**
- LRU Cache (LeetCode #146) — combine with TTL for full-fledged cache
- Rate limiter (sliding window, token bucket)
- Idempotency key store
- Stale-while-revalidate cache

## Variants

1. **TTL + LRU combo** — bound both memory and freshness. On `set`, if size > max, evict the LRU. On `get`, check TTL then bump recency.

2. **Refresh-on-access** — every `get` resets the TTL (sliding expiry, like a session). Trivial change in lazy: `entry.expiresAt = Date.now() + ttl` in `get`. In active: clear timer and re-set.

3. **Expiry callback** — `new TTLMap({ onExpire: (k, v) => ... })`. Active version invokes it in the timer callback; lazy invokes it in `get` when it discovers an expired entry.

4. **Per-key custom TTL** — already supported above (`set(k, v, ttl)`).

5. **Background sweep variant** — `LazyTTLMap` + `setInterval(() => map.sweep(), 60_000)`. Best general-purpose answer.

6. **Async TTL Map for distributed caches** — wraps Redis `SET key value EX ttl`. Same API, different backend. Mention if asked about scale.

## Revision notes

> **ttl-map — 60 second recap**
> - **Two implementations**, pick based on workload:
>   - **Active** — per-entry `setTimeout`; tight memory; timer churn on overwrites. **Must clearTimeout on overwrite.**
>   - **Lazy** — store `{value, expiresAt}`; check `Date.now() >= expiresAt` on read. Zero timers; expired entries linger until accessed.
> - **Hybrid** — lazy + periodic `setInterval(sweep)` — production-grade default.
> - Lazy `has()` must run the same expiry check as `get()`.
> - Active: `timer.unref()` so the process can exit.
> - Use `Date.now()`, not `performance.now()`.
> - Family: LRU+TTL combo cache, idempotency key store, rate limiter.
