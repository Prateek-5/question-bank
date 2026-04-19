# Network Delay Time

## Problem Link
https://leetcode.com/problems/network-delay-time/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Single-source shortest path (Dijkstra).

## Intuition
Signal propagates to all reachable nodes; the total time is the max of shortest distances from k. If any node is unreachable, return -1.

## Detailed Explanation
Build adjacency with weights. Run Dijkstra from k. After relaxation, the answer is max of dist[] if all are finite, else -1.

## Dry Run
times=[[2,1,1],[2,3,1],[3,4,1]], k=2. dist[2]=0, [1]=1, [3]=1, [4]=2. Max=2.

## Approach
Standard min-heap Dijkstra.

## Time and Space Complexity
Time: O((V+E) log V). Space: O(V+E).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int networkDelayTime(vector<vector<int>>& times, int n, int k) {
    vector<vector<pair<int,int>>> g(n + 1);
    for (auto& t : times) g[t[0]].push_back({t[1], t[2]});
    vector<int> dist(n + 1, INT_MAX); dist[k] = 0;
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    pq.push({0, k});
    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        if (d > dist[u]) continue;
        for (auto [v, w] : g[u]) if (d + w < dist[v]) {
            dist[v] = d + w; pq.push({dist[v], v});
        }
    }
    int ans = 0;
    for (int i = 1; i <= n; ++i) {
        if (dist[i] == INT_MAX) return -1;
        ans = max(ans, dist[i]);
    }
    return ans;
}
```

## Follow-up Questions
- Weighted with negative edges → Bellman-Ford.
- Return the actual delay tree.
- Multiple sources → multi-source Dijkstra.
