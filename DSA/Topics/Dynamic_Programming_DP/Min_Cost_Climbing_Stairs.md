# Min Cost Climbing Stairs

## Problem Link
https://leetcode.com/problems/min-cost-climbing-stairs/

## Topic
Dynamic Programming DP

## Core Concept
DP dp[i] = cost[i] + min(dp[i-1], dp[i-2]).

## Intuition
Reach top by stepping one or two at a time; minimize the sum of step costs incurred.

## Detailed Explanation
Iterate; a=b=0 initially (free at start). For each i: c = cost[i] + min(a, b); a = b; b = c. Answer min(a, b) at end.

## Dry Run
cost=[10,15,20] → 15.

## Approach
Rolling DP.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int minCostClimbingStairs(vector<int>& c) {
    int a = 0, b = 0;
    for (int x : c) { int cur = x + min(a, b); a = b; b = cur; }
    return min(a, b);
}
```

## Follow-up Questions
- k steps per move.
- Stochastic costs (expected).
- Reach exactly step n.
