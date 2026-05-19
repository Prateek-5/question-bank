# Request Deduplication — in-flight + recent two-layer dedup

> **Difficulty:** Medium-Senior   |   **Time:** ~20 min   |   **Prereqs:** [cache-stampede-single-flight.md](./cache-stampede-single-flight.md), [`04-promises/async-memoize.md`](../04-promises/async-memoize.md)
>
> **Source:** SWR's `dedupingInterval`, React Query, Apollo cache. Razorpay, Stripe, Atlassian, every BFF.

---

## 1. Problem statement

**Signature**
```ts
class Deduper {
  constructor(opts?: { dedupingIntervalMs?: number; lruCap?: number });
  fetch<T>(key: string, fn: () => Promise<T>): Promise<T>;
  invalidate(key: string): void;
  invalidateAll(): void;
}
```

**Input / Output examples**

| Setup (dedupingIntervalMs=500)                       | Behaviour                                              |
|------------------------------------------------------|---------------------------------------------------------|
| Concurrent `fetch('u', fn)` × 100                    | one `fn` call, all 100 share its promise               |
| Sequential `fetch('u', fn)` 50ms apart, fn took 200ms | first runs fn; later calls within recent window → cached |
| `fetch('u', fn)` 600ms later (window stale)          | runs fn again                                          |
| `fn` rejects                                          | error NOT cached in recent; next call retries          |
| `invalidate('u')` then `fetch('u', fn)`               | runs fn again                                          |

**Constraints**
- Two layers: `inflight` (concurrent) + `recent` (sub-second result reuse).
- **Errors don't cache** — failures retryable.
- LRU-bound `recent` to avoid unbounded growth.
- Canonicalize keys (sort object keys before stringify).

---

## 2. Plain-English restatement

User types in a search box: `search('a')`, `search('ab')`, then backspaces to `search('a')`. Without dedup → 3 network calls. With this Deduper: third call reuses the first's promise (if in-flight) OR its result (within the deduping window). Distinct from a cache: only collapses concurrent and near-concurrent calls.

---

## 3. Why this matters in interviews

