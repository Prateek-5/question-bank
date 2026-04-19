# Maximum Product of Three Numbers

**Problem Link:**
https://leetcode.com/problems/maximum-product-of-three-numbers/

**Topic:**
Greedy

----------------------------------------

## Step 1: Understand the Twist

Given an integer array `nums`, find the **maximum product** of any three numbers.

Simple intuition: pick the three largest numbers. Their product is the max.

Example: `nums = [1, 2, 3, 4]`. Top 3: 2, 3, 4. Product = 24. ✓

But there's a subtle case: **negative numbers**. Two negatives multiplied give a positive.

Example: `nums = [-10, -10, 5, 2]`. Top 3 by value: -10, 2, 5. Product = -100. Bad.

But: (-10) × (-10) × 5 = 500. Much better.

So two very negative numbers can combine with one very positive to beat the "top 3 largest" strategy.

----------------------------------------

## Step 2: The Two Candidates

Actually, only two configurations can give the maximum product of three:

1. **Three largest**: if no negatives (or all positives dominate), this wins.
2. **Two smallest (most negative) × largest**: if there are two large-magnitude negatives, their positive product times the largest gives a candidate.

The answer is `max(top3_product, smallest_two_times_largest)`.

Why no other configurations? 
- One negative × two positives = negative. Worse than any purely positive product.
- Three negatives = negative (product of three negatives is negative). Worse.
- Zero in the mix = product 0. Worse unless forced.

So the two candidates cover all cases.

----------------------------------------

## Step 3: Algorithm

Sort the array. Then:
- max1 = `nums[n-1] * nums[n-2] * nums[n-3]` (top three).
- max2 = `nums[0] * nums[1] * nums[n-1]` (two smallest × largest).

Return `max(max1, max2)`.

O(n log n) due to sort. Space O(1).

----------------------------------------

## Step 4: Without Sorting — O(n)

We don't need a full sort. Just track:
- Top 3 largest (max1, max2, max3).
- Bottom 2 smallest (min1, min2).

One pass over nums updating these 5 running bests.

Then answer is `max(max1 * max2 * max3, min1 * min2 * max1)`.

O(n) time, O(1) space.

----------------------------------------

## Step 5: Trace on `[-10, -10, 5, 2]`

Sorted: `[-10, -10, 2, 5]`.

- Top 3 product: -10 * 2 * 5 = -100.
- Two smallest × largest: -10 * -10 * 5 = 500.

Max: **500**. ✓

For `[1, 2, 3, 4]`:
- Top 3: 4 * 3 * 2 = 24.
- Two smallest × largest: 1 * 2 * 4 = 8.

Max: **24**. ✓

For `[-5, -4, -3, -2, -1]` (all negative):
- Top 3 (least negative): -1 * -2 * -3 = -6.
- Two smallest × largest: -5 * -4 * -1 = -20.

Max: **-6**. ✓ (Makes sense: among negative products, the "least negative" is the max.)

For `[-4, -3, -2, -1, 60]`:
- Top 3: 60 * -1 * -2 = 120.
- Two smallest × largest: -4 * -3 * 60 = 720.

Max: **720**. ✓

----------------------------------------

## Step 6: Why the Two Candidates Cover All Cases

Let a ≤ b ≤ c ≤ d ≤ e ≤ ... ≤ z be the sorted array.

The maximum product of three elements must come from:
- Three largest: (x, y, z) at the top.
- Two smallest × one largest: (a, b, z).

Any mix like (a, c, z) or (a, z, y)? Let's check:
- (a, y, z): if a is negative, a·y·z could beat (x,y,z) if a's magnitude is much larger than x. But then (a, b, z) (both a and b negative, b has large magnitude too) would be even better. So (a, y, z) is dominated by (a, b, z) when a < 0. Not needed separately.

- (a, b, y): if a, b negative, ab > 0, so (a, b, z) > (a, b, y) since z ≥ y.

So only (x, y, z) and (a, b, z) need checking. Done.

----------------------------------------

## Step 7: Name It

**Greedy with case analysis.** The "sort + take edges" pattern is common. Examples:
- Maximum product of k numbers (generalized).
- Minimum product subarray (handle signs carefully).
- Maximum sum with constraints.

The principle: for product/max-value problems, the extremes (highest positives and lowest negatives) matter, middle values rarely do.

----------------------------------------

## Step 8: Complexity

Sort approach: **O(n log n)**.
Running-top-bottom approach: **O(n)**.
Space: **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

**Sort version (simpler):**

```cpp
int maximumProduct(vector<int>& nums) {
    sort(nums.begin(), nums.end());
    int n = nums.size();
    return max(nums[n-1] * nums[n-2] * nums[n-3], 
               nums[0] * nums[1] * nums[n-1]);
}
```

**O(n) running-top-bottom version:**

```cpp
int maximumProduct(vector<int>& nums) {
    int max1 = INT_MIN, max2 = INT_MIN, max3 = INT_MIN;   // top 3 largest
    int min1 = INT_MAX, min2 = INT_MAX;                   // 2 smallest

    for (int x : nums) {
        // Update top 3
        if (x > max1) { max3 = max2; max2 = max1; max1 = x; }
        else if (x > max2) { max3 = max2; max2 = x; }
        else if (x > max3) { max3 = x; }

        // Update bottom 2
        if (x < min1) { min2 = min1; min1 = x; }
        else if (x < min2) { min2 = x; }
    }

    return max(max1 * max2 * max3, min1 * min2 * max1);
}
```

The O(n) version is longer but avoids the sort. Use whichever fits your interview style.

----------------------------------------

## Step 10: Follow-up Questions

- **Maximum product of k numbers.** Generalize: for each even k', consider combinations of pairs of negatives with positives. Becomes a DP problem.
- **Minimum product of three.** Symmetric: the two candidates are "three smallest" and "largest two × smallest."
- **Product of any subset.** NP-hard (subset-sum-ish).
- **Handle very large products (overflow).** Use long long.
- **Streaming array.** Maintain top-3 and bottom-2 incrementally.
- **Max sum instead of product.** Just top 3.
