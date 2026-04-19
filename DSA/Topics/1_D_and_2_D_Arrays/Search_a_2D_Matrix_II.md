# Search a 2D Matrix II

## Problem Link
https://leetcode.com/problems/search-a-2d-matrix-ii/

## Topic
1 D and 2 D Arrays

## Core Concept
Start from top-right (or bottom-left) and eliminate row or column each step.

## Intuition
Rows sorted left-to-right, columns top-to-bottom. From top-right, if value > target move left (column eliminated); if value < target move down (row eliminated).

## Detailed Explanation
r=0, c=m-1. While r<n and c>=0: if mat[r][c]==target return true; if mat[r][c]>target c--; else r++.

## Dry Run
matrix=[[1,4,7],[2,5,8],[3,6,9]], target=5. (0,2)=7>5 → c=1. (0,1)=4<5 → r=1. (1,1)=5 ✓.

## Approach
Staircase search.

## Time and Space Complexity
Time: O(n+m). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool searchMatrix(vector<vector<int>>& M, int t) {
    int n = M.size(), m = M[0].size();
    int r = 0, c = m - 1;
    while (r < n && c >= 0) {
        if (M[r][c] == t) return true;
        if (M[r][c] > t) c--;
        else r++;
    }
    return false;
}
```

## Follow-up Questions
- Count occurrences of target.
- Find closest value.
- If matrix is fully sorted flat, use binary search.
