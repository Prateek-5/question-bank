# Ones and Zeroes

## Problem Link
https://leetcode.com/problems/ones-and-zeroes/

## Topic
Dynamic Programming DP

## Core Concept
0/1 knapsack over two capacities (0s and 1s).

## Intuition
Each string 'costs' its count of 0s and 1s; we maximize count of strings within budgets (m zeros, n ones).

## Detailed Explanation
dp[i][j] = max strings using at most i zeros and j ones. For each string with z zeros, o ones: dp[i][j] = max(dp[i][j], dp[i-z][j-o]+1) iterating i,j downward.

## Dry Run
strs=['10','0001','111001','1','0'], m=5,n=3 → 4.

## Approach
2D 0/1 knapsack.

## Time and Space Complexity
Time: O(K·m·n). Space: O(m·n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findMaxForm(vector<string>& strs, int m, int n) {
    vector<vector<int>> dp(m+1, vector<int>(n+1, 0));
    for (auto& s : strs) {
        int z = count(s.begin(), s.end(), '0'), o = s.size() - z;
        for (int i = m; i >= z; --i) for (int j = n; j >= o; --j)
            dp[i][j] = max(dp[i][j], dp[i-z][j-o] + 1);
    }
    return dp[m][n];
}
```

## Follow-up Questions
- Minimize number of strings to meet a target.
- 3D (0,1,2 digits).
- Unbounded knapsack variant.
