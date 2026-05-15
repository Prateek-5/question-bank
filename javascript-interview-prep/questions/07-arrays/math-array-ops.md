# Numeric Array Operations — `min`, `max`, `sum`, `avg`, `median`

## Source
- codedamn Lab: "JavaScript Math Object Lab" — https://codedamn.com/problem/sJuBtPemiWmWVbQClaxcR
- Canonical interview warm-up that tests `Math` + `reduce` + array idioms together.

## Why this question matters in interviews
This is the "show me you can hold three primitives in your head at once" question. You're expected to deliver clean, idiomatic implementations of `min`, `max`, `sum`, `avg`, and `median` for a numeric array — handle empty input, handle a single-element array, and **not** blow up on huge arrays. The killer trap: `Math.max(...arr)` looks elegant but throws `RangeError: Maximum call stack size exceeded` on arrays around 100k+ elements because spread expands to function arguments. Backend engineers see numeric aggregation everywhere — latency metrics, throughput rollups, p50/p95/p99 calculations on log streams. Knowing the spread-stack trap and `sort`'s string-coercion default is what separates "I use JavaScript" from "I know JavaScript."

## Concepts involved

### The `sort` default behavior trap
```js
[10, 1, 5, 100].sort();   // [1, 10, 100, 5]  ← strings, not numbers
[10, 1, 5, 100].sort((a, b) => a - b);   // [1, 5, 10, 100]
```
`Array.prototype.sort` **stringifies** elements before comparing. `"10" < "5"` lexicographically. Always pass a comparator for numbers. Burn this into muscle memory.

### `Math.min` / `Math.max` and the spread trap
```js
Math.min(1, 2, 3);              // 1 — variadic
Math.min(...arr);                // OK for small arr
Math.min(...bigArr);             // RangeError around 100k–500k elements
```
Spread expands the array into individual function arguments. Engines cap argument count (V8 is roughly 65k–500k depending on version/platform). Use `reduce` instead for unbounded sizes.

Other surprises:
- `Math.min()` with **no args** → `Infinity`.
- `Math.max()` with **no args** → `-Infinity`.
- `Math.max(1, NaN, 3)` → `NaN`. Any NaN poisons the result. Filter first if your data may contain NaN.

### `reduce`-based aggregation idioms
```js
const sum = arr.reduce((a, b) => a + b, 0);
const min = arr.reduce((a, b) => Math.min(a, b), Infinity);
const max = arr.reduce((a, b) => Math.max(a, b), -Infinity);
```
O(n), constant stack depth, no spread. Pass an explicit initial value so `reduce` doesn't throw on empty arrays.

### Median requires sorting
- Sort numerically (`.toSorted((a,b) => a - b)` in ES2023 to avoid mutating input, or `[...arr].sort(...)`).
- Odd length → middle element. Even length → average of the two middle elements.
- O(n log n) — there's a faster O(n) algorithm (quickselect / median-of-medians) but interviewers rarely require it unless they ask explicitly.

### Floating-point caveat
`avg = sum / n` can drift on huge arrays (sum overflows precision past 2^53). For ironclad accuracy, use **Welford's online algorithm**. Mention this for senior-level bonus.

## Brute force approach
Spread into `Math` calls and use the default `sort`:
```js
const min = Math.min(...arr);
const max = Math.max(...arr);
const sum = arr.reduce((a, b) => a + b);   // no initial — throws on empty
const avg = sum / arr.length;              // NaN on empty
const median = arr.sort()[Math.floor(arr.length/2)];  // WRONG: string sort + mutates input
```
Three bugs in five lines: spread blows the stack at scale, no-initial `reduce` throws on `[]`, default `sort` returns lexicographic order, and `arr.sort()` mutates the caller's array.

## Optimal approach
- `min`/`max`/`sum`: single-pass `reduce` with explicit initial values (`Infinity`, `-Infinity`, `0`).
- `avg`: `sum / n`, guard `n === 0`.
- `median`: `[...arr].sort((a,b)=>a-b)`, then index. Never mutate the input.

## Solution (JavaScript)

```js
function min(arr) {
  if (arr.length === 0) return undefined;
  return arr.reduce((a, b) => (a < b ? a : b));   // no spread → safe on huge arrays
}

function max(arr) {
  if (arr.length === 0) return undefined;
  return arr.reduce((a, b) => (a > b ? a : b));
}

function sum(arr) {
  return arr.reduce((a, b) => a + b, 0);          // initial 0 → empty returns 0
}

function avg(arr) {
  if (arr.length === 0) return NaN;               // mirror Math semantics
  return sum(arr) / arr.length;
}

function median(arr) {
  if (arr.length === 0) return undefined;
  const sorted = [...arr].sort((a, b) => a - b);   // non-mutating + numeric compare
  const n = sorted.length;
  const mid = n >> 1;                              // floor(n/2)
  return n % 2 === 1
    ? sorted[mid]
    : (sorted[mid - 1] + sorted[mid]) / 2;
}
```

