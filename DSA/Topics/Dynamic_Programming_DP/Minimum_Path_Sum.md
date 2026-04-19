# Minimum Path Sum

## Problem Link
https://leetcode.com/problems/minimum-path-sum/

## Topic
Dynamic Programming DP

## Core Concept
DP from top-left: dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1]).

## Intuition
At each cell the best path either came from above or from the left — take the cheaper.

## Detailed Explanation
Iterate rows/cols; handle first row/col separately (only one predecessor).

## Dry Run
grid=[[1,3,1],[1,5,1],[4,2,1]] → 7 (1→3→1→1→1).

## Approach
Bottom-up in-place.

## Time and Space Complexity
Time: O(n·m). Space: O(1) if in-place.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int minPathSum(vector<vector<int>>& g) {
    int n=g.size(), m=g[0].size();
    for (int i = 0; i < n; ++i) for (int j = 0; j < m; ++j) {
        if (i == 0 && j == 0) continue;
        int up = i ? g[i-1][j] : INT_MAX;
        int left = j ? g[i][j-1] : INT_MAX;
        g[i][j] += min(up, left);
    }
    return g[n-1][m-1];
}
```

## Follow-up Questions
- Return the path.
- Allow diagonal moves.
- K-th smallest path sum.
