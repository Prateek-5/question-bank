# Range Sum Query — Mutable — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Range_Sum_Query_Mutable.md`](../Range_Sum_Query_Mutable.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/range-sum-query-mutable/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The lesson: when EITHER point updates OR range queries become frequent, prefix sums fail (update is O(n)). Use a SEGMENT TREE: build O(n), update O(log n), query O(log n). THE template; learn it once, reuse forever.**

**Map of this file (10 sections):**

1. Read the problem
2. Why prefix sums fail
3. Segment tree intuition
4. Array-based layout
5. Build, update, query
6. Code
7. Trace it
8. Complexity walkthrough
9. Common pitfalls
10. The shape — segment tree template

---

## 1. Read the problem

Class supporting:
- `update(i, val)`: set `nums[i] = val`.
- `sumRange(l, r)`: sum of `nums[l..r]`.

Both interleaved many times. Need O(log n) per op.

---

## 2. Why prefix sums fail

Prefix sums = O(1) query but O(n) UPDATE (rebuild). When updates and queries both happen often, prefix sums lose.

We need a structure with logarithmic costs on BOTH ops.

---

## 3. Segment tree intuition

> **Mini-refresher: hierarchical range decomposition.**
>
> Recursively split the array in halves. Each tree node stores the SUM of its range.
> - Root covers [0, n-1].
> - Each internal node's value = sum of its two children.
> - Leaves cover single elements.
>
> A range query [l, r] decomposes into O(log n) "canonical" sub-ranges (nodes whose range is fully inside [l, r]). Sum them up.
>
> A point update walks down to the affected leaf (O(log n) levels) and recomputes ancestors on the way back.

---

## 4. Array-based layout

Store the tree in array `tree[]` of size **4n**. Node v has:
- Left child at `2v`, right child at `2v+1`.
- Root at index 1 (makes arithmetic clean).

The 4n bound covers any non-power-of-2 n with padding.

---

## 5. Build, update, query

```
build(v, lo, hi):
    if lo == hi: tree[v] = nums[lo]; return
    mid = (lo + hi) / 2
    build(2v, lo, mid); build(2v+1, mid+1, hi)
    tree[v] = tree[2v] + tree[2v+1]

update(v, lo, hi, i, val):
    if lo == hi: tree[v] = val; return
    mid = (lo + hi) / 2
    if i <= mid: update(2v, lo, mid, i, val)
    else: update(2v+1, mid+1, hi, i, val)
    tree[v] = tree[2v] + tree[2v+1]

query(v, lo, hi, ql, qr):
    if qr < lo or ql > hi: return 0          # no overlap
    if ql <= lo and hi <= qr: return tree[v]  # full overlap
    mid = (lo + hi) / 2
    return query(2v, lo, mid, ql, qr) + query(2v+1, mid+1, hi, ql, qr)
```

Three operations, all recursive, all O(log n).

---

## 6. Code

**C++:**

```cpp
class NumArray {
    vector<int> tree;
    int n;

    void build(int v, int lo, int hi, vector<int>& nums) {
        if (lo == hi) { tree[v] = nums[lo]; return; }
        int mid = (lo + hi) / 2;
        build(2*v, lo, mid, nums);
        build(2*v+1, mid+1, hi, nums);
        tree[v] = tree[2*v] + tree[2*v+1];
    }
    void updateH(int v, int lo, int hi, int i, int val) {
        if (lo == hi) { tree[v] = val; return; }
        int mid = (lo + hi) / 2;
        if (i <= mid) updateH(2*v, lo, mid, i, val);
        else updateH(2*v+1, mid+1, hi, i, val);
        tree[v] = tree[2*v] + tree[2*v+1];
    }
    int queryH(int v, int lo, int hi, int ql, int qr) {
        if (qr < lo || ql > hi) return 0;
        if (ql <= lo && hi <= qr) return tree[v];
        int mid = (lo + hi) / 2;
        return queryH(2*v, lo, mid, ql, qr) + queryH(2*v+1, mid+1, hi, ql, qr);
    }
public:
    NumArray(vector<int>& nums) : n(nums.size()), tree(4 * nums.size(), 0) {
        if (n > 0) build(1, 0, n - 1, nums);
    }
    void update(int i, int val) { updateH(1, 0, n - 1, i, val); }
    int sumRange(int l, int r) { return queryH(1, 0, n - 1, l, r); }
};
```

