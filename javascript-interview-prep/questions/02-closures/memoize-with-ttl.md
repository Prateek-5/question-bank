# Implement `memoize(fn, { ttl })` — cache with expiry

## Source
- Backend interview classic (BFE.dev, lodash `_.memoize` + TTL variants, GreatFrontend).
- Real-world: Redis-style local cache, GraphQL DataLoader patterns, config caches.

## Why this question matters in interviews
Plain `memoize` is a warm-up; `memoize` **with TTL** is the senior-backend extension that probes whether you understand cache lifecycle. It hits four ideas in one problem: closure over a `Map`, time-based eviction (lazy vs active), cache-key strategy, and the eviction–memory trade-off. As a backend engineer you'll build this every other quarter — wrapping a slow upstream call (DB query, third-party API, expensive computation) where stale-by-N-seconds is acceptable. Interviewers grade your answer on **eviction strategy** more than the cache itself.

## Concepts involved

### Syntax to lock in
```js
function memoize(fn, { ttl = Infinity, keyFn = JSON.stringify } = {}) {
  const cache = new Map();          // closed-over state
  return function (...args) {
    const key = keyFn(args);
    const now = Date.now();
    const hit = cache.get(key);
    if (hit && hit.expiresAt > now) return hit.value;
    const value = fn.apply(this, args);
    cache.set(key, { value, expiresAt: now + ttl });
    return value;
  };
}
```

### Runtime / engine behavior
- Closure captures `cache` and `keyFn`. The `Map` lives on the heap as long as the returned wrapper is reachable — this is exactly how you create a memory leak if `ttl = Infinity` and keys keep growing.
- `Date.now()` is sufficient for ms-level TTL; for nanosecond precision use `performance.now()`. Both are monotonic-ish (NTP can pull `Date.now()` backwards — irrelevant for cache TTL but worth knowing).
- `Map` over plain object: preserves insertion order (useful for LRU extensions), allows any key type, has O(1) `get`/`set`/`has`.

### Eviction strategies (the senior discussion)
1. **Lazy (on-read)** — check `expiresAt` only when something tries to read the entry. Simplest, but expired entries linger in memory until accessed.
2. **Active (timer-based)** — `setTimeout(() => cache.delete(key), ttl)` on every set. Frees memory on time, but each entry costs a timer (libuv handle). For 10k entries that's 10k timers — measurable.
3. **Sweep (periodic)** — single `setInterval` that walks the map and deletes expired entries. Best of both, but the sweep itself blocks the event loop briefly.
4. **LRU + TTL** — bound max size (LRU eviction) *and* time. Production-grade. Use a doubly-linked list + Map, or `lru-cache` npm.

### Edge cases (interview traps)
1. **Key collisions** — `JSON.stringify` can't serialize functions, `Map` keys, circular refs, or `BigInt`. Allow `keyFn` override.
2. **`undefined` cached value** — must distinguish "no entry" from "entry with value `undefined`". `Map.has` or storing wrapped `{value, expiresAt}` solves this.
3. **`this` binding** — forward with `fn.apply(this, args)` for method-style use.
4. **Async `fn`** — cache the **Promise**, not the resolved value, so concurrent callers dedupe.
5. **Promise rejection** — should a rejected Promise be cached? Usually no — delete the entry in a `.catch`.
6. **Clock skew / system time changes** — `Date.now()` can jump; use `performance.now()` if you care.
7. **Memory leak** — unbounded Map + Infinity TTL = leak. Always pair with size cap.

## Brute force approach
A plain object as cache + storing `[value, timestamp]` arrays. Works but: prototype-pollution risk on string keys (`__proto__`, `constructor`), no O(1) `size`, no iteration order. `Map` solves all three.

## Optimal approach
Closure over a `Map` of `{ value, expiresAt }` entries. Lazy eviction on read for simplicity. For backend scale, pair with **active sweep** or **LRU cap**. Discuss the trade-off explicitly.

## Solution (JavaScript)

```js
/**
 * Memoize `fn` with a per-entry TTL (ms).
 * Lazy eviction on read; optional active sweep.
 * @param {Function} fn
 * @param {{ ttl?: number, max?: number, keyFn?: (args: any[]) => string }} options
 * @returns {Function & { clear: () => void, delete: (key: string) => boolean }}
 */
function memoize(fn, { ttl = Infinity, max = Infinity, keyFn = (args) => JSON.stringify(args) } = {}) {
  const cache = new Map();           // insertion-ordered for LRU semantics

  function memoized(...args) {
    const key = keyFn(args);
    const now = Date.now();
    const hit = cache.get(key);

    if (hit !== undefined && hit.expiresAt > now) {
      // refresh LRU position
      cache.delete(key);
      cache.set(key, hit);
      return hit.value;
    }

    const value = fn.apply(this, args);
    cache.set(key, { value, expiresAt: now + ttl });

    // Bound size — evict oldest (Map preserves insertion order)
    if (cache.size > max) {
      const oldestKey = cache.keys().next().value;
      cache.delete(oldestKey);
    }
    return value;
  }

  memoized.clear = () => cache.clear();
  memoized.delete = (key) => cache.delete(key);
  return memoized;
}
```

