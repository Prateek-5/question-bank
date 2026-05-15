# Quick sort with pivot selection

## Source
- Canonical divide-and-conquer interview problem.
- LeetCode #912 "Sort an Array": https://leetcode.com/problems/sort-an-array/
- Reference (Lomuto vs Hoare partition): https://en.wikipedia.org/wiki/Quicksort

## Why this question matters in interviews
Quicksort is the **partition primitive** for everything from `nth_element` to `select` to randomized algorithms. Interviewers ask it because it has a *non-obvious* worst case (already-sorted input with first-element pivot → `O(n²)`) and a *non-obvious* fix (randomized or median-of-3 pivot). The conversation around "why your code is `O(n²)` and how to make it `O(n log n)` expected" is what separates senior candidates. As a backend engineer you'll meet quicksort as the engine behind the C `qsort()` and the standard-library sort in many languages pre-2018, and the partition step shows up in **Quickselect** (LC #215 "Kth Largest Element") — a constant in real interviews.

## Concepts involved

### Syntax to lock in

Lomuto partition (simpler to write, slightly slower constants):

```js
function quickSort(arr, lo = 0, hi = arr.length - 1) {
  if (lo >= hi) return arr;
  const p = partitionLomuto(arr, lo, hi);
  quickSort(arr, lo, p - 1);
  quickSort(arr, p + 1, hi);
  return arr;
}

function partitionLomuto(arr, lo, hi) {
  const pivot = arr[hi];                  // last-element pivot
  let i = lo - 1;
  for (let j = lo; j < hi; j++) {
    if (arr[j] <= pivot) {
      i++;
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }
  [arr[i + 1], arr[hi]] = [arr[hi], arr[i + 1]];   // pivot to its slot
  return i + 1;
}
```

Hoare partition (faster, fewer swaps, but trickier index bookkeeping):

```js
function partitionHoare(arr, lo, hi) {
  const pivot = arr[lo + ((hi - lo) >> 1)];   // middle element
  let i = lo - 1, j = hi + 1;
  while (true) {
    do { i++; } while (arr[i] < pivot);
    do { j--; } while (arr[j] > pivot);
    if (i >= j) return j;
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}
// Then recurse on (lo, j) and (j + 1, hi) — note `j`, not `j-1`.
```

### Runtime / engine behavior
- **Average time:** `O(n log n)` — recurrence `T(n) = 2T(n/2) + O(n)` when pivot splits roughly evenly.
- **Worst time:** `O(n²)` — when pivot is always the min or max (e.g., first-element pivot on already-sorted data). Recurrence degenerates to `T(n) = T(n-1) + O(n)`.
- **Best time:** `O(n log n)` — perfectly balanced splits.
- **Space:** `O(log n)` average recursion depth, `O(n)` worst (degenerate splits). **In-place** — no aux array, unlike merge sort.
- **Not stable** — partition swaps reorder equal elements.
- **Cache behavior:** excellent. Sequential scans with two pointers; tight inner loop. This is why quicksort generally beats merge sort on random in-RAM data despite the same big-O.
- **JS engine note:** V8 *was* quicksort pre-7.0 (Oct 2018) and was therefore unstable. ES2019 mandated stability, V8 switched to TimSort. Quicksort is no longer used by `Array.prototype.sort` but it's still the algorithm you'd implement in interview.

### Pivot strategies (the senior conversation)
1. **First element** — `arr[lo]`. **Worst case: already-sorted input → O(n²).** Don't use.
2. **Last element** — `arr[hi]`. Same worst case (reverse-sorted now). The Lomuto example above uses this; for interview you'd add randomization (next).
3. **Random** — `arr[lo + Math.floor(Math.random() * (hi - lo + 1))]` swapped to the pivot slot. **Expected `O(n log n)` for any input.** The standard defensive choice.
4. **Median-of-3** — take `arr[lo]`, `arr[mid]`, `arr[hi]`, pick the median, swap into the pivot slot. Cheap and reliably good on near-sorted data (which is common in practice). What `qsort` and Java's primitive sort use.
5. **Median-of-medians** — true `O(n)` worst-case pivot selection. `O(n log n)` worst-case sort, but huge constants. Theoretical only — never in interview code.

