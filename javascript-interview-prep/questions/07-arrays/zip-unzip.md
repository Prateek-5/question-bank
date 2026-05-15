# zip / unzip arrays (Python-style)

## Source
- Canonical lodash `_.zip` / `_.unzip` interview problem (BFE.dev #97, codedamn, GreatFrontEnd).
- Lodash refs: https://lodash.com/docs/4.17.15#zip, https://lodash.com/docs/4.17.15#unzip
- Inspired by Python's `zip()` builtin.

## Why this question matters in interviews
`zip` is the "do you know functional utilities?" filter. It's also a stealth test of: (1) handling variable arity (`...arrays`), (2) **length policy** — stop-at-shortest vs pad-to-longest, (3) **transpose intuition** (zip is matrix transposition), and (4) **`reduce` fluency** (for unzip). Backend candidates use zip-style logic constantly: pairing parallel result arrays, building DataFrame-like structures, batching mixed-source data. Failing to handle the length-mismatch case professionally is a junior tell.

## Concepts involved

### Syntax to lock in
```js
// zip — combine multiple arrays into an array of tuples
zip([1, 2, 3], ['a', 'b', 'c']);
// → [[1, 'a'], [2, 'b'], [3, 'c']]

zip([1, 2, 3], ['a', 'b'], [true, false, true]);
// stop-at-shortest → [[1, 'a', true], [2, 'b', false]]

// unzip — inverse: array of tuples → tuple of arrays
unzip([[1, 'a'], [2, 'b'], [3, 'c']]);
// → [[1, 2, 3], ['a', 'b', 'c']]
```

### Runtime / engine behavior
- `zip` is **matrix transposition**. `m` arrays of `n` elements → `n` arrays of `m` elements.
- Length policy (lodash default): **stop at the shortest input array.** Equivalent to `Math.min(...arrays.map(a => a.length))`. Python's `zip` does the same. `itertools.zip_longest` (Python) and lodash `_.zipWith` with explicit length give the pad-to-longest variant.
- Result is always a new array — pure function. No input mutation.
- For unzip, the natural pattern is `reduce` over the input rows, pushing each column-value into its column array.

### Edge cases (the interview traps)
1. **Mismatched lengths** — what do you do? Stop-at-shortest is the safe default and matches lodash/Python. Document the choice.
2. **Empty input** — `zip()` (no args) → `[]`. `zip([])` → `[]`. `zip([], [1, 2])` → `[]` (shortest is 0).
3. **`unzip([])`** — empty input → empty output `[]`.
4. **Ragged unzip** — `unzip([[1], [2, 3]])`. Should column 1 have a hole at index 0? Lodash returns `[[1, 2], [undefined, 3]]` (fills with undefined). Decide policy.
5. **Sparse arrays** — `zip([1, , 3], [a, b, c])`. The hole becomes `undefined` in the tuple. Most candidates miss this.
6. **TypedArrays** — `zip(new Uint8Array([1,2]), [10,20])` works but result is plain Array of tuples; the TypedArray semantics don't propagate.
7. **`zipWith(iteratee, ...arrays)`** — the lodash variant that lets you transform each tuple. Common follow-up.
8. **zip is its own inverse**: `unzip(zip(...arrs))` recovers `arrs` (if all equal length). Memorize.

## Brute force approach
Manual nested loops:
```js
function zipBrute(...arrays) {
  const len = Math.min(...arrays.map(a => a.length));
  const result = [];
  for (let i = 0; i < len; i++) {
    const tuple = [];
    for (let j = 0; j < arrays.length; j++) {
      tuple.push(arrays[j][i]);
    }
    result.push(tuple);
  }
  return result;
}
```
This is fine — it's actually the optimal pattern, just expressed verbosely. Refactoring to `Array.from` / `map` is style, not algorithm.

## Optimal approach
- **zip**: compute `len = Math.min(...arrays.map(a => a.length))`, then build `result[i] = arrays.map(a => a[i])` for `i in [0, len)`. O(m × n).
- **unzip**: reduce over rows. For each row, push each value into the corresponding column. `acc[j] ??= []; acc[j].push(row[j])`. O(m × n).

Both are O(input size). Can't do better — output is the same size as input.

## Solution (JavaScript)

```js
/**
 * zip — combine N arrays element-wise, stopping at the shortest.
 *
 * zip([1,2,3], ['a','b','c']) → [[1,'a'], [2,'b'], [3,'c']]
 *
 * @param  {...Array} arrays
 * @returns {Array<Array>}
 */
function zip(...arrays) {
  if (arrays.length === 0) return [];
  const len = Math.min(...arrays.map(a => a.length));
  return Array.from({ length: len }, (_, i) =>
    arrays.map(arr => arr[i])
  );
}

/**
 * zipLongest — pad to the longest with a fill value (default undefined).
 * Mirrors Python's itertools.zip_longest.
 */
function zipLongest(arrays, fillValue = undefined) {
  if (arrays.length === 0) return [];
  const len = Math.max(...arrays.map(a => a.length));
  return Array.from({ length: len }, (_, i) =>
    arrays.map(arr => (i < arr.length ? arr[i] : fillValue))
  );
}

/**
 * unzip — inverse of zip. Array of tuples → tuple of arrays.
 *
 * unzip([[1,'a'], [2,'b'], [3,'c']]) → [[1,2,3], ['a','b','c']]
 */
function unzip(tuples) {
  if (tuples.length === 0) return [];
  return tuples.reduce((acc, row) => {
    row.forEach((val, j) => {
      (acc[j] ??= []).push(val);
    });
    return acc;
  }, []);
}

/**
 * zipWith — zip + per-tuple transform.
 *
 * zipWith((a, b) => a + b, [1,2,3], [10,20,30]) → [11,22,33]
 */
function zipWith(fn, ...arrays) {
  return zip(...arrays).map(tuple => fn(...tuple));
}
```

## Step-by-step dry run

Input 1 — equal-length zip:
```js
zip([1, 2, 3], ['a', 'b', 'c'], [true, false, true]);
// arrays.length = 3, lengths = [3,3,3], len = 3
// i=0: arrays.map(a => a[0]) = [1, 'a', true]
// i=1: [2, 'b', false]
// i=2: [3, 'c', true]
// → [[1,'a',true], [2,'b',false], [3,'c',true]]
```

Input 2 — unequal length (stop-at-shortest):
```js
zip([1, 2, 3, 4], ['a', 'b']);
// lengths = [4, 2], len = 2
// i=0: [1, 'a']
// i=1: [2, 'b']
// → [[1,'a'], [2,'b']]
// 3 and 4 are dropped.
```

Input 3 — unzip:
```js
unzip([[1, 'a'], [2, 'b'], [3, 'c']]);
// row=[1,'a']: acc[0]=[1], acc[1]=['a']
// row=[2,'b']: acc[0]=[1,2], acc[1]=['a','b']
// row=[3,'c']: acc[0]=[1,2,3], acc[1]=['a','b','c']
// → [[1,2,3], ['a','b','c']]
```

Input 4 — ragged unzip (the trap):
```js
unzip([[1, 'a'], [2], [3, 'c', true]]);
// row=[1,'a']:   acc[0]=[1], acc[1]=['a']
// row=[2]:       acc[0]=[1,2]                 // acc[1] NOT touched
// row=[3,'c',true]: acc[0]=[1,2,3], acc[1]=['a','c'], acc[2]=[true]
// → [[1,2,3], ['a','c'], [true]]
// Note: acc[1] has only 2 entries (the 'b' row didn't contribute).
// Lodash's _.unzip would fill the gap with `undefined`.
```

Lodash-compatible version requires pre-allocating to max-row-length and filling gaps explicitly. Worth mentioning in the interview.

## Important takeaways

**Syntax to memorize**
- `zip(...arrays)`: `len = Math.min(...arrays.map(a => a.length))`. Build with `Array.from({length: len}, (_, i) => arrays.map(a => a[i]))`.
- `unzip(tuples)`: `reduce((acc, row) => { row.forEach((v, j) => (acc[j] ??= []).push(v)); return acc; }, [])`.
- `unzip(zip(a, b)) === [a, b]` when `a.length === b.length`. Round-trip guarantee.

**Patterns to reuse**
- **Transpose** — zip is exactly matrix transpose. The same code transposes a 2D matrix: `zip(...matrix)`.
- **Parallel array → array of records** — common pattern: `zip(headers, values).map(([h, v]) => ({[h]: v}))` to build objects from CSV-style columns.
- **`Array.from({length: n}, fn)`** — the idiomatic way to build a fixed-size array with computed values. Cleaner than `new Array(n).fill().map(...)`.
- **`??=` shorthand** — `acc[j] ??= []` is the modern way to init-if-missing.

**Common mistakes**
- Returning an empty array for `zip([], [1, 2])` is correct — but make sure your code doesn't crash with `Math.min(...[].map(...))` returning `Infinity` (which then makes `Array.from({length: Infinity})` blow up). Guard `if (arrays.length === 0) return []`.
- Confusing zip with concat: `zip([1,2], [3,4])` is `[[1,3],[2,4]]`, NOT `[1,2,3,4]`.
- Forgetting that zip is its own inverse — useful sanity check during dry-runs.
- Pre-allocating with the wrong length (using max when you want shortest).

**Related questions**
- `array-set-ops` — also operates on multiple arrays.
- Matrix transpose (specific case of zip applied to 2D).
- Python's `zip` / `itertools.zip_longest` / `enumerate` (`zip` with indices is `Object.entries(arr)` cousin).
- `Object.fromEntries(zip(keys, values))` — build object from parallel arrays.

## Variants

1. **`zip_longest` with fill value** — Python-style. Cover above. Trivial change: `Math.max` instead of `Math.min` + fill missing slots.

2. **`zipWith` (lodash)** — "Take a function as the first arg and apply it to each tuple." `zipWith((a, b) => a + b, [1,2], [3,4])` → `[4, 6]`.

3. **`unzipWith`** — inverse of `zipWith`. Less common but symmetric.

4. **Lazy zip with generators** — "What if the inputs are infinite generators?" Pivot to `function* zipGen(...iters) { ... }`, pulling one value from each, stopping when any returns `done`. Tests iterator-protocol knowledge.

5. **Object-zip** — "Zip keys and values into an object: `zipObject(['a','b'], [1,2])` → `{a:1, b:2}`." One-liner: `Object.fromEntries(zip(keys, values))`.

## Revision notes

> **zip / unzip — 60 second recap**
> - `zip(...arrays)` → array of tuples, stops at **shortest** input.
> - `unzip(tuples)` → array of column-arrays. Inverse of zip.
> - Default length policy: **stop-at-shortest** (matches Python and lodash).
> - `zipLongest` pads to the longest with a fill value.
> - `unzip(zip(a, b)) === [a, b]` when lengths match.
> - **Trap:** ragged unzip — lodash fills gaps with `undefined`; naive `reduce` doesn't.
> - **Family:** matrix transpose, `Object.fromEntries(zip(...))`, `zipWith`, `zipObject`.
