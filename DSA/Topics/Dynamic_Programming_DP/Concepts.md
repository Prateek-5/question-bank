# Dynamic Programming (DP) — Concepts

## Core Theory
DP solves problems by recurrence over overlapping subproblems with optimal substructure. Transforms exponential recursion into polynomial tables via memoization (top-down) or tabulation (bottom-up).

## Common Patterns
- **1D DP** over indices (climbing stairs, LIS, Kadane).
- **2D DP** over (i, j) (LCS, edit distance, interleaving).
- **Knapsack** (0/1, unbounded, bounded).
- **Interval DP** (matrix chain, palindrome partitioning).
- **Digit DP** for count-over-range problems.

## When to Use
When a brute force solution exhibits overlapping subproblems and the answer can be expressed recursively in terms of smaller inputs.

## Template
```cpp
// Top-down
int solve(int i, vector<int>& memo) {
    if (baseCase) return ...;
    if (memo[i] != -1) return memo[i];
    return memo[i] = combine(solve(i-1, memo), solve(i-2, memo));
}
```

## Common Mistakes
- Missing base cases or off-by-one at boundaries.
- Wrong state (too few or too many dimensions).
- Iteration order in bottom-up must respect dependencies.
- Forgetting to initialize memo table to a sentinel.
