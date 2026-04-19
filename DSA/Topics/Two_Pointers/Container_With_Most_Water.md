# Container With Most Water

## Problem Link
https://leetcode.com/problems/container-with-most-water/

## Topic
Two Pointers

## Core Concept
Two pointers — shrink from the side with smaller height.

## Intuition
Area is (r-l)*min(h[l],h[r]). Moving the taller pointer inward can never increase the area since the min height won't grow and width shrinks; so always move the smaller side.

## Detailed Explanation
l=0, r=n-1. Track max area; while l<r: compute area; if h[l]<h[r] l++ else r--.

## Dry Run
h=[1,8,6,2,5,4,8,3,7]. Max area=49 (indices 1..8).

## Approach
Two pointers O(n).

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maxArea(vector<int>& h) {
    int l = 0, r = h.size() - 1, best = 0;
    while (l < r) {
        best = max(best, (r - l) * min(h[l], h[r]));
        if (h[l] < h[r]) l++; else r--;
    }
    return best;
}
```

## Follow-up Questions
- Widths non-uniform between indices.
- Max area with at most k modifications.
- 3D container problem.
