# Search in Rotated Sorted Array — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Search_in_Rotated_Sorted_Array.md`](../Search_in_Rotated_Sorted_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/search-in-rotated-sorted-array/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **This is the canonical "binary search with case analysis" problem.** The lesson: **even when the array isn't globally sorted, you can often find a HALF that IS sorted at each midpoint — and use it to decide where the target lives.** This pattern recurs in "Find Min in Rotated," "Search Rotated II (duplicates)," and Median of Two Sorted Arrays (advanced). **Read [`Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](./Find_First_and_Last_Position_of_Element_in_Sorted_Array.md) first.**

**Map of this file (11 short sections):**

1. Read the problem
2. What rotation looks like
3. Why plain binary search breaks
4. The structural observation — half is always sorted
5. The case analysis
6. The algorithm
7. Code
8. Trace it
9. Edge cases
10. Common pitfalls
11. The shape — locally sorted halves

---

## 1. Read the problem

You're given an array `nums` of distinct integers that was originally sorted in ascending order, then **rotated** at an unknown pivot index `k` (where `0 <= k < n`).

After rotation, the array looks like `[nums[k], nums[k+1], ..., nums[n-1], nums[0], nums[1], ..., nums[k-1]]`.

Given the rotated array and a target value, return the **index of the target** if found, else `-1`.

**Required:** O(log n) time.

**Examples:**

- `nums = [4, 5, 6, 7, 0, 1, 2]`, target = `0` → index `4`.
- `nums = [4, 5, 6, 7, 0, 1, 2]`, target = `3` → `-1`.
- `nums = [1]`, target = `0` → `-1`.

> **Mini-refresher: rotation explained.**
>
> Take `[0, 1, 2, 4, 5, 6, 7]` (sorted). Rotate by 3 positions: take the first 3 elements off the front and put them at the back. Get `[4, 5, 6, 7, 0, 1, 2]`.
>
> Or visualize it as a CIRCLE that you've cut at a different starting point. The order around the circle is unchanged.
>
> Rotation by 0 or n: no change (the array is still sorted).

---

## 2. What rotation looks like

A rotated sorted array has TWO sorted segments:
- **Left segment**: `nums[0..k-1]` — increasing, all values ≥ some threshold.
- **Right segment**: `nums[k..n-1]` — increasing, all values ≤ that threshold.

Actually wait — let me think again. After rotation by `k`, the array is `[nums_orig[k], ..., nums_orig[n-1], nums_orig[0], ..., nums_orig[k-1]]`. So:
- First part of the rotated array: the LARGER half of the original.
- Second part: the SMALLER half.

For `[4, 5, 6, 7, 0, 1, 2]`:
- First part: 4, 5, 6, 7 (sorted, larger values).
- Second part: 0, 1, 2 (sorted, smaller values).

There's exactly ONE "break point" (between 7 and 0). Otherwise, both segments are monotonically increasing.

---

## 3. Why plain binary search breaks

If you blindly do `nums[mid] < target → go right`, you can fail. Consider:

```
nums = [4, 5, 6, 7, 0, 1, 2], target = 0.
lo=0, hi=6. mid=3. nums[3]=7. 7 < 0? No. So go LEFT (standard binary search).
But target 0 is in the RIGHT half. We'd never find it.
```

The "sorted-array invariant" that powers plain binary search (smaller values on the left, larger on the right) is broken by the rotation. We need a more careful decision at the midpoint.

---

## 4. The structural observation — half is always sorted

Here's the saving grace. Even though the WHOLE array isn't sorted, **at any midpoint, ONE of the two halves is sorted**.

Why? The array has exactly ONE break point. When we split at `mid`, one of two cases:
- **The break point is in the right half:** then the LEFT half is purely sorted.
- **The break point is in the left half:** then the RIGHT half is purely sorted.

Either way, ONE side is a sorted sub-array. We can detect which side is sorted in O(1) by comparing endpoints, and then use it.

