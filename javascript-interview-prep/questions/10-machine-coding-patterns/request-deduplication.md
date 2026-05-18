# Request Deduplication (Same-Key In-Flight Coalescing)

## Source / Origin
- React's `useDeferredValue` / Suspense cache; SWR `dedupingInterval`; React Query's queries; Apollo's `network-only` semantics.
- Asked at: Razorpay, Stripe, Atlassian; ubiquitous in any front-end or BFF role.
- Concept reference: sibling `cache-stampede-single-flight.md`, `dataloader-batch-cache.md`.

## Why this question matters in interviews
A search box fires `search('a')`, then `search('ab')`, then `search('a')` again because the user hit backspace. Without dedup, the network sees 3 requests; with dedup, the third reuses the first's promise (if still in-flight) or its cached result (if it just resolved). This pattern is core to perceived performance in user-facing apps. Interviewers test that you (1) distinguish *in-flight* dedup from *result cache*, (2) reason about TTL/stale-while-revalidate, (3) handle errors and aborts cleanly.

## Concepts involved

### Syntax to lock in
```js
class Deduper {
  constructor({ dedupingIntervalMs = 2000 } = {}) {
    this.inflight = new Map();        // key → promise
    this.recent   = new Map();        // key → { result, ts }
    this.dedupingIntervalMs = dedupingIntervalMs;
  }

  async fetch(key, fn) {
    // 1. in-flight dedup
    const inflight = this.inflight.get(key);
    if (inflight) return inflight;

    // 2. recent-result dedup (stale-while-revalidate window)
    const cached = this.recent.get(key);
    if (cached && (Date.now() - cached.ts) < this.dedupingIntervalMs) return cached.result;

    // 3. fresh fetch
    const p = (async () => {
      try {
        const result = await fn();
        this.recent.set(key, { result, ts: Date.now() });
        return result;
      } finally {
        this.inflight.delete(key);
      }
    })();
    this.inflight.set(key, p);
    return p;
  }

  invalidate(key) { this.recent.delete(key); }
}
```

### Edge cases / interview traps
1. **In-flight vs recent.** Two layers: one for concurrent duplicates, one for sub-second-apart duplicates after completion. SWR uses 2s default; React Query uses 0 (no recent-result reuse without `staleTime`).
2. **Errors should not cache.** Don't store an error in `recent`. Otherwise repeated rapid calls all see the same error.
3. **Abort propagation.** If a caller aborts but others are still waiting, don't cancel the in-flight — others depend on it. Reject *this caller's* awaiting branch only.
4. **Cache invalidation.** Mutations need to invalidate the dedup window; otherwise stale reads.
5. **Memory growth.** `recent` Map grows; bound with LRU or periodic sweep.
6. **TTL vs deduping interval.** Deduping is "no two identical calls within X ms"; full cache TTL is a different concept — keep separate.
7. **Key fidelity.** Build the key from *all* params (sort, filter, page). A naive `JSON.stringify` works but is order-dependent; canonicalize first.

## Mental Model

Two layers of dedup, layered on the fetch path:

```
   fetch(key, fn):
    1. inflight[key] exists?     →  YES: return same promise (caller B joins caller A)
    2. recent[key] within X ms?  →  YES: return cached result (NO network)
    3. neither?                  →  NO:  fire fn(), store in inflight; on resolve, copy to recent
```

```
    t=0   call A:  inflight={}, recent={} → fresh fetch, p1
    t=10  call B (same key):  inflight has → return p1
    t=200 p1 resolves; recent[key]={result, ts:200}; inflight.delete
    t=210 call C (same key): inflight empty; recent within 2000ms → return cached result, NO fetch
    t=2300 call D: recent stale → fresh fetch
```

## Why interviewers care

- **Front-end perf intuition.** Knowing why typeahead/autocomplete feels fast in well-built apps.
- **Layered cache reasoning.** In-flight, recent, persistent — three distinct buckets.
- **Error semantics.** Don't cache errors; do dedup errors mid-flight.

## Common beginner confusion

- **"Dedup = cache."** No. Dedup *includes* a tiny cache (recent), but the main job is collapsing concurrent and near-concurrent calls.
- **"Use just in-flight."** Sub-second repeated calls (e.g., React StrictMode double-mount, user-press-Enter-twice) still cause two fetches. Need recent-result reuse.
- **"Use just a TTL cache."** Concurrent requests during the first miss all stampede.
- **"`JSON.stringify(params)` is a stable key."** Object key order is implementation-defined; use a canonical serializer.
- **"Invalidate on every write."** Right idea — but make sure your write-paths actually call `invalidate(key)`.

