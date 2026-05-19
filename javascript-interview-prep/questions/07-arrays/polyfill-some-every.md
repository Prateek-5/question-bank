# Polyfill `Array.prototype.some` and `every`

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [polyfill-filter.md](./polyfill-filter.md), [polyfill-find-findindex.md](./polyfill-find-findindex.md)
>
> **Source:** BFE.dev, GreatFrontEnd, codedamn.

---

## 1. Problem statement

Re-implement `some` / `every` with short-circuit, hole-skipping, `thisArg`, 3-arg predicate.

**Verification examples**

```js
[1, 2, 3].mySome(x => x > 2);          // true (stops at 3)
[1, 2, 3].myEvery(x => x > 0);         // true
[].mySome(() => true);                  // false (vacuous)
[].myEvery(() => false);                // true (vacuous truth)
new Array(3).mySome(() => true);        // false (all holes)
[undefined].mySome(() => true);         // true (explicit undefined is element)
```

**Constraints**
- Short-circuit on first decisive result.
- Skip holes via `i in this`.
- 3-arg predicate + `thisArg`.
- Empty: some→false, every→true (vacuous truth).
- Boolean-coerce result.

---

## 2. Plain-English restatement

`some` returns true if ANY element passes; `every` returns true if ALL elements pass. Both short-circuit, skip holes, support `thisArg`. Empty array: `some` false, `every` true (vacuous truth).

---

## 3. Why this matters in interviews

Three quirks no one remembers: short-circuit, hole-skipping, `thisArg`. Backend candidates fumble `[,,,].some(()=>true)` (false!) and `[].every(()=>false)` (true!). Spec literacy signal.

---

## 4. Mental model

```
   some(pred, thisArg):
     for i in 0..len-1:
       if i in this:
         if Boolean(pred.call(thisArg, this[i], i, this)):
           return true                  ← short-circuit
     return false                        ← vacuous: empty → false

   every(pred, thisArg):
     for i in 0..len-1:
       if i in this:
         if !Boolean(pred.call(thisArg, this[i], i, this)):
           return false                  ← short-circuit
     return true                          ← vacuous: empty → true

   Hole semantics:
     new Array(3).some(()=>true) → false (all holes; predicate never called).
     [undefined].some(()=>true) → true (explicit undefined IS an element).
   
   Vacuous truth:
     [].some() → false (∃ over empty set = false).
     [].every() → true (∀ over empty set = true).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `[].every(() => false)` — true or false?
> 2. `new Array(3).some(() => true)` — true or false?
> 3. `[undefined].some(() => true)` — true or false?

---

## 6. Brute force — walked through

```js
arr.some = function(pred) {
  for (const v of this) if (pred(v)) return true;
  return false;
};
```

Bugs: `for..of` iterates holes as `undefined`; no index/array/thisArg; no Boolean coerce.

---

## 7. The unlocking insight

> **Loop with `i in this` to skip holes; short-circuit on decisive result; vacuous truth defaults. `pred.call(thisArg, v, i, this)`.**

Three properties:

1. **Short-circuit** on first match (some) / fail (every).
2. **Skip via `i in this`** — holes don't invoke.
3. **Vacuous truth** — empty returns `false`/`true` respectively.

---

## 8. Solution (annotated)

```js
Object.defineProperty(Array.prototype, 'mySome', {
  enumerable: false,
  value: function (callback, thisArg) {
    if (this == null) throw new TypeError('mySome on null/undefined');
    if (typeof callback !== 'function') throw new TypeError('cb not callable');

    const O = Object(this);
    const len = O.length >>> 0;
    for (let i = 0; i < len; i++) {
      if (i in O) {                                                       // step 1: skip holes
        if (callback.call(thisArg, O[i], i, O)) return true;             // step 2: short-circuit
      }
    }
    return false;                                                          // step 3: vacuous false
  },
});

Object.defineProperty(Array.prototype, 'myEvery', {
  enumerable: false,
  value: function (callback, thisArg) {
    if (this == null) throw new TypeError('myEvery on null/undefined');
    if (typeof callback !== 'function') throw new TypeError('cb not callable');

    const O = Object(this);
    const len = O.length >>> 0;
    for (let i = 0; i < len; i++) {
      if (i in O) {
        if (!callback.call(thisArg, O[i], i, O)) return false;            // step 4: short-circuit
      }
    }
    return true;                                                           // step 5: vacuous true
  },
});
```

**Try it yourself**

```js
// Normal
[1, 2, 3].mySome(x => x > 2);                                 // true
[1, 2, 3].myEvery(x => x > 0);                                // true
[1, 2, 3].myEvery(x => x > 1);                                // false

