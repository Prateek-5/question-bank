# Sort by multiple keys (asc/desc mix)

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [stable-sort-discussion.md](./stable-sort-discussion.md)
>
> **Source:** BFE.dev #168. Lodash `_.orderBy`. #1 backend array question after polyfills.

---

## 1. Problem statement

Sort an array of objects by multiple keys with per-key asc/desc direction.

**Verification examples**

```js
const users = [
  { name: 'Alice', age: 30, role: 'admin' },
  { name: 'Bob',   age: 25, role: 'user' },
  { name: 'Alice', age: 25, role: 'user' },
];

sortBy(users, [
  { key: 'name', dir: 'asc' },
  { key: 'age',  dir: 'desc' },
]);
// → Alice/30, Alice/25, Bob/25
```

**Constraints**
- Composed comparator across multiple keys.
- Per-key direction (asc/desc).
- Type-aware comparison: strings via localeCompare, numbers via subtract, dates via valueOf.
- Stable sort (ES2019+).
- Comparator returns number (not boolean).

---

## 2. Plain-English restatement

For each pair (a, b), compare by first key; if equal, by next key; etc. Reverse sign for desc keys. Use type-aware compare per field.

---

## 3. Why this matters in interviews

Multi-key sort is **the** backend array question. Every dashboard/report/table needs it. Tests comparator factory, ES2019 stability, mixed asc/desc, type-aware compare.

---

## 4. Mental model

```
   Comparator factory:
     sortBy(arr, keys):
       arr.sort((a, b) => {
         for {key, dir} of keys:
           cmp = compare(a[key], b[key])
           if cmp !== 0:
             return dir === 'desc' ? -cmp : cmp
         return 0
       })
   
   compare(x, y):
     if both numbers: x - y
     if both strings: x.localeCompare(y)   ← honors locale, casing
     if both dates:   x.valueOf() - y.valueOf()
     if null/undef:   policy (last? throw?)
     else:            mixed — coerce or throw.
   
   Sort returns number:
     <0: a before b
     >0: b before a
     0:  equal — stable sort preserves input order.
   
   ES2019+: Array.prototype.sort guaranteed stable (V8 TimSort).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why return number, not boolean?
> 2. Why ES2019 stability matters?
> 3. How to do natural numeric string sort `'10'` > `'2'`?

---

## 6. Brute force — walked through

```js
arr.sort((a, b) => a.name - b.name);     // BUG: strings subtracted = NaN
```

```js
arr.sort((a, b) => a.name > b.name);     // BUG: returns boolean → 1/0
```

Both wrong.

---

## 7. The unlocking insight

> **Composed comparator iterates keys; first non-zero wins. Type-aware base compare. Multiply by -1 for desc.**

Three properties:

1. **Composed comparator** — return on first non-zero.
2. **Type-aware compare** — strings/numbers/dates differ.
3. **Direction flip** — `-cmp` for desc.

---

## 8. Solution (annotated)

```js
function sortBy(arr, keys) {
  return [...arr].sort((a, b) => {                                        // step 1: clone (non-mutating)
    for (const { key, dir = 'asc' } of keys) {
      const cmp = compare(a[key], b[key]);                                 // step 2: per-key
      if (cmp !== 0) {
        return dir === 'desc' ? -cmp : cmp;                                // step 3: direction
      }
    }
    return 0;                                                              // step 4: all equal → stable
  });
}

function compare(x, y) {
  if (x === y) return 0;
  if (x == null) return y == null ? 0 : 1;                                 // step 5: nulls last
  if (y == null) return -1;
  if (typeof x === 'number' && typeof y === 'number') {
    return x - y;                                                          // step 6: numbers
  }
  if (typeof x === 'string' && typeof y === 'string') {
    return x.localeCompare(y, undefined, { numeric: true });               // step 7: natural string sort
  }
  if (x instanceof Date && y instanceof Date) {
    return x.valueOf() - y.valueOf();                                      // step 8: dates
  }
  return String(x).localeCompare(String(y));                                // step 9: fallback
}
```

**Try it yourself**

```js
const users = [
  { name: 'Alice', age: 30 }, { name: 'Bob', age: 25 }, { name: 'Alice', age: 25 },
];

sortBy(users, [{ key: 'name' }, { key: 'age', dir: 'desc' }]);
// Alice/30, Alice/25, Bob/25

sortBy(users, [{ key: 'age', dir: 'desc' }]);
// Bob first? No — desc age: 30 first.
// Result: Alice/30, Bob/25, Alice/25 (stable on ties).

