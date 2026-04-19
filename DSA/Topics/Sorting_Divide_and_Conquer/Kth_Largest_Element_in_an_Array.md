# Kth Largest Element in an Array (Sorting / Divide and Conquer)

**Problem Link:**
https://leetcode.com/problems/kth-largest-element-in-an-array/

**Topic:**
Sorting / Divide and Conquer

----------------------------------------

## Step 1: The Problem

Given `nums` and integer k, return the **k-th largest** element. Duplicates count as distinct entries.

Example: `nums = [3, 2, 1, 5, 6, 4]`, k = 2. Sorted descending: [6, 5, 4, 3, 2, 1]. 2nd largest = **5**.
Example: `nums = [3, 2, 3, 1, 2, 4, 5, 5, 6]`, k = 4. Sorted descending: [6, 5, 5, 4, ...]. 4th = **4**.

This note focuses on the **divide-and-conquer (Quickselect) approach**. The heap-based version appears in the Heap topic notes.

----------------------------------------

## Step 2: Full Sort Baseline

Sort `nums` in ascending order, return `nums[n - k]`. O(n log n). Simple but wasteful — we're computing the entire ordering when we need just one rank.

Can we find the k-th largest without sorting everything?

----------------------------------------

## Step 3: Borrow From Quicksort

Quicksort's key operation is **partition**: choose a pivot, rearrange the array so that all elements ≥ pivot come first, then all elements < pivot. After partition, the pivot ends up at its final position in the sorted order.

If after partitioning, the pivot sits exactly at index `n - k` (from the left, in ascending sort), it's the k-th largest. Done.

If the pivot is at a smaller index (too far left), the k-th largest lies somewhere to its right — recurse right.

If the pivot is at a larger index, recurse left.

Unlike quicksort, **we only recurse into ONE side** — the one containing the target rank. That's where the speedup comes from.

----------------------------------------

## Step 4: Average-Case Linear Time

With random pivots, each recursion works on roughly half the size:
- n + n/2 + n/4 + ... ≈ 2n = O(n).

Average time: **O(n)**. Much better than O(n log n).

Worst case (adversarial pivots on a sorted array): O(n²). Mitigate by choosing the pivot randomly, or by using median-of-medians for a deterministic O(n).

----------------------------------------

## Step 5: Algorithm

```
def quickselect(nums, lo, hi, targetIdx):
    if lo == hi: return nums[lo]
    pivot_idx = random index in [lo, hi]
    pivot_idx = partition(nums, lo, hi, pivot_idx)
    if pivot_idx == targetIdx: return nums[targetIdx]
    elif pivot_idx < targetIdx: return quickselect(nums, pivot_idx + 1, hi, targetIdx)
    else: return quickselect(nums, lo, pivot_idx - 1, targetIdx)

return quickselect(nums, 0, n - 1, n - k)      # n - k in ascending order
```

The `partition` function:
1. Move pivot to `hi`.
2. Walk `i` from `lo`; if `nums[i] < pivot`, swap with position `store_idx`, advance.
3. At the end, swap pivot into `store_idx`. Return `store_idx`.

This classic Lomuto partition places elements < pivot left of store_idx, ≥ pivot to the right, with the pivot at store_idx.

----------------------------------------

## Step 6: Trace on `[3, 2, 1, 5, 6, 4]`, k = 2

We want the 2nd largest → ascending index n - k = 6 - 2 = 4.

```
quickselect(nums, 0, 5, 4).
Say random pivot_idx = 3 (value 5). Partition around 5.
  After partition: smaller values left, pivot at some store_idx.
  Walk: 3 < 5 ✓ (stays), 2 < 5 ✓, 1 < 5 ✓, 4 < 5 ✓, 6 ≥ 5 (stays right).
  Pivot ends at index 4.
store_idx = 4 == targetIdx 4. Return nums[4] = 5.
```

Return **5**. ✓ (No recursion needed since the first partition landed on the target.)

If the random pivot had been 0 (value 3), after partitioning, nums would be like [1, 2, 3, 5, 6, 4] (3 at index 2). pivot_idx = 2 < 4. Recurse into [3, 5]: quickselect(nums, 3, 5, 4). That's a small subarray; one more partition would finish it.

----------------------------------------

## Step 7: Why Randomize?

Without randomization, on a pre-sorted input `[1, 2, 3, 4, 5]` with pivot = last, each partition only shaves one element off — O(n²).

Random pivot makes worst-case inputs improbable. Over time, the expected running time is O(n).

Even better (for guaranteed O(n)): **median-of-medians** — a deterministic pivot choice guaranteeing ≥ 30% of elements fall on each side. In practice, randomization is preferred for its simpler implementation and better constants.

----------------------------------------

## Step 8: Name It

**Quickselect** — a classical divide-and-conquer selection algorithm, introduced by Hoare (same Hoare as quicksort).

Applications:
- Median (k = n/2).
- Top-k queries (find the cutoff, then partition around it).
- Weighted selection.

The heap-based approach (min-heap of size k) has complementary strengths: better when n is huge and streaming, worse for in-memory bulk data.

----------------------------------------

## Step 9: Complexity

Average: **O(n)**.
Worst: O(n²) (without precautions) or O(n) (with median-of-medians).
Space: **O(log n)** recursion depth on average.

----------------------------------------

## Step 10: C++ Implementation

```cpp
class Solution {
    int partition(vector<int>& nums, int lo, int hi, int pivotIdx) {
        int pivot = nums[pivotIdx];
        swap(nums[pivotIdx], nums[hi]);
        int store = lo;
        for (int i = lo; i < hi; ++i) {
            if (nums[i] < pivot) {
                swap(nums[store], nums[i]);
                store++;
            }
        }
        swap(nums[store], nums[hi]);
        return store;
    }

    int quickselect(vector<int>& nums, int lo, int hi, int targetIdx) {
        if (lo == hi) return nums[lo];
        int pivotIdx = lo + rand() % (hi - lo + 1);
        pivotIdx = partition(nums, lo, hi, pivotIdx);
        if (pivotIdx == targetIdx) return nums[targetIdx];
        if (pivotIdx < targetIdx) return quickselect(nums, pivotIdx + 1, hi, targetIdx);
        return quickselect(nums, lo, pivotIdx - 1, targetIdx);
    }

public:
    int findKthLargest(vector<int>& nums, int k) {
        return quickselect(nums, 0, nums.size() - 1, nums.size() - k);
    }
};
```

Key detail: `nums.size() - k` is the index in **ascending** order where the k-th largest sits.

----------------------------------------

## Step 11: Follow-up Questions

- **k-th smallest.** Target index = k - 1.
- **Duplicates at the pivot.** Lomuto partition handles them but packs duplicates on one side. Hoare or three-way partition avoids lopsidedness.
- **Return the top k elements (not just the k-th).** After quickselect on index n - k, the subarray [n-k .. n-1] contains the top k (unsorted).
- **Deterministic O(n) worst case.** Median-of-medians pivot — introsort, BFPRT.
- **Streaming / external memory.** Quickselect needs random access; switch to heap-based approach.
- **Why recurse only into one side?** Because the pivot's final position reveals the target's side definitively — no need to explore the other.
