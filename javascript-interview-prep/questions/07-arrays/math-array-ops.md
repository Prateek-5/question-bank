# Numeric array ops — min, max, sum, avg, median

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [polyfill-reduce.md](./polyfill-reduce.md)
>
> **Source:** codedamn Math Lab. Universal warm-up.

---

## 1. Problem statement

Implement min, max, sum, avg, median for numeric arrays. Avoid spread for large arrays (stack overflow). Default `sort` stringifies — pass comparator.

**Verification examples**

```js
sum([1, 2, 3]);                                   // 6
avg([1, 2, 3]);                                   // 2
min([3, 1, 5, 2]);                                // 1
max([3, 1, 5, 2]);                                // 5
median([1, 2, 3, 4]);                             // 2.5
median([1, 2, 3]);                                // 2

// Spread trap on large arrays
Math.min(...new Array(200_000).fill(1));         // RangeError on many engines
```

**Constraints**
- `[].sort()` stringifies — pass `(a, b) => a - b` for numerics.
- `Math.min(...arr)` blows stack ~100k+ elements (engine-dependent).
- `Math.min()` (no args) → `Infinity`; max → `-Infinity`.
- NaN poisons Math.min/max.
- Median: sort + middle (or pair average).

---

## 2. Plain-English restatement

Aggregate a numeric array. Use `reduce` with explicit init to handle empty. Avoid spread to Math.min/max on large arrays. Sort with numeric comparator.

---

## 3. Why this matters in interviews

Three idioms in one head: reduce, Math, sort. Trap: spread stack overflow + sort default lex. Backend p50/p95/p99, latency rollups.

---

## 4. Mental model

```
   sum:   reduce((a, b) => a + b, 0)
   avg:   sum / n (guard n>0)
   min:   reduce((a, b) => Math.min(a, b), Infinity)
   max:   reduce((a, b) => Math.max(a, b), -Infinity)
   median:
     sort numerically (a-b)
     mid = floor(n/2)
     n odd:  arr[mid]
     n even: (arr[mid-1] + arr[mid]) / 2

   Spread trap:
     Math.min(...bigArr) → RangeError ~100k+.
     V8 argument limit ~65k-500k.
     Use reduce for unbounded sizes.
   
   sort default:
     [10, 1, 5].sort() → [1, 10, 5]  ← lex on string forms.
     Always pass numeric comparator.
   
   NaN:
     Math.max(1, NaN) → NaN.
     Filter NaN before aggregation.
   
   Empty array:
     reduce with init: returns init.
     Math.min() with no args: Infinity.
     median empty: undefined or throw — decide.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does `Math.min(...bigArr)` throw?
> 2. What does `[10, 1].sort()` return?
> 3. What's median of even-length array?

---

## 6. Brute force — walked through

```js
const min = arr => Math.min(...arr);             // breaks at ~100k+
const sort = arr => arr.sort();                  // lex default!
```

Both subtly wrong for production.

---

## 7. The unlocking insight

> **Reduce with explicit init. Numeric sort `(a,b)=>a-b`. Avoid spread for large arrays. Filter NaN if needed.**

Three properties:

1. **`reduce` with init** — handles empty.
2. **Numeric sort** comparator.
3. **Avoid spread** on large.

---

## 8. Solution (annotated)

```js
function sum(arr) {
  return arr.reduce((a, b) => a + b, 0);                                  // step 1: init 0
}

function avg(arr) {
  if (arr.length === 0) return NaN;                                       // step 2: empty guard
  return sum(arr) / arr.length;
}

function min(arr) {
  if (arr.length === 0) return Infinity;
  return arr.reduce((a, b) => (b < a ? b : a));                           // step 3: no spread, no Math
}

function max(arr) {
  if (arr.length === 0) return -Infinity;
  return arr.reduce((a, b) => (b > a ? b : a));
}

function median(arr) {
  if (arr.length === 0) return undefined;
  const sorted = [...arr].sort((a, b) => a - b);                           // step 4: numeric sort
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2
    ? sorted[mid]                                                          // step 5: odd: middle
    : (sorted[mid - 1] + sorted[mid]) / 2;                                 // step 6: even: pair avg
}

// Percentile (linear interpolation)
function percentile(arr, p) {
  if (arr.length === 0) return NaN;
  const sorted = [...arr].sort((a, b) => a - b);
  const i = (p / 100) * (sorted.length - 1);
  const lo = Math.floor(i), hi = Math.ceil(i);
  if (lo === hi) return sorted[lo];
  return sorted[lo] * (hi - i) + sorted[hi] * (i - lo);
}
```

**Try it yourself**

```js
sum([1, 2, 3, 4]);                                            // 10
avg([1, 2, 3, 4]);                                            // 2.5
min([3, 1, 5, 2]);                                            // 1
max([3, 1, 5, 2]);                                            // 5
median([1, 2, 3, 4]);                                         // 2.5
median([1, 2, 3]);                                            // 2

