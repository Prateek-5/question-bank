# Implement `TimeLimitedCache` — TTL cache (LeetCode shape)

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [memoize-with-ttl.md](../02-closures/memoize-with-ttl.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
>
> **Source:** [LeetCode 2622 — Cache With Time Limit](https://leetcode.com/problems/cache-with-time-limit/).

---

## 1. Problem statement

**Signature**
```ts
class TimeLimitedCache {
  set(key: any, value: any, duration: number): boolean;   // true if non-expired entry existed
  get(key: any): any;                                      // value or -1 if missing/expired
  count(): number;                                         // count of non-expired entries
}
```

**Input / Output examples**

| Call sequence                                                              | Returns / state                      |
|-----------------------------------------------------------------------------|---------------------------------------|
| `c.set('a', 1, 100)` at t=0                                                | `false` (no prior entry)              |
| `c.set('a', 2, 50)` at t=60 (prior alive)                                  | `true` — clears old timer; replaces  |
| `c.get('a')` at t=80                                                       | `2`                                   |
| `c.get('a')` at t=120 (entry expired at t=110)                             | `-1`                                  |
| `c.count()` at t=130                                                       | `0`                                   |
| Overwrite without clearing prior timer                                     | **bug** — old timer wipes new value   |

**Constraints**
- `set` returns `true` iff a **non-expired** entry existed before.
- `get` returns `-1` for missing or expired entries.
- `count` excludes expired entries.
- **Critical:** `clearTimeout` the prior timer on overwrite — otherwise it fires and wipes the new value.
- Use `Map` (not plain object) for O(1) ops, non-string keys, no `__proto__` collisions.

---

## 2. Plain-English restatement

Build a key/value cache where each entry has its own time-to-live. Three methods: `set` (with per-key TTL), `get` (returns value or -1 on miss/expire), `count` (non-expired entries). Active eviction via `setTimeout` *plus* lazy verification on read for the small race window between `expiresAt` and the eviction timer firing.

The single most-failed detail: when you overwrite a key with an active TTL, you must `clearTimeout` the prior timer — otherwise that old timer will fire and wipe your new value.

---

## 3. Why this matters in interviews

TTL caches are the single most common backend caching primitive — Redis SETEX, memcached, Node's `lru-cache`. The interview probes two skills: (1) **expiry strategy** — active (`setTimeout` evicts on schedule) vs lazy (check `expiresAt` on read), and the tradeoffs; (2) **state hygiene** — using `Map` (not plain object) for O(1) ops + correct iteration semantics, and remembering to `clearTimeout` when you overwrite a key. Senior candidates are expected to bring up both strategies, pick one, and justify it.

---

## 4. Mental model

```
   class TimeLimitedCache {
     store: Map<key, { value, expiresAt, timerId }>
     
     set(k, v, ms):
       prev = store.get(k)
       existed = prev?.expiresAt > now
       if (prev) clearTimeout(prev.timerId)   ← THE critical line
       timerId = setTimeout(() => store.delete(k), ms)
       store.set(k, { value: v, expiresAt: now + ms, timerId })
       return existed
     
     get(k):
       e = store.get(k)
       if (!e) return -1
       if (e.expiresAt <= now) {              ← lazy verify
         clearTimeout(e.timerId)
         store.delete(k)
         return -1
       }
       return e.value
   }
```

**Active vs lazy expiry:**

- **Active** (`setTimeout` evicts on schedule) — keeps `count()` cheap and bounds memory. Cost: N timers in the event loop for N entries.
- **Lazy** (check `expiresAt` on read) — zero timer overhead, but expired entries linger in memory until a `get` or `count` hits them.
- **Production**: combine — active for memory cleanup, lazy for correctness across the small race window.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If you overwrite a key but forget `clearTimeout`, what happens when the old timer fires?
> 2. Why use `Map` instead of `{}` for the store?
> 3. For 1 million entries, what's the cost of active vs lazy expiry?

---

## 6. Brute force — walked through

### Wrong attempt 1: forget `clearTimeout` on overwrite

```js
set(key, value, duration) {
  const existed = this.store.has(key);
  const timerId = setTimeout(() => this.store.delete(key), duration);
  this.store.set(key, { value, expiresAt: Date.now() + duration, timerId });
  return existed;
}
```

`c.set('a', 1, 100)` at t=0 schedules T1 for t=100. `c.set('a', 2, 50)` at t=60 schedules T2 for t=110 — but **T1 still fires at t=100 and deletes the new value**. The cache appears empty at t=100 even though the new entry should be alive until t=110. Top failure mode.

### Wrong attempt 2: plain object as store

```js
constructor() { this.store = {}; }
set(key, value, duration) {
  // ...
  this.store[key] = ...;
}
```

Three problems:
- `__proto__` and `constructor` keys collide with object prototype.
- Numeric keys are stringified (`1` and `'1'` collide).
- No O(1) `size`, no insertion order for LRU variants.

Use `Map`.

### Wrong attempt 3: return `store.has(key)` for `set`

```js
set(key, value, duration) {
  const existed = this.store.has(key);   // BUG: true even for expired-but-not-evicted
  // ...
  return existed;
}
```

If the entry expired but its eviction timer hasn't fired yet, `has` returns `true`. The contract is "non-expired entry existed" — must check `expiresAt > now`.

### Wrong attempt 4: trust active eviction alone

```js
get(key) {
  const e = this.store.get(key);
  return e ? e.value : -1;             // BUG: race window
}
```

Between `expiresAt = t+100` and the timer firing at t+100, there's a microtask window where `get` could read the stale value. Always **lazy-verify** on read.

---

## 7. The unlocking insight

> **`Map<key, {value, expiresAt, timerId}>`. On `set`, `clearTimeout(prev.timerId)` before scheduling new. On `get`, lazy-verify `expiresAt > now`. `count` iterates and filters by `expiresAt`.**

Four invariants:

1. **`clearTimeout(prev.timerId)` on overwrite.** Even if the prior entry was already expired but its eviction timer hadn't fired yet. Otherwise the old timer wipes the new value.

2. **Lazy verify on `get`.** Even with active eviction, there's a microtask race window. Check `e.expiresAt > Date.now()` on every read.

3. **`set` returns `true` iff non-expired entry existed.** Not `store.has(key)`. Must check the timestamp.

4. **`count` filters by `expiresAt`.** Don't return `store.size` — it counts expired-but-not-evicted entries.

**Active vs lazy production decisions:**

- Small caches (< 1000 entries): active timers are fine. Memory tight; cheap to keep `count()` O(1)-ish.
- Large caches (100k+): prefer lazy. 100k timers waste resources. Add periodic GC (`setInterval(sweep, 60000)`) instead.
- For long-running Node servers, `.unref()` timers so they don't keep the process alive.

---

## 8. Solution (annotated)

```js
class TimeLimitedCache {
  constructor() {
    this.store = new Map();                                  // step 1: Map for O(1) + non-string keys
  }

  set(key, value, duration) {
    const now = Date.now();
    const prev = this.store.get(key);                         // step 2: peek prior
    const existed = !!prev && prev.expiresAt > now;           // step 3: non-expired check

    if (prev) clearTimeout(prev.timerId);                     // step 4: CRITICAL — clear old timer

    const timerId = setTimeout(() => {                        // step 5: schedule new eviction
      this.store.delete(key);
    }, duration);
    // timerId.unref?.();   // optional for Node servers

    this.store.set(key, { value, expiresAt: now + duration, timerId });
    return existed;
  }

  get(key) {
    const entry = this.store.get(key);
    if (!entry) return -1;
    if (entry.expiresAt <= Date.now()) {                      // step 6: lazy verify
      clearTimeout(entry.timerId);
      this.store.delete(key);
      return -1;
    }
    return entry.value;
  }

  count() {
    const now = Date.now();
    let n = 0;
    for (const e of this.store.values()) {                    // step 7: filter by expiresAt
      if (e.expiresAt > now) n++;
    }
    return n;
  }
}
```

**Lazy-only variant (for huge caches):**

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
      if (e.expiresAt <= now) this.store.delete(k);   // opportunistic GC
      else n++;
    }
    return n;
  }
}
```

**Try it yourself**

```js
const c = new TimeLimitedCache();
c.set('a', 1, 100);                       // false
setTimeout(() => c.set('a', 2, 50), 60);  // true (prior alive)
setTimeout(() => console.log(c.get('a')), 80);   // 2
setTimeout(() => console.log(c.get('a')), 120);  // -1
setTimeout(() => console.log(c.count()), 130);   // 0
```

---

## 9. Step-by-step dry run

```js
const c = new TimeLimitedCache();
c.set('a', 1, 100);                              // t=0
setTimeout(() => c.set('a', 2, 50), 60);         // t=60
setTimeout(() => c.get('a'), 80);                // t=80
setTimeout(() => c.get('a'), 120);               // t=120
```

Values-first trace:

| Time | Event                                              | Store state                          | Returns |
|------|----------------------------------------------------|---------------------------------------|---------|
| 0    | `set('a', 1, 100)`: prev=undefined, existed=false  | `{a: {value:1, expiresAt:100, timerId:T1}}` | `false` |
| 60   | `set('a', 2, 50)`: prev exists, expiresAt=100 > 60 → existed=true; `clearTimeout(T1)`; schedule T2 for t=110 | `{a: {value:2, expiresAt:110, timerId:T2}}` | `true` |
| 80   | `get('a')`: expiresAt=110 > 80 → return 2          | (same)                                | `2`     |
| 110  | T2 fires → `store.delete('a')`                     | `{}`                                  | —       |
| 120  | `get('a')`: not in store → return -1               | `{}`                                  | `-1`    |

**If we had forgotten `clearTimeout(T1)` at t=60**: T1 fires at t=100 and deletes 'a' — even though the new entry should be alive until t=110. `get` at t=120 returns -1 (correct for this scenario, but for the wrong reason — the timing of cache misses gets corrupted).

---

## 10. Common confusion + traps

1. **Forgetting `clearTimeout` on overwrite.** Top failure mode. Old timer wipes new value.

2. **Plain object instead of `Map`.** Prototype pollution; numeric keys collide with string forms; no insertion order; slower.

3. **Returning `store.has(key)` for `set`.** Wrong if entry expired but its timer hasn't fired yet.

4. **Trusting active expiry alone.** Race window between `expiresAt` and timer firing. Always lazy-verify in `get`.

5. **Returning `store.size` for `count`.** Includes expired-but-not-evicted entries. Filter by `expiresAt`.

6. **No `.unref()` in long-running Node services.** Active timers keep the process alive on graceful shutdown.

7. **Mutating cached objects.** Cache stores references. `c.set('a', obj, 100); obj.x = 1;` mutates the cache. Document or `structuredClone` on write.

---

## 11. Senior follow-ups & variants

### Variant 1 — LRU + TTL hybrid

```js
class LRUTTLCache {
  constructor(max) {
    this.store = new Map();   // Map insertion order = recency
    this.max = max;
  }
  set(k, v, ms) {
    if (this.store.has(k)) this.store.delete(k);   // delete-then-set: move to end
    const timerId = setTimeout(() => this.store.delete(k), ms);
    this.store.set(k, { value: v, expiresAt: Date.now() + ms, timerId });
    if (this.store.size > this.max) {
      const oldest = this.store.keys().next().value;
      const e = this.store.get(oldest);
      clearTimeout(e.timerId);
      this.store.delete(oldest);
    }
  }
  get(k) {
    const e = this.store.get(k);
    if (!e || e.expiresAt <= Date.now()) return -1;
    this.store.delete(k); this.store.set(k, e);   // refresh recency
    return e.value;
  }
}
```

Production-grade. Bounded memory.

### Variant 2 — Sliding TTL (extend on access)

```js
get(k) {
  const e = this.store.get(k);
  if (!e || e.expiresAt <= Date.now()) return -1;
  // Reschedule the timer for another full duration from now
  clearTimeout(e.timerId);
  e.expiresAt = Date.now() + e.originalDuration;
  e.timerId = setTimeout(() => this.store.delete(k), e.originalDuration);
  return e.value;
}
```

Entries that get accessed stay alive longer. Pattern for session caches.

### Variant 3 — `getRemainingTime(key)`

```js
getRemainingTime(key) {
  const e = this.store.get(key);
  if (!e) return 0;
  return Math.max(0, e.expiresAt - Date.now());
}
```

Useful for HTTP `Cache-Control: max-age` responses.

### Variant 4 — Async load-through cache

```js
async getOrLoad(key, loader) {
  const cached = this.get(key);
  if (cached !== -1) return cached;
  const value = await loader();
  this.set(key, value, this.defaultTTL);
  return value;
}
```

Combine with async memoize (in-flight dedupe). See [async-memoize.md](./async-memoize.md).

---

## 12. How to think aloud in the interview

> "`Map<key, {value, expiresAt, timerId}>`. `set`: clear prior timer if it exists, schedule new eviction timer, store entry, return true iff prior entry was non-expired. `get`: lazy-verify `expiresAt > now`; on hit, return value; on miss-or-expired, clear timer and delete, return -1. `count`: iterate and filter by `expiresAt`. The single most critical line is `clearTimeout(prev.timerId)` on overwrite — without it, the old timer fires and wipes the new value. Use Map not plain object for O(1) and non-string keys. For huge caches (>100k entries), prefer lazy-only + periodic GC over active timers — too many timers waste resources. For Node long-running services, `.unref()` timers."

---

## 13. 60-second revision

> - **`Map<key, {value, expiresAt, timerId}>`.**
> - **`clearTimeout(prev.timerId)` on overwrite** — top failure mode.
> - **`set` returns `true` iff non-expired prior existed** — not `store.has(key)`.
> - **Lazy verify on `get`** — covers race window between `expiresAt` and timer fire.
> - **`count` filters by `expiresAt`** — not `store.size`.
> - **`Map` not `{}`** — O(1), non-string keys, no `__proto__` collision.
> - **Large caches (>100k):** lazy-only + periodic GC.
> - **Family:** rate limiters, session caches, idempotency keys, async memoize.
> - **Trap:** forgetting `clearTimeout`; trusting active expiry alone; returning `store.has` for `set`.

---

**Related:** [memoize-with-ttl.md](../02-closures/memoize-with-ttl.md) · [async-memoize.md](./async-memoize.md) · [`08-maps-sets/ttl-map.md`](../08-maps-sets/ttl-map.md) · [`10-machine-coding-patterns/lru-cache.md`](../10-machine-coding-patterns/lru-cache.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md), [`concepts/promises.md`](../../concepts/promises.md)
