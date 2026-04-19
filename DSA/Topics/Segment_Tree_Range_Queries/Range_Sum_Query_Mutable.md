# Range Sum Query — Mutable

**Problem Link:**
https://leetcode.com/problems/range-sum-query-mutable/

**Topic:**
Segment Tree / Range Queries

----------------------------------------

## Step 1: What's the Problem?

Given an integer array, support two operations many times:
- `update(i, v)`: set `nums[i] = v`.
- `sumRange(l, r)`: return sum of `nums[l..r]` (inclusive).

Naively, each operation is O(n). For many operations, that's O(n²), which doesn't scale.

We want both operations in **O(log n)**.

----------------------------------------

## Step 2: Why Prefix Sums Don't Work Here

Prefix sums give O(1) range sum queries — great! But updating a single element requires re-building the prefix array, which is O(n). If updates are frequent, prefix sums lose.

So we need a data structure that:
- Answers range sums fast.
- Supports point updates fast.

Two standard options: **Segment Tree** and **Binary Indexed Tree (Fenwick)**. Both give O(log n) for both operations.

I'll walk through **Segment Tree** — the more general tool.

----------------------------------------

## Step 3: Segment Tree Intuition

Partition the array into halves recursively. Each node of the tree represents a **range** of the array:
- Root: the entire array.
- Root's left child: left half.
- Root's right child: right half.
- Leaves: single elements.

Each internal node stores the **sum** of its range.

```
       [0, n-1]
      /        \
  [0, mid]   [mid+1, n-1]
   /    \     /       \
  ...   ...  ...     ...
                        leaves: single-element ranges
```

For a range sum query `[l, r]`:
- If the current node's range is entirely inside [l, r]: return the node's sum (single O(1) read).
- If entirely outside: return 0.
- Else: recurse on both children, sum results.

For a point update at index i:
- Walk down to the leaf covering i, update it.
- On the way back up, recompute each ancestor's sum.

Both operations touch O(log n) nodes. Done.

----------------------------------------

## Step 4: Array-Based Segment Tree

Store the tree in an array `tree[]` of size ~4n (safe upper bound). Node at index v has:
- Left child at index `2*v`.
- Right child at index `2*v + 1`.

Root at index 1 (makes indexing arithmetic clean). Leaves are at some depth, depending on n.

Build:
```
build(v, lo, hi, nums):
    if lo == hi:
        tree[v] = nums[lo]
        return
    mid = (lo + hi) / 2
    build(2*v, lo, mid, nums)
    build(2*v+1, mid+1, hi, nums)
    tree[v] = tree[2*v] + tree[2*v+1]
```

Update:
```
update(v, lo, hi, i, val):
    if lo == hi:
        tree[v] = val
        return
    mid = (lo + hi) / 2
    if i <= mid: update(2*v, lo, mid, i, val)
    else: update(2*v+1, mid+1, hi, i, val)
    tree[v] = tree[2*v] + tree[2*v+1]
```

Query:
```
query(v, lo, hi, ql, qr):
    if qr < lo or ql > hi: return 0       # no overlap
    if ql <= lo and hi <= qr: return tree[v]  # full overlap
    mid = (lo + hi) / 2
    return query(2*v, lo, mid, ql, qr) + query(2*v+1, mid+1, hi, ql, qr)
```

All three are recursive and O(log n).

----------------------------------------

## Step 5: Why O(log n)?

For **update**: we walk from root to a single leaf. Height = O(log n). On the way up, each node does O(1) work.

For **query**: at each level, the range `[l, r]` can split into at most 2 fully-covered subranges and some partial overlap. The recursion explores at most O(log n) nodes.

More intuitively: [l, r] can be broken into O(log n) "canonical" subranges that correspond to complete segment-tree nodes. Summing these is O(log n).

----------------------------------------

## Step 6: Trace a Small Example

`nums = [1, 3, 5, 7, 9, 11]`. n = 6.

Build the tree. I'll sketch the conceptual structure:

