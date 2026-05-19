# Polyfill `Array.prototype.flat(depth)`

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [polyfill-reduce.md](./polyfill-reduce.md), [`09-recursion/flatten-array-simple.md`](../09-recursion/flatten-array-simple.md)
>
> **Source:** LeetCode #2625, codedamn. Stripe, Atlassian.

---

## 1. Problem statement

Re-implement `Array.prototype.flat(depth=1)`. Iterative (production-grade) — recursion blows stack on 10k+ depth.

**Verification examples**

```js
[1, [2, [3, [4]]]].myFlat();             // [1, 2, [3, [4]]]
[1, [2, [3, [4]]]].myFlat(2);            // [1, 2, 3, [4]]
[1, [2, [3, [4]]]].myFlat(Infinity);     // [1, 2, 3, 4]
[1, , 2].myFlat();                       // [1, 2] (holes removed)
[1, [2, [3]]].myFlat(0);                 // [1, [2, [3]]] (depth 0 = shallow copy)
```

**Constraints**
- `depth` defaults to **1**, not Infinity.
- Holes removed (output dense).
- Non-mutating.
- Only flattens arrays (not iterables, not array-likes).
- Iterative — must handle deep nesting without RangeError.

---

## 2. Plain-English restatement

Recursively unwrap nested arrays up to `depth` levels. `depth=1` (default) unwraps one level; `Infinity` unwraps fully. Holes are dropped. Use iterative stack to avoid blowing call stack on deep input.

---

## 3. Why this matters in interviews

`flat` tests **stack vs heap** + **depth tracking**. The "wrong but works" recursive answer blows stack on 10k+ levels. The "right" answer uses explicit work stack carrying `[item, remainingDepth]` pairs. Senior signal.

---

## 4. Mental model

```
   Recursive (avoid — stack overflow):
     flat(arr, d) =
       d > 0 ? arr.reduce((a, v) => a.concat(isArr(v) ? flat(v, d-1) : v), [])
             : arr.slice();
   
   Iterative (production-grade):
     stack = arr.map(v => [v, depth])           ← pairs
     result = []
     while stack.length:
       [item, d] = stack.pop()
       if Array.isArray(item) && d > 0:
         push children with d-1 (REVERSE order to maintain output order)
       else:
         result.push(item)
     return result
   
   Holes dropped:
     `for in` / `Array.isArray` checks — holes don't pass either.

   depth = 0:
     Returns a shallow copy (slice).

   Spec subtlety:
     Only Array.isArray children are flattened.
     Set/Map/iterable not flattened by flat().
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Default depth?
> 2. `[1, , 2].flat()` — holes preserved?
> 3. Why iterative over recursive?

---

## 6. Brute force — walked through

```js
function flat(arr, d = 1) {
  return d > 0
    ? arr.reduce((a, v) => a.concat(Array.isArray(v) ? flat(v, d - 1) : v), [])
    : arr.slice();
}
```

Pretty. Blows stack on 10k+ deep arrays (`[1, [2, [3, ...]]]`). Don't ship.

---

## 7. The unlocking insight

> **Iterative stack of `[item, depth]` pairs avoids recursion. Push children with `depth-1` in reverse so output order preserved. Loop while stack non-empty.**

Three properties:

1. **Iterative stack** — no recursion.
2. **Depth carried with item** — pair `[item, d]`.
3. **Reverse-push children** — preserves natural order via stack.

---

## 8. Solution (annotated)

```js
Object.defineProperty(Array.prototype, 'myFlat', {
  enumerable: false,
  value: function (depth = 1) {
    if (this == null) throw new TypeError('myFlat on null/undefined');
    const O = Object(this);
    const len = O.length >>> 0;
    const result = [];

    // Build initial stack — in REVERSE so we pop in forward order
    const stack = [];
    for (let i = len - 1; i >= 0; i--) {                                 // step 1: reverse for stack pop order
      if (i in O) stack.push([O[i], depth]);                              // step 2: skip holes
    }

    while (stack.length > 0) {
      const [item, d] = stack.pop();                                      // step 3: LIFO
      if (Array.isArray(item) && d > 0) {                                 // step 4: still flattening?
        for (let i = item.length - 1; i >= 0; i--) {                     // step 5: push children reverse
          if (i in item) stack.push([item[i], d - 1]);
        }
      } else {
        result.push(item);                                                 // step 6: leaf
      }
    }
    return result;
  },
});

// Compact recursive (DON'T use in production — for reference)
function flatRec(arr, depth = 1) {
  return depth > 0
    ? arr.reduce(
        (a, v) => a.concat(Array.isArray(v) ? flatRec(v, depth - 1) : v),
        [],
      )
    : arr.slice();
}
```

**Try it yourself**

```js
[1, [2, [3, [4]]]].myFlat();                                  // [1, 2, [3, [4]]]
[1, [2, [3, [4]]]].myFlat(2);                                 // [1, 2, 3, [4]]
[1, [2, [3, [4]]]].myFlat(Infinity);                          // [1, 2, 3, 4]
[1, , 2].myFlat();                                             // [1, 2] (holes removed)
[1, [2, [3]]].myFlat(0);                                       // [1, [2, [3]]] (depth 0)

