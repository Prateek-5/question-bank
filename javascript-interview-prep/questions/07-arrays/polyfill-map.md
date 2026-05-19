# Polyfill `Array.prototype.map`

> **Difficulty:** Foundation   |   **Time:** ~15 min   |   **Prereqs:** [polyfill-reduce.md](./polyfill-reduce.md), [holey-vs-packed-arrays.md](./holey-vs-packed-arrays.md)
>
> **Source:** BFE.dev #14, GreatFrontEnd, Frontend Masters. LeetCode #2635.

---

## 1. Problem statement

Re-implement `Array.prototype.map` honoring sparse-array hole preservation, `thisArg`, and the three-arg callback contract.

**Verification examples**

```js
[1, 2, 3].myMap(x => x * 2);                     // [2, 4, 6]
[1, , 3].myMap(x => x * 2);                      // [2, <1 empty>, 6]
[1, 2].myMap(function(x){ return this + x; }, 10); // [11, 12]
[].myMap(() => 1);                                // []
```

**Constraints**
- Three-arg callback: `(value, index, array)`.
- `thisArg` is second param.
- Skip holes when invoking callback (`i in this`).
- Preserve holes in output (`length` set, indices unassigned at holes).
- Non-mutating.
- Throw `TypeError` if callback not callable.

---

## 2. Plain-English restatement

Apply a function to each element, return a new array of results. Output length matches input length; sparse holes are preserved as holes (not filled with `undefined`); predicate sees `(value, index, array)`; `thisArg` binds inside callback.

---

## 3. Why this matters in interviews

If `reduce` tests folds, `map` tests the **hole-preserving contract**. `[1,,3].map(x=>x*2)` → `[2, <empty>, 6]` (not `[2, undefined, 6]`, not `[2, 6]`). The way to do this: don't assign at hole indices; set `result.length = len` at end. Naive `push(undefined)` for holes makes `1 in result` true → broken contract.

---

## 4. Mental model

```
   arr.map(cb, thisArg):
     len = ToLength(arr.length)        ← snapshot once
     result = new Array(len)            ← preallocate; index gaps = holes
     for i in 0..len-1:
       if i in this:                    ← skip holes; don't invoke callback
         result[i] = cb.call(thisArg, this[i], i, this)
     return result

   Hole semantics:
     in  = [1, , 3]                  length 3, no index 1.
     out = [2, , 6]                  length 3, no index 1 — preserved.
     1 in out  → false                ← assertion

   3 callback args:
     cb(value, index, array)          ← index lets predicates like (v,i) => v+i work.

   thisArg:
     cb.call(thisArg, ...)            ← arrows ignore (lexical this).

   Non-mutating:
     Source untouched. Fresh result.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `[1, , 3].map(x => x * 2)` — what's the result?
> 2. Does map honor `thisArg`?
> 3. What's the 3rd argument to the callback?

---

## 6. Brute force — walked through

```js
Array.prototype.myMap = function(cb) {
  const result = [];
  for (let i = 0; i < this.length; i++) {
    result.push(cb(this[i], i, this));            // wrong: invokes on holes; loses holes; ignores thisArg
  }
  return result;
};
```

Fails: holes invoked as `undefined`; output dense (loses hole shape); ignores `thisArg`.

---

## 7. The unlocking insight

> **Hole preservation is the headline. Preallocate `new Array(len)`; only assign at indices where `i in this`; final length is preserved. Use `cb.call(thisArg, …)`.**

Three properties:

1. **Preallocate result** — `new Array(len)`.
2. **Skip via `i in this`** — don't invoke on holes.
3. **Preserve length** — set or trust preallocation.

---

## 8. Solution (annotated)

```js
Object.defineProperty(Array.prototype, 'myMap', {
  enumerable: false,                                                    // step 1: don't pollute for-in
  value: function (callback, thisArg) {
    if (this == null) throw new TypeError('myMap called on null/undefined');
    if (typeof callback !== 'function') throw new TypeError('callback not callable');

    const O = Object(this);
    const len = O.length >>> 0;                                          // step 2: ToUint32 length
    const result = new Array(len);                                       // step 3: preallocate; holes initially

    for (let i = 0; i < len; i++) {
      if (i in O) {                                                       // step 4: skip holes
        result[i] = callback.call(thisArg, O[i], i, O);                  // step 5: 3 args + thisArg
      }
    }
    return result;
  },
});
```

**Try it yourself**

```js
[1, 2, 3].myMap(x => x * 2);                              // [2, 4, 6]
[1, , 3].myMap(x => x * 2);                               // [2, <empty>, 6]
1 in [1, , 3].myMap(x => x * 2);                          // false (hole preserved)

