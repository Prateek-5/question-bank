# Find the Town Judge

## Problem Link
https://leetcode.com/problems/find-the-town-judge/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
In/out-degree counting.

## Intuition
The judge is trusted by n-1 people (in-degree n-1) and trusts nobody (out-degree 0). Track in- and out-degrees and find the node satisfying both.

## Detailed Explanation
For each trust (a,b): out[a]++, in[b]++. The judge i satisfies in[i]=n-1 and out[i]=0. If exactly one such exists, return it; else -1.

## Dry Run
n=3, trust=[[1,3],[2,3]]. in=[_,0,0,2], out=[_,1,1,0]. Node 3: in=2=n-1, out=0 → judge.

## Approach
Two arrays, one scan.

## Time and Space Complexity
Time: O(n + E). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findJudge(int n, vector<vector<int>>& trust) {
    vector<int> score(n + 1, 0);
    for (auto& t : trust) { score[t[0]]--; score[t[1]]++; }
    for (int i = 1; i <= n; ++i) if (score[i] == n - 1) return i;
    return -1;
}
```

## Follow-up Questions
- Multiple judges (all nodes with in-degree n-1 and out-degree 0).
- Trust chains (transitive).
- Dynamic updates — does the judge change?
