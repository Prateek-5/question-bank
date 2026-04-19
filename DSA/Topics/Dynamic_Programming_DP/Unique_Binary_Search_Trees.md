# Unique Binary Search Trees

## Problem Link
https://leetcode.com/problems/unique-binary-search-trees/

## Topic
Dynamic Programming DP

## Core Concept
Catalan numbers — dp[n] = Σ dp[i]·dp[n-1-i].

## Intuition
With n nodes, pick root i; left subtree has i-1 nodes, right has n-i — independent counts multiplied and summed over all roots.

## Detailed Explanation
dp[0]=1. For i=1..n: dp[i] = Σ dp[j]·dp[i-1-j] for j=0..i-1.

## Dry Run
n=3 → dp[3]=5.

## Approach
DP over n.

## Time and Space Complexity
Time: O(n²). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int numTrees(int n) {
    vector<int> dp(n+1, 0); dp[0] = 1;
    for (int i = 1; i <= n; ++i) for (int j = 0; j < i; ++j) dp[i] += dp[j] * dp[i-1-j];
    return dp[n];
}
```

## Follow-up Questions
- Generate all unique BSTs (Unique BSTs II).
- Weighted BSTs (optimal BST).
- Catalan formulas.
