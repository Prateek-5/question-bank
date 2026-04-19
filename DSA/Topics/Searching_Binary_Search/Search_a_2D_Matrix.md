# Search a 2D Matrix

## Problem Link
https://leetcode.com/problems/search-a-2d-matrix/

## Topic
Searching Binary Search

## Core Concept
Treat matrix as flat sorted array; binary search on n*m length.

## Intuition
Rows concatenate into a globally sorted array. Index i maps to (i/m, i%m).

## Detailed Explanation
Binary search indices [0, n*m-1]; at mid decode (r, c) and compare with target.

## Dry Run
Matrix sorted row-wise and first-of-row > last-of-prev-row. target=5 locates via binary search.

## Approach
Standard binary search with index mapping.

## Time and Space Complexity
Time: O(log(nm)). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool searchMatrix(vector<vector<int>>& M, int t) {
    int n = M.size(), m = M[0].size();
    int lo = 0, hi = n*m - 1;
    while (lo <= hi) {
        int md = (lo + hi) / 2;
        int v = M[md/m][md%m];
        if (v == t) return true;
        if (v < t) lo = md + 1; else hi = md - 1;
    }
    return false;
}
```

## Follow-up Questions
- Variant II (only sorted per row and col).
- Return position, not boolean.
- Nearest value query.
