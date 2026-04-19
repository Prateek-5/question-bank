# Edit Distance

## Problem Link
https://leetcode.com/problems/edit-distance/

## Topic
Dynamic Programming DP

## Core Concept
Levenshtein DP: insert/delete/replace transitions.

## Intuition
dp[i][j] = minimum edits to convert s[0..i-1] → t[0..j-1]. Choose between matching, inserting, deleting, replacing.

## Detailed Explanation
Base: dp[0][j]=j, dp[i][0]=i. If chars match: dp[i][j]=dp[i-1][j-1]. Else 1+min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]).

## Dry Run
'horse'→'ros'. Answer 3.

## Approach
2D DP; 1D rolling possible.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int minDistance(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<int>> dp(n+1, vector<int>(m+1, 0));
    for (int i = 0; i <= n; ++i) dp[i][0] = i;
    for (int j = 0; j <= m; ++j) dp[0][j] = j;
    for (int i = 1; i <= n; ++i) for (int j = 1; j <= m; ++j)
        dp[i][j] = s[i-1] == t[j-1] ? dp[i-1][j-1] : 1 + min({dp[i-1][j], dp[i][j-1], dp[i-1][j-1]});
    return dp[n][m];
}
```

## Follow-up Questions
- Weighted operations.
- Print actual edits.
- Damerau-Levenshtein (transpositions).
