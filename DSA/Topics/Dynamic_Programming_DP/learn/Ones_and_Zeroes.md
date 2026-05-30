# Ones and Zeroes — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Ones_and_Zeroes.md`](../Ones_and_Zeroes.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/ones-and-zeroes/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/ones-and-zeroes/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: 2D 0/1 KNAPSACK. Each item has TWO costs (zeros, ones); we have TWO budgets (m, n). Maximize count. Iterate BOTH dimensions DOWNWARD to avoid reuse.**

**Map of this file (8 sections):**

1. Read the problem
2. Why this is 2D knapsack
3. The recurrence
4. Why DOWNWARD iteration (both dimensions)
5. Code
6. Trace it
7. Common pitfalls
8. The shape — multi-dim knapsack

---

## 1. Read the problem

Array `strs` of binary strings, integers `m` and `n`. Return the MAX number of strings you can pick such that total zeros ≤ m AND total ones ≤ n.

**Example:** `strs = ["10", "0001", "111001", "1", "0"]`, m=5, n=3 → can pick `{"10", "0001", "1", "0"}` (zeros=5, ones=3) → **4**.

---

## 2. Why this is 2D knapsack

> **Mini-refresher: each string has TWO costs (zeros, ones) and contributes VALUE = 1 (it counts).**
>
> Standard 0/1 knapsack: items with weight + value; cap on total weight; maximize value.
>
> Here: weight is REPLACED with (zeros, ones); two caps (m, n); value = 1 per item.
>
> Just expand the DP state from 1D `dp[capacity]` to 2D `dp[zeros_used][ones_used]`.

---

## 3. The recurrence

`dp[i][j]` = max count of strings selected with zeros ≤ i and ones ≤ j.

For each string with z zeros and o ones:
- Skip: `dp[i][j]` unchanged.
- Take (if z ≤ i AND o ≤ j): `dp[i][j] = max(dp[i][j], dp[i-z][j-o] + 1)`.

---

## 4. Why DOWNWARD iteration (both dimensions)

> **Mini-refresher: same logic as 1D 0/1 knapsack — extended.**
>
> If we iterate i ASCENDING (or j ASCENDING) after starting to process a string, `dp[i-z][j-o]` could ALREADY reflect this string — so we'd be using the string MULTIPLE times.
>
> Fix: iterate BOTH i and j DOWNWARD (i from m to z, j from n to o). Then `dp[i-z][j-o]` is from BEFORE this string's update — 0/1 (use once) semantics preserved.

---

## 5. Code

**C++:**

```cpp
int findMaxForm(vector<string>& strs, int m, int n) {
    vector<vector<int>> dp(m + 1, vector<int>(n + 1, 0));

    for (const string& s : strs) {
        int zeros = count(s.begin(), s.end(), '0');
        int ones  = (int)s.size() - zeros;

        for (int i = m; i >= zeros; --i) {
            for (int j = n; j >= ones; --j) {
                dp[i][j] = max(dp[i][j], dp[i - zeros][j - ones] + 1);
            }
        }
    }
    return dp[m][n];
}
```

Complexity: **O(N · m · n)** time, **O(m · n)** space.

---

## 6. Trace it

`strs = ["10", "0001", "1", "0"]`, m=5, n=3. Item costs:
- "10": z=1, o=1.
- "0001": z=3, o=1.
- "1": z=0, o=1.
- "0": z=1, o=0.

Start dp all zero.

After "10" (z=1, o=1): dp[i][j] = 1 for i≥1, j≥1.

After "0001" (z=3, o=1):
- dp[4][2] = max(1, dp[1][1]+1) = 2.
- dp[5][2] = max(1, dp[2][1]+1) = 2.
- dp[4][3] = max(1, dp[1][2]+1) = 2.
- dp[5][3] = max(1, dp[2][2]+1) = 2.
(some cells reach 2)

After "1" (z=0, o=1):
- dp[i][3] += 1 where dp[i][2] is high. dp[4][3] = max(2, dp[4][2]+1) = 3. dp[5][3] = max(2, dp[5][2]+1) = 3.

After "0" (z=1, o=0):
- dp[5][3] = max(3, dp[4][3]+1) = 4.  ✓

---

## 7. Common pitfalls

1. **Iterating i or j ASCENDING.** Allows the same string to be picked multiple times. Wrong.
2. **Forgetting to bound `i ≥ z` and `j ≥ o`.** Out-of-bounds reads on dp[i-z][j-o].
3. **3D DP (string-index + zeros + ones).** Works but wastes O(N · m · n) space — the 2D rolling version is enough.
4. **Counting "1" wrong.** Use `count(s.begin(), s.end(), '0')` for zeros; ones = length - zeros.
5. **Off-by-one on m+1 vs n+1 sizing.** Allocate `(m+1) × (n+1)` to include the zero-budget corner.

---

## 8. The shape — multi-dim knapsack

The pattern: **each item has K cost dimensions; total has K budgets; maximize VALUE.**

| Problem | Cost dims | Value |
|---|---|---|
| Classic 0/1 Knapsack | 1 (weight) | each item's value |
| **This problem** | 2 (zeros, ones) | 1 per item (count) |
| Target Sum | 1 (signed sum) | count of ways |
| Last Stone Weight II | 1 (sum) | minimize diff |
| Profitable Schemes | 2 (people, profit) | count |

**Pattern to internalize:**

> "Each cost dimension adds a DP axis. Iterate ALL axes DOWNWARD for 0/1 (each item used once). N · ∏(budgets) time."

---

> **Self-check — the question to ask next time.**
>
> When items have MULTIPLE costs and you have MULTIPLE budgets:
>
> > **"K-dim DP, K nested loops iterating DOWNWARD. Each item updates dp[budget1][budget2]... in place."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Ones_and_Zeroes.md`](../Ones_and_Zeroes.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Partition_Equal_Subset_Sum.md`](./Partition_Equal_Subset_Sum.md).
  - Coming next: [`Split_Array_with_Same_Average.md`](./Split_Array_with_Same_Average.md), [`Minimum_Jumps_to_Reach_Home.md`](./Minimum_Jumps_to_Reach_Home.md), [`Matrix_Chain_Multiplication.md`](./Matrix_Chain_Multiplication.md).
