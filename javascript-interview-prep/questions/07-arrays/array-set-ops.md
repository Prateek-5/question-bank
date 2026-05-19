# Array intersection / union / difference

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [array-dedup.md](./array-dedup.md), [`08-maps-sets/set-operations-polyfill.md`](../08-maps-sets/set-operations-polyfill.md)
>
> **Source:** BFE.dev #76, LeetCode #349/350. ES2025 native Set methods.

---

## 1. Problem statement

Implement `intersection`, `union`, `difference`, `symmetricDifference` on arrays. Achieve O(n+m) via Set lookup (not O(n×m)).

**Verification examples**

```js
intersection([1, 2, 3], [2, 3, 4]);           // [2, 3]
union([1, 2, 3], [2, 3, 4]);                   // [1, 2, 3, 4]
difference([1, 2, 3], [2, 3, 4]);              // [1]
symmetricDifference([1, 2, 3], [2, 3, 4]);     // [1, 4]
```

**Constraints**
- O(n+m) using Set.
- Preserve first-input order (lodash convention).
- Dedup output.
- SameValueZero (handles NaN).
- ES2025 native Set methods now available.

---

## 2. Plain-English restatement

Set operations on arrays. Convert one to Set for O(1) lookup; filter the other through it. Decide order, dedup, multiplicity policy.

---

## 3. Why this matters in interviews

"Intersection of two arrays" = SQL JOIN of JS questions. Bait: `arr1.filter(x => arr2.includes(x))` is O(n×m). Interviewer wants O(n+m) via Set. Bonus: ES2025 `Set.prototype.intersection`.

---

## 4. Mental model

```
   Set-based (O(n+m)):
     intersection(a, b) = a.filter(x => Set(b).has(x))    + dedup
     union(a, b)         = [...new Set([...a, ...b])]
     difference(a, b)    = a.filter(x => !Set(b).has(x))  + dedup
     symmetricDifference = (a\b) ∪ (b\a)
   
   ES2025 native:
     new Set(a).intersection(new Set(b))
     .union(otherSet), .difference(otherSet), .symmetricDifference(otherSet),
     .isSubsetOf(other), .isSupersetOf(other), .isDisjointFrom(other)
   
   N-way intersection (counting Map):
     For K arrays: count occurrences across DEDUPED inputs.
     Elements with count === K are in intersection.
     O(total length).

   Equality: Set uses SameValueZero — NaN handled.
   Reference equality for objects: pass keyFn.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is `filter+includes` O(n×m)?
> 2. Does intersection of `[1,1,2]` and `[1,2]` return `[1,2]` or `[1,1,2]`?
> 3. How do you intersect K arrays?

---

## 6. Brute force — walked through

```js
const intersection = (a, b) => a.filter(x => b.includes(x));  // O(n*m)
```

For 1M × 1M elements: 1e12 ops. Don't ship.

---

## 7. The unlocking insight

> **Convert one to Set for O(1) `has`; filter+dedup the other through it. ES2025 native Set methods for clean syntax.**

Three properties:

1. **Set for O(1) lookup** — O(n+m) total.
2. **Dedup output** via Set wrapping.
3. **Preserve first-input order** (lodash convention).

---

## 8. Solution (annotated)

```js
function intersection(a, b) {
  const setB = new Set(b);                                                // step 1: O(m)
  const seen = new Set();
  const out = [];
  for (const x of a) {                                                    // step 2: O(n)
    if (setB.has(x) && !seen.has(x)) {                                    // step 3: in B + dedup
      seen.add(x);
      out.push(x);
    }
  }
  return out;
}

function union(a, b) {
  return [...new Set([...a, ...b])];                                      // step 4: O(n+m)
}

function difference(a, b) {
  const setB = new Set(b);
  const seen = new Set();
  const out = [];
  for (const x of a) {
    if (!setB.has(x) && !seen.has(x)) {                                    // step 5: in A, not in B
      seen.add(x);
      out.push(x);
    }
  }
  return out;
}

function symmetricDifference(a, b) {
  return [...difference(a, b), ...difference(b, a)];                       // step 6: (a\b) ∪ (b\a)
}

// N-way intersection (counting Map)
function intersectionN(...arrays) {
  if (arrays.length === 0) return [];
  const counts = new Map();
  for (const arr of arrays) {
    const seen = new Set();
    for (const x of arr) {
      if (seen.has(x)) continue;
      seen.add(x);
      counts.set(x, (counts.get(x) || 0) + 1);
    }
  }
  return [...counts].filter(([_, c]) => c === arrays.length).map(([v]) => v);
}
```

**Try it yourself**

```js
intersection([1, 2, 3], [2, 3, 4]);                          // [2, 3]
intersection([1, 1, 2], [1, 2]);                              // [1, 2]   (dedups)
union([1, 2], [2, 3]);                                        // [1, 2, 3]
difference([1, 2, 3], [2, 3, 4]);                             // [1]
symmetricDifference([1, 2, 3], [2, 3, 4]);                    // [1, 4]