## Brute force approach

```js
async function fetch(key, fn) {
  return fn();   // every call hits network
}
```

User mashing backspace → 20 search requests in 1 second.

## Optimal approach

Two-layer Map: `inflight` (collapses concurrent) and `recent` (collapses repeated within window). Errors don't populate `recent`. Expose `invalidate(key)` for write-path correctness.

## Solution (JavaScript)

```js
class Deduper {
  constructor({ dedupingIntervalMs = 2000, lruCap = 1000 } = {}) {
    this.inflight = new Map();
    this.recent = new Map();
    this.dedupingIntervalMs = dedupingIntervalMs;
    this.lruCap = lruCap;
  }

  _touch(key, val) {
    this.recent.delete(key);                      // re-insert at tail
    this.recent.set(key, val);
    if (this.recent.size > this.lruCap) {
      const oldest = this.recent.keys().next().value;
      this.recent.delete(oldest);
    }
  }

  async fetch(key, fn) {
    const inflight = this.inflight.get(key);
    if (inflight) return inflight;
    const cached = this.recent.get(key);
    if (cached && Date.now() - cached.ts < this.dedupingIntervalMs) return cached.result;

    const p = (async () => {
      try {
        const result = await fn();
        this._touch(key, { result, ts: Date.now() });
        return result;
      } finally {
        this.inflight.delete(key);
      }
    })();
    this.inflight.set(key, p);
    return p;
  }

  invalidate(key) { this.recent.delete(key); }
  invalidateAll() { this.recent.clear(); }
}

// Usage in a typeahead
const dedup = new Deduper({ dedupingIntervalMs: 500 });
async function searchUsers(q) {
  return dedup.fetch(`u:${q}`, () => fetch(`/api/users?q=${q}`).then(r => r.json()));
}
```

## Step-by-step dry run

`dedupingIntervalMs=500`. User types "ab", then backspaces to "a" (already typed):

```
t=0    searchUsers('a') → inflight miss, recent miss → fire fetch, p1
t=20   searchUsers('ab') → diff key → fire fetch, p2
t=150  searchUsers('a') → inflight has 'a' (still p1) → return p1 (joined)
t=300  p1 resolves → recent['a']={r, 300}; inflight.delete('a')
t=350  searchUsers('a') → inflight miss; recent['a'] within 500ms → return cached, no fetch
t=900  searchUsers('a') → recent['a'] stale (900-300=600 > 500) → fire fetch, p3
```

Network traffic: 3 calls (`a` at t=0, `ab` at t=20, `a` at t=900) instead of 5.

## How to think aloud in the interview

> "Two-layer dedup: `inflight` Map for concurrent calls, `recent` Map (with timestamp + LRU bound) for sub-second repeats. On `fetch(key, fn)`: in-flight wins, then recent-result wins (within window), otherwise fire fresh and store in both. `finally` cleans `inflight` regardless of success. Errors don't populate `recent` — so failures are retryable immediately. Expose `invalidate(key)` for mutations. The deduping interval is the perceived-fresh threshold — 500ms-2s typical."

## Important takeaways

- **Two layers**: in-flight + recent. Different problems.
- **Errors don't cache.** Recent stays empty on rejection.
- **LRU bound the recent map.** Otherwise unbounded growth.
- **Key canonicalization.** Sort object keys before stringify.
- **Pair with mutations.** Writes call `invalidate(key)`.

## Variants

- **stale-while-revalidate (SWR)** — return stale immediately *and* refresh in background. Two return values: `data` (possibly stale) + `isValidating`.
- **Per-user dedup** — key includes `userId` to avoid cross-user collisions in a BFF.
- **Network-aware** — pause dedup window during retries on the underlying fetch.
- **`focus`-triggered revalidation** — invalidate everything when the tab regains focus (React Query default).

## Revision notes

```
Deduper:
  fetch(key, fn):
    inflight has? return same promise
    recent within window? return cached result
    else: fire fn(); store in inflight + recent (on success)
    finally: delete inflight
  
  TWO layers: inflight (concurrent) + recent (sub-second)
  errors do NOT cache
  LRU bound recent
  invalidate(key) on writes
  variants: SWR, per-user, focus-revalidate
```
