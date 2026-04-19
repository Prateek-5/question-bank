# Convert 1D Array Into 2D Array

## Problem Link
https://leetcode.com/problems/convert-1d-array-into-2d-array/

## Topic
1 D and 2 D Arrays

## Core Concept
Index mapping i → (i/n, i%n).

## Intuition
A 1D array of length m*n maps to an m×n matrix where the k-th element goes to row k/n, col k%n.

## Detailed Explanation
If original.size() != m*n return []. Otherwise fill mat[i/n][i%n] = original[i].

## Dry Run
orig=[1,2,3,4], m=2,n=2 → [[1,2],[3,4]].

## Approach
Direct mapping in one pass.

## Time and Space Complexity
Time: O(m*n). Space: O(m*n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> construct2DArray(vector<int>& a, int m, int n) {
    if ((int)a.size() != m*n) return {};
    vector<vector<int>> res(m, vector<int>(n));
    for (int i = 0; i < m*n; ++i) res[i/n][i%n] = a[i];
    return res;
}
```

## Follow-up Questions
- Reshape with a different ordering (column-major).
- Partial fill with padding.
- Transpose a matrix given as flat array.