> **Mini-refresher: detecting which half is sorted.**
>
> Compare `nums[lo]` to `nums[mid]`:
> - If `nums[lo] <= nums[mid]`: **the left half is sorted** (going strictly UP from lo to mid).
> - Else: **the right half is sorted** (the break is in the left).
>
> Why does the comparison work? If left half is unbroken (sorted), it must satisfy `nums[lo] <= nums[mid]`. If left half has the break point, somewhere inside it values DROP, so `nums[lo] > nums[mid]`.
>
> We use `<=` (not `<`) to handle the edge case where `lo == mid` (a length-1 range — trivially "sorted").

---

## 5. The case analysis

Once we know which half is sorted, we can check in O(1) whether the target falls inside its sorted range:

**Case 1: LEFT half is sorted** (`nums[lo] <= nums[mid]`).
- Sorted range: `[nums[lo], nums[mid]]`.
- Is target in this range? I.e., `nums[lo] <= target < nums[mid]`?
  - YES → target is in the left half. Set `hi = mid - 1`.
  - NO → target must be in the right half (if anywhere). Set `lo = mid + 1`.

**Case 2: RIGHT half is sorted** (`nums[lo] > nums[mid]`).
- Sorted range: `[nums[mid], nums[hi]]`.
- Is target in this range? I.e., `nums[mid] < target <= nums[hi]`?
  - YES → target is in the right half. Set `lo = mid + 1`.
  - NO → target must be in the left half. Set `hi = mid - 1`.

Of course, before all of this: if `nums[mid] == target`, return `mid` immediately.

---

## 6. The algorithm

```
lo, hi = 0, n - 1
while lo <= hi:
    mid = lo + (hi - lo) // 2
    if nums[mid] == target:
        return mid

    if nums[lo] <= nums[mid]:                       # left half sorted
        if nums[lo] <= target < nums[mid]:
            hi = mid - 1
        else:
            lo = mid + 1
    else:                                              # right half sorted
        if nums[mid] < target <= nums[hi]:
            lo = mid + 1
        else:
            hi = mid - 1

return -1
```

Each iteration halves the search range → O(log n).

---

## 7. Code

**C++:**

```cpp
int search(vector<int>& nums, int target) {
    int lo = 0, hi = nums.size() - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (nums[mid] == target) return mid;

        if (nums[lo] <= nums[mid]) {                 // left half sorted
            if (nums[lo] <= target && target < nums[mid]) {
                hi = mid - 1;
            } else {
                lo = mid + 1;
            }
        } else {                                       // right half sorted
            if (nums[mid] < target && target <= nums[hi]) {
                lo = mid + 1;
            } else {
                hi = mid - 1;
            }
        }
    }
    return -1;
}
```

**Python:**

```python
def search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1
```

Complexity: **O(log n) time, O(1) space.**

---

## 8. Trace it

**`nums = [4, 5, 6, 7, 0, 1, 2]`, target = 0:**

```
lo=0, hi=6.
mid=3. nums[3]=7. Not target.
nums[lo]=4 <= nums[mid]=7 → LEFT sorted.
Range: [4, 7). Is 4 <= 0 < 7? NO. → lo = 4.

lo=4, hi=6.
mid=5. nums[5]=1. Not target.
nums[lo]=0 <= nums[mid]=1 → LEFT sorted (the sub-left is just [0, 1]).
Range: [0, 1). Is 0 <= 0 < 1? YES. → hi = 4.

lo=4, hi=4.
mid=4. nums[4]=0. MATCH. Return 4.  ✓
```

**`nums = [4, 5, 6, 7, 0, 1, 2]`, target = 3:**

```
lo=0, hi=6. mid=3. nums[3]=7 ≠ 3.
Left sorted. Range [4, 7). Is 3 in [4, 7)? NO. lo = 4.

lo=4, hi=6. mid=5. nums[5]=1 ≠ 3.
Left sorted (sub: [0, 1]). Range [0, 1). Is 3 in [0, 1)? NO. lo = 6.

lo=6, hi=6. mid=6. nums[6]=2 ≠ 3.
Left sorted (sub: [2]). Range [2, 2). Is 3 in [2, 2)? NO. lo = 7.

lo > hi. Return -1.  ✓
```

---

## 9. Edge cases

