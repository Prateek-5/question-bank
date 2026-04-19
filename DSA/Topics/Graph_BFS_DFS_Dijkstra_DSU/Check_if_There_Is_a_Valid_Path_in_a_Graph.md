# Check if There Is a Valid Path in a Graph

## Problem Link
https://leetcode.com/problems/check-if-there-is-a-valid-path-in-a-grid/description/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Union-Find connectivity test between source and destination.

## Intuition
A valid path between two nodes exists iff they are in the same connected component. DSU answers this in near-constant time after processing all edges.

## Detailed Explanation
Build DSU over n nodes; union each edge's endpoints. Return find(source)==find(destination).

## Dry Run
n=3, edges=[[0,1],[1,2],[2,0]], src=0, dst=2. Union 0-1, 1-2, 2-0. find(0)==find(2) → true.

## Approach
DSU is simplest; BFS/DFS also works in O(V+E).

## Time and Space Complexity
Time: O(V+E α). Space: O(V).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct DSU { vector<int> p; DSU(int n):p(n){iota(p.begin(),p.end(),0);} int f(int x){return p[x]==x?x:p[x]=f(p[x]);} void u(int a,int b){p[f(a)]=f(b);} };

bool validPath(int n, vector<vector<int>>& edges, int src, int dst) {
    DSU d(n);
    for (auto& e : edges) d.u(e[0], e[1]);
    return d.f(src) == d.f(dst);
}
```

## Follow-up Questions
- Return the actual path.
- Shortest path (BFS).
- Dynamic connectivity with deletions (harder).
