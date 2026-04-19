# Shortest Path in an Undirected Graph

## Problem Link
https://www.geeksforgeeks.org/problems/shortest-path-in-weighted-undirected-graph/1

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Unweighted BFS from source.

## Intuition
BFS layers correspond to hop-counts. The shortest path length from s to any node is the level it's first dequeued.

## Detailed Explanation
Initialize dist[s]=0, others -1. BFS; for each neighbor with dist==-1 set dist = dist[u]+1 and enqueue.

## Dry Run
Graph 0-1-2, 0-3. BFS from 0: level 0 {0}, level 1 {1,3}, level 2 {2}. dist=[0,1,2,1].

## Approach
Standard BFS.

## Time and Space Complexity
Time: O(V+E). Space: O(V).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> shortestPath(int n, vector<vector<int>>& edges, int src) {
    vector<vector<int>> g(n);
    for (auto& e : edges) { g[e[0]].push_back(e[1]); g[e[1]].push_back(e[0]); }
    vector<int> d(n, -1); d[src] = 0;
    queue<int> q; q.push(src);
    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int v : g[u]) if (d[v] == -1) { d[v] = d[u] + 1; q.push(v); }
    }
    return d;
}
```

## Follow-up Questions
- Return parent pointers to reconstruct paths.
- Weighted variant uses Dijkstra.
- BFS from multiple sources.
