# Number of Provinces

## Problem Link
https://leetcode.com/problems/number-of-provinces/description/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Connected components in an adjacency matrix.

## Intuition
Cities directly or transitively connected form a province. Count components using DFS or DSU.

## Detailed Explanation
Iterate cities; for each unvisited city, DFS all connected ones and mark visited. Each DFS launch = +1 province.

## Dry Run
isConnected=[[1,1,0],[1,1,0],[0,0,1]]. From 0 visit 0,1. From 2 visit 2. Provinces=2.

## Approach
DFS or DSU over n×n.

## Time and Space Complexity
Time: O(n²). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findCircleNum(vector<vector<int>>& g) {
    int n = g.size(); vector<int> seen(n, 0); int cnt = 0;
    function<void(int)> dfs = [&](int u) {
        seen[u] = 1;
        for (int v = 0; v < n; ++v) if (g[u][v] && !seen[v]) dfs(v);
    };
    for (int i = 0; i < n; ++i) if (!seen[i]) { cnt++; dfs(i); }
    return cnt;
}
```

## Follow-up Questions
- With adjacency list to avoid O(n²).
- Dynamic province counting as edges arrive/leave.
- Province with largest population.
