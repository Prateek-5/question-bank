# Redundant Connection

## Problem Link
https://leetcode.com/problems/redundant-connection/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Union-Find — first edge whose endpoints are already connected creates a cycle.

## Intuition
A tree on n nodes has n-1 edges. The input has n edges → exactly one extra edge creates a cycle. That's the one whose endpoints are already in the same DSU component.

## Detailed Explanation
Iterate edges in order; for each edge, if find(u)==find(v), return it. Otherwise union.

## Dry Run
edges=[[1,2],[1,3],[2,3]]. Union 1-2, 1-3. On (2,3): find(2)==find(3) → return [2,3].

## Approach
Single DSU pass.

## Time and Space Complexity
Time: O(N α). Space: O(N).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct DSU { vector<int> p; DSU(int n):p(n){iota(p.begin(),p.end(),0);} int f(int x){return p[x]==x?x:p[x]=f(p[x]);} };

vector<int> findRedundantConnection(vector<vector<int>>& edges) {
    DSU d(edges.size() + 1);
    for (auto& e : edges) {
        int a = d.f(e[0]), b = d.f(e[1]);
        if (a == b) return e;
        d.p[a] = b;
    }
    return {};
}
```

## Follow-up Questions
- Directed variant (Redundant Connection II).
- If multiple cycles exist, find the earliest/latest.
- Weighted: remove the heaviest edge in the cycle.
