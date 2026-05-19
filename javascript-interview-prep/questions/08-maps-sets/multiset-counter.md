# Multiset / Counter (frequency Map)

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md)
>
> **Source:** Python `collections.Counter`. LeetCode frequency tag.

---

## 1. Problem statement

Build a Counter class on top of Map: increment, decrement (auto-remove at 0), get-with-default, topK, iteration.

**Verification examples**

```js
const c = new Counter('mississippi');
c.get('s');                              // 4
c.get('m');                              // 1
c.get('z');                              // 0
c.topK(2);                               // [['i', 4], ['s', 4]] or [['s', 4], ['i', 4]]

c.inc('a');
c.dec('s', 4);
c.has('s');                              // false (auto-removed at 0)
```

**Constraints**
- `Map.get(missing) === undefined`; use `?? 0`.
- `dec` at 0 should remove (multiset invariant).
- topK via sort entries by count.
- Iterable via `[Symbol.iterator]`.

---

## 2. Plain-English restatement

Map<key, count> with bump/dec and helpers. Initialize from iterable. Sentinel for missing = 0 (via `?? 0`).

---

## 3. Why this matters in interviews

Most-used data structure after array+hashmap. Senior bar: know the `?? 0` idiom, when to reach (anagram, top-K, distinct count, sliding window with constraints).

---

## 4. Mental model

```
   Counter = Map<key, count>
   
   inc(k, by=1):
     map.set(k, (map.get(k) ?? 0) + by)
   
   dec(k, by=1):
     next = (map.get(k) ?? 0) - by
     if next ≤ 0: map.delete(k)
     else: map.set(k, next)
   
   get(k):
     map.get(k) ?? 0   ← never undefined
   
   topK(k):
     [...map.entries()].sort((a, b) => b[1] - a[1]).slice(0, k)
     O(n log n); for very large use a min-heap (O(n log k)).
   
   Idiom:
     map.set(k, (map.get(k) || 0) + 1)  ← || treats legit 0 as missing; use ??
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why `?? 0` not `|| 0`?
> 2. Should dec at 0 delete or stay at 0?
> 3. topK with O(n log k) — how?

---

## 6. Brute force — walked through

```js
// O(n²) frequency via filter
function countOf(arr, x) { return arr.filter(v => v === x).length; }
```

Useless for top-K; O(n²) for one entry.

---

## 7. The unlocking insight

> **Map<key, count> with `?? 0` sentinel. Dec-to-0 deletes (multiset invariant). topK via sorted entries.**

Three properties:

1. **`?? 0`** for missing (not `||`).
2. **Dec-to-0 deletes** — keeps Map minimal.
3. **`[...map.entries()].sort()`** for topK.

---

## 8. Solution (annotated)

```js
class Counter {
  constructor(iterable) {
    this.map = new Map();
    if (iterable) for (const item of iterable) this.inc(item);             // step 1: init from iter
  }

  inc(k, by = 1) {
    this.map.set(k, (this.map.get(k) ?? 0) + by);                          // step 2: bump
    return this;
  }

  dec(k, by = 1) {
    const next = (this.map.get(k) ?? 0) - by;
    if (next <= 0) this.map.delete(k);                                     // step 3: auto-remove
    else this.map.set(k, next);
    return this;
  }

  get(k) { return this.map.get(k) ?? 0; }                                  // step 4: default 0
  has(k) { return this.map.has(k); }
  get size() { return this.map.size; }
  delete(k) { return this.map.delete(k); }

  topK(k) {                                                                 // step 5: sorted entries
    return [...this.map.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, k);
  }

  [Symbol.iterator]() { return this.map[Symbol.iterator](); }              // step 6: iterable

  total() {
    let t = 0;
    for (const v of this.map.values()) t += v;
    return t;
  }

  toObject() { return Object.fromEntries(this.map); }
}
```

**Try it yourself**

```js
const c = new Counter('mississippi');
c.get('s');                                                   // 4
c.get('z');                                                   // 0 (not undefined)
c.topK(2);                                                    // [['i', 4], ['s', 4]] (order tie)
c.total();                                                     // 11

// Anagram check via Counter
function isAnagram(s, t) {
  if (s.length !== t.length) return false;
  const cs = new Counter(s), ct = new Counter(t);
  for (const [k, v] of cs) if (ct.get(k) !== v) return false;
  return true;
}

