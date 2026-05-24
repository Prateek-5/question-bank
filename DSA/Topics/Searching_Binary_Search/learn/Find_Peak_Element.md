# Find Peak Element — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_Peak_Element.md`](../Find_Peak_Element.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/find-peak-element/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **This problem broadens binary search beyond "sorted arrays."** The lesson: **binary search works whenever you can derive a monotonic property from a LOCAL comparison at the midpoint — even if the array itself is unsorted.** Once you internalize this, you'll see binary search as "halving a search space using a monotonic invariant," not "lookup in a sorted array." **Read [`Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](./Find_First_and_Last_Position_of_Element_in_Sorted_Array.md) first** for the template.

**Map of this file (10 short sections):**

1. Read the problem
2. Definition — what's a "peak"?
3. The brute force
4. The slope insight
5. Why this gives a binary search
6. The algorithm
7. Code
8. Trace it
9. Common pitfalls
10. The shape — binary search on any monotonic decision

---

## 1. Read the problem

Given an array `nums` of integers (length n ≥ 1), return the index of **any peak element**.

A **peak** is an element strictly greater than its neighbors. The endpoints have only one neighbor each, and the "out of bounds" side is treated as `-∞`. So:
- `nums[0]` is a peak iff `nums[0] > nums[1]` (or n = 1).
- `nums[n-1]` is a peak iff `nums[n-1] > nums[n-2]`.
- For any `i` in the middle: `nums[i]` is a peak iff `nums[i-1] < nums[i] > nums[i+1]`.

