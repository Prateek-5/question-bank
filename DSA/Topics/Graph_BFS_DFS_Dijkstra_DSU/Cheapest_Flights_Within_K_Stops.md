# Cheapest Flights Within K Stops

## Problem Link
https://leetcode.com/problems/cheapest-flights-within-k-stops/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Bellman-Ford limited to K+1 edge relaxations, or modified Dijkstra tracking stops.

## Intuition
We can take at most K intermediate stops = K+1 edges. Bellman-Ford performs one edge-relaxation pass per allowable edge, so K+1 passes compute shortest paths with at most K+1 edges.

## Detailed Explanation
Init dist[src]=0. Repeat K+1 times: snapshot dist, for each edge (u,v,w) update newDist[v] = min(newDist[v], snapshot[u]+w). Return dist[dst] or -1 if unreachable. Snapshotting prevents using two edges in one pass.

## Dry Run
n=3, flights=[[0,1,100],[1,2,100],[0,2,500]], src=0, dst=2, K=1. Pass 1: dist=[0,100,500]. Pass 2: dist=[0,100,200]. Answer=200.

## Approach
Bellman-Ford with snapshot (cleanest) or Dijkstra with (cost, node, stops) state.

## Time and Space Complexity
Time: O((K+1)·E). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findCheapestPrice(int n, vector<vector<int>>& f, int src, int dst, int k) {
    const int INF = 1e9;
    vector<int> dist(n, INF); dist[src] = 0;
    for (int i = 0; i <= k; ++i) {
        vector<int> nd = dist;
        for (auto& e : f) {
            if (dist[e[0]] == INF) continue;
            nd[e[1]] = min(nd[e[1]], dist[e[0]] + e[2]);
        }
        dist = nd;
    }
    return dist[dst] == INF ? -1 : dist[dst];
}
```

## Follow-up Questions
- Return the actual path.
- Variant: at most K *hops* (edges).
- Negative-weight edges (Bellman-Ford already handles).