Complexity: build O(n), each update/query **O(log n)**, space O(n).

---

## 7. Trace it

`nums = [1, 3, 5, 7, 9, 11]`. n = 6.

Tree structure (conceptual):
```
[0..5] sum=36
├── [0..2] sum=9
│   ├── [0..1] sum=4
│   │   ├── [0]=1
│   │   └── [1]=3
│   └── [2]=5
└── [3..5] sum=27
    ├── [3..4] sum=16
    │   ├── [3]=7
    │   └── [4]=9
    └── [5]=11
```

**sumRange(2, 4):**
- Root [0..5]: partial. Recurse.
- [0..2]: partial with [2..4]. Recurse.
  - [0..1]: disjoint. Return 0.
  - [2]: full. Return 5.
  - → 5.
- [3..5]: partial. Recurse.
  - [3..4]: full. Return 16.
  - [5]: disjoint. Return 0.
  - → 16.
- Root → 5 + 16 = **21**.  ✓ (5+7+9 = 21)

**update(3, 2):** walk to leaf [3], set 2. Recompute [3..4] = 2+9=11. [3..5] = 11+11=22. Root = 9+22=31.

---

## 8. Complexity walkthrough

- **Build:** each node touched once. n leaves + n-1 internals = ~2n = O(n).
- **Update:** walk from root to a leaf, recompute ancestors. Depth = O(log n).
- **Query:** at each level, at most 2 "partial overlap" nodes recurse further. Total nodes visited = O(log n).

---

## 9. Common pitfalls

1. **Array size 2n instead of 4n.** 2n is too small for non-power-of-2 n. Use 4n.
2. **0-indexed vs 1-indexed tree.** Pick one (1-indexed is cleaner with 2v, 2v+1) and stick with it.
3. **Wrong identity for "no overlap."** For sum: 0. For max: INT_MIN. For min: INT_MAX. For GCD: 0. For product: 1.
4. **Forgetting to recompute the parent after update.** Each return back up the recursion must do `tree[v] = combine(children)`.
5. **Off-by-one on the range [lo, hi].** This template uses INCLUSIVE bounds [lo, hi].
6. **Recursing on disjoint nodes.** The query's first check `qr < lo || ql > hi` prunes them early.

---

## 10. The shape — segment tree template

The pattern: **any ASSOCIATIVE binary operation can power a segment tree.**

| Operation | Identity | Use case |
|---|---|---|
| **Sum** | 0 | range-sum queries |
| Min | +∞ | RMQ |
| Max | -∞ | range-max |
| GCD | 0 | range-gcd |
| Bitwise OR/AND | 0 / ~0 | range-bitwise |
| Custom monoid | identity | structured queries |

**Pattern to internalize:**

> "Mutable array + range queries → segment tree. 4n array, recursive build/update/query, O(log n) per op. Identity depends on the operation."

---

> **Self-check — the question to ask next time.**
>
> When updates AND range queries both happen:
>
> > **"Segment tree. 4n storage. Build O(n), each op O(log n). Pick the correct identity (0 for sum, ±∞ for min/max, 1 for product)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Range_Sum_Query_Mutable.md`](../Range_Sum_Query_Mutable.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Range_Sum_Query_Immutable.md`](./Range_Sum_Query_Immutable.md).
  - Coming next: [`Range_Maximum_Query.md`](./Range_Maximum_Query.md), [`Segment_Tree_Range_Maximum_Query_Node_Update.md`](./Segment_Tree_Range_Maximum_Query_Node_Update.md).