intersectionN([1, 2, 3], [2, 3, 4], [3, 4, 5]);              // [3]

// NaN handling
intersection([NaN], [NaN]);                                   // [NaN] (Set SVZ)
[NaN].filter(x => [NaN].includes(x));                         // [NaN] (includes is SVZ)
[NaN].filter(x => [NaN].indexOf(x) !== -1);                   // [] (indexOf ===)

// ES2025 native (Node 22+)
new Set([1, 2, 3]).intersection(new Set([2, 3, 4]));         // Set(2) { 2, 3 }
new Set([1, 2]).isSubsetOf(new Set([1, 2, 3]));              // true

// By key
function intersectionBy(a, b, keyFn) {
  const keysB = new Set(b.map(keyFn));
  return a.filter(x => keysB.has(keyFn(x)));
}
intersectionBy([{id:1}, {id:2}], [{id:2}, {id:3}], x => x.id);  // [{id:2}]
```

---

## 9. Step-by-step dry run

```
intersection([1,2,3], [2,3,4]):
  setB = Set{2,3,4}. seen={}. out=[].
  x=1: setB.has(1) false → skip.
  x=2: setB.has(2) true, !seen → push. out=[2]. seen={2}.
  x=3: setB.has(3) true, !seen → push. out=[2,3]. seen={2,3}.
  Return [2, 3].

intersection([1,1,2], [1,2]):
  setB = Set{1,2}. seen={}. out=[].
  x=1: in setB, !seen → push 1. seen={1}.
  x=1: in setB, but seen → skip.
  x=2: in setB, !seen → push 2.
  Return [1, 2].  (Dedups.)

intersectionN([1,2,3], [2,3,4], [3,4,5]):
  counts after dedup-per-array: 1→1, 2→2, 3→3, 4→2, 5→1.
  Filter count === 3: only 3.
  Return [3].
```

---

## 10. Common confusion + traps

1. **`filter+includes` O(n×m)** — Set it for O(n+m).
2. **`indexOf` misses NaN** — use Set or includes.
3. **Multiplicity** — dedup? SQL INTERSECT vs INTERSECT ALL. Pick + state.
4. **Order** — lodash preserves first-input order; native Set methods don't guarantee.
5. **Reference equality** — `[{a:1}]` × `[{a:1}]` = `[]`. Need keyFn.
6. **N-way** — counting Map elegant.
7. **`new Set(a).intersection(new Set(b))`** returns Set — spread back if array needed.

---

## 11. Senior follow-ups & variants

### Variant 1 — ES2025 native Set methods
Spec stable; Node 22+. Skip polyfills.

### Variant 2 — N-way ops
Counting Map for intersection across K arrays.

### Variant 3 — By key
`intersectionBy(a, b, keyFn)` for objects.

### Variant 4 — Lodash parity
Match order/dedup semantics.

### Variant 5 — Bitmask sets
For small finite domains (e.g., enum sets), use integer bitmask — O(1) ops.

---

## 12. How to think aloud

> "Array set ops have a canonical performance trap: `filter+includes` is O(n×m); convert one to Set for O(n+m). For intersection: build `Set(b)`, filter `a` through it, dedup via tracking `seen`. Preserve first-input order (lodash convention). Difference is the same with negation. Union: `[...new Set([...a, ...b])]`. Symmetric difference: `(a\b) ∪ (b\a)`. N-way intersection: counting Map — count occurrences across DEDUPED inputs; element with count === K is in intersection. ES2025 added native `Set.prototype.intersection / union / difference / symmetricDifference / isSubsetOf / isSupersetOf / isDisjointFrom` — Node 22+. NaN handled by Set's SameValueZero (and includes); indexOf misses NaN. Reference equality for objects → need `keyFn` variant. Trap: filter+includes (quadratic); indexOf NaN; multiplicity policy unspecified."

---

## 13. 60-second revision

> - **Set for O(n+m)** vs `filter+includes` O(n×m).
> - **`intersection(a, b)`** — Set(b) + filter a + dedup.
> - **`union`** — Set spread.
> - **`difference`** — Set(b) + filter !has.
> - **`symmetricDifference`** — diff both ways.
> - **N-way** — counting Map; count === K.
> - **ES2025 native Set methods** — Node 22+.
> - **NaN** SVZ-handled by Set.
> - **By key** — `keyFn` for objects.
> - **Trap:** filter+includes; multiplicity; ref equality.

---

**Related:** [array-dedup.md](./array-dedup.md) · [`08-maps-sets/set-operations-polyfill.md`](../08-maps-sets/set-operations-polyfill.md) · [`08-maps-sets/object-vs-map-vs-set.md`](../08-maps-sets/object-vs-map-vs-set.md) · [polyfill-filter.md](./polyfill-filter.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
