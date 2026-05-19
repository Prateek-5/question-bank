# Implement `asyncMemoize(fn)` — cache the in-flight promise

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [memoize-with-ttl.md](../02-closures/memoize-with-ttl.md), [build-promise-from-scratch.md](./build-promise-from-scratch.md)
>
> **Source:** Senior backend / full-stack interview standard. Foundation for SWR, React Query, p-memoize, Apollo cache.

---

## 1. Problem statement

**Signature**
```ts
function asyncMemoize<F extends (...args: any[]) => Promise<any>>(
  fn: F,
  opts?: {
    keyFn?: (...args: any[]) => string;
    cacheRejections?: boolean;
    ttl?: number;
  }
): F & { clear(): void; delete(...args: any[]): boolean };
```

**Input / Output examples**

| Setup                                                                 | Behaviour                                                |
|-----------------------------------------------------------------------|-----------------------------------------------------------|
| Three concurrent `memoized(1)` calls                                  | **One** call to underlying `fn` — concurrent callers share the same in-flight promise |
| `memoized(1)` then `memoized(1)` after settle                         | second call hits cache, returns same resolved value      |
| `memoized(1)` rejects; `memoized(1)` again                           | retries (default eviction on reject)                     |
| `memoized(1)` rejects with `cacheRejections: true`                    | second call sees the cached rejection (no retry)         |
| With `ttl: 1000`, second call after 2s                                | retries (entry expired)                                  |

**Constraints**
- **Cache the in-flight Promise**, not the resolved value. That's how concurrent callers dedupe.
- Default: **evict on rejection** so transient errors don't permanently break the cache.
- Forward `this` for method-style use.
- Wrap `fn(...)` in `Promise.resolve().then(...)` to convert sync throws into rejections.
- Use **identity check before deletion** to avoid CAS-style races.

---

## 2. Plain-English restatement

Wrap an async function so that calling it with the same arguments more than once returns the same Promise — both for **concurrent calls** (three callers fire at the same time → one network request, three callers wait on the same promise) and for **after-settle calls** (cache hits the resolved value).

The crucial insight: cache the **Promise itself**, not the resolved value. If you cache the value after `await`, two parallel callers both miss the cache, both fire the network call. By storing the in-flight promise the moment you create it, every concurrent caller subscribes to the same one.

---

## 3. Why this matters in interviews

Async memoization tests something subtle: **cache the IN-FLIGHT promise, not the resolved value**. If three concurrent callers all `await memoized('key')`, the network should be hit **once**, not three times. Caching the value after settle is the easy part — caching the pending promise so concurrent callers share the same network roundtrip is the senior insight. This is exactly what request-deduplication libraries (SWR, React Query, p-memoize) do. Interviewers also probe: cache key generation (object args), eviction on rejection, TTL, memory bounds, and the identity check before deletion (CAS pattern).

---

## 4. Mental model

```
   asyncMemoize(fn)
        │
        ├── cache: Map<key, { promise, expiresAt }>
        │
        └── returns wrapper(...args):
              key = keyFn(...args)
              if cache.has(key) and not expired → return cached promise
              else:
                promise = Promise.resolve().then(() => fn(...args))
                cache.set(key, { promise, expiresAt })
                promise.catch(() => cache.delete(key))   // evict on reject
                return promise

   Concurrent callers:
     caller 1: memoized(1) → cache miss → store P1 → return P1
     caller 2: memoized(1) → cache HIT → return SAME P1
     caller 3: memoized(1) → cache HIT → return SAME P1
   All three await the same promise. fn is called ONCE.
```

Three semantic decisions:

1. **Cache the promise, not the value** — concurrent dedupe.
2. **Evict on rejection by default** — transient errors retry on next call.
3. **Identity check before deletion** — guards against CAS race where a fresh entry was inserted before the rejection's microtask ran.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If two callers fire `memoized(1)` at the same time, how many network requests happen?
> 2. If you cache the resolved value (after `await`), how does that behave under concurrent calls?
> 3. If `fn` throws synchronously (bad input), what should the wrapper do?

---

## 6. Brute force — walked through

### Wrong attempt 1: cache the resolved value

```js
function asyncMemoizeBad(fn) {
  const cache = new Map();
  return async (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const result = await fn(...args);    // BUG: two callers both miss cache before this resolves
    cache.set(key, result);
    return result;
  };
}
```

Two concurrent callers both hit `cache.has === false`, both fire `fn`, both write the same value at the end. Network hit twice. **Cache the promise to prevent this.**

