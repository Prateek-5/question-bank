# Most Stones Removed with Same Row or Column

## Problem Link
https://leetcode.com/problems/most-stones-removed-with-same-row-or-column/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
DSU grouping stones that share a row or column; answer is n - components.

## Intuition
Stones in the same row/column can all be removed except one (you need one stone remaining as the last). So within each connected group (via shared row/column) you remove size-1 stones. Total = n - #components.

## Detailed Explanation
Union stones that share a row or column (map each row/column index to its first stone). Count DSU components. Answer = n - components.

## Dry Run
stones = [[0,0],[0,1],[1,0],[1,2],[2,1],[2,2]]. All in one component → answer = 6 - 1 = 5.

## Approach
DSU over stone indices with row/column index mapping.

## Time and Space Complexity
Time: O(n α). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct DSU { vector<int> p; DSU(int n):p(n){iota(p.begin(),p.end(),0);} int f(int x){return p[x]==x?x:p[x]=f(p[x]);} void u(int a,int b){p[f(a)]=f(b);} };

int removeStones(vector<vector<int>>& s) {
    int n = s.size();
    DSU d(n);
    unordered_map<int,int> rowMap, colMap;
    for (int i = 0; i < n; ++i) {
        int r = s[i][0], c = s[i][1];
        if (rowMap.count(r)) d.u(i, rowMap[r]); else rowMap[r] = i;
        if (colMap.count(c)) d.u(i, colMap[c]); else colMap[c] = i;
    }
    int comps = 0;
    for (int i = 0; i < n; ++i) if (d.f(i) == i) comps++;
    return n - comps;
}
```

## Follow-up Questions
- Maximum stones removed given removal constraints.
- Weighted stones.
- Queries on dynamic stone addition/removal.
