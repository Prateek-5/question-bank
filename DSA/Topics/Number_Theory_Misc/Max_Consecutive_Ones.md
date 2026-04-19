# Max Consecutive Ones

## Problem Link
https://leetcode.com/problems/max-consecutive-ones/

## Topic
Number Theory Misc

## Core Concept
Running counter reset on 0.

## Intuition
Track the length of the current streak of 1s; update the max when it grows.

## Detailed Explanation
cur=0, best=0. For each x: cur = x?cur+1:0; best=max(best,cur).

## Dry Run
nums=[1,1,0,1,1,1]. Streaks 2 then 3 → best=3.

## Approach
Single pass.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findMaxConsecutiveOnes(vector<int>& a) {
    int cur = 0, best = 0;
    for (int x : a) { cur = x ? cur + 1 : 0; best = max(best, cur); }
    return best;
}
```

## Follow-up Questions
- Flip at most k zeros (sliding window).
- Longest run of any value.
- 2D grid variant.