The problem guarantees adjacent elements are different (so you don't have to handle ties).

**Required:** O(log n) time.

**You can return ANY peak** — not necessarily the global maximum. This freedom is what makes O(log n) possible.

**Examples:**

- `nums = [1, 2, 3, 1]` → index 2 (value 3, neighbors 2 and 1).
- `nums = [1, 2, 1, 3, 5, 6, 4]` → either index 1 (value 2, peaks against 1 and 1) OR index 5 (value 6, peaks against 5 and 4).

---

## 2. Definition — what's a "peak"?

> **Mini-refresher: peak vs global maximum.**
>
> A **peak** is a LOCAL maximum — strictly greater than its immediate neighbors. There may be MULTIPLE peaks in an array.
>
> The **global maximum** is the single largest value. The global max is always a peak, but a peak isn't always the global max.
>
> This problem accepts ANY peak. That's important — finding the global max requires O(n), but finding ANY peak can be done in O(log n) by exploiting local structure.

For an array of length 1, `nums[0]` is trivially a peak (no neighbors to compare against; both "neighbors" are -∞).

For `nums = [3, 2]`, the peak is index 0 (3 > 2 and -∞).
For `nums = [2, 3]`, the peak is index 1 (3 > 2 and -∞).

---

## 3. The brute force

Linear scan. For each i, check if it's a peak. Return the first one found.

```
for i in 0..n-1:
    left = nums[i-1] if i > 0 else -inf
    right = nums[i+1] if i < n-1 else -inf
    if nums[i] > left and nums[i] > right:
        return i
```

O(n). The problem promises a peak exists, so this always finds one. But O(n) doesn't meet the O(log n) requirement.

How do we use binary search when the array isn't sorted?

---

## 4. The slope insight

Consider the comparison `nums[mid]` vs `nums[mid + 1]`:

**Case A: `nums[mid] < nums[mid + 1]`** (slope going UP at position mid).

Claim: a peak exists in the right half `[mid + 1, n - 1]`.

Why? Starting at `mid + 1`, the value `nums[mid + 1]` is greater than its left neighbor (`nums[mid]`). Now walk right:
- If `nums[mid + 1] > nums[mid + 2]`: `mid + 1` is a peak. Done.
- Else `nums[mid + 1] < nums[mid + 2]`: the ascent continues. Move to `mid + 2`.

Keep walking right. Either we find a peak (some position where the slope changes from up to down), or we reach the END (`nums[n - 1]`). At the end, the "right neighbor" is `-∞`, so `nums[n - 1] > -∞`. Combined with the fact that the ascent has been monotone up to here (else we'd have already found a peak), `nums[n - 1] > nums[n - 2]`. So `nums[n - 1]` is a peak.

**Either way, a peak exists in `[mid + 1, n - 1]`.**

**Case B: `nums[mid] > nums[mid + 1]`** (slope going DOWN at position mid).

By symmetric argument, a peak exists in `[0, mid]` (the left half, including mid itself).

> **Mini-refresher: the "either-end is -∞" trick.**
>
> The argument relies on the "out of bounds = -∞" convention. As long as you're going UP and you reach the end of an interval, the end is a peak (because the OUTSIDE is -∞).
>
> Geometrically: imagine the array as a mountain landscape with -∞ on either side. If you start walking up, you MUST eventually hit a peak — you can't keep going up forever (the array is finite), and you can't suddenly stop "level" (adjacent elements are distinct). The peak is where the slope reverses.

---

## 5. Why this gives a binary search

We have a way to DECIDE between left and right halves using ONE comparison at the midpoint. That's the requirement for binary search.

The "monotonic predicate" here isn't on values directly — it's on the question "does the right half contain a peak?" That question is determined by the local comparison `nums[mid] vs nums[mid + 1]`, and the answer reliably narrows the search to a HALF where a peak is GUARANTEED to exist.

Each iteration halves the range. O(log n).

> **Mini-refresher: binary search doesn't require sorted data.**
>
> Binary search requires:
> 1. A SEARCH RANGE that can be halved.
> 2. A LOCAL TEST at the midpoint that tells you which half contains the answer.
>
> Sorted data is the most common setup (test: `nums[mid] vs target`). But ANY problem with property #2 admits binary search.
>
> Other examples:
> - **This problem:** peak finding on unsorted array.
> - **Search in rotated sorted array:** the array has two sorted segments; the midpoint tells you which segment contains the target.
> - **Search on a bitonic array:** strictly increasing then strictly decreasing.
> - **Square root by binary search:** test `mid * mid <= target`.

---

## 6. The algorithm

```
lo, hi = 0, n - 1
while lo < hi:
    mid = lo + (hi - lo) // 2
    if nums[mid] < nums[mid + 1]:
        lo = mid + 1                # peak in right half
    else:
        hi = mid                     # peak in left half (including mid)
return lo
```

Loop invariant: the range `[lo, hi]` ALWAYS contains a peak. Each iteration narrows the range by at least half.

When `lo == hi`, the range has narrowed to a single index — and by the invariant, THAT index is a peak.

> **Mini-refresher: safe `mid + 1` access.**
>
> We do `nums[mid + 1]`. For this to be safe, `mid + 1 <= n - 1`, i.e., `mid <= n - 2`.
>
> Since `mid = lo + (hi - lo) / 2` and `lo < hi`, we have `mid < hi <= n - 1`, so `mid + 1 <= hi <= n - 1`. Safe.
>
> If we had instead used `hi = n`, this safety wouldn't hold automatically. The choice `hi = n - 1` is INTENTIONAL here.

---

## 7. Code

**C++:**

```cpp
int findPeakElement(vector<int>& nums) {
    int lo = 0, hi = nums.size() - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (nums[mid] < nums[mid + 1]) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
```

**Python:**

```python
def findPeakElement(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < nums[mid + 1]:
            lo = mid + 1
        else:
            hi = mid
    return lo
```

**JavaScript:**

```javascript
function findPeakElement(nums) {
    let lo = 0, hi = nums.length - 1;
    while (lo < hi) {
        const mid = Math.floor((lo + hi) / 2);
        if (nums[mid] < nums[mid + 1]) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}
```

Complexity: **O(log n) time, O(1) space.**

---

## 8. Trace it

**Example: `nums = [1, 2, 1, 3, 5, 6, 4]`.**

```
lo=0, hi=6.

mid=3. nums[3]=3, nums[4]=5. 3 < 5 → ascent → lo = 4.
lo=4, hi=6.

mid=5. nums[5]=6, nums[6]=4. 6 > 4 → descent → hi = 5.
lo=4, hi=5.

mid=4. nums[4]=5, nums[5]=6. 5 < 6 → ascent → lo = 5.
lo=5, hi=5. EXIT.

Return 5. nums[5] = 6. Neighbors: 5, 4. PEAK. ✓
```

**Example: `nums = [1, 2, 3, 1]`.**

```
lo=0, hi=3.

mid=1. nums[1]=2, nums[2]=3. 2 < 3 → lo = 2.
lo=2, hi=3.

mid=2. nums[2]=3, nums[3]=1. 3 > 1 → hi = 2.
lo=2, hi=2. EXIT.

Return 2. nums[2] = 3. Neighbors: 2, 1. PEAK. ✓
```

**Edge: `nums = [1]`** (single element).

```
lo=0, hi=0. EXIT immediately.
Return 0.  ✓ (vacuously a peak)
```

**Edge: `nums = [2, 1]`** (descending).

```
lo=0, hi=1.

mid=0. nums[0]=2, nums[1]=1. 2 > 1 → hi = 0.
lo=0, hi=0. EXIT.

Return 0.  ✓ (nums[0]=2 with neighbor 1 and -∞; PEAK)
```

---

## 9. Common pitfalls

1. **Initializing `hi = n` instead of `hi = n - 1`.** Then `mid + 1` could exceed `n - 1` and segfault.

2. **Using `<=` in the loop instead of `<`.** Then when `lo == hi`, you'd do one more iteration, accessing `nums[mid + 1]` where `mid + 1 = hi + 1 = n`. Out of bounds.

3. **Comparing `nums[mid - 1]` vs `nums[mid]` instead of `nums[mid]` vs `nums[mid + 1]`.** The latter is safer (we already control `mid + 1 <= hi`).

4. **Wrong slope direction.** Confusing "ascent" (mid < mid + 1, go right) with "descent" (mid > mid + 1, go left). Sketch a graph on paper if confused.

5. **Trying to find the GLOBAL max.** That requires O(n). The problem only asks for any peak.

6. **Worrying about duplicates.** The problem guarantees adjacent elements differ. If duplicates were allowed, this O(log n) wouldn't work in general (worst case becomes O(n)).

7. **Wrapping the array as circular.** Don't. The endpoints have -∞ neighbors, not the other end.

8. **Returning `nums[lo]` instead of `lo`.** Read the question — it asks for the INDEX, not the value.

---

## 10. The shape — binary search on any monotonic decision

The lesson generalizes:

> **Binary search applies WHENEVER a local comparison at the midpoint reliably tells you which HALF contains a valid answer.**

| Problem | The local decision |
|---|---|
| **This problem** | `nums[mid] < nums[mid+1]` → ascent → go right |
| Find Minimum in Rotated Sorted Array | `nums[mid] > nums[hi]` → min is in right half |
| Search in Rotated Sorted Array | check which half is sorted, then check target's range |
| Search in a Bitonic Array | find the peak first, then binary search each half |
| Sqrt(x) | `mid * mid <= x` |
| Capacity to Ship Packages | feasibility(mid) → go left or right |
| Find K Closest Elements | `nums[mid + k] - x < x - nums[mid]` → go right |
| 2D Peak Finding | reduce to 1D peak per middle row |

**Pattern to internalize:**

> "Binary search ≠ sorted-array lookup. Binary search = halve a search range using a monotonic LOCAL decision. The decision can be anything: slope direction, feasibility, parity invariant. If you can decide which half contains the answer in O(1), you get O(log n) overall."

---

> **Self-check — the question to ask next time.**
>
> When you face an O(log n) problem on data that ISN'T sorted, ask:
>
> > **"Can I derive a LOCAL property at the midpoint that tells me which half contains a valid answer? (Slope, feasibility, parity, peak, etc.)"**
>
> If yes, binary search applies — even on unsorted data.

---

## Cross-references

- **Reference card (post-mastery):** [`../Find_Peak_Element.md`](../Find_Peak_Element.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](./Find_First_and_Last_Position_of_Element_in_Sorted_Array.md) — template for sorted-array search.
  - Coming next: Search_in_Rotated_Sorted_Array — binary search with a twist.
  - Coming after: Capacity_To_Ship_Packages, Magnetic_Force — binary search on the ANSWER.
