# Maximal Rectangle

## Problem Link
https://leetcode.com/problems/maximal-rectangle/

## Topic
Dynamic Programming DP

## Core Concept
Histogram rectangle per row using largest-rectangle-in-histogram.

## Intuition
For each row treat consecutive 1s above as histogram bars; apply monotonic stack to find largest rectangle.

## Detailed Explanation
Maintain heights[j]; for each row update heights (reset on 0). Compute row's largest rectangle; track max.

## Dry Run
matrix=[['1','0','1','0','0'],...]. Answer=6.

## Approach
DP heights + monotonic stack per row.

## Time and Space Complexity
Time: O(n·m). Space: O(m).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int largestRectangleArea(vector<int>& h) {
    h.push_back(0);
    stack<int> st; int best = 0;
    for (int i = 0; i < (int)h.size(); ++i) {
        while (!st.empty() && h[st.top()] > h[i]) {
            int top = st.top(); st.pop();
            int w = st.empty() ? i : i - st.top() - 1;
            best = max(best, h[top] * w);
        }
        st.push(i);
    }
    h.pop_back();
    return best;
}
int maximalRectangle(vector<vector<char>>& M) {
    if (M.empty()) return 0;
    int m = M[0].size(), best = 0;
    vector<int> h(m, 0);
    for (auto& r : M) {
        for (int j = 0; j < m; ++j) h[j] = r[j]=='1' ? h[j]+1 : 0;
        best = max(best, largestRectangleArea(h));
    }
    return best;
}
```

## Follow-up Questions
- Maximum square (easier DP).
- Count maximal rectangles.
- Sub-rectangle with sum constraint.