// Natural numeric string sort
['file10', 'file2', 'file1'].sort((a, b) => a.localeCompare(b, undefined, {numeric: true}));
// ['file1', 'file2', 'file10']

// Schwartzian transform — pre-compute heavy keys
function sortBySchwartzian(arr, keyFn) {
  return arr
    .map((item, i) => ({ item, key: keyFn(item), i }))                   // O(n) compute
    .sort((a, b) => a.key - b.key || a.i - b.i)                          // O(n log n) cheap compare
    .map(x => x.item);
}

// ES2023 non-mutating
const sorted = arr.toSorted((a, b) => a.name.localeCompare(b.name));
```

---

## 9. Step-by-step dry run

```
sortBy(users, [{key:'name'}, {key:'age', dir:'desc'}]):
  Users: Alice/30, Bob/25, Alice/25.
  
  Pair Alice/30 vs Bob/25:
    name: 'Alice'.localeCompare('Bob') → negative. Return cmp. 
    Alice before Bob.
  
  Pair Alice/30 vs Alice/25:
    name: 0 (equal).
    age: 30 vs 25 → 5. dir='desc' → -5. 
    -5 → Alice/30 before Alice/25.
  
  Final: [Alice/30, Alice/25, Bob/25].

Stable sort:
  Two items equal on all keys → input order preserved.
  ES2019+ guarantees this.

Without composed comparator (old approach):
  Sort by minor key first, then major.
  Stability preserves minor order on major ties.
  Works post-2019; was buggy before.
```

---

## 10. Common confusion + traps

1. **`a.name - b.name`** — NaN for strings.
2. **Return boolean** — coerces to 1/0; broken.
3. **`<` operator** — works for same type only; mixed → coerce.
4. **`'10' < '2'`** — true lexicographically; use `{numeric: true}`.
5. **Casing** — `'A' < 'b'` by codepoint; localeCompare handles.
6. **Null/undefined** — policy unspecified; document.
7. **Mutates input** — `sort` mutates; clone first for immutable.

---

## 11. Senior follow-ups & variants

### Variant 1 — Schwartzian transform
Pre-compute keys for O(n) + sort on cheap keys.

### Variant 2 — `Intl.Collator`
Locale-aware compare; reuse instance for performance.

### Variant 3 — `toSorted` (ES2023)
Non-mutating sort.

### Variant 4 — Custom direction sentinel
`{ key: 'date', dir: 1 }` (1 asc, -1 desc) — saves multiplication.

### Variant 5 — Lodash `_.orderBy(arr, keys, dirs)`
Separate arrays for keys and directions.

---

## 12. How to think aloud

> "Multi-key sort: composed comparator iterates key descriptors; first non-zero cmp wins. Per-key compare must be type-aware: numbers via subtraction (`x - y`), strings via `localeCompare(y, undefined, {numeric: true})` for natural ordering (`'file2'` before `'file10'`), dates via `valueOf()` subtraction. For desc: multiply cmp by -1. Comparator MUST return a number — returning boolean coerces to 1/0 and breaks sort. ES2019+ `Array.prototype.sort` is stable (V8 TimSort, SpiderMonkey/JSC mergesort), so equal-keyed items preserve input order; before 2019, multi-key sort needed original-index tiebreakers. For non-mutation: `[...arr].sort(...)` or ES2023 `arr.toSorted(...)`. For heavy keys (expensive computation): Schwartzian transform — `arr.map(item => ({item, key: keyFn(item)})).sort(byKey).map(x => x.item)` — pays O(n) compute instead of O(n log n). Trap: `a.name - b.name` (NaN); boolean return; `<` on mixed types; lexicographic numeric strings; mutating original."

---

## 13. 60-second revision

> - **Composed comparator** — first non-zero wins.
> - **Return number** (not boolean).
> - **Type-aware compare:** numbers subtract, strings `localeCompare`, dates `valueOf`.
> - **Desc:** `-cmp`.
> - **ES2019+ stable** — multi-key works naturally.
> - **`toSorted` (ES2023)** for non-mutation.
> - **Schwartzian** for heavy keys.
> - **`{numeric: true}`** for natural string sort.
> - **Trap:** subtract strings (NaN); boolean return; lex numeric.

---

**Related:** [stable-sort-discussion.md](./stable-sort-discussion.md) · [polyfill-reduce.md](./polyfill-reduce.md) · [structured-clone-vs-spread.md](./structured-clone-vs-spread.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
