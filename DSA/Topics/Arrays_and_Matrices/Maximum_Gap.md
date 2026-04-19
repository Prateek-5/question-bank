# Maximum Gap

**Problem Link:**
https://leetcode.com/problems/maximum-gap/

**Topic:**
Arrays & Matrices

----------------------------------------

## Step 1: Understand the Task

Given an **unsorted** array, find the **maximum gap between successive elements in the sorted order**. Return 0 if the array has fewer than 2 elements.

Example: `nums = [3, 6, 9, 1]`.
Sort: [1, 3, 6, 9]. Successive gaps: 2, 3, 3. Max: **3**.

Constraint: must run in **O(n)** time and O(n) space.

If we could use O(n log n), just sort and scan. But the problem's twist is the linear-time requirement.

----------------------------------------

## Step 2: The Linear-Time Trick — Pigeonhole

If we have n numbers in a range [min, max], the **average** gap between consecutive sorted numbers is `(max - min) / (n - 1)`. The **max** gap must be ≥ this average (you can't have all gaps below average).

Here's the key observation: if we divide the range [min, max] into **n - 1 buckets of width (max - min) / (n - 1)**, then by pigeonhole:
- There are n numbers and n - 1 buckets.
- Some bucket must contain at least 2 numbers, but that's irrelevant.
- The **gap between two consecutive sorted numbers in the same bucket is at most the bucket width** = average gap.
- The maximum gap overall must therefore span **across** buckets.

So the max gap is always `(max of some bucket) - (min of the next non-empty bucket to the right)`. We don't need to know the internal order of numbers within buckets — just per-bucket min and max.

That's the insight. The algorithm:
1. Find global min and max.
2. Compute bucket width `= ceil((max - min) / (n - 1))`.
3. Bucket each number: `bucket_idx = (num - min) / width`. Record each bucket's min and max.
4. Scan buckets left to right. For each non-empty bucket, compute `bucket.min - previous_bucket.max`. Track the largest such cross-bucket gap.
5. Return the max.

All O(n). Neat.

----------------------------------------

## Step 3: Why Pigeonhole Forces Max Gap Across Buckets

Suppose for contradiction the max gap is **within** a bucket. A bucket has width w = (max - min) / (n - 1). Any two numbers in the same bucket differ by at most w. But w ≤ max gap. So the within-bucket gap is ≤ average gap, which is ≤ max gap.

Hmm, that's not quite a contradiction yet. Let me think again.

Actually: we have n numbers spanning [min, max], so total span = max - min. If gaps sum to max - min and there are n - 1 gaps, the max gap ≥ (max - min) / (n - 1) = bucket width w.

Within a bucket, any gap is < w (bucket width). So within-bucket gaps are all strictly less than the max gap. Therefore the max gap must lie across buckets. ✓

That's the pigeonhole argument. Subtle but correct.

----------------------------------------

## Step 4: Trace on `[3, 6, 9, 1]`

n = 4. min = 1, max = 9. Range = 8.
Bucket width w = ceil(8 / 3) = 3 (we want width such that we get ≥ n-1 = 3 buckets).

Actually let me recompute. w = (max - min) / (n - 1) = 8 / 3 ≈ 2.67. If we take w = 3, we have buckets of width 3:
- Bucket 0: [1, 4).
- Bucket 1: [4, 7).
- Bucket 2: [7, 10).

Numbers:
- 1: bucket (1 - 1) / 3 = 0.
- 3: bucket (3 - 1) / 3 = 0.
- 6: bucket (6 - 1) / 3 = 1.
- 9: bucket (9 - 1) / 3 = 2.

Per-bucket min/max:
- Bucket 0: {1, 3}. min=1, max=3.
- Bucket 1: {6}. min=6, max=6.
- Bucket 2: {9}. min=9, max=9.

Cross-bucket gaps:
- Bucket 0 max=3 → Bucket 1 min=6. Gap = 3.
- Bucket 1 max=6 → Bucket 2 min=9. Gap = 3.

Max gap: **3**. ✓

Notice we ignored within-bucket gaps (like 3 - 1 = 2 in bucket 0) — by pigeonhole they can't be the max.

----------------------------------------

## Step 5: Bucket Width Details

For n = 4, we want n - 1 = 3 buckets to span [min, max]. Bucket width should be such that max lands in the last bucket.

Naive: w = (max - min) / (n - 1), integer division. Edge cases: if max == min, w = 0 (answer is 0 — all same). Ensure w ≥ 1 otherwise.

Some prefer w = ceil((max - min) / (n - 1)) to guarantee numbers fit in exactly n - 1 buckets. Using `max(1, (max - min) / (n - 1))` handles the degenerate cases.

Bucket count: `ceil((max - min + 1) / w)` or similar. Using `(max - min) / w + 1` works cleanly.

These off-by-one details are subtle; test your implementation carefully on edge cases.

----------------------------------------

## Step 6: Name It

**Bucket sort by quantized values** + **pigeonhole argument**. The technique:
1. Divide range into buckets of carefully-chosen width.
2. Exploit pigeonhole to avoid within-bucket work.
3. Scan cross-bucket gaps.

This is a specialized algorithm — not widely reusable — but the pattern of "use pigeonhole to prove a structural bound, then exploit it" is valuable.

Alternative: **radix sort** also gives O(n) for integer arrays, but its constants are higher. For an interview, bucket-based is more elegant.

----------------------------------------

## Step 7: Complexity

Time: **O(n)** — one pass to find min/max, one pass to bucket, one pass over buckets.
Space: **O(n)** for bucket storage.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int maximumGap(vector<int>& nums) {
    if (nums.size() < 2) return 0;

    int mn = *min_element(nums.begin(), nums.end());
    int mx = *max_element(nums.begin(), nums.end());
    if (mn == mx) return 0;

    int n = nums.size();
    int width = max(1, (mx - mn) / (n - 1));
    int numBuckets = (mx - mn) / width + 1;

    vector<int> bucketMin(numBuckets, INT_MAX);
    vector<int> bucketMax(numBuckets, INT_MIN);

    for (int x : nums) {
        int idx = (x - mn) / width;
        bucketMin[idx] = min(bucketMin[idx], x);
        bucketMax[idx] = max(bucketMax[idx], x);
    }

    int prevMax = mn;
    int maxGap = 0;
    for (int i = 0; i < numBuckets; ++i) {
        if (bucketMin[i] == INT_MAX) continue;   // empty bucket
        maxGap = max(maxGap, bucketMin[i] - prevMax);
        prevMax = bucketMax[i];
    }
    return maxGap;
}
```

Key implementation details:
- `width = max(1, (mx - mn) / (n - 1))` avoids division by zero and ensures meaningful buckets.
- Empty buckets are skipped (their `bucketMin` stays at `INT_MAX`).
- `prevMax` tracks the max of the last non-empty bucket seen, for cross-bucket gap computation.

----------------------------------------

## Step 9: Follow-up Questions

- **Array of floats instead of ints.** Same algorithm, use floating-point bucket widths.
- **Find the second largest gap.** Track top-2 instead of top-1.
- **Return the (smaller, larger) pair forming the max gap.** Track which pair produced the max during the scan.
- **Negative values in the array.** Algorithm works — mn might be negative, but `x - mn` is non-negative, so bucket indices stay valid.
- **Array where most values are duplicates.** Many buckets are empty; algorithm still O(n).
- **Why not radix sort?** Works, but has higher constants and is less conceptually clean than pigeonhole-bucket for this problem.
