# Shortest Path in Binary Matrix

## Problem Link
https://leetcode.com/problems/shortest-path-in-binary-matrix/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
BFS in 8-directional grid.

## Intuition
Unweighted shortest path → BFS. From (0,0), expand to 8-direction neighbors that are 0, recording distance.

## Detailed Explanation
If start or end is 1 return -1. BFS from (0,0) with dist=1. Expand 8 neighbors; when reaching (n-1,n-1), return dist.

## Dry Run
grid=[[0,0,0],[1,1,0],[1,1,0]]. Path (0,0)→(0,1)→(0,2)→(1,2)→(2,2). Distance 5.

## Approach
BFS with 8 moves and grid cell marking.

## Time and Space Complexity
Time: O(n²). Space: O(n²).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int shortestPathBinaryMatrix(vector<vector<int>>& g) {
    int n = g.size();
    if (g[0][0] || g[n-1][n-1]) return -1;
    queue<tuple<int,int,int>> q; q.push({0,0,1});
    g[0][0] = 1;
    int dr[] = {-1,-1,-1,0,0,1,1,1}, dc[] = {-1,0,1,-1,1,-1,0,1};
    while (!q.empty()) {
        auto [r,c,d] = q.front(); q.pop();
        if (r==n-1 && c==n-1) return d;
        for (int k=0;k<8;k++) {
            int nr=r+dr[k], nc=c+dc[k];
            if (nr<0||nc<0||nr>=n||nc>=n||g[nr][nc]) continue;
            g[nr][nc] = 1; q.push({nr,nc,d+1});
        }
    }
    return -1;
}
```

## Follow-up Questions
- Weighted cells — Dijkstra.
- A* with Chebyshev heuristic.
- Multi-goal shortest path.
