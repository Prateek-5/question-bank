# Segment Tree / Range Queries — Concepts Guide

----------------------------------------

## 1. Introduction

Segment trees are the 'Swiss Army knife' of range problems. When you need to answer *range queries* (sum, min, max over a subarray) *and* support *point or range updates*, a plain prefix sum isn't enough — updates would cost O(n). Segment trees give you O(log n) for both.

----------------------------------------

## 2. Real-Life Analogy

Imagine a company org chart where every department reports a rolled-up number (like revenue) to its parent. If the CEO wants the total revenue of the West Coast region, he just reads the West Coast VP's roll-up — O(log n) if the hierarchy is balanced. When one salesperson updates their number, only their chain of managers needs to recompute — again O(log n). That's exactly what a segment tree does with array indices.

----------------------------------------

## 3. Core Idea

A segment tree is a balanced binary tree over array indices. Each node covers a sub-range and stores the aggregated value for that range. Queries and updates walk at most two root-to-leaf paths — O(log n) each. Lazy propagation adds deferred updates: a node can say 'all my descendants have had X applied to them' and push that down only when necessary, keeping range updates in O(log n) too.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Use a segment tree when:

- **You need range queries AND updates on the same array.**
- **The aggregation is associative** (sum, min, max, XOR, gcd).
- **You need O(log n) per operation on a large array.**

For static arrays (no updates), prefer simpler tools: prefix sums for sum, sparse table for idempotent ops (min/max/gcd). For single-type updates with prefix-sum queries, a Fenwick/BIT is simpler.

----------------------------------------

## 5. Types / Variations

- **Range sum + point update.**
- **Range min/max + point update.**
- **Range update + point query** (via difference-array BIT or lazy segtree).
- **Range update + range query** (lazy propagation segtree).
- **Persistent segment tree** (versioned queries).
- **Merge-sort tree / wavelet tree** for harder queries (k-th order statistics, range distinct).

----------------------------------------

## 6. Step-by-Step Working

**Build (recursive):**
1. If l == r, store leaf value.
2. Else recurse on [l, mid] and [mid+1, r], then combine.

**Point update:**
1. Recurse to the leaf corresponding to index i.
2. Update leaf value.
3. On the way back, recombine parents.

**Range query [ql, qr]:**
1. If current [l, r] is disjoint from [ql, qr], return identity.
2. If current [l, r] is fully inside [ql, qr], return stored value.
3. Otherwise, recurse on both children and combine.

**Lazy propagation (range update + range query):**
- Before recursing, push any pending update to children.
- On full-cover updates, apply directly to the node and mark lazy; don't recurse.

----------------------------------------

## 7. Visual Explanation

**Segment tree for [1, 3, 5, 7] with sum aggregation:**

```
          16  (sum of [1,3,5,7])
         /  \
        4    12
       / \   / \
      1   3 5   7
```

**Query sum of [1..2] (values 3 and 5):**
- Root [0..3]: partial overlap → recurse.
- Left [0..1]: partial overlap → recurse. Right child [1..1] fully inside → return 3.
- Right [2..3]: partial overlap → recurse. Left child [2..2] fully inside → return 5.
- Combine: 3 + 5 = 8.

----------------------------------------

## 8. Code Templates (C++)

```cpp
class SegTree {
    int n;
    vector<long long> t;
    void build(int v, int l, int r, vector<int>& a) {
        if (l == r) { t[v] = a[l]; return; }
        int m = (l + r) / 2;
        build(2*v, l, m, a);
        build(2*v+1, m+1, r, a);
        t[v] = t[2*v] + t[2*v+1];
    }
    void upd(int v, int l, int r, int i, int val) {
        if (l == r) { t[v] = val; return; }
        int m = (l + r) / 2;
        if (i <= m) upd(2*v, l, m, i, val);
        else upd(2*v+1, m+1, r, i, val);
        t[v] = t[2*v] + t[2*v+1];
    }
    long long qry(int v, int l, int r, int ql, int qr) {
        if (ql > r || qr < l) return 0;
        if (ql <= l && r <= qr) return t[v];
        int m = (l + r) / 2;
        return qry(2*v, l, m, ql, qr) + qry(2*v+1, m+1, r, ql, qr);
    }
public:
    SegTree(vector<int>& a): n(a.size()) {
        t.assign(4 * n, 0);
        build(1, 0, n - 1, a);
    }
    void update(int i, int v) { upd(1, 0, n - 1, i, v); }
    long long query(int l, int r) { return qry(1, 0, n - 1, l, r); }
};
```

----------------------------------------

## 9. Common Mistakes

- **Allocating too small an array** — 4·n is a safe upper bound for the tree.
- **Off-by-one in [l, r] vs [l, r)** conventions — pick one and stick to it.
- **Forgetting to push lazy before descending.**
- **Not handling 'no overlap' case correctly** in queries (return identity, not 0 for min queries).
- **Recomputing parent without re-combining children** on updates.

----------------------------------------

## 10. Interview Insights

Segment tree questions test whether you can build a non-trivial data structure under time pressure. Interviewers want to see:

1. **Clean recursion structure** — build, update, query.
2. **Correct identity handling** (0 for sum, INT_MAX for min, INT_MIN for max).
3. **Awareness of lazy propagation** for range updates.
4. **Trade-off reasoning** — when BIT or sparse table is sufficient.

If the problem has static queries only, mention sparse table as a simpler alternative — it shows depth.