const obj = { factor: 10 };
[1, 2].myMap(function (x) { return x * this.factor; }, obj);  // [10, 20]

// Three args
['a', 'b'].myMap((v, i, arr) => `${i}:${v} of ${arr.length}`);  // ["0:a of 2", "1:b of 2"]

// Length snapshot
const a = [1, 2, 3];
a.myMap((v) => { a.push(99); return v; });                // ignores pushed during iteration
```

---

## 9. Step-by-step dry run

```
[1, , 3].myMap(x => x * 2):
  len = 3. result = [empty × 3].
  
  i=0: 0 in [1,,3] true → result[0] = (1*2) = 2. result = [2, empty, empty].
  i=1: 1 in [1,,3] false → skip. result = [2, empty, empty].
  i=2: 2 in [1,,3] true → result[2] = 6. result = [2, empty, 6].
  
  Return [2, empty, 6]. length=3. 1 in result = false.

[1, undefined, 3].myMap(x => x * 2):
  i=0: in → result[0] = 2.
  i=1: in (explicit undefined IS in) → cb(undefined) → NaN. result[1] = NaN.
  i=2: in → 6.
  Result [2, NaN, 6].

Difference: explicit undefined vs hole.

With thisArg = {f:10}, cb = function(x){return x*this.f}:
  i=0: cb.call({f:10}, 1, 0, [1,2]) → 10.
  i=1: cb.call({f:10}, 2, 1, [1,2]) → 20.
  Result [10, 20].
```

---

## 10. Common confusion + traps

1. **`push(undefined)` for holes** — breaks `i in result`.
2. **Ignore `thisArg`** — predicate sees wrong `this`.
3. **Forget 3rd arg** — predicates using `(v, i) => ...` work; using `array` breaks.
4. **Pre-loop length capture missed** — pushes during iteration cause wrong behavior.
5. **`this[i] !== undefined`** as hole check — wrong; explicit undefined IS an element.
6. **Mutate source** — `map` is non-mutating; don't modify `this`.
7. **`Object.defineProperty` not used** — prototype pollution makes `for...in` enumerate `myMap`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Hole preservation test
`1 in [1,,3].myMap(x => x*2)` must be `false`.

### Variant 2 — Array-like input
`Array.prototype.myMap.call({0:'a', 1:'b', length:2}, x => x+'!')` → `['a!', 'b!']`.

### Variant 3 — Async map
Not native; `Promise.all(arr.map(asyncFn))` or `for await` for ordered.

### Variant 4 — `Array.from(arr, mapper)`
Built-in alternative; doesn't preserve holes (creates dense).

### Variant 5 — `.flatMap(fn)`
`map` + `flat(1)` in one pass.

---

## 12. How to think aloud

> "`map` looks trivial but the hole-preserving contract is the differentiator. Output length matches input length; sparse holes preserved as holes — not filled with undefined. Three callback args `(value, index, array)`; `thisArg` second param to map. Step 1: validate `this` not null, callback callable. Step 2: snapshot length via `>>> 0` (ToUint32). Step 3: preallocate `new Array(len)` — gives us hole-shaped result. Step 4: loop `i in this` check to skip holes — `this[i] !== undefined` would skip explicit undefined too (wrong). Step 5: `callback.call(thisArg, value, i, this)` — three args + thisArg. Return result. Non-mutating; defineProperty with enumerable:false so for-in doesn't enumerate. Tests: `[1,,3].myMap(x=>x*2)` → `[2, <empty>, 6]` and `1 in result === false`. Trap: push(undefined) for holes (breaks contract); ignoring thisArg; using `arr[i] !== undefined` as hole check; forgetting length snapshot."

---

## 13. 60-second revision

> - **Output length = input length**; preserve holes.
> - **`new Array(len)`** + only assign at `i in this`.
> - **`callback.call(thisArg, value, i, this)`** — 3 args.
> - **`i in this`** to skip holes (not `!== undefined`).
> - **`length >>> 0`** for ToUint32 spec.
> - **Non-mutating.**
> - **`Object.defineProperty(..., {enumerable: false})`** to avoid for-in.
> - **Trap:** push(undefined) for holes; thisArg ignored; undefined ≠ hole.

---

**Related:** [polyfill-filter.md](./polyfill-filter.md) · [polyfill-reduce.md](./polyfill-reduce.md) · [polyfill-flat.md](./polyfill-flat.md) · [polyfill-find-findindex.md](./polyfill-find-findindex.md) · [holey-vs-packed-arrays.md](./holey-vs-packed-arrays.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
