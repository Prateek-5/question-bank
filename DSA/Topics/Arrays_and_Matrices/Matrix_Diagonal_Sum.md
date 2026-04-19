# Matrix Diagonal Sum

## Problem Link
https://leetcode.com/problems/matrix-diagonal-sum/

## Topic
Arrays and Matrices

## Core Concept
Sum primary + secondary diagonal; subtract center if n is odd.

## Intuition
Every element on the primary diagonal satisfies i==j. Secondary satisfies i+j==n-1. If n is odd the middle element is counted twice.

## Detailed Explanation
sum = Σ mat[i][i] + Σ mat[i][n-1-i]. If n is odd, subtract mat[n/2][n/2].

## Dry Run
n=3. mat=[[1,2,3],[4,5,6],[7,8,9]]. Primary=1+5+9=15, secondary=3+5+7=15. Sum=30, subtract 5 → 25.

## Approach
Single loop.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int diagonalSum(vector<vector<int>>& M) {
    int n = M.size(), s = 0;
    for (int i = 0; i < n; ++i) s += M[i][i] + M[i][n-1-i];
    if (n & 1) s -= M[n/2][n/2];
    return s;
}
```

## Follow-up Questions
- Anti-diagonal sum by row+col constant.
- 3D diagonal.
- Sum of diagonals at distance k from main.
