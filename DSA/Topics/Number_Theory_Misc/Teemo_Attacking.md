# Teemo Attacking

## Problem Link
https://leetcode.com/problems/teemo-attacking/description/

## Topic
Number Theory Misc

## Core Concept
Sum of overlap-adjusted durations.

## Intuition
Each attack poisons for duration, but a new attack before the previous one ends just resets the end. Accumulate min(duration, nextStart - thisStart).

## Detailed Explanation
For i=0..n-2: add min(duration, timeSeries[i+1] - timeSeries[i]). Add duration for last attack.

## Dry Run
timeSeries=[1,4], duration=2. min(2, 3)=2, +2 last = 4.

## Approach
Single pass.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findPoisonedDuration(vector<int>& t, int d) {
    int total = 0;
    for (int i = 0; i + 1 < (int)t.size(); ++i)
        total += min(d, t[i+1] - t[i]);
    return total + (t.empty() ? 0 : d);
}
```

## Follow-up Questions
- Variable per-attack duration.
- Minimum attacks to poison fully.
- Interval merging generalization.