### Edge cases
1. **Empty / single element** — `lo >= hi` guard handles both.
2. **All equal elements** — Lomuto degrades to `O(n²)` because every comparison is `<=`. Fix with **3-way partitioning** (Dutch National Flag) → `O(n)` on all-equal input.
3. **Already-sorted with first/last pivot** — the famous `O(n²)` trap. **Always mention this**, even if your code is randomized.
4. **Reverse-sorted with first/last pivot** — same `O(n²)` trap.
5. **Recursion depth** — pathological splits push depth to `O(n)`. For `n = 100k`, you can blow V8's default ~10–15k stack. Fix: recurse on the smaller side, **iterate on the larger** (tail-call elimination by hand).
6. **Duplicates** — if pivot equals many elements, two-way partition wastes work. Switch to 3-way (Dutch Flag) for duplicate-heavy data.
7. **In-place mutation** — caller's array is sorted. If they want a copy, slice first.

## Brute force approach
Naive: pick first element, partition into two new arrays, recurse, concatenate. Loses the in-place advantage and allocates `O(n²)` in the worst case for the new arrays. Mention only to dismiss in favor of in-place partition.

## Optimal approach
In-place partition (Lomuto for clarity, Hoare for speed). **Randomize the pivot** to make worst case astronomically unlikely on adversarial input. Recurse on the smaller partition first and iterate on the larger (manual tail-call) to cap stack at `O(log n)`. For duplicate-heavy input, use 3-way partition.

## Solution (JavaScript)

```js
/**
 * In-place quicksort with randomized pivot.
 * Time: O(n log n) expected, O(n²) worst-case (extremely unlikely with randomization).
 * Space: O(log n) expected stack, O(n) worst.
 * NOT stable.
 *
 * @param {number[]} arr  mutated in place
 * @param {number}   [lo=0]
 * @param {number}   [hi=arr.length-1]
 */
function quickSort(arr, lo = 0, hi = arr.length - 1) {
  while (lo < hi) {
    const p = partition(arr, lo, hi);
    // Recurse on the smaller half, iterate on the larger:
    // keeps stack depth at O(log n) even with bad splits.
    if (p - lo < hi - p) {
      quickSort(arr, lo, p - 1);
      lo = p + 1;
    } else {
      quickSort(arr, p + 1, hi);
      hi = p - 1;
    }
  }
  return arr;
}

function partition(arr, lo, hi) {
  // Randomized pivot — defeats already-sorted worst case
  const r = lo + Math.floor(Math.random() * (hi - lo + 1));
  [arr[r], arr[hi]] = [arr[hi], arr[r]];      // move pivot to end
  const pivot = arr[hi];
  let i = lo - 1;
  for (let j = lo; j < hi; j++) {
    if (arr[j] <= pivot) {
      i++;
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }
  [arr[i + 1], arr[hi]] = [arr[hi], arr[i + 1]];
  return i + 1;
}

/**
 * 3-way partition (Dutch National Flag) — best when many duplicates.
 * Linear time on all-equal input.
 */
function quickSort3Way(arr, lo = 0, hi = arr.length - 1) {
  if (lo >= hi) return arr;
  const r = lo + Math.floor(Math.random() * (hi - lo + 1));
  [arr[r], arr[lo]] = [arr[lo], arr[r]];
  const pivot = arr[lo];
  let lt = lo, gt = hi, i = lo + 1;
  while (i <= gt) {
    if      (arr[i] < pivot) { [arr[lt], arr[i]] = [arr[i], arr[lt]]; lt++; i++; }
    else if (arr[i] > pivot) { [arr[gt], arr[i]] = [arr[i], arr[gt]]; gt--;      }
    else                     { i++; }
  }
  quickSort3Way(arr, lo, lt - 1);
  quickSort3Way(arr, gt + 1, hi);
  return arr;
}
```

## Step-by-step dry run

Input: `quickSort([3, 6, 1, 8, 2, 5])`, pretend the random pivot picks `arr[hi] = 5` for the top call.

Lomuto partition with pivot=5, lo=0, hi=5:
- i = -1
- j=0: `arr[0]=3 <= 5` → i=0, swap arr[0] with arr[0] (no-op). Array: `[3, 6, 1, 8, 2, 5]`.
- j=1: `arr[1]=6 <= 5`? no. Skip.
- j=2: `arr[2]=1 <= 5` → i=1, swap arr[1] with arr[2]. Array: `[3, 1, 6, 8, 2, 5]`.
- j=3: `arr[3]=8 <= 5`? no. Skip.
- j=4: `arr[4]=2 <= 5` → i=2, swap arr[2] with arr[4]. Array: `[3, 1, 2, 8, 6, 5]`.
- End loop. Swap arr[i+1=3] with arr[hi=5]. Array: `[3, 1, 2, 5, 6, 8]`. Return 3.

