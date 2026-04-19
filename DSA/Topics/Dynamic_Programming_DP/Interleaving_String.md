# Interleaving String

## Problem Link
https://leetcode.com/problems/interleaving-string/

## Topic
Dynamic Programming DP

## Core Concept
2D DP checking whether s3 can be formed by interleaving s1,s2.

## Intuition
dp[i][j] = true if s3[0..i+j-1] is an interleave of s1[0..i-1] and s2[0..j-1]. Transition from using s1[i-1] or s2[j-1].

## Detailed Explanation
dp[i][j] = (dp[i-1][j] && s1[i-1]==s3[i+j-1]) || (dp[i][j-1] && s2[j-1]==s3[i+j-1]).

## Dry Run
s1='aab', s2='axy', s3='aaxaby'. dp[3][3]=true.

## Approach
Bottom-up 2D DP.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m) or O(m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool isInterleave(string s1, string s2, string s3) {
    int n = s1.size(), m = s2.size();
    if (n + m != (int)s3.size()) return false;
    vector<vector<bool>> dp(n+1, vector<bool>(m+1, false));
    dp[0][0] = true;
    for (int i = 0; i <= n; ++i) for (int j = 0; j <= m; ++j) {
        if (i > 0 && dp[i-1][j] && s1[i-1] == s3[i+j-1]) dp[i][j] = true;
        if (j > 0 && dp[i][j-1] && s2[j-1] == s3[i+j-1]) dp[i][j] = true;
    }
    return dp[n][m];
}
```

## Follow-up Questions
- 3-string interleave.
- Count of distinct interleavings.
- With wildcards.
