# `flat(arr, depth)` — recursive AND iterative

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [flatten-array-simple.md](./flatten-array-simple.md), [flatten-deeply-nested-array.md](./flatten-deeply-nested-array.md)
>
> **Source:** codedamn. LeetCode #2625.

---

## 1. Problem statement

Implement flatten with depth parameter. Recursive + iterative.

**Verification examples**

```js
flat([1, [2, [3]]], 0);                   // [1, [2, [3]]] (shallow copy, no flatten)
flat([1, [2, [3]]], 1);                   // [1, 2, [3]]
flat([1, [2, [3, [4]]]], 2);              // [1, 2, 3, [4]]
flat([1, [2, [3, [4]]]], Infinity);       // [1, 2, 3, 4]
flat([1, [2]], -1);                       // [1, [2]]  (negative treated as 0)
```

**Constraints**
- depth = 0: shallow copy.
- depth = Infinity: full flatten.
- Negative depth treated as 0.
- Both recursive and iterative must be available.

---

## 2. Plain-English restatement

Generalized flatten. Same recursive + iterative as flatten-deeply-nested, but emphasis on depth=0 (shallow copy) and negative coercion.

---

## 3. Why this matters in interviews

Mid-tier. Tests generalization (depth control), iterative discipline, edge cases.

---

## 4. Mental model

```
   Same as flatten-deeply-nested but explicit depth handling:
     depth = 0 → shallow copy via arr.slice().
     depth < 0 → coerce to 0.
     depth = Infinity → recursive until leaf.
   
   Recursive: O(d) stack frames.
   Iterative: O(d) heap stack entries.
   
   Why depth=0 is shallow COPY not reference:
     Spec returns new array always. arr.slice() copies one level.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `flat([1, [2]], 0)` — same array or copy?
> 2. Negative depth?
> 3. `flat([1, [2, [3]]], Infinity - 1)` — what depth used?

---

## 6. Brute force — walked through

```js
function flat(arr, depth = 1) {
  return depth > 0
    ? arr.reduce((a, x) => a.concat(Array.isArray(x) ? flat(x, depth - 1) : x), [])
    : arr.slice();
}
```

Pretty but O(n²) (concat) and stack-bounded.

---

## 7. The unlocking insight

> **Depth control via base case. `depth = 0 → slice`. Iterative `[item, depthRemaining]` stack for safety.**

Three properties:

1. **`depth = 0` shallow copy.**
2. **Recursive `depth - 1`** per level.
3. **Iterative pairs `[item, depth]`** for safety.

---

## 8. Solution (annotated)

```js
function flat(arr, depth = 1) {
  depth = Math.max(0, Math.floor(depth));                                   // step 1: coerce
  if (depth === 0) return arr.slice();                                      // step 2: shallow copy
  return flatRecursive(arr, depth);
}

function flatRecursive(arr, depth = 1) {
  const out = [];
  for (const item of arr) {
    if (Array.isArray(item) && depth > 0) {
      for (const x of flatRecursive(item, depth - 1)) out.push(x);          // step 3: recurse
    } else {
      out.push(item);
    }
  }
  return out;
}

// Iterative for production safety
function flatIterative(arr, depth = 1) {
  depth = Math.max(0, Math.floor(depth));
  if (depth === 0) return arr.slice();

  const out = [];
  const stack = [];
  for (let i = arr.length - 1; i >= 0; i--) stack.push([arr[i], depth]);
  while (stack.length) {
    const [item, d] = stack.pop();
    if (Array.isArray(item) && d > 0) {
      for (let i = item.length - 1; i >= 0; i--) {
        stack.push([item[i], d - 1]);
      }
    } else {
      out.push(item);
    }
  }
  return out;
}
```

**Try it yourself**

```js
flat([1, [2, [3]]], 0);                                       // [1, [2, [3]]]  (shallow copy)
flat([1, [2, [3]]], 1);                                       // [1, 2, [3]]
flat([1, [2, [3, [4]]]], 2);                                  // [1, 2, 3, [4]]
flat([1, [2, [3]]], Infinity);                                // [1, 2, 3]
flat([1, [2]], -1);                                            // [1, [2]] (coerced to 0)
flat([1, [2]], 1.7);                                           // [1, 2] (floored to 1)

