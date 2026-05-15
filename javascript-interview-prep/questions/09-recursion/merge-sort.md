# Merge sort — divide and conquer

## Source
- Canonical divide-and-conquer interview problem.
- LeetCode #912 "Sort an Array": https://leetcode.com/problems/sort-an-array/
- Topic-page reference: https://www.geeksforgeeks.org/merge-sort/

## Why this question matters in interviews
Merge sort is the **canonical "explain recursion in production" question** at senior interviews. It's the algorithm V8 used as its baseline `Array.prototype.sort` from 2018 (TimSort, which is a merge-sort variant, was adopted in V8 7.0 per the spec stability requirement). Interviewers want three signals: (1) you can write **clean recursive divide**, (2) you understand **stability** and why it matters (sorting users by lastName then firstName, multi-key sorts), and (3) you can explain the `O(n log n)` recurrence `T(n) = 2T(n/2) + O(n)` from first principles. Bonus: merge-sort is the only `O(n log n)` comparison sort that's also stable, which is why it (and TimSort) won the language-spec war over quicksort.

## Concepts involved

### Syntax to lock in

```js
function mergeSort(arr) {
  if (arr.length <= 1) return arr;           // base case
  const mid = arr.length >> 1;               // integer divide
  const left  = mergeSort(arr.slice(0, mid));
  const right = mergeSort(arr.slice(mid));
  return merge(left, right);
}

function merge(left, right) {
  const result = [];
  let i = 0, j = 0;
  while (i < left.length && j < right.length) {
    // <= keeps the LEFT element first on ties → stability
    if (left[i] <= right[j]) result.push(left[i++]);
    else                     result.push(right[j++]);
  }
  // drain whichever side has leftovers
  while (i < left.length)  result.push(left[i++]);
  while (j < right.length) result.push(right[j++]);
  return result;
}
```

### Runtime / engine behavior
- **Time complexity:** `T(n) = 2T(n/2) + O(n)` → `O(n log n)` by the Master Theorem. Holds for worst, average, and best case. There is no "bad input" for merge sort, unlike quicksort.
- **Space:** `O(n)` auxiliary for the `result` buffer at each merge level, plus `O(log n)` recursion stack. Total `O(n)`. **Not in-place.** This is merge-sort's only real weakness vs heap-sort or in-place quicksort.
- **Stability:** preserved by the `<=` comparison in the merge step. If two elements are equal, the one from the left half (lower original index) is emitted first. Flip to `<` and you lose stability.
- **Cache behavior:** sequential reads on both halves, sequential writes to output — very cache-friendly. This is why TimSort (merge-sort variant) outperforms quicksort on real hardware despite quicksort's lower constant factor in pure operation count.
- **V8 specifics:** before V8 7.0 (Oct 2018), `Array.prototype.sort` was QuickSort for arrays > 10 — **unstable**. Lots of legacy code accidentally relied on unstable order. ES2019 mandates stability; V8 now uses TimSort. Knowing this is a senior-tier detail.