### Wrong attempt 2: cache rejections forever

```js
const promise = fn(...args);
cache.set(key, promise);
// no eviction on reject
```

If `fn(...args)` rejects once due to a transient error, every subsequent caller sees the same rejection forever. Network is broken in cache. Default should be: evict on reject so the next call retries.

### Wrong attempt 3: evict without identity check

```js
promise.catch(() => cache.delete(key));
```

Sounds fine, but consider:
- Call 1: fires, store P1, P1 rejects.
- Call 2: BEFORE P1's `.catch` microtask fires, this call hits cache (P1 still there), grabs P1 (which is rejected).
- Call 3: After P1's `.catch` evicts. Now call 3 misses cache, fires P3. Cache stores P3.
- P1's `.catch` runs: `cache.delete(key)` — deletes **P3** instead of P1.

Use identity check:

```js
promise.catch(() => {
  if (cache.get(key)?.promise === promise) cache.delete(key);
});
```

CAS pattern — only delete if the entry is still mine.

### Wrong attempt 4: forget to handle sync throws

```js
const promise = fn(...args);   // BUG: if fn throws synchronously, wrapper crashes
```

Wrap with `Promise.resolve().then(() => fn(...args))` to convert sync throws into rejections uniformly.

---

## 7. The unlocking insight

> **Cache the in-flight Promise (not the resolved value) so concurrent callers share one network roundtrip. Evict on rejection (default) so transient failures don't stick. Use identity-check-before-delete to avoid CAS races. Wrap `fn(...)` in `Promise.resolve().then(...)` for sync-throw safety.**

The complete shape:

```js
function asyncMemoize(fn, opts = {}) {
  const {
    keyFn = (...args) => JSON.stringify(args),
    cacheRejections = false,
    ttl = Infinity,
  } = opts;
  const cache = new Map();

  function memoized(...args) {
    const key = keyFn(...args);
    const now = Date.now();
    const hit = cache.get(key);

    if (hit && hit.expiresAt > now) return hit.promise;

    const promise = Promise.resolve().then(() => fn.apply(this, args));
    cache.set(key, { promise, expiresAt: now + ttl });

    if (!cacheRejections) {
      promise.catch(() => {
        if (cache.get(key)?.promise === promise) cache.delete(key);
      });
    }

    return promise;
  }

  memoized.clear = () => cache.clear();
  memoized.delete = (...args) => cache.delete(keyFn(...args));
  return memoized;
}
```

Three subtleties to articulate:

1. **`Promise.resolve().then(() => fn.apply(this, args))`** lifts sync throws and async work uniformly into a promise we can `.catch` on.

2. **`cache.set` BEFORE `.catch` registration.** The order matters — if you `.catch` first and `set` second, a rejection in the same microtask could trigger eviction of an entry that doesn't exist yet.

3. **Identity check `cache.get(key)?.promise === promise`** prevents the CAS-style race where a fresh entry was inserted between the original rejection and its eviction microtask.

---

## 8. Solution (annotated)

```js
function asyncMemoize(fn, {
  keyFn = (...args) => JSON.stringify(args),
  cacheRejections = false,
  ttl = Infinity,
} = {}) {
  const cache = new Map();                                       // step 1: key → { promise, expiresAt }

  function memoized(...args) {
    const key = keyFn(...args);
    const now = Date.now();
    const hit = cache.get(key);

    if (hit && hit.expiresAt > now) {                             // step 2: cache hit (still valid)
      return hit.promise;
    }

    const promise = Promise.resolve().then(() => fn.apply(this, args));  // step 3: lift fn into promise
    cache.set(key, { promise, expiresAt: now + ttl });            // step 4: store FIRST

    if (!cacheRejections) {
      promise.catch(() => {                                        // step 5: evict on rejection
        if (cache.get(key)?.promise === promise) {                  // step 6: identity check (CAS)
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

// WeakMap variant for object-keyed identity caching
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

**Try it yourself**

```js
let networkCalls = 0;
const fetchUser = asyncMemoize(async (id) => {
  networkCalls++;
  await new Promise((r) => setTimeout(r, 50));
  return { id, name: `User${id}` };
});

// Three concurrent calls — ONE network hit
const [a, b, c] = await Promise.all([fetchUser(1), fetchUser(1), fetchUser(2)]);
console.log(networkCalls);   // 2  (id=1 deduplicated, id=2 fresh)
console.log(a === b);         // true (same resolved value AND same promise)
console.log(a.id === c.id);   // false