percentile([1, 2, 3, 4, 5], 50);                              // 3
percentile([1, 2, 3, 4, 5], 95);                              // 4.8
percentile(latencies, 99);                                    // p99

// NaN handling
const arr = [1, NaN, 3];
const clean = arr.filter(x => !Number.isNaN(x));
max(clean);                                                    // 3

// Avoid spread trap
const big = new Array(500_000).fill(1).map((_, i) => Math.random());
// Math.max(...big);  → RangeError on V8
max(big);                                                      // safe

// Single-pass min and max
function minMax(arr) {
  let mn = Infinity, mx = -Infinity;
  for (const x of arr) {
    if (x < mn) mn = x;
    if (x > mx) mx = x;
  }
  return { min: mn, max: mx };
}
```

---

## 9. Step-by-step dry run

```
sum([1, 2, 3, 4]):
  reduce(0, 1) = 1.
  reduce(1, 2) = 3.
  reduce(3, 3) = 6.
  reduce(6, 4) = 10.

median([4, 1, 3, 2]):
  sorted = [1, 2, 3, 4]. n=4 even.
  mid = 2. avg(sorted[1], sorted[2]) = (2+3)/2 = 2.5.

median([4, 1, 3, 2, 5]):
  sorted = [1, 2, 3, 4, 5]. n=5 odd.
  mid = 2. sorted[2] = 3.

Math.min(...bigArr) where len = 500_000:
  Spread expands to 500k function args.
  V8 caps args ~65k-500k → RangeError.
  
  vs reduce: O(n) but no spread. No limit.

[10, 1, 5].sort():
  Default stringifies: "10", "1", "5".
  Compare as strings: "1" < "10" < "5".
  Result: [1, 10, 5]. WRONG numeric order.

[10, 1, 5].sort((a, b) => a - b):
  Numeric: 1, 5, 10. CORRECT.
```

---

## 10. Common confusion + traps

1. **`Math.min(...arr)`** — stack overflow ~100k+.
2. **`[10, 1, 5].sort()`** — lex order.
3. **`Math.min()`** with no args → Infinity.
4. **NaN poisons** Math.min/max.
5. **`reduce` without init** — empty throws (or seed bug).
6. **`median` doesn't mutate** — clone before sort.
7. **Integer overflow** — no in JS (BigInt for huge sums).

---

## 11. Senior follow-ups & variants

### Variant 1 — Percentile
Linear interpolation between adjacent sorted values.

### Variant 2 — Streaming min/max
Single-pass; no storage; or running window (deque).

### Variant 3 — Running variance / stddev
Welford's online algorithm.

### Variant 4 — Median of medians
O(n) selection (theoretical; rarely used).

### Variant 5 — `BigInt` for huge sums
Avoids precision loss; can't use Math directly.

---

## 12. How to think aloud

> "Numeric array ops have two classic traps: (1) `Math.min(...arr)` blows the stack around 100k elements because spread expands to function arguments and engines cap them. Use `reduce((a,b) => b<a ? b : a)` instead — no spread, no limit. (2) `[10, 1, 5].sort()` returns `[1, 10, 5]` because default sort stringifies elements and compares lex — `'1' < '10' < '5'`. Always pass `(a,b)=>a-b` for numerics. Other edges: `Math.min()` with no args returns `Infinity`; NaN poisons Math.min/max — filter first. `median`: clone, sort numerically, middle element (odd) or average of mid pair (even). `percentile`: linear interpolation between adjacent sorted indices. Single-pass `minMax` for both at once. `BigInt` for sums that exceed 2^53. Streaming variance: Welford's online algorithm. Trap: spread on large; default sort; reduce no init (empty throws); NaN poisoning; integer precision past 2^53."

---

## 13. 60-second revision

> - **`reduce` with explicit init.**
> - **Numeric sort:** `(a,b)=>a-b`.
> - **Avoid spread** for large arrays.
> - **`Math.min()` no args → Infinity.**
> - **NaN poisons** — filter first.
> - **`median`:** clone, sort, middle or pair-avg.
> - **`percentile`:** linear interpolation.
> - **Single-pass minMax** for both.
> - **`BigInt`** for huge sums.
> - **Trap:** spread stack overflow; lex sort; NaN; empty no init.

---

**Related:** [polyfill-reduce.md](./polyfill-reduce.md) · [sort-by-multiple-keys.md](./sort-by-multiple-keys.md) · [polyfill-some-every.md](./polyfill-some-every.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
