# Quick sort with pivot selection

> **Difficulty:** Medium   |   **Time:** ~12 min   |   **Prereqs:** [merge-sort.md](./merge-sort.md)
>
> **Source:** LeetCode #912. Quickselect (LeetCode #215) shares partition.

---

## 1. Problem statement

In-place quicksort. Discuss worst-case (O(n²) on sorted input with bad pivot) and fixes (random/median-of-3).

**Verification examples**

```js
quickSort([3, 1, 4, 1, 5, 9, 2, 6]);     // [1, 1, 2, 3, 4, 5, 6, 9]
quickSort([]);                            // []
quickSort([3, 3, 3]);                     // [3, 3, 3]
```

**Constraints**
- Average O(n log n); worst O(n²).
- O(log n) stack with median-of-3 pivot.
- In-place (no extra array per level).
- Unstable.

---

## 2. Plain-English restatement

Pick pivot; partition into ≤ pivot vs > pivot; recurse each side. Bad pivot → O(n²). Random/median-of-3 → O(n log n) expected.

---

## 3. Why this matters in interviews

Partition primitive for Quickselect (k-th element). Senior bar: discuss worst case + fix.

---

## 4. Mental model

```
   Lomuto partition (simple, last-pivot):
     pivot = arr[hi]
     i = lo - 1
     for j = lo..hi-1:
       if arr[j] <= pivot:
         i++; swap arr[i], arr[j]
     swap arr[i+1], arr[hi]
     return i + 1
   
   Hoare partition (faster, two-pointer):
     pivot = arr[lo]
     i = lo - 1, j = hi + 1
     while true:
       do i++; while arr[i] < pivot
       do j--; while arr[j] > pivot
       if i >= j: return j
       swap arr[i], arr[j]
   
   Worst case:
     Already-sorted + first/last-element pivot → partitions of size n-1 + 0.
     T(n) = T(n-1) + O(n) → O(n²).
     Stack depth n → RangeError on V8.
   
   Fixes:
     Random pivot.
     Median-of-3 (lo, mid, hi).
     3-way partition for many duplicates.
   
   Tail recursion optim (manual):
     Always recurse on smaller half first; iterate larger.
     Stack bounded by O(log n).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does sorted input + last-pivot hit O(n²)?
> 2. Stack depth without fix?
> 3. Stable?

---

## 6. Brute force — walked through

```js
function quickSortNaive(arr) {
  if (arr.length <= 1) return arr;
  const pivot = arr[0];
  const less = arr.slice(1).filter(x => x < pivot);
  const equal = arr.filter(x => x === pivot);
  const greater = arr.slice(1).filter(x => x > pivot);
  return [...quickSortNaive(less), ...equal, ...quickSortNaive(greater)];
}
```

Allocates arrays — not in-place. O(n log n) expected.

---

## 7. The unlocking insight

> **Partition in-place; recurse on each side. Use random/median-of-3 pivot to avoid O(n²). Tail-recurse smaller for O(log n) stack.**

Three properties:

1. **In-place partition**.
2. **Random or median-of-3 pivot.**
3. **Tail-recurse smaller** half.

---

## 8. Solution (annotated)

```js
function quickSort(arr, lo = 0, hi = arr.length - 1) {
  if (lo >= hi) return arr;
  const p = partitionLomuto(arr, lo, hi);                                  // step 1: partition
  quickSort(arr, lo, p - 1);
  quickSort(arr, p + 1, hi);
  return arr;
}

function partitionLomuto(arr, lo, hi) {
  // Median-of-3 pivot to avoid O(n²) on sorted input
  const mid = (lo + hi) >> 1;
  if (arr[mid] < arr[lo]) [arr[lo], arr[mid]] = [arr[mid], arr[lo]];
  if (arr[hi] < arr[lo]) [arr[lo], arr[hi]] = [arr[hi], arr[lo]];
  if (arr[mid] < arr[hi]) [arr[mid], arr[hi]] = [arr[hi], arr[mid]];      // step 2: put median at hi

  const pivot = arr[hi];
  let i = lo - 1;
  for (let j = lo; j < hi; j++) {
    if (arr[j] <= pivot) {
      i++;
      [arr[i], arr[j]] = [arr[j], arr[i]];                                 // step 3: swap
    }
  }
  [arr[i + 1], arr[hi]] = [arr[hi], arr[i + 1]];
  return i + 1;
}

// 3-way partition for many duplicates (Dutch national flag)
function quickSort3Way(arr, lo = 0, hi = arr.length - 1) {
  if (lo >= hi) return arr;
  let lt = lo, gt = hi, i = lo;
  const pivot = arr[lo + Math.floor(Math.random() * (hi - lo + 1))];       // step 4: random
  while (i <= gt) {
    if (arr[i] < pivot)      [arr[i++], arr[lt++]] = [arr[lt], arr[i]];
    else if (arr[i] > pivot) [arr[i], arr[gt--]]   = [arr[gt], arr[i]];
    else i++;
  }
  quickSort3Way(arr, lo, lt - 1);
  quickSort3Way(arr, gt + 1, hi);
  return arr;
}

// Quickselect — k-th smallest, average O(n)
function quickSelect(arr, k) {
  let lo = 0, hi = arr.length - 1;
  while (lo <= hi) {
    const p = partitionLomuto(arr, lo, hi);
    if (p === k) return arr[p];
    if (p < k) lo = p + 1;
    else hi = p - 1;
  }
  return undefined;
}
```

**Try it yourself**

```js
quickSort([3, 1, 4, 1, 5, 9, 2, 6]);                         // [1, 1, 2, 3, 4, 5, 6, 9]
quickSort([3, 3, 3, 3]);                                      // [3, 3, 3, 3]

