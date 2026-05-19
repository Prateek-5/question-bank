# Single-level flatten

> **Difficulty:** Foundation   |   **Time:** ~5 min   |   **Prereqs:** none
>
> **Source:** codedamn lab. Native `Array.prototype.flat()`.

---

## 1. Problem statement

Peel ONE level of nesting. Don't recurse.

**Verification examples**

```js
flatten([1, [2, 3], [4, [5]]]);          // [1, 2, 3, 4, [5]]
flatten([1, 2, 3]);                      // [1, 2, 3]
flatten([[1], [2], [3]]);                // [1, 2, 3]
flatten([]);                              // []
```

**Constraints**
- Single level only.
- No recursion.
- O(n) time.

---

## 2. Plain-English restatement

For each element: if array, expand its items; else push. One level deep.

---

## 3. Why this matters in interviews

Opener test — over-engineers fall into recursion when one-line for-of suffices. Read the prompt.

---

## 4. Mental model

```
   for item of arr:
     if Array.isArray(item):
       for x of item: out.push(x)
     else: out.push(item)
   
   Equivalent: [].concat(...arr) — concat spread peels one level.
   Equivalent: arr.flat() — native, default depth 1.

   Anti-pattern:
     reduce((a, b) => a.concat(b), [])   ← O(n²) on huge inputs (each concat copies).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Should you recurse?
> 2. `flatten([])` returns?
> 3. Difference from `flat(Infinity)`?

---

## 6. Brute force — walked through

```js
arr.reduce((a, b) => a.concat(b), [])    // works; O(n²) on huge
```

---

## 7. The unlocking insight

> **One level only. for-of + conditional push or `push(...item)`. No recursion.**

Three properties:

1. **No recursion** — single level.
2. **`Array.isArray`** check.
3. **Avoid `reduce+concat`** O(n²).

---

## 8. Solution (annotated)

```js
function flatten(arr) {
  const out = [];
  for (const item of arr) {
    if (Array.isArray(item)) {
      for (const x of item) out.push(x);                                   // step 1: expand one level
    } else {
      out.push(item);                                                       // step 2: leaf
    }
  }
  return out;
}

// Spread one-liner
const flatten2 = (arr) => [].concat(...arr);

// Native
const flatten3 = (arr) => arr.flat();                                       // default depth 1
```

**Try it yourself**

```js
flatten([1, [2, 3], 4]);                                      // [1, 2, 3, 4]
flatten([[1], [2, 3], 4]);                                    // [1, 2, 3, 4]
flatten([[1, [2]], 3]);                                       // [1, [2], 3]  ← inner [2] preserved
flatten([]);                                                   // []
flatten([[], [], []]);                                         // []

// Performance comparison on huge inputs
const huge = Array.from({length: 10_000}, (_, i) => [i, i+1]);
// O(n) — for-loop or push(...item)
flatten(huge);
// O(n²) — reduce+concat
huge.reduce((a, b) => a.concat(b), []);    // slow for n=10k
```

---

## 9. Step-by-step dry run

```
flatten([1, [2, 3], 4, [5]]):
  out = [].
  item=1: not array → out.push(1). out=[1].
  item=[2, 3]: array → push 2, 3. out=[1, 2, 3].
  item=4: not array → push 4. out=[1, 2, 3, 4].
  item=[5]: array → push 5. out=[1, 2, 3, 4, 5].
  return [1, 2, 3, 4, 5].

flatten([1, [2, [3]], 4]):
  out=[1].
  item=[2, [3]]: array → push each: out=[1, 2, [3]].
  item=4 → out=[1, 2, [3], 4].
  return [1, 2, [3], 4].   ← inner [3] preserved (one level peeled only).
```

---

## 10. Common confusion + traps

1. **Recurse anyway** — wastes; over-engineered.
2. **`reduce+concat`** — O(n²) for huge.
3. **`typeof item === 'object'`** — matches null/{}/Date.
4. **Mutate input** — non-mutating expected.
5. **Spread into existing** vs new array — both fine.
6. **`flat()` undefined in old envs** — polyfill.
7. **Sparse arrays** — `for-of` skips holes; `flat()` removes holes.

---

## 11. Senior follow-ups & variants

### Variant 1 — Depth N
See `flatten-with-depth.md`.

### Variant 2 — Infinity
See `flatten-deeply-nested-array.md`.

### Variant 3 — `flatMap`
Map then flat(1) — fused.

### Variant 4 — Stream
Generator yielding leaves.

### Variant 5 — In-place
Mutate original; uncommon.

---

## 12. How to think aloud

> "Single-level flatten: for-of loop, check `Array.isArray(item)`, expand one level via inner loop or `push(...item)`. Do NOT recurse — the prompt is one level only. Avoid `reduce((a, b) => a.concat(b), [])` — it's O(n²) on huge inputs because each `concat` copies the accumulator. One-liner: `[].concat(...arr)` or native `arr.flat()` (default depth 1). `Array.isArray` over `typeof item === 'object'` (which matches null/Date/{}). Variants: depth N (see flatten-with-depth.md), Infinity (see flatten-deeply-nested-array.md), `flatMap` for map+flat(1). Trap: recursing when not asked; reduce+concat O(n²); typeof object."

---

## 13. 60-second revision

> - **One level only** — no recursion.
> - **`for-of` + `Array.isArray` + push.**
> - **Native `arr.flat()`** — default depth 1.
> - **`[].concat(...arr)`** one-liner.
> - **Avoid `reduce+concat`** O(n²).
> - **Variants:** depth N, Infinity, flatMap.
> - **Trap:** recurse; reduce+concat; typeof object.

---

**Related:** [flatten-with-depth.md](./flatten-with-depth.md) · [flatten-deeply-nested-array.md](./flatten-deeply-nested-array.md) · [`07-arrays/polyfill-flat.md`](../07-arrays/polyfill-flat.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md), [`concepts/arrays.md`](../../concepts/arrays.md)
