# Maps, Sets, WeakMaps, WeakSets

## TL;DR
- **`Map`**: arbitrary keys (objects, primitives), preserves insertion order, O(1) avg get/set/has/delete, has `.size`.
- **`Set`**: unique values, insertion order, O(1) ops, has `.size`.
- **`WeakMap`/`WeakSet`**: keys must be objects (or symbols in ES2023); **keys are weakly held** → GC reclaims entries when the key is unreachable. No iteration, no `.size`.
- `Map` vs Object: prefer `Map` when keys aren't strings/symbols, when you need ordered iteration, frequent add/remove, or `.size`.
- Equality is **SameValueZero** for Map/Set (NaN equals NaN; +0 equals -0).

## Why backend interviewers care
- Caching, deduplication, rate-limit counters, in-memory indexes — all map/set territory.
- Choosing Map vs Object correctly affects perf and correctness (prototype pollution, key types).
- WeakMap is the canonical answer for "cache per object without leaking memory".

## Core mental model
A `Map` is conceptually a hash table with an insertion-order linked list overlay. V8 uses an open-addressed hash table; iteration walks the insertion-order list, so iteration is deterministic.

Equality semantics: **SameValueZero**. Important consequences:
- `NaN === NaN` is false, but `map.set(NaN, 1).get(NaN)` works.
- `+0` and `-0` are treated equal.
- Object keys are identity-equal — `{a:1}` is a different key from another `{a:1}`.

```js
const m = new Map();
const k = { id: 1 };
m.set(k, "v");
m.get({ id: 1 }); // undefined — different object identity
m.get(k);         // "v"
```

A `Set` is a `Map` with values only (V8 shares much of the impl).

**Weak collections** don't prevent GC. Entries vanish when the key object is collected — no callback, no notification. This is exactly what you want for per-object caches (e.g. memoizing a parser by AST node) without leaking.

```js
const cache = new WeakMap();
function parse(node) {
  if (cache.has(node)) return cache.get(node);
  const result = expensiveParse(node);
  cache.set(node, result);
  return result;
}
// When `node` goes away, cache entry vanishes — no leak.
```

WeakRefs and FinalizationRegistry exist for advanced cases (typically discouraged in app code; ok for libraries).

## Syntax cheat sheet
```js
// Map
const m = new Map();
m.set("a", 1);
m.set(2, "b");
m.set({}, "obj-key");
m.get("a");                       // 1
m.has(2);                         // true
m.delete("a");                    // true / false
m.size;                           // number
m.clear();

// Init from iterable
const m2 = new Map([["a", 1], ["b", 2]]);
const m3 = new Map(Object.entries({ a: 1, b: 2 }));

// Iteration (insertion order)
for (const [k, v] of m) {}
for (const k of m.keys()) {}
for (const v of m.values()) {}
m.forEach((v, k) => {});

// Spread
const arr = [...m];               // [[k,v],...]
const obj = Object.fromEntries(m);

// Set
const s = new Set([1, 2, 2, 3]); // {1,2,3}
s.add(4);
s.has(2);
s.delete(2);
s.size;
[...s];                           // [1,3,4]

// Set ops (ES2025 — Node 22+ has these natively)
s.union(other);
s.intersection(other);
s.difference(other);
s.symmetricDifference(other);
s.isSubsetOf(other);
s.isSupersetOf(other);
s.isDisjointFrom(other);

// Polyfills for older runtimes
const union = (a, b) => new Set([...a, ...b]);
const intersection = (a, b) => new Set([...a].filter(x => b.has(x)));
const difference = (a, b) => new Set([...a].filter(x => !b.has(x)));

// WeakMap (object keys only, no iteration)
const wm = new WeakMap();
wm.set(obj, "data");
wm.get(obj);
wm.has(obj);
wm.delete(obj);
// NO .size, NO .keys(), NO iteration

// WeakSet — similar
const ws = new WeakSet();
ws.add(obj);
ws.has(obj);

// Map vs Object
const o = Object.create(null);   // no prototype — safer dict
o["__proto__"];                  // undefined, not Object.prototype

// Map.groupBy / Object.groupBy (ES2024)
Object.groupBy(items, x => x.category);
Map.groupBy(items, x => x.obj);  // when keys are objects
```

