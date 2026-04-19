# Rotting Oranges

## Problem Link
https://leetcode.com/problems/rotting-oranges/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Multi-source BFS from all rotten oranges simultaneously.

## Intuition
Every minute the infection spreads one step in all directions from every rotten orange. BFS level = minute. Answer is the last level that changed state.

## Detailed Explanation
Push all rotten cells at time 0. BFS expands to fresh neighbors, marking them rotten with time+1. After BFS, if any fresh remains → -1, else return max time observed.

## Dry Run
grid=[[2,1,1],[1,1,0],[0,1,1]]. Minute 0: (0,0). Minute 1: (0,1),(1,0). Minute 2: (0,2),(1,1). Minute 3: (2,1). Minute 4: (2,2). Answer=4.

## Approach
BFS with level tracking and fresh-count.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int orangesRotting(vector<vector<int>>& g) {
    int n=g.size(), m=g[0].size(), fresh=0, minutes=0;
    queue<pair<int,int>> q;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) {
        if (g[i][j]==2) q.push({i,j});
        else if (g[i][j]==1) fresh++;
    }
    int dr[] = {-1,1,0,0}, dc[] = {0,0,-1,1};
    while (!q.empty() && fresh) {
        int sz = q.size(); minutes++;
        while (sz--) {
            auto [r,c] = q.front(); q.pop();
            for (int k=0;k<4;k++) {
                int nr=r+dr[k], nc=c+dc[k];
                if (nr<0||nc<0||nr>=n||nc>=m||g[nr][nc]!=1) continue;
                g[nr][nc]=2; fresh--; q.push({nr,nc});
            }
        }
    }
    return fresh ? -1 : minutes;
}
```

## Follow-up Questions
- Infection with variable speed per cell.
- Source selection — minimize infection time with k sources.
- 3D rotting grid.
