# Longest Arithmetic Subsequence

## Problem Link
https://leetcode.com/problems/longest-arithmetic-subsequence/

## Topic
Dynamic Programming DP

## Core Concept
DP over (index, common_difference) pairs.

## Intuition
For each index j and diff d, dp[j][d] = longest AP ending at j with difference d = dp[i][d]+1 over i<j with a[j]-a[i]=d.

## Detailed Explanation
Use a map per index. For each (i,j), d=a[j]-a[i]; dp[j][d] = max(dp[j][d], dp[i][d]+1). Track global max.

## Dry Run
nums=[9,4,7,2,10]. Longest AP 4,7,10 → length 3.

## Approach
O(n²) with hashmap dp.

## Time and Space Complexity
Time: O(n²). Space: O(n²).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int longestArithSeqLength(vector<int>& a) {
    int n = a.size(), best = 2;
    vector<unordered_map<int,int>> dp(n);
    for (int j = 1; j < n; ++j) for (int i = 0; i < j; ++i) {
        int d = a[j] - a[i];
        dp[j][d] = dp[i].count(d) ? dp[i][d] + 1 : 2;
        best = max(best, dp[j][d]);
    }
    return best;
}
```

## Follow-up Questions
- Arithmetic slices count.
- Geometric subsequence.
- AP with fixed difference.
