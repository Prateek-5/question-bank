# Range Sum Query — Immutable — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Range_Sum_Query_Immutable.md`](../Range_Sum_Query_Immutable.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/range-sum-query-immutable/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/range-sum-query-immutable/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **The lesson: STATIC array + many range-sum queries = PREFIX SUM. Precompute once in O(n); each query is O(1) via `prefix[r+1] - prefix[l]`. No segment tree needed for IMMUTABLE arrays.**

**Map of this file (7 sections):**

1. Read the problem
2. The naive scan
3. The prefix-sum trick
4. Indexing: prefix[0] = 0
5. Code
6. Trace it
7. The shape — invertible-op prefix arrays

---

## 1. Read the problem

Class `NumArray` with `sumRange(l, r)` returning `nums[l] + ... + nums[r]` (inclusive). The array is FIXED — no updates.

**Example:** `nums = [-2, 0, 3, -5, 2, -1]`. `sumRange(0, 2) = 1`. `sumRange(2, 5) = -1`. `sumRange(0, 5) = -3`.

---

## 2. The naive scan

Per query, loop from l to r — O(n) per query. For q queries, O(n·q). Too slow for many queries.

The wasteful part: each query re-sums values we already summed in prior queries. Caching helps.

---

## 3. The prefix-sum trick

> **Mini-refresher: cumulative sums.**
>
> `prefix[i]` = sum of `nums[0..i-1]` (first i elements). Then:
>
> ```
> sumRange(l, r) = prefix[r+1] - prefix[l]
> ```
>
> Because `prefix[r+1]` = sum of [0..r], and subtracting `prefix[l]` (sum of [0..l-1]) leaves exactly indices [l..r].
>
> Precompute prefix in O(n). Each query is then ONE subtraction = O(1).

---

## 4. Indexing: prefix[0] = 0

> **Mini-refresher: include a sentinel `prefix[0] = 0`.**
>
> With this, `sumRange(0, r) = prefix[r+1] - prefix[0] = prefix[r+1]` — no special case for l=0.
>
> The array has size n+1 (not n).

---

## 5. Code

**C++:**

```cpp
class NumArray {
    vector<int> prefix;
public:
    NumArray(vector<int>& nums) {
        prefix.assign(nums.size() + 1, 0);
        for (int i = 0; i < (int)nums.size(); ++i) {
            prefix[i + 1] = prefix[i] + nums[i];
        }
    }
    int sumRange(int left, int right) {
        return prefix[right + 1] - prefix[left];
    }
};
```

Complexity: O(n) constructor, **O(1) per query**, O(n) space.

---

## 6. Trace it

`nums = [-2, 0, 3, -5, 2, -1]`. n=6.

prefix:
- prefix[0] = 0
- prefix[1] = 0 + (-2) = -2
- prefix[2] = -2 + 0 = -2
- prefix[3] = -2 + 3 = 1
- prefix[4] = 1 + (-5) = -4
- prefix[5] = -4 + 2 = -2
- prefix[6] = -2 + (-1) = -3

Queries:
- sumRange(0, 2) = prefix[3] - prefix[0] = 1 - 0 = **1**.  ✓
- sumRange(2, 5) = prefix[6] - prefix[2] = -3 - (-2) = **-1**.  ✓
- sumRange(0, 5) = prefix[6] - prefix[0] = **-3**.  ✓

---

## 7. The shape — invertible-op prefix arrays

The pattern: **for any ASSOCIATIVE + INVERTIBLE operation, prefix arrays give O(1) range queries on STATIC data.**

| Operation | Prefix definition | Range query |
|---|---|---|
| **Sum** | `prefix[i] = sum[0..i-1]` | prefix[r+1] - prefix[l] |
| XOR | `prefix[i] = xor[0..i-1]` | prefix[r+1] ^ prefix[l] (XOR self-inverse) |
| Product (mod prime) | running product | divide via modular inverse |
| Count of X | running count | difference |
| MIN/MAX | NOT invertible → use sparse table or segment tree | n/a |

**Pattern to internalize:**

> "Immutable array + range query with invertible op → PREFIX. O(n) build, O(1) per query. For non-invertible ops (min/max), need sparse table or segment tree."

---

> **Self-check — the question to ask next time.**
>
> When asked for many range sums on a static array:
>
> > **"Prefix sum array of size n+1 with prefix[0]=0. Query = prefix[r+1] - prefix[l]. O(1) per query."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Range_Sum_Query_Immutable.md`](../Range_Sum_Query_Immutable.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Range_Sum_Query_Mutable.md`](./Range_Sum_Query_Mutable.md), [`Range_Maximum_Query.md`](./Range_Maximum_Query.md).
