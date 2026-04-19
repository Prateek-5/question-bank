# Subarray Sums Divisible by K

**Problem Link:**
https://leetcode.com/problems/subarray-sums-divisible-by-k/

**Topic:**
Math

----------------------------------------

## Step 1: Read the Problem

Given an array `nums` (can contain negatives) and integer `k`, return the **count of non-empty contiguous subarrays** whose sum is divisible by k.

Example: `nums = [4, 5, 0, -2, -3, 1]`, k = 5.

Subarrays with sums divisible by 5:
- [4, 5, 0, -2, -3, 1] sum = 5. ✓
- [5] sum = 5. ✓
- [5, 0] sum = 5. ✓
- [5, 0, -2, -3] sum = 0. ✓ (0 is divisible by anything)
- [0] sum = 0. ✓
- [0, -2, -3] sum = -5. ✓
- [-2, -3] sum = -5. ✓

Count: 7.

----------------------------------------

## Step 2: Modular Arithmetic Sets the Stage

Sum of subarray `nums[l..r]` divisible by k iff `(prefix[r+1] - prefix[l]) % k == 0` iff `prefix[r+1] % k == prefix[l] % k`.

So: **two prefix sums with the same remainder mod k mean the subarray between them is divisible by k**.

This turns "find subarrays divisible by k" into "count pairs of prefix sums sharing the same remainder mod k."

Similar to Subarray Sum Equals K, but using the remainder as the bucket key.

----------------------------------------

## Step 3: Algorithm

```
count = 0
remainders = {0: 1}   # sentinel for empty prefix (sum 0)
prefix = 0

for x in nums:
    prefix += x
    r = ((prefix % k) + k) % k   # non-negative mod
    count += remainders.get(r, 0)   # pair with all previous prefixes sharing remainder r
    remainders[r] = remainders.get(r, 0) + 1

return count
```

For each prefix, check how many previous prefixes had the same remainder. Each such pair represents a valid subarray.

----------------------------------------

## Step 4: The Non-Negative Modulo Fix

Be careful: in many languages, `-3 % 5` is `-3` (the result keeps the dividend's sign). We want a non-negative remainder (0 to k-1) for consistent bucket lookups.

The trick: `((prefix % k) + k) % k`. The inner `% k` may give negative; adding `k` makes it positive; the outer `% k` normalizes to [0, k).

----------------------------------------

## Step 5: Trace

`nums = [4, 5, 0, -2, -3, 1]`, k = 5.

```
remainders = {0: 1}. prefix = 0. count = 0.

x = 4. prefix = 4. r = 4. remainders[4] = 0. count += 0. remainders[4] = 1.
x = 5. prefix = 9. r = 4. remainders[4] = 1. count += 1. Total 1. remainders[4] = 2.
x = 0. prefix = 9. r = 4. count += 2. Total 3. remainders[4] = 3.
x = -2. prefix = 7. r = 2. count += 0. remainders[2] = 1.
x = -3. prefix = 4. r = 4. count += 3. Total 6. remainders[4] = 4.
x = 1. prefix = 5. r = 0. remainders[0] = 1 (the sentinel). count += 1. Total 7. remainders[0] = 2.
```

Return 7. ✓

The sentinel `remainders[0] = 1` represents the empty prefix. When we first hit a prefix sum divisible by k, it pairs with the sentinel, counting the subarray from index 0.

----------------------------------------

## Step 6: Why the Sentinel

A subarray `nums[0..r]` has sum divisible by k iff `prefix[r+1] % k == 0`. There's no explicit "earlier" prefix to pair with — we're pairing with the "empty prefix" (sum 0, implicitly at index -1).

By pre-seeding `remainders[0] = 1`, the algorithm correctly counts these "starts from index 0" subarrays.

----------------------------------------

## Step 7: Name It

**Prefix-sum modulo + hashmap counting.** Same pattern as Subarray Sum Equals K and Largest Subarray With 0 Sum, but with modular arithmetic.

The big idea: **congruent prefix sums define divisible subarrays**.

Related:
- Count Subarrays with Sum = k (non-divisibility version).
- Continuous Subarray Sum (check if any such subarray exists with extra length constraint).
- Subarray Product Less Than K (different technique — sliding window).

----------------------------------------

## Step 8: Complexity

Time: **O(n)** — single pass, O(1) hashmap ops (or O(1) with array of size k).
Space: **O(k)** for the remainder table.

If k is small (say ≤ 10^4), use a plain array `int count[k]` for better cache performance.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int subarraysDivByK(vector<int>& nums, int k) {
    vector<int> remainders(k, 0);
    remainders[0] = 1;   // sentinel for empty prefix
    int prefix = 0;
    int count = 0;

    for (int x : nums) {
        prefix += x;
        int r = ((prefix % k) + k) % k;
        count += remainders[r];
        remainders[r]++;
    }

    return count;
}
```

Clean. Array indexed by remainder is both fast and simple.

The non-negative mod `((prefix % k) + k) % k` is essential for correctness with negative sums.

----------------------------------------

## Step 10: Follow-up Questions

- **Count subarrays with sum = k (not divisibility).** Different key: use prefix sum directly, not mod.
- **Find (not just count) the actual subarrays.** Track indices of prefix sums per remainder; output pairs.
- **Minimum-length subarray divisible by k.** Track earliest index per remainder.
- **Largest subarray divisible by k.** Track first-seen-index per remainder; compute `i - first_occurrence`.
- **Product divisible by k.** Different approach — prime factorization.
- **Two arrays, count subarrays (l, r) with combined sum div by k.** More complex; double prefix-sum.
