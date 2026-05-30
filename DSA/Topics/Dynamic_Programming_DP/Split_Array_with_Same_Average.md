# Split Array with Same Average

**Problem Link:**
<a href="https://leetcode.com/problems/split-array-with-same-average/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/split-array-with-same-average/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Parse the Question

Given an integer array `nums`, determine if it's possible to split it into **two non-empty** subsets `A` and `B` such that **avg(A) == avg(B)**.

Example: `nums = [1, 2, 3, 4, 5, 6, 7, 8]`. Average of all = 36 / 8 = 4.5.

Can we split into two groups each averaging 4.5?
- {1, 4, 5, 8} averages (1+4+5+8)/4 = 18/4 = 4.5. ✓
- {2, 3, 6, 7} averages (2+3+6+7)/4 = 18/4 = 4.5. ✓

Return true. Another example: `nums = [3, 1]`. Can we split? {3} avg 3, {1} avg 1. Not equal. Return false.

----------------------------------------

## Step 2: Math First

If A and B both equal the total average, then A's sum and B's sum also equal their respective averages times their sizes. Let's call this "total avg" T.

- Total avg T = sum(nums) / n.
- For A with size k: avg(A) = T means sum(A) = k · T = k · sum(nums) / n.

For sum(A) to be an integer, we need `k · sum(nums) / n` to be an integer — `k · sum(nums)` divisible by n.

This means: for each candidate size k (1 ≤ k < n), check if `k · total_sum % n == 0`. If so, compute the required subset sum `target = k · total_sum / n` and check if a **size-k subset summing to target** exists in nums.

We've reduced "split with equal averages" to "find a size-k subset summing to target, for some k."

----------------------------------------

## Step 3: Brute Force — Enumerate Subsets

For each size k and each target, enumerate subsets of size k. O(C(n, k)) per size, exponential in n. For n = 30, already 10^8 worst case.

We can use subset-sum DP with size tracking:

`dp[k][s]` = true if some subset of size k sums to s.

Process numbers one by one. For each number x:
- For k from high to low (to avoid reuse in same pass):
  - For s:
    - If dp[k-1][s-x] was true: set dp[k][s] = true.

O(n · k · s) = O(n³ · max_val) — feasible for moderate n.

Alternatively, use a set-based approach: `possible_sums[k]` = set of reachable sums with exactly k elements.

----------------------------------------

## Step 4: Optimization — Meet in the Middle

For n up to 30, even O(n³) can be too much. A classic trick: split nums into two halves, enumerate subsets of each half, and combine.

Each half has ≤ 15 elements, so 2^15 = 32768 subsets per half. For each subset, record its (size, sum) pair.

For each candidate (k, target):
- For each (k1, s1) in first half, check if (k - k1, target - s1) is in the second half's set.

Total: O(2^(n/2) · n) with hashmaps.

For n = 30, that's ~32768 × 30 ≈ 10^6 — fast.

The trick is a classic **meet-in-the-middle**: split into halves to reduce exponential cost.

----------------------------------------

## Step 5: Simpler Approach That Works for n ≤ 30

For the typical constraint n ≤ 30, we can sidestep meet-in-the-middle by using bitset DP:

`possible[k]` = a bitset where bit s is set if some size-k subset sums to s.

Process each number x:
- From k = current_max down to 1:
  - `possible[k] |= possible[k - 1] << x` (shift indicates "add x to every sum").

After processing all numbers, for each k in [1, n/2] (smaller half is sufficient by symmetry), check if `possible[k].test(k · total_sum / n)` when that's an integer.

Space: O(n · sum_max / 64) bits. For n = 30, sum ≤ 300,000, so ~300K bits per level, 30 levels → 10M bits = ~1.25 MB. Tight but feasible.

This is the practical approach for this specific problem.

----------------------------------------

## Step 6: Why We Only Check k ≤ n / 2

If a size-k subset averages T, its complement (size n-k) also averages T. So checking all k ≤ n/2 finds the same answers as checking all k.

Also, a useful early exit: if `k · total_sum % n != 0`, no valid target sum exists for this k. Skip.

----------------------------------------

## Step 7: Trace Briefly for `[1, 2, 3, 4, 5, 6, 7, 8]`

total_sum = 36, n = 8, avg = 4.5.

Check k = 1: 1 · 36 / 8 = 4.5. Not integer. Skip.
Check k = 2: 2 · 36 / 8 = 9. Target = 9, size 2. Is there a size-2 subset summing to 9? {1,8}, {2,7}, {3,6}, {4,5}. Yes! But we need to check: does avg match total avg? avg of {1, 8} = 4.5. ✓ So answer is true.

Great — we could stop at k = 2.

(The problem asks for any valid split. Finding one is enough.)

----------------------------------------

## Step 8: Name It

**Subset-sum DP with size constraint**, or a **meet-in-the-middle** approach for larger n. The overarching theme: reduce a seemingly-complex partition problem to a canonical "is there a subset with this sum and that size" check.

Variants:
- Partition Equal Subset Sum (just one size unconstrained).
- Target Sum (counts subsets with given ±-sum).
- K-th Largest Sum of Subsets.

----------------------------------------

## Step 9: Complexity

Subset-sum DP: **O(n² · sum)** time, O(n · sum) space.
Meet-in-the-middle: **O(n · 2^(n/2))** time.

----------------------------------------

## Step 10: C++ Implementation

Bitset DP version (works for n ≤ 30, values ≤ 10000):

```cpp
bool splitArraySameAverage(vector<int>& nums) {
    int n = nums.size();
    int total = accumulate(nums.begin(), nums.end(), 0);
    if (n < 2) return false;

    // possible[k][s] = true if a size-k subset sums to s.
    // Use bitset for each k.
    vector<bitset<30001>> possible(n / 2 + 1);
    possible[0][0] = 1;

    for (int x : nums) {
        // iterate k from high to low to avoid reusing the same number
        for (int k = min((int)possible.size() - 1, n / 2); k >= 1; --k) {
            possible[k] |= possible[k - 1] << x;
        }
    }

    for (int k = 1; k <= n / 2; ++k) {
        if ((k * total) % n != 0) continue;
        int target = k * total / n;
        if (possible[k][target]) return true;
    }
    return false;
}
```

This is a cleaner formulation. It uses bitset operations for speed.

For a more straightforward but less efficient implementation, use an unordered_set per size.

----------------------------------------

## Step 11: Follow-up Questions

- **Find the actual partition.** Track parent pointers in the DP.
- **Split into k subsets with equal average.** Much harder — generalizes to NP-hard in full generality.
- **Average constraint with tolerance.** Approximate variants; computationally easier for specific tolerances.
- **Preprocess to reduce equivalent elements.** Subtract the mean from everything; the problem becomes "find a subset with sum zero." Cleaner but same complexity.
- **For larger n (say 40).** Meet-in-the-middle is the standard approach.
