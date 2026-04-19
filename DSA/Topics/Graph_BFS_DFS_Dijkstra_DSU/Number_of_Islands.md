# Number of Islands

## Problem Link
https://leetcode.com/problems/number-of-islands/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Count connected components of 1s via DFS/BFS.

## Intuition
Each island is a 4-connected component. Iterate all cells; whenever we hit an unvisited 1, flood-fill the whole island and increment a counter.

## Detailed Explanation
DFS from each unvisited land cell, marking visited by setting '1'→'0'. Each DFS launch counts as one island.

## Dry Run
grid=[['1','1','0'],['0','1','0'],['0','0','1']]. From (0,0) flood {(0,0),(0,1),(1,1)} → 1 island. From (2,2) → 2 islands.

## Approach
DFS; could use BFS to avoid deep recursion.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m) in the worst case.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int numIslands(vector<vector<char>>& g) {
    int n = g.size(), m = g[0].size(), cnt = 0;
    function<void(int,int)> dfs = [&](int r, int c) {
        if (r<0||c<0||r>=n||c>=m||g[r][c]!='1') return;
        g[r][c] = '0';
        dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1);
    };
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) if (g[i][j]=='1') { cnt++; dfs(i,j); }
    return cnt;
}
```

## Follow-up Questions
- Variant with 8-connectivity.
- Count islands in a streamed grid (add land operations).
- Largest island.
