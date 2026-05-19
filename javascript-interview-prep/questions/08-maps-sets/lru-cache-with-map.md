# LRU Cache using `Map`

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md), [ttl-map.md](./ttl-map.md)
>
> **Source:** LeetCode #146. Staff-and-up machine-coding staple.

---

## 1. Problem statement

LRU cache with O(1) get/put. JS trick: `Map` preserves insertion order; `delete + set` re-inserts at end (most recent).

**Verification examples**

```js
const cache = new LRUCache(2);
cache.put(1, 'a');
cache.put(2, 'b');
cache.get(1);                            // 'a' — bumps 1 to most recent
cache.put(3, 'c');                       // evicts 2 (LRU)
cache.get(2);                            // -1 (evicted)
cache.get(3);                            // 'c'
```

**Constraints**
- O(1) get & put.
- Capacity-bounded.
- Eviction: least recently used.
- Touch on read (get) also bumps recency.

---

## 2. Plain-English restatement

Map keeps insertion order. Reading: delete + set re-inserts at end (newest). Writing over capacity: evict `map.keys().next().value` (oldest).

---

## 3. Why this matters in interviews

THE machine-coding problem at staff. Tests: Map literacy + insertion-order trick + O(1) discipline. In production: query caches, JWT key caches, connection pools.

---

## 4. Mental model

```
   Map preserves insertion order (ES2015 spec).
   
   LRU operations:
     get(k):
       if not in map: return -1
       val = map.get(k)
       map.delete(k); map.set(k, val)    ← bump to most recent
       return val
   
     put(k, v):
       if map has k: map.delete(k)        ← will re-insert at end
       map.set(k, v)
       if map.size > cap:
         oldest = map.keys().next().value  ← O(1) first key
         map.delete(oldest)
   
   All ops O(1) because:
     Map.set / delete: O(1) hash + linked-list bookkeeping.
     map.keys().next(): O(1) — iterator starts at head.

   Compare to "vanilla" hash + doubly-linked list:
     Same asymptotics; Map already does both internally.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why use `delete + set` instead of just `set`?
> 2. How is `map.keys().next().value` O(1)?
> 3. Does `get` modify recency?

---

## 6. Brute force — walked through

```js
class NaiveLRU {
  constructor(cap) { this.cap = cap; this.data = {}; this.order = []; }
  get(k) {
    if (!(k in this.data)) return -1;
    this.order = this.order.filter(x => x !== k);   // O(n)
    this.order.push(k);
    return this.data[k];
  }
}
```

O(n) per get/put. Use Map.

---

## 7. The unlocking insight

> **Map's insertion-order property + delete-then-set bump = O(1) LRU in ~20 lines.**

Three properties:

1. **Map insertion order** = recency.
2. **`delete + set`** bumps to end.
3. **`keys().next().value`** = oldest, O(1).

---

## 8. Solution (annotated)

```js
class LRUCache {
  constructor(capacity) {
    this.cap = capacity;
    this.map = new Map();
  }

  get(key) {
    if (!this.map.has(key)) return -1;                                    // step 1: miss
    const val = this.map.get(key);
    this.map.delete(key);                                                  // step 2: remove
    this.map.set(key, val);                                                // step 3: re-insert at end
    return val;
  }

  put(key, value) {
    if (this.map.has(key)) {
      this.map.delete(key);                                                // step 4: dedup for bump
    }
    this.map.set(key, value);
    if (this.map.size > this.cap) {
      const oldest = this.map.keys().next().value;                         // step 5: O(1) head
      this.map.delete(oldest);                                             // step 6: evict
    }
  }
}
```

**Try it yourself**

```js
const c = new LRUCache(3);
c.put(1, 'a');                                                // Map: {1:a}
c.put(2, 'b');                                                // {1:a, 2:b}
c.put(3, 'c');                                                // {1:a, 2:b, 3:c}
c.get(1);                                                      // 'a'; Map: {2:b, 3:c, 1:a}
c.put(4, 'd');                                                // Evicts 2: {3:c, 1:a, 4:d}
c.get(2);                                                      // -1
c.get(3);                                                      // 'c'; Map: {1:a, 4:d, 3:c}