Now recurse on `[3, 1, 2]` (lo=0, hi=2) and `[6, 8]` (lo=4, hi=5).

Left, pivot=2:
- j=0: 3 <= 2? no.
- j=1: 1 <= 2 → i=0, swap arr[0] with arr[1]. `[1, 3, 2]`.
- End. Swap arr[1] with arr[2]. `[1, 2, 3]`. Return 1. Recurse on `[1]` and `[3]` — both base cases.

Right, pivot=8:
- j=4: 6 <= 8 → i=4, swap arr[4] with arr[4] (no-op).
- End. Swap arr[5] with arr[5] (no-op). Return 5.
- Recurse on `[6]` and `[]` — both base cases.

Final array: `[1, 2, 3, 5, 6, 8]`. Total swaps: ~5, comparisons: ~9.

## Important takeaways

**Syntax to memorize**
- Lomuto: `i = lo - 1`; for each `j` in `[lo, hi)`, if `arr[j] <= pivot` then `++i` and swap. Final swap of `arr[i+1]` with pivot.
- Hoare: two pointers walking inward, swap inversions, return when they cross. Recurse on `(lo, j)` and `(j+1, hi)`.
- **Randomize the pivot. Always.** It's two lines that defeat the entire worst-case scenario.

**Patterns to reuse**
- The **partition** primitive alone solves **Quickselect** (LC #215 "Kth Largest Element") in average `O(n)`: only recurse into the side containing index k.
- Dutch National Flag (3-way partition) is the canonical solution to LC #75 "Sort Colors."
- Randomization-as-worst-case-mitigation is the same trick used in randomized binary search trees, skip lists, and hash table seed randomization (defeating HashDoS).

**Common mistakes**
- Using `arr[lo]` or `arr[hi]` as pivot without randomization, then getting roasted by interviewer's already-sorted test case.
- Off-by-one in Hoare (recursing on `(lo, j-1)` instead of `(lo, j)` — common bug).
- Claiming quicksort is stable. It is **not**.
- Claiming `O(1)` space because it's "in-place." Stack space is `O(log n)` average, `O(n)` worst — not constant.
- Forgetting the "all equal elements → O(n²) in Lomuto" trap. Mention 3-way partition.
- Allocating new arrays per recursion ("simple" quicksort) — defeats the in-place advantage.

**Related questions**
- Quickselect — kth smallest/largest in expected `O(n)`. Partition once, recurse into one side.
- Sort colors (Dutch National Flag, LC #75).
- Merge sort (`09-recursion/merge-sort.md`) — sister algorithm; stable + `O(n log n)` worst-case, costs `O(n)` space.

## Variants

1. **Quickselect** — find the k-th smallest in average `O(n)`. After partition, recurse only into the half containing index k. Classic LC #215.

2. **3-way partition (Dutch Flag)** — handles many duplicates in `O(n)`. Code above. Used by Java's `Arrays.sort` for primitives.

3. **Introsort** — start with quicksort, switch to heapsort when recursion depth exceeds `2 log₂ n`. Used by C++'s `std::sort`. Guarantees `O(n log n)` worst case while keeping quicksort's average constant factor.

4. **Iterative quicksort** — replace recursion with an explicit stack of `(lo, hi)` pairs. Useful when stack space is tight or you're in a non-TCO environment (V8). Note: the "recurse on smaller, iterate on larger" trick in the solution achieves the same memory bound while keeping the code readable.

5. **Median-of-3 / median-of-medians pivot** — alternative pivots. Median-of-3 is cheap and helps on near-sorted data; median-of-medians gives true `O(n log n)` worst case but is theoretical (huge constants).

## Revision notes

> **quick sort — 60 second recap**
> - In-place divide-and-conquer; **partition** then recurse.
> - Average **`O(n log n)`**, worst **`O(n²)`** — already-sorted with first-pivot.
> - **Always randomize the pivot** (or median-of-3). Two lines, defeats worst case.
> - Space: `O(log n)` average stack, `O(n)` worst. **No aux array** (unlike merge sort).
> - **Not stable.** ES2019 requires stability ⇒ V8 dropped quicksort, switched to TimSort.
> - **Trap 1:** all-equal elements → Lomuto degenerates to `O(n²)`. Use **3-way partition** (Dutch Flag).
> - **Trap 2:** unbounded recursion depth on bad pivots — recurse on smaller half, iterate on larger.
> - Partition primitive → **Quickselect** (kth-largest in `O(n)` average).
> - Pivot strategies: first (bad), last (bad), random (defensive), median-of-3 (practical winner), median-of-medians (theoretical).
