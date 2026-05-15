# Implement `TimeLimitedCache` (TTL Cache)

## Source
- LeetCode #2622 "Cache With Time Limit": https://leetcode.com/problems/cache-with-time-limit/
- Canonical: every Redis/memcached client, every server-side memo layer.

## Why this question matters in interviews
TTL caches are the single most common backend caching primitive — Redis SETEX, memcached, Node's `lru-cache`. The interview probes two skills: (1) **expiry strategy** — active (`setTimeout` evicts on schedule) vs lazy (check `expiresAt` on read), and the tradeoffs; (2) **state hygiene** — using `Map` (not plain object) for O(1) ops + correct iteration semantics, and remembering to `clearTimeout` when you overwrite a key. Senior candidates are expected to bring up both strategies, pick one, and justify it. Show you've thought about memory pressure, timer storms, and what happens at `count()` time across the expiry boundary — these are real production concerns.

## Concepts involved

### Syntax to lock in
```js
class TimeLimitedCache {
  constructor() { this.store = new Map(); }
  set(key, value, duration) {
    const existed = this.store.has(key) && this.store.get(key).expiresAt > Date.now();
    if (this.store.has(key)) clearTimeout(this.store.get(key).timerId);
    const timerId = setTimeout(() => this.store.delete(key), duration);
    this.store.set(key, { value, expiresAt: Date.now() + duration, timerId });
    return existed;
  }
  get(key) {
    const e = this.store.get(key);
    if (!e || e.expiresAt <= Date.now()) return -1;
    return e.value;
  }
  count() {
    const now = Date.now();
    let n = 0;
    for (const e of this.store.values()) if (e.expiresAt > now) n++;
    return n;
  }
}
```

### Runtime / engine behavior
- `Map` gives O(1) `get`/`set`/`delete` and preserves insertion order (useful for LRU variants).
- `setTimeout` returns a Timeout handle in Node, a number in the browser. `clearTimeout` works on both.
- Each active timer **keeps the event loop alive** in Node. In a long-lived server with 1M cache entries, that's 1M timers. Lazy expiry avoids this.
- `Map.delete` inside a `setTimeout` callback runs in the **timers phase** as a macrotask — by the time it runs, the key may already have been overwritten (the old timer should have been cleared, but defensive code re-checks `expiresAt`).

### Edge cases (interview traps)
1. **Overwrite during active TTL** — must `clearTimeout` the old timer; otherwise the old timer fires at the old expiry and wipes the new value. **The most-failed interview detail.**
2. **`set` returns `true` only if a non-expired entry existed** — the LeetCode contract: `true` if there was a live entry, `false` otherwise. Many candidates return `this.store.has(key)`, which is wrong if the entry expired but the timer hasn't fired yet.
3. **`get` across the boundary** — if you call `get` between expiry and the eviction timer firing, the active-only implementation returns the stale value. Always **double-check `expiresAt` on read** (lazy verify, even with active expiry).
4. **`count` across the boundary** — must iterate and filter by `expiresAt`. Don't just return `this.store.size`.
5. **Timer storm** — adding 100k entries simultaneously schedules 100k timers. Node copes, but it's wasteful. Lazy expiry + periodic GC is the prod pattern.
6. **Negative or zero `duration`** — set + immediate expire. `setTimeout(..., 0)` defers eviction to the next macrotask; `get` called synchronously after `set(k, v, 0)` still returns `v` until the macrotask runs. **Lazy check on read fixes this.**
7. **`unref()` for Node** — if these timers shouldn't block process exit, call `.unref()` on each. Browser timers don't have this.
8. **`structuredClone` / referential leaks** — cache stores references, not copies. Mutating a cached object mutates the cache. Worth mentioning.

## Brute force approach
**Plain object + no expiry timer**, check `Date.now()` on every read (lazy-only). Simple, no timer overhead, but `count()` is O(n) (you have to filter expired entries). For LeetCode this is fine and arguably the best answer for production memory. Mention this first, then implement the active variant.

## Optimal approach
**`Map` + active expiry via `setTimeout` + lazy verification on read.** Active eviction keeps `count()` cheap (mostly) and memory bounded; lazy verification handles the small window between expiry and timer firing. Always `clearTimeout` on overwrite/delete.

## Solution (JavaScript)

```js
/**
 * Time-limited cache. Keys auto-expire after their per-key `duration` ms.
 * - `set(k, v, ms)` returns true iff a non-expired entry existed.
 * - `get(k)` returns the value or -1 if missing/expired.
 * - `count()` returns the number of non-expired entries.
 */
class TimeLimitedCache {
  constructor() {
    /** @type {Map<any, { value: any, expiresAt: number, timerId: any }>} */
    this.store = new Map();
  }

  set(key, value, duration) {
    const now = Date.now();
    const prev = this.store.get(key);
    const existed = !!prev && prev.expiresAt > now;

    // Always clear an existing timer — even if expired but not yet evicted.
    if (prev) clearTimeout(prev.timerId);

    const timerId = setTimeout(() => {
      this.store.delete(key);
    }, duration);
    // Optional for Node servers — let the process exit even with pending timers:
    // timerId.unref?.();

    this.store.set(key, { value, expiresAt: now + duration, timerId });
    return existed;
  }

  get(key) {
    const entry = this.store.get(key);
    if (!entry) return -1;
    // Lazy verification: covers the window between expiresAt and the eviction timer firing.
    if (entry.expiresAt <= Date.now()) {
      clearTimeout(entry.timerId);
      this.store.delete(key);
      return -1;
    }
    return entry.value;
  }

  count() {
    const now = Date.now();
    let n = 0;
    for (const e of this.store.values()) if (e.expiresAt > now) n++;
    return n;
  }
}
```

