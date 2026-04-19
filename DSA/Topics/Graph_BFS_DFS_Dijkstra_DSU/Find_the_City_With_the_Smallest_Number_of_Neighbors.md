# Find the City With the Smallest Number of Neighbors

## Problem Link
https://leetcode.com/problems/find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
All-pairs shortest paths via Floyd-Warshall under distance threshold.

## Intuition
We want, for each city, how many others are within threshold distance. With small n (≤100), Floyd-Warshall O(n³) is fine. Count reachable cities per node and pick the city with the smallest count, breaking ties by larger index.

## Detailed Explanation
Init dist[i][i]=0, dist[u][v]=w for edges (both directions). For k,i,j: dist[i][j]=min(dist[i][j], dist[i][k]+dist[k][j]). For each node, count j with dist[i][j]<=threshold. Output the node with min count (largest index on tie).

## Dry Run
n=4, edges=[[0,1,3],[1,2,1],[1,3,4],[2,3,1]], threshold=4. After FW: from 3, neighbors within 4 = {1,2} (count 2). From 0, {1,2} (count 2). Tie → choose larger idx → 3.

## Approach
Floyd-Warshall then scan counts.

## Time and Space Complexity
Time: O(n³). Space: O(n²).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findTheCity(int n, vector<vector<int>>& edges, int t) {
    const int INF = 1e9;
    vector<vector<int>> d(n, vector<int>(n, INF));
    for (int i=0;i<n;i++) d[i][i]=0;
    for (auto& e : edges) { d[e[0]][e[1]] = e[2]; d[e[1]][e[0]] = e[2]; }
    for (int k=0;k<n;k++) for (int i=0;i<n;i++) for (int j=0;j<n;j++)
        if (d[i][k]+d[k][j] < d[i][j]) d[i][j] = d[i][k]+d[k][j];
    int best = -1, cnt = INT_MAX;
    for (int i=0;i<n;i++) {
        int c = 0;
        for (int j=0;j<n;j++) if (i!=j && d[i][j]<=t) c++;
        if (c <= cnt) { cnt = c; best = i; }
    }
    return best;
}
```

## Follow-up Questions
- Use n Dijkstras for O(n·E log n).
- What if threshold queries come online?
- Maximize instead of minimize neighbor count.