// Deep input safety
const deep = []; let cur = deep;
for (let i = 0; i < 100000; i++) { const n = []; cur.push(n); cur = n; }
deep.myFlat(Infinity);                                        // OK — iterative, no overflow
// flatRec(deep, Infinity);                                   // RangeError: Maximum call stack

// Native parity
[1, [2]].flat();                                              // [1, 2] — native
[[1, 2], [3]].flatMap(x => x);                                // [1, 2, 3] — flat after map
```

---

## 9. Step-by-step dry run

```
[1, [2, [3, [4]]]].myFlat(2):

Initial stack (reverse): pop will yield in array order.
  stack.push([ [2,[3,[4]]], 2 ])  ← reverse, but only one inner array.
  stack.push([ 1, 2 ])
  
Iteration:
  pop [1, 2]: not array → result.push(1). result=[1].
  pop [ [2,[3,[4]]], 2 ]: array, d=2>0 →
    push reverse: [ [3,[4]], 1 ], [ 2, 1 ].
  pop [ 2, 1 ]: not array → result.push(2). result=[1,2].
  pop [ [3,[4]], 1 ]: array, d=1>0 →
    push reverse: [ [4], 0 ], [ 3, 0 ].
  pop [ 3, 0 ]: not array → result.push(3). result=[1,2,3].
  pop [ [4], 0 ]: array but d=0 → result.push([4]). result=[1,2,3,[4]].

Return [1, 2, 3, [4]].

Recursive blows stack:
  flatRec(deep, ∞) → calls itself 100k times → RangeError.
  
Iterative:
  Stack memory is HEAP (V8 doesn't limit). 100k items fine.
```

---

## 10. Common confusion + traps

1. **Default depth = Infinity** — no; it's `1`.
2. **Holes preserved like map** — no; dropped.
3. **Recursive in production** — RangeError on deep.
4. **Forward push children** — reverses output order; push REVERSE.
5. **Flatten iterables/Set/Map** — no; only `Array.isArray`.
6. **Mutate source** — non-mutating.
7. **`depth = 0` returns same array** — should be shallow COPY.

---

## 11. Senior follow-ups & variants

### Variant 1 — `flatMap`
`arr.flatMap(fn) === arr.map(fn).flat(1)` — fused single pass.

### Variant 2 — Recursive with explicit stack
Use trampoline pattern (see 09-recursion).

### Variant 3 — Tail-recursive flat
Not optimized in V8 (no TCO); use iterative.

### Variant 4 — Streaming flat
Generator yielding leaves; can stop early.

### Variant 5 — Branded "depth"
Number of flattens; Infinity sentinel; negative treated as 0.

---

## 12. How to think aloud

> "`flat` polyfill must be ITERATIVE because recursive blows stack on deeply-nested input (think AST flattening, adversarial JSON). Spec: default depth `1` (not Infinity!); holes dropped (output dense); non-mutating; only flattens `Array.isArray` children (not Sets/iterables). Approach: stack of `[item, remainingDepth]` pairs; pop LIFO; if array and depth > 0, push children in REVERSE (so pop order matches original order); else push item to result. Initial fill: iterate input reverse, skip holes via `i in O`. Tests: `[1,[2,[3,[4]]]].flat()` = `[1,2,[3,[4]]]`; `.flat(Infinity)` fully flattens; `[1,,2].flat()` = `[1,2]`; `[1,[2]].flat(0)` is shallow copy. Trap: default Infinity (wrong); recursive production (RangeError); forward push (reverses order); preserving holes (drop them); flattening non-arrays (only Array.isArray)."

---

## 13. 60-second revision

> - **Default depth = 1** (not Infinity).
> - **Holes dropped** (output dense).
> - **Iterative stack** — `[item, depth]` pairs.
> - **Push children REVERSE** — preserves output order via LIFO.
> - **`Array.isArray` check** — only arrays flattened.
> - **`depth = 0` → shallow copy.**
> - **Non-mutating.**
> - **`flatMap`** = map + flat(1).
> - **Trap:** default Infinity; recursive blows stack; forward push order; preserve holes.

---

**Related:** [polyfill-reduce.md](./polyfill-reduce.md) · [polyfill-map.md](./polyfill-map.md) · [`09-recursion/flatten-array-simple.md`](../09-recursion/flatten-array-simple.md) · [`09-recursion/flatten-with-depth.md`](../09-recursion/flatten-with-depth.md) · [`09-recursion/flatten-deeply-nested-array.md`](../09-recursion/flatten-deeply-nested-array.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md), [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
