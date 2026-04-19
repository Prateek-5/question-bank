# Daily Temperatures

## Problem Link
https://leetcode.com/problems/daily-temperatures/

## Topic
Stack

## Core Concept
Monotonic decreasing stack of indices.

## Intuition
For each day, look ahead for the next warmer day. A stack of unresolved indices works: whenever a warmer day appears, pop and record distance.

## Detailed Explanation
Iterate i; while stack non-empty and T[i]>T[stack.top()], pop j and set res[j]=i-j. Push i.

## Dry Run
T=[73,74,75,71,69,72,76,73]. Answer [1,1,4,2,1,1,0,0].

## Approach
Monotonic stack.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> dailyTemperatures(vector<int>& T) {
    int n = T.size(); vector<int> res(n, 0); stack<int> st;
    for (int i = 0; i < n; ++i) {
        while (!st.empty() && T[i] > T[st.top()]) { res[st.top()] = i - st.top(); st.pop(); }
        st.push(i);
    }
    return res;
}
```

## Follow-up Questions
- Next colder day.
- Previous warmer day.
- Circular day array.