## Edge cases & interview traps
1. **`Object` keys are stringified** — `obj[1]` and `obj["1"]` are the same key; `Map` keeps them distinct.
2. **`map.set(NaN, 1).get(NaN)` works** — SameValueZero.
3. **`Map` preserves insertion order**; modern Objects do too for string keys, but integer-string keys (`"1"`, `"2"`) are sorted numerically first — gotcha.
4. **`Object` has prototype keys** (`toString`, etc.) — `Object.create(null)` avoids them.
5. **`Map` size is `.size`** (property), `Array.length`, but `Object` has no built-in size.
6. **JSON.stringify(map) → "{}"** — Map isn't JSON-serializable directly; convert via `Object.fromEntries`.
7. **`new Set([1, "1"])` keeps both** — strict equality.
8. **Mutating a key object after insertion doesn't change its hash** — Map uses identity, not content.
9. **Memory: Map has higher per-entry overhead** than a plain object — but better at growing/shrinking.
10. **Iterating + mutating Map is mostly safe** in spec, but unspecified for entries added during iteration of the same Map.
11. **WeakMap entries can disappear at ANY GC** — never check `.has` then `.get` in two steps; do it in one.
12. **WeakRef.deref() may return undefined** at any time post-GC.
13. **FinalizationRegistry callbacks are not guaranteed** to run, ever.
14. **`Set` for dedup of objects only dedups by identity**, not by content. For content dedup, use a `Map` keyed by serialized form, or a hash function.
15. **Use Map for caches with non-string keys**, Object for static-key bags / known schemas.
16. **Prototype pollution**: `obj[userInput] = val` with `__proto__` is dangerous; Map is immune.
    ```js
    const o = {};
    o["__proto__"] = { polluted: true };
    ({}).polluted; // true — every object now has it (in some merge scenarios)

    const m = new Map();
    m.set("__proto__", { polluted: true }); // safe; no prototype effect
    ```

## Interview worked examples

### Example 1 — Two-Sum with a Map
**Asked as:** "Given an array of integers and a target, return indices of two numbers that add up to it."

I'd say: "Brute force is O(n²). Better: one pass with a Map of `value → index`. For each element, check if `target - current` is in the map; if yes, return the pair. O(n) time, O(n) space."

```js
function twoSum(nums, target) {
  const seen = new Map();
  for (let i = 0; i < nums.length; i++) {
    const complement = target - nums[i];
    if (seen.has(complement)) return [seen.get(complement), i];
    seen.set(nums[i], i);
  }
  return null;
}
twoSum([2, 7, 11, 15], 9); // [0, 1]
```

**What the interviewer is testing:** Hash-map lookup pattern; trading space for time.
**Sharp follow-up they often ask:** "What if duplicates exist?" → Map stores the latest index; for two-sum where both indices must differ, check `seen.has(complement)` BEFORE inserting the current.

### Example 2 — WeakMap-keyed memoization
**Asked as:** "Memoize an expensive function that takes an object argument — without leaking memory."

I'd say: "If I use a regular Map keyed by the object, that Map keeps the object alive forever — classic leak. WeakMap holds keys weakly, so when the consumer drops the object, the cache entry is auto-cleaned by GC. Only works for object keys."

```js
const cache = new WeakMap();
function expensive(obj) {
  if (cache.has(obj)) return cache.get(obj);
  const result = compute(obj);
  cache.set(obj, result);
  return result;
}
```

**What the interviewer is testing:** Knowing WeakMap exists; understanding memory implications of caches.
**Sharp follow-up they often ask:** "What if the key is a primitive (e.g., user ID)?" → WeakMap rejects primitives; fall back to a Map + LRU/TTL eviction.

### Example 3 — LRU cache using Map
**Asked as:** "Implement an LRU cache with O(1) get and put."

I'd say: "Map preserves insertion order. On `get`, I delete and re-set to bump to most-recently-used. On `set` over capacity, I evict the first key via `m.keys().next().value`. Both ops O(1) thanks to Map's hash + linked-list overlay."

```js
class LRU {
  constructor(cap) { this.cap = cap; this.m = new Map(); }
  get(k) {
    if (!this.m.has(k)) return undefined;
    const v = this.m.get(k);
    this.m.delete(k);
    this.m.set(k, v);                              // move to end (MRU)
    return v;
  }
  put(k, v) {
    if (this.m.has(k)) this.m.delete(k);
    this.m.set(k, v);
    if (this.m.size > this.cap) {
      this.m.delete(this.m.keys().next().value);   // evict LRU
    }
  }
}
```

**What the interviewer is testing:** Insertion-order semantics of Map; O(1) eviction trick.
**Sharp follow-up they often ask:** "Why is `this.m.keys().next().value` O(1)?" → Map iterators don't traverse a tree; they walk the insertion-order linked list head.

### Example 4 — Map vs Object mental model
**Asked as:** "When would you pick Map over Object?"

I'd say: "Five triggers: (1) non-string keys, (2) frequent add/delete on the hot path (Map shrinks better; Objects fragment), (3) you need `.size`, (4) you need guaranteed insertion-order iteration (Object sorts integer-string keys numerically), (5) avoiding prototype pollution from user input. Object wins for static schemas and JSON shape."

```js
// Integer-string keys: Object reorders!
const o = {};
o["2"] = "a"; o["1"] = "b"; o["foo"] = "c";
Object.keys(o); // ["1", "2", "foo"] — integers first, sorted

// Map preserves insertion order:
const m = new Map();
m.set("2", "a"); m.set("1", "b"); m.set("foo", "c");
[...m.keys()]; // ["2", "1", "foo"]
```

**What the interviewer is testing:** Engineering judgment, not memorization.
**Sharp follow-up they often ask:** "What about perf?" → Modern V8 optimizes Object for static shapes (hidden classes). Map is steadier for grow/shrink workloads. Benchmark for hot paths.