## Step-by-step dry run

Input: `arr = [4, 1, 7, 3, 9, 2]`.

**min**
- `reduce` with no initial → seed `acc=4`, start at index 1.
- `i=1`: `1 < 4` → `acc=1`. `i=2`: `7<1` no. `i=3`: `3<1` no. `i=4`: `9<1` no. `i=5`: `2<1` no.
- Return `1`.

**sum**
- `acc=0`; iter: 4, 5, 12, 15, 24, 26. Return `26`.

**avg**
- `26 / 6 = 4.333...`. Return `4.333...`.

**median**
- `sorted = [1, 2, 3, 4, 7, 9]`. `n=6`, even. `mid=3`. Return `(sorted[2] + sorted[3]) / 2 = (3 + 4) / 2 = 3.5`.
- Verify: original `arr` is **unchanged** — `[...arr].sort` created a fresh copy.

Edge runs:
- `min([])` → `undefined`. `sum([])` → `0`. `avg([])` → `NaN`. `median([])` → `undefined`.
- `min([5])` → `reduce` with single element + no initial returns it directly. → `5`. Same for `max`, `median`.
- `max([1, NaN, 3])` with `Math.max` would be `NaN`; with the `(a > b ? a : b)` reducer, `NaN > x` is always false, so `NaN` slips through depending on order. **If NaN may appear, filter first:** `arr.filter(Number.isFinite)`.

## Important takeaways

**Syntax to memorize**
- `arr.reduce((a, b) => a + b, 0)` — sum with safe initial.
- `[...arr].sort((a, b) => a - b)` — numeric sort, non-mutating.
- `n >> 1` — fast floor-divide-by-2. Equivalent to `Math.floor(n / 2)` for non-negative integers.

**Patterns to reuse**
- Replace `Math.max(...arr)` with `arr.reduce((a, b) => Math.max(a, b), -Infinity)` whenever array size is unbounded. Same for `Math.min`.
- Always provide an explicit initial value to `reduce` unless you genuinely want first-element-as-seed semantics.

**Common mistakes**
- `arr.sort()[mid]` — string sort, wrong result, also mutates input.
- `Math.max(...arr)` on large arrays — `RangeError`. Real production bug pattern.
- `avg([]) === 0` — wrong; division by 0 is `NaN`. Decide the contract and document it.
- Forgetting that `NaN` poisons comparisons. `NaN < anything` and `NaN > anything` are both false.
- Using `arr.reduce((a, b) => a + b)` without an initial on potentially empty arrays — throws.

**Related questions**
- p95 / p99 from a latency array (sort then `arr[Math.floor(0.95 * n)]`).
- Variance + standard deviation (Welford's algorithm for numerical stability).
- Rolling window min/max with a deque (monotonic queue) — O(n) instead of O(n log n).

## Variants

1. **Streaming aggregator** — `Math.min`/`max`/`sum`/`count` updated on each push, no array stored. Use a class with `add(x)` and `value()` methods. Common for log-processing problems.
2. **Welford online mean + variance** — numerically stable single-pass: `mean += (x - mean) / n; M2 += (x - mean_old) * (x - mean_new);`. Pulled out in any senior data-eng interview.
3. **Percentile** — generalize `median` to `quantile(arr, q)`. Indexing: `sorted[Math.floor(q * (n - 1))]` (nearest-rank) vs linear-interpolation (R-7 method). Clarify with interviewer.

## Revision notes

> **Numeric array ops — 60 second recap**
> - `Math.max(...arr)` blows the stack around 100k elements. Use `arr.reduce((a,b)=>a>b?a:b, -Infinity)`.
> - `arr.sort()` **stringifies**. ALWAYS pass `(a, b) => a - b` for numeric sort.
> - `[...arr].sort(...)` to avoid mutating; or ES2023 `arr.toSorted(...)`.
> - `sum`: `reduce((a,b)=>a+b, 0)` — initial 0 means `sum([]) === 0`.
> - `avg([])` → `NaN`. `min([])`/`max([])`/`median([])` → `undefined`. Pick contracts and document.
> - `median`: sort first, even length → average two middle elements.
> - `NaN` poisons `>`/`<` comparisons; filter with `Number.isFinite` if dirty data is possible.
> - Big-O: min/max/sum O(n); median O(n log n); quickselect O(n) average.
> - **Trap:** mutating input via `.sort()` without spreading. Burns callers.
> - **Trap:** `Math.min()` with no args → `Infinity`; `Math.max()` → `-Infinity`. Test your guards.
