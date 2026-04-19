# Capacity To Ship Packages Within D Days

## Problem Link
https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/

## Topic
Searching Binary Search

## Core Concept
Binary search on answer — minimum ship capacity.

## Intuition
Capacity monotonic: if capacity C works, any C' > C also works. Binary search capacity in [max(weights), sum(weights)].

## Detailed Explanation
Check function: greedy fill day by day; if load + w > cap, start new day. Feasible iff days used <= D.

## Dry Run
weights=[1,2,3,4,5,6,7,8,9,10], D=5. Answer 15 (binary search between 10 and 55).

## Approach
Binary search + greedy feasibility.

## Time and Space Complexity
Time: O(n log(sum)). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int shipWithinDays(vector<int>& w, int D) {
    int lo = *max_element(w.begin(), w.end()), hi = accumulate(w.begin(), w.end(), 0);
    auto feasible = [&](int cap) {
        int days = 1, load = 0;
        for (int x : w) {
            if (load + x > cap) { days++; load = 0; }
            load += x;
        }
        return days <= D;
    };
    while (lo < hi) {
        int m = (lo + hi) / 2;
        if (feasible(m)) hi = m; else lo = m + 1;
    }
    return lo;
}
```

## Follow-up Questions
- Fixed capacity, find min days.
- Variable daily capacities.
- Koko Eating Bananas / Split Array Largest Sum.