// Empty
[].mySome(() => true);                                         // false
[].myEvery(() => false);                                       // true

// Holes
new Array(3).mySome(() => true);                              // false (all holes)
[1, , 3].mySome(x => x === undefined);                        // false (hole skipped)
[undefined].mySome(() => true);                               // true

// thisArg
[1, 2, 3].mySome(function(x){ return x > this.min; }, { min: 2 });  // true

// Coerce result
[1].mySome(() => 'truthy');                                   // true (boolean coerce)
```

---

## 9. Step-by-step dry run

```
[1, 2, 3].mySome(x => x > 2):
  i=0: 1>2 false.
  i=1: 2>2 false.
  i=2: 3>2 true → return true.

[1, , 3].mySome(x => x === undefined):
  i=0: 1===undefined false.
  i=1: 1 in arr false → skip.
  i=2: 3===undefined false.
  Loop end → return false.
  
  vs naive `for..of`:
    arr[0]=1, arr[1]=undefined (hole reads as undefined), arr[2]=3.
    pred(undefined) → true → return true. WRONG.

new Array(3).mySome(()=>true):
  i=0: 0 in arr false → skip.
  i=1: 1 in arr false → skip.
  i=2: 2 in arr false → skip.
  Return false.

[].myEvery(()=>false):
  loop body never runs.
  Return true (vacuous).
```

---

## 10. Common confusion + traps

1. **`[].every(() => false)` — true** (vacuous; common surprise).
2. **`for..of` iterates holes as undefined** — breaks contract.
3. **`thisArg` ignored** — second param.
4. **Predicate result not Boolean-coerced** — `if (cb(...))` does it naturally.
5. **`new Array(3).some(()=>true)` — false** (not invoked).
6. **`[undefined].some(()=>true)` — true** (explicit undefined IS element).
7. **Mutation during iteration** — len snapshotted.

---

## 11. Senior follow-ups & variants

### Variant 1 — `includes` vs `some`
`includes` uses SameValueZero (NaN-aware); `some` uses predicate.

### Variant 2 — `none()`
Lodash; `!arr.some(pred)`.

### Variant 3 — `find` family doesn't skip holes
ES6 cleanup; different from some/every/map/filter.

### Variant 4 — Async every/some
`Promise.all(arr.map(asyncPred))` + `.every(Boolean)`.

### Variant 5 — Set/Map versions
Set/Map don't have some/every; use spread + array methods.

---

## 12. How to think aloud

> "`some` returns true if any element passes; `every` if all do — both short-circuit. Three quirks: 1) Skip holes via `i in this` — `new Array(3).some(()=>true)` is false (predicate never invoked). 2) Vacuous truth: `[].some()` false, `[].every()` true. 3) `thisArg` second param. Predicate gets `(value, index, array)`. Boolean coerce via `if (cb(...))`. Length snapshotted. Difference from `find`/`findIndex`: those don't skip holes — ES6 cleanup. `[undefined].some(()=>true)` IS true because explicit undefined is an element (it `in` the array). Trap: for..of iterates holes; `[].every()` returning false; `[undefined]` confused with hole."

---

## 13. 60-second revision

> - **Short-circuit** on decisive result.
> - **Skip holes** via `i in this`.
> - **Vacuous:** `[].some() = false`, `[].every() = true`.
> - **`thisArg`** second param.
> - **3 callback args.**
> - **`new Array(3).some(()=>true) = false`** (holes).
> - **`[undefined].some(()=>true) = true`** (element).
> - **Boolean coerce** result naturally.
> - **Trap:** for..of breaks holes; vacuous truth surprise; thisArg ignored.

---

**Related:** [polyfill-filter.md](./polyfill-filter.md) · [polyfill-find-findindex.md](./polyfill-find-findindex.md) · [polyfill-map.md](./polyfill-map.md) · [polyfill-reduce.md](./polyfill-reduce.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
