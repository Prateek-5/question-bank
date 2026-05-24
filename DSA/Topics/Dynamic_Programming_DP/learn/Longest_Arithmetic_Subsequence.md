# Longest Arithmetic Subsequence — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Longest_Arithmetic_Subsequence.md`](../Longest_Arithmetic_Subsequence.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/longest-arithmetic-subsequence/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: state = (last index, common difference). Use a HASHMAP per index because the difference can be any integer. `dp[j][d] = dp[i][d] + 1` for previous index i with `a[j] - a[i] = d`.**

**Map of this file (8 sections):**

1. Read the problem
2. The 2D state `(j, d)`
3. The recurrence
4. Why hashmaps (not 2D array)
5. Code
6. Trace it
7. Common pitfalls
8. The shape — LIS-family with extra state

---

## 1. Read the problem

Given integer array `nums`, find the length of the LONGEST ARITHMETIC SUBSEQUENCE (consecutive picked elements have the same difference).

**Example:** `[9, 4, 7, 2, 10]` → `[4, 7, 10]` (diff 3) → **3**.

Note: any 2-element subsequence is trivially arithmetic, so the answer is ≥ 2 for n ≥ 2.

---

## 2. The 2D state `(j, d)`

> **Mini-refresher: fix the LAST element AND the common difference.**
>
> Let `dp[j][d]` = length of the longest arithmetic subsequence ENDING at index j with common difference d.
>
> Answer = `max(dp[j][d])` over all (j, d).
>
> Why both dimensions? Without `d`, two APs ending at j with different differences look the same, so we'd lose info. The (j, d) pair uniquely identifies the AP's "tail state."

---

## 3. The recurrence

For each pair (i, j) with i < j: the difference is `d = nums[j] - nums[i]`. This pair can either:
- Extend an AP ending at i with the same d → `dp[j][d] = dp[i][d] + 1`.
- Start a fresh pair (i, j) → length 2.

So `dp[j][d] = max(dp[j][d], dp[i][d] + 1 if exists else 2)` over all i < j.

---

## 4. Why hashmaps (not 2D array)

The difference d can be any integer in `[-10^4, 10^4]` (or larger). A 2D dense array indexed by (j, d) would be O(n · range) — wasteful.

> **Mini-refresher: per-index hashmap.**
>
> Use `dp[j]: dict[diff → length]`. Each j stores only the diffs ACTUALLY seen. Memory O(n²) worst case; cache-friendly enough in practice.

---

## 5. Code

**C++:**

```cpp
int longestArithSeqLength(vector<int>& nums) {
    int n = nums.size();
    vector<unordered_map<int, int>> dp(n);
    int best = 2;
    for (int j = 1; j < n; ++j) {
        for (int i = 0; i < j; ++i) {
            int d = nums[j] - nums[i];
            auto it = dp[i].find(d);
            int len = (it != dp[i].end()) ? it->second + 1 : 2;
            dp[j][d] = max(dp[j][d], len);
            best = max(best, dp[j][d]);
        }
    }
    return best;
}
```

**Python:**

```python
def longestArithSeqLength(nums):
    n = len(nums)
    dp = [dict() for _ in range(n)]
    best = 2
    for j in range(1, n):
        for i in range(j):
            d = nums[j] - nums[i]
            length = dp[i].get(d, 1) + 1   # base "1" because (i alone) has length 1
            dp[j][d] = max(dp[j].get(d, 2), length)
            best = max(best, dp[j][d])
    return best
```

Complexity: **O(n²)** time, **O(n²)** worst-case space.

---

## 6. Trace it

`nums = [9, 4, 7, 2, 10]`. Walking the (j, i) pairs:

```
j=1 (4): pair (0,1) d = 4-9 = -5. dp[1][-5] = 2.
j=2 (7):
  (0,2) d = -2. dp[2][-2] = 2.
  (1,2) d = 3.  dp[2][3] = 2.
j=3 (2):
  (0,3) d = -7. dp[3][-7] = 2.
  (1,3) d = -2. dp[3][-2] = 2.
  (2,3) d = -5. dp[3][-5] = 2.
j=4 (10):
  (0,4) d = 1.  dp[4][1] = 2.
  (1,4) d = 6.  dp[4][6] = 2.
  (2,4) d = 3.  dp[2][3] = 2 → dp[4][3] = 3.   ← winner
  (3,4) d = 8.  dp[4][8] = 2.

best = 3.  ✓ (AP: 4, 7, 10)
```

---

## 7. Common pitfalls

1. **Returning the highest LENGTH-2 result (e.g., 1) on edge cases.** For n ≥ 2 the minimum is 2; initialize `best = 2`.
2. **Treating `dp[i][d]` as "length-of-pair" (= 2) when it doesn't exist.** When extending, the formula is `dp[i][d] + 1` for an existing dp[i][d] (already length ≥ 2). The "fresh pair" case at (i, j) is exactly length 2.
3. **Using a 2D dense array.** Diffs span a huge range; use hashmap.
4. **Overwriting dp[j][d] without max.** Multiple i's may produce the same d at j; take the best.
5. **Treating arithmetic = positive difference only.** Diffs can be negative (decreasing AP) or zero (constant AP).

---

## 8. The shape — LIS-family with extra state

The pattern: **subsequence DP with an EXTRA dimension that captures the constraint.**

| Problem | Extra state |
|---|---|
| LIS | (none — just last element) |
| **This problem** | + common difference |
| Longest Geometric Subsequence | + common ratio |
| Longest String Chain | + last word/length |
| Wiggle Subsequence | + up/down flag |
| Arithmetic Slices II | + same dimension, but COUNT not max |

**Pattern to internalize:**

> "When the LIS-style problem has a TRANSITION-LEVEL invariant (difference, ratio, parity), add that invariant to the state. Per-index hashmap keeps memory tame."

---

> **Self-check — the question to ask next time.**
>
> When the subsequence must satisfy a PER-STEP property (constant difference, constant ratio, alternating direction), ask:
>
> > **"State = (last index, property value). DP over both. Hashmap for sparse property values."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Longest_Arithmetic_Subsequence.md`](../Longest_Arithmetic_Subsequence.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Longest_Increasing_Subsequence.md`](./Longest_Increasing_Subsequence.md).
  - Coming next: [`Russian_Doll_Envelopes.md`](./Russian_Doll_Envelopes.md), [`Maximum_Height_by_Stacking_Cuboids.md`](./Maximum_Height_by_Stacking_Cuboids.md), [`Longest_Common_Subsequence.md`](./Longest_Common_Subsequence.md).
