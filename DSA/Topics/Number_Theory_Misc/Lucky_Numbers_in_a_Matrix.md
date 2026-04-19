# Lucky Numbers in a Matrix

## Problem Link
https://leetcode.com/problems/lucky-numbers-in-a-matrix/description/

## Topic
Number Theory Misc

## Core Concept
Row min ∩ column max.

## Intuition
A lucky number is the minimum in its row and simultaneously the maximum in its column. Precompute row-mins and col-maxes and intersect.

## Detailed Explanation
Compute rowMin[i], colMax[j]. For each cell equal to both rowMin[i] and colMax[j], add to result.

## Dry Run
M=[[3,7,8],[9,11,13],[15,16,17]]. rowMin=[3,9,15]. colMax=[15,16,17]. Only 15 matches both → answer [15].

## Approach
Two passes.

## Time and Space Complexity
Time: O(n·m). Space: O(n+m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> luckyNumbers(vector<vector<int>>& M) {
    int n = M.size(), m = M[0].size();
    vector<int> rmn(n, INT_MAX), cmx(m, INT_MIN);
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) { rmn[i]=min(rmn[i], M[i][j]); cmx[j]=max(cmx[j], M[i][j]); }
    vector<int> res;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) if (M[i][j]==rmn[i] && M[i][j]==cmx[j]) res.push_back(M[i][j]);
    return res;
}
```

## Follow-up Questions
- Median-based lucky numbers.
- Matrix with ties (multiple minima).
- Sparse matrices.
