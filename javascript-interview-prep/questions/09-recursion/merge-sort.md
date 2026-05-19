# Merge sort — divide and conquer

> **Difficulty:** Medium   |   **Time:** ~12 min   |   **Prereqs:** [quick-sort.md](./quick-sort.md), [`07-arrays/stable-sort-discussion.md`](../07-arrays/stable-sort-discussion.md)
>
> **Source:** LeetCode #912. V8's TimSort = merge-sort variant.

---

## 1. Problem statement

Implement merge sort. O(n log n) worst-case; stable.

**Verification examples**

```js
mergeSort([3, 1, 4, 1, 5, 9, 2, 6]);     // [1, 1, 2, 3, 4, 5, 6, 9]
mergeSort([]);                            // []
mergeSort([1]);                           // [1]

// Stability check
const arr = [{k: 1, v: 'a'}, {k: 1, v: 'b'}, {k: 0, v: 'c'}];
mergeSort(arr, (a, b) => a.k - b.k);
// [{k:0,v:'c'}, {k:1,v:'a'}, {k:1,v:'b'}]   ← stable
```

**Constraints**
- O(n log n) all cases (no worst-case explosion like quicksort).
- O(n) extra space.
- Stable.
- Recursion depth ~log n (safe).

---

## 2. Plain-English restatement

Recursively split into halves until size ≤ 1; merge two sorted halves into one. Stability from `<=` choosing left first.

---

## 3. Why this matters in interviews

Canonical D&C. V8 baseline (TimSort). Tests: clean recursive divide, stability awareness, recurrence reasoning.

---

## 4. Mental model

```
   mergeSort(arr):
     if arr.length <= 1: return arr
     mid = arr.length / 2
     left = mergeSort(arr.slice(0, mid))
     right = mergeSort(arr.slice(mid))
     return merge(left, right)
   
   merge(left, right):
     i, j = 0, 0
     result = []
     while i < left.len && j < right.len:
       if left[i] <= right[j]:           ← <= for stability
         result.push(left[i++])
       else: result.push(right[j++])
     append remainders.
     return result
   
   Recurrence: T(n) = 2T(n/2) + O(n) → O(n log n).
   Stack depth: log n (safe).
   Space: O(n) extra for merged arrays.
   
   Stability:
     Equal-key elements: left wins (because we check <=).
     Multi-key sort possible: sort by minor key first, major key second.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is `<=` the stability invariant?
> 2. Recursion depth?
> 3. In-place merge sort — possible?

---

## 6. Brute force — walked through

```js
// O(n²) — bubble/insertion
function bubble(arr) {
  for (let i = 0; i < arr.length; i++) {
    for (let j = 0; j < arr.length - 1 - i; j++) {
      if (arr[j] > arr[j+1]) [arr[j], arr[j+1]] = [arr[j+1], arr[j]];
    }
  }
  return arr;
}
```

O(n²); useless past n=10k.

---

## 7. The unlocking insight

> **Divide log n times, merge O(n) per level. `<=` makes it stable. log n recursion depth (safe).**

Three properties:

1. **Divide log n times**.
2. **Merge O(n) per level**.
3. **`<=` for stability**.

---

## 8. Solution (annotated)

```js
function mergeSort(arr, cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0)) {
  if (arr.length <= 1) return arr;                                          // step 1: base
  const mid = arr.length >> 1;
  const left = mergeSort(arr.slice(0, mid), cmp);                           // step 2: divide
  const right = mergeSort(arr.slice(mid), cmp);
  return merge(left, right, cmp);
}

function merge(left, right, cmp) {
  const result = new Array(left.length + right.length);
  let i = 0, j = 0, k = 0;
  while (i < left.length && j < right.length) {
    if (cmp(left[i], right[j]) <= 0) {                                      // step 3: <= for stable
      result[k++] = left[i++];
    } else {
      result[k++] = right[j++];
    }
  }
  while (i < left.length) result[k++] = left[i++];                          // step 4: drain
  while (j < right.length) result[k++] = right[j++];
  return result;
}

// In-place (kind of — uses index ranges)
function mergeSortInPlace(arr, cmp = (a, b) => a - b, lo = 0, hi = arr.length - 1) {
  if (lo >= hi) return;
  const mid = (lo + hi) >> 1;
  mergeSortInPlace(arr, cmp, lo, mid);
  mergeSortInPlace(arr, cmp, mid + 1, hi);
  mergeInPlace(arr, cmp, lo, mid, hi);
}

function mergeInPlace(arr, cmp, lo, mid, hi) {
  const buf = new Array(hi - lo + 1);
  let i = lo, j = mid + 1, k = 0;
  while (i <= mid && j <= hi) {
    buf[k++] = cmp(arr[i], arr[j]) <= 0 ? arr[i++] : arr[j++];
  }
  while (i <= mid) buf[k++] = arr[i++];
  while (j <= hi) buf[k++] = arr[j++];
  for (let m = 0; m < buf.length; m++) arr[lo + m] = buf[m];
}
```

**Try it yourself**

```js
mergeSort([3, 1, 4, 1, 5, 9, 2, 6]);                         // [1, 1, 2, 3, 4, 5, 6, 9]

