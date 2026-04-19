# Valid Parentheses

## Problem Link
https://leetcode.com/problems/valid-parentheses/

## Topic
Stack

## Core Concept
Stack matching each closer to the last opener.

## Intuition
Use a stack: on open push; on close check top matches and pop. Valid iff stack is empty at end.

## Detailed Explanation
Iterate; map close→open. Handle early fail when top doesn't match.

## Dry Run
s='()[]{}' → stack shrinks each pair → valid.

## Approach
Stack matching.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool isValid(string s) {
    stack<char> st;
    for (char c : s) {
        if (c == '(' || c == '[' || c == '{') st.push(c);
        else {
            if (st.empty()) return false;
            char t = st.top(); st.pop();
            if ((c == ')' && t != '(') || (c == ']' && t != '[') || (c == '}' && t != '{')) return false;
        }
    }
    return st.empty();
}
```

## Follow-up Questions
- Minimum edits to make valid.
- Longest valid substring.
- Streaming version.
