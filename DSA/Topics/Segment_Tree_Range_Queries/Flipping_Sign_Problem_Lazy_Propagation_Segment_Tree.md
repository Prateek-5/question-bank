# Flipping Sign Problem (Lazy Propagation Segment Tree)

**Problem Link:**
https://www.geeksforgeeks.org/dsa/flipping-sign-problem-lazy-propagation-segment-tree/

**Topic:**
Segment Tree / Range Queries

----------------------------------------

## Step 1: The Operations

Given an array of integers, support two operations efficiently:
1. **Flip range [l, r]**: multiply every element in nums[l..r] by -1.
2. **Sum query on [l, r]**: return `nums[l] + nums[l+1] + ... + nums[r]`.

Both operations must be fast (O(log n) each). Naive O(n) per op is too slow for many queries.

Example: nums = [1, -2, 3, 4, -5].
- sum(0, 4) = 1 - 2 + 3 + 4 - 5 = 1.
- flip(1, 3): nums becomes [1, 2, -3, -4, -5].
- sum(0, 4) = 1 + 2 - 3 - 4 - 5 = -9.

----------------------------------------

## Step 2: Why Basic Segment Tree Isn't Enough

A standard segment tree with node = sum of segment supports sum queries in O(log n) but **not range updates** in better than O(n).

If we naively flipped every element in [l, r], that's O(n) per update. With many updates, too slow.

**Lazy propagation** solves this: postpone updates and push them only when needed.

----------------------------------------

## Step 3: Lazy Propagation Concept

Each segment tree node stores:
- `sum`: sum of the segment it covers.
- `lazy`: a "pending flip" flag. If lazy = 1, the segment's children have not yet reflected the flip — but the node itself has.

When we visit a node:
- If lazy = 1, its sum is already post-flip (we applied the flip to `sum` when we set the lazy). But children's sums are stale.
- Before recursing into children, **push** the lazy flag down: apply the flip to children's sums, toggle their lazy flags, and clear the parent's lazy.

This way, we only propagate lazy when actually needed — cost is amortized to O(log n) per operation.

----------------------------------------

## Step 4: How a Flip Propagates

When we apply a flip to a node:
- `sum = -sum` (because every element flipped its sign; the sum flips too).
- `lazy ^= 1` (toggle: two flips cancel).

If we flip the same segment twice, lazy goes 1 → 0, and sum goes -sum → sum. Back to original.

----------------------------------------

## Step 5: Algorithm

```
def build(node, lo, hi):
    lazy[node] = 0
    if lo == hi:
        sum[node] = arr[lo]
    else:
        mid = (lo + hi) // 2
        build(left_child(node), lo, mid)
        build(right_child(node), mid+1, hi)
        sum[node] = sum[left] + sum[right]

def push_down(node):
    if lazy[node]:
        apply_flip(left_child(node))
        apply_flip(right_child(node))
        lazy[node] = 0

def apply_flip(node):
    sum[node] = -sum[node]
    lazy[node] ^= 1

def update(node, lo, hi, l, r):
    if r < lo or hi < l: return      # disjoint
    if l <= lo and hi <= r:
        apply_flip(node)
        return
    push_down(node)
    mid = (lo + hi) // 2
    update(left, lo, mid, l, r)
    update(right, mid+1, hi, l, r)
    sum[node] = sum[left] + sum[right]

def query(node, lo, hi, l, r):
    if r < lo or hi < l: return 0    # disjoint
    if l <= lo and hi <= r: return sum[node]
    push_down(node)
    mid = (lo + hi) // 2
    return query(left, lo, mid, l, r) + query(right, mid+1, hi, l, r)
```

`push_down` applies the pending lazy to children on demand, then clears the parent's lazy.

Both update and query are O(log n).

----------------------------------------

## Step 6: Trace on a Small Case

Suppose nums = [1, -2, 3]. Build segment tree (simplified, with sum at each node).

Initial sums:
- Root (0..2): sum = 2.
- Left (0..1): sum = -1.
  - (0..0): sum = 1.
  - (1..1): sum = -2.
- Right (2..2): sum = 3.

**flip(0, 1)**:
- Root (0..2), range [0, 2] vs [0, 1]: partial overlap. push_down (lazy = 0, nothing). Recurse.
  - Left (0..1) fully within [0, 1]. Apply flip: sum = 1 (was -1), lazy = 1. Return.
  - Right (2..2) disjoint. Return.
