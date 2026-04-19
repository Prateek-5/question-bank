# Keys and Rooms

## Problem Link
https://leetcode.com/problems/keys-and-rooms/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
BFS/DFS connectivity from room 0.

## Intuition
Treat rooms as nodes and keys as directed edges. Can we reach all rooms from room 0? Standard traversal.

## Detailed Explanation
DFS from 0, marking visited rooms. Each visit pushes all keys found. At end, check all rooms visited.

## Dry Run
rooms=[[1],[2],[3],[]]. DFS 0→1→2→3. All visited → true.

## Approach
Iterative DFS using a stack.

## Time and Space Complexity
Time: O(V+E). Space: O(V).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool canVisitAllRooms(vector<vector<int>>& rooms) {
    int n = rooms.size();
    vector<int> seen(n, 0);
    stack<int> st; st.push(0); seen[0] = 1;
    int cnt = 1;
    while (!st.empty()) {
        int u = st.top(); st.pop();
        for (int v : rooms[u]) if (!seen[v]) { seen[v] = 1; cnt++; st.push(v); }
    }
    return cnt == n;
}
```

## Follow-up Questions
- Minimum keys to visit all rooms.
- Variant: each key unlocks once.
- Weighted: time cost per room.
