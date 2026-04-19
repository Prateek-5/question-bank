# Unique Paths

## Problem Link
https://leetcode.com/problems/unique-paths/

## Topic
Dynamic Programming DP

## Core Concept
Combinations C(m+n-2, m-1) or DP.

## Intuition
Every path consists of (m-1) downs and (n-1) rights — total (m+n-2) moves chosen from either.

## Detailed Explanation
Compute binomial coefficient iteratively to avoid overflow.

## Dry Run
m=3,n=7 → C(8,2)=28.

## Approach
Iterative nCr.

## Time and Space Complexity
Time: O(min(m,n)). Space: O(1).

## C++ Implementation
```cpp
int uniquePaths(int m, int n) {
    long long r = 1;
    for (int i = 1; i < m; ++i) r = r * (n - 1 + i) / i;
    return (int)r;
}
```

## Follow-up Questions
- With obstacles (Unique Paths II).
- Paths with k moves.
- Unique paths in 3D.
