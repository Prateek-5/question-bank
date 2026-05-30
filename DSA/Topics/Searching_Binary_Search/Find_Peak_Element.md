# Find Peak Element

**Problem Link:**
<a href="https://leetcode.com/problems/find-peak-element/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/find-peak-element/</a>

**Topic:**
Searching / Binary Search

----------------------------------------

## Step 1: Nail Down the Definition

A **peak** is an element that is **strictly greater than its neighbors**. The array has the boundary convention: out-of-bounds neighbors (beyond the array) are treated as `-∞`. So the first element is a peak if it's greater than the second; the last element is a peak if it's greater than the second-to-last.

Given an array, return the **index of any peak**. The problem promises at least one peak exists, and requires O(log n) time.

Example: `[1, 2, 3, 1]`. At index 2, the value 3 is greater than neighbors 2 and 1. Peak. Return 2.

Example: `[1, 2, 1, 3, 5, 6, 4]`. Index 1 (value 2) is a peak (neighbors 1 and 1). Also index 5 (value 6) is a peak (neighbors 5 and 4). Either answer is accepted.

Note: the problem allows **any** peak — not necessarily the global max. This turns out to matter for the algorithm.

----------------------------------------

## Step 2: The Linear Scan First

If we weren't constrained to O(log n), we could scan left to right and return the first i where `a[i] > a[i-1]` and `a[i] > a[i+1]` (with boundary care). O(n).

But the problem demands O(log n), which immediately suggests **binary search**. But binary search usually works on sorted data — here the array can be any shape. What property lets binary search work?

----------------------------------------

## Step 3: A Really Useful Observation

Look at any two adjacent elements `a[m]` and `a[m+1]`. They're different (since the problem guarantees strict comparisons, and typical constraints have distinct neighbors). Suppose `a[m] < a[m+1]` — the array is going up at that position.

**Claim:** a peak must exist in the right half `[m+1, n-1]`.

Why? Consider the array restricted to `[m+1, n-1]`. Its leftmost element is `a[m+1]`. Its out-of-bounds neighbor on the left (as far as the sub-array is concerned) is `-∞`. So `a[m+1]` is either:
- A peak of this sub-array (if `a[m+1] > a[m+2]`).
- Not a peak, in which case `a[m+2] > a[m+1]` — the ascent continues. Apply the same argument to `[m+2, n-1]`.

Either we find a peak at some point, or we reach the right boundary. At the right boundary `a[n-1]`, its right-side out-of-bounds neighbor is `-∞`, so `a[n-1]` is a peak iff `a[n-1] > a[n-2]`. Since we've been ascending all along (each step was `a[i] > a[i-1]`), yes — `a[n-1]` is a peak.

Symmetric argument if `a[m] > a[m+1]`: a peak exists in `[0, m]`.

So comparing `a[m]` with `a[m+1]` tells us which half to search. That's the binary-search hook.

----------------------------------------

## Step 4: The Algorithm

```
lo = 0, hi = n - 1
while lo < hi:
    m = (lo + hi) / 2
    if a[m] < a[m + 1]:
        lo = m + 1       # peak is in the right half (including m+1)
    else:
        hi = m           # peak is in the left half (including m)
return lo
```

When `lo == hi`, we've zeroed in on a peak index. The loop invariant guarantees this index is a peak.

Two subtleties:
- We use `a[m]` vs `a[m+1]`, which requires `m + 1 ≤ hi`. Since `m = (lo + hi) / 2` with `lo < hi`, we have `m ≤ hi - 1 < hi`, so `m + 1 ≤ hi`. Safe.
- The loop terminates because each iteration shrinks the range by at least half.

----------------------------------------

## Step 5: Trace on `[1, 2, 1, 3, 5, 6, 4]`

```
lo=0, hi=6.
m=3. a[3]=3, a[4]=5. a[m] < a[m+1]. lo = m+1 = 4.
lo=4, hi=6.
m=5. a[5]=6, a[6]=4. a[m] > a[m+1]. hi = m = 5.
lo=4, hi=5.
m=4. a[4]=5, a[5]=6. a[m] < a[m+1]. lo = m+1 = 5.
lo=5, hi=5. Loop exits.
Return 5.
```

a[5] = 6. Its neighbors are 5 and 4. It's a peak. ✓

Let me try `[1, 2, 3, 1]`:
```
lo=0, hi=3.
m=1. a[1]=2, a[2]=3. a[m] < a[m+1]. lo=2.
lo=2, hi=3.
m=2. a[2]=3, a[3]=1. a[m] > a[m+1]. hi=2.
lo=2, hi=2. Return 2.
```

a[2] = 3. Peak. ✓

----------------------------------------

## Step 6: Why O(log n) Works Without Sorted Data

Normally binary search requires a **monotonic predicate** over positions — something like "is a[m] >= target?" that flips from false to true at one point. Here, the predicate is "does the answer (a peak) lie in the right half?" and that predicate is monotonic in a different sense: it's determined entirely by the local comparison `a[m] vs. a[m+1]`.

As long as each binary-search step reliably narrows down a region where we *know* a peak exists, we get O(log n). And the key argument (from Step 3) is that a region still ends in a peak regardless of what's outside — the boundary "−∞" on the sub-array guarantees this.

That's the real insight: *local* comparisons at the midpoint tell us enough about *global* structure to halve the problem at each step. That's more powerful than sorting, in a sense.

----------------------------------------

## Step 7: Name It

This is **binary search on a non-sorted array** — a common and powerful pattern. The same thinking applies to problems like:
- Search in a rotated sorted array (different monotonic predicate).
- Find a local minimum in a tree or graph.
- Finding a local minimum in a bitonic array.

The core mental move: "binary search doesn't need the array to be sorted — it needs a monotonic property over *decisions*."

----------------------------------------

## Step 8: Complexity

Time: each iteration halves the search range. **O(log n)**.
Space: **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int findPeakElement(vector<int>& nums) {
    int lo = 0, hi = nums.size() - 1;
    while (lo < hi) {
        int m = lo + (hi - lo) / 2;        // overflow-safe midpoint
        if (nums[m] < nums[m + 1]) {
            lo = m + 1;                     // peak in right half
        } else {
            hi = m;                         // peak in left half (including m)
        }
    }
    return lo;
}
```

One thing worth noting: `lo + (hi - lo) / 2` instead of `(lo + hi) / 2` prevents integer overflow for very large arrays. Small habit, always worth using.

----------------------------------------

## Step 10: Follow-up Questions

- **Find the global maximum, not any peak.** The problem guarantees adjacent elements are distinct — but there can be multiple peaks. To find global max, you need O(n). No log n trick there.
- **2D Peak (matrix).** There's an O(m log n) algorithm: find the max of the middle row, then recurse into the half (top or bottom) containing its larger vertical neighbor. Neat extension of the 1D idea.
- **What if duplicates are allowed in neighbors?** Harder — the monotonic predicate breaks. Worst case O(n).
- **Find a local minimum instead.** Flip all comparisons in the algorithm.
- **Ternary search on a bitonic (strictly increasing then strictly decreasing) array.** Since the shape is more constrained, ternary search is also O(log n) but uses a slightly different step.
