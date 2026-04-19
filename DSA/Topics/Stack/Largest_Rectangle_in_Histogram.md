# Largest Rectangle in Histogram

## Problem Link
https://leetcode.com/problems/largest-rectangle-in-histogram/

## Topic
Stack

## Core Concept
Monotonic increasing stack of bar indices.

## Intuition
For each bar, the largest rectangle with it as the shortest bar has width equal to the distance between the previous smaller and next smaller bars.

## Detailed Explanation
Append sentinel 0. For each i: while top's height > h[i], pop as height; width = stack.empty() ? i : i - stack.top() - 1. Track max. Push i.

## Dry Run
h=[2,1,5,6,2,3] → max area 10.

## Approach
Monotonic stack.

## Time and Space Complexity
Time: O(n). Space: O(n).

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
```

## Follow-up Questions
- Maximal rectangle in 0/1 matrix.
- Rectangles with at most k ones.
- Dynamic histogram queries.
