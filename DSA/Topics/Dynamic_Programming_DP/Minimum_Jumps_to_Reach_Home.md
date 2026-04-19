# Minimum Jumps to Reach Home

## Problem Link
https://leetcode.com/problems/minimum-jumps-to-reach-home/description/

## Topic
Dynamic Programming DP

## Core Concept
BFS on (position, direction) with forbidden squares.

## Intuition
Bug's state is (pos, lastDir). BFS expands forward b or backward a (only once consecutively). Track visited pairs.

## Detailed Explanation
Queue (pos, backJust, steps). Forward move: pos+a; if valid push. Backward move: pos-b if backJust==0 and pos-b>=0 and not forbidden. Upper bound pos<=6000 approx.

## Dry Run
forbidden=[14,4,18,1,15], a=3,b=15, x=9. BFS finds 3 jumps.

## Approach
BFS with (position, last-direction) state.

## Time and Space Complexity
Time: O(bound). Space: O(bound).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int minimumJumps(vector<int>& f, int a, int b, int x) {
    set<int> forb(f.begin(), f.end());
    const int LIM = 6000;
    queue<tuple<int,int,int>> q; q.push({0, 0, 0});
    set<pair<int,int>> seen; seen.insert({0, 0});
    while (!q.empty()) {
        auto [p, back, s] = q.front(); q.pop();
        if (p == x) return s;
        int nf = p + a;
        if (nf <= LIM && !forb.count(nf) && !seen.count({nf, 0})) { seen.insert({nf,0}); q.push({nf,0,s+1}); }
        int nb = p - b;
        if (!back && nb >= 0 && !forb.count(nb) && !seen.count({nb, 1})) { seen.insert({nb,1}); q.push({nb,1,s+1}); }
    }
    return -1;
}
```

## Follow-up Questions
- Tighten the limit.
- Continuous variant.
- Weighted jumps.
