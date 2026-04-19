# Distinct Subsequences

## Problem Link
https://leetcode.com/problems/distinct-subsequences/

## Topic
Dynamic Programming DP

## Core Concept
DP dp[i][j] = ways to form t[0..j-1] from s[0..i-1].

## Intuition
At each (i,j), either skip s[i-1] (dp[i-1][j]) or consume it if s[i-1]==t[j-1] (+ dp[i-1][j-1]).

## Detailed Explanation
Init dp[i][0]=1. For i,j>0: dp[i][j] = dp[i-1][j] + (s[i-1]==t[j-1] ? dp[i-1][j-1] : 0).

## Dry Run
s='rabbbit', t='rabbit'. dp[n][m]=3.

## Approach
2D DP; can compress to 1D.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m) or O(m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int numDistinct(string s, string t) {
    int n = s.size(), m = t.size();
    vector<unsigned long long> dp(m+1, 0); dp[0] = 1;
    for (int i = 1; i <= n; ++i)
        for (int j = m; j >= 1; --j)
            if (s[i-1] == t[j-1]) dp[j] += dp[j-1];
    return (int)dp[m];
}
```

## Follow-up Questions
- Number of distinct supersequences.
- LCS variant (Edit-distance).
- Regex subsequences.
