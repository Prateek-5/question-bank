# zip / unzip (Python-style)

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [transpose-matrix.md](./transpose-matrix.md), [polyfill-reduce.md](./polyfill-reduce.md)
>
> **Source:** BFE.dev #97. Lodash `_.zip` / `_.unzip`. Python `zip()`.

---

## 1. Problem statement

`zip(...arrays)` combines K arrays of length N into N tuples of K elements. `unzip(tuples)` is the inverse. Stop-at-shortest by default.

**Verification examples**

```js
zip([1, 2, 3], ['a', 'b', 'c']);
// [[1, 'a'], [2, 'b'], [3, 'c']]

zip([1, 2, 3], ['a', 'b']);
// [[1, 'a'], [2, 'b']]              ← stop at shortest

unzip([[1, 'a'], [2, 'b'], [3, 'c']]);
// [[1, 2, 3], ['a', 'b', 'c']]

zip();                                // []
zip([]);                              // []
```

**Constraints**
- Stop-at-shortest (lodash/Python default).
- Pad-to-longest variant: `zip_longest`.
- Pure: no input mutation.
- Variable arity: `...arrays`.

---

## 2. Plain-English restatement

`zip` pairs corresponding elements across multiple arrays into tuples. `unzip` is the inverse. `zip` is matrix transposition. Stop at shortest by default.

---

## 3. Why this matters in interviews

Tests variable arity, length policy, transpose intuition, reduce fluency. Backend pairs parallel arrays / builds DataFrame-like structures.

---

## 4. Mental model

```
   zip(...arrays):
     n = min(arrays.map(a => a.length))    ← stop at shortest
     out = []
     for i in 0..n-1:
       out.push(arrays.map(a => a[i]))
     return out
   
   zip_longest(...arrays, fillValue = undefined):
     n = max(...lengths)
     for i in 0..n-1:
       out.push(arrays.map(a => i < a.length ? a[i] : fillValue))

   unzip(tuples):
     return zip(...tuples)               ← transpose!
   
   zipWith(fn, ...arrays):
     same as zip but applies fn to each tuple before pushing.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `zip([1, 2], ['a'])` length?
> 2. How is zip related to transpose?
> 3. `zip()` (no args)?

---

## 6. Brute force — walked through

```js
function zip(...arrays) {
  const n = Math.min(...arrays.map(a => a.length));
  return Array.from({ length: n }, (_, i) => arrays.map(a => a[i]));
}
```

Clean; lodash-compatible. Variants for unzip + longest.

---

## 7. The unlocking insight

> **`zip(...arrays)` is `transpose(arrays)` with stop-at-shortest. `unzip = zip(...tuples)`. Map per index across all arrays.**

Three properties:

1. **`Math.min(...lengths)`** — stop-at-shortest.
2. **`zip(...arrays) === transpose(arrays)`.**
3. **`unzip === zip(...tuples)`.**

---

## 8. Solution (annotated)

```js
function zip(...arrays) {
  if (arrays.length === 0) return [];                                     // step 1: empty arity
  const n = Math.min(...arrays.map((a) => a.length));                     // step 2: stop-at-shortest
  return Array.from({ length: n }, (_, i) =>                              // step 3: per index
    arrays.map((a) => a[i])                                                // step 4: pluck across arrays
  );
}

function unzip(tuples) {
  return zip(...tuples);                                                   // step 5: transpose
}

function zipLongest(fillValue, ...arrays) {
  if (arrays.length === 0) return [];
  const n = Math.max(...arrays.map((a) => a.length));
  return Array.from({ length: n }, (_, i) =>
    arrays.map((a) => (i < a.length ? a[i] : fillValue)),
  );
}

function zipWith(fn, ...arrays) {
  if (arrays.length === 0) return [];
  const n = Math.min(...arrays.map((a) => a.length));
  return Array.from({ length: n }, (_, i) =>
    fn(...arrays.map((a) => a[i])),                                       // step 6: apply per tuple
  );
}
```

**Try it yourself**

```js
zip([1, 2, 3], ['a', 'b', 'c']);                              // [[1,'a'],[2,'b'],[3,'c']]
zip([1, 2, 3], ['a', 'b']);                                   // [[1,'a'],[2,'b']]
zip([1, 2, 3], ['a', 'b', 'c'], [true, false, true]);         // 3 tuples of 3

unzip([[1, 'a'], [2, 'b'], [3, 'c']]);                        // [[1,2,3], ['a','b','c']]

