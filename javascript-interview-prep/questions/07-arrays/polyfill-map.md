# Polyfill `Array.prototype.map`

## Source
- Canonical interview problem (BFE.dev #14, GreatFrontEnd, Frontend Masters).
- Companion to LeetCode #2635 "Apply Transform Over Each Element in Array" — https://leetcode.com/problems/apply-transform-over-each-element-in-array/

## Why this question matters in interviews
If `reduce` tests "do you understand folds," `map` tests "do you understand the **hole-preserving contract**" — which is more subtle than candidates realize. The native `map` does something almost unique among array methods: it **skips holes when calling the callback, but preserves them in the output**. `[1, , 3].map(x => x * 2)` → `[2, <1 empty slot>, 6]`, not `[2, undefined, 6]` and not `[2, 6]`. Getting this exactly right is the differentiator. You'll also be probed on `thisArg`, the three callback args (`value`, `index`, `array`), and non-mutation. As a backend engineer, `map` is your transform primitive — every ETL stage, every projection, every "deserialize each row" is a `map`. Owning the spec means you don't get burned by sparse data or `this`-binding bugs.

## Concepts involved

### Syntax to lock in
```js
arr.map(callback, thisArg);
// callback(value, index, array) -> mappedValue
```

### Spec details that win you the round
1. **Hole-preserving output.** Output array has the same `length` as input. Indices that were holes in the input remain holes in the output — not `undefined`. The way to do this in the polyfill: **don't assign** at those indices, then explicitly set `result.length = len` at the end (or pre-create with `new Array(len)`).
2. **Skip holes when calling the callback** — use `i in this`. Native `map` does NOT invoke the callback for missing indices.
3. **`thisArg` binds `this` inside the callback** — `callback.call(thisArg, ...)`. Forgotten constantly.
4. **Length captured up front.** Pushes during iteration don't extend the loop.
5. **Three args passed:** `(value, index, originalArray)`. Forgetting `index` breaks predicates like `(v, i) => v + i`.
6. **Non-mutating.** Returns a fresh array. Source untouched.

### Why output holes matter
```js
const a = [1, , 3];           // length 3, hole at index 1
const native = a.map(x => x * 2);
console.log(native);           // [2, <1 empty slot>, 6]
console.log(native.length);    // 3
console.log(1 in native);      // false  ← hole, not undefined
console.log(native[1]);        // undefined (because hole reads as undefined)
```
If your polyfill does `result.push(undefined)` for holes, `1 in result` becomes `true` and you've broken the contract. Subtle, but every spec-test suite catches it.

### Mutating vs non-mutating
`map` is non-mutating, just like `filter`, `slice`, `concat`, `flat`. Contrast with `forEach` (also non-mutating but returns `undefined`) and the mutating family `push`/`pop`/`shift`/`unshift`/`splice`/`sort`/`reverse`/`fill`/`copyWithin`.

### Code-smell aspect
`Array.prototype.myMap = ...` pollutes every array, and naive assignment makes the method **enumerable** — meaning `for...in arr` will surface `myMap` as a key. Use `Object.defineProperty(Array.prototype, 'myMap', { enumerable: false, writable: true, configurable: true, value: fn })` to keep it hidden. This is exactly why the SmooshGate (`Array.prototype.flatten` → `flat`) happened.

## Brute force approach
A `for` loop that `result.push(callback(this[i], i, this))` for every `i`. Three flaws:
- Invokes the callback on holes (passes `undefined`).
- Produces a dense output (no holes preserved).
- Ignores `thisArg`.

Brute force fails the official spec tests. Interviewers will reach for `[1, , 3]` and watch your output.

## Optimal approach
Pre-allocate `new Array(len)`. Loop `i = 0..len-1`. If `i in this`, call `callback.call(thisArg, value, i, this)` and **assign** to `result[i]`. If `i` is a hole, skip — the slot in the pre-allocated array stays a hole automatically. Set `result.length = len` at the end for safety (handles edge cases where assignments only set lower indices).

## Solution (JavaScript)

```js
Object.defineProperty(Array.prototype, 'myMap', {
  value: function (callback, thisArg) {
    if (typeof callback !== 'function') {
      throw new TypeError(callback + ' is not a function');
    }

    const len = this.length >>> 0;       // ToUint32
    const result = new Array(len);        // pre-allocate; slots are holes by default

    for (let i = 0; i < len; i++) {
      if (i in this) {                    // skip holes — don't even call cb
        result[i] = callback.call(thisArg, this[i], i, this);
      }
      // else: leave result[i] as a hole
    }
    return result;
  },
  writable: true,
  configurable: true,
  enumerable: false,                       // critical: don't break for...in
});
```

## Step-by-step dry run

Input:
```js
const arr = [10, , 20];
const out = arr.myMap(function (v, i) {
  return v * this.factor + i;
}, { factor: 3 });
```

Trace:
- `len = 3`. `result = new Array(3)` → `[<empty>, <empty>, <empty>]`.
- `i=0`: `0 in arr` → true. `value=10`. `cb.call({factor:3}, 10, 0, arr)` → `10*3 + 0 = 30`. `result[0] = 30`.
- `i=1`: `1 in arr` → **false** (hole). Skip. `result[1]` stays a hole.
- `i=2`: `value=20`. `20*3 + 2 = 62`. `result[2] = 62`.
- Return `[30, <empty>, 62]`. Length 3. `1 in result === false`.

Compare to a brute-force polyfill that uses `push`:
- It would produce `[NaN, NaN, 62]` (since `undefined * 3 + i = NaN`) and have `1 in result === true`. Wrong on two axes.

Edge run — empty array:
- `[].myMap(x => x)` → `len=0`, loop doesn't execute. Returns `[]` (new empty array, NOT the original).

Edge run — fully sparse:
- `new Array(3).myMap(x => x * 2)` → length 3, callback never runs, returns `[<empty>, <empty>, <empty>]`. Matches native.

## Important takeaways

**Syntax to memorize**
- `new Array(len)` pre-allocates a sparse array of the right length. Use indexed assignment, not `push`, to preserve holes.
- `callback.call(thisArg, value, i, this)` — three args, with `thisArg`.
- `i in this` for hole detection.

**Patterns to reuse**
- "Pre-allocate + indexed assign" is the only way to preserve holes. Same pattern in any polyfill that mirrors `map`'s output shape (e.g., a hole-preserving `mapAsync`).
- `Object.defineProperty(..., { enumerable: false })` is the SmooshGate-safe way to extend prototypes.

**Common mistakes**
- Using `push` — produces a dense output, fails the hole-preserving test.
- Forgetting `thisArg` — silent bug in method-style use.
- Calling the callback on holes (passing `undefined`) — wastes work and may throw if the callback isn't `undefined`-safe.
- Skipping `length = len` cleanup when the last index is a hole. In practice `new Array(len)` already sets `length = len`, so this is a sanity belt-and-suspenders. Worth mentioning.

**Related questions**
- Polyfill `filter` (similar, but **doesn't** preserve holes — output is always dense).
- Polyfill `forEach` (no return value; otherwise identical iteration).
- Polyfill `flatMap` (`map` then flatten depth 1 — easy follow-up).
- Async `map` (`Promise.all(arr.map(asyncFn))`) — different concern; talk through sequential vs parallel.

## Variants

1. **`mapAsync` (parallel)** — `Promise.all(arr.map(async (v, i) => ...))`. Common follow-up. Mention the gotcha: rejections short-circuit; use `Promise.allSettled` if you need per-item resilience.
2. **`mapAsync` (sequential)** — `for...of` with `await`. Slower but preserves order and back-pressure. Useful when each call has side effects (DB writes, rate-limited API).
3. **`flatMap` polyfill** — same shape as `map` but if the callback returns an array, splice it in one level. `arr.flatMap(fn) === arr.map(fn).flat(1)`. Spec-wise it's a `map` followed by a depth-1 flatten.

## Revision notes

> **map polyfill — 60 second recap**
> - Signature: `cb(value, i, arr)` + optional `thisArg`.
> - **Pre-allocate** `new Array(len)` to preserve hole positions in the output.
> - Loop `i=0..len-1`; if `i in this`, assign `result[i] = cb.call(thisArg, value, i, this)`.
> - Skip holes — both in callback invocation **and** in output (don't assign).
> - Non-mutating; returns a fresh array.
> - Attach via `Object.defineProperty(..., { enumerable: false })` to avoid breaking `for...in`.
> - Output `length === input.length` always.
> - **Trap:** using `push` → dense output. `[1, , 3].myMap(x=>x*2)` should give `[2, <hole>, 6]`, not `[2, undefined, 6]`.
> - **Trap:** forgetting `thisArg` — breaks `arr.map(fn, this)` from method context.
> - Family: `filter` (doesn't preserve holes — output is always dense), `forEach` (no return), `flatMap` (map + flat 1).
