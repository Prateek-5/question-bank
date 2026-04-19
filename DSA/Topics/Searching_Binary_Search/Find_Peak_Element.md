# Find Peak Element

## Problem Link
https://leetcode.com/problems/find-peak-element/

## Topic
Searching Binary Search

## Core Concept
Binary search using neighbor comparison.

## Intuition
An element is a peak iff greater than both neighbors. If nums[m] < nums[m+1], a peak exists in [m+1, n-1]; else in [0, m].

## Detailed Explanation
lo=0, hi=n-1. While lo<hi: m=(lo+hi)/2. If nums[m] < nums[m+1] lo=m+1 else hi=m. Return lo.

## Dry Run
nums=[1,2,3,1]. m=1:2<3 → lo=2. m=2: 3>1 → hi=2. Return 2.

## Approach
Binary search O(log n).

## Time and Space Complexity
Time: O(log n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findPeakElement(vector<int>& a) {
    int lo = 0, hi = a.size() - 1;
    while (lo < hi) {
        int m = (lo + hi) / 2;
        if (a[m] < a[m+1]) lo = m + 1;
        else hi = m;
    }
    return lo;
}
```

## Follow-up Questions
- Peak in 2D matrix.
- Multiple peaks (return all).
- Bitonic array peak.
