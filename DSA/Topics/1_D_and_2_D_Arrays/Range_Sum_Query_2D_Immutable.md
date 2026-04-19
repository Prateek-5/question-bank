# Range Sum Query 2D – Immutable

## Problem Link
https://leetcode.com/problems/range-sum-query-2d-immutable/

## Topic
1 D and 2 D Arrays

## Core Concept
2D prefix-sum inclusion-exclusion.

## Intuition
Precompute P[i][j] = sum of rectangle (0,0)-(i-1,j-1). Any sub-rectangle sum = P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1].

## Detailed Explanation
Build (n+1)×(m+1) prefix. Each query in O(1).

## Dry Run
matrix=[[3,0,1,4,2],...]. Precompute P. Query (2,1)-(4,3) = P[5][4]-P[2][4]-P[5][1]+P[2][1].

## Approach
2D prefix sums.

## Time and Space Complexity
Build O(n*m), query O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class NumMatrix {
    vector<vector<int>> P;
public:
    NumMatrix(vector<vector<int>>& M) {
        int n = M.size(), m = M[0].size();
        P.assign(n+1, vector<int>(m+1, 0));
        for (int i = 0; i < n; ++i) for (int j = 0; j < m; ++j)
            P[i+1][j+1] = M[i][j] + P[i][j+1] + P[i+1][j] - P[i][j];
    }
    int sumRegion(int r1, int c1, int r2, int c2) {
        return P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1];
    }
};
```

## Follow-up Questions
- Mutable variant (Binary Indexed Tree 2D).
- 3D prefix sum.
- Sum over rotated rectangles.