// Shallow copy distinct
const a = [[1, 2]];
const b = flat(a, 0);
b !== a;                                                       // true (new array)
b[0] === a[0];                                                 // true (one level shared)

// Production-safe deep
const huge = []; let cur = huge;
for (let i = 0; i < 100_000; i++) { const n = []; cur.push(n); cur = n; }
flatIterative(huge, Infinity);                                // OK
// flatRecursive(huge, Infinity);                             // RangeError
```

---

## 9. Step-by-step dry run

```
flat([1, [2, [3]]], 0):
  coerce: 0.
  depth === 0 → arr.slice() → [1, [2, [3]]] (new array, one level copy).

flat([1, [2, [3]]], 1):
  coerce: 1.
  recurse:
    item=1: not array → push 1.
    item=[2,[3]]: array, d=1>0 → recurse with d=0.
      flatRecursive([2,[3]], 0):
        item=2: not array → push 2.
        item=[3]: array but d=0 → push [3].
        return [2, [3]].
      for each: push 2, push [3].
    out = [1, 2, [3]].

flat([1, [2]], -1):
  coerce: Math.max(0, Math.floor(-1)) = 0.
  arr.slice() → [1, [2]].

flat([1, [2]], 1.7):
  coerce: floor(1.7) = 1.
  Recurse with depth 1 → [1, 2].
```

---

## 10. Common confusion + traps

1. **`depth = 0` returns ref** — should be copy.
2. **Negative depth recurse** — coerce to 0.
3. **Non-integer depth** — floor (or accept; native floors).
4. **`Infinity - 1`** — stays Infinity (no warning).
5. **Recursive on huge** — RangeError.
6. **Spread output huge** — intermediate alloc.
7. **`arr.flat`** assumes int-depth; same coercion.

---

## 11. Senior follow-ups & variants

### Variant 1 — In-place
Mutate; rarely useful.

### Variant 2 — Generator
Yield leaves; lazy.

### Variant 3 — Drop predicate
Combine flat + filter.

### Variant 4 — Polyfill `Array.prototype.flat`
Install with non-enumerable.

### Variant 5 — Type-preserving
For typed arrays etc.

---

## 12. How to think aloud

> "Same recursive/iterative pattern as flatten-deeply-nested but explicit depth handling. Spec: coerce depth via `Math.max(0, Math.floor(depth))` — negative → 0, non-integer → floored. `depth === 0` returns `arr.slice()` (shallow copy — new array, one level shared). `depth === Infinity` is the deep case. Recursive: pretty, but call stack = nesting depth (up to depth param); blows on adversarial. Iterative: heap stack of `[item, depthRemaining]` pairs; push reverse for pop-order = forward. Variants: generator yielding leaves lazily (early break); flatMap = map + flat(1); polyfill installs with `Object.defineProperty({enumerable: false})`. Trap: depth=0 returning input ref (should copy); negative depth recursing; non-integer; recursive on huge."

---

## 13. 60-second revision

> - **Depth control:** `Math.max(0, Math.floor(depth))`.
> - **`depth = 0`** → `arr.slice()` (shallow copy).
> - **Recursive elegant; iterative safe.**
> - **Iterative pairs** `[item, depthRemaining]`.
> - **Negative → 0** (coerce).
> - **`Infinity` stays Infinity** through `-1`.
> - **Variants:** generator, polyfill, flatMap.
> - **Trap:** depth=0 ref-return; negative recurse; stack overflow.

---

**Related:** [flatten-array-simple.md](./flatten-array-simple.md) · [flatten-deeply-nested-array.md](./flatten-deeply-nested-array.md) · [`07-arrays/polyfill-flat.md`](../07-arrays/polyfill-flat.md) · [trampoline-pattern.md](./trampoline-pattern.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
