# Number of Enclaves

## Problem Link
https://leetcode.com/problems/number-of-enclaves/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Flood-fill from border land cells and count remaining interior land.

## Intuition
Enclaves are land cells that cannot reach the boundary. Remove all land connected to the border; what remains are enclaves.

## Detailed Explanation
DFS/BFS from every boundary cell that is 1, marking connected land as 0. Then count total 1s remaining.

## Dry Run
grid=[[0,0,0,0],[1,0,1,0],[0,1,1,0],[0,0,0,0]]. Border cells: no 1 on border. So all interior 1s are enclaves → count = 4.

## Approach
Border DFS then scan.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int numEnclaves(vector<vector<int>>& g) {
    int n = g.size(), m = g[0].size();
    function<void(int,int)> dfs = [&](int r, int c) {
        if (r<0||c<0||r>=n||c>=m||!g[r][c]) return;
        g[r][c] = 0;
        dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1);
    };
    for (int i=0;i<n;i++) { dfs(i,0); dfs(i,m-1); }
    for (int j=0;j<m;j++) { dfs(0,j); dfs(n-1,j); }
    int cnt = 0;
    for (auto& r : g) for (int v : r) cnt += v;
    return cnt;
}
```

## Follow-up Questions
- Variation where diagonal moves allowed.
- Count of separate enclave components.
- Largest enclave.