## Step-by-step dry run

Input:
```js
let calls = 0;
const slow = (x) => { calls++; return x * 2; };
const fast = memoize(slow, { ttl: 100 });

fast(5);            // t=0  → calls=1, returns 10
fast(5);            // t=10 → calls=1, returns 10 (cache hit)
fast(6);            // t=20 → calls=2, returns 12
setTimeout(() => fast(5), 150);  // t=150 → calls=3, returns 10 (expired)
```

Trace:
- `t=0` — `fast(5)`: key `'[5]'`. No entry. Call `slow(5)`, `calls=1`. Set `cache['[5]'] = { value: 10, expiresAt: 100 }`. Return 10.
- `t=10` — `fast(5)`: key `'[5]'`. Hit found, `expiresAt(100) > now(10)`. **No call**. Return 10. `calls` stays 1.
- `t=20` — `fast(6)`: key `'[6]'`. Miss. Call `slow(6)`, `calls=2`. Set `cache['[6]'] = { value: 12, expiresAt: 120 }`. Return 12.
- `t=150` — `fast(5)`: key `'[5]'`. Entry exists, but `expiresAt(100) <= now(150)` → treat as miss. Call `slow(5)`, `calls=3`. Overwrite entry with new `expiresAt = 250`. Return 10.

What's on the heap: the `cache` Map holds two entries with `{value, expiresAt}` boxes. `slow` is also captured. None of this is GC'd while `fast` is reachable.

## Important takeaways

**Syntax to memorize**
- `let cache = new Map()` in outer scope, **never** inside the wrapper.
- Store `{value, expiresAt}`, not raw values — separates "no entry" from "entry with value `undefined`".
- `JSON.stringify(args)` is the **default**, not the only option. Always allow a `keyFn` override.

**Patterns to reuse**
- This is the canonical "closure over a Map" pattern. Same skeleton powers: in-flight dedupe, request coalescing, DataLoader, rate-limiter buckets, idempotency-key cache.
- Pair lazy eviction (cheap, simple) with an LRU cap (bounds memory). Or active sweep (`setInterval`) if you care about prompt memory release.

**Common mistakes**
- Putting `new Map()` inside the wrapper — cache resets on every call (memoize becomes a no-op).
- Using `cache[key] === undefined` to detect misses — false negative when value is `undefined`. Use `Map.has` or wrap values.
- `JSON.stringify` on non-serializable args — functions disappear, circular refs throw.
- Forgetting that async results should cache the **Promise** (so concurrent callers dedupe).
- Caching rejected promises — your "transient failure" becomes "sticky failure" for the whole TTL window.

**Related questions**
- `memoize(fn)` (no TTL — same skeleton)
- LRU cache (Map + insertion order)
- DataLoader / request dedupe (closure over `Map<key, Promise>`)
- Cache invalidation by tag (Map<key, val> + Map<tag, Set<key>>)

## Variants

1. **Async `memoize` with in-flight dedupe** — Cache the Promise; on rejection, `cache.delete(key)` so the next call retries. Senior interviewers always follow up with this.

2. **LRU + TTL hybrid** — `max` size cap plus per-entry TTL. Tests doubly-linked-list + Map knowledge or `Map`'s insertion-order trick (delete-then-set refreshes recency).

3. **Per-key TTL** — let the caller specify `ttl` at call time (or via a return-shape `{ value, ttl }` from `fn`). Useful when upstream sets cache-control headers.

## Revision notes

> **memoize-with-ttl — 60 second recap**
> - Closure over a `Map` of `{ value, expiresAt }` entries.
> - `Date.now() + ttl` at write; `expiresAt > Date.now()` at read.
> - Map > plain object: O(1) ops, any-key, no prototype pollution, insertion order.
> - Eviction modes: **lazy** (on-read), **active** (setTimeout per entry), **sweep** (setInterval), **LRU cap**. Discuss trade-offs.
> - Wrap values in `{value, expiresAt}` to distinguish missing from `undefined`.
> - Async: cache the **Promise** for in-flight dedupe; delete on rejection.
> - Always allow `keyFn` override — `JSON.stringify` is fragile.
> - **Trap:** `new Map()` inside the wrapper = broken. Unbounded TTL = memory leak.
