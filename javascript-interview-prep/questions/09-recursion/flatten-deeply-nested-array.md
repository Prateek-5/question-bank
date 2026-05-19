# `flat(arr, depth)` — deeply nested with `Infinity`

> **Difficulty:** Foundation-Medium   |   **Time:** ~10 min   |   **Prereqs:** [flatten-array-simple.md](./flatten-array-simple.md)
>
> **Source:** LeetCode #2625. Native `Array.prototype.flat()`.

---

## 1. Problem statement

Flatten arbitrarily nested array fully (`Infinity`) or to a depth. Provide recursive + iterative implementations.

**Verification examples**

```js
flat([1, [2, [3, [4]]]]);                 // [1, 2, [3, [4]]] (default 1)
flat([1, [2, [3, [4]]]], 2);              // [1, 2, 3, [4]]
flat([1, [2, [3, [4]]]], Infinity);       // [1, 2, 3, 4]

// Deeply nested adversarial input
const deep = []; let cur = deep;
for (let i = 0; i < 100_000; i++) { const n = []; cur.push(n); cur = n; }
flatRecursive(deep, Infinity);            // RangeError
flatIterative(deep, Infinity);            // OK
```

**Constraints**
- Recursive: O(d) stack frames; blows past ~10-15k.
- Iterative: heap stack; handles million-deep.
- V8 does NOT optimize tail calls.
- `Array.isArray` not `instanceof`.

---

## 2. Plain-English restatement

Flatten with depth control. Recursive elegant but stack-limited. Iterative with explicit stack for production.

---

## 3. Why this matters in interviews

Mid-tier flatten — tests V8 TCO awareness + iterative discipline. Senior offers BOTH versions proactively.

---

## 4. Mental model

```
   Recursive (elegant, stack-limited):
     flat(arr, depth):
       out = []
       for item of arr:
         if Array.isArray(item) && depth > 0:
           for x of flat(item, depth - 1): out.push(x)
         else: out.push(item)
       return out
     
     Call stack depth = nesting depth (up to depth param).
     V8 default ~10-15k frames; blows up.
   
   Iterative (heap stack, unlimited):
     stack = arr.map(item => [item, depth])    ← pair (item, remainingDepth)
     out = []
     while stack:
       [item, d] = stack.pop()
       if Array.isArray(item) && d > 0:
         push children REVERSE order: [child, d-1]
       else: out.push(item)
     return out (must reverse if pushed in wrong order)
   
   Or: shift from start; push from end — preserves order naturally.

   Why iterative is production-grade:
     Stack memory in heap (V8 doesn't limit).
     Survives adversarial inputs (1M-deep arrays from parsing JSON).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does V8 do with tail-recursion?
> 2. When does recursive blow stack?
> 3. Why push children REVERSE in iterative?

---

## 6. Brute force — walked through

```js
function flat(arr, depth = 1) {
  return depth > 0
    ? arr.reduce((a, x) => a.concat(Array.isArray(x) ? flat(x, depth - 1) : x), [])
    : arr.slice();
}
```

O(n²) concat. Pretty but slow + stack-limited.

---

## 7. The unlocking insight

> **Recursive elegant; iterative production-grade. V8 doesn't TCO. Explicit work stack `[item, depth]` pairs.**

Three properties:

1. **`Array.isArray`** not `instanceof`.
2. **Recursive: depth = stack frames.**
3. **Iterative: heap stack survives deep input.**

---

## 8. Solution (annotated)

```js
// Recursive — elegant, stack-limited
function flatRecursive(arr, depth = 1) {
  const out = [];
  for (const item of arr) {
    if (Array.isArray(item) && depth > 0) {
      for (const x of flatRecursive(item, depth - 1)) {                    // step 1: recurse
        out.push(x);
      }
    } else {
      out.push(item);
    }
  }
  return out;
}

// Iterative — production-grade, depth-safe
function flatIterative(arr, depth = 1) {
  const out = [];
  // Use a stack of [item, depthRemaining] pairs.
  // Push the input items in reverse so we POP them in original order.
  const stack = [];
  for (let i = arr.length - 1; i >= 0; i--) {                              // step 2: reverse push
    stack.push([arr[i], depth]);
  }
  while (stack.length) {
    const [item, d] = stack.pop();
    if (Array.isArray(item) && d > 0) {
      for (let i = item.length - 1; i >= 0; i--) {                          // step 3: reverse children
        stack.push([item[i], d - 1]);
      }
    } else {
      out.push(item);                                                       // step 4: leaf
    }
  }
  return out;
}
```

**Try it yourself**

```js
flatRecursive([1, [2, [3, [4]]]]);                           // [1, 2, [3, [4]]]
flatRecursive([1, [2, [3, [4]]]], Infinity);                 // [1, 2, 3, 4]
flatIterative([1, [2, [3, [4]]]], Infinity);                 // [1, 2, 3, 4]

