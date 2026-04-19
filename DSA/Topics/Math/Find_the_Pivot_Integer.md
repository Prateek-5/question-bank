# Find the Pivot Integer

## Problem Link
https://leetcode.com/problems/find-the-pivot-integer/

## Topic
Math

## Core Concept
Prefix-sum equation: sum(1..x) = sum(x..n).

## Intuition
Both sides share x once. We need x(x+1)/2 = (n(n+1) - x(x-1))/2. Solving gives x = sqrt(n(n+1)/2). Check if the square root is an integer.

## Detailed Explanation
Compute S = n*(n+1)/2. We need x² = S, so check if round(sqrt(S))² == S. If yes return that x, else -1.

## Dry Run
n=8. S=36. sqrt(36)=6 → return 6. Verify: 1+...+6=21, 6+7+8=21. ✓

## Approach
Closed-form derivation; O(1) with a single sqrt check.

## Time and Space Complexity
O(1).

## C++ Implementation
```cpp
#include <cmath>
int pivotInteger(int n) {
    int S = n * (n + 1) / 2;
    int x = (int)sqrt((double)S);
    return x * x == S ? x : -1;
}
```

## Follow-up Questions
- Weighted pivot where elements are arbitrary.
- Pivot in a generic array — use prefix sums.
- Multiple pivots counting problem.