// Sliding window with K distinct
function longestKDistinct(s, k) {
  const c = new Counter();
  let left = 0, best = 0;
  for (let right = 0; right < s.length; right++) {
    c.inc(s[right]);
    while (c.size > k) c.dec(s[left++]);
    best = Math.max(best, right - left + 1);
  }
  return best;
}

// Top-K with min-heap (O(n log k))
function topKHeap(counter, k) {
  // for small k, sort is fine; heap when k << n
}
```

---

## 9. Step-by-step dry run

```
new Counter('aab'):
  map = {}.
  'a': inc → map.set('a', (undefined ?? 0) + 1) = 1. map = {a:1}.
  'a': inc → 1+1 = 2. map = {a:2}.
  'b': inc → 1. map = {a:2, b:1}.

c.dec('a', 5):
  next = 2 - 5 = -3.
  -3 ≤ 0 → delete('a'). map = {b:1}.

c.dec('b'):
  next = 1 - 1 = 0.
  0 ≤ 0 → delete('b'). map = {}.

c.get('z'):
  map.get('z') = undefined. undefined ?? 0 = 0. Return 0.

|| vs ??:
  (map.get('zero') || 0) where map.get('zero') === 0:
    0 is falsy → || returns 0 (RHS). So we'd inc 0 → 1.
    Wait, but if value IS 0, it should already be deleted in this class.
    Edge case: if we don't auto-delete, |0 vs ??0 differ for legit 0 stored.

topK([['a',2],['b',1],['c',2]], 2):
  Sort by count desc: [['a',2],['c',2],['b',1]] (stable on tie).
  Slice 2: [['a',2],['c',2]].
```

---

## 10. Common confusion + traps

1. **`|| 0`** instead of `?? 0` — legit 0 treated as missing.
2. **Dec without delete** — Counter grows forever (keys with 0).
3. **topK with sort on huge** — O(n log n); use min-heap for O(n log k).
4. **`Object.entries` vs `map.entries`** — wrong for Map.
5. **`Symbol.iterator` returns map's** — caller may misuse.
6. **NaN as key** — works (Map handles); be aware.
7. **Negative counts** — multiset has no negatives; clamp/delete.

---

## 11. Senior follow-ups & variants

### Variant 1 — Min-heap topK
O(n log k) instead of O(n log n).

### Variant 2 — Bag (allow negatives)
Don't delete on 0; signed counts.

### Variant 3 — Counter union / intersection
Element-wise max / min.

### Variant 4 — Bounded counter
Cap counts; "saturate" semantics.

### Variant 5 — Counter from object
`Counter(Object.entries(obj))` if values are counts.

---

## 12. How to think aloud

> "Counter is Map<key, count> with bump/dec helpers and topK. Use `?? 0` for missing default — NOT `|| 0`, because `||` treats a legitimate `0` as missing (matters if you store legit 0s; less so in pure multiset since we delete at 0). Multiset invariant: `dec` that brings count to 0 or below deletes the key — keeps Map minimal, lets `has` work as 'present positive'. Initialize from any iterable (string, array). topK: `[...map.entries()].sort((a,b) => b[1] - a[1]).slice(0, k)` — O(n log n); for huge n with small k, use a min-heap of size k for O(n log k). Make iterable by returning the underlying map's `Symbol.iterator`. Variants: Bag (allow negatives, don't delete on 0); Counter union/intersection (element-wise max/min); bounded/saturating counter. Use cases: anagram check (`isAnagram(s, t)` compares Counters), top-K elements, sliding window 'longest with K distinct chars', stream analytics ('top hashtags last hour'). Trap: `|| 0` for legit 0; not deleting on 0 (memory grows); using Object instead of Map (numeric key coercion)."

---

## 13. 60-second revision

> - **`Map<key, count>`** with `?? 0` default.
> - **Dec → 0** deletes (multiset).
> - **`(get(k) ?? 0) + by`** for inc.
> - **`topK`** via sorted entries; heap for O(n log k).
> - **Iterable** via Map's iterator.
> - **Bag** = signed counts; don't delete.
> - **Counter union** = element-wise max.
> - **Trap:** `|| 0` vs `?? 0`; don't-delete leak; Object key coercion.

---

**Related:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [first-non-repeating-char.md](./first-non-repeating-char.md) · [group-anagrams.md](./group-anagrams.md) · [group-by.md](./group-by.md) · [`07-arrays/array-dedup.md`](../07-arrays/array-dedup.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
