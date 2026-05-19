# Implement `memoize(fn)` — cache function results

> **Difficulty:** Easy-Medium   |   **Time:** ~15 min   |   **Prereqs:** [`concepts/closures.md`](../../concepts/closures.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
>
> **Source:** [LeetCode 2623 — Memoize](https://leetcode.com/problems/memoize/). The classic closure + Map exercise.

---

## 1. Problem statement

**Signature**
```ts
function memoize<F extends (...args: any[]) => any>(fn: F): F & { cache: Map<string, any>; clear(): void };
```

**Input / Output examples**

| Setup                                                          | Behaviour                                              |
|----------------------------------------------------------------|---------------------------------------------------------|
| `memo(1, 2); memo(1, 2);`                                     | `fn` called once; second call returns cached result   |
| `memo(1, 2); memo(2, 1);`                                     | different keys → `fn` called twice                    |
| `memo({a:1}); memo({a:1});`                                   | same JSON-key collide → cached (may be wrong if you wanted identity) |
| Returns `undefined`                                            | cached correctly via `cache.has`, not `?? compute`    |
| Same `memo()` used recursively (e.g., fib)                     | exponential speedup if `fn` calls memoized version    |

**Constraints**
- Cache key: `JSON.stringify(args)` for primitives + plain-object args.
- Use `Map` (not plain object) — O(1) ops, no `Object.prototype` collisions.
- Pure functions only — memoizing side effects is a bug.
- For object-identity-keyed caching → Memoize II (nested Map trie).

---

## 2. Plain-English restatement

Wrap a pure function so each unique input is computed once and cached. Subsequent calls with the same inputs return the cached result without re-running `fn`. Classic uses: expensive computations (fib, factorial), API response caches, derived-state computations. The key trick: use a `Map`, not a plain object (to avoid `__proto__` collisions); use `JSON.stringify(args)` as a cache key; use `cache.has(key)` (not `cache.get(key) ?? compute`) to handle cached `undefined` values.

---

## 3. Why this matters in interviews

Memoize is the classic 10-minute warm-up that tests **closures + Map + cache-key design** in one shot. Interviewers love it because the naive solution looks fine but breaks the moment the args contain objects — leading naturally into "Memoize II" (object-keyed). A senior answer pre-empts the "what about objects?" question by saying "this version assumes primitive args; for object-identity keys, you'd use a Map trie — happy to extend if useful."

---

## 4. Mental model

A **closure-scoped phone book**: every unique combination of args gets a phone number (the cached result). Lookup is O(1); first time you ring up an args set, the operator goes and fetches the answer (calls `fn`) and writes it down.

```
   memoize(fn)
     │
     └── closure-scoped Map
            │
            ├── "[1,2]" → 3       (cache.set after first fn(1,2))
            ├── "[2,1]" → 3       (different key, different entry)
            └── "[1,2,3]" → 6
   
   memo(1, 2) → cache.has("[1,2]")? yes → return 3 (skip fn)
   memo(3, 4) → cache.has("[3,4]")? no  → fn(3,4)=7, cache.set, return 7
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why use `Map` instead of `{}` for the cache?
> 2. What's wrong with `cache.get(key) ?? compute()` if `fn` can return `undefined`?
> 3. Will `memo({a:1, b:2})` and `memo({b:2, a:1})` share a cache entry?

---

## 6. Brute force — walked through

### Wrong attempt 1: plain object
```js
const cache = {};
if (cache[key]) ...   // BUG: prototype pollution, cached falsy values
```
`cache["toString"]` returns the inherited method. `cache.hasOwnProperty(key)` works but verbose. Use `Map` for O(1) ops, non-string keys, no proto pollution.

### Wrong attempt 2: `cache.get(key) ?? compute()`
If `fn` legitimately returns `undefined`, the next call re-invokes `fn` every time. Use `cache.has(key)` as the sentinel.

### Wrong attempt 3: cache inside the wrapper
```js
return function (...args) {
  const cache = new Map();   // BUG: fresh per call
  ...
};
```
Cache must live in factory scope.

### Wrong attempt 4: object-key shape collisions
`memo({a:1, b:2})` and `memo({b:2, a:1})` stringify identically → same cache entry. For shape-equality that's fine; for object-identity it's wrong. Use Memoize II (nested Map trie) if you need identity-keyed.

---

## 7. The unlocking insight

> **Closure-scoped `Map` keyed by `JSON.stringify(args)`. `cache.has(key)` then `cache.get(key)` (don't conflate with `??`). Forward `this` via `fn.apply(this, args)`.**

Three properties:

1. **`Map` not `{}`** — O(1), no `__proto__` collision, any key type (though we stringify here).
2. **`cache.has(key)`** as the sentinel — covers cached `undefined`.
3. **Closure-scoped cache** in factory function, not inside the wrapper.

Cache grows unbounded — for production, pair with LRU eviction or TTL.

---

## 8. Solution (annotated)

```js
function memoize(fn) {
  const cache = new Map();                                  // step 1: closure-scoped Map

  function memoized(...args) {
    const key = JSON.stringify(args);                        // step 2: stringify for primitive args
    if (cache.has(key)) {                                    // step 3: cache.has, not ?? compute
      return cache.get(key);
    }
    const result = fn.apply(this, args);                     // step 4: forward this
    cache.set(key, result);
    return result;
  }

  memoized.cache = cache;                                    // exposed for tests / debugging
  memoized.clear = () => cache.clear();
  return memoized;
}
```

**Try it yourself**

```js
let calls = 0;
const slowSum = (a, b) => { calls++; return a + b; };
const sum = memoize(slowSum);

sum(1, 2);    // calls=1, returns 3
sum(1, 2);    // calls=1 (cached), returns 3
sum(2, 1);    // calls=2, returns 3 (different key)
sum(1, 2);    // calls=1 (still cached), returns 3

console.log(calls);   // 2

// Fib with recursion via memoized self
const fib = memoize((n) => n < 2 ? n : fib(n - 1) + fib(n - 2));
fib(40);   // fast, even though naive fib(40) = ~1.6 billion ops
```

---

## 9. Step-by-step dry run

```
let calls = 0
const slowSum = (a,b) => { calls++; return a + b }
const sum = memoize(slowSum)

sum(1,2):  key="[1,2]". cache.has? no. fn(1,2)=3. calls=1. cache.set("[1,2]",3). return 3.
sum(1,2):  key="[1,2]". cache.has? yes. return cache.get("[1,2]")=3. calls unchanged.
sum(2,1):  key="[2,1]". cache.has? no. fn(2,1)=3. calls=2. cache.set("[2,1]",3). return 3.
sum(1,2):  cache hit. return 3.

After 4 calls: calls === 2.

Cache: { "[1,2]": 3, "[2,1]": 3 }
```

---

## 10. Common confusion + traps

1. **Plain object cache** → `__proto__` collision (e.g., `memo("toString")`).
2. **`cache.get(key) ?? compute()`** → re-invokes when `fn` returns `undefined`.
3. **Cache inside the wrapper** → fresh per call; memoize becomes a no-op.
4. **Forget `this` forwarding** → breaks `obj.method = memoize(obj.method)`.
5. **Object-key shape collisions** → `{a:1, b:2}` and `{b:2, a:1}` share entry.
6. **Memoizing side-effectful fn** → silent bug; result deviates from "fresh" call.
7. **Unbounded cache growth** → long-running process leaks memory. Use LRU.

---

## 11. Senior follow-ups & variants

### Variant 1 — Custom key resolver
```js
memoize(fn, { keyFn: (...args) => args[0].id })
```
Lets caller hash by specific property. Lodash supports this.

### Variant 2 — TTL memoize
Cache entries expire after N ms. Combine `Map<key, {value, expiry}>` with lazy eviction on read.

### Variant 3 — Async memoize (in-flight dedupe)
Cache the **Promise** (not the resolved value) so concurrent calls reuse the in-flight request. On reject, evict so next call retries. See [`04-promises/async-memoize.md`](../04-promises/async-memoize.md).

### Variant 4 — Bounded LRU memoize
Wrap cache in LRU container. Avoids unbounded memory in long-running processes.

### Variant 5 — Memoize II (object-identity keyed)
Nested Map trie. Each arg is a key in a tree of Maps. Handles object identity correctly without stringification. See [memoize-ii.md](./memoize-ii.md).

---

## 12. How to think aloud

> "Closure over a Map. Key = `JSON.stringify(args)`. `cache.has(key)` then `cache.get(key)` — avoid the `??` shortcut because `fn` might cache `undefined`. Forward `this` via `fn.apply`. Map over plain object for O(1) ops and no `__proto__` collision. For object-identity keys this version is wrong — two object literals with the same shape stringify identically; use a nested Map trie (Memoize II). For async, cache the Promise to dedupe in-flight calls. Cache grows unbounded; in production, wrap with LRU or TTL."

---

## 13. 60-second revision

> - **`new Map()`** in factory scope; key = `JSON.stringify(args)`.
> - **`cache.has(key)`** as sentinel, not `?? compute`.
> - **`fn.apply(this, args)`** for method-style use.
> - **Map > plain object:** O(1), no proto pollution.
> - **Pure functions only** — memoizing side effects is a bug.
> - **Object args:** shape-equality collides; use Memoize II for identity-keyed.
> - **Async:** cache the Promise (dedupe in-flight), evict on reject.
> - **Family:** memoize-ii, async-memoize, LRU memoize, TTL memoize.
> - **Trap:** plain object → proto collision; `??` → re-invokes on `undefined`; cache inside wrapper.

---

**Related:** [memoize-ii.md](./memoize-ii.md) · [`04-promises/async-memoize.md`](../04-promises/async-memoize.md) · [lru-cache.md](./lru-cache.md) · [`02-closures/memoize-with-ttl.md`](../02-closures/memoize-with-ttl.md) · [`02-closures/memoize-with-deep-equality.md`](../02-closures/memoize-with-deep-equality.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
