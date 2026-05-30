# Subsequence of Size K With Largest Sum — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Subsequence_of_Size_K_With_Largest_Sum.md`](../Subsequence_of_Size_K_With_Largest_Sum.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/subsequence-of-size-k-with-the-largest-sum/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/subsequence-of-size-k-with-the-largest-sum/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The lesson: pick the k LARGEST values, but emit them in ORIGINAL INDEX order. Sort indexed pairs by value descending, take top k, then re-sort by index.**

**Map of this file (7 sections):**

1. Read the problem
2. Top-K + index preservation
3. Code
4. Trace it
5. Quickselect alternative
6. Common pitfalls
7. The shape — order-preserving top-K

---

## 1. Read the problem

Array `nums`, integer `k`. Return a SUBSEQUENCE of length k whose SUM is maximum. The output must preserve the original positional order of picked elements.

**Examples:**

- `nums = [2, 1, 3, 3], k = 2` → biggest two are 3, 3 → output **[3, 3]** (in original order, at indices 2 and 3).
- `nums = [-1, -2, 3, 4], k = 3` → top three: 4, 3, -1 → in original index order: **[-1, 3, 4]**.

---

## 2. Top-K + index preservation

> **Mini-refresher: two sorts.**
>
> 1. Sort indexed pairs `(value, index)` by VALUE DESCENDING. Take first k.
> 2. Sort the k picked pairs by INDEX ASCENDING.
> 3. Output values in the resulting order.

The first sort picks the k largest; the second restores ORIGINAL POSITIONAL ORDER (required for "subsequence" semantics).

---

## 3. Code

**C++:**

```cpp
vector<int> maxSubsequence(vector<int>& nums, int k) {
    int n = nums.size();
    vector<pair<int, int>> indexed;
    indexed.reserve(n);
    for (int i = 0; i < n; ++i) indexed.push_back({nums[i], i});

    sort(indexed.begin(), indexed.end(), greater<pair<int, int>>());
    indexed.resize(k);
    sort(indexed.begin(), indexed.end(),
         [](auto& a, auto& b) { return a.second < b.second; });

    vector<int> result;
    result.reserve(k);
    for (auto& [val, idx] : indexed) result.push_back(val);
    return result;
}
```

Complexity: **O(n log n)** time (sort dominates), **O(n)** space.

---

## 4. Trace it

`nums = [2, 1, 3, 3], k = 2`:

- Indexed: [(2,0), (1,1), (3,2), (3,3)].
- Sort desc by value: [(3,2), (3,3), (2,0), (1,1)].
- Top 2: [(3,2), (3,3)].
- Sort by index: [(3,2), (3,3)] (already in order).
- Output: **[3, 3]**.  ✓

`nums = [-1, -2, 3, 4], k = 3`:

- Indexed: [(-1,0), (-2,1), (3,2), (4,3)].
- Sort desc: [(4,3), (3,2), (-1,0), (-2,1)].
- Top 3: [(4,3), (3,2), (-1,0)].
- Sort by index: [(-1,0), (3,2), (4,3)].
- Output: **[-1, 3, 4]**.  ✓

---

## 5. Quickselect alternative

Quickselect finds the k-th largest in O(n) average. Then scan nums in original order; emit elements with value above the threshold (and tied-threshold elements until you have k). Trickier with duplicates at the threshold.

For typical interview constraints (n ≤ 10³), the two-sort approach is cleaner.

---

## 6. Common pitfalls

1. **Skipping the second sort.** Output would be in descending-value order — not a valid subsequence of the original.
2. **Sorting nums itself.** Loses index information needed for re-ordering.
3. **Returning the values without index info.** Same issue.
4. **Tie-breaking on equal values.** With duplicates, any choice is valid as long as the sum is maximal. The two-sort approach picks consistently based on tuple ordering.
5. **Modifying nums.** If caller needs nums preserved, work on a COPY.

---

## 7. The shape — order-preserving top-K

The pattern: **select top-k by value; emit in original order.**

| Problem | Order constraint |
|---|---|
| **This problem** | original index order |
| Top K Frequent Elements | any order |
| Kth Largest in Stream | not order-preserving |
| K Closest Points | any order |
| Subsequence of Words | original order in document |
| Print Largest M Subarrays | preserved indices |

**Pattern to internalize:**

> "Top-K with order preservation = sort by value desc + take k + sort by index asc. O(n log n)."

---

> **Self-check — the question to ask next time.**
>
> When asked for the largest-sum subsequence of size k, preserving order:
>
> > **"Pair (value, index). Sort by value desc, take k, sort by index asc, emit values."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Subsequence_of_Size_K_With_Largest_Sum.md`](../Subsequence_of_Size_K_With_Largest_Sum.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Kth_Largest_Element_in_an_Array.md`](../../Heap_Priority_Queue/learn/Kth_Largest_Element_in_an_Array.md), [`Top_K_Frequent_Elements.md`](../../Heap_Priority_Queue/learn/Top_K_Frequent_Elements.md).
  - Coming next: [`Number_of_Digit_One.md`](./Number_of_Digit_One.md), [`Divisor_Game.md`](./Divisor_Game.md), [`Memoization_DP_Basics.md`](./Memoization_DP_Basics.md), [`Implement_Rand10_Using_Rand7.md`](./Implement_Rand10_Using_Rand7.md).