// Stable multi-key
const users = [
  {name: 'A', age: 25}, {name: 'B', age: 25}, {name: 'C', age: 20}
];
// Sort by age then name (relies on stability)
const byAge = mergeSort([...users].sort((a, b) => a.name.localeCompare(b.name)),
                        (a, b) => a.age - b.age);
// All age-25 retain name order.

// External merge sort (for files too big for memory)
async function externalMergeSort(filename) {
  const chunks = await splitIntoChunks(filename);   // sorted chunks on disk
  return mergeChunks(chunks);   // k-way merge
}

// Bottom-up iterative — no recursion
function mergeSortIter(arr) {
  let result = arr.slice();
  for (let size = 1; size < result.length; size *= 2) {
    for (let lo = 0; lo < result.length; lo += 2 * size) {
      const mid = Math.min(lo + size - 1, result.length - 1);
      const hi = Math.min(lo + 2 * size - 1, result.length - 1);
      if (mid < hi) {
        const merged = merge(result.slice(lo, mid + 1), result.slice(mid + 1, hi + 1), (a, b) => a - b);
        for (let i = 0; i < merged.length; i++) result[lo + i] = merged[i];
      }
    }
  }
  return result;
}
```

---

## 9. Step-by-step dry run

```
mergeSort([3, 1, 4, 1]):
  mid = 2.
  left = mergeSort([3, 1]):
    mid = 1.
    left = mergeSort([3]) = [3].
    right = mergeSort([1]) = [1].
    merge([3], [1], cmp):
      3 <= 1? No → push 1. j=1.
      Drain left: push 3.
      Return [1, 3].
  right = mergeSort([4, 1]):
    Similar → [1, 4].
  merge([1, 3], [1, 4]):
    1 <= 1? Yes (stable, left first) → push 1 (from left). i=1.
    3 <= 1? No → push 1 (from right). j=1.
    3 <= 4? Yes → push 3. i=2.
    Drain right: push 4.
    Return [1, 1, 3, 4].

Recursion tree depth log2(4) = 2.

Stability:
  Two equal-key elements: cmp returns 0.
  We use cmp(left, right) <= 0 — equal (== 0) takes LEFT first.
  Left half came first in input → relative order preserved.

If we used < (strict):
  cmp(left, right) < 0 → strict less.
  Equal case: takes right first → flips input order.
  Not stable.

Iterative mergeSortIter:
  size=1: merge pairs (1,2)(3,4)... — sort pairs.
  size=2: merge groups of 4.
  size=4: merge groups of 8.
  ...
```

---

## 10. Common confusion + traps

1. **`<` instead of `<=`** — unstable.
2. **In-place** — JS makes it awkward (no efficient in-place merge).
3. **`arr.slice` O(n) per level** — total O(n log n) extra space.
4. **Stack overflow** — log n depth; safe.
5. **TimSort vs plain mergesort** — TimSort adapts to existing runs.
6. **Empty / single element** — already sorted; base case.
7. **Comparator returns bool** — coerces; broken.

---

## 11. Senior follow-ups & variants

### Variant 1 — Bottom-up iterative
No recursion; same O(n log n).

### Variant 2 — In-place (advanced)
Galloping merge with rotation; complex.

### Variant 3 — External merge sort
For files > memory.

### Variant 4 — K-way merge
Merge k sorted lists (LeetCode #23).

### Variant 5 — TimSort
Detect runs + galloping; what V8 actually uses.

---

## 12. How to think aloud

> "Merge sort: classic divide-and-conquer. Recursively split until size ≤ 1; merge two sorted halves into one. Recurrence `T(n) = 2T(n/2) + O(n)` → `O(n log n)` by Master Theorem. O(n) extra space for merged arrays. Recursion depth log n — safe in V8. STABLE: in `merge`, when equal-key elements meet, take LEFT first (use `cmp(left, right) <= 0` not `<`); equal-keyed elements in left half were earlier in input, so their order is preserved. This is what V8 chose as the spec stability mandate (ES2019); V8's TimSort is a merge-sort variant with adaptive run detection. Multi-key sort via stability: sort by minor key first, then major key — minor order preserved within major ties. Variants: bottom-up iterative (no recursion, same O(n log n)); external merge sort for files larger than memory (sort chunks to disk, k-way merge); k-way merge with min-heap (LeetCode #23 'Merge K sorted lists'). TimSort: detect already-sorted runs (linear early-out); galloping mode for runs; what V8 ships. Trap: `<` instead of `<=` (unstable); expecting in-place (no efficient in-place merge in JS); `slice` O(n) per level (total O(n log n) extra space — acceptable but worth mentioning); comparator returning boolean (coerces to 1/0, breaks sort)."

---

## 13. 60-second revision

> - **Divide log n times; merge O(n) per level.**
> - **`O(n log n)` all cases.**
> - **Stable via `<=`** in merge.
> - **O(n) extra space.**
> - **Recursion depth log n** — safe.
> - **Bottom-up iterative** variant.
> - **External merge sort** for files.
> - **TimSort = adaptive mergesort** (V8).
> - **Trap:** `<` unstable; in-place complex; comparator bool.

---

**Related:** [quick-sort.md](./quick-sort.md) · [`07-arrays/stable-sort-discussion.md`](../07-arrays/stable-sort-discussion.md) · [`07-arrays/sort-by-multiple-keys.md`](../07-arrays/sort-by-multiple-keys.md) · [iterative-from-recursive.md](./iterative-from-recursive.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
