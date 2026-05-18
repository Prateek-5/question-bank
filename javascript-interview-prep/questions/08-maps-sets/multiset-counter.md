# Multiset / Counter (Frequency Map)

## Source / Origin
- Python's `collections.Counter`; LeetCode tag.
- Asked at: every senior interview involving frequency/anagram/top-K problems.
- Concept reference: `concepts/maps-sets.md`.

## Why this question matters in interviews
"Frequency map" is the most-used data structure in coding interviews after array and hashmap. Senior bar: you can implement it cleanly with Map, handle the increment idiom (`map.set(k, (map.get(k) ?? 0) + 1)`), and know when to reach for it (anagram check, top-K, distinct count, sliding window with constraints).

## Concepts involved

### Syntax to lock in
```js
class Counter {
  constructor(iterable) {
    this.map = new Map();
    if (iterable) for (const item of iterable) this.inc(item);
  }
  inc(k, by = 1) { this.map.set(k, (this.map.get(k) ?? 0) + by); return this; }
  dec(k, by = 1) {
    const next = (this.map.get(k) ?? 0) - by;
    if (next <= 0) this.map.delete(k);
    else this.map.set(k, next);
    return this;
  }
  get(k) { return this.map.get(k) ?? 0; }
  has(k) { return this.map.has(k); }
  get size() { return this.map.size; }
  topK(k) {
    return [...this.map.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, k);
  }
  [Symbol.iterator]() { return this.map[Symbol.iterator](); }
}
```

### Edge cases / traps
1. **`Map.prototype.get` returns `undefined` for missing.** Use `?? 0` for arithmetic.
2. **`delete` on zero/negative** — typical contract is delete-when-zero (so `size` reflects distinct keys still present).
3. **Composite keys** — Map supports object keys by identity; for content-equality, canonicalize (see `memoize-with-deep-equality.md`).
4. **Iteration order** — Map preserves insertion order; useful for stable top-K with ties.
5. **`Counter.equals(other)`** — compare maps; useful for anagram tests.
6. **Negative counts** — sometimes allowed in symmetric-diff arithmetic; usually clamp to 0.
7. **Object vs Map** — Map handles numeric keys without stringification; faster for large keysets.

## Mental Model

```
   Counter("abracadabra"):
   ┌──────────┐
   │ a → 5    │
   │ b → 2    │
   │ r → 2    │
   │ c → 1    │
   │ d → 1    │
   └──────────┘

   .inc('a')        → a → 6
   .dec('b')        → b → 1
   .dec('b')        → delete b (or keep as 0; design choice)
   .topK(2)         → [['a', 5], ['b', 2]]
```

## Why interviewers care

- **Ubiquitous primitive** — they want to see fluency.
- **Map vs Object choice** — Map for non-string keys, large keysets.
- **Idiomatic patterns** — increment-or-set, top-K, sliding-window state.

## Common confusion

- **"Use Object instead of Map."** Object keys are stringified — `obj[1]` and `obj['1']` collide. Map preserves key identity for non-string types.
- **"`map[key]++` works."** No — Map doesn't proxy bracket syntax for read/write of internal storage. Use get/set.
- **"Iterate in random order."** Map iterates in insertion order, which is deterministic.
- **"Counter is just an Object."** It's an idiom; the class wrapper provides clarity and methods.

## Brute force

```js
function counts(arr) {
  const out = {};
  for (const x of arr) out[x] = (out[x] || 0) + 1;
  return out;
}
```

Fine for string-key cases. Misses non-string keys and the `Object.prototype` collision risk.

## Optimal approach

A Counter class wrapping Map. inc/dec/get/topK. Useful internal API surface; reusable.

## Solution

