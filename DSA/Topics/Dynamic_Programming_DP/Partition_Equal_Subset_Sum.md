# Partition Equal Subset Sum

**Problem Link:**
https://leetcode.com/problems/partition-equal-subset-sum/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: What Does Partition Actually Mean?

Given an array of positive integers, decide whether it can be split into two groups **with equal sums**. Return true or false.

Example: `[1, 5, 11, 5]`. Sum is 22. Can we get two groups each summing to 11? Yes — `{11}` alone vs. `{1, 5, 5}`. Return **true**.

`[1, 2, 3, 5]`. Sum is 11. Half would be 5.5 — not even an integer. So splitting into two equal-sum groups is impossible. Return **false**.

Important: "two groups" means every element goes in exactly one group. Nothing can be left out.

----------------------------------------

## Step 2: A Free Early Exit

If the total sum is odd, we can stop immediately — there's no way to split an odd integer into two equal halves. So assume from now on that `total = 2T` for some integer T.

Now the question reduces to: **is there any subset summing to exactly T?**

If yes, that subset is one group, and its complement (the rest of the array) is the other. They each sum to T. Partition possible.

If no subset sums to T, no partition is possible.

So the new problem is: **subset-sum-equals-T**. Let me focus on that.

----------------------------------------

## Step 3: Try the Subset-Sum Question by Hand

`nums = [1, 5, 11, 5]`, T = 11. Can I pick some subset summing to 11?

Let me enumerate subsets and their sums:
- `{}` → 0
- `{1}` → 1
- `{5}` → 5
- `{11}` → 11 ✓ (found it!)
- ... more subsets exist but we already have one.

Yes, so partition is possible. ✓

`nums = [1, 5, 5, 3]`, total = 14, T = 7. Subsets summing to 7?
- `{1}` → 1, `{5}` → 5, `{3}` → 3, `{5,3}` → 8, `{1,3,5}` → 9, `{1,5}` → 6, `{5,5}` → 10, ...
- No subset sums to exactly 7. So partition is not possible.

----------------------------------------

## Step 4: The Brute Force Is Exponential

For n items, there are 2^n subsets. For n = 20, that's about a million — borderline okay. For n = 200, it's 10^60 — impossible.

Why is it so wasteful? Because most of those subsets are being re-computed piecewise. If I ask "what sums can I form using the first 3 elements?" and get `{0, 1, 5, 6, 11, 12, 16, 17}`, then adding a 4th element of value `5` means each reachable sum is still reachable (skip the new item) or can be increased by 5 (take it). That's all — no need to re-enumerate all 16 subsets of size 4.

So the question becomes: can I just track the set of **reachable sums** as I process elements one at a time?

----------------------------------------

## Step 5: The Boolean Table Approach

Let `dp[i][s] = true` if some subset of the first `i` elements sums to `s`.

Transitions:
- **Skip element i:** `dp[i][s] = dp[i-1][s]`.
- **Take element i (if `nums[i-1] <= s`):** `dp[i][s] = dp[i][s] OR dp[i-1][s - nums[i-1]]`.

Base cases:
- `dp[0][0] = true` (empty subset sums to 0).
- `dp[0][s] = false` for `s > 0`.

Goal: `dp[n][T]`.

Let me build the table for `nums = [1, 5, 11, 5]`, T = 11. I'll show only the reachable sums per row (implicitly, un-shown sums are false):

```
Row 0 (no items):         {0}
Row 1 (considered 1):      {0, 1}
Row 2 (considered 5 more): {0, 1, 5, 6}
Row 3 (considered 11):     {0, 1, 5, 6, 11, 12, 16, 17}
                           ↑ 11 is reachable — we can stop early!
```

So `dp[3][11] = true`. Answer: partition is possible.

----------------------------------------

## Step 6: 1D Space Optimization

Each row depends only on the previous row. So we can use a single 1D boolean array of size `T+1`, updating it in place.

But we have to be careful about direction. If we iterate `s` from 0 upward while updating, `dp[s]` uses `dp[s - num]` — which might have *already* been updated this same iteration, letting us "use the same item twice." Not what we want.

To fix: iterate `s` **downward**, from T to `num`. That way, when we read `dp[s - num]`, it's still from the previous row.

```cpp
vector<bool> dp(T + 1, false);
dp[0] = true;
for (int x : nums) {
    for (int s = T; s >= x; --s) {
        dp[s] = dp[s] || dp[s - x];
    }
}
return dp[T];
```