// Adversarial: 100k-deep
const deep = []; let cur = deep;
for (let i = 0; i < 100_000; i++) { const n = []; cur.push(n); cur = n; }
cur.push('end');

// flatRecursive(deep, Infinity);    // RangeError: Maximum call stack
flatIterative(deep, Infinity);         // ['end']

// LeetCode #2625 — Infinity is the canonical test
flatIterative([1, [2, [3, [4, [5]]]]], Infinity);            // [1, 2, 3, 4, 5]
```

---

## 9. Step-by-step dry run

```
flatIterative([1, [2, [3]]], 1):
  Initial stack (reverse of input): [[ [2,[3]], 1 ], [1, 1]].
  Stack: bottom→top: [ [2,[3]], 1 ], [1, 1].
  
  pop [1, 1]: not array. out.push(1). out=[1].
  pop [[2, [3]], 1]: is array, d=1>0.
    push children reverse: [[3], 0], [2, 0].
    Stack: [[3], 0], [2, 0].
  pop [2, 0]: d=0, not array (well, 2 is not array anyway). out.push(2). out=[1, 2].
  pop [[3], 0]: is array, d=0. → falls to else (d>0 false). out.push([3]). out=[1, 2, [3]].
  
  Return [1, 2, [3]].

flatRecursive(deep, Infinity), deep is 100k-nested:
  Each call: for item, recurse with depth-1.
  Call stack depth = 100k frames.
  V8 limit ~10-15k. Blows up.

flatIterative:
  Stack array in heap. 100k entries.
  Heap can hold millions of entries.
  Each iteration: pop + push children. O(n) total.
  No stack growth. Survives.

Reverse-push reasoning:
  Stack is LIFO. To process in original order, push reverse.
  e.g. [a, b, c]: push c, b, a. Pop a → b → c.
```

---

## 10. Common confusion + traps

1. **Recursive on adversarial input** — stack overflow.
2. **V8 TCO** — no; despite ES2015 spec (only JSC does).
3. **`instanceof Array`** — cross-realm fail.
4. **`typeof === 'object'`** — matches null/{}.
5. **Spread `out.push(...flat(...))`** — intermediate array per call.
6. **Concat reduce** — O(n²).
7. **Push children forward** — reverses output order.

---

## 11. Senior follow-ups & variants

### Variant 1 — Generator (lazy)
Yield leaves; consumer can break early.

### Variant 2 — Polyfill `Array.prototype.flat`
Install on prototype with non-enumerable.

### Variant 3 — `flatMap`
Map+flat(1) fused.

### Variant 4 — Drop holes
Native `flat` drops holes; iterative respects.

### Variant 5 — Big-O comparison
Concat-reduce vs push: O(n²) vs O(n).

---

## 12. How to think aloud

> "Two implementations: recursive (elegant) and iterative (production-grade). Recursive: for each item, if it's an array and depth > 0, recurse with `depth - 1`, push results. Stack frames = nesting depth, capped by `depth` param. V8 default stack ~10-15k frames; blows on adversarial input (100k-deep array from parsing untrusted JSON). V8 does NOT optimize tail calls despite ES2015 spec — only Safari/JSC does. So 'write it tail-recursive' is wrong on the server. Iterative: explicit work stack of `[item, depthRemaining]` pairs, pop LIFO, push children in REVERSE order (so pop yields original order). Stack lives in heap (V8 doesn't bound) — survives million-deep inputs. `Array.isArray` over `instanceof Array` (cross-realm safe) and over `typeof item === 'object'` (matches null/{}). Avoid `reduce + concat` — O(n²) because each concat copies the accumulator. Variants: lazy generator (yield leaves; stop early); polyfill on Array.prototype with non-enumerable; flatMap fuses map+flat(1). Trap: recursive on adversarial; concat O(n²); push children forward (reverses output); instanceof Array."

---

## 13. 60-second revision

> - **Recursive elegant; iterative production.**
> - **V8 NO TCO** — recursive blows on 10-15k+ depth.
> - **Iterative `[item, depth]` stack** in heap.
> - **Push children REVERSE** for pop-order = forward.
> - **`Array.isArray`** — not instanceof, not typeof.
> - **Avoid reduce+concat** O(n²).
> - **Lazy generator** for early break.
> - **Trap:** recursive adversarial; concat-reduce; reverse-push.

---

**Related:** [flatten-array-simple.md](./flatten-array-simple.md) · [flatten-with-depth.md](./flatten-with-depth.md) · [`07-arrays/polyfill-flat.md`](../07-arrays/polyfill-flat.md) · [trampoline-pattern.md](./trampoline-pattern.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
