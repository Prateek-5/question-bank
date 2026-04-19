# Subarray Sum Equals K

**Problem Link:**
https://leetcode.com/problems/subarray-sum-equals-k/

**Topic:**
Hashing / Sliding Window

----------------------------------------

## Step 1: Understand the Problem

Given an integer array `nums` (may contain negatives) and an integer `k`, count the number of **contiguous** subarrays whose sum equals `k`.

Example: `nums = [1, 1, 1]`, `k = 2`. Subarrays with sum 2: `[1, 1]` (indices 0-1) and `[1, 1]` (indices 1-2). Count = 2.

Notice "contiguous" again. And the presence of negatives is important — it rules out some common tricks, as we'll see.

----------------------------------------

## Step 2: The Brute Force and Why It's Slow

For each pair `(i, j)` with `i ≤ j`, compute the sum of `nums[i..j]` and check if it equals `k`. There are O(n²) pairs. We can compute the sum in O(1) if we extend `j` one at a time from `i`:

```cpp
int count = 0;
for (int i = 0; i < n; ++i) {
    int s = 0;
    for (int j = i; j < n; ++j) {
        s += nums[j];
        if (s == k) count++;
    }
}
```

O(n²). For `n = 10^4` fine, for `n = 10^5` maybe borderline, for bigger — no good.

You might wonder: "What about sliding window?" Sliding window works when we can *grow* the window to increase the sum and *shrink* it to decrease. But here **the array has negatives**. Adding an element might *decrease* the sum. So growing doesn't monotonically increase, and the usual sliding-window invariant breaks. We need a different idea.

----------------------------------------

## Step 3: Rewriting the Problem With Prefix Sums

Let's define `P[0] = 0` and `P[i+1] = P[i] + nums[i]`. So `P[i]` is the sum of the first `i` elements (empty prefix gives 0).

Now the sum of the subarray `nums[l..r-1]` is exactly `P[r] - P[l]`.

**Rephrased:** we want to count pairs `(l, r)` with `l < r` and `P[r] - P[l] = k`, which is:

> `P[l] = P[r] - k`

So for each `r` (right endpoint), how many earlier prefix sums `P[l]` equal `P[r] - k`?

This flips the problem from "subarray-sum equals k" into "how many previous prefix sums equal this specific value?" And counting occurrences of specific values is what a **hashmap** is built for.

----------------------------------------

## Step 4: Building the Algorithm

Walk through the array, maintaining:

- `sum` = running prefix sum (equivalent to `P[r]` at this moment).
- `cnt` = a hashmap `prefix_value → how many times we've seen it before`.

At each index `r`:

1. Update `sum += nums[r]`.
2. Ask: how many earlier prefix sums equal `sum - k`? Look it up in `cnt`. That's the number of valid subarrays *ending at `r`*.
3. Record `sum` itself: increment `cnt[sum]`.

The order matters — we look up *before* inserting, because we don't want the current prefix to count itself.

One subtle piece: the hashmap must start with `cnt[0] = 1`. Why? Because an "empty prefix" has sum 0. If the current running sum itself equals `k`, the valid subarray is `nums[0..r]` — which corresponds to `P[l] = P[0] = 0`. Without `cnt[0] = 1` pre-seeded, we'd miss all subarrays starting from index 0.

----------------------------------------

## Step 5: Trace on a Concrete Example

`nums = [3, 4, 7, 2, -3, 1, 4, 2]`, `k = 7`.

```
Start: sum = 0, cnt = {0: 1}, count = 0

r=0, nums[0]=3:
  sum = 3
  need = sum - k = 3 - 7 = -4. cnt[-4] = 0. count += 0.
  cnt[3]++. cnt = {0:1, 3:1}.

r=1, nums[1]=4:
  sum = 7
  need = 0. cnt[0] = 1. count += 1.   ← [3,4] has sum 7.
  cnt[7]++. cnt = {0:1, 3:1, 7:1}.

r=2, nums[2]=7:
  sum = 14
  need = 7. cnt[7] = 1. count += 1.   ← [7] itself has sum 7.
  cnt[14]++. cnt = {0:1, 3:1, 7:1, 14:1}.

r=3, nums[3]=2:
  sum = 16
  need = 9. cnt[9] = 0. count += 0.
  cnt[16]++.

r=4, nums[4]=-3:
  sum = 13
  need = 6. cnt[6] = 0. count += 0.
  cnt[13]++.

r=5, nums[5]=1:
  sum = 14
  need = 7. cnt[7] = 1. count += 1.   ← [7,2,-3,1] has sum 7.
  cnt[14]++. Now cnt[14] = 2.

r=6, nums[6]=4:
  sum = 18
  need = 11. cnt[11] = 0. count += 0.
  cnt[18]++.

r=7, nums[7]=2:
  sum = 20
  need = 13. cnt[13] = 1. count += 1.   ← [2,-3,1,4,2]... wait let me check.
                                         The prefix sum was 13 at r=4. From index 5 to 7 inclusive:
                                         nums[5]+nums[6]+nums[7] = 1+4+2 = 7. ✓
```

Final count = **4**.

Notice how `cnt[14]` reached 2. That matters when we arrive at the same prefix sum twice — each previous occurrence represents a distinct starting point, so we count them all.

Notice also: the hashmap pattern is robust against negatives. We're not asking whether the sum increases monotonically — we're asking whether a specific number has been seen before.

----------------------------------------

## Step 6: Why This Works — The Formal Argument

Every subarray `nums[l..r-1]` with sum `k` corresponds to a pair of prefix sums `P[l], P[r]` with `P[r] - P[l] = k`. For each `r` we want to count valid `l` with `l < r`.

At the moment we process index `r` in the loop:
- `sum` is exactly `P[r+1]` (if we're 0-indexed and `r` is the current index just added to the sum).
- `cnt` holds the counts of all prefix sums `P[0], P[1], ..., P[r]` — that is, all prefix sums *before* the current one.

So `cnt[sum - k]` is exactly the number of earlier prefix sums that match the condition. Correct by construction.

----------------------------------------

## Step 7: Complexity

Time: single pass, with O(1) average hashmap operations → **O(n)**.

Space: in the worst case, every prefix sum is distinct, so the hashmap can hold up to n+1 entries → **O(n)**.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int subarraySum(vector<int>& nums, int k) {
    unordered_map<int, int> cnt;
    cnt[0] = 1;                      // empty prefix
    int sum = 0, count = 0;
    for (int x : nums) {
        sum += x;
        auto it = cnt.find(sum - k);
        if (it != cnt.end()) count += it->second;
        cnt[sum]++;
    }
    return count;
}
```

Reading the code: we update `sum`, we look up how many previous prefix sums equal `sum - k`, we bump the counter of the current prefix sum. That's the whole thing.

----------------------------------------

## Step 9: Follow-up Questions

- **All subarrays whose sum is divisible by k.** Same technique, but group prefix sums by their remainder mod `k`. `cnt[r]` = number of prefix sums with remainder `r`.
- **Longest subarray with sum equal to k.** Instead of counting, we want the max length. Store in the hashmap the *first occurrence* of each prefix sum; on a hit, the length is `r - first_occurrence`. Only insert if the prefix sum isn't already there.
- **Longest subarray with sum at most k.** If the array has non-negative elements, sliding window in O(n). With negatives, it's harder — sorted set of prefix sums + binary search.
- **Count subarrays with average equal to m.** Subtract `m` from each element, then ask for subarrays with sum zero.
- **What if the array is very large and streams in?** You can't use this technique directly since you may run out of memory; approximate sketches (count-min) help in special cases.
