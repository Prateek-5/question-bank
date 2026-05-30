# Segment Tree — Range Maximum Query with Node Update

**Problem Link:**
<a href="https://www.geeksforgeeks.org/dsa/segment-tree-set-2-range-maximum-query-node-update/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/dsa/segment-tree-set-2-range-maximum-query-node-update/</a>

**Topic:**
Segment Tree / Range Queries

----------------------------------------

## Step 1: The Operations We Need

Given an array `arr` of length n, support two operations efficiently:
1. **Range maximum query**: `rmq(l, r)` returns `max(arr[l], arr[l+1], ..., arr[r])`.
2. **Point update**: `update(i, x)` sets `arr[i] = x`.

Why do we need a data structure? Because:
- Query in O(n) per call is too slow if there are many queries.
- Storing all pairwise maxes upfront is O(n²) space.

We want **O(log n) per operation** — and a **segment tree** delivers that.

----------------------------------------

## Step 2: Intuition — Hierarchical Summaries

Imagine splitting the array in half. Each half has its own max. To query the max over the whole array, take `max(left_half_max, right_half_max)`.

Recursively split each half. Each sub-range has a precomputed max. A balanced binary tree of depth O(log n) lets us answer any range query by **combining** ~O(log n) sub-range maxes.

That's the segment tree: each node stores the max of a contiguous segment of the array; children cover the left and right halves.

----------------------------------------

## Step 3: Tree Structure

Represent the tree as an array `tree[]` of size 4n (safe upper bound):
- `tree[1]` is the root, covering [0, n-1].
- For node `v` covering [lo, hi]: children are `2v` (covers [lo, mid]) and `2v + 1` (covers [mid+1, hi]), where `mid = (lo + hi) / 2`.
- Leaves correspond to single-element ranges [i, i].

Each node stores the max of its segment.

----------------------------------------

## Step 4: Build in O(n)

Recursively build: if [lo, hi] is a single element (lo == hi), tree[v] = arr[lo]. Otherwise, build children first, then tree[v] = max(tree[2v], tree[2v+1]).

```
def build(v, lo, hi):
    if lo == hi:
        tree[v] = arr[lo]
    else:
        mid = (lo + hi) / 2
        build(2v, lo, mid)
        build(2v+1, mid+1, hi)
        tree[v] = max(tree[2v], tree[2v+1])
```

Each of n leaves is visited once; internal nodes sum to O(n) total. Build is **O(n)**.

----------------------------------------

## Step 5: Query in O(log n)

To query `rmq(l, r)` starting at node v covering [lo, hi]:

```
def query(v, lo, hi, l, r):
    if r < lo or hi < l: return -∞   # disjoint
    if l <= lo and hi <= r: return tree[v]   # fully inside
    mid = (lo + hi) / 2
    return max(query(2v, lo, mid, l, r),
               query(2v+1, mid+1, hi, l, r))
```

Three cases: disjoint (no contribution), fully contained (use stored max), partial overlap (recurse).

The partial-overlap case is where the recursion lives. At each level, at most 2 nodes are "partially overlapping" with [l, r] — so the recursion visits O(log n) nodes total.

----------------------------------------

## Step 6: Update in O(log n)

To update arr[i] = x:

```
def update(v, lo, hi, i, x):
    if lo == hi:
        tree[v] = x
        return
    mid = (lo + hi) / 2
    if i <= mid: update(2v, lo, mid, i, x)
    else update(2v+1, mid+1, hi, i, x)
    tree[v] = max(tree[2v], tree[2v+1])
```

Walk down to the leaf corresponding to index i. Update. On the way back up, recompute the max at each ancestor from its children.

Depth is O(log n) → update is O(log n).

----------------------------------------

## Step 7: Trace — Small Example

arr = [1, 3, 5, 7, 9, 11]. n = 6.

Build: tree will have:
- Root [0, 5] → max(arr) = 11.
- Left child [0, 2] → max(1, 3, 5) = 5.
- Right child [3, 5] → max(7, 9, 11) = 11.
- Left-left [0, 1] → max(1, 3) = 3.
- Etc.

