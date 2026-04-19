# Searching / Binary Search — Concepts

## Core Theory
Binary search works whenever the search space has a monotonic property — either the input is sorted, or some predicate is monotonic over the index/value. It halves the space per step, yielding O(log n).

## Common Patterns
- **Sorted-array search** (classic, upper/lower bound).
- **Binary search on answer:** search a numeric range with a feasibility function.
- **Staircase search in 2D**.
- **Rotated array search** with sorted-half detection.

## When to Use
Whenever monotonicity is present or a candidate answer can be checked faster than enumerating all answers.

## Template
```cpp
int lo = 0, hi = n - 1;
while (lo < hi) { int m = (lo + hi) / 2; if (ok(m)) hi = m; else lo = m + 1; }
```

## Common Mistakes
- Using `(lo + hi) / 2` with overflow risk on large ints — use `lo + (hi - lo) / 2`.
- Wrong boundary update causing infinite loop.
- Misidentifying the monotonic predicate.
