# Implement `memoize(fn, { ttl })` — cache results with time-based expiry

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [once-with-cached-return.md](./once-with-cached-return.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
>
> **Source:** Backend interview classic (BFE.dev, lodash `_.memoize` + TTL variants, GreatFrontend).

---

## 1. Problem statement

**Signature**
```ts
function memoize<F extends (...args: any[]) => any>(
  fn: F,
  options?: { ttl?: number; max?: number; keyFn?: (args: Parameters<F>) => string }
): F & { clear(): void; delete(key: string): boolean };
```

**Input / Output examples**

| Setup                                                 | Sequence at given times                          | Behaviour                                      |
|-------------------------------------------------------|--------------------------------------------------|------------------------------------------------|
| `let n=0; const f = memoize(x => (n++, x*2), {ttl: 100})` | `f(5)` at t=0, `f(5)` at t=10, `f(5)` at t=200 | `n=1` after the t=200 call (cached then expired) |
| `f(5); f(6); f(5)` at t=0 (no ttl)                     | mixed                                             | 2 calls total: `f(5)` cached, `f(6)` separate  |
| `f({a:1}); f({a:1})` with default `keyFn`              | repeated identical objects                        | both hit cache (`JSON.stringify(args)`)        |
| `const f = memoize(slow, {max: 100})`                  | 100+ unique calls                                 | LRU evicts oldest                              |

**Constraints**
- Per-call cache keyed by arguments (default: `JSON.stringify`).
- Optional `ttl` (ms) — expired entries are recomputed.
- Optional `max` — bounded cache size with LRU eviction.
- `undefined` must be cacheable as a legitimate return.
- Forward `this` to `fn`.

---

## 2. Plain-English restatement

Wrap `fn` so that calling it with the same arguments more than once returns the previously computed result instead of re-running `fn`. Add a time-to-live: entries older than `ttl` milliseconds are treated as misses and recomputed. Optionally cap the cache size so it doesn't grow forever — the oldest unused entry is evicted on overflow.

You're building a **closure over a `Map`** — the dominant pattern for any kind of local cache: in-flight dedupe, DataLoader, rate-limiter buckets, idempotency cache.

---

## 3. Why this matters in interviews

Plain `memoize` is a warmup; `memoize` with TTL is the senior-backend extension that probes whether you understand cache lifecycle. It hits four ideas in one problem: closure over a `Map`, time-based eviction (lazy vs active vs sweep), cache-key strategy, and the eviction-vs-memory tradeoff. As a backend engineer, you'll build this every few quarters — wrapping a slow upstream call (DB, third-party API, expensive computation) where stale-by-N-seconds is acceptable. Interviewers grade on the **eviction strategy discussion** more than the cache itself.

---

## 4. Mental model

The wrapper is a **library reference desk** with a hold-shelf behind it. Each request comes in keyed by its arguments. Staff check the shelf:

- **Hit and fresh** (within TTL): hand out the book on the shelf.
- **Miss or expired**: go fetch a new copy (call `fn`), put it on the shelf with a stamped expiry date, hand it out.
- **Shelf full** (size cap): toss the least-recently-checked-out book to make room.

```
   memoize(fn, {ttl: 100, max: 1000})
     │
     ├── shelf:  Map<key, { value, expiresAt }>
     │
     └── returns ──► wrapper(...args)
                       │
                       ├── key = keyFn(args)
                       ├── hit && expiresAt > now? → return value, refresh LRU
                       │
                       └── else → value = fn(...); store; evict oldest if size > max
```

The Map is preserved across calls because it lives in the factory's LE.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If `fn` returns `undefined`, will the next call hit the cache or re-run `fn`? Why does this hinge on how you check for "hit"?
> 2. What happens if you put `new Map()` *inside* the wrapper instead of in the outer scope?
> 3. With `ttl: Infinity` and no `max`, what's the failure mode?

---

## 6. Brute force — walked through

### Wrong attempt 1: `new Map()` inside the wrapper

```js
function memoize(fn) {
  return function (...args) {
    const cache = new Map();          // BUG: fresh cache every call
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const value = fn.apply(this, args);
    cache.set(key, value);
    return value;
  };
}
```

The cache resets on every invocation — memoize is a no-op. The Map must live in the factory scope, not the wrapper body.

### Wrong attempt 2: plain object instead of Map

```js
function memoize(fn) {
  const cache = {};                    // dangerous: prototype pollution + string-key only
  return function (...args) {
    const key = JSON.stringify(args);
    if (key in cache) return cache[key];
    return cache[key] = fn.apply(this, args);
  };
}
```

Works for most cases, but: `__proto__` and `constructor` keys cause prototype-pollution. Non-string keys are stringified silently (`1` and `'1'` collide). No O(1) `size`. `Map` solves all three.

### Wrong attempt 3: use `cache.get(key) ?? compute()` as the hit check

```js
const cached = cache.get(key);
if (cached !== undefined) return cached;
```

Breaks for `fn` that returns `undefined` legitimately. Use `cache.has(key)` (or wrap values in `{value, expiresAt}` and check the wrapper).

---

## 7. The unlocking insight

> **One `Map` in the factory scope, entries wrapped as `{value, expiresAt}` for two reasons: it lets `undefined` be a valid cache hit, and it carries the TTL with each entry.**

The Map lives in the factory LE; the wrapper closes over it; every call reads/writes through the closure. The wrapped value (`{value, expiresAt}`) solves two problems at once:

1. **Sentinel collision avoidance**: checking `cache.has(key)` (or `entry !== undefined`) distinguishes "no entry" from "entry with value `undefined`."
2. **Per-entry expiry**: storing `expiresAt = Date.now() + ttl` at write time lets the read path decide freshness independently for each entry.

Eviction is a senior-discussion topic. Four strategies, each with tradeoffs:

| Strategy | Mechanism | Pros | Cons |
|---|---|---|---|
| Lazy (on-read) | Check `expiresAt` only when something reads. | Simple, cheap. | Expired entries linger in memory until next read. |
| Active (per-entry timer) | `setTimeout(() => cache.delete(key), ttl)` on each set. | Frees memory on time. | One libuv timer per entry — 10k entries = 10k timers. |
| Sweep (periodic) | A single `setInterval` walks the map and deletes expired entries. | Best of both. | The sweep itself blocks the event loop briefly. |
| LRU + TTL | Bound size *and* time. Map's insertion order = LRU (delete-then-set refreshes). | Production-grade. | More moving parts. |

The default solution does **lazy + LRU cap** — production-friendly, no timers, bounded memory.

---

## 8. Solution (annotated)

```js
function memoize(fn, {                             // step 1: factory takes fn + options
  ttl = Infinity,                                   //         default = no expiry
  max = Infinity,                                   //         default = no size cap
  keyFn = (args) => JSON.stringify(args),           //         default = JSON-stringify args
} = {}) {
  const cache = new Map();                          // step 2: SINGLE Map in factory scope (NOT inside wrapper)

  function memoized(...args) {                      // step 3: returned wrapper
    const key = keyFn(args);                        // step 4: canonical key from args
    const now = Date.now();
    const hit = cache.get(key);

    if (hit !== undefined && hit.expiresAt > now) { // step 5: fresh hit — return cached value
      cache.delete(key);                             //         delete-and-reinsert to refresh
      cache.set(key, hit);                           //         LRU position (Map keeps insertion order)
      return hit.value;
    }

    const value = fn.apply(this, args);              // step 6: miss or expired — call fn, forward this
    cache.set(key, { value, expiresAt: now + ttl }); // step 7: wrap with expiry; insert at tail

    if (cache.size > max) {                          // step 8: bounded-size eviction
      const oldestKey = cache.keys().next().value;   //         Map iterates insertion order
      cache.delete(oldestKey);
    }
    return value;
  }

  memoized.clear  = () => cache.clear();             // step 9: decorated helpers
  memoized.delete = (key) => cache.delete(key);
  return memoized;
}
```

**Try it yourself**

```js
let calls = 0;
const slow = (x) => { calls++; return x * 2; };
const fast = memoize(slow, { ttl: 100 });

console.log(fast(5));      // 10, calls=1
console.log(fast(5));      // 10, calls=1 (cached)
console.log(fast(6));      // 12, calls=2
setTimeout(() => {
  console.log(fast(5));    // 10, calls=3 (expired, recomputed)
}, 150);
```

---

## 9. Step-by-step dry run

Input:

```js
let calls = 0;
const slow = (x) => { calls++; return x * 2; };
const fast = memoize(slow, { ttl: 100 });
fast(5);                        // t=0
fast(5);                        // t=10
fast(6);                        // t=20
setTimeout(() => fast(5), 150); // t=150
```

Values-first trace:

| Time | Call    | Key     | Cache state (key → value/expiresAt)     | Fresh hit? | `fn` called? | Returns | `calls` |
|------|---------|---------|------------------------------------------|------------|---------------|---------|---------|
| 0    | `fast(5)` | `'[5]'` | `{'[5]': v=10, exp=100}`                | no entry   | yes           | `10`    | 1       |
| 10   | `fast(5)` | `'[5]'` | hit fresh (exp=100 > 10)                 | yes        | no            | `10`    | 1       |
| 20   | `fast(6)` | `'[6]'` | `{'[5]':...; '[6]': v=12, exp=120}`     | no entry   | yes           | `12`    | 2       |
| 150  | `fast(5)` | `'[5]'` | entry exists but `exp=100 ≤ 150` → miss | no         | yes           | `10`    | 3       |

`fn` was invoked 3 times across 4 calls. The Map persisted via the factory closure.

---

## 10. Common confusion + traps

1. **`new Map()` inside the wrapper resets every call.**
   Has to live in the factory scope. The closure holds the Map; the wrapper reads/writes it.

2. **`cache.get(key) ?? compute()` is wrong for `undefined`-returning functions.**
   Use `cache.has(key)` or wrap entries in `{value, expiresAt}` and check the wrapper.

3. **`JSON.stringify` keys are fragile.**
   Functions become `null`, circular refs throw, BigInt throws, `undefined` becomes `null`. Allow a `keyFn` override.

4. **Forgetting `this` forwarding.**
   `fn(args)` ≠ `fn.apply(this, args)`. Breaks `obj.method = memoize(obj.method)`.

5. **Async results — cache the Promise.**
   For `async function`, store the Promise itself. Concurrent callers all `await` the same in-flight call. Delete on rejection so transient failures don't become sticky:
   ```js
   const value = fn.apply(this, args);
   cache.set(key, { value, expiresAt: now + ttl });
   if (value && typeof value.then === 'function') {
     value.catch(() => cache.delete(key));
   }
   ```

6. **Unbounded memory.**
   `ttl: Infinity` + no `max` + diverse keys = leak. Always pair with size cap in production.

7. **`Date.now()` jumps.**
   NTP can pull system time backwards. Doesn't break our logic (we only care about deltas) but if you care about monotonicity use `performance.now()`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async memoize with in-flight dedupe

```js
function memoizeAsync(fn, { ttl = Infinity } = {}) {
  const cache = new Map();
  return async function (...args) {
    const key = JSON.stringify(args);
    const now = Date.now();
    const hit = cache.get(key);
    if (hit && hit.expiresAt > now) return hit.value;     // value is a Promise

    const value = Promise.resolve().then(() => fn.apply(this, args));
    cache.set(key, { value, expiresAt: now + ttl });
    value.catch(() => cache.delete(key));                  // don't cache failures
    return value;
  };
}
```

Caching the **Promise** (not the resolved value) means 100 concurrent callers share one in-flight `fn` call. Same skeleton as [`10-machine-coding-patterns/cache-stampede-single-flight.md`](../10-machine-coding-patterns/cache-stampede-single-flight.md).

### Variant 2 — Active sweep instead of lazy eviction

```js
function memoize(fn, { ttl, sweepEveryMs = ttl } = {}) {
  const cache = new Map();
  const sweep = () => {
    const now = Date.now();
    for (const [k, { expiresAt }] of cache) {
      if (expiresAt <= now) cache.delete(k);
    }
  };
  const handle = setInterval(sweep, sweepEveryMs);
  if (handle.unref) handle.unref();   // don't keep Node alive just for the sweep
  return /* ... wrapper ... */;
}
```

Frees memory promptly; pays a periodic scan cost. Use when entries are expensive (large objects) and memory pressure matters.

### Variant 3 — Per-key TTL

Let `fn` return `{ value, ttl }` and use the per-call ttl instead of a fixed one. Useful for upstream cache-control headers.

```js
const wrapped = fn.apply(this, args);
const value = wrapped.value ?? wrapped;
const perKeyTtl = wrapped.ttl ?? ttl;
cache.set(key, { value, expiresAt: now + perKeyTtl });
```

### Variant 4 — Tag-based invalidation

Caching often needs "invalidate everything tagged `user:42`." Carry tags in entries and maintain a reverse index `Map<tag, Set<key>>`. See [`08-maps-sets/cache-invalidate-by-tag.md`](../08-maps-sets/cache-invalidate-by-tag.md).

### Variant 5 — WeakMap key when the args are an object (identity-based caching)

If the cache key is an object that you'd like garbage-collected when no longer referenced, use a `WeakMap` instead of `Map`. Trade-off: no `keys()`, no `size`, no iteration.

---

## 12. How to think aloud in the interview

> "Closure over a `Map<key, {value, expiresAt}>`. Map lives in the factory scope — must, otherwise the cache resets every call. Wrap entries with expiry so `undefined` can be a valid cached value (via `cache.has` or the `entry !== undefined` check on the wrapper). Default key is `JSON.stringify(args)` with a `keyFn` override for tricky inputs. Forward `this` via `apply`. For lifecycle: lazy eviction on read is simplest; active sweep for prompt cleanup; LRU cap for bounded memory. For async, cache the Promise and delete it on reject so failures don't stick. Expose `clear()` and `delete(key)` for testing and invalidation."

---

## 13. 60-second revision

> - **Pattern:** closure over `new Map()` in factory scope; wrap entries as `{value, expiresAt}`.
> - **Key default:** `JSON.stringify(args)`; allow `keyFn` override.
> - **Eviction:** lazy (on-read) is default; active sweep (`setInterval`) or LRU cap for production.
> - **LRU via Map insertion order:** delete-and-reinsert on hit refreshes recency; evict `cache.keys().next().value` on overflow.
> - **Async:** cache the **Promise** for in-flight dedupe; `.catch(() => cache.delete(key))` so failures don't stick.
> - **Trap:** `new Map()` inside the wrapper — broken (resets per call).
> - **Trap:** `cache.get(key) ?? compute()` — false negatives for `undefined`-returning functions.
> - **Family:** `memoize` (no TTL), LRU cache, DataLoader, request dedupe, rate-limiter buckets.

---

**Related:** [memoize-with-deep-equality.md](./memoize-with-deep-equality.md) · [once-with-cached-return.md](./once-with-cached-return.md) · [`10-machine-coding-patterns/cache-stampede-single-flight.md`](../10-machine-coding-patterns/cache-stampede-single-flight.md) · [`08-maps-sets/cache-invalidate-by-tag.md`](../08-maps-sets/cache-invalidate-by-tag.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md), [`concepts/closures.md`](../../concepts/closures.md)
