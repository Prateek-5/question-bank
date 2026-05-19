# Polyfill `Array.prototype.find` / `findIndex`

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [polyfill-some-every.md](./polyfill-some-every.md), [polyfill-filter.md](./polyfill-filter.md)
>
> **Source:** BFE.dev #46, GreatFrontEnd, codedamn.

---

## 1. Problem statement

Re-implement `find` and `findIndex`. They are ES6+ — and crucially, **do NOT skip holes** (unlike `some`/`every`/`map`/`filter`).

**Verification examples**

```js
[1, 2, 3].myFind(x => x > 1);            // 2
[1, 2, 3].myFindIndex(x => x > 1);       // 1
[1, 2, 3].myFind(x => x > 99);           // undefined
[1, 2, 3].myFindIndex(x => x > 99);      // -1
[, , , 3].myFind(x => true);             // undefined (hole at 0 visited as undefined; passes)
                                          //   wait — predicate of `true` returns undefined.
                                          //   Actually: visits index 0, pred(undefined)→true, returns undefined.
```

**Constraints**
- 3-arg predicate `(value, index, array)`.
- `thisArg` second param.
- **NO hole-skipping** (ES6 cleanup).
- Short-circuit on first truthy.
- `find` returns element (or undefined); `findIndex` returns index (or -1).

---

## 2. Plain-English restatement

`find` returns first ELEMENT where predicate truthy; `findIndex` returns first INDEX. Both visit ALL indices including holes (where value is `undefined`). Returns `undefined`/`-1` if none found.

---

## 3. Why this matters in interviews

The "trap" question: `find` / `findIndex` look like clones of `some` but they DON'T skip holes. ES6 deliberately cleaned this up. `[,,,3].find(x=>true)` returns `undefined` (the first hole passes). Common bug.

---

## 4. Mental model

```
   find(pred, thisArg):
     for i in 0..len-1:
       v = this[i]                       ← read directly; no `i in this`
       if Boolean(pred.call(thisArg, v, i, this)):
         return v                         ← short-circuit
     return undefined

   findIndex same but returns i (or -1).
   
   Key difference vs some/every/map/filter:
     find/findIndex visit ALL indices.
     Holes read as undefined and pred IS called.
   
   ES2023: findLast / findLastIndex — same semantics, reverse iter.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `[,,,3].find(x => true)` returns what?
> 2. Can `find` distinguish "found undefined" from "not found"?
> 3. Does `find` skip holes like `some` does?

---

## 6. Brute force — walked through

```js
arr.find = function(pred) {
  for (let i = 0; i < this.length; i++) {
    if (i in this && pred(this[i])) return this[i];   // BUG: skips holes — wrong spec
  }
  return undefined;
};
```

The bug: ES6 `find` does NOT skip holes. Use the index without `in` check.

---

## 7. The unlocking insight

> **Visit ALL indices (no hole-skipping). Read `this[i]` directly; predicate sees `undefined` at holes. Short-circuit on truthy.**

Three properties:

1. **No hole-skipping** — visit every index.
2. **Short-circuit** on first truthy.
3. **Default returns** — `undefined` for find, `-1` for findIndex.

---

## 8. Solution (annotated)

```js
Object.defineProperty(Array.prototype, 'myFind', {
  enumerable: false,
  value: function (callback, thisArg) {
    if (this == null) throw new TypeError('myFind on null/undefined');
    if (typeof callback !== 'function') throw new TypeError('cb not callable');

    const O = Object(this);
    const len = O.length >>> 0;
    for (let i = 0; i < len; i++) {
      const v = O[i];                                                    // step 1: read (NO `i in O` check)
      if (callback.call(thisArg, v, i, O)) return v;                     // step 2: short-circuit element
    }
    return undefined;                                                     // step 3: default
  },
});

Object.defineProperty(Array.prototype, 'myFindIndex', {
  enumerable: false,
  value: function (callback, thisArg) {
    if (this == null) throw new TypeError('myFindIndex on null/undefined');
    if (typeof callback !== 'function') throw new TypeError('cb not callable');

    const O = Object(this);
    const len = O.length >>> 0;
    for (let i = 0; i < len; i++) {
      if (callback.call(thisArg, O[i], i, O)) return i;                  // step 4: short-circuit index
    }
    return -1;                                                            // step 5: default
  },
});