Query rmq(1, 4) (arr[1..4] = [3, 5, 7, 9]):
- Start at root [0, 5]. Partial overlap with [1, 4]. Recurse.
- Left [0, 2]: partial overlap with [1, 4] (intersection [1, 2]). Recurse.
  - Left-left [0, 1]: partial with [1, 4] (intersection [1, 1]). Recurse.
    - [0, 0]: disjoint with [1, 4]. Return -∞.
    - [1, 1]: fully inside. Return 3.
  - Right-right [2, 2]: fully inside. Return 5.
  - [0, 2] returns max(3, 5) = 5.
- Right [3, 5]: partial with [1, 4] (intersection [3, 4]). Recurse.
  - Right-left [3, 4]: fully inside. Return max(7, 9) = 9.
  - Right-right [5, 5]: disjoint. Return -∞.
  - Right returns 9.
- Root returns max(5, 9) = **9**. ✓

Update arr[3] = 20:
- Walk root → right [3, 5] → right-left [3, 4] → leaf [3, 3]. Set tree[leaf] = 20.
- On return, leaf [3, 3] = 20. [3, 4] = max(20, 9) = 20. [3, 5] = max(20, 11) = 20. Root = max(5, 20) = 20.

New rmq(1, 4) would return 20.

----------------------------------------

## Step 8: Why 4n Size for the Tree Array?

For n not a power of 2, the segment tree still fits in 4n nodes (overhead due to padding). Safe conservative bound. For optimization, use 2·2^⌈log2 n⌉ — the exact minimal.

----------------------------------------

## Step 9: Name It

**Segment tree** — a universal range-query data structure. Supports any **associative** operation: sum, min, max, gcd, bitwise OR/AND, custom monoid.

Variants:
- **Range update, point query**: use "lazy propagation" on a difference-style structure.
- **Range update, range query**: lazy propagation.
- **Persistent segment tree**: keep history of updates.
- **Merge sort tree / wavelet tree**: for k-th smallest in a range.

For this problem (point update, range max query), the basic version suffices.

----------------------------------------

## Step 10: Complexity

- Build: **O(n)**.
- Query: **O(log n)**.
- Update: **O(log n)**.
- Space: **O(n)** (4n array).

----------------------------------------

## Step 11: C++ Implementation

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

    int query(int v, int lo, int hi, int l, int r) {
        if (r < lo || hi < l) return INT_MIN;
        if (l <= lo && hi <= r) return tree[v];
        int mid = lo + (hi - lo) / 2;
        return max(query(2*v, lo, mid, l, r),
                   query(2*v+1, mid+1, hi, l, r));
    }

    void update(int v, int lo, int hi, int i, int x) {
        if (lo == hi) { tree[v] = x; return; }
        int mid = lo + (hi - lo) / 2;
        if (i <= mid) update(2*v, lo, mid, i, x);
        else update(2*v+1, mid+1, hi, i, x);
        tree[v] = max(tree[2*v], tree[2*v+1]);
    }

public:
    SegTree(vector<int>& arr) : n(arr.size()) {
        tree.assign(4 * n, INT_MIN);
        build(arr, 1, 0, n - 1);
    }

    int rangeMax(int l, int r) {
        return query(1, 0, n - 1, l, r);
    }

    void pointUpdate(int i, int x) {
        update(1, 0, n - 1, i, x);
    }
};
```

----------------------------------------

## Step 12: Follow-up Questions

- **Range minimum instead.** Swap `max` for `min`, and disjoint sentinel to +INF.
- **Range sum.** Swap `max` for `+`, and disjoint sentinel to 0.
- **Range update (e.g., add x to arr[l..r]).** Requires lazy propagation.
- **k-th largest in a range.** Merge sort tree or wavelet tree.
- **Why 4n size?** Worst case for non-power-of-2 n, the tree has up to 2·2^⌈log2 n⌉ ≤ 4n nodes.
- **Iterative segment tree.** A more compact implementation exists; same complexities, faster in practice but trickier to get right.
