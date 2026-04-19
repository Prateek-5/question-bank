# Triangle

## Problem Link
https://leetcode.com/problems/triangle/

## Topic
Dynamic Programming DP

## Core Concept
Bottom-up DP on rows.

## Intuition
From the bottom row up, each cell's min path = its value + min of two children below.

## Detailed Explanation
Initialize dp=last row. For i from n-2 to 0: dp[j] = triangle[i][j] + min(dp[j], dp[j+1]).

## Dry Run
triangle=[[2],[3,4],[6,5,7],[4,1,8,3]]. Answer 11.

## Approach
O(n²) DP in-place.

## Time and Space Complexity
Time: O(n²). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int minimumTotal(vector<vector<int>>& t) {
    vector<int> dp = t.back();
    for (int i = t.size() - 2; i >= 0; --i)
        for (int j = 0; j <= i; ++j)
            dp[j] = t[i][j] + min(dp[j], dp[j+1]);
    return dp[0];
}
```

## Follow-up Questions
- Path itself.
- Max sum (same recurrence with max).
- Stochastic weights.
