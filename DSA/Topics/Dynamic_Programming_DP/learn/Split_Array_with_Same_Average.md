# Split Array with Same Average — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Split_Array_with_Same_Average.md`](../Split_Array_with_Same_Average.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/split-array-with-same-average/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/split-array-with-same-average/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: reduce equal-average split to "find a size-k subset summing to k·total/n." For each candidate k, that requires `k·total % n == 0`. Solve with SIZE-INDEXED subset-sum DP (or BITSET for speed).**

**Map of this file (9 sections):**

1. Read the problem
2. Math reduction
3. The integer-divisibility filter
4. Size-indexed subset-sum DP
5. Bitset acceleration
6. Why only k ≤ n/2
7. Code
8. Common pitfalls
9. The shape — partition with constraint

---

## 1. Read the problem

Given integer array `nums`, decide if it can be split into TWO non-empty subsets A and B with `avg(A) == avg(B)`.

**Examples:**

- `[1, 2, 3, 4, 5, 6, 7, 8]` → e.g., A={1,4,5,8} (avg 4.5), B={2,3,6,7} (avg 4.5). **true**.
- `[3, 1]` → only one split possible, avgs 3 and 1. **false**.

---

## 2. Math reduction

> **Mini-refresher: if both halves have the total average T, then any subset with avg = T works.**
>
> T = sum(nums) / n. For a subset A of size k to have avg T: sum(A) = k · T = k · sum(nums) / n.
>
> The problem reduces to: **for some k (1 ≤ k < n), does a SIZE-k SUBSET sum to k · total / n?**

If we find any such (k, subset), partition exists.

---

## 3. The integer-divisibility filter

> **Mini-refresher: `k · total` must be divisible by `n`.**
>
> Otherwise the required subset sum isn't an integer, so no subset can match.
>
> Skip values of k that fail this divisibility test → big speedup.

---

## 4. Size-indexed subset-sum DP

`possible[k]` = set of sums achievable by SIZE-k subsets.

Initialize `possible[0] = {0}`. For each item x:
- For k from current max down to 1 (DOWNWARD to prevent reuse):
  - `possible[k] |= {s + x : s in possible[k-1]}`.

Then for each k ∈ [1, n/2] with `k · total % n == 0`, check if `(k · total / n) ∈ possible[k]`.

---

## 5. Bitset acceleration

If sums fit in a bounded range (n ≤ 30, values ≤ 10000 → sum ≤ 300000), represent `possible[k]` as a BITSET:

```
possible[k] |= possible[k-1] << x
```

The shift-by-x adds x to every sum in possible[k-1]. One bitwise op handles thousands of sums at once.

---

## 6. Why only k ≤ n/2

If size-k subset A averages T, then size-(n-k) complement B also averages T. So if size k works, so does size n-k — same partition. Check only k ∈ [1, n/2] to halve the work.

---

## 7. Code

**C++ — bitset DP:**

```cpp
bool splitArraySameAverage(vector<int>& nums) {
    int n = nums.size();
    if (n < 2) return false;
    int total = accumulate(nums.begin(), nums.end(), 0);

    vector<bitset<300001>> possible(n / 2 + 1);
    possible[0][0] = 1;

    for (int x : nums) {
        for (int k = min((int)possible.size() - 1, n / 2); k >= 1; --k) {
            possible[k] |= possible[k - 1] << x;
        }
    }

    for (int k = 1; k <= n / 2; ++k) {
        if ((k * total) % n != 0) continue;
        int target = k * total / n;
        if (possible[k][target]) return true;
    }
    return false;
}
```

Complexity: time **O(n · (n/2) · sum / 64)** ≈ very fast for n ≤ 30. Space O(n · sum / 64) bits.

---

## 8. Common pitfalls

1. **Forgetting the divisibility check.** Trying every k → checking sums that can never be matched. Waste.
2. **Computing target as `k * total / n` BEFORE checking divisibility.** Integer division silently rounds — produces a wrong target. Order matters.
3. **Iterating k ASCENDING.** Reuses items within one pass. WRONG. Descending only.
4. **Checking k = n.** A subset of all elements means the OTHER subset is empty. Reject — both must be non-empty.
5. **Bitset size too small.** Sum can reach n · max_val. For LeetCode constraints (n ≤ 30, val ≤ 10000), 300001 is safe.

---

## 9. The shape — partition with constraint

The pattern: **partition reduces to subset-sum + size constraint.**

| Problem | Constraint |
|---|---|
| Partition Equal Subset Sum | size-anything, sum = total/2 |
| **This problem** | size-k, sum = k · total / n |
| Target Sum | with ± signs (also reduces to subset sum) |
| K-Sum subsets | size-k summing to S |
| Partition K Equal Sum Subsets | K groups, each sum = total/K (NP-hard) |

**Pattern to internalize:**

> "Partition with average / sum constraint → subset-sum DP, possibly with SIZE as an extra DP dimension. Use bitset shifts for high-throughput addition."

---

> **Self-check — the question to ask next time.**
>
> When asked to split into subsets with EQUAL average/sum-per-element:
>
> > **"Each candidate size k requires sum = k · total/n. Integer divisibility filter. Size-indexed subset-sum DP, bitset shift = add."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Split_Array_with_Same_Average.md`](../Split_Array_with_Same_Average.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Partition_Equal_Subset_Sum.md`](./Partition_Equal_Subset_Sum.md), [`Ones_and_Zeroes.md`](./Ones_and_Zeroes.md).
  - Coming next: [`Minimum_Jumps_to_Reach_Home.md`](./Minimum_Jumps_to_Reach_Home.md), [`Matrix_Chain_Multiplication.md`](./Matrix_Chain_Multiplication.md).