### Lazy-only variant (preferred for memory)

```js
class LazyTTLCache {
  constructor() { this.store = new Map(); }
  set(k, v, ms) {
    const now = Date.now();
    const prev = this.store.get(k);
    const existed = !!prev && prev.expiresAt > now;
    this.store.set(k, { value: v, expiresAt: now + ms });
    return existed;
  }
  get(k) {
    const e = this.store.get(k);
    if (!e) return -1;
    if (e.expiresAt <= Date.now()) { this.store.delete(k); return -1; }
    return e.value;
  }
  count() {
    const now = Date.now();
    let n = 0;
    for (const [k, e] of this.store) {
      if (e.expiresAt <= now) this.store.delete(k); // opportunistic GC
      else n++;
    }
    return n;
  }
}
```

## Step-by-step dry run

Input:
```js
const c = new TimeLimitedCache();
c.set('a', 1, 100);          // t=0  → false (no prior)
setTimeout(() => c.set('a', 2, 50), 60);   // t=60 → true (prior 'a' still alive until t=100)
setTimeout(() => c.get('a'), 80);          // t=80 → 2
setTimeout(() => c.get('a'), 120);         // t=120 → -1 (expired at t=60+50=110)
setTimeout(() => c.count(), 130);          // t=130 → 0
```

Trace:
- `t=0`: `set('a', 1, 100)`. `prev` undefined → `existed = false`. Schedule eviction-timer T1 for `t=100`. Store: `{a: {value:1, expiresAt:100, timerId:T1}}`. Return `false`.
- `t=60`: `set('a', 2, 50)`. `prev` exists, `expiresAt=100 > 60` → `existed = true`. `clearTimeout(T1)`. Schedule T2 for `t=110`. Store: `{a: {value:2, expiresAt:110, timerId:T2}}`. Return `true`.
- `t=80`: `get('a')`. `expiresAt=110 > 80` → return `2`.
- `t=110`: T2 fires → `store.delete('a')`.
- `t=120`: `get('a')`. Not in store → return `-1`.
- `t=130`: `count()`. Iterate empty map → return `0`.

Key thing to call out: if at `t=60` we'd **forgotten** `clearTimeout(T1)`, T1 would still fire at `t=100` and wipe the *new* value, breaking the cache.

## Important takeaways

**Syntax to memorize**
- `Map` over `{}` — O(1) ops, non-string keys, no prototype-pollution risk.
- `clearTimeout(prev.timerId)` **before** scheduling a new one on overwrite.
- Lazy verification on `get` even if you have active expiry.

**Patterns to reuse**
- This is the same skeleton as: rate limiters (token-bucket refill timer), session caches, idempotency-key stores, debounce-with-cache.
- For LRU + TTL, layer this on top of an `LRUMap` (insertion order = recency).

**Common mistakes**
- Forgetting `clearTimeout` on overwrite → old timer wipes new value.
- Plain object instead of `Map` → key collisions with `__proto__`, slower hashing, no insertion order.
- Returning `this.store.has(key)` for `set`'s return value → wrong if the entry expired-but-not-evicted.
- Trusting active expiry alone → race window between `expiresAt` and the timer firing.
- Not `.unref()`-ing timers in long-running Node services where you want clean shutdown.

**Related questions**
- LRU cache (different eviction policy).
- Memoize with TTL (decorator pattern over this cache).
- Distributed cache (Redis SETEX) — same contract, different backing store.

## Variants

1. **Per-key max + TTL (LRU+TTL)** — layer a `Map` keyed by access-recency. Evict by recency once size exceeds `max`, by `expiresAt` lazily on read.

2. **Async load-through cache** — `get(key, loader)` calls `loader()` on miss, caches its promise (single-flight de-dupe), evicts after TTL. Very common in production.

3. **Sliding TTL** — every `get` extends `expiresAt` by `duration`. Tweak `get` to `clearTimeout` and reschedule.

4. **`getRemainingTime(key)`** — returns `expiresAt - Date.now()` clamped to 0. Useful for HTTP `Cache-Control: max-age` responses.

## Revision notes

> **TimeLimitedCache — 60 second recap**
> - `Map<key, { value, expiresAt, timerId }>`.
> - `set` → clear prior timer, store new entry with `expiresAt = now + ms`, schedule eviction timer. Return `true` iff prior entry was non-expired.
> - `get` → lazy-verify `expiresAt > now`, else evict and return `-1`.
> - `count` → iterate values, count where `expiresAt > now`.
> - **Active** expiry = `setTimeout` evicts; **Lazy** = check on read. Production: combine — active for memory, lazy for correctness.
> - `clearTimeout(prev.timerId)` on overwrite — top failure mode.
> - For 100k+ entries, prefer **lazy only** + opportunistic GC; 100k timers waste resources.
> - Use `Map` not `{}` (perf, non-string keys, no prototype pollution).
> - Family: rate limiters, session stores, idempotency keys — same skeleton.
