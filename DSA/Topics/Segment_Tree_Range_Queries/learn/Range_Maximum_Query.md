# Range Maximum Query — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Range_Maximum_Query.md`](../Range_Maximum_Query.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://www.geeksforgeeks.org/range-minimum-query-for-static-array/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/range-minimum-query-for-static-array/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: STATIC array + many range-max queries → SPARSE TABLE. Precompute `sparse[k][i]` = max of size-2^k windows. Query = max of two overlapping power-of-two windows. O(n log n) build, O(1) query. Works because MAX is IDEMPOTENT (overlap doesn't double-count).**

**Map of this file (9 sections):**

1. Read the problem
2. Why prefix sum doesn't work
3. Sparse table — power-of-two windows
4. The O(1) query trick
5. Why idempotence matters
6. Code
7. Trace it
8. When sparse table works (and when it doesn't)
9. Common pitfalls

---

## 1. Read the problem

STATIC integer array. Answer many `query(l, r)` = max of `arr[l..r]`.

**Example:** `arr = [1, 3, 2, 7, 9, 11, 3]`. `query(1, 4) = 9`. `query(0, 6) = 11`.

---

## 2. Why prefix sum doesn't work

Prefix sums rely on the inverse: `range_sum = prefix[r+1] - prefix[l]`. Max has NO INVERSE — you can't "subtract" a max.

So we need a different precomputation.

---

## 3. Sparse table — power-of-two windows

> **Mini-refresher: precompute max over every power-of-2 window.**
>
> `sparse[k][i]` = max of `arr[i..i + 2^k - 1]` (window of size 2^k starting at i).
>
> Base: `sparse[0][i] = arr[i]`.
>
> Recurrence: `sparse[k][i] = max(sparse[k-1][i], sparse[k-1][i + 2^(k-1)])` — combine two halves of size 2^(k-1) to cover size 2^k.
>
> Build: O(n log n) time and space.

---

## 4. The O(1) query trick

> **Mini-refresher: cover [l, r] with two overlapping power-of-two windows.**
>
> Let `len = r - l + 1`, `k = floor(log2(len))`. Two windows of size 2^k:
> - Anchored at l: covers `[l, l + 2^k - 1]`.
> - Ending at r: covers `[r - 2^k + 1, r]`.
>
> Together they cover [l, r] (with possible overlap; that's OK).
>
> Query: `max(sparse[k][l], sparse[k][r - 2^k + 1])`.

ONE max combination = O(1).

---

## 5. Why idempotence matters

Sparse table relies on the OVERLAP being harmless. Max is IDEMPOTENT: `max(x, x) = x`. Overlapping the same element twice doesn't change the result.

This works for: **max, min, GCD, bitwise OR/AND**.

It does NOT work for SUM (because `x + x = 2x` ≠ x). For sum, use prefix sums or a segment tree.

---

## 6. Code

**C++:**

```cpp
class SparseTable {
    vector<vector<int>> sparse;
    vector<int> log2_table;
public:
    SparseTable(vector<int>& arr) {
        int n = arr.size();
        int K = (int)log2(n) + 1;
        sparse.assign(K, vector<int>(n, 0));
        log2_table.assign(n + 1, 0);
        for (int i = 2; i <= n; ++i) log2_table[i] = log2_table[i / 2] + 1;
        for (int i = 0; i < n; ++i) sparse[0][i] = arr[i];
        for (int k = 1; (1 << k) <= n; ++k) {
            for (int i = 0; i + (1 << k) <= n; ++i) {
                sparse[k][i] = max(sparse[k-1][i], sparse[k-1][i + (1 << (k-1))]);
            }
        }
    }
    int query(int l, int r) {
        int len = r - l + 1;
        int k = log2_table[len];
        return max(sparse[k][l], sparse[k][r - (1 << k) + 1]);
    }
};
```

Complexity: build O(n log n), **query O(1)**, space O(n log n).

---

## 7. Trace it

`arr = [1, 3, 2, 7, 9, 11, 3]`. n=7.

sparse[0] (size-1 windows) = arr = [1, 3, 2, 7, 9, 11, 3].

sparse[1] (size-2 windows): max(arr[i], arr[i+1]):
- [0]=max(1,3)=3, [1]=3, [2]=7, [3]=9, [4]=11, [5]=11.

sparse[2] (size-4 windows): max(sparse[1][i], sparse[1][i+2]):
- [0]=max(3,7)=7, [1]=max(3,9)=9, [2]=max(7,11)=11, [3]=max(9,11)=11.

**Query(1, 4):** len=4, k=2. max(sparse[2][1], sparse[2][1]) = max(9, 9) = **9**.  ✓

**Query(0, 6):** len=7, k=2 (floor log2 7 = 2). max(sparse[2][0], sparse[2][3]) = max(7, 11) = **11**.  ✓

---

## 8. When sparse table works (and when it doesn't)

| Setting | Sparse table fits? |
|---|---|
| Static array, idempotent op (min/max/GCD) | YES — best choice |
| Static array, non-idempotent (sum, product) | NO — use prefix arrays |
| Mutable array (updates) | NO — use segment tree (rebuild is O(n log n)) |
| 2D | YES — 2D sparse table, O(n m log n log m) build, O(1) query |

---

## 9. Common pitfalls

1. **Using upper_bound on log2 instead of floor.** Use `floor(log2(len))`. A precomputed `log2_table[]` avoids floating-point issues.
2. **Sum/product with sparse table.** Wrong — non-idempotent. Use prefix sums.
3. **Trying to update.** Sparse table requires full rebuild. Use segment tree for mutability.
4. **Window-end out of bounds.** Ensure `i + 2^k - 1 < n` when building.
5. **Off-by-one on `r - 2^k + 1`.** This is the START INDEX of the second window. Carefully derived from "window of size 2^k ending at r."

---

## Cross-references

- **Reference card (post-mastery):** [`../Range_Maximum_Query.md`](../Range_Maximum_Query.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Range_Sum_Query_Immutable.md`](./Range_Sum_Query_Immutable.md), [`Range_Sum_Query_Mutable.md`](./Range_Sum_Query_Mutable.md).
  - Coming next: [`Segment_Tree_Range_Maximum_Query_Node_Update.md`](./Segment_Tree_Range_Maximum_Query_Node_Update.md), [`Flipping_Sign_Problem_Lazy_Propagation.md`](./Flipping_Sign_Problem_Lazy_Propagation.md).