- **Not rotated (rotated by 0):** the array is fully sorted. `nums[lo] <= nums[mid]` always holds. The left-sorted branch always fires. Algorithm degenerates to classical binary search. ✓
- **Rotated by n:** same as not rotated. ✓
- **Single element:** lo = hi = 0. One iteration. Match or return -1. ✓
- **Target at the boundary (the break point):** the break-side is the right half. Should be caught by the right-sorted case. ✓
- **Target equals `nums[lo]` or `nums[hi]`:** the `<=` comparisons in the range checks handle this.

> **Mini-refresher: the `<=` vs `<` in the range checks.**
>
> For left-sorted: `nums[lo] <= target < nums[mid]`. Inclusive on `lo`, exclusive on `mid` (because `mid` was already checked above and isn't the target — but if it WERE the target, we'd have returned earlier).
> For right-sorted: `nums[mid] < target <= nums[hi]`. Exclusive on `mid`, inclusive on `hi`.
>
> The asymmetry is because the "mid != target" check fires first, so we know target ≠ nums[mid].

---

## 10. Common pitfalls

1. **Forgetting the `nums[mid] == target` check at the TOP of the loop.** Without it, you'd never find the target.

2. **Using `<` instead of `<=` in `nums[lo] <= nums[mid]`.** When `lo == mid` (length-1 range), `nums[lo] == nums[mid]`, but `<` would be FALSE. Use `<=`.

3. **Confusing the two ranges' endpoint conventions.** Left sorted: `[nums[lo], nums[mid])`. Right sorted: `(nums[mid], nums[hi]]`. Mind the inclusive/exclusive sides.

4. **Trying to handle duplicates** with this exact algorithm. With duplicates, `nums[lo] == nums[mid]` doesn't tell you which half is sorted. The variant "Search in Rotated Sorted Array II" handles this with extra shrinking and worst-case O(n).

5. **Iterating with `while lo < hi` (strict) instead of `lo <= hi`.** This template uses `lo <= hi` because we update `hi = mid - 1` (exclusive of mid). Mixing templates causes bugs.

6. **Updating `hi = mid` instead of `hi = mid - 1`.** Combined with `lo <= hi`, this causes infinite loops.

7. **Searching for the pivot first, then doing TWO binary searches.** Works but two-pass; the unified approach is cleaner and still O(log n).

8. **Returning `mid` only when target is at `lo` or `hi`.** Return `mid` anytime `nums[mid] == target`.

---

## 11. The shape — locally sorted halves

This pattern — "at each midpoint, ONE half has a usable structural property" — generalizes:

| Problem | Local property at midpoint |
|---|---|
| **This problem** | one half is sorted (no break point) |
| Find Minimum in Rotated Sorted Array | `nums[mid] > nums[hi]` → min in right half |
| Search in Rotated Sorted Array II (duplicates) | mostly the same, with shrink-on-tie |
| Find Peak Element | `nums[mid] < nums[mid+1]` → peak in right half |
| Search in a Bitonic Array | first find peak, then binary search each side |
| Median of Two Sorted Arrays | complex case analysis on which half of each contains the median |

**Pattern to internalize:**

> "Even on non-sorted data, if you can do CASE ANALYSIS at the midpoint and reliably narrow the search to a HALF where the answer must be, you get O(log n). Often the case analysis is: 'which half is well-behaved (sorted / monotone / has the right slope)?'"

The complexity of case analysis grows with the data's irregularity. But the payoff (log time vs linear) is decisive.

---

> **Self-check — the question to ask next time.**
>
> When you face an O(log n) problem on data with SOME structure (rotated, bitonic, sliced), ask:
>
> > **"At any midpoint, can I do case analysis to determine WHICH HALF is well-behaved and whether the target lives in it?"**
>
> If yes, binary search applies despite the irregular global structure.

---

## Cross-references

- **Reference card (post-mastery):** [`../Search_in_Rotated_Sorted_Array.md`](../Search_in_Rotated_Sorted_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](./Find_First_and_Last_Position_of_Element_in_Sorted_Array.md), [`Find_Peak_Element.md`](./Find_Peak_Element.md).
  - Coming next: [`Single_Element_in_a_Sorted_Array.md`](./Single_Element_in_a_Sorted_Array.md), [`Search_a_2D_Matrix.md`](./Search_a_2D_Matrix.md).
