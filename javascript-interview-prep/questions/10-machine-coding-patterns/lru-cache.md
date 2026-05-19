# Implement an LRU Cache

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md), [memoize.md](./memoize.md)
>
> **Source:** [LeetCode 146 — LRU Cache](https://leetcode.com/problems/lru-cache/). The single most-asked data-structure design problem in tech interviews.

---

## 1. Problem statement

**Signature**
```ts
class LRUCache {
  constructor(capacity: number);
  get(key: any): any | -1;
  put(key: any, value: any): void;
}
```

**Input / Output examples**

| Setup (capacity 2)            | Map state (oldest → newest)   | Result      |
|-------------------------------|-------------------------------|-------------|
| `put(1, 'A')`                 | `[1→A]`                       |             |
| `put(2, 'B')`                 | `[1→A, 2→B]`                  |             |
| `get(1)`                      | `[2→B, 1→A]` (bumped)         | `'A'`       |
| `put(3, 'C')`                 | `[1→A, 3→C]` (evict 2)        |             |
| `get(2)`                      | unchanged                     | `-1`        |
| `put(4, 'D')`                 | `[3→C, 4→D]` (evict 1)        |             |
| `get(1)`                      | unchanged                     | `-1`        |

**Constraints**
- O(1) `get` and `put`.
- LRU eviction = evict the least recently used key when over capacity.
- `get` and `put` on existing key both bump to MRU.
- Return `-1` on missing key (LeetCode convention).

---

## 2. Plain-English restatement

A bounded cache where the oldest-untouched entry gets evicted when you exceed capacity. "Touched" = inserted, updated, or read. Every operation must be O(1). In JS the idiomatic trick is to use a `Map` (which preserves insertion order) and **delete-then-reinsert** to bump an entry to the most-recent end.

---

## 3. Why this matters in interviews

LRU is the **#1 data-structure design problem in tech interviews**, period. Shows up in coding rounds, low-level design, and system design (as a building block of CDN caches, Redis `allkeys-lru`, MySQL buffer pool). In JS the **Map + delete+reinsert** shortcut is what senior interviewers expect; mention the HashMap+DLL approach (language-agnostic) for completeness.

---

## 4. Mental model

```
   Map iteration order = insertion order
   ┌─── LRU end (oldest) ────────── MRU end (newest) ───┐
   │  key1   key2   key3   key4   key5                  │
   └────────────────────────────────────────────────────┘
       ↑ next eviction target                ↑ just touched

   get(key3):
     read value
     delete key3
     re-set key3 with same value   ← now at MRU end
   ┌─── LRU end ──────────────── MRU end ───────────────┐
   │  key1   key2   key4   key5   key3                  │
   └────────────────────────────────────────────────────┘

   put(newKey, v) when at capacity:
     evict map.keys().next().value  (the oldest)
     set newKey, v                  (lands at MRU)
```

**Language-agnostic equivalent:** HashMap + Doubly Linked List with sentinel head (MRU) and tail (LRU).

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `put(1,A); put(2,B); get(1); put(3,C)` with capacity=2, which key gets evicted — 1 or 2? Why?
> 2. Why is `map.keys().next().value` an O(1) way to find the LRU?
> 3. What happens in `put(key, value)` if the key already exists in the cache?

---

## 6. Brute force — walked through

### Wrong attempt 1: plain object + timestamps
```js
{ key: { value, ts: Date.now() } }
// eviction scans all entries to find min ts → O(N) per put
```
Acceptable as the brute force; immediately upgrade to O(1).

### Wrong attempt 2: forget to bump on `get`
```js
get(key) { return this.map.get(key) ?? -1; }   // no bump
```
Degrades to **FIFO**, not LRU. Frequently-read entries get evicted because they look old.

### Wrong attempt 3: evict AFTER inserting
```js
this.map.set(key, value);
if (this.map.size > capacity) evict();
```
Works (briefly over capacity) but mixes concerns. Idiomatic: check **before**: `size >= capacity` → evict, then set.

---

## 7. The unlocking insight

> **`Map` preserves insertion order. Delete-then-reinsert on access bumps an entry to the MRU end. `map.keys().next().value` is the LRU in O(1). All ops are one or two Map mutations.**

Three properties:

1. **Insertion-order iteration** — JS `Map` specifies it; first-inserted = LRU.
2. **Delete-then-reinsert** is the bump-to-MRU trick (O(1) both ops).
3. **`keys().next().value`** is O(1) — the iterator is lazy, doesn't scan.

---

## 8. Solution (annotated)

```js
class LRUCache {
  constructor(capacity) {
    if (capacity <= 0) throw new Error('capacity must be > 0');
    this.capacity = capacity;
    this.map = new Map();                                           // step 1: insertion-order Map
  }

  get(key) {
    if (!this.map.has(key)) return -1;                              // step 2: miss
    const value = this.map.get(key);
    this.map.delete(key);                                            // step 3: bump-to-MRU
    this.map.set(key, value);
    return value;
  }

  put(key, value) {
    if (this.map.has(key)) {
      this.map.delete(key);                                          // step 4: refresh existing
    } else if (this.map.size >= this.capacity) {
      const lruKey = this.map.keys().next().value;                  // step 5: O(1) oldest
      this.map.delete(lruKey);
    }
    this.map.set(key, value);                                        // step 6: insert at MRU end
  }
}
```

**Language-agnostic version — HashMap + Doubly Linked List:**
```js
class DLLNode {
  constructor(key, value) { this.key = key; this.value = value; this.prev = null; this.next = null; }
}

class LRUCacheDLL {
  constructor(capacity) {
    this.capacity = capacity;
    this.map = new Map();
    this.head = new DLLNode(null, null);
    this.tail = new DLLNode(null, null);
    this.head.next = this.tail; this.tail.prev = this.head;
  }
  _unlink(n) { n.prev.next = n.next; n.next.prev = n.prev; }
  _atHead(n) { n.next = this.head.next; n.prev = this.head; this.head.next.prev = n; this.head.next = n; }
  get(key) {
    const n = this.map.get(key); if (!n) return -1;
    this._unlink(n); this._atHead(n);
    return n.value;
  }
  put(key, value) {
    let n = this.map.get(key);
    if (n) { n.value = value; this._unlink(n); this._atHead(n); return; }
    if (this.map.size >= this.capacity) {
      const lru = this.tail.prev; this._unlink(lru); this.map.delete(lru.key);
    }
    n = new DLLNode(key, value);
    this._atHead(n); this.map.set(key, n);
  }
}
```

**Try it yourself**

```js
const c = new LRUCache(2);
c.put(1, 'A');           // [1→A]
c.put(2, 'B');           // [1→A, 2→B]
c.get(1);                // 'A' → [2→B, 1→A]
c.put(3, 'C');           // evict 2 → [1→A, 3→C]
c.get(2);                // -1
c.put(4, 'D');           // evict 1 → [3→C, 4→D]
c.get(1);                // -1
c.get(3);                // 'C' → [4→D, 3→C]
c.get(4);                // 'D' → [3→C, 4→D]
```

---

## 9. Step-by-step dry run

```
capacity = 2

put(1, A):    size=0<2 → set. map=[1→A]
put(2, B):    size=1<2 → set. map=[1→A, 2→B]
get(1):       hit. delete 1, set 1=A. map=[2→B, 1→A]. return 'A'.
put(3, C):    size=2≥2 → evict map.keys().next().value = 2. map=[1→A]. set 3=C. map=[1→A, 3→C].
get(2):       miss. return -1.
put(4, D):    size=2≥2 → evict 1. map=[3→C]. set 4=D. map=[3→C, 4→D].
get(1):       miss. return -1.
get(3):       hit. delete 3, set 3=C. map=[4→D, 3→C]. return 'C'.
get(4):       hit. delete 4, set 4=D. map=[3→C, 4→D]. return 'D'.

Every operation: 1 hash lookup + at most 1 delete + 1 set + 1 keys().next(). All O(1).
```

---

## 10. Common confusion + traps

1. **Forget to bump on `get`** → FIFO instead of LRU.
2. **Forget to update on `put` for existing key** → wrong value AND wrong ordering.
3. **Evict AFTER inserting** (`size > capacity`) instead of before — both work but mixes concerns.
4. **Scan map to find LRU** → O(N) instead of O(1). Use `keys().next()`.
5. **Plain object as cache** — JS sorts integer-string keys numerically; insertion order breaks.
6. **Capacity 0** — every put evicts immediately. Validate `capacity > 0`.
7. **Confuse LRU with LFU** — LFU evicts by access *frequency*, not recency.

---

## 11. Senior follow-ups & variants

### Variant 1 — TTL + LRU
Each entry has `{value, expiry}`. On `get`, lazy-evict if expired (return -1, remove). Eviction policy stays LRU.

### Variant 2 — LFU cache
[LeetCode 460](https://leetcode.com/problems/lfu-cache/). Eviction by lowest access count; ties broken by LRU within count. Two HashMaps + min-frequency tracker.

### Variant 3 — Approximate LRU (Redis-style)
Pick K random keys, evict the one with the oldest access timestamp. O(1) amortized, no DLL, sacrifices precision. Good system-design talking point.

### Variant 4 — Thread-safe LRU
Lock around get/put; or shard by `hash(key) % N` for concurrency.

### Variant 5 — Byte-size LRU
Eviction triggered by total payload size, not entry count. Useful for image/response caches.

---

## 12. How to think aloud

> "JS-idiomatic: `Map` preserves insertion order. Bump-to-MRU = `delete + set`. Evict LRU = `delete(map.keys().next().value)`. Trigger eviction when `size >= capacity` BEFORE setting. O(1) everything. Language-agnostic version: HashMap + Doubly Linked List with sentinel head (MRU) and tail (LRU); `get` unlinks and re-inserts at head; `put` evicts node before tail when at capacity. Trap: forgetting to bump on `get` degrades to FIFO. Trap: plain object — integer-string keys sort numerically. Variants: TTL+LRU (lazy expire), LFU (frequency), approximate LRU (Redis random-K), byte-size LRU."

---

## 13. 60-second revision

> - **JS shortcut: `Map` + delete-and-reinsert** for MRU bump.
> - **`map.keys().next().value`** = LRU in O(1).
> - **Trigger eviction at `size >= capacity` BEFORE insert.**
> - **`get` on existing key MUST bump** (else degrades to FIFO).
> - **Language-agnostic:** HashMap + DLL with sentinel head/tail.
> - **Family:** LFU, TTL cache, approximate LRU, LRU memoize.
> - **Trap:** no bump on `get`; plain object; `keys().next()` not called.

---

**Related:** [memoize.md](./memoize.md) · [memoize-ii.md](./memoize-ii.md) · [rate-limiter-token-bucket.md](./rate-limiter-token-bucket.md) · [`02-closures/memoize-with-ttl.md`](../02-closures/memoize-with-ttl.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
