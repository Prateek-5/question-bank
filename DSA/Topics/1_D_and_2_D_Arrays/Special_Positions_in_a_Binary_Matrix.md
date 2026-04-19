# Special Positions in a Binary Matrix

## Problem Link
https://leetcode.com/problems/special-positions-in-a-binary-matrix/

## Topic
1 D and 2 D Arrays

## Core Concept
Row/column sums; a position is special if its cell is 1 and row sum = col sum = 1.

## Intuition
A special 1 must be alone in its row and column. Precompute row/column sums, then count cells that are 1 with both sums equal to 1.

## Detailed Explanation
Compute rowSum, colSum. For each (i,j) with mat[i][j]==1 and rowSum[i]==1 and colSum[j]==1, increment.

## Dry Run
mat=[[1,0,0],[0,0,1],[1,0,0]]. rowSum=[1,1,1], colSum=[2,0,1]. (0,0):rowSum=1,colSum=2 → no. (1,2):1,1 → yes. Special=1.

## Approach
Two passes.

## Time and Space Complexity
Time: O(n*m). Space: O(n+m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int numSpecial(vector<vector<int>>& M) {
    int n = M.size(), m = M[0].size();
    vector<int> rs(n,0), cs(m,0);
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) { rs[i]+=M[i][j]; cs[j]+=M[i][j]; }
    int cnt = 0;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++)
        if (M[i][j]==1 && rs[i]==1 && cs[j]==1) cnt++;
    return cnt;
}
```

## Follow-up Questions
- Special positions in a non-binary matrix.
- Return the positions.
- Weighted version with thresholds.
