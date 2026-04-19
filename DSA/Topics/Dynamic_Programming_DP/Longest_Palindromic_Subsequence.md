# Longest Palindromic Subsequence

## Problem Link
https://leetcode.com/problems/longest-palindromic-subsequence/

## Topic
Dynamic Programming DP

## Core Concept
LCS of s and reverse(s).

## Intuition
A palindromic subsequence of s corresponds to a common subsequence of s and reverse(s).

## Detailed Explanation
Compute LCS(s, reverse(s)).

## Dry Run
'bbbab'. LCS with 'babbb' = 'bbbb' length 4.

## Approach
Standard LCS DP.

## Time and Space Complexity
Time: O(n²). Space: O(n²).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int longestPalindromeSubseq(string s) {
    string t(s.rbegin(), s.rend());
    int n = s.size();
    vector<vector<int>> dp(n+1, vector<int>(n+1, 0));
    for (int i=1;i<=n;i++) for (int j=1;j<=n;j++)
        dp[i][j] = s[i-1]==t[j-1] ? dp[i-1][j-1]+1 : max(dp[i-1][j], dp[i][j-1]);
    return dp[n][n];
}
```

## Follow-up Questions
- Print the palindrome.
- Longest palindromic substring (Manacher).
- Palindrome partitioning.
