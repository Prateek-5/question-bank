# Maximum Subarray

## Problem Link
https://leetcode.com/problems/maximum-subarray/

## Topic
Dynamic Programming DP

## Core Concept
Kadane's algorithm — running-sum reset.

## Intuition
Walk the array tracking current subarray sum; reset to current element whenever the running sum becomes negative.

## Detailed Explanation
cur=best=nums[0]. For i from 1: cur=max(nums[i], cur+nums[i]); best=max(best,cur).

## Dry Run
nums=[-2,1,-3,4,-1,2,1,-5,4] → best=6.

## Approach
Linear Kadane.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maxSubArray(vector<int>& a) {
    int cur = a[0], best = a[0];
    for (int i = 1; i < (int)a.size(); ++i) { cur = max(a[i], cur + a[i]); best = max(best, cur); }
    return best;
}
```

## Follow-up Questions
- Return the actual subarray.
- Circular subarray maximum.
- 2D Kadane.
