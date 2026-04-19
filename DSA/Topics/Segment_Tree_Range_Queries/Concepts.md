# Segment Tree / Range Queries — Concepts

## Core Theory
Segment trees support range queries and updates in O(log n). They decompose an array into O(n) nodes, each covering a sub-range. Lazy propagation defers range updates to descendants only when needed, preserving O(log n) per operation.

## Common Patterns
- **Point update, range query** (sum / min / max).
- **Range update, range query** via lazy propagation.
- **Persistent segment trees** for versioned queries.
- **Binary search on segment tree** (first index ≥ x in range).

## When to Use
When you need both frequent updates *and* range queries on the same array. For static arrays, use sparse tables or prefix sums.

## Template
```cpp
// Skeleton for a segment tree
void build(int v, int l, int r) { /* ... */ }
void update(int v, int l, int r, int i, int val) { /* ... */ }
int query(int v, int l, int r, int ql, int qr) { /* ... */ }
```

## Common Mistakes
- Off-by-one in [l, r] vs [l, r) conventions.
- Forgetting to push lazy before descending.
- Sizing tree too small — 4·n is a safe upper bound.