### Edge cases
1. **Empty array** — `mergeSort([])` returns `[]`. Base case `length <= 1` covers it.
2. **Single element** — already sorted; base case returns the array as-is. **Returning the same reference** is fine here because the algorithm never mutates the input (we `slice` before recursing).
3. **Already-sorted input** — still `O(n log n)`. Not adaptive. TimSort *is* adaptive (runs detection), which is why it wins on partially-sorted data.
4. **Duplicates** — fine; stability ensures duplicates retain original relative order.
5. **Stability matters in multi-key sorts** — sort by `lastName`, then by `firstName`; on the second pass, equal `firstName` rows must keep `lastName` order. Requires a stable sort. Merge sort is stable; naive quicksort isn't.
6. **`arr.slice(0, mid)`** allocates — this is what makes merge-sort `O(n)` space. An "in-place" merge sort exists (Kronrod's algorithm) but the merge step becomes `O(n²)` time in the worst case; rarely worth the trouble.
7. **Comparator function** — if interviewer passes a `(a, b) => -1|0|1` comparator, use `cmp(left[i], right[j]) <= 0` instead of `<=`. Don't hard-code numeric comparison.

## Brute force approach
Selection sort or bubble sort — `O(n²)` swaps. Mention only to anchor the `O(n log n)` improvement. Insertion sort is worth a real shout-out because TimSort uses it for runs ≤ 32 (small-array constant factor beats merge-sort's allocation overhead).

## Optimal approach
Recursive divide-and-conquer: split the array in half, recursively sort each half, then merge them in linear time. The merge step is the algorithmic core — it's two pointers sweeping in tandem. Always `O(n log n)`, always stable. Two practical concerns: it allocates `O(n)` extra memory (use in-place quicksort if memory-constrained) and the recursion depth is `log₂(n)` (~20 frames for n=1M; stack-safe in V8).

## Solution (JavaScript)

```js
/**
 * Stable merge sort. Returns a new sorted array; does not mutate input.
 * Time: O(n log n) — worst, average, best.
 * Space: O(n) auxiliary + O(log n) call stack.
 *
 * @param {number[]} arr
 * @param {(a: any, b: any) => number} [cmp]  comparator: negative → a first
 * @returns {Array}
 */
function mergeSort(arr, cmp = (a, b) => a < b ? -1 : a > b ? 1 : 0) {
  if (arr.length <= 1) return arr.slice();   // copy for caller safety
  const mid = arr.length >> 1;
  const left  = mergeSort(arr.slice(0, mid), cmp);
  const right = mergeSort(arr.slice(mid),    cmp);
  return merge(left, right, cmp);
}

function merge(left, right, cmp) {
  const out = new Array(left.length + right.length);
  let i = 0, j = 0, k = 0;
  while (i < left.length && j < right.length) {
    // <= 0 keeps left-first on ties → stability
    if (cmp(left[i], right[j]) <= 0) out[k++] = left[i++];
    else                              out[k++] = right[j++];
  }
  while (i < left.length)  out[k++] = left[i++];
  while (j < right.length) out[k++] = right[j++];
  return out;
}

/**
 * Bottom-up iterative merge sort — no recursion, useful when you
 * want to avoid stack frames or you're in a TCO-less engine.
 * Same O(n log n) / O(n).
 */
function mergeSortIterative(arr, cmp = (a, b) => a - b) {
  const n = arr.length;
  let buf = arr.slice();
  let tmp = new Array(n);
  for (let width = 1; width < n; width *= 2) {
    for (let lo = 0; lo < n; lo += 2 * width) {
      const mid = Math.min(lo + width, n);
      const hi  = Math.min(lo + 2 * width, n);
      let i = lo, j = mid, k = lo;
      while (i < mid && j < hi) {
        if (cmp(buf[i], buf[j]) <= 0) tmp[k++] = buf[i++];
        else                          tmp[k++] = buf[j++];
      }
      while (i < mid) tmp[k++] = buf[i++];
      while (j < hi)  tmp[k++] = buf[j++];
    }
    [buf, tmp] = [tmp, buf];                 // swap buffers — no copy
  }
  return buf;
}
```

## Step-by-step dry run

Input: `mergeSort([5, 2, 4, 6, 1, 3])`.

Divide tree (only structure shown):
```
              [5, 2, 4, 6, 1, 3]
              /                 \
        [5, 2, 4]              [6, 1, 3]
        /      \                /      \
      [5]    [2, 4]           [6]    [1, 3]
              /  \                    /  \
            [2]  [4]                [1]  [3]
```

Merge phase (bottom-up):
- `merge([2], [4])` → compare 2 ≤ 4 → take 2; drain → `[2, 4]`.
- `merge([5], [2, 4])` → 5 ≤ 2? no → take 2. 5 ≤ 4? no → take 4. Drain → `[2, 4, 5]`.
- `merge([1], [3])` → `[1, 3]`.
- `merge([6], [1, 3])` → 6 ≤ 1? no → take 1. 6 ≤ 3? no → take 3. Drain → `[1, 3, 6]`.
- `merge([2, 4, 5], [1, 3, 6])` →
  - 2 ≤ 1? no → take 1. Out: `[1]`.
  - 2 ≤ 3? yes → take 2. Out: `[1, 2]`.
  - 4 ≤ 3? no → take 3. Out: `[1, 2, 3]`.
  - 4 ≤ 6? yes → take 4. Out: `[1, 2, 3, 4]`.
  - 5 ≤ 6? yes → take 5. Out: `[1, 2, 3, 4, 5]`.
  - Drain right → `[1, 2, 3, 4, 5, 6]`.

Total comparisons: 11 for n=6. The bound `n log n` gives ~15 — actual is within a small constant.

## Important takeaways

**Syntax to memorize**
- Base case `arr.length <= 1` — not `=== 0`.
- `const mid = arr.length >> 1` — integer divide via bit shift (also fine: `Math.floor(arr.length / 2)`).
- Merge step is **two pointers** sweeping; never `splice` or `shift` from the inputs (both are `O(n)` — would push merge to `O(n²)`).
- `<=` in merge for **stability**. Flipping to `<` quietly breaks it.

**Patterns to reuse**
- **Divide-and-conquer skeleton** — split / recurse / combine. Same shape as quicksort, FFT, Strassen matrix multiply, closest-pair-of-points, count-inversions, parallel reduce.
- The merge step is the same code as **merge k sorted lists** (LC #23) — just use a min-heap when k > 2.
- Counting inversions (LC #493) is a one-line tweak of merge: add `result += mid - i` whenever you take from the right half.
- External merge sort (sorting data larger than RAM) is the same algorithm with chunks read from disk — backend essentials.

**Common mistakes**
- Using `arr.shift()` instead of an index — turns each merge from `O(n)` to `O(n²)`.
- Forgetting the second `while` drain loop — leaves the longer half's tail unwritten.
- Using `<` instead of `<=` in merge → unstable sort (matters for multi-key).
- Claiming `O(1)` space — it's `O(n)` because of the merge buffer. In-place merge sort exists but is impractical (O(n²) merge or huge constants).
- Saying "merge sort is faster than quicksort." It isn't on random data — quicksort has lower constants. Merge sort wins on **stability**, **worst-case guarantee**, and **external/parallel scenarios**.

**Related questions**
- Quick sort (`09-recursion/quick-sort.md`) — sister algorithm; trade-offs go the other way.
- Merge k sorted lists / files (external sort).
- Count inversions (Kendall tau distance).
- Stability discussion in `07-arrays/stable-sort-discussion.md`.

## Variants

1. **In-place merge sort** — Kronrod's algorithm achieves `O(1)` extra space but the merge becomes `O(n²)` worst-case or requires complex block-rotation. Mention as a curiosity; never write in interview.

2. **Bottom-up iterative merge sort** — no recursion (provided in the solution). Useful in environments with shallow stacks or when you want predictable allocations.

3. **TimSort** — V8's actual sort. Detects existing "runs" of sorted data, switches to insertion sort for short runs (≤ 32), then merges runs with galloping. Adaptive: `O(n)` on already-sorted input, `O(n log n)` worst-case, stable.

4. **Parallel merge sort** — divide step is trivially parallel; spawn worker threads on the two halves, join at merge. Real win on multi-core; backend interview gold for "how would you sort 100 GB?"

5. **External merge sort** — split input into RAM-sized chunks, sort each, write to temp files, then k-way merge with a heap. The way databases sort.

## Revision notes

> **merge sort — 60 second recap**
> - Divide-and-conquer: split, recurse, **merge**.
> - Time: **`O(n log n)`** worst / avg / best. Recurrence `T(n) = 2T(n/2) + O(n)`.
> - Space: **`O(n)`** auxiliary, **`O(log n)`** stack.
> - **Stable** — `<=` in merge keeps left-first on ties.
> - V8's `Array.prototype.sort` uses **TimSort** (merge-sort variant) since v7.0, Oct 2018. ES2019 mandates stability.
> - **Trap 1:** `<` in merge → unstable.
> - **Trap 2:** `shift()` in merge → `O(n²)`. Use index pointers.
> - Family: quicksort (sister), merge-k-sorted-lists, count-inversions, external/parallel sort.
> - Beats quicksort on **stability**, **worst-case guarantee**, and **external/parallel** scenarios. Loses on constant factor for random in-RAM data.
