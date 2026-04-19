# Minimize Maximum Pair Sum in Array

**Problem Link:**
https://leetcode.com/problems/minimize-maximum-pair-sum-in-array/description/

**Topic:**
Two Pointers

----------------------------------------

## Step 1: The Task

Given an array `nums` of **even length** n, you must **pair** the elements into n/2 pairs. Each element belongs to exactly one pair.

For each pair, compute the pair's **sum**. The "maximum pair sum" is the largest such sum.

Goal: **choose the pairing** that **minimizes the maximum pair sum**. Return that minimum.

Example: `nums = [3, 5, 2, 3]`.
Pairings:
- (3, 5), (2, 3): sums 8, 5. Max = 8.
- (3, 2), (5, 3): sums 5, 8. Max = 8.
- (3, 3), (5, 2): sums 6, 7. Max = **7**.

Minimum achievable max = **7**.

----------------------------------------

## Step 2: First Intuition — Try Random Pairings?

With n elements, the number of pairings is astronomical (n! / (2^(n/2) · (n/2)!)). We need a principle to pick the optimal.

Let's observe: the **largest** element in nums will be in some pair. Whoever it's paired with is added to the largest sum. To minimize this worst-case sum, pair the largest with the **smallest** — that drags its sum down as much as possible.

Now consider the second-largest. It's in another pair; to minimize its sum, pair with the second-smallest.

So the pattern: **sort nums, then pair smallest with largest, second-smallest with second-largest, etc.**

----------------------------------------

## Step 3: Prove the Greedy

Claim: sorting ascending and pairing (first, last), (second, second-to-last), etc., minimizes the maximum pair sum.

Proof sketch (exchange argument): suppose an optimal pairing has (a, b) and (c, d) where a < c ≤ d < b (so a is the smallest, b is the largest, and c, d are inner). Swap to (a, b') where b' is b's original partner... actually, the cleaner argument:

Consider any pairing. If the largest element x is NOT paired with the smallest, say x is paired with y and the smallest z is paired with w. Then:
- pair sums: x + y and z + w.
- max of these two: max(x + y, z + w).

After swap: (x, z) and (y, w). Sums: x + z and y + w.
- Since z is the smallest, x + z ≤ x + y.
- And y + w ≤ x + y (since y ≤ x, w ≤ y). Also y + w vs z + w: y + w ≥ z + w (since y ≥ z). Hmm.
- max(x+z, y+w) ≤ max(x+y, z+w)?

Let's think: max(x+y, z+w) ≥ x+y (since x+y is one of the terms). After swap, max(x+z, y+w). x+z ≤ x+y (since z ≤ y). y+w: if y+w ≤ x+y, then max ≤ x+y. y+w ≤ x+y iff w ≤ x, which is true (since x is the largest). So the swap doesn't increase the max. Apply iteratively: the sort-and-pair-extremes strategy is optimal.

----------------------------------------

## Step 4: Algorithm

```
sort nums ascending
best = 0
for i in 0..n/2 - 1:
    pair_sum = nums[i] + nums[n-1-i]
    best = max(best, pair_sum)
return best
```

Two pointers: i from the left, n-1-i from the right, walking inward.

O(n log n) time (dominated by sort). O(1) extra (in-place sort).

----------------------------------------

## Step 5: Trace on `[3, 5, 2, 3]`

Sort: [2, 3, 3, 5].
Pairs:
- (2, 5): sum = 7.
- (3, 3): sum = 6.

Max = **7**. ✓

Trace on `[3, 5, 4, 2, 4, 6]`:
Sort: [2, 3, 4, 4, 5, 6].
Pairs:
- (2, 6) = 8.
- (3, 5) = 8.
- (4, 4) = 8.

Max = 8.

Verify by trying another pairing: (2, 5), (3, 6), (4, 4) → sums 7, 9, 8. Max = 9. Worse. ✓

Another: (2, 3), (4, 4), (5, 6) → sums 5, 8, 11. Max = 11. Worse. ✓

----------------------------------------

## Step 6: Why This Pattern?

Intuitively: large + large = very large. To avoid that, never pair two large numbers together. By always pairing a large with a small, we "dilute" each extreme.

This trick appears often:
- Minimize max load when distributing items.
- Balance two groups.
- Pair high with low to flatten peaks.

----------------------------------------

## Step 7: Name It

**Sort-and-pair-extremes / two-pointer shaving**. Also called "match largest with smallest" — a greedy technique.

Applications:
- Minimize maximum pair sum (this problem).
- Fair team assignments (split n people into 2 teams with balanced strengths).
- Divide chocolate optimally.

Related: the opposite goal ("maximize minimum pair sum") uses similar sorting but different pairing (e.g., pair adjacent in sorted order).

----------------------------------------

## Step 8: Complexity

Time: **O(n log n)** — sorting dominates.
Space: **O(1)** if sorted in place.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int minPairSum(vector<int>& nums) {
    sort(nums.begin(), nums.end());
    int n = nums.size();
    int best = 0;
    for (int i = 0; i < n / 2; ++i) {
        best = max(best, nums[i] + nums[n - 1 - i]);
    }
    return best;
}
```

Single sort + pair-wise scan. Minimal code, clean.

----------------------------------------

## Step 10: Follow-up Questions

- **Minimize max pair product instead of sum.** Same technique (pair small with large) to avoid large × large.
- **Maximize min pair sum.** Sort and pair adjacent: (nums[0], nums[1]), (nums[2], nums[3]), ... to keep each pair's sum as large as possible collectively.
- **Pairs of size k (k-sized groups).** Sorting still helps, but pairing logic becomes "interleave extremes within each group."
- **Odd-length array.** Problem specifies even; extension would need one triplet or one leftover.
- **Weighted: minimize sum of (max_pair_sum · weight_per_pair).** Different objective; probably needs DP.
- **Why not pair (smallest, second-smallest), etc.?** Then the largest would pair with another large number — its pair sum would be 2 × large, likely much worse.
