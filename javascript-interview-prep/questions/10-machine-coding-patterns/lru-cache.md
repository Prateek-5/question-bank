# Implement an LRU Cache

## Source
- Canonical machine-coding / data-structures interview problem (LeetCode #146, BFE.dev, Frontend Masters, system-design rounds).
- LeetCode reference: https://leetcode.com/problems/lru-cache/

## Why this question matters in interviews
LRU is the **single most-asked data-structure design problem in tech interviews**, period. It shows up in coding rounds, low-level design rounds, and even system-design rounds (as a building block of CDN cache, Redis `allkeys-lru`, MySQL buffer pool). The classic answer is **HashMap + Doubly Linked List**, both O(1) — but in JavaScript there's a beautiful shortcut: `Map` preserves **insertion order**, so you can implement LRU using only a `Map` and the trick `delete + re-set` on access to bump an entry to the "most recently used" end. This shortcut is the **idiomatic JS answer** and senior interviewers expect you to know it. Mention the HashMap+DLL approach for completeness — it's what the LeetCode test cases assume in stricter language tracks (Java, C++), and it shows you understand the underlying mechanics.

## Concepts involved

### Syntax to lock in
```js
class LRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.map = new Map();
  }

  get(key) {
    if (!this.map.has(key)) return -1;
    const value = this.map.get(key);
    this.map.delete(key);
    this.map.set(key, value);   // re-insert → moves to end (most recent)
    return value;
  }

  put(key, value) {
    if (this.map.has(key)) this.map.delete(key);
    else if (this.map.size >= this.capacity) {
      // Evict oldest (first inserted) = first key in iteration order
      const oldestKey = this.map.keys().next().value;
      this.map.delete(oldestKey);
    }
    this.map.set(key, value);
  }
}
```

### Runtime / engine behavior
- `Map` in JS specifies **insertion-order iteration**. The first key inserted is the first key iterated. This is the load-bearing property for the Map-based LRU.
- `map.keys().next().value` returns the **first** (oldest) key in O(1). The iterator is lazy; `next()` doesn't scan the whole map.
- `delete + set` is the bump-to-most-recent trick. Both ops are O(1) average for `Map`. This gives O(1) get and put.
- For non-JS languages (Java, C++, Go), you need the HashMap + Doubly Linked List approach: hash → node, node has prev/next pointers, head = MRU, tail = LRU. Eviction = unlink tail.

### Edge cases (these are the interview traps)
1. **`get` on a missing key** — return `-1` (LeetCode convention) or `undefined`. Pick one and state it.
2. **`put` when key already exists** — must update value AND move to MRU. The `delete + set` handles both.
3. **`capacity = 0`** — every `put` evicts immediately. Don't crash; the implementation above handles it but you'll never have a cached entry. Worth mentioning.
4. **Eviction at exact capacity vs over capacity** — evict when `size >= capacity` BEFORE inserting. Off-by-one is a common bug.
5. **`get` after eviction** — must return `-1`. Don't reinsert evicted keys.
6. **Concurrent modification** — single-threaded JS, no issue. In multi-threaded languages, the whole cache needs a lock.
7. **Counting hits/misses** — if interviewer adds it: increment a counter in `get` based on `has(key)`.
8. **TTL combined with LRU** — common follow-up. Store `{value, expiry}` in the Map; lazy-evict on read.

## Brute force approach
Plain object + an "access timestamp" property per entry. On `get`, update timestamp. On `put` over capacity, scan all entries to find the smallest timestamp and delete. O(N) eviction. Acceptable for a brute-force pass; immediately upgrade.

## Optimal approach
**JS-idiomatic: Map with delete-and-reinsert.** O(1) everything. ~15 lines of code.

**Language-agnostic: HashMap + Doubly Linked List.**
- HashMap: `key → node`.
- DLL: each node holds `key, value, prev, next`. Maintain `head` (sentinel for MRU side) and `tail` (sentinel for LRU side).
- `get`: lookup node, unlink and reinsert at head, return value.
- `put`: if exists, update + move to head. Else create node, insert at head; if over capacity, unlink the node before `tail` and remove from map.

Worth implementing once in your prep so you can speak to it; reach for the Map version in interviews.

## Solution (JavaScript)

```js
/**
 * O(1) LRU cache using Map's insertion-order iteration.
 */
class LRUCache {
  constructor(capacity) {
    if (capacity <= 0) throw new Error('capacity must be > 0');
    this.capacity = capacity;
    this.map = new Map();
  }

  /**
   * @returns {any} value if present, else -1 (LeetCode convention).
   */
  get(key) {
    if (!this.map.has(key)) return -1;
    const value = this.map.get(key);
    // Bump to most-recently-used: delete + reinsert.
    this.map.delete(key);
    this.map.set(key, value);
    return value;
  }

  put(key, value) {
    if (this.map.has(key)) {
      // Existing key → delete so reinsert puts it at the MRU end.
      this.map.delete(key);
    } else if (this.map.size >= this.capacity) {
      // At capacity → evict LRU (oldest = first iterated).
      const lruKey = this.map.keys().next().value;
      this.map.delete(lruKey);
    }
    this.map.set(key, value);
  }

  // Optional helpers
  has(key) { return this.map.has(key); }
  get size() { return this.map.size; }
  clear() { this.map.clear(); }
}
```

For completeness, the HashMap + DLL version:

```js
class DLLNode {
  constructor(key, value) {
    this.key = key; this.value = value;
    this.prev = null; this.next = null;
  }
}

class LRUCacheDLL {
  constructor(capacity) {
    this.capacity = capacity;
    this.map = new Map();
    this.head = new DLLNode(null, null);   // sentinel MRU
    this.tail = new DLLNode(null, null);   // sentinel LRU
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  _unlink(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }

  _insertAtHead(node) {
    node.next = this.head.next;
    node.prev = this.head;
    this.head.next.prev = node;
    this.head.next = node;
  }

  get(key) {
    const node = this.map.get(key);
    if (!node) return -1;
    this._unlink(node);
    this._insertAtHead(node);
    return node.value;
  }

  put(key, value) {
    let node = this.map.get(key);
    if (node) {
      node.value = value;
      this._unlink(node);
      this._insertAtHead(node);
      return;
    }
    if (this.map.size >= this.capacity) {
      const lru = this.tail.prev;
      this._unlink(lru);
      this.map.delete(lru.key);
    }
    node = new DLLNode(key, value);
    this._insertAtHead(node);
    this.map.set(key, node);
  }
}
```

## Step-by-step dry run

Input (capacity 2):
```js
const c = new LRUCache(2);
c.put(1, 'A');
c.put(2, 'B');
c.get(1);       // returns 'A', bumps 1 to MRU
c.put(3, 'C');  // evicts 2 (LRU)
c.get(2);       // returns -1
c.put(4, 'D');  // evicts 1 (LRU after step above)
c.get(1);       // returns -1
c.get(3);       // returns 'C'
c.get(4);       // returns 'D'
```

Trace the Map state (oldest → newest):

- `put(1, 'A')`: size 0 → 1. Map: `[1→A]`.
- `put(2, 'B')`: size 1 → 2. Map: `[1→A, 2→B]`.
- `get(1)`: hit. delete 1, set 1='A' (now at end). Map: `[2→B, 1→A]`. Return `'A'`.
- `put(3, 'C')`: size = capacity → evict first key = 2. Map: `[1→A]`. Then set 3. Map: `[1→A, 3→C]`.
- `get(2)`: miss → -1.
- `put(4, 'D')`: size = capacity → evict first = 1. Map: `[3→C]`. Set 4. Map: `[3→C, 4→D]`.
- `get(1)`: miss → -1.
- `get(3)`: hit. delete 3, set 3='C'. Map: `[4→D, 3→C]`. Return `'C'`.
- `get(4)`: hit. delete 4, set 4='D'. Map: `[3→C, 4→D]`. Return `'D'`.

Every operation is O(1): single hash lookup + at most one delete + one set + one `keys().next()`.

## Important takeaways

**Syntax to memorize**
- `Map` preserves **insertion order**. First-inserted key = LRU, last-inserted = MRU.
- Bump-to-MRU: `map.delete(key); map.set(key, value);`
- Evict LRU: `map.delete(map.keys().next().value);`
- Eviction trigger: `map.size >= capacity` **before** inserting a new key.

**Patterns to reuse**
- "Insertion-order iteration as ordering" is the same trick that makes JS Sets useful for ordered de-duped queues.
- The HashMap + DLL pattern shows up in: Java's `LinkedHashMap`, Redis's LRU eviction (approximate, samples N keys), database buffer pools.
- LRU is a foundational building block for: LRU memoize, request-coalescing cache, image cache, hot-key prefetch, browser HTTP cache.

**Common mistakes**
- Forgetting to bump on `get` → degrades to FIFO, not LRU.
- Forgetting to update on `put` for existing keys → wrong value AND wrong ordering.
- Evicting after inserting (size > capacity → evict) instead of before (size >= capacity → evict, then insert) — same answer but the off-by-one bites if capacity is reduced dynamically.
- Iterating the whole Map to find the LRU → O(N) instead of O(1). Use `keys().next()`.
- Using a plain object instead of Map → no insertion-order guarantee for **integer-string** keys (those are sorted numerically in v8). Map dodges this.

**Related questions**
- **LFU cache** (Least Frequently Used) — track access frequency. More complex; usually a HashMap of HashMaps-of-DLL.
- **TTL cache** — entries expire after N ms; combine with LRU for memory-bounded TTL.
- **LRU memoize** — wrap `memoize` to drop oldest entries when bounded.
- Redis `maxmemory-policy allkeys-lru` — production LRU.

## Variants

1. **TTL + LRU** — each entry has `{value, expiry}`. On `get`, lazy-evict if expired (return -1 and remove). Eviction policy stays LRU.

2. **LFU cache** (LeetCode #460) — eviction by lowest access count; ties broken by LRU within the same count. Two HashMaps + a min-frequency tracker. Harder.

3. **Approximate LRU (Redis-style)** — pick K random keys, evict the one with the oldest access timestamp. O(1) amortized, no DLL needed, sacrifices precision. Good system-design talking point.

4. **Thread-safe LRU** — multi-language, lock around get/put. Or split into N shards keyed by `hash(key) % N` for concurrency.

5. **LRU with size limits in bytes** — eviction triggered by total payload size, not entry count. Useful for image / response caches.

## Revision notes

> **LRU cache — 60 second recap**
> - JS shortcut: `Map` + delete-and-reinsert for MRU bump. `map.keys().next().value` is the LRU.
> - O(1) get, O(1) put, O(1) eviction. ~15 lines.
> - Language-agnostic: HashMap + Doubly Linked List with sentinel head/tail.
> - **Trap:** forgetting to bump on `get` → degrades to FIFO.
> - **Trap 2:** evicting AFTER insert vs BEFORE — both work but use `size >= capacity` consistently.
> - Family: LFU, TTL cache, approximate-LRU (Redis-style), LRU memoize.
