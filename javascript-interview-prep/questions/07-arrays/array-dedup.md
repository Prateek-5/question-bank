# Deduplicate an array — Set, Map, or filter+indexOf

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [`08-maps-sets/two-sum-map.md`](../08-maps-sets/two-sum-map.md), [`08-maps-sets/object-vs-map-vs-set.md`](../08-maps-sets/object-vs-map-vs-set.md)
>
> **Source:** BFE.dev, LeetCode #26 variant. Universal warm-up.

---

## 1. Problem statement

Remove duplicates from an array. Pick approach based on element type (primitive / object).

**Verification examples**

```js
// Primitives
[...new Set([1, 2, 2, 3, 3, 3])];                            // [1, 2, 3]

// Objects by key
const dedupByKey = (arr, key) =>
  [...new Map(arr.map(x => [key(x), x])).values()];

dedupByKey([{id:1, name:'a'}, {id:2}, {id:1, name:'b'}], u => u.id);
// [{id:1, name:'a'}, {id:2}]   ← keeps FIRST occurrence

// NaN handling — only Set handles it
new Set([NaN, NaN]).size;                                     // 1
[NaN, NaN].filter((v, i, a) => a.indexOf(v) === i);          // [] (indexOf misses NaN!)
```

**Constraints**
- O(n) time using Set/Map; O(n²) using indexOf.
- Set uses SameValueZero (NaN === NaN; +0 === -0).
- indexOf uses `===` (NaN never found).
- Preserve insertion order.

---

## 2. Plain-English restatement

Return a new array with each unique value appearing once. For primitives, use Set; for objects by some key, use Map. Watch for NaN, -0, reference equality, and order preservation.

---

## 3. Why this matters in interviews

Looks like a one-liner — that's why it's diagnostic. Senior signal: pick approach by input type, know NaN/reference traps, discuss complexity. Backend uses: dedup DB rows, idempotency keys, event batches.

---

## 4. Mental model

```
   Primitives:
     [...new Set(arr)]                  ← O(n), SameValueZero, keeps first.
   
   Objects by key:
     [...new Map(arr.map(x => [keyFn(x), x])).values()]
                                         ← Map constructor: last-write-wins!
                                         ← To keep FIRST: manual loop with !has check.
   
   Functional dedup (small arrays only):
     arr.filter((v, i, a) => a.indexOf(v) === i)   ← O(n²); misses NaN.
   
   Equality semantics:
     Set/Map use SameValueZero:
       NaN === NaN (special; unlike ===).
       +0 === -0 (special; unlike Object.is).
       Otherwise === semantics.
     
     indexOf uses ===.
     includes uses SameValueZero (handles NaN).
   
   Reference equality:
     {a:1} !== {a:1}  ← two distinct refs.
     Dedup by content: JSON.stringify key (caveat: key order, undefined, cycles).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does `[NaN, NaN].filter((v,i,a)=>a.indexOf(v)===i)` return `[]`?
> 2. Does `new Map(arr.map(x => [k(x), x]))` keep first or last?
> 3. How to dedup `[{a:1}, {a:1}]` by content?

---

## 6. Brute force — walked through

```js
// O(n²) via indexOf
arr.filter((v, i, a) => a.indexOf(v) === i);
```

Issues: O(n²); doesn't dedup NaN.

```js
// O(n²) via includes
const out = [];
for (const v of arr) if (!out.includes(v)) out.push(v);
```

includes uses SameValueZero (handles NaN) — still O(n²).

---

## 7. The unlocking insight

> **Set for primitives (O(n), SameValueZero, first-wins). Map keyed by key fn for objects. For first-wins by key, use manual loop with `if (!seen.has(k))`.**

Three properties:

1. **Set/Map = hash table O(1)** lookups.
2. **SameValueZero** — handles NaN.
3. **First-wins vs last-wins** — depends on Map constructor vs manual loop.

---

## 8. Solution (annotated)

```js
// Primitives
function dedup(arr) {
  return [...new Set(arr)];                                              // step 1: O(n), first-wins
}

// Objects by key, FIRST-wins
function dedupByKeyFirst(arr, keyFn) {
  const seen = new Map();
  for (const item of arr) {                                              // step 2: manual loop
    const k = keyFn(item);
    if (!seen.has(k)) seen.set(k, item);                                  // step 3: only set if absent
  }
  return [...seen.values()];
}

// Objects by key, LAST-wins (Map constructor idiom)
function dedupByKeyLast(arr, keyFn) {
  return [...new Map(arr.map((x) => [keyFn(x), x])).values()];           // step 4: constructor overwrites
}

// Deep dedup via stringify (caveat: key order, cycles)
function dedupDeep(arr) {
  const seen = new Set();
  const out = [];
  for (const item of arr) {
    const k = JSON.stringify(item);                                       // step 5: serialize as key
    if (!seen.has(k)) { seen.add(k); out.push(item); }
  }
  return out;
}
```

**Try it yourself**

```js
dedup([1, 2, 2, 3, 3, 3]);                                    // [1, 2, 3]
dedup([NaN, NaN, NaN]);                                       // [NaN] (Set handles NaN)
dedup([0, -0]);                                                // [0] (SameValueZero)
dedup(['1', 1]);                                               // ['1', 1] (no coercion)

