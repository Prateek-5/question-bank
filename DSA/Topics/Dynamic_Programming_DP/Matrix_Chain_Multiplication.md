# Matrix Chain Multiplication

## Problem Link
https://practice.geeksforgeeks.org/problems/matrix-chain-multiplication0303/1

## Topic
Dynamic Programming DP

## Core Concept
Interval DP over splitting index.

## Intuition
To multiply chain p[i..j], pick a split k; cost = dp[i][k] + dp[k+1][j] + p[i-1]*p[k]*p[j]. Try all splits, take min.

## Detailed Explanation
Standard interval DP with increasing length.

## Dry Run
p=[1,2,3,4]. Optimal 18.

## Approach
Bottom-up DP in increasing chain length.

## Time and Space Complexity
Time: O(n³). Space: O(n²).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int mcm(vector<int>& p) {
    int n = p.size() - 1;
    vector<vector<int>> dp(n+1, vector<int>(n+1, 0));
    for (int len = 2; len <= n; ++len)
        for (int i = 1; i + len - 1 <= n; ++i) {
            int j = i + len - 1;
            dp[i][j] = INT_MAX;
            for (int k = i; k < j; ++k)
                dp[i][j] = min(dp[i][j], dp[i][k] + dp[k+1][j] + p[i-1]*p[k]*p[j]);
        }
    return dp[1][n];
}
```

## Follow-up Questions
- Reconstruct the parenthesization.
- Optimal BST (similar DP).
- Egg-drop DP.
