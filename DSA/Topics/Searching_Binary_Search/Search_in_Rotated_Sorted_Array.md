# Search in Rotated Sorted Array

## Problem Link
https://leetcode.com/problems/search-in-rotated-sorted-array/

## Topic
Searching Binary Search

## Core Concept
Binary search with rotation detection.

## Intuition
At each midpoint, one half is sorted. Check which half is sorted and whether target lies in it; discard the other half.

## Detailed Explanation
lo=0, hi=n-1. Loop: m=(lo+hi)/2. If a[m]==target return m. If a[lo]<=a[m] (left sorted): if a[lo]<=target<a[m] hi=m-1 else lo=m+1. Else right sorted: if a[m]<target<=a[hi] lo=m+1 else hi=m-1.

## Dry Run
nums=[4,5,6,7,0,1,2], target=0. m=3:7≠0, left sorted [4..7], 0 not in it → lo=4. m=5:1≠0, left sorted [0..1], 0 in it → hi=4. m=4: 0 found.

## Approach
Modified binary search.

## Time and Space Complexity
Time: O(log n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int search(vector<int>& a, int t) {
    int lo = 0, hi = a.size() - 1;
    while (lo <= hi) {
        int m = (lo + hi) / 2;
        if (a[m] == t) return m;
        if (a[lo] <= a[m]) {
            if (a[lo] <= t && t < a[m]) hi = m - 1;
            else lo = m + 1;
        } else {
            if (a[m] < t && t <= a[hi]) lo = m + 1;
            else hi = m - 1;
        }
    }
    return -1;
}
```

## Follow-up Questions
- Variant with duplicates (harder).
- Find min in rotated sorted array.
- Multiple rotations.
