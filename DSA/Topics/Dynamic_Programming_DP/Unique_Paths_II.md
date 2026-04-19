# Unique Paths II

## Problem Link
https://leetcode.com/problems/unique-paths-ii/

## Topic
Dynamic Programming DP

## Core Concept
DP over grid with obstacles.

## Intuition
dp[i][j] = 0 if obstacle; else sum of dp[i-1][j] and dp[i][j-1].

## Detailed Explanation
Bottom-up DP; base dp[0][0] = grid[0][0]==0.

## Dry Run
grid=[[0,0,0],[0,1,0],[0,0,0]] → 2 paths.

## Approach
Standard grid DP.

## Time and Space Complexity
Time: O(n·m). Space: O(m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int uniquePathsWithObstacles(vector<vector<int>>& g) {
    int n=g.size(), m=g[0].size();
    vector<long long> dp(m, 0); dp[0] = g[0][0] ? 0 : 1;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) {
        if (g[i][j]) dp[j] = 0;
        else if (j > 0) dp[j] += dp[j-1];
    }
    return (int)dp[m-1];
}
```

## Follow-up Questions
- With weighted obstacles.
- Minimize obstacles on path.
- Count paths mod p.
