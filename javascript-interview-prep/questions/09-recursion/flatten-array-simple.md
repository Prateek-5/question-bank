# Implement single-level `flatten(arr)` — one level of nesting

## Source
- codedamn "Flatten Array" lab: https://codedamn.com/problem/Bj6pjjD2gkDYOUVMrDywr
- Equivalent to `Array.prototype.flat()` with default depth = 1.

## Why this question matters in interviews
This is the **opener** — interviewers ask single-level flatten to gauge whether you reach for recursion or iteration when no recursion is needed. The whole point: **don't over-engineer**. A single-level flatten is just a `for-of` plus `push`/`push(...)`. Many candidates panic and write a recursive solution that flattens to infinite depth, then get docked for not reading the prompt. As a backend engineer you'll write this when expanding chunked DB results: `chunks.flat()` to get back a flat row list.

## Concepts involved

### Syntax to lock in
```js
// Native — what we're re-implementing
[1, [2, 3], [4, [5]]].flat();   // [1, 2, 3, 4, [5]]  — only ONE level peeled off
```

```js
function flatten(arr) {
  const out = [];
  for (const item of arr) {
    if (Array.isArray(item)) {
      for (const x of item) out.push(x);   // peel exactly one level
    } else {
      out.push(item);
    }
  }
  return out;
}
```

### Runtime / engine behavior
- This is **non-recursive**. No call stack worries. O(n) time, O(n) output space.
- `Array.prototype.concat` and the spread operator both flatten exactly one level: `[].concat([1, [2, [3]]])` → `[1, [2, [3]]]`. That makes a one-liner version trivial.
- Spread (`[...a, ...b]`) allocates a new array each time — fine for short inputs, bad in a hot loop.
- The reduce one-liner `arr.reduce((a, b) => a.concat(b), [])` reads cleanly but allocates a new array on every iteration → O(n²) in the worst case (each `concat` copies the accumulator). Mention this trade-off.

### Edge cases (interview traps)
1. **Non-array items at the top level** — `flatten([1, 2, 3])` should return `[1, 2, 3]`, not throw. Cover the base case.
2. **Empty arrays** — `flatten([])` → `[]`. `flatten([[]])` → `[]`. `flatten([[], [1]])` → `[1]`.
3. **Deeper nesting stays nested** — `flatten([1, [2, [3]]])` → `[1, 2, [3]]`, NOT `[1, 2, 3]`. The interviewer is watching for this.
4. **Sparse arrays** — `flatten([1, , 3])` should produce `[1, 3]` if matching native semantics. Use `for (let i in arr)` or `for (let i = 0; i < arr.length; i++) if (i in arr)`.
5. **Don't mutate input** — build a new array.
6. **`null` / `undefined` items** — not arrays; push as-is.

## Brute force approach
The brute force IS the optimal here. No clever trick. The over-engineering trap is to write a recursive deep-flatten when only one level is asked for. Read the prompt; ask "single-level or full?" out loud.

## Optimal approach
Linear walk, conditional push or spread. O(n). The reduce/concat one-liner is acceptable for code-review style but call out the O(n²) concat-allocation cost.

## Solution (JavaScript)

```js
/**
 * Flatten exactly one level of nesting.
 * @param {Array} arr
 * @returns {Array}
 */
function flatten(arr) {
  const out = [];
  for (let i = 0; i < arr.length; i++) {
    if (!(i in arr)) continue;        // skip holes (native flat skips them)
    const item = arr[i];
    if (Array.isArray(item)) {
      for (let j = 0; j < item.length; j++) {
        if (j in item) out.push(item[j]);
      }
    } else {
      out.push(item);
    }
  }
  return out;
}

// One-liner alternatives (mention but explain costs)
const flattenSpread = (arr) => [].concat(...arr);
const flattenReduce = (arr) => arr.reduce((a, b) => a.concat(b), []);
```

`[].concat(...arr)` is the cleanest. It spreads `arr` as concat arguments — and `concat` flattens its array arguments exactly one level. Works because `concat` was designed for this. Caveat: if `arr` has 100k+ elements, the spread can hit the argument-count limit (V8 ~65k); fall back to the loop.

## Step-by-step dry run

Input:
```js
flatten([1, [2, 3], [4, [5, 6]], 7]);
```

Trace:
- `i=0`, item=`1` → not array → `out=[1]`
- `i=1`, item=`[2, 3]` → array → push `2`, `3` → `out=[1, 2, 3]`
- `i=2`, item=`[4, [5, 6]]` → array → push `4`, then push `[5, 6]` **as-is** (single level only) → `out=[1, 2, 3, 4, [5, 6]]`
- `i=3`, item=`7` → not array → `out=[1, 2, 3, 4, [5, 6], 7]`

Return `[1, 2, 3, 4, [5, 6], 7]`. The `[5, 6]` stays nested. That's the whole point.

## Important takeaways

**Syntax to memorize**
- `[].concat(...arr)` — the one-line single-level flatten.
- `for-of` + `Array.isArray` check + push/spread — the explicit version.
- Native: `arr.flat()` with no argument defaults to depth 1.

**Patterns to reuse**
- "Peel one level" is the same operation that `Array.prototype.concat` performs on its array arguments. Internalize this — it's why `[].concat(a, b, c)` works as a merge.
- Single-level is a specialization of `flat(arr, 1)`. If you've memorized the depth-parameterized version, this is `flat(arr, 1)`.

**Common mistakes**
- Going straight to recursion. The prompt said *one level*. Don't recurse.
- Using `arr.flat(Infinity)` and calling it a day — defeats the polyfill exercise.
- Using `arr.reduce((a, b) => [...a, ...b], [])` — O(n²) due to spread-copy on every step. Spread spreads `b`'s elements one by one through the args list; engine copies `a` into a fresh array each iteration. Acceptable for ≤100 items, awful at scale.
- Forgetting non-array items at the top level — `flatten([1, 2, 3])` shouldn't throw.

**Related questions**
- `flat(arr, depth)` — generalized version (see `flatten-with-depth.md`).
- `flattenDeep(arr)` — fully recursive (see `flatten-deeply-nested-array.md`).
- `chunk(arr, size)` — the inverse: group flat array into sub-arrays of size N.

## Variants

1. **Flatten with a filter** — `flatten(arr, predicate)` only peels arrays where `predicate(item)` is true. Tests function-as-parameter and combining two operations cleanly.

2. **Flatten objects' values** — `Object.values(obj).flat()` style — given `{a: [1, 2], b: [3]}` return `[1, 2, 3]`. Same shape, different traversal entry.

3. **Don't allocate output** — yield items via a generator: `function* flatten(arr) { for (const x of arr) Array.isArray(x) ? yield* x : yield x; }`. Zero intermediate allocation; consumer pulls lazily.

## Revision notes

> **flatten(arr) single-level — 60 second recap**
> - Peel **exactly one level**. Don't recurse.
> - Cleanest: `[].concat(...arr)`. Watch the 65k-arg spread limit.
> - Explicit: `for-of` + `Array.isArray` + push/spread.
> - `arr.reduce((a, b) => a.concat(b), [])` is O(n²) — works but slow.
> - Skip holes with `if (i in arr)` to match native `flat`.
> - O(n) time, O(n) space. No call stack growth.
> - **Trap:** going recursive when only one level was asked for.
