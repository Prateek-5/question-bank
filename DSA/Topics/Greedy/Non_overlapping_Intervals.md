# Non-overlapping Intervals

## Problem Link
https://leetcode.com/problems/non-overlapping-intervals/

## Topic
Greedy

## Core Concept
Greedy by earliest end time — classic activity-selection.

## Intuition
To remove the minimum number of intervals, keep as many non-overlapping as possible. Sorting by end time and always picking the interval ending earliest maximizes the count kept.

## Detailed Explanation
Sort intervals by end. Iterate; if the current start < last end, it overlaps → remove (answer++). Else accept and update last end.

## Dry Run
Intervals [[1,2],[2,3],[3,4],[1,3]]. Sort by end: [[1,2],[2,3],[1,3],[3,4]]. Keep [1,2]. [2,3] start>=last end 2 → keep. [1,3] start<3 → remove. [3,4] keep. Removed=1.

## Approach
Sort + one scan.

## Time and Space Complexity
Time: O(n log n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int eraseOverlapIntervals(vector<vector<int>>& a) {
    sort(a.begin(), a.end(), [](auto& x, auto& y){ return x[1] < y[1]; });
    int cnt = 0, end = INT_MIN;
    for (auto& iv : a) {
        if (iv[0] < end) cnt++;
        else end = iv[1];
    }
    return cnt;
}
```

## Follow-up Questions
- Return the kept intervals.
- Weighted interval scheduling (DP).
- Minimum number of rooms (sweep line).
