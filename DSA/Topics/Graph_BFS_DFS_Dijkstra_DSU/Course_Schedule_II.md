# Course Schedule II

## Problem Link
https://leetcode.com/problems/course-schedule-ii/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Topological sort via Kahn's algorithm (BFS on in-degree).

## Intuition
Courses with prerequisites form a DAG. A valid order is any topological ordering. Kahn's BFS repeatedly takes zero-indegree nodes, yielding a valid order or detecting a cycle (when not all nodes processed).

## Detailed Explanation
Compute in-degree for each course. Queue all zero-indegree nodes. Pop, append to order, and for each outgoing edge decrement indegree — push if it hits 0. If final order size < n, return [] (cycle).

## Dry Run
n=4, prereqs=[[1,0],[2,0],[3,1],[3,2]]. In-deg: [0,1,1,2]. Queue {0}. Pop 0 → order=[0], decrement 1 and 2 to 0, push both. Pop 1 → order=[0,1], 3→1. Pop 2 → order=[0,1,2], 3→0, push. Pop 3 → order=[0,1,2,3].

## Approach
Kahn BFS — handles cycle detection naturally.

## Time and Space Complexity
Time: O(V + E). Space: O(V + E).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> findOrder(int n, vector<vector<int>>& pre) {
    vector<vector<int>> g(n);
    vector<int> ind(n, 0);
    for (auto& p : pre) { g[p[1]].push_back(p[0]); ind[p[0]]++; }
    queue<int> q;
    for (int i = 0; i < n; ++i) if (!ind[i]) q.push(i);
    vector<int> order;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        order.push_back(u);
        for (int v : g[u]) if (--ind[v] == 0) q.push(v);
    }
    return (int)order.size() == n ? order : vector<int>{};
}
```

## Follow-up Questions
- Course Schedule I (just detect feasibility).
- DFS-based topo sort with cycle detection.
- Parallel course scheduling — minimum semesters.
