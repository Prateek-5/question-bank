# Polyfill `Array.prototype.reduce`

> **Difficulty:** Foundation   |   **Time:** ~15 min   |   **Prereqs:** [polyfill-map.md](./polyfill-map.md), [lodash-reduce.md](./lodash-reduce.md)
>
> **Source:** BFE.dev #18, GreatFrontEnd. LeetCode #2626.

---

## 1. Problem statement

Re-implement `Array.prototype.reduce` honoring no-initial-value seed handling, hole-skipping, and TypeError on empty-no-initial.

**Verification examples**

```js
[1, 2, 3].myReduce((acc, x) => acc + x, 0);     // 6
[1, 2, 3].myReduce((acc, x) => acc + x);        // 6 (acc = 1, starts at i=1)
[, , 3, 4].myReduce((a, b) => a + b);           // 7 (seed = first defined = 3)
[].myReduce((a, b) => a + b);                   // TypeError
[1, , 3].myReduce((acc, x) => acc + x, 0);      // 4 (hole skipped)
```

**Constraints**
- 4-arg callback: `(acc, current, index, array)`.
- No initial value → seed = first defined element, start at next index.
- Empty + no initial → `TypeError`.
- Skip holes via `i in this`.
- Length snapshotted.

---

## 2. Plain-English restatement

Fold an array into a single value. With initial value: `acc = init, i = 0`. Without: `acc = first non-hole element, i = its index + 1`. Skip holes. Throw on empty-no-initial.

---

## 3. Why this matters in interviews

`reduce` tests closures-over-accumulator + no-initial edge case + sparse semantics + `TypeError` discipline. Senior backend engineers fold constantly (event aggregation, log rollups, RPC fan-in).

---

## 4. Mental model

```
   arr.reduce(cb, init?):
     len = ToLength
     i = 0
     if init given:
       acc = init
     else:
       // find first non-hole index
       while i < len && !(i in this): i++
       if i >= len: throw TypeError("Reduce of empty array with no initial value")
       acc = this[i]; i++
     
     while i < len:
       if i in this:
         acc = cb(acc, this[i], i, this)
       i++
     return acc

   No initial + sparse:
     [, , 3, 4].reduce((a,b)=>a+b)
     i=0 hole, i=1 hole, i=2 → seed=3, i=3.
     i=3 (4): acc = 3+4 = 7.
     return 7.

   No initial + empty:
     [].reduce(fn) → TypeError.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `[].reduce((a,b)=>a+b)` — what happens?
> 2. `[, , 3].reduce((a,b)=>a+b)` — what's the seed?
> 3. Are holes invoked?

---

## 6. Brute force — walked through

```js
arr.reduce = function(cb, init) {
  let acc = init !== undefined ? init : this[0];
  for (let i = 0; i < this.length; i++) acc = cb(acc, this[i], i, this);
  return acc;
};
```

Bugs: passing `0` as init triggers `[0].reduce` to use `this[0]` (wrong); double-counts seed; invokes on holes; no TypeError.

---

## 7. The unlocking insight

> **Branch on `arguments.length >= 2` for seed selection. Skip holes via `i in this`. Throw on empty-no-initial.**

Three properties:

1. **`arguments.length >= 2`** distinguishes "init passed" from "omitted" — not `init !== undefined`.
2. **First defined as seed** when no init.
3. **`TypeError` on empty-no-initial.**

---

## 8. Solution (annotated)

```js
Object.defineProperty(Array.prototype, 'myReduce', {
  enumerable: false,
  value: function (callback, ...rest) {
    if (this == null) throw new TypeError('myReduce on null/undefined');
    if (typeof callback !== 'function') throw new TypeError('cb not callable');

    const O = Object(this);
    const len = O.length >>> 0;
    const hasInit = rest.length >= 1;                                    // step 1: distinguish passed vs omitted
    let acc;
    let i = 0;

    if (hasInit) {
      acc = rest[0];                                                     // step 2: explicit init
    } else {
      while (i < len && !(i in O)) i++;                                  // step 3: find first non-hole
      if (i >= len) {
        throw new TypeError('Reduce of empty array with no initial value');
      }
      acc = O[i];
      i++;                                                                // step 4: start AFTER seed
    }

    while (i < len) {
      if (i in O) {                                                       // step 5: skip holes
        acc = callback(acc, O[i], i, O);
      }
      i++;
    }
    return acc;
  },
});
```

**Try it yourself**

```js
[1, 2, 3, 4].myReduce((a, b) => a + b, 0);                   // 10
[1, 2, 3, 4].myReduce((a, b) => a + b);                      // 10 (no init)
[, , 3, 4].myReduce((a, b) => a + b);                        // 7 (seed=3, i starts at 3)

