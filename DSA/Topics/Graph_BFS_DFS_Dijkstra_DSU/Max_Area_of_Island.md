# Max Area of Island

## Problem Link
https://leetcode.com/problems/max-area-of-island/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
DFS flood-fill counting connected land cells.

## Intuition
Each island is a 4-connected component of 1s. DFS/BFS from each unvisited 1 cell to count its size; track the max.

## Detailed Explanation
Iterate cells. On a 1, launch DFS marking cells as visited (or flip to 0) and counting. Update the global max area.

## Dry Run
grid=[[1,1,0],[0,1,0],[0,0,1]]. From (0,0) DFS visits (0,0),(0,1),(1,1) → area 3. From (2,2) area 1. Max=3.

## Approach
DFS with boundary and visited checks.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m) stack.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maxAreaOfIsland(vector<vector<int>>& g) {
    int n = g.size(), m = g[0].size(), best = 0;
    function<int(int,int)> dfs = [&](int r, int c) {
        if (r<0||c<0||r>=n||c>=m||!g[r][c]) return 0;
        g[r][c] = 0;
        return 1 + dfs(r+1,c) + dfs(r-1,c) + dfs(r,c+1) + dfs(r,c-1);
    };
    for (int i=0;i<n;i++) for (int j=0;j<m;j++)
        if (g[i][j]) best = max(best, dfs(i,j));
    return best;
}
```

## Follow-up Questions
- Count number of islands instead.
- 8-connected instead of 4-connected.
- Find the island containing a given cell.