Core to perceived performance in user-facing apps. Tests two-layer reasoning (in-flight vs recent), error semantics (don't cache failures), TTL/SWR concepts.

---

## 4. Mental model

```
   fetch(key, fn):
     1. inflight[key]?            → YES: return same promise (joined)
     2. recent[key] within X ms?  → YES: return cached result (no network)
     3. neither?                  → fire fn(); on success populate both

   Timeline (X = 500ms):
   t=0    call A → inflight={}, recent={} → fresh; p1
   t=10   call B → inflight has 'a' → return p1   (joined)
   t=200  p1 resolves → recent['a']={r, ts:200}; inflight.delete('a')
   t=210  call C → recent within 500ms → return cached r (no network)
   t=900  call D → recent stale (900-200=700>500) → fresh; p3
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why two layers (inflight + recent) instead of one?
> 2. Why don't errors populate `recent`?
> 3. What goes wrong if you cache `JSON.stringify(params)` without canonicalizing key order?

---

## 6. Brute force — walked through

### Wrong attempt 1: no dedup
Backspace mash → 20 search calls in 1s.

### Wrong attempt 2: only in-flight dedup
Sub-second repeated calls (StrictMode double-mount, double-Enter) still cause two fetches.

### Wrong attempt 3: TTL cache only
Concurrent first-misses all stampede (no inflight layer).

### Wrong attempt 4: cache errors in `recent`
Failed calls all rapidly see same error; no retry possible.

---

## 7. The unlocking insight

> **Two-layer dedup: `inflight: Map<key, Promise>` for concurrent dedup + `recent: Map<key, {result, ts}>` for sub-second repeated calls. Errors don't populate `recent`. Expose `invalidate(key)` for write-paths. LRU-bound `recent`.**

Three properties:

1. **In-flight + recent** — solves both concurrent stampede and sub-second repeats.
2. **Errors retry** — never cache failure in `recent`.
3. **LRU bound** — bounded memory under unbounded keyspace.

---

## 8. Solution (annotated)

```js
class Deduper {
  constructor({ dedupingIntervalMs = 2000, lruCap = 1000 } = {}) {
    this.inflight = new Map();                                       // step 1: concurrent layer
    this.recent = new Map();                                          // step 2: recent layer
    this.dedupingIntervalMs = dedupingIntervalMs;
    this.lruCap = lruCap;
  }

  _touch(key, val) {                                                 // step 3: LRU re-insert
    this.recent.delete(key);
    this.recent.set(key, val);
    if (this.recent.size > this.lruCap) {
      const oldest = this.recent.keys().next().value;
      this.recent.delete(oldest);
    }
  }

  async fetch(key, fn) {
    const inflight = this.inflight.get(key);
    if (inflight) return inflight;                                    // step 4: concurrent hit

    const cached = this.recent.get(key);
    if (cached && Date.now() - cached.ts < this.dedupingIntervalMs) {
      return cached.result;                                            // step 5: recent hit
    }

    const p = (async () => {
      try {
        const result = await fn();
        this._touch(key, { result, ts: Date.now() });                  // step 6: success → recent
        return result;
      } finally {
        this.inflight.delete(key);                                     // step 7: cleanup
      }
    })();
    this.inflight.set(key, p);
    return p;
  }

  invalidate(key) { this.recent.delete(key); }
  invalidateAll() { this.recent.clear(); }
}
```

**Try it yourself**

```js
const dedup = new Deduper({ dedupingIntervalMs: 500 });

async function searchUsers(q) {
  return dedup.fetch(`u:${q}`, () => fetch(`/api/users?q=${q}`).then((r) => r.json()));
}

// Type "ab" then backspace
await Promise.all([searchUsers('a'), searchUsers('ab'), searchUsers('a')]);
// First call fires; second 'ab' fires; third 'a' joins first's in-flight.

// On mutation
async function createUser(data) {
  const r = await fetch('/api/users', { method: 'POST', body: JSON.stringify(data) });
  dedup.invalidateAll();    // or invalidate specific keys
  return r;
}
```

---

## 9. Step-by-step dry run

```
dedupingIntervalMs=500.

t=0    searchUsers('a') → inflight miss; recent miss → fire fetch_a; p1
t=20   searchUsers('ab') → diff key → fire fetch_ab; p2
t=150  searchUsers('a') → inflight has 'a' (p1) → return p1 (joined)
t=300  p1 resolves → _touch('a', {result, ts:300}); inflight.delete('a')
t=350  searchUsers('a') → inflight miss; recent 'a' age=50<500 → return cached, NO fetch
t=900  searchUsers('a') → recent 'a' age=600>500 → stale → fire fetch_a; p3

Network calls: 3 ('a' at t=0, 'ab' at t=20, 'a' at t=900) vs 5 without dedup.

Error scenario:
  searchUsers('x') → fn rejects.
  finally: inflight.delete('x'). recent NOT populated.
  Next searchUsers('x') → fresh attempt (retry possible).
```

---

## 10. Common confusion + traps

1. **Dedup = cache** — no; dedup includes a tiny cache. Cache TTL is a separate concern.
2. **Only in-flight layer** — sub-second repeats still miss.
3. **Only TTL cache** — concurrent first-misses all stampede.
4. **Cache errors** — failures unretryable.
5. **Unbounded `recent`** — memory grows under high-cardinality keys.
6. **`JSON.stringify(params)` unsorted** — object key order is implementation-defined; canonicalize first.
7. **Forget `invalidate` on writes** — stale reads after mutations.

---

## 11. Senior follow-ups & variants

### Variant 1 — Stale-while-revalidate (SWR)
Return stale immediately, refresh in background. Two return values: `data` (possibly stale) + `isValidating`.

### Variant 2 — Per-user dedup
Key includes `userId` to avoid cross-user collisions in a BFF.

### Variant 3 — Network-aware
Pause dedup window during retries.

### Variant 4 — Focus-triggered revalidation
Invalidate all when tab regains focus (React Query default).

### Variant 5 — Distributed dedup
Multi-instance dedup via Redis + SETNX. Different machinery.

---

## 12. How to think aloud

> "Two-layer dedup: `inflight: Map<key, Promise>` for concurrent calls; `recent: Map<key, {result, ts}>` for sub-second repeated calls. `fetch(key, fn)`: in-flight hit wins, then recent-within-window wins, else fire fresh. Errors DON'T populate `recent` so failures retry. LRU bound `recent`. Canonicalize keys (sort object props). Pair with mutations: writes call `invalidate(key)`. SWR variant: return stale and revalidate in background. Trap: only in-flight layer; cache errors; unbounded recent; unsorted key serialization."

---

## 13. 60-second revision

> - **Two layers:** `inflight` (concurrent) + `recent` (sub-second).
> - **Errors don't cache** in `recent`; retry on next call.
> - **LRU-bound `recent`** for high-cardinality keys.
> - **Canonicalize keys** (sort object props before stringify).
> - **Invalidate on writes.**
> - **Different from cache:** dedup is short-window; cache TTL is hours.
> - **Variants:** SWR (stale + revalidate), per-user, focus-revalidate, distributed.
> - **Trap:** one-layer only; cache errors; unbounded recent; unsorted keys; missing invalidation.

---

**Related:** [cache-stampede-single-flight.md](./cache-stampede-single-flight.md) · [`04-promises/async-memoize.md`](../04-promises/async-memoize.md) · [dataloader-batch-cache.md](./dataloader-batch-cache.md) · [idempotency-wrapper.md](./idempotency-wrapper.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
