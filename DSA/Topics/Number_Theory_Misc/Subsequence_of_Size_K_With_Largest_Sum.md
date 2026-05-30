# Subsequence of Size K With Largest Sum

**Problem Link:**
<a href="https://leetcode.com/problems/subsequence-of-size-k-with-the-largest-sum/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/subsequence-of-size-k-with-the-largest-sum/</a>

**Topic:**
Number Theory / Misc (really sorting / selection)

----------------------------------------

## Step 1: The Task

Given array `nums` and integer k, return a subsequence of length k whose **sum is maximum**.

"Subsequence" here means "subset" — we pick k elements without requiring contiguity. Importantly, the problem asks us to preserve the **original order** of the picked elements in the returned array.

Example: `nums = [2, 1, 3, 3]`, k = 2.
Biggest two values: 3 and 3 (indices 2 and 3). In original order: [3, 3]. Return.

Example: `nums = [-1, -2, 3, 4]`, k = 3.
Biggest three values: 4, 3, -1. In original order: [-1, 3, 4].

----------------------------------------

## Step 2: Which K Elements to Pick?

To maximize sum, we pick the **k largest elements**. That's clear.

The twist: the output preserves the elements' **original order in nums**, not descending-by-value order. So we need to know which indices were picked, then emit them in original order.

----------------------------------------

## Step 3: Approach — Find K Largest, Then Re-Order

Simplest approach:
1. Copy nums with indices attached: `[(nums[0], 0), (nums[1], 1), ...]`.
2. Sort by value descending.
3. Take first k — these are the k largest, each with their original index.
4. Re-sort these k by index ascending.
5. Emit values in this order.

```
indexed = [(nums[i], i) for i in 0..n-1]
indexed.sort(key = -value)                   # descending by value
picked = indexed[:k]
picked.sort(key = index)                      # ascending by index
return [value for (value, index) in picked]
```

O(n log n) time, O(n) space.

----------------------------------------

## Step 4: Faster with Quickselect / Heap

**Quickselect** to find the k-th largest in O(n) average. Then scan nums, emit elements ≥ threshold in original order. Requires care with duplicates at the threshold (might pick too few or too many).

**Min-heap** of size k as we scan nums: keep the k largest so far. After scanning, iterate nums and emit those present in the heap (watch duplicates).

The sort approach is cleanest. For n up to 1000 or so (typical constraints), O(n log n) is fine.

----------------------------------------

## Step 5: Handle Duplicates at the Threshold

Consider `nums = [1, 1, 2, 1]`, k = 2. Two largest: 2, 1 (some 1). Which 1?

Any choice is valid as long as the sum is maximal (2 + 1 = 3). The problem typically accepts any valid answer.

If we use the "sort by value, take top k, resort by index" approach:
- Sort descending: [(2, 2), (1, 0), (1, 1), (1, 3)].
- Top 2: [(2, 2), (1, 0)].
- Sort by index: [(1, 0), (2, 2)].
- Return [1, 2].

Fine.

----------------------------------------

## Step 6: Trace

`nums = [2, 1, 3, 3]`, k = 2.

- Indexed: [(2, 0), (1, 1), (3, 2), (3, 3)].
- Sort desc by value: [(3, 2), (3, 3), (2, 0), (1, 1)].
- Top 2: [(3, 2), (3, 3)].
- Sort by index: [(3, 2), (3, 3)].
- Output: [3, 3]. ✓

`nums = [-1, -2, 3, 4]`, k = 3.

- Indexed: [(-1, 0), (-2, 1), (3, 2), (4, 3)].
- Sort desc: [(4, 3), (3, 2), (-1, 0), (-2, 1)].
- Top 3: [(4, 3), (3, 2), (-1, 0)].
- Sort by index: [(-1, 0), (3, 2), (4, 3)].
- Output: [-1, 3, 4]. ✓

----------------------------------------

## Step 7: Why Not Just Sort Descending and Take k?

If the problem accepted any order, we'd just return nums sorted descending, truncated to k. But the problem says "subsequence" — order matters.

A "subsequence" in the strict sense preserves the original positional order of the chosen elements. So we need to re-sort by index after selection.

----------------------------------------

## Step 8: Name It

**Top-K selection with order preservation** — a combination of top-k (select) and reordering.

Related problems:
- Kth Largest Element.
- Top K Frequent Elements.
- Top K Closest Points to Origin.
- K Smallest Pairs.

The pattern "select k best, then emit in original order" appears in streaming / online scenarios.

----------------------------------------

## Step 9: Complexity

Time: **O(n log n)** (dominated by the first sort).
Space: **O(n)** for the indexed array.

For constraints up to ~1000, this is instantaneous.

----------------------------------------

## Step 10: C++ Implementation

```cpp
vector<int> maxSubsequence(vector<int>& nums, int k) {
    int n = nums.size();
    vector<pair<int, int>> indexed;
    indexed.reserve(n);
    for (int i = 0; i < n; ++i) indexed.push_back({nums[i], i});

    // Sort descending by value, break ties arbitrarily
    sort(indexed.begin(), indexed.end(), greater<pair<int, int>>());

    // Take top k
    indexed.resize(k);

    // Re-sort by original index
    sort(indexed.begin(), indexed.end(), [](auto& a, auto& b) { return a.second < b.second; });

    vector<int> result;
    result.reserve(k);
    for (auto& [val, idx] : indexed) result.push_back(val);
    return result;
}
```

Two sorts: one on value (to select top-k), one on index (to restore original order).

----------------------------------------

## Step 11: Follow-up Questions

- **Smallest k sum instead.** Same idea, sort ascending.
- **Subsequence with sum exactly = S.** Subset sum; NP-hard for general S.
- **Contiguous subarray of length k with max sum.** Sliding window — different problem.
- **Return the indices instead of values.** Skip the final extraction step.
- **Streaming input.** Use a min-heap of size k to maintain the top-k, but preserving order is harder.
- **Why sort by index at the end?** Because "subsequence" preserves original order; if we skipped this, the output would be in descending-value order, which is not a subsequence.
