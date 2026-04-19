# Longest Valid Parentheses

## Problem Link
https://leetcode.com/problems/longest-valid-parentheses/

## Topic
Queues Deque Monotonic Queue

## Core Concept
Stack of indices with sentinel base.

## Intuition
Push -1 initially. On '(' push index. On ')' pop; if stack empty push current index as new base; else current length = i - stack.top().

## Detailed Explanation
Track best as we iterate.

## Dry Run
'(()' → stack starts [-1]. '(': [-1,0]. '(': [-1,0,1]. ')': pop 1 → [-1,0]; len=2-0=2. Best=2.

## Approach
Stack indexing.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int longestValidParentheses(string s) {
    stack<int> st; st.push(-1);
    int best = 0;
    for (int i = 0; i < (int)s.size(); ++i) {
        if (s[i] == '(') st.push(i);
        else {
            st.pop();
            if (st.empty()) st.push(i);
            else best = max(best, i - st.top());
        }
    }
    return best;
}
```

## Follow-up Questions
- Return the actual substring.
- Count valid substrings.
- Multiple bracket types.