```js
class Counter {
  constructor(iterable) {
    this.m = new Map();
    if (iterable) for (const x of iterable) this.inc(x);
  }
  inc(k, by = 1) { this.m.set(k, (this.m.get(k) ?? 0) + by); return this; }
  dec(k, by = 1) {
    const next = (this.m.get(k) ?? 0) - by;
    if (next <= 0) this.m.delete(k); else this.m.set(k, next);
    return this;
  }
  get(k) { return this.m.get(k) ?? 0; }
  has(k) { return this.m.has(k); }
  get size() { return this.m.size; }
  total() { let s = 0; for (const v of this.m.values()) s += v; return s; }
  topK(k) { return [...this.m.entries()].sort((a, b) => b[1] - a[1]).slice(0, k); }
  equals(other) {
    if (this.size !== other.size) return false;
    for (const [k, v] of this.m) if (other.get(k) !== v) return false;
    return true;
  }
  add(other) {
    for (const [k, v] of other.m) this.inc(k, v);
    return this;
  }
  sub(other) {
    for (const [k, v] of other.m) this.dec(k, v);
    return this;
  }
  [Symbol.iterator]() { return this.m[Symbol.iterator](); }
}

// Applications

// 1. Anagram check
function isAnagram(s, t) {
  if (s.length !== t.length) return false;
  return new Counter(s).equals(new Counter(t));
}

// 2. Group anagrams (using sorted-string key)
function groupAnagrams(strs) {
  const groups = new Map();
  for (const s of strs) {
    const key = [...s].sort().join('');
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(s);
  }
  return [...groups.values()];
}

// 3. Top-K frequent
function topKFrequent(nums, k) {
  return new Counter(nums).topK(k).map(([n]) => n);
}

// 4. Sliding window "at most K distinct" — uses Counter for the window state
function lengthOfLongestSubstringKDistinct(s, k) {
  const window = new Counter();
  let left = 0, best = 0;
  for (let right = 0; right < s.length; right++) {
    window.inc(s[right]);
    while (window.size > k) {
      window.dec(s[left]);
      left++;
    }
    best = Math.max(best, right - left + 1);
  }
  return best;
}

// 5. Check if t can be formed from s (each char in s used at most once)
function canConstruct(s, t) {
  const need = new Counter(t);
  for (const c of s) need.dec(c);
  return need.size === 0;
}
```

## Dry run

```js
const c = new Counter('aabbcc');
// inc a → a:1
// inc a → a:2
// inc b → b:1
// inc b → b:2
// inc c → c:1
// inc c → c:2
c.get('a');     // 2
c.size;         // 3
c.topK(2);      // [['a',2],['b',2]]  (or ['a','c'] depending on tie)
c.dec('a', 2);  // delete a
c.size;         // 2
```

## How to think aloud

> "Counter wraps Map with inc/dec/get/topK. `Map.get(k) ?? 0` to default missing. Delete-on-zero so size reflects distinct keys. Use Map not Object so non-string keys work and there's no `__proto__` collision. Applications: anagram via equals; top-K via sort; sliding window of distinct chars; subtract one counter from another. For composite keys (object identity vs content), canonicalize first."

## Important takeaways

- **`map.set(k, (map.get(k) ?? 0) + 1)`** is the canonical idiom.
- **Delete-on-zero** so `size` = distinct keys.
- **Map preserves insertion order**, useful for stable top-K.
- **Map > Object** for non-string keys and large keysets.
- **Common applications**: anagram, top-K, sliding window distinct, sub/superset checks.

## Variants

- **WeakMap** for object keys with GC-friendly semantics.
- **Sorted multiset** — `TreeMap`-equivalent (no built-in; use a sorted structure or BTree).
- **Counter union/intersection** — set arithmetic on counters.
- **Most/least common** — heap of size K for streaming top-K.

## Revision notes

```
Counter:
  m = new Map()
  inc(k, by=1): m.set(k, (m.get(k) ?? 0) + by)
  dec(k, by=1): next = (m.get(k) ?? 0) - by; if <= 0 delete else set
  get(k): m.get(k) ?? 0
  topK(k): sort entries desc, slice 0..k
  equals(other): same size, same counts
  add/sub(other): inc/dec per entry

USES:
  anagram check (equals)
  top-K frequent
  sliding window with "distinct count" invariant
  subset check (can s build t)
  multiset arithmetic

WHY MAP NOT OBJECT:
  non-string keys (numbers, objects, symbols)
  insertion order preserved
  no Object.prototype collision
```
