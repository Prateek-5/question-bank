# LRU Cache using `Map`

## Source
- Canonical interview problem (LeetCode #146 in many languages; JS-flavored variant).
- LeetCode reference: https://leetcode.com/problems/lru-cache/

## Why this question matters in interviews
LRU is **the** machine-coding problem at staff-and-up rounds. The interviewer is checking two things: (1) do you reach for **`Map`** in JS instead of building a HashMap + doubly-linked list, and (2) do you correctly exploit `Map`'s **insertion-order iteration** to get O(1) `get`, `set`, and eviction in ~20 lines? Backend engineers see LRU everywhere — query result caches, connection pools, JWT key caches, in-memory rate-limit buckets. Getting it wrong in production means either memory leaks (no eviction) or repeated cache misses (wrong recency policy). The JS-specific elegance — `delete + set` to bump recency — is the *entire* point of using `Map` over a generic dict.

## Concepts involved

### Syntax to lock in
```js
class LRUCache {
  constructor(capacity) {
    this.cap = capacity;
    this.map = new Map();
  }
  get(key) {
    if (!this.map.has(key)) return -1;
    const val = this.map.get(key);
    this.map.delete(key);                 // remove from current position
    this.map.set(key, val);               // re-insert at end (most recent)
    return val;
  }
  put(key, value) {
    if (this.map.has(key)) this.map.delete(key);
    this.map.set(key, value);
    if (this.map.size > this.cap) {
      const oldest = this.map.keys().next().value;   // O(1)
      this.map.delete(oldest);
    }
  }
}
```

### Runtime / engine behavior
- **`Map` preserves insertion order.** Iteration via `for...of map`, `map.keys()`, `map.values()`, `map.entries()` all yield entries in the order they were `set`. This is the ECMAScript spec, not an implementation detail.
- `map.delete(k)` followed by `map.set(k, v)` is **O(1) average** and moves the key to the **end** of the iteration order. That's the trick: "most recently used" = "most recently inserted."
- `map.keys().next().value` — calls the iterator protocol once. Returns the **first** (oldest) key in O(1). Don't reach for `Array.from(map.keys())[0]` — that's O(n).
- `map.size` is a getter; O(1).
- V8 implements `Map` as an open-addressing hash table with a parallel insertion-order index. Both operations stay O(1) average.

### Edge cases (these are the interview traps)
1. **Update of existing key** — must still bump to most-recent. Do `delete` + `set`, not just `set` (which keeps the original position!).
2. **Capacity of 0** — every `put` immediately evicts itself. Decide: throw, or silently no-op. Most implementations throw at construction; LeetCode often allows `cap >= 1`.
3. **`get` on missing key** — return `-1` (LeetCode convention) or `undefined`. Know which contract you're meeting.
4. **Eviction order** — oldest = `keys().next().value`. Never `entries().next()` then discard — same complexity but reads clumsy.
5. **`Map` keys are by identity** — `cache.put({}, 1); cache.get({})` is a miss because two object literals are distinct references. Same trap as `Map` in general.
6. **Object keys with `JSON.stringify`** — if you stringify to normalize, you've lost the identity advantage of `Map`. Decide upfront.
7. **Concurrent mutation during iteration** — don't iterate the map while inserting/deleting. The spec defines semantics but it's fragile; the LRU implementation never iterates, so this is moot.
8. **Memory** — `Map` does not GC keys. If keys are user objects you want auto-released, use **`WeakMap`** instead — but then you lose ordering (WeakMap is not iterable). LRU + WeakMap are mutually exclusive.
9. **Thread safety** — JS is single-threaded; nothing to worry about in browser/Node main thread. But across `worker_threads` you'd need a shared store.
10. **Doubly-linked-list alternative** — works in any language and is the textbook answer. In JS it's almost always wrong: `Map` already *is* a hashtable + ordered index.

## Brute force approach
Array of `[key, value]` pairs. `get`: linear scan, splice, push to end. `put`: linear scan to find existing key, then push. Eviction: `arr.shift()`. **O(n) per op.** Wrong but a useful straw man to mention so the interviewer sees you know why `Map` wins.

## Optimal approach
Single `Map`. Insertion order = recency order. Three idioms:
- `get(k)`: `delete + set` to bump.
- `put(k, v)`: `delete` if present, then `set`; evict `keys().next().value` if `size > cap`.
- Capacity check is **strict greater than** because the just-inserted key is also counted.

O(1) average for all three. O(cap) memory.

## Solution (JavaScript)

```js
class LRUCache {
  /**
   * @param {number} capacity  positive integer
   */
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be a positive integer');
    }
    this.capacity = capacity;
    this.map = new Map();
  }

  /**
   * @param {any} key
   * @returns {any}  value or -1 if missing
   */
  get(key) {
    if (!this.map.has(key)) return -1;
    const value = this.map.get(key);
    // Bump to most-recent position
    this.map.delete(key);
    this.map.set(key, value);
    return value;
  }

  /**
   * @param {any} key
   * @param {any} value
   */
  put(key, value) {
    if (this.map.has(key)) {
      this.map.delete(key);                // remove old position
    }
    this.map.set(key, value);              // insert as most-recent

    if (this.map.size > this.capacity) {
      // Evict least-recently-used = first inserted = first in iteration order
      const oldestKey = this.map.keys().next().value;
      this.map.delete(oldestKey);
    }
  }

  // Bonus utilities
  has(key)   { return this.map.has(key); }
  get size() { return this.map.size; }
  clear()    { this.map.clear(); }
}
```

## Step-by-step dry run

Input:
```js
const c = new LRUCache(2);
c.put(1, 'a');   // map: [1->a]
c.put(2, 'b');   // map: [1->a, 2->b]
c.get(1);        // returns 'a', bumps 1.   map: [2->b, 1->a]
c.put(3, 'c');   // size would be 3, evict oldest (2).  map: [1->a, 3->c]
c.get(2);        // -> -1 (evicted)
c.put(1, 'A');   // existing key — delete+set bumps. map: [3->c, 1->A]
c.put(4, 'd');   // evict 3.  map: [1->A, 4->d]
```

Detailed trace of `c.put(3, 'c')` when state is `[2->b, 1->a]`:
1. `map.has(3)` → false → skip delete.
2. `map.set(3, 'c')` → map becomes `[2->b, 1->a, 3->c]`. `size === 3`.
3. `size (3) > cap (2)` → evict. `map.keys().next().value` → `2`.
4. `map.delete(2)` → map becomes `[1->a, 3->c]`.

After all ops: cache contains `1 -> 'A'` and `4 -> 'd'`, recency order [1, 4]. Subsequent `get(1)` would return `'A'` and reorder to `[4, 1]`.

## Important takeaways

**Syntax to memorize**
- `map.delete(k); map.set(k, v)` — the "bump to most-recent" idiom.
- `map.keys().next().value` — O(1) oldest key.
- `size > capacity` (strict greater) for the eviction check.
- Class with `capacity`, `map`, three methods. No DLL, no extra index.

**Patterns to reuse**
- Map's **insertion order = recency** is reusable for: LFU's tie-breaker, MRU caches, ordered Sets (a Set is also insertion-ordered!), session stores, query-deduplication caches.
- "Delete + re-set to bump" — same trick works on `Set` for ordered-set-with-touch semantics.

**Common mistakes**
- Just calling `set(k, v)` on an existing key. `Map.set` **does not** reorder if the key exists — value updates in place, position stays. Cache becomes broken-LRU.
- Computing oldest via `Array.from(map.keys())[0]` — O(n) per eviction. Defeats the purpose.
- Using `>=` instead of `>` for the eviction check — evicts too eagerly.
- Reaching for HashMap + DLL in JS. Correct in C++/Java. Over-engineered in JS and slower (every node is a heap object).
- Returning `undefined` when the contract says `-1`. Read the spec.

**Related questions**
- LFU cache (least-frequently-used) — much harder; uses Map<freq, Set<key>>.
- TTL cache — combine Map ordering with `setTimeout` per key (see `Cache With Time Limit`).
- LRU with size in **bytes** rather than entries — useful for response caches.
- WeakMap-backed cache for object keys with auto-GC.

## Variants

1. **TTL on top of LRU** — each entry has `{ value, expiresAt }`. On `get`, check `expiresAt < Date.now()` and evict eagerly. Schedule a `setTimeout` per entry only if active sweeping is needed.

2. **Async LRU (request dedup)** — value is a Promise; if a key is in-flight, subsequent `get`s wait on the same promise. Memoizes async fetches; covers webhook deduplication.

3. **Capacity in bytes** — track an approximate byte size per entry (`new TextEncoder().encode(JSON.stringify(v)).length` or supplied by caller). Evict until total < cap. Same `delete + set` recency.

4. **Persistent (write-back) LRU** — on eviction, hand the entry to a `flush(key, value)` callback to persist to disk/DB. Backend-y variant for warm-cache patterns.

## Revision notes

> **LRU with Map — 60 second recap**
> - `Map` preserves insertion order. `delete(k); set(k, v)` = "bump to most recent."
> - `get`: bump and return; missing -> -1.
> - `put`: if exists, delete; set; if `size > cap`, evict `keys().next().value`.
> - All ops O(1) average.
> - **Trap:** just calling `set` on an existing key — value updates but position doesn't. Always delete first.
> - **Trap:** `>=` vs `>` on the eviction check.
> - Don't reach for HashMap + DLL in JS. `Map` is already exactly that.
