# Partition Equal Subset Sum — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Partition_Equal_Subset_Sum.md`](../Partition_Equal_Subset_Sum.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/partition-equal-subset-sum/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/partition-equal-subset-sum/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: REDUCE to subset-sum-equals-T where T = total/2. THE 0/1 KNAPSACK template. `dp[s] |= dp[s - x]` for each x, with `s` iterated DOWNWARD (key trick to avoid double-use).**

**Map of this file (9 sections):**

1. Read the problem
2. The reduction — subset sum = total/2
3. The odd-sum early reject
4. The 0/1 knapsack DP
5. Why iterate `s` DOWNWARD
6. Code (boolean + bitset)
7. Trace it
8. Common pitfalls
9. The shape — subset-sum DP

---

## 1. Read the problem

Given an array of positive integers, return true iff it can be split into TWO subsets with EQUAL sums. Every element must go to one of the two subsets.

**Examples:**

- `[1, 5, 11, 5]` → sum=22, T=11. Subset `{11}` sums to 11. **true**.
- `[1, 2, 3, 5]` → sum=11 (odd). **false**.

---

## 2. The reduction — subset sum = total/2

> **Mini-refresher: equal partition ⇔ subset summing to total/2.**
>
> If total = 2T and some subset sums to T, its complement also sums to T. Partition exists.
>
> Conversely, if a partition exists, both halves sum to T = total/2.
>
> So the problem reduces to: "is there a subset summing to T = total/2?"

---

## 3. The odd-sum early reject

If total is ODD, T = total/2 isn't an integer → no equal partition possible. Return false IMMEDIATELY.

```python
if sum(nums) % 2: return False
T = sum(nums) // 2
```

---

## 4. The 0/1 knapsack DP

> **Mini-refresher: subset sum = 0/1 knapsack with weight = value.**
>
> Let `dp[s]` = "is there a subset summing to exactly s using items considered so far?"
>
> Initially `dp[0] = true`, all others false.
>
> For each item x, update: `dp[s] |= dp[s - x]` for s from T down to x.

The boolean OR captures "either we already could reach s without x, OR we can reach s by adding x to a subset that summed to s-x."

---

## 5. Why iterate `s` DOWNWARD

> **Mini-refresher: descending `s` prevents double-use.**
>
> If we iterate `s` ASCENDING after a fresh row, `dp[s] = dp[s - x]` reads `dp[s-x]` AFTER its update — so we'd be using `x` MULTIPLE times within one "process this item" pass. That's UNBOUNDED knapsack.
>
> For 0/1 (each item used at most once): iterate `s` DOWNWARD from T to x. Then `dp[s - x]` is still the PREVIOUS-row value.

The direction is the DIFFERENCE between 0/1 (descending) and unbounded (ascending) knapsack. Memorize this distinction.

---

## 6. Code (boolean + bitset)

**C++ — boolean DP:**

```cpp
bool canPartition(vector<int>& nums) {
    int sum = accumulate(nums.begin(), nums.end(), 0);
    if (sum & 1) return false;
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

**C++ — bitset (faster):**

```cpp
bool canPartition(vector<int>& nums) {
    int sum = accumulate(nums.begin(), nums.end(), 0);
    if (sum & 1) return false;
    int target = sum / 2;

    bitset<10001> dp;
    dp[0] = 1;
    for (int x : nums) dp |= (dp << x);
    return dp[target];
}
```

`dp | (dp << x)` does the entire row update in O(target / 64) by leveraging 64-bit OR operations.

Complexity: **O(n · target)** boolean, **O(n · target / 64)** bitset. Space O(target).

---

## 7. Trace it

`nums = [1, 5, 11, 5]`. sum=22, target=11.

Initial: `dp = [T, F, F, F, F, F, F, F, F, F, F, F]`.

Process 1 (s from 11 down to 1):
- `dp[1] |= dp[0]` = T. (Now dp[1] = T.)
- Others unchanged.
- `dp = [T, T, F, F, F, F, F, F, F, F, F, F]`.

Process 5 (s from 11 down to 5):
- dp[6] |= dp[1] = T. dp[5] |= dp[0] = T. Others unchanged.
- `dp = [T, T, F, F, F, T, T, F, F, F, F, F]`.

Process 11 (s from 11 down to 11):
- dp[11] |= dp[0] = T.
- `dp = [T, T, F, F, F, T, T, F, F, F, F, T]`.

dp[11] = **T** → can partition.  ✓

---

## 8. Common pitfalls

1. **Iterating `s` ASCENDING.** Allows double-use of items → unbounded knapsack. Wrong answer.
2. **Forgetting the odd-sum check.** Wastes time computing a doomed DP.
3. **Allocating a 2D DP table.** Works but uses O(n · T) space. The 1D trick gets O(T).
4. **Setting `dp[0] = false`.** dp[0] = TRUE — the empty subset sums to 0.
5. **Iterating `s` only down to 0.** Stop at `s = x` (you'd be reading `dp[s-x]` for s < x which is meaningless).

---

## 9. The shape — subset-sum DP

The pattern: **0/1 knapsack — for each item, choose include or skip; track reachable sums/values.**

| Problem | Twist |
|---|---|
| **This problem** | boolean reachability to T = total/2 |
| Subset Sum to K | boolean reachability to K |
| 0/1 Knapsack (classic) | max value with capacity bound |
| Target Sum (LC 494) | with ± signs, reduces to subset sum |
| Ones and Zeroes | 2D knapsack (m zeros, n ones) |
| Last Stone Weight II | minimize difference = subset sum |
| Coin Change II | unbounded — iterate s ASCENDING |
| Partition K Equal Sum Subsets | bitmask DP, harder |

**Pattern to internalize:**

> "0/1 knapsack: for each item, descending update; for unbounded, ascending update. The TRICK isn't the recurrence — it's the loop direction."

---

> **Self-check — the question to ask next time.**
>
> When you see "can we pick a subset summing to ___" or "is there a partition with property ___":
>
> > **"Reduce to subset sum. dp[s] |= dp[s-x] for each x, iterate s DOWNWARD for 0/1. O(n · sum) time, O(sum) space."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Partition_Equal_Subset_Sum.md`](../Partition_Equal_Subset_Sum.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Frog_Jump.md`](./Frog_Jump.md), [`Decode_Ways.md`](./Decode_Ways.md).
  - Coming next: [`Ones_and_Zeroes.md`](./Ones_and_Zeroes.md), [`Split_Array_with_Same_Average.md`](./Split_Array_with_Same_Average.md), [`Minimum_Jumps_to_Reach_Home.md`](./Minimum_Jumps_to_Reach_Home.md).
