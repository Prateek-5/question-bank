# Arrays & Matrices — Concepts

## Core Theory
Array and matrix problems emphasize traversal patterns (row/col scans, diagonals, spirals), counting contributions, and careful boundary handling.

## Common Patterns
- **Contribution counting:** each element's weight × number of subarrays it belongs to.
- **Two-pointer trapping** (rainwater).
- **Boundary traversals** (spiral, surrounded regions).
- **Per-row max/min tracking** (lucky numbers).

## When to Use
When input structure is naturally 2D or when you want O(1) random access.

## Template
```cpp
int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
for (int k = 0; k < 4; ++k) { int nr = r + dr[k], nc = c + dc[k]; /* bounds */ }
```

## Common Mistakes
- Off-by-one in boundary checks.
- Forgetting to restart state between test cases.
- Using nested loops when a pattern-based closed form exists.
