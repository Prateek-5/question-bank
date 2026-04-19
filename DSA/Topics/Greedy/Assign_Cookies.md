# Assign Cookies

## Problem Link
https://leetcode.com/problems/assign-cookies/

## Topic
Greedy

## Core Concept
Greedy two-pointer — pair smallest sufficient cookie with smallest greed.

## Intuition
Satisfy the least greedy child with the smallest cookie that fits — saves bigger cookies for greedier children.

## Detailed Explanation
Sort greed g and cookies s. i=j=0. If s[j]>=g[i], satisfy i++. Always j++. Answer = i.

## Dry Run
g=[1,2,3], s=[1,1]. j=0,i=0 match→i=1. j=1,i=1: 1<2 → skip. End. Satisfied=1.

## Approach
Two-pointer sweep.

## Time and Space Complexity
Time: O(n log n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findContentChildren(vector<int>& g, vector<int>& s) {
    sort(g.begin(),g.end()); sort(s.begin(),s.end());
    int i = 0, j = 0;
    while (i < (int)g.size() && j < (int)s.size()) {
        if (s[j] >= g[i]) i++;
        j++;
    }
    return i;
}
```

## Follow-up Questions
- Multiple cookies per child.
- Cost per cookie — minimize cost to satisfy.
- Online version with streaming children.