Let me trace this on `nums = [1, 5, 11, 5]`, T = 11.

```
Initial dp: [T, F, F, F, F, F, F, F, F, F, F, F]   (indices 0..11)

Process 1 (s from 11 down to 1):
  dp[1] |= dp[0] → dp[1] = T.
  Others unchanged.
  dp: [T, T, F, F, F, F, F, F, F, F, F, F]

Process 5 (s from 11 down to 5):
  dp[11] |= dp[6] = F → F.
  ...
  dp[6] |= dp[1] = T → T.
  dp[5] |= dp[0] = T → T.
  dp: [T, T, F, F, F, T, T, F, F, F, F, F]

Process 11 (s from 11 down to 11):
  dp[11] |= dp[0] = T → T.
  dp: [T, T, F, F, F, T, T, F, F, F, F, T]

At this point dp[11] is true — we could stop. Process 5 (redundant but trace anyway):
  dp[11] |= dp[6] = T → still T.
  dp[10] |= dp[5] = T → T.
  dp[6] |= dp[1] = T → still T.
  dp[5] |= dp[0] = T → still T.
```

`dp[11]` is true at the end → partition possible. ✓

----------------------------------------

## Step 7: Name What We Found

This is a classic **subset-sum DP**. It's often phrased as a "0/1 knapsack" variant where each item has weight equal to value. The recurrence `dp[s] = dp[s] OR dp[s - x]` iterated over items is the bread-and-butter pattern.

The trick of iterating `s` downward is also the defining move for **0/1 knapsack** (each item used at most once) vs. upward for **unbounded knapsack** (each item unlimited). Memorizing the direction isn't the point — *understanding why it prevents double-use* is.

----------------------------------------

## Step 8: The Bitset Speed-Up (Optional but Cool)

Once you're comfortable with the boolean DP, there's a trick that speeds it up by ~64x in practice.

Represent the entire row as a bit: bit `s` is 1 iff sum `s` is reachable. Now what does "take element `x`" look like on a bitset?

Every reachable sum `s` should have `s + x` also become reachable. Shifting the bitset left by `x` positions moves every "1-bit" at position `s` to position `s + x`. That's exactly "everything reachable before is now also reachable `x` higher."

So the recurrence `dp = dp | (dp << x)` does both things at once: keep the previous row, plus add all shifted sums.

```cpp
bitset<10001> dp;      // assumes T <= 10000
dp[0] = 1;
for (int x : nums) dp |= (dp << x);
return dp[T];
```

Same algorithm, but the bitset lets the hardware OR 64 bits at a time. Blazingly fast in practice.

Note: understanding the boolean version is essential; the bitset is a micro-optimization of the same idea.

----------------------------------------

## Step 9: Complexity

Boolean DP: time **O(n·T)**, space **O(T)**.
Bitset DP: time **O(n·T / 64)** due to hardware parallelism, space **O(T/64)** bits.

For the typical LeetCode constraint (sum up to 20000), both are fast enough. The bitset just runs faster.

----------------------------------------

## Step 10: C++ Implementation

```cpp
bool canPartition(vector<int>& nums) {
    int sum = accumulate(nums.begin(), nums.end(), 0);
    if (sum & 1) return false;              // odd sum — immediate fail
    int target = sum / 2;

    vector<bool> dp(target + 1, false);
    dp[0] = true;
    for (int x : nums) {
        for (int s = target; s >= x; --s) {
            dp[s] = dp[s] || dp[s - x];
        }
    }
    return dp[target];
}
```

The two key ingredients:
- Sum check for the quick odd-reject.
- Downward iteration of `s` to ensure each element is used at most once per item.

----------------------------------------

## Step 11: Follow-up Questions

- **Minimum difference between two subsets (not necessarily equal).** Compute all reachable sums `s` up to `total/2`. The answer is `total - 2 * max(reachable s ≤ total/2)`.
- **Find the actual partition (two concrete subsets).** Track parent pointers during DP, then walk back.
- **What if numbers can be negative?** The target could also be negative. Shift the index range to accommodate.
- **Partition into K equal subsets.** NP-hard in general. Bitmask DP with memoization works for small N; branch-and-bound with smart pruning helps in practice.
- **Count the number of distinct subsets summing to target.** Integer DP instead of boolean: `dp[s] += dp[s - x]`, still iterate `s` downward.
