# Maximum Height by Stacking Cuboids

## Problem Link
https://leetcode.com/problems/maximum-height-by-stacking-cuboids/description/

## Topic
Dynamic Programming DP

## Core Concept
Sort cuboid dimensions; find LIS-like chain maximizing height.

## Intuition
Each cuboid can be rotated; sort its dims so width≤depth≤height. Then sort cuboids and use DP where dp[i] = best stack ending with cuboid i.

## Detailed Explanation
For each cuboid sort its (a,b,c). Sort cuboids lexicographically. dp[i] = c[i] + max over j<i with a[j]≤a[i], b[j]≤b[i], c[j]≤c[i] of dp[j]. Answer max dp.

## Dry Run
cuboids=[[50,45,20],[95,37,53],[45,23,12]] → sort each and chain; answer 190.

## Approach
Sort-then-LIS DP.

## Time and Space Complexity
Time: O(n²). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maxHeight(vector<vector<int>>& c) {
    for (auto& v : c) sort(v.begin(), v.end());
    sort(c.begin(), c.end());
    int n = c.size(), best = 0;
    vector<int> dp(n);
    for (int i = 0; i < n; ++i) {
        dp[i] = c[i][2];
        for (int j = 0; j < i; ++j)
            if (c[j][0] <= c[i][0] && c[j][1] <= c[i][1] && c[j][2] <= c[i][2])
                dp[i] = max(dp[i], dp[j] + c[i][2]);
        best = max(best, dp[i]);
    }
    return best;
}
```

## Follow-up Questions
- Box stacking (3 orientations per box).
- With weights constraint.
- Maximize count of stacked cuboids.
