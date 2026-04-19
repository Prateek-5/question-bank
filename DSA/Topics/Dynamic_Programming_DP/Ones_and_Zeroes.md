# Ones and Zeroes

**Problem Link:**
https://leetcode.com/problems/ones-and-zeroes/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Read the Problem

You have an array `strs` of binary strings (containing only '0' and '1'), and two integers `m` and `n`. Return the **maximum number of strings** you can pick such that the total count of 0s across picked strings is ≤ m, and total count of 1s is ≤ n.

Example: `strs = ["10", "0001", "111001", "1", "0"]`, m = 5, n = 3.

String counts (zeros, ones):
- "10" → (1, 1)
- "0001" → (3, 1)
- "111001" → (2, 4)
- "1" → (0, 1)
- "0" → (1, 0)

Pick as many as possible with total zeros ≤ 5, total ones ≤ 3.

Try picking {"10", "0001", "1", "0"}: zeros = 1+3+0+1 = 5, ones = 1+1+1+0 = 3. Four strings, exactly at the limits. ✓

Can we get 5? Include "111001" which has (2, 4) ones. Would push ones count to 3 + 4 = 7 > n. Dropping some other string to accommodate: might reduce count. Can't easily get 5.

Answer: **4**.

----------------------------------------

## Step 2: Shape of the Problem

Each string is an item with two "costs" (zeros and ones). We have two "budgets" (m and n). Maximize the count of chosen items subject to the budgets.

This is **0/1 knapsack** — classic — but with **two** capacity dimensions instead of one.

In standard 0/1 knapsack, state is (items considered, remaining capacity). Here, state is (items considered, remaining zero-budget, remaining one-budget).

----------------------------------------

## Step 3: Set Up the DP

Let `dp[i][j]` = maximum number of strings we can pick, using at most `i` zeros and `j` ones.

For each string with `z` zeros and `o` ones:
- **Skip it:** `dp[i][j]` stays.
- **Take it (if z ≤ i and o ≤ j):** `dp[i][j] = dp[i - z][j - o] + 1`.

Take the max.

Iteration: process strings one at a time, update dp.

```
dp = 2D array of (m+1) × (n+1), initialized to 0.

for each string:
    count its zeros z and ones o.
    for i from m down to z:
        for j from n down to o:
            dp[i][j] = max(dp[i][j], dp[i - z][j - o] + 1)

return dp[m][n]
```

Key detail: iterate `i` and `j` **downward**. Why? Because in 0/1 knapsack, we can't use the same item twice. Iterating upward would let `dp[i - z][j - o]` already reflect the new item, double-counting.

Going downward ensures `dp[i - z][j - o]` is from the **previous** iteration (before this item was considered).

----------------------------------------

## Step 4: Trace for `strs = ["10", "0001", "1", "0"]`, m = 5, n = 3

I'll only process these 4 strings (ignoring "111001" since the answer uses the other 4).

Zeros and ones per string:
- "10": z=1, o=1.
- "0001": z=3, o=1.
- "1": z=0, o=1.
- "0": z=1, o=0.

Start with dp = zeros (6×4 grid: i from 0 to 5, j from 0 to 3).

**Process "10" (z=1, o=1):**
For i from 5 down to 1, j from 3 down to 1:
- dp[i][j] = max(dp[i][j], dp[i-1][j-1] + 1).
- All dp[i-1][j-1] are 0, so dp[i][j] becomes 1 for all (i ≥ 1, j ≥ 1).

After: dp[i][j] = 1 for (i, j) with i ≥ 1 and j ≥ 1. Others 0.

