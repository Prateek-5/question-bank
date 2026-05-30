# Maximum Size Subarray Sum Equals K

**Problem Link:**
<a href="https://leetcode.com/problems/maximum-size-subarray-sum-equals-k/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/maximum-size-subarray-sum-equals-k/</a>

**Topic:**
Hashing / Sliding Window

----------------------------------------

## Step 1: Restate

Given an integer array `nums` (may contain negatives) and an integer `k`, find the **length of the longest contiguous subarray** summing to `k`. Return 0 if no such subarray exists.

Example: `nums = [1, -1, 5, -2, 3]`, k = 3.
- Subarray [1, -1, 5, -2] sums to 3. Length 4.
- Subarray [5, -2] sums to 3. Length 2.
- Subarray [3] sums to 3. Length 1.
- Longest: **4**.

Example: `nums = [-2, -1, 2, 1]`, k = 1.
- [-2, -1, 2, 1] sums to 0.
- [-1, 2] sums to 1. Length 2.
- [1] sums to 1. Length 1.
- Longest: **2**.

----------------------------------------

## Step 2: Brute-Force Baseline

Try every subarray. O(n²). For each start, accumulate sum; track max length where sum hits k.

For n = 10^5, O(n²) is too slow. Need O(n).

----------------------------------------

## Step 3: Prefix Sum Equivalence

Define `P[i] = nums[0] + nums[1] + ... + nums[i-1]`. So P[0] = 0.

Subarray `nums[l..r]` sums to k iff `P[r+1] - P[l] = k`, i.e., `P[l] = P[r+1] - k`.

For each r, we want to know: is there any earlier prefix sum equal to `P[r+1] - k`? If yes, the subarray from l to r sums to k.

To maximize length, we want the **earliest** l that satisfies the equation. Store the **first occurrence** of each prefix sum in a hashmap.

```
first = {0: -1}   # empty prefix sum = 0 "at index -1"
prefix = 0
best = 0

for r in 0..n-1:
    prefix += nums[r]
    need = prefix - k
    if need in first:
        best = max(best, r - first[need])
    if prefix not in first:
        first[prefix] = r
return best
```

The sentinel `first[0] = -1` handles subarrays starting from index 0.

"If prefix not in first" — important for maximization. Store **first occurrence only**; later occurrences don't help (they give shorter subarrays).

----------------------------------------

## Step 4: Trace on the First Example

`nums = [1, -1, 5, -2, 3]`, k = 3.

```
first = {0: -1}. prefix = 0. best = 0.

r=0, nums=1. prefix = 1. need = 1 - 3 = -2. Not in first.
  prefix=1 not in first. first[1] = 0.

r=1, nums=-1. prefix = 0. need = -3. Not in first.
  prefix=0 in first (at -1). Don't overwrite.

r=2, nums=5. prefix = 5. need = 2. Not in first.
  first[5] = 2.

r=3, nums=-2. prefix = 3. need = 0. In first at -1. best = max(0, 3 - (-1)) = 4.
  first[3] = 3.

r=4, nums=3. prefix = 6. need = 3. In first at 3. best = max(4, 4 - 3) = 4.
  first[6] = 4.
```

Return 4. ✓

Notice how the sentinel `first[0] = -1` enabled the match at r=3: the subarray starts from index 0 and sums to 3.

----------------------------------------

## Step 5: Second Example Trace

`nums = [-2, -1, 2, 1]`, k = 1.

```
first = {0: -1}. prefix = 0.

r=0, nums=-2. prefix = -2. need = -3. Not in first.
  first[-2] = 0.

r=1, nums=-1. prefix = -3. need = -4. Not in first.
  first[-3] = 1.

r=2, nums=2. prefix = -1. need = -2. In first at 0. best = 2 - 0 = 2.
  first[-1] = 2.

r=3, nums=1. prefix = 0. need = -1. In first at 2. best = max(2, 3 - 2) = 2.
  prefix=0 in first. Don't overwrite.
```

Return 2. ✓

----------------------------------------

## Step 6: Why First-Occurrence Storage

If prefix sum `p` appears at indices `a` and `b` with a < b, using a as the match gives the longer subarray. Storing b would shortchange us.

The `if prefix not in first` check ensures we keep the first.

----------------------------------------

## Step 7: Name It

**Prefix sum + hashmap with first-occurrence storage.** Same pattern as Subarray Sum Equals K (which counts), but we track maximum length instead.

Related:
- Subarray Sum Equals K (count).
- Largest Subarray With 0 Sum (same technique, k = 0).
- Longest Subarray with Equal 0s and 1s (convert 0 → -1, find k=0 subarray).

For maximum length, always store first occurrence. For counting, increment per occurrence.

----------------------------------------

## Step 8: Complexity

Time: **O(n)** — single pass, O(1) hashmap ops.
Space: O(n) for the hashmap.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int maxSubArrayLen(vector<int>& nums, int k) {
    unordered_map<long long, int> first;
    first[0] = -1;
    long long prefix = 0;
    int best = 0;

    for (int r = 0; r < (int)nums.size(); ++r) {
        prefix += nums[r];
        long long need = prefix - k;
        auto it = first.find(need);
        if (it != first.end()) {
            best = max(best, r - it->second);
        }
        if (first.find(prefix) == first.end()) {
            first[prefix] = r;
        }
    }
    return best;
}
```

`long long` for prefix and need to avoid overflow for sums outside `int` range.

----------------------------------------

## Step 10: Follow-up Questions

- **Count subarrays with sum k.** Switch to counting occurrences; use SubarraySumEqualsK template.
- **Smallest (shortest) subarray with sum k.** Same algorithm, but store **last** occurrence instead.
- **All subarrays with sum k (as ranges).** Iterate, record all matches.
- **Sum at most / exactly / at least k.** "Exactly" = this problem. "At most" and "at least" require different techniques (sorted prefix + binary search).
- **Handle multidimensional arrays.** Reduce 2D to 1D via row-range compression, then apply this.
- **Streaming array.** Algorithm is already one-pass; works as data arrives.
