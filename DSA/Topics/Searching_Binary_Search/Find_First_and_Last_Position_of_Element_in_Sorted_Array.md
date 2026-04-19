# Find First and Last Position of Element in Sorted Array

## Problem Link
https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/

## Topic
Searching Binary Search

## Core Concept
Two binary searches — lower_bound and upper_bound.

## Intuition
Lower bound gives first index with value ≥ target, upper bound first index > target. If lower_bound's value matches target, positions are (lb, ub-1).

## Detailed Explanation
Use std::lower_bound and std::upper_bound on the sorted array.

## Dry Run
nums=[5,7,7,8,8,10], target=8. lb=3, ub=5 → [3,4].

## Approach
STL binary search helpers.

## Time and Space Complexity
Time: O(log n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> searchRange(vector<int>& a, int t) {
    auto lb = lower_bound(a.begin(), a.end(), t);
    auto ub = upper_bound(a.begin(), a.end(), t);
    if (lb == a.end() || *lb != t) return {-1, -1};
    return {(int)(lb - a.begin()), (int)(ub - a.begin() - 1)};
}
```

## Follow-up Questions
- Count occurrences (ub-lb).
- Find n-th occurrence by binary searching index.
- Works on sorted linked list?
