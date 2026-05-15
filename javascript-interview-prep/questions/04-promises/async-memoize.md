# Memoize an async function (dedupe in-flight calls)

## Source
- Senior backend / full-stack interview standard — appears at every shop that builds caching layers.
- Real-world: dedupe concurrent React `useEffect` fetches, dedupe upstream API calls in a Node API gateway, cache DB queries during a single request.
- Cousin of SWR / React Query / TanStack Query internals.

## Why this question matters in interviews
Async memoization tests something subtle: **cache the IN-FLIGHT promise, not the resolved value**. If three concurrent callers all `await memoized('key')`, the network should be hit **once**, not three times. Caching the value after settle is the easy part — caching the pending promise so concurrent callers share the same network roundtrip is the senior insight. This is exactly what request-deduplication libraries (SWR, React Query, p-memoize) do. Interviewers also probe: cache key generation (object args), eviction on rejection, TTL, and memory bounds.

## Concepts involved

### Syntax to lock in
```js
const fetchUser = asyncMemoize(async (id) => {
  const res = await fetch(`/api/users/${id}`);
  return res.json();
});

// Three concurrent calls → ONE network request.
const [a, b, c] = await Promise.all([fetchUser(1), fetchUser(1), fetchUser(1)]);
```

### Runtime / engine behavior
- Cache key: serialize args. For primitive args, `JSON.stringify(args)` is fine. For object args, decide upfront: deep equality (slow), reference equality (`Map` keyed by object), or hash a stable property.
- On call: if cache has a promise for the key, return it. Otherwise, call `fn`, store the promise, return it.
- **Critical decision**: what to do on rejection?
  - Cache it forever → next call sees the same rejection (good if errors are "real").
  - Delete on reject → next call retries (good for transient errors).
  - Common convention: **delete on reject**. Real libraries do this.
- TTL: optional second cache layer that expires entries after N ms.
- Memory bound: optional LRU cap.

### Edge cases (interview traps)
1. **Key from object args** — `JSON.stringify({ a: 1, b: 2 })` and `JSON.stringify({ b: 2, a: 1 })` produce different strings. Production code sorts keys or uses a deterministic stringifier.
2. **`undefined` args / variadic** — `JSON.stringify([1, undefined])` → `'[1,null]'`. Subtle.
3. **`this` context** — if `fn` is a method, memoize must preserve `this` (use `function` not arrow, `.apply(this, args)`).
4. **Pending promise eviction on success** — most implementations replace the pending promise with itself (no-op) because the promise is already resolved; subsequent `.then` resolves instantly.
5. **Memory leak** — if you never evict, the cache grows forever. Add LRU or TTL.
6. **Rejection caching** — discussed above; pick a policy and document it.
7. **Cancellation interaction** — if a memoized fetch supports cancellation and one caller cancels, the others shouldn't be affected. Don't propagate cancellation to the shared promise.

## Brute force approach
"Cache the resolved value after `await`." Looks fine — but two concurrent callers both miss the cache, both fire the network call. Defeats the purpose. The fix is to **cache the promise the moment you create it**, not the value after it settles.

## Optimal approach
`Map<string, Promise<V>>`. On call, compute key, return cached promise if present. Otherwise, create promise (call `fn(...)`), store in map BEFORE awaiting, attach `.catch` to delete on reject. Return promise.

## Solution (JavaScript)

```js
function asyncMemoize(fn, {
  keyFn = (...args) => JSON.stringify(args),
  cacheRejections = false,
  ttl = Infinity,
} = {}) {
  const cache = new Map(); // key -> { promise, expiresAt }

  function memoized(...args) {
    const key = keyFn(...args);
    const now = Date.now();
    const hit = cache.get(key);

    if (hit && hit.expiresAt > now) {
      return hit.promise;
    }

    // Create the promise; STORE FIRST, then attach error handler.
    const promise = Promise.resolve().then(() => fn.apply(this, args));
    cache.set(key, { promise, expiresAt: now + ttl });

    if (!cacheRejections) {
      promise.catch(() => {
        // Evict on rejection so the next call retries.
        if (cache.get(key)?.promise === promise) {
          cache.delete(key);
        }
      });
    }

    return promise;
  }

  memoized.clear = () => cache.clear();
  memoized.delete = (...args) => cache.delete(keyFn(...args));
  return memoized;
}

// Variant: object-arg-safe via WeakMap (when args are objects)
function asyncMemoizeByRef(fn) {
  const cache = new WeakMap();
  return function (arg) {
    if (cache.has(arg)) return cache.get(arg);
    const p = Promise.resolve().then(() => fn.call(this, arg));
    cache.set(arg, p);
    p.catch(() => { if (cache.get(arg) === p) cache.delete(arg); });
    return p;
  };
}
```

