# Search in Rotated Sorted Array

**Problem Link:**
https://leetcode.com/problems/search-in-rotated-sorted-array/

**Topic:**
Searching / Binary Search

----------------------------------------

## Step 1: The Problem

You have an array that was originally sorted in ascending order but has been **rotated** at some unknown pivot. Given a target, return its index, or -1 if not present. Do it in O(log n).

Example: `[4, 5, 6, 7, 0, 1, 2]` was `[0, 1, 2, 4, 5, 6, 7]` before rotation at pivot 4. Target 0 → index 4. Target 3 → not found.

The O(log n) requirement rules out a linear scan. We have to use binary search. But the array isn't fully sorted, so plain binary search breaks. We need to adapt it.

----------------------------------------

## Step 2: What Does Rotation Preserve?

Even though the array isn't sorted overall, it still has useful structure. Take a rotated array and split it at its middle `mid`. Look at the **two halves** `[l..mid]` and `[mid+1..r]`.

Claim: at least **one** of the two halves is sorted.

Why? A sorted array is one contiguous increasing run. Rotating it at one pivot creates exactly **two** increasing runs. When we cut anywhere with `mid`, we hit at most one "break point" between the two runs — so at least one side is a clean increasing run.

Example: `[4, 5, 6, 7, 0, 1, 2]`, mid = 3 (value 7). Left `[4,5,6,7]` is sorted. Right `[0,1,2]` is also sorted. Both sorted because mid landed right at the boundary.

Example: mid = 5 (value 1). Left `[4,5,6,7,0,1]` is not sorted (break between 7 and 0). Right `[2]` is trivially sorted.

So at each step, we can figure out which half is sorted by comparing `a[l]` to `a[mid]`:

- If `a[l] <= a[mid]`: the left half is sorted.
- Otherwise: the right half is sorted.

----------------------------------------

## Step 3: Using the Sorted Half

Once we know a half is sorted, we can check in O(1) whether the target lies within its range.

- If **left is sorted** and `a[l] <= target < a[mid]`: target is in the left half. Search there.
- If **left is sorted** and target is outside that range: target must be in the right half. Search there.
- If **right is sorted** and `a[mid] < target <= a[r]`: target is in the right half.
- Otherwise: target is in the left half.

At each step we cut the search space in half, so we still achieve O(log n).

This is the key idea. Now let's code it carefully.

----------------------------------------

## Step 4: Pseudocode

```
lo = 0, hi = n - 1
while lo <= hi:
    mid = (lo + hi) / 2
    if a[mid] == target: return mid

    if a[lo] <= a[mid]:                   # left is sorted
        if a[lo] <= target < a[mid]:      # target in left
            hi = mid - 1
        else:
            lo = mid + 1
    else:                                  # right is sorted
        if a[mid] < target <= a[hi]:      # target in right
            lo = mid + 1
        else:
            hi = mid - 1
return -1
```

Two subtleties:
- `a[lo] <= a[mid]` uses `<=` (not `<`) because if the array has only one element between lo and mid, `a[lo] == a[mid]` is possible.
- The boundary comparisons use `<` and `<=` carefully to handle the endpoint values.

----------------------------------------

## Step 5: Dry Run on `[4, 5, 6, 7, 0, 1, 2]` for target 0

```
lo=0, hi=6, a=[4,5,6,7,0,1,2].
mid=3, a[mid]=7. Not target.
a[lo]=4 <= a[mid]=7 → left sorted.
Is 4 <= 0 < 7? No. So target not in left. lo = mid + 1 = 4.

lo=4, hi=6, a[lo..hi]=[0,1,2].
mid=5, a[mid]=1. Not target.
a[lo]=0 <= a[mid]=1 → left sorted.
Is 0 <= 0 < 1? Yes. Target in left. hi = mid - 1 = 4.

lo=4, hi=4.
mid=4, a[mid]=0. Target found! Return 4.
```

Correct.

Now for target 3:

```
lo=0, hi=6, mid=3, a[mid]=7. Not target.
Left sorted. Is 4 <= 3 < 7? No. lo=4.

lo=4, hi=6, mid=5, a[mid]=1. Not target.
Left sorted ([0,1]). Is 0 <= 3 < 1? No. lo=6.

lo=6, hi=6, mid=6, a[mid]=2. Not target.
Left sorted ([2]). Is 2 <= 3 < 2? No. lo=7.

lo>hi, return -1.
```

Correct.

----------------------------------------

## Step 6: Why This Is Correct — The Invariant

At every iteration of the loop, the target (if present) is in `a[lo..hi]`. The algorithm preserves this.

When we identify a sorted half and the target is in its range, we restrict `[lo, hi]` to that half — the target is definitely there.

When the target is *not* in the sorted half's range, it's either outside the array (not present) or in the other half. We restrict to the other half, preserving the invariant.

Eventually `lo > hi` (target not present) or `a[mid] == target` (found it).

Each iteration halves the search space → O(log n) iterations.

----------------------------------------

## Step 7: An Important Edge Case

What if the array **wasn't rotated** (rotation by 0)? Then the whole array is sorted, `a[lo] <= a[mid]` always holds, and we always enter the "left sorted" branch. The algorithm degenerates to regular binary search. ✓

What if rotated by exactly n (full rotation)? Same as no rotation. ✓

What if the array has only one element? `lo == hi`, one iteration, return 0 if match else -1. ✓

What if the array has duplicates? **The algorithm above assumes all elements are distinct.** With duplicates, `a[lo] == a[mid] == a[hi]` gives no information about which half is sorted. The variant "Search in Rotated Sorted Array II" handles duplicates by linearly shrinking `lo` and `hi` when they tie with `a[mid]`, making the worst case O(n).

----------------------------------------

## Step 8: Complexity

Time: **O(log n)**. Each iteration halves the search range.
Space: **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int search(vector<int>& a, int target) {
    int lo = 0, hi = a.size() - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;    // avoid overflow
        if (a[mid] == target) return mid;
        if (a[lo] <= a[mid]) {            // left half sorted
            if (a[lo] <= target && target < a[mid]) hi = mid - 1;
            else lo = mid + 1;
        } else {                          // right half sorted
            if (a[mid] < target && target <= a[hi]) lo = mid + 1;
            else hi = mid - 1;
        }
    }
    return -1;
}
```

Note the use of `lo + (hi - lo) / 2` instead of `(lo + hi) / 2` — the latter can overflow for large arrays.

----------------------------------------

## Step 10: Follow-up Questions

- **Find the rotation point (the original index 0).** Binary search for the "break point" where `a[mid] > a[mid+1]`.
- **Rotated array with duplicates (Search in RSA II).** When `a[lo] == a[mid]`, we can't tell which side is sorted, so shrink `lo`. Worst case O(n) but still fast on average.
- **Find minimum in rotated sorted array.** Find the pivot — the smallest element. Binary search comparing `a[mid]` with `a[hi]`.
- **Search in a 2D matrix that's row-sorted and circularly-rotated per row.** Solve each row independently; total O(m log n).
- **Can we count the number of rotations?** Equivalent to finding the pivot index.