```
[0..5] sum = 36
├── [0..2] sum = 9
│   ├── [0..1] sum = 4
│   │   ├── [0] = 1
│   │   └── [1] = 3
│   └── [2] = 5
└── [3..5] sum = 27
    ├── [3..4] sum = 16
    │   ├── [3] = 7
    │   └── [4] = 9
    └── [5] = 11
```

`sumRange(2, 4)` — want sum of nums[2..4] = 5 + 7 + 9 = 21.

Query traversal:
- Root [0..5]: partial overlap with [2..4]. Recurse both.
- [0..2]: partial with [2..4]. Recurse.
  - [0..1]: no overlap with [2..4]. Return 0.
  - [2]: full overlap. Return 5.
  - Total: 5.
- [3..5]: partial with [2..4]. Recurse.
  - [3..4]: full overlap. Return 16.
  - [5]: no overlap. Return 0.
  - Total: 16.
- Root returns 5 + 16 = 21. ✓

`update(3, 2)` — change nums[3] from 7 to 2.

Walk:
- Root → [3..5] → [3..4] → [3]. Leaf [3]: tree[...] = 2.
- Recompute [3..4]: 2 + 9 = 11.
- Recompute [3..5]: 11 + 11 = 22.
- Recompute root [0..5]: 9 + 22 = 31.

After update, sumRange queries use the new values.

----------------------------------------

## Step 7: Implementation Choices

- **Segment tree size:** `4 * n` is safe. Tighter bounds exist but not worth the complexity.
- **1-indexed tree:** conventions in competitive programming. Makes 2*v, 2*v+1 clean.
- **Class-based:** wrap build, update, query in a class for cleaner client code.

----------------------------------------

## Step 8: Name It

**Segment tree with point updates and range sum queries** — the classical "range-tree" structure. Variants:
- Range min/max query (replace sum with min/max).
- Range update, point query (with lazy propagation or difference technique).
- Range update, range query (full lazy propagation).

**Binary Indexed Tree (BIT)** — simpler, smaller constant factors, but less flexible. Works for sum-like operations. Good to know as an alternative.

----------------------------------------

## Step 9: Complexity

Build: **O(n)**.
Update: **O(log n)**.
Query: **O(log n)**.
Space: **O(n)** (with the 4n upper bound, O(n)).

----------------------------------------

## Step 10: C++ Implementation

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

    void updateHelper(int v, int lo, int hi, int i, int val) {
        if (lo == hi) { tree[v] = val; return; }
        int mid = (lo + hi) / 2;
        if (i <= mid) updateHelper(2*v, lo, mid, i, val);
        else updateHelper(2*v+1, mid+1, hi, i, val);
        tree[v] = tree[2*v] + tree[2*v+1];
    }

    int queryHelper(int v, int lo, int hi, int ql, int qr) {
        if (qr < lo || ql > hi) return 0;
        if (ql <= lo && hi <= qr) return tree[v];
        int mid = (lo + hi) / 2;
        return queryHelper(2*v, lo, mid, ql, qr) + queryHelper(2*v+1, mid+1, hi, ql, qr);
    }

public:
    NumArray(vector<int>& nums) : n(nums.size()), tree(4 * nums.size(), 0) {
        if (n > 0) build(1, 0, n - 1, nums);
    }

    void update(int index, int val) {
        updateHelper(1, 0, n - 1, index, val);
    }

    int sumRange(int left, int right) {
        return queryHelper(1, 0, n - 1, left, right);
    }
};
```

Clean. The private helpers take tree indices; public interface is clean.

----------------------------------------

## Step 11: Follow-up Questions

- **Range min / max instead of sum.** Same structure; replace `tree[2*v] + tree[2*v+1]` with `min` or `max`. Neutral element changes: 0 → INF or -INF.
- **Range update (add k to all in [l, r]) with range query.** Lazy propagation — store pending updates at nodes, push down on descent.
- **2D segment tree.** Tree of trees. O(log² n) per operation.
- **Persistent segment tree.** Keep all historical versions. Useful for offline queries.
- **Binary Indexed Tree (Fenwick).** Simpler alternative for point-update + prefix-sum. O(log n), smaller constant.
- **Why size 4n?** Safe upper bound on total nodes. Tighter bounds (2 × next-power-of-2 of n) work too but are more error-prone.