// Variants — with TTL
class TTLLRU {
  constructor(cap, ttlMs) {
    this.cap = cap;
    this.ttl = ttlMs;
    this.map = new Map();
  }
  get(k) {
    if (!this.map.has(k)) return undefined;
    const { value, exp } = this.map.get(k);
    if (exp < Date.now()) { this.map.delete(k); return undefined; }
    this.map.delete(k);
    this.map.set(k, { value, exp });
    return value;
  }
  put(k, v) {
    if (this.map.has(k)) this.map.delete(k);
    this.map.set(k, { value: v, exp: Date.now() + this.ttl });
    if (this.map.size > this.cap) {
      this.map.delete(this.map.keys().next().value);
    }
  }
}

// LFU variant requires frequency tracking — different problem.
```

---

## 9. Step-by-step dry run

```
new LRUCache(2).
put(1, 'a'):
  has? No. set(1, 'a'). Map: {1:a}.
  size 1 ≤ 2 — no evict.

put(2, 'b'):
  has? No. set(2, 'b'). Map: {1:a, 2:b}.

get(1):
  has? Yes. val='a'. delete(1). Map: {2:b}.
  set(1, 'a'). Map: {2:b, 1:a}.   ← 1 is now most recent.
  Return 'a'.

put(3, 'c'):
  has? No. set(3, 'c'). Map: {2:b, 1:a, 3:c}.
  size 3 > 2 → evict oldest.
  keys().next().value = 2 (front of insertion order).
  delete(2). Map: {1:a, 3:c}.

get(2):
  has? No. Return -1.

get(3):
  has? Yes. val='c'. delete(3). Map: {1:a}.
  set(3, 'c'). Map: {1:a, 3:c}.   ← 3 now most recent.
  Return 'c'.
```

---

## 10. Common confusion + traps

1. **Just `set` without `delete` first** — Map doesn't bump existing entries on re-set; insertion position unchanged.
2. **`Array.from(map.keys())[0]`** — O(n); use `keys().next().value`.
3. **No touch on read** — get must bump recency.
4. **Capacity off-by-one** — evict when size > cap (not >=).
5. **Eviction during put with same key** — delete-first or check `has` before set.
6. **Async race** — not thread-safe in concurrent contexts.
7. **TTL combined with LRU** — check expiry; delete if stale.

---

## 11. Senior follow-ups & variants

### Variant 1 — TTL + LRU
Combine eviction policies; expire on read.

### Variant 2 — LFU (frequency-based)
Track count; evict least-frequent. More complex.

### Variant 3 — Multi-tier (L1 + L2)
Hot in-memory + cold disk/network.

### Variant 4 — Bounded by memory bytes (not count)
Estimate size per entry.

### Variant 5 — Concurrent (`AsyncMutex`)
Wrap put/evict in mutex for async-safe.

---

## 12. How to think aloud

> "LRU cache: O(1) get and put, capacity-bounded, evicts least-recently-used. JS shortcut: `Map` preserves insertion order; that's our recency list. `get(k)`: if present, `delete(k); set(k, val)` re-inserts at the end (most recent); return value. `put(k, v)`: if present, delete first (so set re-inserts at end); set; if size > cap, evict `map.keys().next().value` (the front of insertion order — O(1) iterator). All ops O(1) because Map internally is hash + linked list with O(1) reorder. Don't use `Array.from(map.keys())[0]` — that's O(n). Must touch on read (get bumps recency). Variants: TTL + LRU (check expiry in get/put); LFU (frequency-based — different problem); multi-tier (L1 in-memory + L2 disk); memory-bounded (estimate bytes per entry); concurrent (async mutex). Trap: re-set without delete (doesn't bump); off-by-one cap check; not bumping on read."

---

## 13. 60-second revision

> - **`Map` insertion order = recency.**
> - **`delete + set`** bumps to end.
> - **`keys().next().value`** = oldest, O(1).
> - **All ops O(1).**
> - **Touch on read** — get bumps recency.
> - **Evict when `size > cap`** (after insert).
> - **TTL variant** — check expiry.
> - **LFU is different** — frequency-based.
> - **Trap:** re-set without delete; `Array.from` for first; no read bump.

---

**Related:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [ttl-map.md](./ttl-map.md) · [cache-invalidate-by-tag.md](./cache-invalidate-by-tag.md) · [`10-machine-coding-patterns/memoize.md`](../10-machine-coding-patterns/memoize.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
