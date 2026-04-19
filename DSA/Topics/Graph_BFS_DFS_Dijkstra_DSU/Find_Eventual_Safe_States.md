# Find Eventual Safe States

## Problem Link
https://leetcode.com/problems/find-eventual-safe-states/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Topological sort on the reverse graph (or DFS with three-color marking).

## Intuition
A safe node leads only to terminal (no outgoing) or other safe nodes. Reverse edges and BFS from terminal nodes; any node reached is safe. Equivalently, nodes not on any cycle.

## Detailed Explanation
Reverse the graph. Start BFS from nodes with original out-degree 0. Decrement in the reversed graph's in-degree when their predecessors are processed. All processed nodes are safe.

## Dry Run
graph=[[1,2],[2,3],[5],[0],[5],[],[]] → safes are 2,4,5,6. Terminal 5,6 initially, then 2 (points only to 5), then 4 (points to 5).

## Approach
Reverse graph + Kahn, or three-color DFS (white/gray/black).

## Time and Space Complexity
Time: O(V + E). Space: O(V + E).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> eventualSafeNodes(vector<vector<int>>& g) {
    int n = g.size();
    vector<vector<int>> rev(n);
    vector<int> outd(n);
    for (int u = 0; u < n; ++u) {
        outd[u] = g[u].size();
        for (int v : g[u]) rev[v].push_back(u);
    }
    queue<int> q;
    for (int i = 0; i < n; ++i) if (!outd[i]) q.push(i);
    vector<int> safe;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        safe.push_back(u);
        for (int v : rev[u]) if (--outd[v] == 0) q.push(v);
    }
    sort(safe.begin(), safe.end());
    return safe;
}
```

## Follow-up Questions
- Detect cycle nodes vs safe nodes.
- Count of strongly connected components.
- Nodes from which all paths end in a target set.
