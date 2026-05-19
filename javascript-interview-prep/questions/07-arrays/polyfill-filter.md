# Polyfill `Array.prototype.filter`

> **Difficulty:** Foundation   |   **Time:** ~12 min   |   **Prereqs:** [polyfill-map.md](./polyfill-map.md), [holey-vs-packed-arrays.md](./holey-vs-packed-arrays.md)
>
> **Source:** BFE.dev, GreatFrontEnd. LeetCode #2634.

---

## 1. Problem statement

Re-implement `Array.prototype.filter` honoring hole-skipping, `thisArg`, three-arg callback, non-mutation.

**Verification examples**

```js
[1, 2, 3].myFilter(x => x > 1);             // [2, 3]
[1, , 3].myFilter(() => true);              // [1, 3]    ← length 2, dense
[1, 2].myFilter(function(x){ return x === this; }, 2);  // [2]
[].myFilter(() => true);                    // []
```

**Constraints**
- Predicate `(value, index, array)` → truthy/falsy.
- `thisArg` second param.
- Skip holes (`i in this`).
- Output is dense (holes NOT preserved).
- Non-mutating.

---

## 2. Plain-English restatement

Keep only the elements where predicate returns truthy. Skip holes entirely (output is dense — holes are not preserved). Three-arg callback; `thisArg` binds.

---

## 3. Why this matters in interviews

Looks trivial — "push items where predicate truthy." Trap: holes skipped, `thisArg`, three-arg callback, non-mutation. Tight 15-line polyfill separating spec-aware engineers from `for`-loop coders.

---

## 4. Mental model

```
   arr.filter(pred, thisArg):
     len = ToLength(arr.length)        ← snapshot
     result = []                        ← starts empty; push as we go
     for i in 0..len-1:
       if i in this:                    ← skip holes; predicate NOT called
         v = this[i]
         if Boolean(pred.call(thisArg, v, i, this)):
           result.push(v)
     return result
   
   Difference vs map:
     map preserves holes (output sparse).
     filter SKIPS holes entirely (output dense).
     
   Order preserved:
     output is relative-order-preserved subset.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `[1, , 3].filter(() => true)` length? Holes preserved?
> 2. Does filter mutate?
> 3. How is predicate result coerced?

---

## 6. Brute force — walked through

```js
arr.forEach((v, i) => { if (pred(v)) result.push(v); });
```

Misses: holes invoked with undefined; ignores thisArg; predicate args incomplete.

---

## 7. The unlocking insight

> **Skip holes via `i in this`; output dense (relative-order subset). `pred.call(thisArg, v, i, this)`. Boolean coerce result.**

Three properties:

1. **Skip via `i in this`** — predicate not invoked on holes.
2. **Dense output** — push only truthy.
3. **3-arg callback + thisArg** — full spec.

---

## 8. Solution (annotated)

```js
Object.defineProperty(Array.prototype, 'myFilter', {
  enumerable: false,                                                    // step 1: non-enumerable
  value: function (callback, thisArg) {
    if (this == null) throw new TypeError('myFilter on null/undefined');
    if (typeof callback !== 'function') throw new TypeError('cb not callable');

    const O = Object(this);
    const len = O.length >>> 0;                                          // step 2: ToUint32
    const result = [];

    for (let i = 0; i < len; i++) {
      if (i in O) {                                                       // step 3: skip holes
        const v = O[i];
        if (callback.call(thisArg, v, i, O)) {                           // step 4: thisArg + 3 args + truthy
          result.push(v);                                                // step 5: dense push
        }
      }
    }
    return result;
  },
});
```

**Try it yourself**

```js
[1, 2, 3, 4].myFilter(x => x % 2 === 0);                     // [2, 4]

// Holes skipped, output dense
[1, , 3].myFilter(() => true);                                // [1, 3], length 2

// thisArg
[1, 2, 3].myFilter(function (x) { return x > this.min; }, { min: 1 });   // [2, 3]

// Index in predicate
['a', 'b', 'c'].myFilter((v, i) => i % 2 === 0);              // ['a', 'c']

// Array-like
Array.prototype.myFilter.call({0:1, 1:2, 2:3, length:3}, x => x > 1);    // [2, 3]
```

---

## 9. Step-by-step dry run

```
[1, , 3].myFilter(() => true):
  len = 3. result = [].
  
  i=0: 0 in [1,,3] true → pred(1) truthy → push 1. result = [1].
  i=1: 1 in [1,,3] false → skip. result = [1].
  i=2: 2 in [1,,3] true → pred(3) truthy → push 3. result = [1, 3].
  
  Return [1, 3]. length=2. dense (no holes).

Difference from map:
  [1,,3].myMap(x => x) → [1, <empty>, 3], length 3. holes preserved.
  [1,,3].myFilter(()=>true) → [1, 3], length 2. dense.

Length snapshot:
  arr.myFilter(v => { arr.push(99); return v < 100; });
  pushed values NOT visited (len snapshotted).
```

---

## 10. Common confusion + traps

1. **Holes invoked with `undefined`** — wrong; skip.
2. **`thisArg` ignored** — common miss.
3. **Mutate source** — non-mutating.
4. **Output sparse like map** — no; dense.
5. **Coerce predicate to Boolean** — `if (cb(...))` does this naturally.
6. **`this[i] !== undefined`** as hole check — wrong.
7. **Forget 3-arg signature** — predicates using `(v,i,a)` break.

---

## 11. Senior follow-ups & variants

### Variant 1 — `groupBy` via filter
`{true: filter(p), false: filter(notP)}` — two passes. `partition` does one pass.

### Variant 2 — `.filter(Boolean)`
Drop falsy elements idiom.

### Variant 3 — `findIndex` family
Doesn't skip holes (ES6 cleanup).

### Variant 4 — Web Streams analog
`TransformStream` that conditionally enqueues.

### Variant 5 — Async filter
Not native; `Promise.all(arr.map(asyncPred)).then(...)`.

---

## 12. How to think aloud

> "`filter` skips holes and produces dense output (different from `map` which preserves holes). Spec: 3-arg callback `(value, index, array)`, `thisArg` second param, snapshot length, non-mutating. Step 1: validate. Step 2: snapshot len via `>>> 0`. Step 3: loop with `i in this` to skip holes — predicate NOT invoked on missing indices. Step 4: `cb.call(thisArg, v, i, this)`. Step 5: if truthy, push value. Boolean coercion natural via `if`. Result dense — sparse holes don't transfer. Use defineProperty with enumerable:false. Tests: `[1,,3].myFilter(() => true)` → `[1,3]` length 2; `[1].myFilter.call({0:1,length:1}, x=>true)` works on array-likes. Trap: invoking on holes (use `i in this`); ignoring thisArg; mutating source; expecting hole preservation."

---

## 13. 60-second revision

> - **Skip via `i in this`** — predicate not called on holes.
> - **Dense output** — push truthy elements; no hole preservation.
> - **`pred.call(thisArg, v, i, this)`** — 3 args + thisArg.
> - **`length >>> 0`** snapshot.
> - **Non-mutating.**
> - **`Object.defineProperty(..., {enumerable: false})`**.
> - **Trap:** invoking on holes; thisArg ignored; hole preservation; mutate source.

---

**Related:** [polyfill-map.md](./polyfill-map.md) · [polyfill-reduce.md](./polyfill-reduce.md) · [polyfill-find-findindex.md](./polyfill-find-findindex.md) · [polyfill-some-every.md](./polyfill-some-every.md) · [group-and-partition.md](./group-and-partition.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
