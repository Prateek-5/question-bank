# Maps, Sets, WeakMaps, WeakSets

## Intuitive primer (read this first)

Before any syntax, sit with the *purpose* of each collection — once intent clicks, the methods read themselves.

- **`Map`** = a **labeled drawer system**. Each drawer (entry) has a label of *any* type (a string, a number, an object reference, even `NaN`). You ask the drawer system "give me what's behind label `X`" and it answers in O(1). Unlike a plain Object — which is more like a folder where labels are silently coerced into strings and integer-looking labels jump to the front — a `Map` keeps your labels untouched and remembers the order you added them.
- **`Set`** = a **uniqueness gatekeeper**. Imagine a bouncer at a club door who keeps a list of who's already inside; if you try to add someone already on the list, nothing happens. That's it. No values, just membership.
- **`WeakMap`** = a **sticky note on an object**. You stuck a note on a parked car. The day the car is towed away (garbage-collected), the note goes with it. You can't enumerate sticky notes, you can't count them; you can only ask "is there a note on *this* specific car?". This is exactly why WeakMap exists: per-object metadata that *cannot leak memory*.
- **`WeakSet`** = a **silent guest list** of objects you don't want to keep alive. Used for "have I already processed this node?" checks in graph traversal where you don't want to extend the lifetime of the graph.

### Why these exist at all (first principles)

JavaScript shipped in 1995 with only Object as a key-value store. Object had three flaws that surfaced as the language grew up:
1. Keys are silently stringified — so `obj[1]` and `obj["1"]` collide.
2. Objects inherit from `Object.prototype` — so `obj.toString` exists before you set anything, and a user input of `"__proto__"` can corrupt your dictionary (prototype pollution).
3. No `.size`, no guaranteed iteration order across all key types, no clean "is this key present?" (you have to write `hasOwnProperty`).

`Map` (ES2015) was the language admitting "we need a real dictionary type." `Set` came along for free because internally a Set is just a Map with values ignored. `WeakMap`/`WeakSet` were added to solve the harder problem of *garbage-collection-friendly metadata*.

### Progression (simplest → interview-grade)
1. **Simplest:** "I have a list of name → age pairs." Either Object or Map works.
2. **Intermediate:** "Now keys can be DOM nodes / user objects, not strings." → Map is mandatory.
3. **Advanced:** "Now I want the map to *not* keep the DOM node alive after it's removed from the page." → WeakMap.
4. **Interview-grade:** "Build an LRU cache in O(1)." → Map + insertion-order trick. "Cache per request without leaks." → WeakMap.

## Mental Model

Picture a `Map` as **two data structures glued together**:

```
┌──────────────────────────────────────────────────────────┐
│  HASH TABLE (for O(1) lookup by key)                     │
│                                                          │
│   hash("a") % buckets ─► bucket #3 ─► [entry A]          │
│   hash(objRef)         ─► bucket #7 ─► [entry B] [E]     │ ← collision chain
│   hash(NaN)            ─► bucket #1 ─► [entry C]         │
│                                                          │
└──────────────────────────────────────────────────────────┘
        ▲ each entry node also lives in a linked list ▼
┌──────────────────────────────────────────────────────────┐
│  INSERTION-ORDER LINKED LIST (for deterministic iter)    │
│                                                          │
│   HEAD ─► [A] ─► [C] ─► [B] ─► [E] ─► TAIL               │
│           ▲ first inserted              ▲ last inserted  │
└──────────────────────────────────────────────────────────┘
```

When you `map.set(k, v)`: hash `k`, find bucket, append a node, AND link it to the tail of the order-list. When you `map.delete(k)`: unlink from bucket chain AND from order-list. Both O(1). When you iterate `for (const [k,v] of map)`: walk the order-list. This dual structure is why LRU implementations using Map are so clean — the linked list is *already there*, you don't have to maintain it.

### Hash collision intuition

Two different keys can hash to the same bucket. The Map stores a small chain (or open-addressing probe) inside that bucket and walks it to find the right entry by *strict identity*. You rarely need to think about this — average O(1) holds — but it explains:
- Why a malicious user dumping crafted strings into your cache could theoretically degrade you to O(n) per op (hash-flooding). V8 mitigates with randomized hash seeds per process.
- Why iteration order is *insertion* order, not hash order — the linked list overlay decouples them.

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

### What they're really testing (decoded)
- **Map vs Object choice:** can you justify a data-structure decision *for a use case*, or do you reach for `{}` reflexively? Senior engineers articulate trade-offs in seconds.
- **WeakMap awareness:** signals you've thought about memory lifecycle in long-running Node processes (the #1 cause of "our pod gets OOM-killed at 3am" tickets).
- **LRU on Map:** signals you understand that Map is *not* a hash table — it's a hash table plus an ordered linked list, and you can exploit that.

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

### Common beginner confusion: Map vs Object

This is the question interviewers love because most candidates answer poorly. Use this decision tree:

