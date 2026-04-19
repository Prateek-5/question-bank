# Is Graph Bipartite

## Problem Link
https://leetcode.com/problems/is-graph-bipartite/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Two-coloring via BFS/DFS.

## Intuition
A graph is bipartite iff nodes can be 2-colored so adjacent nodes differ in color. BFS from each unvisited node assigns alternating colors; a conflict means non-bipartite (odd cycle).

## Detailed Explanation
color[i] ∈ {0, 1, -1}. For each uncolored node start BFS: color root 0, for each neighbor assign opposite color and push. If a neighbor is already colored the same, return false.

## Dry Run
graph=[[1,3],[0,2],[1,3],[0,2]]. BFS from 0: color 0=A, 1=B, 3=B. From 1: color 2=A. No conflict → true.

## Approach
BFS coloring across all components.

## Time and Space Complexity
Time: O(V+E). Space: O(V).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool isBipartite(vector<vector<int>>& g) {
    int n = g.size();
    vector<int> col(n, -1);
    for (int s = 0; s < n; ++s) if (col[s] == -1) {
        queue<int> q; q.push(s); col[s] = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (int v : g[u]) {
                if (col[v] == -1) { col[v] = 1 - col[u]; q.push(v); }
                else if (col[v] == col[u]) return false;
            }
        }
    }
    return true;
}
```

## Follow-up Questions
- Find the two partitions.
- DSU-based check.
- k-colorability (NP-hard for k≥3).
