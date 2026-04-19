# Longest Common Subsequence

## Problem Link
https://leetcode.com/problems/longest-common-subsequence/

## Topic
Dynamic Programming DP

## Core Concept
Classic 2D DP over (i,j).

## Intuition
dp[i][j] = LCS of s[0..i-1], t[0..j-1]. If chars match extend; else max of skipping one.

## Detailed Explanation
dp[i][j] = s[i-1]==t[j-1] ? dp[i-1][j-1]+1 : max(dp[i-1][j], dp[i][j-1]).

## Dry Run
s='abcde', t='ace' → LCS 'ace' length 3.

## Approach
Bottom-up DP.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m) or O(m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int longestCommonSubsequence(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<int>> dp(n+1, vector<int>(m+1, 0));
    for (int i=1;i<=n;i++) for (int j=1;j<=m;j++)
        dp[i][j] = s[i-1]==t[j-1] ? dp[i-1][j-1]+1 : max(dp[i-1][j], dp[i][j-1]);
    return dp[n][m];
}
```

## Follow-up Questions
- Print the LCS.
- LCS of three strings.
- Space-optimized to O(m).
