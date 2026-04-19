# Minimum Weight Cycle

## Problem Link
https://www.geeksforgeeks.org/problems/minimum-weight-cycle/1

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
For each edge (u,v,w), remove it and compute shortest u→v path; answer = min over edges of (w + shortest_path).

## Intuition
A minimum-weight cycle must contain at least one edge; enumerating each possible 'closing' edge and finding the shortest alternative route yields the minimum cycle weight.

## Detailed Explanation
For each edge (u,v,w): temporarily remove it, run Dijkstra from u to v, cycle weight = w + dist. Track minimum. Return INF if no cycle.

## Dry Run
Edges {(0,1,1),(1,2,1),(2,0,3)}. Remove (0,1,1): path 0→2→1 = 4, cycle=5. Remove (1,2,1): 1→0→2=4, cycle=5. Remove (2,0,3): 2→1→0=2, cycle=5. Answer=5.

## Approach
O(E · (V+E) log V). For small graphs use Floyd-Warshall based O(V³).

## Time and Space Complexity
Time: O(V·E log V) with Dijkstra.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int dijk(vector<vector<pair<int,int>>>& g, int s, int t, int banU, int banV) {
    int n = g.size();
    vector<int> d(n, INT_MAX); d[s] = 0;
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    pq.push({0, s});
    while (!pq.empty()) {
        auto [dd, u] = pq.top(); pq.pop();
        if (dd > d[u]) continue;
        for (auto [v, w] : g[u]) {
            if ((u==banU && v==banV) || (u==banV && v==banU)) continue;
            if (dd + w < d[v]) { d[v] = dd + w; pq.push({d[v], v}); }
        }
    }
    return d[t];
}
int minWeightCycle(int n, vector<vector<int>>& edges) {
    vector<vector<pair<int,int>>> g(n);
    for (auto& e : edges) { g[e[0]].push_back({e[1], e[2]}); g[e[1]].push_back({e[0], e[2]}); }
    int best = INT_MAX;
    for (auto& e : edges) {
        int d = dijk(g, e[0], e[1], e[0], e[1]);
        if (d != INT_MAX) best = min(best, d + e[2]);
    }
    return best;
}
```

## Follow-up Questions
- Directed graph minimum cycle.
- Only positive weights guaranteed? Use BFS for unweighted.
- Minimum mean cycle (Karp's algorithm).
