# Polyfill `Array.prototype.reduce`

## Source
- LeetCode #2626 "Array Reduce Transformation" — https://leetcode.com/problems/array-reduce-transformation/
- Canonical interview problem (BFE.dev #18, Frontend Masters, GreatFrontEnd).

## Why this question matters in interviews
`reduce` is the most powerful and most misunderstood array method. Asking you to reimplement it tests four things at once: **closures over an accumulator**, **handling the "no initial value" edge case** (which silently shifts the start index by 1), **sparse-array hole semantics**, and the discipline to throw `TypeError` on the empty-no-initial case. Senior backend engineers fold/aggregate data constantly — event aggregation, log rollups, RPC fan-in. If you can re-derive `reduce`, you can re-derive every group-by, sum-by, index-by helper you'll ever need. It's also the warm-up before harder ones like `flat` and `groupBy`.

## Concepts involved

### Syntax to lock in
```js
// Spec signature
arr.reduce(callback, [initialValue]);
// callback(accumulator, currentValue, currentIndex, array)
```

### The spec rules people forget
1. **No `initialValue`** → accumulator starts as the **first defined element**, and iteration begins at the index *after* it. Crucial nuance: if `arr` is sparse like `[, , 3, 4]`, the first defined element is `3` at index 2, so iteration starts at index 3.
2. **Empty array + no `initialValue`** → throw `TypeError("Reduce of empty array with no initial value")`. Real spec text.
3. **Holes are skipped.** `[1, , 3].reduce(fn, 0)` only invokes `fn` twice, not three times. Use `if (i in this)` — NOT `this[i] !== undefined` (which mis-skips legitimate `undefined` entries).
4. **Length is read once at the start.** Pushing during reduce does *not* extend the iteration.
5. The fourth callback argument is the **original array** (`this` inside the polyfill).

### Code-smell warning
Adding to `Array.prototype` pollutes every array in the runtime and can break `for...in` loops (which enumerate prototype props by default). Mitigate with `Object.defineProperty(..., { enumerable: false })`. In production code, prefer a standalone function — but interviewers explicitly want the prototype attachment to test your understanding of `this` binding.

## Brute force approach
A `for` loop that always starts at `i = 0` and treats the first call as "use `initialValue` if defined, else `arr[0]`". It works for dense arrays with an initial value, but quietly breaks on:
- Sparse arrays (calls callback on holes with `undefined`).
- No-initial-value case with sparse leading holes (uses `undefined` as the seed).
- Empty array + no init (returns `undefined` instead of throwing).

Brute force fails the spec tests. Don't ship it.

## Optimal approach
One pass, O(n) time, O(1) extra space. Branch up front on "did the caller pass an initial value?" — that decides the seed and the starting index. Inside the loop, gate the callback on `i in this` so holes are skipped exactly as the spec dictates.

## Solution (JavaScript)

```js
Object.defineProperty(Array.prototype, 'myReduce', {
  value: function (callback, initialValue) {
    if (typeof callback !== 'function') {
      throw new TypeError(callback + ' is not a function');
    }

    const len = this.length >>> 0;          // ToUint32, matches spec
    let i = 0;
    let acc;
    const hasInitial = arguments.length >= 2;

    if (hasInitial) {
      acc = initialValue;
    } else {
      // Find first defined element (skip holes)
      while (i < len && !(i in this)) i++;
      if (i >= len) {
        throw new TypeError('Reduce of empty array with no initial value');
      }
      acc = this[i++];
    }

    while (i < len) {
      if (i in this) {                       // skip holes
        acc = callback(acc, this[i], i, this);
      }
      i++;
    }
    return acc;
  },
  writable: true,
  configurable: true,
  enumerable: false,                          // critical for for...in safety
});
```

## Step-by-step dry run

Input:
```js
const sparse = [10, , 20, 30];   // length=4, indices 0,2,3 present; 1 is a hole
sparse.myReduce((a, b) => a + b);          // no initial value
```

Trace:
- `len = 4`, `hasInitial = false`.
- Hole-skip loop: `i=0`, `0 in this` → true. `acc = this[0] = 10`. `i = 1`.
- Main loop, `i=1`: `1 in this` → **false** (it's a hole). Skip. `i = 2`.
- `i=2`: `2 in this` → true. `acc = cb(10, 20, 2, sparse) = 30`. `i = 3`.
- `i=3`: `3 in this` → true. `acc = cb(30, 30, 3, sparse) = 60`. `i = 4`.
- Return `60`.

Now with `[].myReduce((a,b)=>a+b)` — empty array, no initial:
- `len = 0`, `hasInitial = false`. Hole-skip loop exits immediately with `i = 0 >= len`. Throws `TypeError`. Matches native behavior.

And `[1, 2, 3].myReduce((a,b)=>a+b, 100)`:
- `acc = 100`, `i = 0`. Three callback invocations: 101, 103, 106. Return `106`.

## Important takeaways

**Syntax to memorize**
- `arguments.length >= 2` is the only reliable way to detect "initial value was passed." Don't use `initialValue === undefined` — the caller might pass `undefined` deliberately.
- `i in this` for hole detection. NOT `this[i] !== undefined` and NOT `Object.prototype.hasOwnProperty.call(this, i)` (the latter works but is slower and noisier).
- `this.length >>> 0` is the ToUint32 coercion the spec mandates. Handles weird length values like negatives or non-integers.

**Patterns to reuse**
- The "branch on `arguments.length` for the seed" pattern reappears in `reduceRight`, `findLast`, and many lodash helpers.
- `Object.defineProperty(..., { enumerable: false })` is the standard way to extend a prototype without breaking enumeration. Same trick the polyfill libraries use.

**Common mistakes**
- Iterating with `forEach` inside the polyfill (cheating + forEach skips holes differently than you might expect; also can't break early).
- Calling `callback.call(undefined, ...)` and assuming `this` inside the callback. The spec leaves callback `this` unbound — don't force it.
- Forgetting the empty + no-init throw. Interviewer will hand you `[].reduce(fn)` and watch your face.

**Related questions**
- Polyfill `map`, `filter`, `forEach`, `flat`, `flatMap`.
- Implement `reduceRight` (start from the end, decrement `i`).
- Implement lodash `_.reduce` which also works on objects (separate file in this bucket).

## Variants

1. **`reduceRight`** — iterate `i = len - 1` down to `0`. Same hole/initial rules but mirrored. Common follow-up.
2. **Async reduce** — `await`-aware version: `for...of` with `await callback(...)`. Becomes a great event-loop question because parallel `Promise.all + map` is *wrong* when reductions are sequential.
3. **`reduce` on object** — lodash variant that iterates `Object.keys(obj)`. Different `this` semantics; see `lodash-reduce.md`.

## Revision notes

> **reduce polyfill — 60 second recap**
> - Signature: `cb(acc, cur, i, arr)`, optional `initialValue`.
> - Detect initial via `arguments.length >= 2` — never `=== undefined`.
> - No initial → seed with first **defined** element (skip leading holes), start loop at next index.
> - Empty array + no initial → throw `TypeError("Reduce of empty array with no initial value")`.
> - Skip holes with `if (i in this)`.
> - Read `length` once, coerce with `>>> 0`.
> - Attach via `Object.defineProperty(Array.prototype, 'myReduce', { enumerable: false })` so `for...in` stays clean.
> - **Trap:** treating `undefined` array entries as holes. They're not — only true holes (missing indices) are skipped.