// Retry on rejection (default)
let attempt = 0;
const flaky = asyncMemoize(async () => {
  attempt++;
  if (attempt === 1) throw new Error('first call fails');
  return 'success';
});
try { await flaky(); } catch {}
const result = await flaky();   // retries — attempt=2, returns 'success'
console.log(result);             // 'success'

// TTL eviction
const cached = asyncMemoize(async (id) => fetch(`/api/${id}`).then(r => r.json()),
                            { ttl: 1000 });
await cached(1);                    // network hit
await cached(1);                    // cache hit
await sleep(2000);
await cached(1);                    // network hit (TTL expired)
```

---

## 9. Step-by-step dry run

Input:

```js
let networkCalls = 0;
const fetchUser = asyncMemoize(async (id) => {
  networkCalls++;
  await new Promise(r => setTimeout(r, 50));
  return { id, name: `User${id}` };
});

const [a, b, c] = await Promise.all([fetchUser(1), fetchUser(1), fetchUser(2)]);
```

Values-first trace:

| Time (ms) | Event                                                                            | `cache` state                        | `networkCalls` |
|-----------|-----------------------------------------------------------------------------------|---------------------------------------|----------------|
| 0         | `fetchUser(1)` call A: key='[1]'; miss; create P1; store; return P1              | `{ '[1]': P1 }`                      | 0              |
| 0         | `fetchUser(1)` call B: key='[1]'; HIT; return same P1                            | `{ '[1]': P1 }`                      | 0              |
| 0         | `fetchUser(2)` call C: key='[2]'; miss; create P2; store; return P2              | `{ '[1]': P1, '[2]': P2 }`           | 0              |
| 0+µ       | P1's `.then` fires: `fn(1)` runs; `networkCalls=1`; schedule timer               | (same)                                | 1              |
| 0+µ       | P2's `.then` fires: `fn(2)` runs; `networkCalls=2`; schedule timer               | (same)                                | 2              |
| 50        | both timers fire; P1 resolves with `{id:1, name:'User1'}`; P2 resolves           | (same)                                | 2              |
| 50+µ      | `Promise.all` resolves                                                            | (same)                                | 2              |

`a` and `b` are the *same object* (returned from P1). `c` is the User2 object. `networkCalls === 2`, not 3.

If one of the calls rejected (e.g., `fetchUser(1)` throws), all three callers awaiting P1 see the same rejection. The `.catch` inside `asyncMemoize` evicts the entry. A subsequent `fetchUser(1)` would retry.

---

## 10. Common confusion + traps

1. **Caching the resolved value instead of the promise.**
   Concurrent callers still fire N requests. The whole point is to cache *during* the in-flight window.

2. **Caching rejections forever by default.**
   One transient error makes the function permanently broken. Default: evict on reject.

3. **Not preserving `this`.**
   `fn.apply(this, args)` — methods need this.

4. **Naive `JSON.stringify` on object args.**
   Non-deterministic key order (engine-specific), NaN/undefined edge cases. Use a stable stringify or `keyFn` override.

5. **No bound on cache size.**
   Slow memory leak in long-running processes. Add LRU.

6. **Evicting without identity check.**
   Could delete a fresh entry if a slow retry's `.catch` fires after a new call settled. Use `cache.get(key)?.promise === promise` before deletion.

7. **Forgetting `Promise.resolve().then(...)` wrap.**
   `fn` can throw synchronously (bad input, type errors). The wrap converts to rejection.

8. **Storing the promise *after* registering `.catch`.**
   Race condition: rejection microtask runs before `cache.set`. Store first, then register the handler.

---

## 11. Senior follow-ups & variants

### Variant 1 — TTL + LRU bounds

```js
function asyncMemoize(fn, { ttl = Infinity, maxSize = 1000, keyFn } = {}) {
  const cache = new Map();   // Map preserves insertion order — natural LRU
  return function (...args) {
    const key = keyFn(...args);
    const now = Date.now();
    const hit = cache.get(key);
    if (hit && hit.expiresAt > now) {
      cache.delete(key);                                // LRU: move to end on hit
      cache.set(key, hit);
      return hit.promise;
    }
    const promise = Promise.resolve().then(() => fn.apply(this, args));
    cache.set(key, { promise, expiresAt: now + ttl });
    if (cache.size > maxSize) cache.delete(cache.keys().next().value);   // evict oldest
    promise.catch(() => { if (cache.get(key)?.promise === promise) cache.delete(key); });
    return promise;
  };
}
```

### Variant 2 — Stale-while-revalidate (SWR's hallmark)

```js
function asyncMemoizeSWR(fn, { ttl, staleTtl } = {}) {
  const cache = new Map();
  return function (...args) {
    const key = JSON.stringify(args);
    const now = Date.now();
    const hit = cache.get(key);

    if (hit && hit.freshUntil > now) return hit.promise;         // fresh — return cached

    if (hit && hit.staleUntil > now) {                            // stale — return cached + refresh in bg
      backgroundRefresh(key, args);
      return hit.promise;
    }

    // expired — fetch fresh
    const promise = Promise.resolve().then(() => fn.apply(this, args));
    cache.set(key, { promise, freshUntil: now + ttl, staleUntil: now + staleTtl });
    return promise;
  };
}
```

Return immediately with stale data; fetch fresh in background.

### Variant 3 — Negative cache for "not found" responses

```js
function asyncMemoize(fn, { ttl, negTtl } = {}) {
  const cache = new Map();
  return function (...args) {
    const key = JSON.stringify(args);
    const hit = cache.get(key);
    if (hit) return hit.promise;
    const promise = Promise.resolve().then(() => fn.apply(this, args));
    cache.set(key, { promise });
    promise.then(
      () => { cache.set(key, { promise, expiresAt: Date.now() + ttl }); },
      () => { cache.set(key, { promise, expiresAt: Date.now() + negTtl }); },
    );
    return promise;
  };
}
```

Cache rejections briefly so you don't retry every call, but flush quickly.

### Variant 4 — Per-tenant namespacing

```js
function asyncMemoize(fn, { keyFn, tenantOf } = {}) {
  const tenantCaches = new Map();
  return function (tenantId, ...args) {
    if (!tenantCaches.has(tenantId)) tenantCaches.set(tenantId, new Map());
    const cache = tenantCaches.get(tenantId);
    // ... rest of standard memoize, scoped to this tenant cache ...
  };
}
```

Multi-tenant APIs: don't leak across tenants.

### Variant 5 — Cancellation safety

If a memoized fetch supports cancellation and one caller cancels, the others shouldn't be affected. Don't propagate cancellation to the shared promise:

```js
// Each caller wraps the shared promise in a per-caller cancellation layer
function withCancellation(promise, signal) {
  return new Promise((resolve, reject) => {
    promise.then(resolve, reject);
    signal?.addEventListener('abort', () => reject(signal.reason), { once: true });
  });
}
```

---

## 12. How to think aloud in the interview

> "Cache the in-flight Promise, not the resolved value — that's the senior insight. Concurrent callers get the same promise, share one network roundtrip. Default: evict on rejection so transient errors retry; opt-in to cache rejections via flag. Use identity check before deletion (`cache.get(key)?.promise === promise`) to guard against CAS races. Wrap `fn(...args)` in `Promise.resolve().then(...)` for sync-throw safety. For object args, use a stable stringify (sorted keys) or WeakMap by reference. Add TTL + LRU bounds for memory safety. For React-style stale-while-revalidate, layer fresh-vs-stale windows. Per-tenant: namespace the cache. Each method call preserves `this` via `fn.apply(this, args)`."

---

## 13. 60-second revision

> - **Cache the promise**, not the resolved value — concurrent dedupe.
> - **Pattern:** `Map<key, {promise, expiresAt}>`.
> - **Evict on reject (default)** so transient errors retry.
> - **Identity check before delete:** `if (cache.get(key)?.promise === promise) cache.delete(key)`.
> - **`Promise.resolve().then(() => fn(...))`** for sync-throw safety.
> - **Preserve `this`:** `fn.apply(this, args)`.
> - **Key:** stable stringify or `keyFn` override; WeakMap for object identity.
> - **TTL + LRU** for memory safety.
> - **Family:** request dedupe, SWR, React Query, Apollo cache.
> - **Trap:** caching value (concurrent leak), caching rejections forever, evicting without identity check, no `Promise.resolve()` wrap.

---

**Related:** [memoize-with-ttl.md](../02-closures/memoize-with-ttl.md) · [memoize-with-deep-equality.md](../02-closures/memoize-with-deep-equality.md) · [cache-with-time-limit.md](./cache-with-time-limit.md) · [priority-async-queue.md](./priority-async-queue.md) · [`10-machine-coding-patterns/cache-stampede-single-flight.md`](../10-machine-coding-patterns/cache-stampede-single-flight.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
