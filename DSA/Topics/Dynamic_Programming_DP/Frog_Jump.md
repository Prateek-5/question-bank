# Frog Jump

## Problem Link
https://leetcode.com/problems/frog-jump/

## Topic
Dynamic Programming DP

## Core Concept
DP with states (position, last-jump); transitions to k-1, k, k+1.

## Intuition
Frog at stone i with last jump k can jump to stones i+k-1, i+k, i+k+1. Track reachable (stone, jump size) pairs.

## Detailed Explanation
Map stone → set of jump sizes that reach it. From each (stone, k), attempt to reach stone+k-1, stone+k, stone+k+1. Check if last stone is reachable.

## Dry Run
stones=[0,1,3,5,6,8,12,17]. From 0 with k=0 → 1(k=1). Continue reaching 17.

## Approach
Memoization or BFS.

## Time and Space Complexity
Time: O(n²). Space: O(n²).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool canCross(vector<int>& s) {
    unordered_map<int, unordered_set<int>> d;
    for (int x : s) d[x] = {};
    d[0].insert(0);
    for (int x : s) for (int k : d[x])
        for (int dk : {k-1, k, k+1}) if (dk > 0 && d.count(x+dk)) d[x+dk].insert(dk);
    return !d[s.back()].empty();
}
```

## Follow-up Questions
- Minimum number of jumps.
- Find a valid sequence of stones.
- Allow negative jumps (back).
