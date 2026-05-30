# Reverse Pairs

**Problem Link:**
<a href="https://leetcode.com/problems/reverse-pairs/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/reverse-pairs/</a>

**Topic:**
Sorting / Divide and Conquer

----------------------------------------

## Step 1: Define a Reverse Pair

Given an integer array `nums`, a **reverse pair** is a pair of indices `(i, j)` such that:
- `i < j`, AND
- `nums[i] > 2 · nums[j]`.

Return the total count of reverse pairs.

Example: `nums = [1, 3, 2, 3, 1]`. Reverse pairs:
- (i=1, j=4): nums[1]=3, 2·nums[4]=2. 3 > 2 ✓.
- (i=3, j=4): nums[3]=3, 2·nums[4]=2. 3 > 2 ✓.
- Others? (i=0, j=4): 1 > 2? No. (i=1, j=2): 3 > 4? No. etc.

Count = **2**.

Example: `nums = [2, 4, 3, 5, 1]`.
- (0, 4): 2 > 2? No.
- (1, 4): 4 > 2? Yes. ✓
- (2, 4): 3 > 2? Yes. ✓
- (3, 4): 5 > 2? Yes. ✓
Count = **3**.

----------------------------------------

## Step 2: Brute Force

Two nested loops: for each i < j, check if nums[i] > 2 · nums[j]. O(n²). For n = 5·10⁴, that's 2.5·10⁹ — too slow.

We need O(n log n).

----------------------------------------

## Step 3: Why This Feels Like Inversion Counting

Counting inversions (pairs where `nums[i] > nums[j]` with i < j) is a classic problem solved with **merge sort** in O(n log n). Reverse pairs is nearly the same, but with the extra factor of 2.

Merge sort's "conquer" step merges two sorted halves. During this merge, we can count "how many elements in the left half exceed (or beat some condition) elements in the right half" — because once elements are sorted, monotonic pointers let us count in a single sweep.

**Plan:** adapt merge sort. During the merge, count reverse pairs where `i` is in the left half and `j` is in the right half. Recursively count pairs entirely within each half.

----------------------------------------

## Step 4: Counting During Merge

Suppose we have sorted left half L and sorted right half R. We want to count pairs (l, r) where l ∈ L, r ∈ R, and `L[l] > 2 · R[r]`. (And position-wise, every l comes before every r since L was the left half.)

Since L and R are each sorted, we can use a two-pointer scan:
- For each l in L (walking left to right), find the largest r such that `L[l] > 2 · R[r]`. All indices 0..r qualify.
- Because L is sorted ascending, as l increases, L[l] increases, so the threshold stays ≥ current r — the pointer only moves forward.

```
j = 0
for l in 0..|L|-1:
    while j < |R| and L[l] > 2 * R[j]:
        j++
    count += j         # j indices in R satisfy
```

This counts all cross-half reverse pairs in O(|L| + |R|).

After counting, we still need to **merge** L and R back into a sorted array for the parent call. That's standard merge-sort merging.

----------------------------------------

## Step 5: Algorithm (Merge Sort with Counting)

```
def mergeSortCount(nums, lo, hi):
    if lo >= hi: return 0
    mid = (lo + hi) // 2
    count = mergeSortCount(nums, lo, mid) + mergeSortCount(nums, mid + 1, hi)

    # Count cross-half reverse pairs
    j = mid + 1
    for i in lo..mid:
        while j <= hi and nums[i] > 2 * nums[j]:
            j++
        count += j - (mid + 1)

    # Merge lo..mid and mid+1..hi into sorted order
    merge(nums, lo, mid, hi)
    return count
```

Two passes per level: one to count (separate pointers), one to merge. O(n) per level, O(log n) levels → **O(n log n)**.

Why count BEFORE merging? Because after merging, we lose the "left half vs right half" distinction; we'd need to count in a different way.

----------------------------------------

## Step 6: Trace on `[1, 3, 2, 3, 1]`

Split recursively:
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

**[3, 1] merge** (lo=3, mid=3, hi=4):
- Left = [3], right = [1]. Check i=0: nums[0]=3 > 2·1=2? Yes. j advances. count += 1.
- Merge: [1, 3]. Array segment becomes [1, 3].

