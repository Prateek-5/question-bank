# Magnetic Force Between Two Balls

## Problem Link
https://leetcode.com/problems/magnetic-force-between-two-balls/

## Topic
Searching Binary Search

## Core Concept
Binary search on minimum distance.

## Intuition
Monotonic: if gap g is feasible (can place m balls with pairwise distance ≥ g), any smaller g is feasible. Binary search the largest feasible g.

## Detailed Explanation
Sort positions. Feasibility(g): greedy place balls; start with first, then next whose position ≥ last placed + g. Count placed; feasible if >= m.

## Dry Run
position=[1,2,3,4,7], m=3. Search in [1, max diff]. g=3 feasible (1,4,7). g=4 not. Answer=3.

## Approach
Sort + binary search + greedy.

## Time and Space Complexity
Time: O(n log range). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maxDistance(vector<int>& p, int m) {
    sort(p.begin(), p.end());
    int lo = 1, hi = p.back() - p.front();
    auto ok = [&](int g) {
        int cnt = 1, last = p[0];
        for (int i = 1; i < (int)p.size(); ++i)
            if (p[i] - last >= g) { cnt++; last = p[i]; }
        return cnt >= m;
    };
    while (lo < hi) {
        int md = (lo + hi + 1) / 2;
        if (ok(md)) lo = md; else hi = md - 1;
    }
    return lo;
}
```

## Follow-up Questions
- Minimum distance when balls can repel.
- Variable ball sizes.
- Maximize sum of min-distances.
