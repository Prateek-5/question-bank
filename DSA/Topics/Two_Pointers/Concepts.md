# Two Pointers — Concepts

## Core Theory
Two-pointer techniques exploit ordering or monotonic counts. Pointers usually move in the same direction (sliding window) or toward each other (opposite ends).

## Common Patterns
- **Opposite-end pointers** on sorted arrays (two-sum, container).
- **Same-direction pointers** for subarray sums, distinct counts.
- **Fast/slow pointers** for linked-list cycle detection and middle finding.
- **Three-pointer partitioning** (Dutch flag).

## When to Use
Any problem where constraints advance pointers monotonically without backtracking — often converts an O(n²) scan to O(n).

## Template
```cpp
int l = 0, r = n - 1;
while (l < r) { int s = a[l] + a[r]; if (s == t) ...; else if (s < t) l++; else r--; }
```

## Common Mistakes
- Moving the wrong pointer when both sides are equal.
- Missing duplicates handling on sorted arrays.
- Using two pointers on unsorted data without preprocessing.
