# Reverse Pairs — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Reverse_Pairs.md`](../Reverse_Pairs.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/reverse-pairs/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~24 minutes. **Senior bar:** modify merge sort to COUNT cross-half pairs satisfying a custom predicate. The lesson: **merge sort's "conquer" step naturally lets you count pairs (i, j) where i is in the LEFT half and j in the RIGHT — in O(n) per merge level, O(n log n) total.** Same template counts inversions, "smaller after self," range sums. **Read [`Kth_Largest_Element_in_an_Array.md`](./Kth_Largest_Element_in_an_Array.md) and Merge_Two_Sorted_Lists first** for divide-and-conquer and merging.

**Map of this file (10 sections):**

1. Read the problem
2. The brute force
3. Connection to inversion counting
4. The merge-sort plan
5. The two-pointer count step
6. Code
7. Trace it
8. Why count BEFORE merging
9. Common pitfalls
10. The shape — merge sort as a counting primitive

---

## 1. Read the problem

Given an integer array `nums`, a **reverse pair** is a pair `(i, j)` with:
- `0 <= i < j < n`, AND
- `nums[i] > 2 * nums[j]`.

Return the **total count** of reverse pairs.

**Examples:**

- `nums = [1, 3, 2, 3, 1]` → pairs: (1, 4): 3 > 2; (3, 4): 3 > 2. Count = **2**.
- `nums = [2, 4, 3, 5, 1]` → pairs: (1, 4): 4 > 2; (2, 4): 3 > 2; (3, 4): 5 > 2. Count = **3**.

---

## 2. The brute force

Two nested loops:

```
count = 0
for i in 0..n-2:
    for j in i+1..n-1:
        if nums[i] > 2 * nums[j]: count += 1
return count
```

O(n²). For n = 5 × 10⁴, that's 2.5 × 10⁹ ops — TLE.

We need O(n log n).

---

## 3. Connection to inversion counting

> **Mini-refresher: inversion counting.**
>
> An **inversion** in an array is a pair (i, j) with `i < j` and `nums[i] > nums[j]`. Counting inversions is a classical problem.
>
> Naïve: O(n²). Smart: **merge sort** in O(n log n).
>
> Reverse Pairs is a generalization: count pairs where `nums[i] > 2 * nums[j]` (the factor 2 distinguishes it).

The merge-sort approach to inversions counts pairs DURING the merge step. We'll adapt the same idea for our predicate `nums[i] > 2 * nums[j]`.

---

## 4. The merge-sort plan

```
mergeSortCount(nums, lo, hi):
    if lo >= hi: return 0
    mid = (lo + hi) // 2
    count = mergeSortCount(nums, lo, mid) + mergeSortCount(nums, mid + 1, hi)
    count += countCrossPairs(nums, lo, mid, hi)
    merge(nums, lo, mid, hi)
    return count
```

Each merge level:
1. Recurse into left and right halves, getting counts of pairs WITHIN each.
2. Count cross-half pairs (i in left, j in right) satisfying our predicate.
3. Merge the two sorted halves.

Total: O(n) per level × O(log n) levels = **O(n log n)**.

---

## 5. The two-pointer count step

Critical step: count pairs `(i, j)` with `i` in `[lo, mid]`, `j` in `[mid + 1, hi]`, and `nums[i] > 2 * nums[j]`.

Because BOTH halves are sorted (from recursion), use a TWO-POINTER scan:

```
j = mid + 1
for i in lo..mid:
    while j <= hi and nums[i] > 2 * nums[j]:
        j += 1
    count += (j - (mid + 1))   # j elements in right half satisfy the predicate
```

> **Mini-refresher: why the two-pointer scan is O(n).**
>
> For each `i` in the left (sorted, ascending), find the LARGEST `j` such that `nums[i] > 2 * nums[j]`. All indices `mid+1, mid+2, ..., j-1` qualify.
>
> Because left is sorted ASCENDING, as i increases, `nums[i]` increases. So MORE j's qualify (or the same). The pointer `j` only MOVES FORWARD — never resets.
>
> Total cost across all i: at most `|right|` advances of j, plus `|left|` outer iterations. O(|left| + |right|).

Without sortedness, we'd be back to O(|left| × |right|).

---

## 6. Code

**C++:**

```cpp
class Solution {
    long long answer = 0;

    void mergeSort(vector<int>& nums, int lo, int hi) {
        if (lo >= hi) return;
        int mid = lo + (hi - lo) / 2;
        mergeSort(nums, lo, mid);
        mergeSort(nums, mid + 1, hi);

        // Count cross-half pairs (i in [lo, mid], j in [mid+1, hi])
        int j = mid + 1;
        for (int i = lo; i <= mid; ++i) {
            while (j <= hi && (long long)nums[i] > 2LL * nums[j]) {
                j++;
            }
            answer += (j - (mid + 1));
        }

        // Standard merge
        vector<int> tmp(hi - lo + 1);
        int a = lo, b = mid + 1, k = 0;
        while (a <= mid && b <= hi) {
            tmp[k++] = nums[a] <= nums[b] ? nums[a++] : nums[b++];
        }
        while (a <= mid) tmp[k++] = nums[a++];
        while (b <= hi) tmp[k++] = nums[b++];
        for (int x = 0; x < (int)tmp.size(); ++x) nums[lo + x] = tmp[x];
    }

public:
    int reversePairs(vector<int>& nums) {
        if (nums.empty()) return 0;
        mergeSort(nums, 0, nums.size() - 1);
        return (int)answer;
    }
};
```

**CRUCIAL DETAIL:** use `(long long)nums[i] > 2LL * nums[j]`. `nums[i]` can be near `INT_MAX` or `INT_MIN`; doubling overflows 32-bit. Use 64-bit arithmetic.

