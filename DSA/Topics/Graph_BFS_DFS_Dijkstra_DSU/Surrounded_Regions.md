# Surrounded Regions

## Problem Link
https://leetcode.com/problems/surrounded-regions/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Flood-fill from boundary Os to identify safe ones; flip the rest.

## Intuition
An 'O' is surrounded iff it cannot escape to the boundary. Mark all 'O's reachable from the boundary as safe; flip all other 'O's to 'X'.

## Detailed Explanation
DFS/BFS from every boundary 'O', marking as temporary '#'. Then scan: '#' → 'O' (safe), 'O' → 'X' (surrounded).

## Dry Run
board=[['X','X','X','X'],['X','O','O','X'],['X','X','O','X'],['X','O','X','X']]. Border O at (3,1) only is safe. Others flipped to X.

## Approach
Two passes after boundary DFS.

## Time and Space Complexity
Time: O(n·m). Space: O(n·m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
void solve(vector<vector<char>>& b) {
    int n = b.size(), m = b[0].size();
    function<void(int,int)> dfs = [&](int r, int c) {
        if (r<0||c<0||r>=n||c>=m||b[r][c]!='O') return;
        b[r][c] = '#';
        dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1);
    };
    for (int i=0;i<n;i++) { dfs(i,0); dfs(i,m-1); }
    for (int j=0;j<m;j++) { dfs(0,j); dfs(n-1,j); }
    for (int i=0;i<n;i++) for (int j=0;j<m;j++)
        b[i][j] = (b[i][j]=='#' ? 'O' : 'X');
}
```

## Follow-up Questions
- In-place variant with constant extra memory.
- 8-connected variant.
- Detect number of surrounded regions.