**[2, 3, 1] merge** (lo=2, mid=2, hi=4):
- Left = [2] (just index 2), right = [1, 3] (indices 3,4, already sorted).
- i=0: nums[2]=2 > 2·1=2? No. 2 > 2·3=6? No. count += 0.
- Merge: [1, 2, 3]. Array segment becomes [1, 2, 3].

**[1, 3] merge**:
- Left = [1], right = [3]. 1 > 6? No. count += 0. Merge: [1, 3].

**Top-level merge** (lo=0, mid=1, hi=4):
- Left = [1, 3], right = [1, 2, 3].
- i=0: nums[0]=1. Check 1 > 2·1 = 2? No. j stays at 2 (mid+1). count += 0.
- i=1: nums[1]=3. Check 3 > 2·1=2? Yes. j=3. Check 3 > 2·2=4? No. count += (3 - 2) = 1.

Total from this level: 1.

Grand total: 1 (from [3,1]) + 0 + 0 + 1 (top) = **2**. ✓

----------------------------------------

## Step 7: Why Two Pointers Work

Key property: **L is sorted ascending.** When we advance `i` (moving to a larger L[i]), the condition `L[i] > 2·R[j]` becomes easier to satisfy, so `j` (the count threshold) only moves forward. No backtracking.

This is why the two-pointer scan is O(|L| + |R|), not O(|L|·|R|).

If L weren't sorted, we couldn't skip — we'd have to re-check for every i separately.

----------------------------------------

## Step 8: Name It

**Merge sort with auxiliary counting** — a pattern used for:
- Inversion count.
- Count of smaller numbers after self (LeetCode 315).
- Count of range sums (LeetCode 327).
- Reverse pairs (this problem).

Alternative: **Binary Indexed Tree (BIT / Fenwick tree)** on coordinate-compressed values, or **segment tree**. Also O(n log n) but with different constants. Merge sort is often cleaner to write.

----------------------------------------

## Step 9: Complexity

Time: **O(n log n)**.
Space: **O(n)** for the merge buffer.

----------------------------------------

## Step 10: C++ Implementation

```cpp
class Solution {
    long long answer = 0;

    void mergeSort(vector<int>& nums, int lo, int hi) {
        if (lo >= hi) return;
        int mid = lo + (hi - lo) / 2;
        mergeSort(nums, lo, mid);
        mergeSort(nums, mid + 1, hi);

        // Count reverse pairs with i in [lo, mid], j in [mid+1, hi]
        int j = mid + 1;
        for (int i = lo; i <= mid; ++i) {
            while (j <= hi && (long long)nums[i] > 2LL * nums[j]) j++;
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
        for (int i = 0; i < (int)tmp.size(); ++i) nums[lo + i] = tmp[i];
    }

public:
    int reversePairs(vector<int>& nums) {
        if (nums.empty()) return 0;
        mergeSort(nums, 0, nums.size() - 1);
        return (int)answer;
    }
};
```

Critical detail: use `long long` / `2LL` when computing `2 · nums[j]` — `nums[j]` can be near INT_MIN or INT_MAX, and doubling can overflow 32-bit. The comparison must use wider arithmetic.

----------------------------------------

## Step 11: Follow-up Questions

- **Count pairs with `nums[i] > k · nums[j]` for arbitrary k.** Same algorithm; swap the `2` for `k`.
- **Count inversions (k = 1).** Same template, but the count naturally merges with the merging step itself (condition check during merge). Simpler code.
- **Using BIT instead.** Coordinate-compress `nums` and `2·nums`, then scan right to left, for each j adding to the count positions greater than 2·nums[j], then inserting nums[j] into the BIT at its compressed position.
- **Negative numbers and overflow.** Use 64-bit arithmetic for `2 · nums[j]`.
- **Stable ordering matters?** Doesn't affect count, only the final sorted order. Merge sort is naturally stable.
- **Can we do linear time?** No — reverse pair count is not computable in sub-O(n log n) without special structure.