**Python:**

```python
def reversePairs(nums):
    def merge_sort(lo, hi):
        if lo >= hi:
            return 0
        mid = (lo + hi) // 2
        count = merge_sort(lo, mid) + merge_sort(mid + 1, hi)

        # Count cross-half pairs
        j = mid + 1
        for i in range(lo, mid + 1):
            while j <= hi and nums[i] > 2 * nums[j]:
                j += 1
            count += j - (mid + 1)

        # Merge
        nums[lo:hi + 1] = sorted(nums[lo:hi + 1])    # quick-and-dirty merge
        return count

    return merge_sort(0, len(nums) - 1)
```

Complexity: **O(n log n) time, O(n) space.**

---

## 7. Trace it

**`nums = [1, 3, 2, 3, 1]`.**

Tree of splits:
```
[1, 3, 2, 3, 1]
├── [1, 3]
│   ├── [1]
│   └── [3]
└── [2, 3, 1]
    ├── [2]
    └── [3, 1]
        ├── [3]
        └── [1]
```

**Bottom-up:**

`merge(3, 4)` of [3] and [1]:
- Count: i=3 (nums[3]=3). Walk j from 4. nums[3]=3 > 2·1=2? YES → j=5. count += 1.
- Merge → [1, 3] at positions 3-4.

`merge(2, 4)` of [2] and [1, 3]:
- Count: i=2 (nums[2]=2). j starts at 3.
  - nums[2]=2 > 2·nums[3]=2·1=2? NO. (2 > 2 is false.)
  - Stop. count += 0.
- Merge → [1, 2, 3] at positions 2-4.

`merge(0, 1)` of [1] and [3]:
- Count: 1 > 6? NO. count += 0.
- Merge → [1, 3] at positions 0-1.

`merge(0, 4)` of [1, 3] and [1, 2, 3]:
- i=0: nums[0]=1. j=2. 1 > 2? NO. count += 0.
- i=1: nums[1]=3. j=2. 3 > 2·1=2? YES → j=3. 3 > 2·2=4? NO. count += (3 - 2) = 1.
- Merge → [1, 1, 2, 3, 3].

Total: 1 + 0 + 0 + 1 = **2**.  ✓

---

## 8. Why count BEFORE merging

If we MERGE first, the left and right halves blend together — we lose the distinction. Then we can't tell which elements came from "left" vs "right" of the original split.

Counting BEFORE the merge uses the still-distinct halves' sortedness. The two-pointer scan works because both halves are independently sorted.

> **Mini-refresher: the order matters.**
>
> 1. Recurse left, recurse right. (Halves become sorted internally.)
> 2. **Count cross-half pairs** (halves still distinct).
> 3. Merge the two sorted halves into one sorted segment.
>
> Reversing steps 2 and 3 would break the algorithm.

---

## 9. Common pitfalls

1. **Integer overflow on `2 * nums[j]`.** Use 64-bit (`long long`, `2LL`). `nums[j]` near `INT_MIN` makes `2 * nums[j]` underflow. CRITICAL.

2. **Counting AFTER merging.** Halves blend; can't distinguish "i in left" from "j in right." Count BEFORE.

3. **Using `>=` instead of `>`.** The predicate is STRICTLY greater. Use `>`.

4. **Resetting `j` for each `i`.** Don't — that's O(n²). j moves monotonically forward.

5. **Forgetting that BOTH halves are sorted by the recursion.** This is what enables the two-pointer scan.

6. **Modifying the array during counting.** Don't merge until after counting.

7. **Using `int` for the count.** Reverse pair count can exceed `INT_MAX`. Use `long long` for the accumulator.

8. **Trying a BIT (Binary Indexed Tree) approach.** Also works (O(n log n) with coordinate compression), but merge sort is often cleaner for this problem.

---

## 10. The shape — merge sort as a counting primitive

Merge sort isn't just for SORTING. The merge step is a NATURAL way to compare LEFT vs RIGHT halves, enabling per-pair counting in O(n) per level.

Problems solved this way:

| Problem | Predicate counted during merge |
|---|---|
| **This problem** | `nums[i] > 2 * nums[j]` |
| Count Inversions | `nums[i] > nums[j]` |
| Count of Smaller Numbers After Self | per-element count of `nums[j] < nums[i]` |
| Count of Range Sum (LC #327) | `lower <= prefix[j] - prefix[i] <= upper` |
| Count Pairs with `|nums[i] - nums[j]| <= k` | similar two-pointer scan |

**Pattern to internalize:**

> "Merge sort's CONQUER step is a natural counting opportunity: two sorted halves let you count cross-pair properties via a two-pointer scan in O(n) per merge level. Combine with the recursion: O(n log n) total."

This is one of the most elegant patterns in algorithm design — modify a sort to do bonus work for free.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem about COUNTING PAIRS `(i, j)` with `i < j` and some predicate on `nums[i]` and `nums[j]`, ask:
>
> > **"Can I count via merge sort? During each merge, two-pointer scan the sorted halves to count cross-pair instances."**
>
> If yes, O(n log n) — beats O(n²) brute force.

---

## Cross-references

- **Reference card (post-mastery):** [`../Reverse_Pairs.md`](../Reverse_Pairs.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Sort_Colors.md`](./Sort_Colors.md), [`Kth_Largest_Element_in_an_Array.md`](./Kth_Largest_Element_in_an_Array.md).
  - Coming next: [`Count_of_Smaller_Numbers_After_Self.md`](./Count_of_Smaller_Numbers_After_Self.md) — same template, PER-element count.
