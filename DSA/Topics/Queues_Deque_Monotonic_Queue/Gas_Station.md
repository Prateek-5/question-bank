# Gas Station

## Problem Link
https://leetcode.com/problems/gas-station/

## Topic
Queues Deque Monotonic Queue

## Core Concept
Greedy running-tank: if total gas ≥ total cost, starting station is the one after the last negative prefix.

## Intuition
If total gas - total cost < 0, no solution. Else a valid starting point exists; resetting start whenever tank goes negative finds it.

## Detailed Explanation
total=0, tank=0, start=0. For i: diff=gas[i]-cost[i]; total+=diff; tank+=diff; if tank<0: start=i+1, tank=0. Return total<0 ? -1 : start.

## Dry Run
gas=[1,2,3,4,5], cost=[3,4,5,1,2]. total=3. Reset points; final start=3.

## Approach
Single-pass greedy.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int canCompleteCircuit(vector<int>& g, vector<int>& c) {
    int tot = 0, tank = 0, start = 0;
    for (int i = 0; i < (int)g.size(); ++i) {
        int d = g[i] - c[i];
        tot += d; tank += d;
        if (tank < 0) { start = i + 1; tank = 0; }
    }
    return tot < 0 ? -1 : start;
}
```

## Follow-up Questions
- Multiple valid starts — find all.
- Minimum refill stops given range.
- Weighted gas tanks.
