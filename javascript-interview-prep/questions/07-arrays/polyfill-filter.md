# Polyfill `Array.prototype.filter`

## Source
- LeetCode #2634 "Filter Elements from Array" — https://leetcode.com/problems/filter-elements-from-array/
- Canonical interview problem; appears on BFE.dev, GreatFrontEnd, and most senior front-end / full-stack rounds.

## Why this question matters in interviews
`filter` looks trivial — "just push items where the predicate returns truthy." That's the trap. Interviewers test whether you know it (a) **skips holes**, (b) **accepts a `thisArg`**, (c) **passes `(value, index, array)`** to the predicate, and (d) preserves the original array (non-mutating). It's a tight 15-line polyfill that separates engineers who *use* JS from engineers who *understand* JS. Backend engineers reach for `filter` in every list endpoint — knowing the exact semantics keeps you safe when filtering sparse data structures (e.g., a fixed-size buffer with `undefined` slots vs. a sparse array with holes — they behave differently).

## Concepts involved

### Syntax to lock in
```js
arr.filter(callback, thisArg);
// callback(value, index, array) -> truthy/falsy
```

### Spec details that matter
1. **Holes are skipped** — predicate is *not* called on missing indices. `[1, , 3].filter(() => true)` returns `[1, 3]`, length 2, **dense** (no preserved hole).
2. **`thisArg` binds `this` inside the predicate.** Polyfills miss this constantly. `callback.call(thisArg, ...)` is the fix.
3. **The result is always a new dense array.** No mutation, no shared reference.
4. **Length is captured up front.** Items pushed during iteration are not visited.
5. The output array preserves **relative order** of kept items.
6. Predicate receives `(value, index, originalArray)` — three args. Forgetting `index` breaks predicates like `(v, i) => i % 2 === 0`.

### Mutating vs non-mutating
`filter` is non-mutating. Sits in the same family as `map`, `slice`, `concat`, `flat`, `toSorted`/`toReversed` (ES2023). Compare against the mutating family: `push`, `pop`, `shift`, `unshift`, `splice`, `sort`, `reverse`, `fill`, `copyWithin`. Knowing which is which prevents a class of "why is my source array changed?" bugs.

### Code-smell aspect
Attaching to `Array.prototype` pollutes the global. Use `Object.defineProperty` with `enumerable: false` so `for...in` loops on arrays don't pick up `myFilter`. In production you'd ship a standalone helper instead, but the interview wants the prototype version to test `this` handling.

## Brute force approach
A `for` loop that does `if (callback(this[i], i, this)) result.push(this[i])`. Works for dense arrays with no `thisArg`. Fails three spec tests:
- Sparse arrays — predicate gets called with `undefined` for holes.
- `thisArg` is ignored.
- Some candidates use `forEach`, which is fine for dense arrays but can't access the third callback `array` argument cleanly and obscures the `this`-binding question.

## Optimal approach
Single pass, O(n). Skip holes via `i in this`. Forward `(value, index, array)` to the callback. Use `callback.call(thisArg, ...)` to honor `thisArg`. Cache `length` once. Push into a fresh result array.

## Solution (JavaScript)

```js
Object.defineProperty(Array.prototype, 'myFilter', {
  value: function (callback, thisArg) {
    if (typeof callback !== 'function') {
      throw new TypeError(callback + ' is not a function');
    }

    const len = this.length >>> 0;             // ToUint32
    const result = [];

    for (let i = 0; i < len; i++) {
      if (i in this) {                          // skip holes
        const value = this[i];
        if (callback.call(thisArg, value, i, this)) {
          result.push(value);
        }
      }
    }
    return result;
  },
  writable: true,
  configurable: true,
  enumerable: false,
});
```

## Step-by-step dry run

Input:
```js
const arr = [1, , 2, 3, 4];                    // hole at index 1, length 5
const ctx = { threshold: 2 };
const out = arr.myFilter(function (v) {
  return v > this.threshold;
}, ctx);
```

Trace:
- `len = 5`, `result = []`.
- `i=0`: `0 in arr` → true. `value=1`. `cb.call(ctx, 1, 0, arr)` → `this.threshold=2`, `1>2` → false. Skip.
- `i=1`: `1 in arr` → **false** (hole). Skip entirely; predicate never runs.
- `i=2`: `2 in arr` → true. `value=2`. `2>2` → false. Skip.
- `i=3`: `value=3`. `3>2` → true. `result.push(3)` → `[3]`.
- `i=4`: `value=4`. `4>2` → true. `result.push(4)` → `[3, 4]`.
- Return `[3, 4]`. Length 2, dense.

Compare against the broken brute force (no `i in this` guard): it would call the predicate at `i=1` with `value=undefined`, which throws if `this.threshold` access chains anything, or silently passes if the predicate tolerates undefined. Either way: wrong.

## Important takeaways

**Syntax to memorize**
- `callback.call(thisArg, value, i, this)` — three args + `thisArg` binding. Memorize this exact line.
- `i in this` is the hole check. `this[i] !== undefined` is **wrong** (legitimate `undefined` entries would be skipped).
- Push to a new array; never mutate `this`.

**Patterns to reuse**
- The `i in this` hole guard appears in `map`, `forEach`, `reduce`, `some`, `every`. Same idiom every time.
- `callback.call(thisArg, ...)` is the standard pattern for any prototype helper that documents a `thisArg`.

**Common mistakes**
- Forgetting to forward `index` and `array` to the predicate.
- Using `Array.from({length})` and indexing — overkill; just `push`.
- Treating sparse `undefined` and a hole as the same thing. They're not — `arr[i] === undefined` can be true for a present `undefined` *or* an absent slot.

**Related questions**
- Polyfill `map` (same skeleton, but assigns to indexed result instead of pushing — and result must preserve length, not pack down).
- Polyfill `some` / `every` (short-circuit returns).
- Implement `filter` on a Set or Map (no holes, but `thisArg` semantics still matter).

## Variants

1. **`filterMap`** — combine filter + map in one pass. Return `[true, mappedValue]` or `false` from the callback. Common follow-up; one less iteration over large arrays.
2. **Async filter** — predicate returns a Promise. Sequential vs parallel implementations are different problems; clarify with the interviewer.
3. **Filter with `findIndex`-style early exit** — not part of the spec, but a fun extension: return the first N matches.

## Revision notes

> **filter polyfill — 60 second recap**
> - Signature: `cb(value, i, arr)` + optional `thisArg`.
> - Skip holes with `if (i in this)`.
> - Bind `this` in predicate via `callback.call(thisArg, ...)`.
> - Returns a **new dense array** — original untouched.
> - Cache `length` once with `>>> 0`.
> - Attach via `Object.defineProperty(..., { enumerable: false })` so `for...in` stays sane.
> - Family member of non-mutating methods: `map`, `slice`, `concat`, `flat`, `toSorted`.
> - **Trap:** equating "hole" with `=== undefined`. Use `i in this` only.
> - **Trap:** ignoring `thisArg` — silent bug in `obj.method = arr.filter(predicate, this)`.
