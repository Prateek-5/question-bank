# Regular Expression Matching

## Problem Link
https://leetcode.com/problems/regular-expression-matching/

## Topic
Dynamic Programming DP

## Core Concept
DP over (i,j) handling '.' and '*'.

## Intuition
dp[i][j] = s[0..i-1] matches p[0..j-1]. '.' matches any char; '*' allows zero or more of preceding char.

## Detailed Explanation
If p[j-1]=='*': dp[i][j] = dp[i][j-2] || (match(s[i-1], p[j-2]) && dp[i-1][j]). Else: dp[i][j] = match && dp[i-1][j-1].

## Dry Run
s='aab', p='c*a*b' → true.

## Approach
Bottom-up DP.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool isMatch(string s, string p) {
    int n = s.size(), m = p.size();
    vector<vector<bool>> dp(n+1, vector<bool>(m+1, false));
    dp[0][0] = true;
    for (int j = 1; j <= m; ++j) if (p[j-1] == '*') dp[0][j] = dp[0][j-2];
    auto match = [&](int i, int j){ return p[j-1]=='.' || s[i-1]==p[j-1]; };
    for (int i = 1; i <= n; ++i) for (int j = 1; j <= m; ++j) {
        if (p[j-1] == '*') dp[i][j] = dp[i][j-2] || (match(i, j-1) && dp[i-1][j]);
        else dp[i][j] = match(i, j) && dp[i-1][j-1];
    }
    return dp[n][m];
}
```

## Follow-up Questions
- Wildcard matching (?,* simpler).
- NFA-based general regex.
- Greedy + backtrack implementation.
