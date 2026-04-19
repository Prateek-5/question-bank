# Max Points on a Line

## Problem Link
https://leetcode.com/problems/max-points-on-a-line/

## Topic
Hashing Sliding Window

## Core Concept
For each point, count slopes of lines to all others using hashmap with normalized slope keys.

## Intuition
Pick a pivot; group other points by slope (dy/dx reduced by gcd and signed). Max count + 1 (pivot) is best through that point.

## Detailed Explanation
For each i, clear map; for each j≠i compute (dx,dy), normalize by gcd and sign (dx first). Increment count[(dx,dy)]. Track global max.

## Dry Run
points=[[1,1],[2,2],[3,3]] → 3.

## Approach
O(n²) with hashmap.

## Time and Space Complexity
Time: O(n²). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maxPoints(vector<vector<int>>& pts) {
    int n = pts.size(), best = 0;
    if (n <= 2) return n;
    for (int i = 0; i < n; ++i) {
        map<pair<int,int>, int> cnt;
        int localMax = 0;
        for (int j = 0; j < n; ++j) if (i != j) {
            int dx = pts[j][0] - pts[i][0], dy = pts[j][1] - pts[i][1];
            int g = __gcd(abs(dx), abs(dy));
            if (g == 0) g = 1;
            dx /= g; dy /= g;
            if (dx < 0) { dx = -dx; dy = -dy; }
            if (dx == 0 && dy < 0) dy = -dy;
            localMax = max(localMax, ++cnt[{dx, dy}]);
        }
        best = max(best, localMax + 1);
    }
    return best;
}
```

## Follow-up Questions
- Weighted points (count with weights).
- 3D lines.
- Cluster points forming triangles.
