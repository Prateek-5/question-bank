# Find K Closest Elements

**Problem Link:**
https://leetcode.com/problems/find-k-closest-elements/

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: Understand the Problem

Given a **sorted** array `arr`, an integer `k`, and an integer `x`, return the `k` closest elements to `x` from the array, sorted in ascending order.

"Closest" is by absolute difference `|arr[i] - x|`. Ties broken by preferring smaller values.

Example: `arr = [1, 2, 3, 4, 5]`, k = 4, x = 3.
- Distances: |1-3|=2, |2-3|=1, |3-3|=0, |4-3|=1, |5-3|=2.
- Pick 4 smallest distances: 3 (dist 0), 2 (dist 1), 4 (dist 1), 1 (dist 2).
- Ties at dist=2: between 1 and 5, prefer 1.
- Sorted: [1, 2, 3, 4].

`k=4, x=-1`: distances 2, 3, 4, 5, 6. Pick 4 smallest: 1, 2, 3, 4. Result: [1, 2, 3, 4].

----------------------------------------

## Step 2: First Approach — Heap of Size K

A very direct approach: use a max-heap of size k keyed on distance-to-x. For each arr[i]:
- Push (distance, value).
- If heap size > k, pop (kicks out the farthest).

At the end, the heap has the k closest. Sort them by value for the output.

Time: O(n log k). Works but ignores the sorted-ness of the input.

----------------------------------------

## Step 3: Better — Exploit the Sorted Input

The input is sorted. The "k closest" elements must form a **contiguous window** in the array. Why?

Suppose the answer is some subset S of k elements. Order them by index. The leftmost has some index L, the rightmost has index R, with R - L + 1 ≥ k. But if R - L + 1 > k, there must be elements in [L, R] that aren't in S. Since arr is sorted, those elements are all *between* arr[L] and arr[R] in value, and are therefore at most as far from x as max(arr[L], arr[R]). So they should be in S too — contradiction.

Conclusion: the k closest elements are k **consecutive** elements in the sorted array. We just need to find the right window.

This is a huge simplification — we're not picking arbitrary k out of n; we're picking a contiguous window of size k.

----------------------------------------

## Step 4: Find the Right Window via Binary Search

The window is `arr[L .. L + k - 1]` for some left index L in `[0, n - k]`. How do we pick L?

Intuition: the window should be "centered on x." Specifically, compare the leftmost element of the window (at L) with the element just past the right end (at L + k):
- If `x - arr[L] > arr[L + k] - x`: the right element is closer to x than the left one. Shifting the window right is beneficial — we'd gain a closer element (arr[L+k]) and lose a farther one (arr[L]).
- Otherwise: the left element is at least as good. The current window is at least as good as moving right.

Binary-search on L. Keep shrinking to the better half.

```
lo = 0, hi = n - k
while lo < hi:
    mid = (lo + hi) / 2
    if x - arr[mid] > arr[mid + k] - x:
        lo = mid + 1
    else:
        hi = mid
return arr[lo .. lo + k - 1]
```

O(log(n - k) + k). Extremely fast.

----------------------------------------

## Step 5: Why the Comparison Direction Works

The condition `x - arr[mid] > arr[mid + k] - x` is asking: is the left boundary of the current window **farther** from x than the element just past the right? If yes, the window's left boundary is a "weak link" — we should shift right to drop it.

Tie case: if `x - arr[mid] == arr[mid + k] - x`, we don't shift. The problem's tie-break prefers smaller values, and staying at the current window keeps arr[mid] (smaller) in favor of arr[mid + k] (larger).

That's why the `>` is strict — on equality, we stay.

----------------------------------------

## Step 6: Trace on `[1, 2, 3, 4, 5]`, k = 4, x = 3

n = 5, k = 4. L ranges in [0, 1].

```
lo=0, hi=1.
mid=0.
x - arr[0] = 3 - 1 = 2.
arr[0 + 4] - x = arr[4] - 3 = 5 - 3 = 2.
2 > 2? No. Set hi=0.

Loop ends. L = 0.
Return arr[0..3] = [1, 2, 3, 4].
```

✓

Try `arr = [1, 2, 3, 4, 5]`, k = 4, x = -1:

```
lo=0, hi=1.
mid=0.
x - arr[0] = -1 - 1 = -2.
arr[4] - x = 5 - (-1) = 6.
-2 > 6? No. Set hi=0.
Loop ends. L = 0.
Return [1, 2, 3, 4].
```

✓

Try `arr = [1, 2, 3, 4, 5]`, k = 4, x = 4:

```
lo=0, hi=1.
mid=0.
3 (=4-1) > 1 (=5-4)? Yes. Set lo=1.
Loop ends. L = 1.
Return arr[1..4] = [2, 3, 4, 5].
```

Distance check: from 4, distances are 3, 2, 1, 0, 1. Four smallest: 2, 3, 4, 5 (distances 2, 1, 0, 1). ✓

----------------------------------------

## Step 7: Compare Approaches

| Approach | Time | Space |
|---|---|---|
| Max-heap size k | O(n log k) | O(k) |
| Sort by dist, take first k | O(n log n) | O(n) |
| Binary search on window | O(log(n-k) + k) | O(k) |

Binary search wins because it exploits the sorted structure of the input. The other approaches treat the input as unsorted, which is a missed opportunity.

For interviews, mentioning the heap approach first (general, works on unsorted input) and then the binary search optimization (exploits sortedness) shows range.

----------------------------------------

## Step 8: Name It

This is **binary search on a sliding window boundary**. The decision variable isn't an index in the array — it's the **left index of the chosen window**. We binary-search over possible window positions using a comparison that tells us which direction to shift.

The same meta-technique (binary searching over a parameter that isn't an array index) appears in:
- Capacity to Ship Packages Within D Days.
- Koko Eating Bananas.
- Split Array Largest Sum.

The trick is recognizing the monotonic structure.

----------------------------------------

## Step 9: Complexity

Binary search on window: **O(log(n - k) + k)**.
- Binary search: O(log(n - k)).
- Extract k elements: O(k).

Space: O(k) for the output.

----------------------------------------

## Step 10: C++ Implementation

```cpp
vector<int> findClosestElements(vector<int>& arr, int k, int x) {
    int lo = 0, hi = arr.size() - k;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (x - arr[mid] > arr[mid + k] - x) lo = mid + 1;
        else hi = mid;
    }
    return vector<int>(arr.begin() + lo, arr.begin() + lo + k);
}
```

The binary search is the key. Everything else is just slicing the k-length window out of arr.

Edge cases handled naturally:
- k = n: loop doesn't execute (lo = hi = 0). Returns the whole array.
- x smaller than all elements: `x - arr[mid]` is very negative, never > right side, so hi shrinks to 0. Returns first k.
- x larger than all: `arr[mid+k] - x` is very negative, condition is true, lo grows to n-k. Returns last k.

----------------------------------------

## Step 11: Follow-up Questions

- **Unsorted input.** Use the heap approach: O(n log k).
- **Return the k closest sorted by distance (not value).** Use a heap and don't re-sort by value.
- **Streaming input.** Heap approach with lazy updates.
- **Closest-k in 2D (points in a plane).** Different problem — requires KD-tree or spatial index.
- **Unusual distance metric.** Binary search works if the metric preserves the "contiguous window" property (typically requires monotonic distance along the array).
- **What if duplicates exist?** Algorithm works unchanged — the binary search shifts over tied elements according to the tie-break rule (prefer smaller values).
