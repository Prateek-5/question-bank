# 1-D & 2-D Arrays — Concepts

## Core Theory
Arrays are random-access containers. Mastery includes prefix sums, difference arrays, in-place transformations (rotation, spiral), and index arithmetic for 1D↔2D mapping.

## Common Patterns
- **Prefix sums (1D, 2D)** for range queries in O(1).
- **Sliding window** for contiguous subarray sums / constraints.
- **In-place matrix ops** (transpose, rotate, zero-out).
- **Index mapping**: flat idx ↔ (row, col).

## When to Use
Whenever constant-time random access is needed, or data naturally has spatial structure. Prefer hashmaps when keys are sparse.

## Template
```cpp
// 2D prefix sum
for (int i = 0; i < n; ++i) for (int j = 0; j < m; ++j)
    P[i+1][j+1] = M[i][j] + P[i][j+1] + P[i+1][j] - P[i][j];
```

## Common Mistakes
- Off-by-one in prefix indices (use P[0..n] of length n+1).
- Row-major vs column-major misuse.
- Forgetting to copy when passing arrays that may mutate.