// ES2023: findLast / findLastIndex
Object.defineProperty(Array.prototype, 'myFindLast', {
  enumerable: false,
  value: function (callback, thisArg) {
    const O = Object(this);
    const len = O.length >>> 0;
    for (let i = len - 1; i >= 0; i--) {                                 // reverse iteration
      const v = O[i];
      if (callback.call(thisArg, v, i, O)) return v;
    }
    return undefined;
  },
});
```

**Try it yourself**

```js
// Standard
[1, 2, 3].myFind(x => x > 1);                                // 2
[1, 2, 3].myFindIndex(x => x > 1);                           // 1
[].myFind(() => true);                                        // undefined
[].myFindIndex(() => true);                                   // -1

// Hole behavior — KEY DIFFERENCE FROM some/filter
[,,,3].myFind(x => true);                                     // undefined (visits i=0, val=undefined)
[,,,3].myFindIndex(x => x === 3);                             // 3 (visits all, finds 3)

// Distinguish "found undefined" from "not found"
const arr = [1, undefined, 3];
arr.myFind(x => x === undefined);                             // undefined (same as not found!)
arr.myFindIndex(x => x === undefined);                        // 1 (clear distinction)

// thisArg
users.myFind(function(u){ return u.id === this.id; }, { id: 42 });

// findLast (ES2023)
[1, 2, 3, 4].myFindLast(x => x % 2 === 0);                    // 4
```

---

## 9. Step-by-step dry run

```
[,,,3].myFind(x => true):
  len = 4.
  i=0: v = this[0] = undefined (hole reads as undefined).
       pred(undefined, 0, arr) = true → return undefined.
  
  WAIT — this returns undefined but match WAS at index 0.
  This is the canonical trap: find returning undefined is AMBIGUOUS
  (could be "found undefined" or "not found").

[,,,3].myFindIndex(x => x === 3):
  i=0: 3 === undefined false.
  i=1: undefined !== 3.
  i=2: undefined !== 3.
  i=3: 3 === 3 → return 3.

[1, undefined, 3].myFindIndex(x => x === undefined):
  i=0: 1 === undefined false.
  i=1: undefined === undefined → return 1.

Compare to some/every:
  [,,,3].some(x => true) → false (holes skipped).
  vs find which returns undefined (visit hole as undefined, pass true).
  Different semantics by design.
```

---

## 10. Common confusion + traps

1. **Skip holes like `some`** — wrong; `find` visits all.
2. **`find` returns undefined ambiguity** — use `findIndex !== -1` for existence.
3. **`thisArg` ignored** — second param.
4. **Predicate signature missed** — 3 args.
5. **`findLast` reverse** but same hole behavior.
6. **`indexOf` uses `===` not predicate** — find is predicate-based.
7. **Empty array** — `[].find()` → undefined; `[].findIndex()` → -1.

---

## 11. Senior follow-ups & variants

### Variant 1 — `findLast` / `findLastIndex`
ES2023; iterate reverse.

### Variant 2 — `indexOf` vs `findIndex`
indexOf: SameValueZero comparison (no NaN). findIndex: predicate (handles NaN).

### Variant 3 — `find` on object
Use `Object.entries(obj).find(([k,v]) => pred(v))`.

### Variant 4 — `findFirstMatching` async
`Promise.race(arr.map(asyncPred))` — but order-aware needs `for await`.

### Variant 5 — Use findIndex over find
Distinguishes "found undefined" from "not found".

---

## 12. How to think aloud

> "`find` and `findIndex` are ES6+ and they DON'T skip holes — deliberate spec cleanup. Visit every index `0..len-1`; read `this[i]` directly without `in` check; predicate gets `(value, index, array)` where value at holes is `undefined`. Short-circuit on first truthy. `find` returns the element (or `undefined`); `findIndex` returns the index (or `-1`). `thisArg` second param. Trap: `[,,,3].find(x=>true)` returns `undefined` (visits i=0, val=undefined, pred true, returns undefined) — different from `some(()=>true)` which returns false. Ambiguity: `find` returning undefined could mean 'found undefined element' or 'not found' — use `findIndex !== -1` for existence check. ES2023 added `findLast`/`findLastIndex` (reverse). `indexOf` uses `===` (no NaN); `findIndex` uses predicate (handles NaN via `Number.isNaN`)."

---

## 13. 60-second revision

> - **No hole skipping** — visit every index (diff from some/every/map/filter).
> - **`find` returns element** or `undefined`.
> - **`findIndex` returns index** or `-1`.
> - **3 args + `thisArg`**.
> - **Short-circuit** on first truthy.
> - **`findLast` / `findLastIndex`** — ES2023, reverse.
> - **Use `findIndex` for existence** — disambiguates undefined.
> - **Trap:** skip holes (wrong); find/undefined ambiguity; indexOf vs findIndex.

---

**Related:** [polyfill-some-every.md](./polyfill-some-every.md) · [polyfill-filter.md](./polyfill-filter.md) · [polyfill-map.md](./polyfill-map.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