### Example 5 — Group anagrams
**Asked as:** "Group words that are anagrams of each other."

I'd say: "Use a Map keyed by the sorted-letter signature of each word. All anagrams normalize to the same key, so they end up in the same bucket. O(n · k log k) where k is max word length."

```js
function groupAnagrams(words) {
  const groups = new Map();
  for (const w of words) {
    const key = [...w].sort().join("");
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(w);
  }
  return [...groups.values()];
}
groupAnagrams(["eat","tea","tan","ate","nat","bat"]);
// [["eat","tea","ate"], ["tan","nat"], ["bat"]]
```

**What the interviewer is testing:** Hash-by-derived-key pattern.
**Sharp follow-up they often ask:** "Can you avoid the sort?" → Use a 26-char count vector as key (e.g., `"a:1,b:0,c:0,..."`) for O(k) per word.

### Example 6 — First non-repeating character
**Asked as:** "Return the index of the first character that appears exactly once."

I'd say: "Two-pass with a Map: first pass counts frequencies in insertion order; second pass iterates the Map (or original string) and returns the first count-1 entry. Map's insertion order is the key — that's why this is O(n)."

```js
function firstNonRepeating(s) {
  const count = new Map();
  for (const c of s) count.set(c, (count.get(c) ?? 0) + 1);
  for (let i = 0; i < s.length; i++) {
    if (count.get(s[i]) === 1) return i;
  }
  return -1;
}
firstNonRepeating("leetcode"); // 0  (the 'l')
firstNonRepeating("loveleetcode"); // 2  (the 'v')
```

**What the interviewer is testing:** Frequency-map pattern; using count to filter.
**Sharp follow-up they often ask:** "One-pass version?" → Track first-seen index + dedup; but two-pass with Map is cleaner and the same time complexity.

## Common machine-coding patterns
- **LRU cache (Map ordering)** — Map's insertion-order property is the trick:
  ```js
  class LRU {
    constructor(cap) { this.cap = cap; this.m = new Map(); }
    get(k) {
      if (!this.m.has(k)) return;
      const v = this.m.get(k); this.m.delete(k); this.m.set(k, v); return v;
    }
    set(k, v) {
      if (this.m.has(k)) this.m.delete(k);
      this.m.set(k, v);
      if (this.m.size > this.cap) this.m.delete(this.m.keys().next().value);
    }
  }
  ```
- **Per-object memoize (WeakMap)** — sketch above.
- **Counter / frequency map** —
  ```js
  const freq = new Map();
  for (const x of arr) freq.set(x, (freq.get(x) ?? 0) + 1);
  ```
- **Group by** —
  ```js
  Object.groupBy(arr, x => x.cat);
  // or manual:
  arr.reduce((m, x) => (m.get(x.cat) ?? m.set(x.cat, []).get(x.cat)).push(x) && m, new Map());
  ```
- **Dedup with custom key** —
  ```js
  const seen = new Set();
  arr.filter(x => !seen.has(x.id) && seen.add(x.id));
  ```
- **Two-sum (hash map)** — classic. `Map` of value → index, look up `target - current`.

## Backend-specific notes
For request-scoped caches keyed by request objects, `WeakMap` is ideal — when the request ends and its objects are released, the cache entries vanish automatically. This avoids the need for explicit cleanup hooks.

For application-level caches, prefer Map + an eviction strategy (LRU, TTL) over plain Object — easier to size-check, no prototype concerns. Battle-tested: `lru-cache`, `quick-lru`.

For high-throughput counters (rate limiters, metrics aggregation in-process), Map's O(1) ops beat repeatedly hashing strings into an Object on hot paths. Externalize to Redis if you have multiple processes.

Be careful with `Map` as cache without bounds — every set grows it. Cap with LRU or TTL.

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ MAPS / SETS — DAY-BEFORE CRAM                            │
├──────────────────────────────────────────────────────────┤
│ • Map: any-typed keys, insertion order, .size, O(1)      │
│ • Set: unique values, insertion order, .size, O(1)       │
│ • Equality: SameValueZero (NaN === NaN, +0 === -0)       │
│ • Map > Object when: non-string keys, frequent add/del   │
│ • Object.create(null) → no proto, safer dict             │
│ • JSON.stringify(Map) → '{}'; use Object.fromEntries     │
│ • WeakMap: obj keys, GC'd, no iteration, no .size        │
│ • WeakMap perfect for per-object cache                   │
│ • LRU = Map + delete oldest = m.keys().next().value      │
│ • Set ops: union/intersection/difference (ES2025)        │
│ • Object groups integer-string keys NUMERICALLY first    │
│ • Set dedups by identity for objects, not content        │
│ • freq map: m.set(x, (m.get(x) ?? 0) + 1)                │
│ • Object.groupBy / Map.groupBy (ES2024)                  │
│ • Don't unbounded-cache in Map — always evict            │
└──────────────────────────────────────────────────────────┘
```