// Empty cases
[].myReduce((a, b) => a + b, 0);                              // 0 (init returned)
[].myReduce((a, b) => a + b);                                 // TypeError

// Holes skipped
[1, , 3].myReduce((acc, x) => acc + x, 0);                   // 4 (hole not invoked)

// Object grouping
const grouped = items.myReduce((acc, item) => {
  (acc[item.type] ??= []).push(item);
  return acc;
}, {});

// Right reduce (separate method)
[1, 2, 3].myReduceRight((a, b) => `${a}-${b}`);              // '3-2-1'
```

---

## 9. Step-by-step dry run

```
[, , 3, 4].myReduce((a, b) => a + b):
  hasInit = false.
  i = 0: 0 in arr false → i = 1.
  i = 1: 1 in arr false → i = 2.
  i = 2: 2 in arr true → acc = 3. i = 3.
  
  Main loop:
  i = 3: 3 in arr true → acc = cb(3, 4, 3, arr) = 7. i = 4.
  i = 4: loop exit.
  
  Return 7.

[1, , 3].myReduce((a, b) => a + b, 0):
  hasInit = true. acc = 0. i = 0.
  i = 0: 0 in arr true → acc = cb(0, 1) = 1. i = 1.
  i = 1: 1 in arr false → skip. i = 2.
  i = 2: 2 in arr true → acc = cb(1, 3) = 4. i = 3.
  Return 4. (Hole not double-counted nor invoked.)

[].myReduce(fn):
  hasInit = false.
  while loop: 0 in [] false, i = 1. 1 >= 0... wait, len=0. So while condition: i < 0 = false immediately.
  i = 0 = len. Throw TypeError.
```

---

## 10. Common confusion + traps

1. **`init !== undefined`** as "init passed" check — fails when init=undefined intentionally. Use `arguments.length >= 2`.
2. **Empty + no init → returns undefined** — should throw.
3. **Holes invoked** — skip via `i in this`.
4. **No-init double-counts seed** — start at index AFTER seed.
5. **No-init with all holes → seed undefined** — should be TypeError too.
6. **Callback fourth arg missed** — `cb(acc, v, i, array)`.
7. **Mutate during iteration** — length snapshotted; extra pushes ignored.

---

## 11. Senior follow-ups & variants

### Variant 1 — `reduceRight`
Same logic, iterate from `len-1` down. Seed = last non-hole when no init.

### Variant 2 — Transducers
Compose reduce+map+filter into single pass.

### Variant 3 — `groupBy` via reduce
`arr.reduce((acc, x) => ({...acc, [key(x)]: (acc[key(x)]||[]).concat(x)}), {})`.

### Variant 4 — async reduce
Not native; manual loop with `await cb(acc, v, i, arr)` chained.

### Variant 5 — `Array.from` + reduce
Convert array-like, then reduce.

---

## 12. How to think aloud

> "`reduce` polyfill must handle the no-initial-value seed and TypeError discipline. Step 1: check `arguments.length >= 2` (or rest array length) to distinguish passed-undefined from omitted. Step 2: if init given, `acc = init, i = 0`. Else find first non-hole via `while (i < len && !(i in this)) i++`; if all holes/empty, throw `TypeError('Reduce of empty array with no initial value')`. Seed = `this[i]`, then `i++` to start AFTER seed. Step 3: main loop, skip holes via `i in this`, call `cb(acc, this[i], i, this)`. Length snapshotted via `>>> 0` once. Tests: `[].reduce(fn)` throws; `[,,3,4].reduce((a,b)=>a+b)` returns 7 (seed=3, sums in 4); `[1,,3].reduce((a,b)=>a+b,0)` returns 4 (hole skipped). Trap: `init !== undefined` (fails for explicit undefined); double-counting seed; invoking holes; not throwing on empty."

---

## 13. 60-second revision

> - **`arguments.length >= 2`** to detect init.
> - **No init:** seed = first non-hole; start at `seedIdx + 1`.
> - **Empty + no init → `TypeError`.**
> - **Skip holes via `i in this`.**
> - **4 callback args: `(acc, current, index, array)`.**
> - **`length >>> 0`** snapshot.
> - **`reduceRight`** mirror.
> - **Trap:** `init !== undefined` (wrong); double seed; invoke on holes; empty no throw.

---

**Related:** [polyfill-map.md](./polyfill-map.md) · [polyfill-filter.md](./polyfill-filter.md) · [polyfill-flat.md](./polyfill-flat.md) · [lodash-reduce.md](./lodash-reduce.md) · [group-and-partition.md](./group-and-partition.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
