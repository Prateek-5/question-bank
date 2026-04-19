# Dungeon Game

## Problem Link
https://leetcode.com/problems/dungeon-game/

## Topic
Dynamic Programming DP

## Core Concept
Bottom-up min-HP DP from bottom-right.

## Intuition
We need minimum starting HP so the knight never drops to ≤0. Work backward from the princess cell where needed health = max(1, 1 - room_value).

## Detailed Explanation
dp[i][j] = max(1, min(dp[i+1][j], dp[i][j+1]) - dungeon[i][j]). Base: dp[n-1][m-1] = max(1, 1 - dungeon[n-1][m-1]).

## Dry Run
dungeon=[[-2,-3,3],[-5,-10,1],[10,30,-5]]. Answer=7.

## Approach
Reverse DP in-place.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int calculateMinimumHP(vector<vector<int>>& D) {
    int n = D.size(), m = D[0].size();
    vector<vector<int>> dp(n+1, vector<int>(m+1, INT_MAX));
    dp[n][m-1] = dp[n-1][m] = 1;
    for (int i = n-1; i >= 0; --i)
        for (int j = m-1; j >= 0; --j)
            dp[i][j] = max(1, min(dp[i+1][j], dp[i][j+1]) - D[i][j]);
    return dp[0][0];
}
```

## Follow-up Questions
- 3D variant.
- Include power-ups that cap HP.
- Return the path.
