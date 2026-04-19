# Spiral Matrix II

## Problem Link
https://leetcode.com/problems/spiral-matrix-ii/

## Topic
Arrays and Matrices

## Core Concept
Fill n×n matrix by spiraling boundaries inward.

## Intuition
Simulate walking in a spiral: right, down, left, up, shrinking boundaries each loop.

## Detailed Explanation
Maintain top, bottom, left, right bounds. Alternate filling row/column, then shrink the used boundary.

## Dry Run
n=3 → [[1,2,3],[8,9,4],[7,6,5]].

## Approach
Four-direction simulation.

## Time and Space Complexity
Time: O(n²). Space: O(n²) for output.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> generateMatrix(int n) {
    vector<vector<int>> m(n, vector<int>(n, 0));
    int t = 0, b = n-1, l = 0, r = n-1, x = 1;
    while (t <= b && l <= r) {
        for (int j = l; j <= r; ++j) m[t][j] = x++;
        t++;
        for (int i = t; i <= b; ++i) m[i][r] = x++;
        r--;
        if (t <= b) for (int j = r; j >= l; --j) m[b][j] = x++;
        b--;
        if (l <= r) for (int i = b; i >= t; --i) m[i][l] = x++;
        l++;
    }
    return m;
}
```

## Follow-up Questions
- Spiral Matrix I (read instead of fill).
- Rectangular spiral.
- Diagonal/zigzag fill.
