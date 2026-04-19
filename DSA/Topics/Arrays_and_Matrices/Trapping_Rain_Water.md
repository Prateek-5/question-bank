# Trapping Rain Water

## Problem Link
https://leetcode.com/problems/trapping-rain-water/

## Topic
Arrays and Matrices

## Core Concept
Two-pointer sweep comparing left_max and right_max.

## Intuition
Water above each bar equals min(max_left, max_right) − height. Moving pointer from the smaller side lets us compute contribution instantly.

## Detailed Explanation
l=0, r=n-1, ml=mr=0. While l<r: if h[l]<h[r]: if h[l]>=ml ml=h[l] else water+=ml-h[l]; l++. Symmetric for r.

## Dry Run
height=[0,1,0,2,1,0,1,3,2,1,2,1]. Answer=6.

## Approach
Two pointers O(n).

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int trap(vector<int>& h) {
    int l = 0, r = h.size() - 1, ml = 0, mr = 0, water = 0;
    while (l < r) {
        if (h[l] < h[r]) { ml = max(ml, h[l]); water += ml - h[l]; l++; }
        else { mr = max(mr, h[r]); water += mr - h[r]; r--; }
    }
    return water;
}
```

## Follow-up Questions
- Trapping Rain Water II (2D, priority queue BFS).
- Return the water level for each bar.
- Variable cell widths.
