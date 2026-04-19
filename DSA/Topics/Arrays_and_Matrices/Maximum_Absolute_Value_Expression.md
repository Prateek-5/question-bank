# Maximum Absolute Value Expression

## Problem Link
https://leetcode.com/problems/maximum-of-absolute-value-expression/

## Topic
Arrays and Matrices

## Core Concept
Simplify |a|+|b|+|c| over four sign combinations; scan with prefix maxima/minima.

## Intuition
|x1-x2|+|y1-y2|+|i-j| simplifies to one of 4 sign combos of (±x ± y ± i). For each combo track max and min; best diff is max-min.

## Detailed Explanation
For each of 4 sign combos s1, s2 ∈ {+1,-1}: val[i] = s1*x[i] + s2*y[i] + i. answer = max over combos of (max(val) - min(val)).

## Dry Run
arr1=[1,2,3,4], arr2=[-1,4,5,6]. Best combo yields 13.

## Approach
4 sign combinations × O(n).

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maxAbsValExpr(vector<int>& a, vector<int>& b) {
    int n = a.size(), ans = 0;
    for (int sx : {1, -1}) for (int sy : {1, -1}) {
        int mn = INT_MAX, mx = INT_MIN;
        for (int i = 0; i < n; ++i) {
            int v = sx*a[i] + sy*b[i] + i;
            mn = min(mn, v); mx = max(mx, v);
        }
        ans = max(ans, mx - mn);
    }
    return ans;
}
```

## Follow-up Questions
- 3D extension.
- Maximize over pairs with distance constraint.
- Stream version.