zipLongest(null, [1, 2, 3], ['a', 'b']);                      // [[1,'a'],[2,'b'],[3,null]]

zipWith((a, b) => a + b, [1, 2, 3], [10, 20, 30]);            // [11, 22, 33]
zipWith((a, b) => ({ a, b }), [1, 2], ['x', 'y']);            // [{a:1,b:'x'}, {a:2,b:'y'}]

// Empty cases
zip();                                                         // []
zip([]);                                                       // []
zip([], [1, 2]);                                              // [] (min is 0)

// Build an object from keys + values arrays
function objFromArrays(keys, values) {
  return Object.fromEntries(zip(keys, values));
}
objFromArrays(['a', 'b'], [1, 2]);                            // {a: 1, b: 2}
```

---

## 9. Step-by-step dry run

```
zip([1, 2, 3], ['a', 'b']):
  n = min(3, 2) = 2.
  i=0: arrays.map(a => a[0]) → [1, 'a']. push.
  i=1: → [2, 'b']. push.
  Return [[1, 'a'], [2, 'b']].

unzip([[1, 'a'], [2, 'b'], [3, 'c']]):
  Spread: zip([1,'a'], [2,'b'], [3,'c']).
  n = min(2, 2, 2) = 2.
  i=0: [1, 2, 3]. push.
  i=1: ['a', 'b', 'c']. push.
  Return [[1, 2, 3], ['a', 'b', 'c']].

zip([], [1, 2]):
  n = min(0, 2) = 0.
  Loop empty.
  Return [].

zipWith((a, b) => a*b, [1, 2, 3], [10, 20, 30]):
  n=3.
  i=0: fn(1, 10) = 10.
  i=1: fn(2, 20) = 40.
  i=2: fn(3, 30) = 90.
  Return [10, 40, 90].
```

---

## 10. Common confusion + traps

1. **Pad-to-longest by default** — no; stop-at-shortest.
2. **Empty input** — `zip() === []`; `zip([]) === []`.
3. **Sparse arrays** — hole becomes `undefined` in tuple.
4. **Mutation** — neither zip nor unzip mutates.
5. **Single array input** — `zip([1,2,3])` → `[[1],[2],[3]]` (each element wrapped).
6. **TypedArray** — works; result is plain Array of tuples.
7. **`zip` vs `zipWith`** — zipWith applies a fn per tuple.

---

## 11. Senior follow-ups & variants

### Variant 1 — `zip_longest` (pad)
Like Python `itertools.zip_longest`.

### Variant 2 — `zipObject(keys, values)`
Lodash variant; returns `Object.fromEntries(zip(keys, values))`.

### Variant 3 — Lazy zip
Generator yielding tuples; for huge inputs.

### Variant 4 — Async zip
`zipAsync` for parallel async iterables.

### Variant 5 — `unzip` with ragged tuples
Spec: pad shorter columns with undefined or holes.

---

## 12. How to think aloud

> "`zip` is variadic: `function zip(...arrays)`. Length policy is stop-at-shortest (lodash/Python default) — `n = Math.min(...arrays.map(a => a.length))`. Per index `i`, build tuple `arrays.map(a => a[i])`. `Array.from({length: n}, mapper)` for clean one-liner. `unzip` is just `zip(...tuples)` — they're inverses (both are matrix transpose). Variants: `zipLongest(fill, ...arrays)` pads with fill value; `zipWith(fn, ...arrays)` applies a function per tuple before pushing — useful for sums, object builds. Empty cases: `zip()` → `[]`; `zip([], [1, 2])` → `[]` (min is 0). Sparse arrays: holes become `undefined` in tuple. `zipObject(keys, values)` = `Object.fromEntries(zip(keys, values))`. Trap: pad-to-longest by default (wrong); empty edge cases; expecting mutation (pure)."

---

## 13. 60-second revision

> - **`zip(...arrays)`** — variadic, stop-at-shortest.
> - **`Math.min(...lengths)`** for n.
> - **`zip = transpose`; `unzip = zip(...tuples)`.**
> - **`zipLongest`** pads to longest.
> - **`zipWith`** applies fn per tuple.
> - **`zipObject(k, v)`** = `Object.fromEntries(zip(k, v))`.
> - **`zip()`** → `[]`.
> - **Pure** — no mutation.
> - **Trap:** pad default (wrong); empty edges; holes → undefined.

---

**Related:** [transpose-matrix.md](./transpose-matrix.md) · [polyfill-map.md](./polyfill-map.md) · [polyfill-reduce.md](./polyfill-reduce.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