```
Are your keys ALWAYS strings/symbols, known statically (a fixed schema)?
├── YES → Object is fine. Bonus: JSON-serializable for free.
│         e.g. const user = { name, age, email };
│
└── NO → Are keys non-strings (numbers stay numbers, objects, NaN)?
         ├── YES → Map. Always.
         │
         └── NO (still strings, but dynamic) → Are keys USER-CONTROLLED?
                  ├── YES → Map (prototype-pollution safe)
                  │         or Object.create(null) (no prototype = safer).
                  │
                  └── NO → Do you need .size / frequent add+delete /
                            guaranteed insertion order across mixed key types?
                            ├── YES → Map
                            └── NO  → Object (V8 optimizes static shapes via hidden classes)
```

The mistake beginners make: they hear "Map is faster" or "Map is better" as an absolute. It isn't. Object with a fixed shape can be faster (hidden class optimization). Map wins for *dynamic, mixed-key, grow-shrink* workloads.

### Why WeakMap/WeakSet exist (the GC story)

Imagine you're writing a parser library. Users pass you AST nodes; you want to cache parsed results per node:

```js
const cache = new Map();           // ← THE LEAK
function parse(node) {
  if (cache.has(node)) return cache.get(node);
  cache.set(node, doWork(node));
  return cache.get(node);
}
```

The user finishes parsing 10,000 nodes and drops their references. The garbage collector wants to reclaim those nodes — but **your `cache` Map is still holding strong references to them**. The nodes stay alive. The 10,000 entries accumulate. Your Node process slowly bloats and eventually OOMs.

Swap `Map` for `WeakMap` and the GC is allowed to remove both the node *and* its cache entry the moment the user's reference drops. You don't have to know when — it just works. That's the entire purpose of WeakMap: **opt out of being a GC root for your keys**.

Consequences (why the API is so restricted):
- **No iteration / no `.size`** — because if you could iterate, you'd have to "know" what's still there, but entries can disappear non-deterministically.
- **Keys must be objects** (or symbols ES2023+) — primitives have no identity for GC to track.
- **No "on cleanup" callback** — GC timing is implementation-defined.

WeakSet is the same idea for "have I seen this object?" sets where you don't want to extend its life.

### Bridge: from "why" to "how"
You now know *what* each collection is and *why* it exists. The next section drills the exact methods you'll type at the keyboard. Read it as muscle-memory reference; the intuition above is what powers your interview answers, the syntax below is what powers your fingers.

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

### Bridge: from API to landmines
The methods above are the "happy path." The next section is the **trapdoor list** — subtle behaviors that show up in interviews precisely because they catch out engineers who learned Map/Set from a 5-minute YouTube video. Every trap below is a *story* about how JS evolved differently from other languages.

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

### How to think aloud while solving these
Senior candidates narrate their thought process. Each example below has an "I'd say" block — read it as the literal script you'd speak to the interviewer. The pattern is:
1. State the brute-force baseline (proves you understand the problem).
2. Name the trade you're making (usually space for time).
3. Pick a data structure and justify it in one sentence.
4. Write code.
5. State complexity.
6. Volunteer one edge case.

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

#### Mental walkthrough — twoSum([2, 7, 11, 15], 9)
```
i=0  current=2  complement=9-2=7   seen={}            7 not in seen   → seen.set(2, 0) ⇒ {2→0}
i=1  current=7  complement=9-7=2   seen={2→0}         2 IS in seen!   → return [0, 1]  ✓
```
Notice: by checking *before* inserting, we guarantee `i ≠ j`. If we inserted first, `nums = [3, 3], target = 6` would return `[1, 1]` — wrong.

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

#### Mental model — why this works
```
LRU as a desk with limited papers
─────────────────────────────────
Capacity = 3 papers on the desk.
Each time you READ a paper, you move it to the TOP of the stack (most recently used).
When you add a NEW paper and the desk is full, you toss the BOTTOM paper (least recently used).

Map's insertion-order list IS the stack. The "top" is the tail (end). The "bottom" is the head (start).
delete-then-set = "pull out and put on top".
keys().next().value = "the bottom paper" — O(1) because we walk one step of the linked list.
```

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

## Senior storytelling: how to frame "I'd use a Map here"
When an interviewer hands you any data problem, the *signal* of seniority isn't reaching for a clever data structure — it's narrating *why*. Sample scripts:

- **For caching:** "I'll use a Map, capped at N entries with LRU eviction via `keys().next().value`. If keys were objects with bounded lifetime, I'd swap to WeakMap and let GC handle eviction."
- **For dedup:** "Set if values are primitives or I dedup by reference. If I need to dedup by content, I'll project each item to a stable key (id, or stringified shape) and dedup with a Set on that projection."
- **For frequency counts:** "Map keyed by the value, count incremented with `(m.get(x) ?? 0) + 1`. I prefer Map over Object here because the keys might collide with `__proto__`/`toString` if they're user input."
- **For graph traversal:** "Visited set is a Set of node references — pure identity check. If I were worried about retaining the graph after traversal, I'd use a WeakSet."

Saying any of these gets you 80% of the data-structure question even if your code has a small bug.

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