// Worst-case (sorted + last-pivot, no median):
const sorted = Array.from({length: 10_000}, (_, i) => i);
// With median-of-3: O(n log n).
// Without (just last-element): O(n²) — slow.

// Quickselect — 5th smallest
quickSelect([3, 1, 4, 1, 5, 9, 2, 6].slice(), 4);            // 4 (0-indexed → 5th)

// Compare with sort
[3, 1, 4, 1, 5, 9, 2, 6].sort((a, b) => a - b)[4];           // 4
// quickSelect avg O(n) vs sort O(n log n) — when only k needed.
```

---

## 9. Step-by-step dry run

```
quickSort([3, 1, 4, 1]):
  partition([3,1,4,1], 0, 3):
    median-of-3: lo=3, mid=1, hi=1. After:
      arr[lo]=1 (min), arr[mid]=3 (max), arr[hi]=1 (median).
      But median-of-3 expects a unique-ish picker; with [3,1,4,1] median is between 1 and 3.
      For simplicity say pivot = 1 at hi.
    pivot=1. i=-1.
    j=0 (3): 3<=1? No.
    j=1 (1): 1<=1? Yes. i=0. swap[0][1] → [1,3,4,1].
    j=2 (4): 4<=1? No.
    Swap arr[1][hi=3]: [1,1,4,3].
    return 1.
  
  quickSort([1,1,4,3], 0, 0): base.
  quickSort([1,1,4,3], 2, 3):
    partition([1,1,4,3], 2, 3): pivot=3. j=2 (4): >3. swap arr[2][3] = [1,1,3,4]. return 2.
    quickSort(2, 1): base. quickSort(3, 3): base.
  
  Result: [1,1,3,4].

Worst case (sorted, last-pivot):
  [1,2,3,4,5], pivot=5.
  Partition: all ≤ 5 → i increments through. final i=4 (index of last). p=4.
  Recurse [0..3], [5..5].
  [1,2,3,4], pivot=4 → similar → recurse [0..2].
  ...
  Each level: n-1 partition + 0 partition. Total O(n) per level × n levels = O(n²).
  Stack depth n.

With median-of-3:
  Pivot is median of [lo, mid, hi] — middle value.
  Sorted input: median = mid = 3. Partition balanced. O(n log n).

3-way for [3,3,3,3,3]:
  All equal. lt stays at lo; gt stays at hi; range collapses.
  O(n) for this case.
```

---

## 10. Common confusion + traps

1. **Last-element pivot on sorted** — O(n²).
2. **No median-of-3** — vulnerable.
3. **Stable assumption** — quicksort UNstable.
4. **Stack overflow** — naive on sorted ~10-15k.
5. **Many duplicates** — 3-way partition.
6. **Quickselect inplace** — yes (no copy).
7. **`<` vs `<=`** in partition — both work; `<=` for left-bias.

---

## 11. Senior follow-ups & variants

### Variant 1 — 3-way partition (Dutch flag)
For arrays with many duplicates.

### Variant 2 — Random pivot
Avoids adversarial sorted input.

### Variant 3 — Quickselect (LeetCode #215)
K-th element O(n) average.

### Variant 4 — Introsort
Quicksort + heapsort fallback for guaranteed O(n log n).

### Variant 5 — Parallel quicksort
Recursive branches can run in parallel.

---

## 12. How to think aloud

> "Quicksort: pick a pivot, partition array into ≤ pivot vs > pivot, recurse on each side. Average O(n log n); worst O(n²) — non-obvious worst-case is already-sorted input with first/last-element pivot, where each partition is n-1 + 0, recurrence becomes T(n) = T(n-1) + O(n) = O(n²), and stack depth is n (RangeError on V8 for n > 10-15k). Fixes: random pivot, or median-of-3 (pivot = median of `arr[lo], arr[mid], arr[hi]`). Median-of-3 is deterministic and handles sorted input. For many duplicates, 3-way partition (Dutch national flag): `< pivot | == pivot | > pivot` regions — avoids O(n²) on `[5, 5, 5, ..., 5]`. Lomuto partition is simpler (last-element pivot, single forward scan with swap); Hoare partition is faster (two pointers crossing) but trickier index bookkeeping. Quicksort is UNSTABLE — equal-keyed elements may swap. The partition step is the primitive behind Quickselect (LeetCode #215 'K-th largest') — pick pivot, recurse into the side containing k, O(n) average. Introsort: hybrid quicksort + heapsort fallback on deep recursion, used in C++ std::sort. Tail-recurse smaller side first to bound stack at O(log n). Trap: last-pivot on sorted (O(n²)); no fallback for adversarial; expecting stability; assuming O(n log n) without fix."

---

## 13. 60-second revision

> - **Partition + recurse** each side.
> - **Average O(n log n);** worst O(n²) on sorted + last-pivot.
> - **Median-of-3 / random pivot** avoids worst.
> - **3-way partition** for duplicates.
> - **UNSTABLE.**
> - **Lomuto simple; Hoare faster.**
> - **Quickselect** = partition for k-th, O(n) avg.
> - **Introsort** hybrid for guarantee.
> - **Trap:** O(n²) sorted; stable assumption; no fix.

---

**Related:** [merge-sort.md](./merge-sort.md) · [`07-arrays/stable-sort-discussion.md`](../07-arrays/stable-sort-discussion.md) · [backtracking-template.md](./backtracking-template.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