- sum[root] = sum[left] + sum[right] = 1 + 3 = 4.

State: Root sum = 4, lazy=0. Left sum = 1, lazy=1. Left children sums haven't been updated but lazy=1 signals them.

**query(0, 2)**:
- Root fully contains [0, 2]. Return sum[root] = 4.

Check by hand: after flipping 0..1, nums becomes [-1, 2, 3]. Sum = 4. ✓

----------------------------------------

## Step 7: Why Lazy Doesn't Break Sum Invariants

When we flip a range, the sum of that range becomes the negation. If the range is fully covered by a segment tree node, the node's sum can be updated in O(1) — we don't need to visit leaves.

The lazy flag records "I owe my children a flip." When we later need to descend into children, we push the flip down first, keeping sums consistent.

Without lazy: every range update would walk to the leaves — O(n). With lazy: only walks as deep as needed — O(log n).

----------------------------------------

## Step 8: Name It

**Segment tree with lazy propagation.** A universal pattern for range-update + range-query problems.

Variants:
- **Range assign + range sum query** (lazy = "new value to assign").
- **Range add + range sum query** (lazy = "amount to add").
- **Range multiply + range sum query** (lazy = "multiplier"; more complex).
- **Range flip sign + range sum query** (this problem — lazy = flip bit).

The framework is always: maintain lazy tag, apply_op, push_down. Each operation must be composable (applying two lazy ops gives another valid lazy op).

----------------------------------------

## Step 9: Complexity

- Build: **O(n)**.
- Update: **O(log n)** amortized.
- Query: **O(log n)** amortized.
- Space: **O(n)**.

The `O(log n)` per op is the critical improvement over naive O(n).

----------------------------------------

## Step 10: C++ Implementation

```cpp
class SegTree {
    vector<long long> sum;
    vector<int> lazy;
    int n;

    void build(vector<int>& arr, int v, int lo, int hi) {
        if (lo == hi) { sum[v] = arr[lo]; return; }
        int mid = (lo + hi) / 2;
        build(arr, 2*v, lo, mid);
        build(arr, 2*v+1, mid+1, hi);
        sum[v] = sum[2*v] + sum[2*v+1];
    }

    void applyFlip(int v) {
        sum[v] = -sum[v];
        lazy[v] ^= 1;
    }

    void push(int v) {
        if (lazy[v]) {
            applyFlip(2*v);
            applyFlip(2*v+1);
            lazy[v] = 0;
        }
    }

    void update(int v, int lo, int hi, int l, int r) {
        if (r < lo || hi < l) return;
        if (l <= lo && hi <= r) { applyFlip(v); return; }
        push(v);
        int mid = (lo + hi) / 2;
        update(2*v, lo, mid, l, r);
        update(2*v+1, mid+1, hi, l, r);
        sum[v] = sum[2*v] + sum[2*v+1];
    }

    long long query(int v, int lo, int hi, int l, int r) {
        if (r < lo || hi < l) return 0;
        if (l <= lo && hi <= r) return sum[v];
        push(v);
        int mid = (lo + hi) / 2;
        return query(2*v, lo, mid, l, r) + query(2*v+1, mid+1, hi, l, r);
    }

public:
    SegTree(vector<int>& arr) : n(arr.size()) {
        sum.assign(4 * n, 0);
        lazy.assign(4 * n, 0);
        build(arr, 1, 0, n - 1);
    }

    void flipRange(int l, int r) { update(1, 0, n - 1, l, r); }
    long long sumRange(int l, int r) { return query(1, 0, n - 1, l, r); }
};
```

The `push` + `applyFlip` combo is the heart of lazy propagation.

----------------------------------------

## Step 11: Follow-up Questions

- **Range assign (set all to x) + sum query.** Lazy stores the assigned value; apply sets sum = length · x.
- **Range add + sum query.** Lazy stores the delta; apply adds length · delta to sum.
- **Multiple overlapping update types.** Need to carefully define composition (e.g., "apply add then assign" vs "assign then add" — canonicalize).
- **Iterative segment tree with lazy.** Possible but significantly trickier.
- **Why `sum[v] = -sum[v]` for flip?** Because every element flipped sign, the sum also flips. Purely numerical.
- **Why 4n space for segment tree?** Safe upper bound; actual usage is smaller but easier to over-allocate.