**Process "0001" (z=3, o=1):**
For i from 5 down to 3, j from 3 down to 1:
- dp[i][j] = max(dp[i][j], dp[i-3][j-1] + 1).
- For i = 3, j = 1: dp[0][0] + 1 = 1. dp[3][1] was 1. Max 1. No change.
- For i = 4, j = 1: dp[1][0] + 1 = 1. dp[4][1] = 1. No change.
  (Hmm, but we'd like to show the DP picking up this string in combination with earlier.)
- For i = 4, j = 2: dp[1][1] + 1 = 2. dp[4][2] was 1. Now 2. ✓
- For i = 5, j = 2: dp[2][1] + 1 = 2. dp[5][2] was 1. Now 2.
- Etc.

After "0001": dp[i][j] reflects "can pick up to 2 strings using these budgets."

**Process "1" (z=0, o=1):**
For i from 5 down to 0, j from 3 down to 1:
- dp[i][j] = max(dp[i][j], dp[i][j-1] + 1).
- For i = 4, j = 3: dp[4][2] was 2 (after "0001"). dp[4][3] = max(old, 2+1) = 3.
- For i = 5, j = 3: dp[5][2] was 2. dp[5][3] = max(old, 3).

After "1": some cells jump to 3.

**Process "0" (z=1, o=0):**
For i from 5 down to 1, j from 3 down to 0:
- dp[i][j] = max(dp[i][j], dp[i-1][j] + 1).
- For i = 5, j = 3: dp[4][3] was 3 (after "1"). dp[5][3] = max(old, 3+1) = 4.

After all 4 strings: dp[5][3] = 4. ✓

----------------------------------------

## Step 5: Why Downward Iteration Prevents Double-Counting

Consider the inner loop when processing a new string. We're updating dp using `dp[i - z][j - o]`.

If we went upward (i from z to m, j from o to n), we'd compute:
- dp[z][o] = max(dp[z][o], dp[0][0] + 1). OK.
- dp[2z][2o] = max(dp[2z][2o], dp[z][o] + 1). But dp[z][o] was already updated with **this item**. So we're picking the same item twice!

Going downward fixes this: when we update dp[2z][2o], dp[z][o] still holds its pre-update value (didn't process it yet in this pass). No double-count.

This directional trick is the defining feature of **0/1 knapsack** vs **unbounded knapsack** (which iterates upward).

----------------------------------------

## Step 6: Name It

**2D 0/1 knapsack** — "items with two-dimensional costs, one-dimensional value (count)." Same pattern solves:
- Target Sum (1D 0/1 knapsack with +/- choices).
- Partition Equal Subset Sum (1D 0/1 knapsack on half the total).
- Coin Change II (unbounded 1D knapsack, different direction).

The number of budget dimensions matches the dimensionality of the DP table (excluding the item index axis).

----------------------------------------

## Step 7: Complexity

Time: for each of the N strings, we update an `(m+1) × (n+1)` table. **O(N · m · n)**.
Space: **O(m · n)** — one 2D table.

For typical constraints (N ≤ 600, m, n ≤ 100), ~6 × 10^6 operations — fast.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int findMaxForm(vector<string>& strs, int m, int n) {
    vector<vector<int>> dp(m + 1, vector<int>(n + 1, 0));

    for (const string& s : strs) {
        int zeros = count(s.begin(), s.end(), '0');
        int ones  = s.size() - zeros;

        for (int i = m; i >= zeros; --i) {
            for (int j = n; j >= ones; --j) {
                dp[i][j] = max(dp[i][j], dp[i - zeros][j - ones] + 1);
            }
        }
    }
    return dp[m][n];
}
```

Clean. The downward iteration in both `i` and `j` is the critical detail — getting the direction wrong here produces very wrong answers (all items would be picked repeatedly).

----------------------------------------

## Step 9: Follow-up Questions

- **Items have weights/values too.** Add another dimension or use weighted DP. Maximize total value subject to budgets.
- **Unlimited copies of each string.** Change iteration to upward (`i from zeros to m`). That's unbounded knapsack.
- **Budgets can be very large (10^9).** DP table too big. Need a different approach (greedy if applicable, or more structure).
- **Three budgets instead of two.** 3D DP table, extra nested loop.
- **Reconstruct which strings were picked.** Track parent pointers in a separate table; backtrack from dp[m][n].
- **Why max (not min)?** Problem asks for maximum count. For minimum count with budget-constraint, different interpretation.
