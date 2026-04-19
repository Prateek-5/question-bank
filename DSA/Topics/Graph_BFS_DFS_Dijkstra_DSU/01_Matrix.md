# 01 Matrix

## Problem Link
https://leetcode.com/problems/01-matrix/description/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Multi-source BFS from all zeros simultaneously.

## Intuition
Each cell's answer is the distance to the *nearest* zero. Instead of BFS from every one cell, invert it — start BFS from every zero at distance 0 and propagate outward. Each cell is first reached at its correct distance.

## Detailed Explanation
Initialize dist[r][c] = 0 if cell is 0, else INF. Push all zeros into a queue. BFS: for the front cell, visit 4 neighbors; if neighbor's distance > current+1, update and push. BFS guarantees shortest distance in unweighted graphs.

## Dry Run
mat=[[0,0,0],[0,1,0],[1,1,1]]. Zeros pushed at dist 0. BFS expands: (1,1)=1, (2,0)=1, (2,2)=1, (2,1)=2. Result matches shortest-zero distances.

## Approach
Multi-source BFS gives O(n*m).

## Time and Space Complexity
Time: O(n·m). Space: O(n·m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> updateMatrix(vector<vector<int>>& mat) {
    int n = mat.size(), m = mat[0].size();
    vector<vector<int>> d(n, vector<int>(m, INT_MAX));
    queue<pair<int,int>> q;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) if (!mat[i][j]) { d[i][j]=0; q.push({i,j}); }
    int dr[] = {-1,1,0,0}, dc[] = {0,0,-1,1};
    while (!q.empty()) {
        auto [r,c] = q.front(); q.pop();
        for (int k=0;k<4;k++) {
            int nr=r+dr[k], nc=c+dc[k];
            if (nr<0||nc<0||nr>=n||nc>=m) continue;
            if (d[nr][nc] > d[r][c] + 1) { d[nr][nc] = d[r][c] + 1; q.push({nr,nc}); }
        }
    }
    return d;
}
```

## Follow-up Questions
- Use two-pass DP for the same problem.
- Weighted variant with Dijkstra.
- 3D matrix analog.