The `Promise.resolve().then(() => fn(...args))` wrapping converts a sync throw from `fn` into a rejection, which then triggers the eviction logic uniformly.

## Step-by-step dry run

Input:
```js
let networkCalls = 0;
const fetchUser = asyncMemoize(async (id) => {
  networkCalls++;
  await new Promise(r => setTimeout(r, 50));
  return { id, name: `User${id}` };
});

const [a, b, c] = await Promise.all([fetchUser(1), fetchUser(1), fetchUser(2)]);
console.log(networkCalls); // 2 — id=1 deduplicated, id=2 fresh
console.log(a === b);      // true — same resolved value AND same promise
```

Trace:
- **t=0** — `fetchUser(1)` (call A). Key=`'[1]'`. Cache miss. Build `Promise.resolve().then(() => fn(1))`. Store `cache.set('[1]', { promise: P1, expiresAt: ∞ })`. Return P1.
- **t=0** — `fetchUser(1)` (call B). Key=`'[1]'`. Cache hit (entry not expired). Return the *same* P1.
- **t=0** — `fetchUser(2)` (call C). Key=`'[2]'`. Cache miss. Store P2. Return P2.
- **microtask** — `Promise.resolve().then(() => fn(1))` triggers: networkCalls=1, schedule timer.
- **microtask** — `Promise.resolve().then(() => fn(2))` triggers: networkCalls=2, schedule timer.
- **t=50** — both timers fire. P1 resolves with `{id:1, name:'User1'}`. P2 resolves with `{id:2, name:'User2'}`.
- `Promise.all` completes. `a` and `b` are the SAME object (returned from P1). `c` is the User2 object.
- `networkCalls === 2`.

If one of the calls rejected (e.g., `fetchUser(1)` throws), all three callers awaiting `P1` see the same rejection. The `.catch` inside `asyncMemoize` evicts the entry, so a fresh `fetchUser(1)` after the rejection retries.

## Important takeaways

**Syntax to memorize**
- `cache.get(key)?.promise` — the cached entry.
- `Promise.resolve().then(() => fn.apply(this, args))` — normalize sync throws into rejections.
- Store-first-then-attach-error-handler — never reverse this order.
- Identity check before deleting: `if (cache.get(key)?.promise === promise)` — guards against race where a fresh entry was inserted before the rejection's microtask ran.

**Patterns to reuse**
- "Cache the in-flight promise, evict on settle" is the **request deduplication** pattern — same shape used in SWR, React Query, Apollo. Core idea generalizes to any shared async work.
- The identity-check-before-eviction is the **CAS (compare-and-swap)** pattern — protects against stale evictions in concurrent scenarios.
- WeakMap-by-arg-reference is the canonical **identity-keyed cache** trick — auto-evicts when args are garbage collected.

**Common mistakes**
- Caching the **resolved value** after `await` — defeats the purpose; two parallel callers still miss.
- Caching rejections forever by default — one transient error makes the function permanently broken.
- Not preserving `this` — breaks method-style use.
- Naive `JSON.stringify` on object args — non-deterministic key order, NaN/undefined edge cases.
- No bound on cache size — slow memory leak in long-running processes.
- Evicting without identity check — could delete a fresh entry if a slow retry's `.catch` fires after a new call settled.

**Related questions**
- `memoize` (sync version — see `closures/memoize-with-ttl.md`)
- `priority-async-queue.md` (often paired — memoize before queueing)
- `deferred-with-resolvers.md` (alternative implementation using deferreds explicitly)
- SWR / React Query architecture deep-dive

## Variants

1. **TTL-based async memoize** — entries expire after `ttl` ms. Already in the solution above.
2. **LRU async memoize** — bound cache size; evict least recently used on overflow. Use a Map (Map preserves insertion order) and delete+re-set on hit.
3. **Per-tenant cache** — accept a `tenantId` and namespace the cache. Common in multi-tenant APIs.
4. **Stale-while-revalidate** — return cached value immediately, fire fresh request in background, update cache on success. SWR's hallmark.
5. **Negative cache** — opt-in cache rejections with a separate TTL. Useful for "user not found" responses you don't want to retry every call.

## Revision notes

> **asyncMemoize — 60 second recap**
> - **Cache the promise, not the value** — that's how you dedupe concurrent calls.
> - Pattern: `Map<key, Promise>`. On call: return cached if present; else create, store, attach `.catch` to evict on reject.
> - Evict on reject (default) so transient errors don't permanently break the cache.
> - Wrap `fn(...)` in `Promise.resolve().then(() => fn(...))` to convert sync throws into rejections.
> - Use **identity check before delete** to avoid CAS races.
> - Cache key: stable stringify for primitives; WeakMap for object identity.
> - **Trap:** caching the resolved value instead of the in-flight promise — concurrent callers still fire N requests.
