# Open the Lock

## Problem Link
https://leetcode.com/problems/open-the-lock/

## Topic
Sorting Divide and Conquer

## Core Concept
BFS over states (4-digit combinations).

## Intuition
Each dial state has 8 neighbors (each wheel +1 or -1). BFS from '0000' avoiding deadends, stopping at target.

## Detailed Explanation
Queue initial '0000'. Generate 8 neighbors per state; skip visited/deadend. Levels = minimum moves.

## Dry Run
deadends=['0201','0101','0102','1212','2002'], target='0202'. BFS yields 6.

## Approach
BFS on 10000 states.

## Time and Space Complexity
Time: O(10000). Space: O(10000).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int openLock(vector<string>& dead, string target) {
    unordered_set<string> blocked(dead.begin(), dead.end());
    if (blocked.count("0000")) return -1;
    if (target == "0000") return 0;
    queue<pair<string,int>> q; q.push({"0000", 0});
    blocked.insert("0000");
    while (!q.empty()) {
        auto [s, d] = q.front(); q.pop();
        for (int i = 0; i < 4; ++i) for (int dd : {-1, 1}) {
            string t = s;
            t[i] = ((t[i] - '0' + dd + 10) % 10) + '0';
            if (blocked.count(t)) continue;
            if (t == target) return d + 1;
            blocked.insert(t);
            q.push({t, d + 1});
        }
    }
    return -1;
}
```

## Follow-up Questions
- Bi-directional BFS for speed.
- Weighted moves.
- N-dial variant.