const users = [{id:1, name:'a'}, {id:2}, {id:1, name:'b'}];
dedupByKeyFirst(users, u => u.id);                            // [{id:1, name:'a'}, {id:2}]
dedupByKeyLast(users, u => u.id);                             // [{id:1, name:'b'}, {id:2}]

dedupDeep([{a:1}, {a:1}, {b:2}]);                             // [{a:1}, {b:2}]

// Compose with other ops
const uniqueIds = new Set(orders.map(o => o.userId));         // dedup + project
const byCategory = new Map(products.map(p => [p.category, p])); // last-wins by category
```

---

## 9. Step-by-step dry run

```
dedup([1, 2, 2, NaN, NaN]):
  Set construction: add 1 (size 1). add 2 (size 2). add 2 (already; size 2). add NaN (size 3). add NaN (SVZ: already; size 3).
  Result: [1, 2, NaN].

vs filter+indexOf:
  [1, 2, 2, NaN, NaN].filter((v, i, a) => a.indexOf(v) === i):
    i=0, v=1: indexOf(1)=0 → keep.
    i=1, v=2: indexOf(2)=1 → keep.
    i=2, v=2: indexOf(2)=1, but i=2 → drop.
    i=3, v=NaN: indexOf(NaN)=-1, but i=3 → drop. WRONG: NaN never found.
    i=4, v=NaN: indexOf(NaN)=-1, but i=4 → drop.
  Result: [1, 2] — NaN entirely lost!

dedupByKeyFirst(users, u => u.id) where users = [{id:1,n:'a'}, {id:1,n:'b'}]:
  seen={}. 
  item={id:1,n:'a'}: k=1. !has → seen.set(1, {id:1,n:'a'}).
  item={id:1,n:'b'}: k=1. has → skip.
  values: [{id:1,n:'a'}].

dedupByKeyLast same input:
  Map constructor: [[1, {n:'a'}], [1, {n:'b'}]].
  Map sets 1→{n:'a'}, then 1→{n:'b'} (overwrites).
  values: [{id:1, n:'b'}].
```

---

## 10. Common confusion + traps

1. **`filter+indexOf` misses NaN** — indexOf uses ===.
2. **`new Map(arr.map(...))` is last-wins** — manual loop for first-wins.
3. **`{}` ≠ `{}`** — reference equality; dedup-by-content needs keyFn.
4. **JSON.stringify** — key order varies; circular refs throw; undefined dropped.
5. **+0 vs -0 conflated** — usually fine; Object.is for strict.
6. **`'1'` vs `1`** — distinct in Set (no coercion).
7. **O(n²) on huge arrays** — Set is O(n).

---

## 11. Senior follow-ups & variants

### Variant 1 — Dedup with merge
Last entry wins per key but combine fields: `{...a, ...b}`.

### Variant 2 — Dedup preserving frequency
`Map<key, count>` for histogram.

### Variant 3 — Dedup with `includes`
SameValueZero (handles NaN) but still O(n²).

### Variant 4 — Streaming dedup
For very large streams: bloom filter (approximate) or Set with eviction.

### Variant 5 — `Map.groupBy` (ES2024)
Groups by key — different from dedup.

---

## 12. How to think aloud

> "Three approaches by tradeoff: (1) `[...new Set(arr)]` for primitives — O(n), SameValueZero (handles NaN), first-occurrence-wins. (2) For objects by key, Map: `new Map(arr.map(x => [keyFn(x), x]))` — but this is LAST-wins because Map constructor overwrites; for FIRST-wins write a manual loop with `if (!seen.has(k))`. (3) `filter+indexOf` — O(n²); misses NaN entirely because indexOf uses ===. Set/Map use SameValueZero: NaN===NaN; +0===-0. Reference equality for objects: `{a:1} !== {a:1}` — two distinct refs. Deep dedup via `JSON.stringify` as key — caveat: key order, circular refs throw, undefined dropped. Order preservation: Set maintains insertion order; reflects first occurrence. Time: O(n) hash, O(n²) filter+indexOf. Trap: filter+indexOf with NaN; Map constructor last-wins surprise; JSON.stringify with cycles."

---

## 13. 60-second revision

> - **Primitives:** `[...new Set(arr)]`.
> - **By key (first-wins):** manual loop with `!seen.has(k)`.
> - **By key (last-wins):** `new Map(arr.map(...))`.
> - **Set/Map use SameValueZero** — handles NaN.
> - **`indexOf` uses ===** — misses NaN.
> - **Reference equality** for objects (need keyFn).
> - **Deep dedup:** JSON.stringify (cycles, undefined caveats).
> - **Trap:** filter+indexOf and NaN; Map constructor wins surprise.

---

**Related:** [`08-maps-sets/object-vs-map-vs-set.md`](../08-maps-sets/object-vs-map-vs-set.md) · [`08-maps-sets/group-by.md`](../08-maps-sets/group-by.md) · [`08-maps-sets/multiset-counter.md`](../08-maps-sets/multiset-counter.md) · [array-set-ops.md](./array-set-ops.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
