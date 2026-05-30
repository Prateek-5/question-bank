# Segment Tree — Range Maximum Query with Node Update — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Segment_Tree_Range_Maximum_Query_Node_Update.md`](../Segment_Tree_Range_Maximum_Query_Node_Update.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://www.geeksforgeeks.org/dsa/segment-tree-set-2-range-maximum-query-node-update/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/dsa/segment-tree-set-2-range-maximum-query-node-update/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: same segment-tree template as RSQ-Mutable, but with `max` instead of `+` and `INT_MIN` as the identity. Sparse tables fail when updates exist; segment trees give O(log n) for both.**

**Map of this file (8 sections):**

1. Read the problem
2. Why sparse table fails here
3. Segment tree with `max`
4. Identity: INT_MIN
5. Code
6. Trace it
7. Common pitfalls
8. The shape — segment tree variants

---

## 1. Read the problem

Array `arr` with two operations:
1. `rmq(l, r)`: max of `arr[l..r]`.
2. `update(i, x)`: set `arr[i] = x`.

Both operations need O(log n).

---

## 2. Why sparse table fails here

Sparse table is O(1) PER QUERY but requires FULL REBUILD on update — O(n log n). For frequent updates, this is unusable.

Segment tree: O(log n) for BOTH ops. Right tool for mutable arrays.

---

## 3. Segment tree with `max`

Same SHAPE as the sum segment tree, with two changes:
- Combine = `max` instead of `+`.
- Identity (for "no overlap" branch) = `INT_MIN` instead of 0.

```
build(v, lo, hi):
    if lo == hi: tree[v] = arr[lo]; return
    mid = (lo + hi) / 2
    build(2v, lo, mid); build(2v+1, mid+1, hi)
    tree[v] = max(tree[2v], tree[2v+1])

update(v, lo, hi, i, x):
    if lo == hi: tree[v] = x; return
    ...
    tree[v] = max(tree[2v], tree[2v+1])

query(v, lo, hi, ql, qr):
    if qr < lo or ql > hi: return INT_MIN
    if ql <= lo and hi <= qr: return tree[v]
    ...
    return max(query left, query right)
```

---

## 4. Identity: INT_MIN

> **Mini-refresher: identity = value that doesn't change the combine.**
>
> For sum, identity is 0: x + 0 = x.
> For max, identity is -∞ (INT_MIN): max(x, -∞) = x.
> For min, +∞.
> For GCD, 0: gcd(x, 0) = x.
> For product, 1.
>
> Use the right identity when a query branch contributes nothing.

---

## 5. Code

**C++:**

```cpp
class SegTree {
    vector<int> tree;
    int n;
    void build(vector<int>& arr, int v, int lo, int hi) {
        if (lo == hi) { tree[v] = arr[lo]; return; }
        int mid = lo + (hi - lo) / 2;
        build(arr, 2*v, lo, mid);
        build(arr, 2*v+1, mid+1, hi);
        tree[v] = max(tree[2*v], tree[2*v+1]);
    }
    int queryH(int v, int lo, int hi, int l, int r) {
        if (r < lo || hi < l) return INT_MIN;
        if (l <= lo && hi <= r) return tree[v];
        int mid = lo + (hi - lo) / 2;
        return max(queryH(2*v, lo, mid, l, r),
                   queryH(2*v+1, mid+1, hi, l, r));
    }
    void updateH(int v, int lo, int hi, int i, int x) {
        if (lo == hi) { tree[v] = x; return; }
        int mid = lo + (hi - lo) / 2;
        if (i <= mid) updateH(2*v, lo, mid, i, x);
        else updateH(2*v+1, mid+1, hi, i, x);
        tree[v] = max(tree[2*v], tree[2*v+1]);
    }
public:
    SegTree(vector<int>& arr) : n(arr.size()) {
        tree.assign(4 * n, INT_MIN);
        build(arr, 1, 0, n - 1);
    }
    int rangeMax(int l, int r) { return queryH(1, 0, n - 1, l, r); }
    void pointUpdate(int i, int x) { updateH(1, 0, n - 1, i, x); }
};
```

Complexity: build O(n), each op **O(log n)**, space O(n).

---

## 6. Trace it

`arr = [1, 3, 5, 7, 9, 11]`. n=6.

Tree (max at each internal node):
```
[0..5] max=11
├── [0..2] max=5
│   ├── [0..1] max=3
│   │   ├── [0]=1
│   │   └── [1]=3
│   └── [2]=5
└── [3..5] max=11
    ├── [3..4] max=9
    │   ├── [3]=7
    │   └── [4]=9
    └── [5]=11
```

**rangeMax(1, 4):**
- [0..5]: partial. Recurse.
- [0..2]: partial with [1..4]. Recurse.
  - [0..1]: partial. → [0]: disjoint → INT_MIN. [1]: full → 3. Return 3.
  - [2]: full → 5.
  - Return max(3, 5) = 5.
- [3..5]: partial.
  - [3..4]: full → 9.
  - [5]: disjoint → INT_MIN.
  - Return 9.
- Root → max(5, 9) = **9**.  ✓

**pointUpdate(3, 20):** walk to leaf [3], set 20. Recompute [3..4]=max(20,9)=20, [3..5]=max(20,11)=20, root=max(5,20)=20.

---

## 7. Common pitfalls

1. **Using 0 as identity for max.** Wrong if array has negative values — max would falsely return 0. Use INT_MIN.
2. **Forgetting to recompute the parent after update.** Each recursive return must do `tree[v] = max(children)`.
3. **Confusing range max with min.** Just swap. The structure is identical.
4. **Wrong array size.** Use 4n for safety.
5. **Iterative segment tree with wrong identity.** The iterative version still needs careful identity handling.

---

## 8. The shape — segment tree variants

The pattern: **same template, swap (combine, identity) for different queries.**

| Query type | Combine | Identity |
|---|---|---|
| Sum | + | 0 |
| **Max** | max | INT_MIN |
| Min | min | INT_MAX |
| GCD | gcd | 0 |
| Product | × | 1 |
| Bitwise AND | & | ~0 (all ones) |
| Bitwise OR | \| | 0 |
| Count of elements | + 1 each | 0 |

**Pattern to internalize:**

> "Segment tree is GENERIC over any associative op (monoid). Plug in the combine function + identity. Build/update/query templates stay the same."

---

> **Self-check — the question to ask next time.**
>
> When updates AND range max/min/gcd queries both happen:
>
> > **"Segment tree. Combine = max/min/gcd. Identity = ±∞ or 0 (per op). Each op O(log n)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Segment_Tree_Range_Maximum_Query_Node_Update.md`](../Segment_Tree_Range_Maximum_Query_Node_Update.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Range_Sum_Query_Mutable.md`](./Range_Sum_Query_Mutable.md), [`Range_Maximum_Query.md`](./Range_Maximum_Query.md).
  - Coming next: [`Flipping_Sign_Problem_Lazy_Propagation.md`](./Flipping_Sign_Problem_Lazy_Propagation.md), [`Flipping_Sign_Problem_Lazy_Propagation_Segment_Tree.md`](./Flipping_Sign_Problem_Lazy_Propagation_Segment_Tree.md).
