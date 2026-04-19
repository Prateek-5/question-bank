# Expression Contains Redundant Bracket or Not

## Problem Link
https://www.geeksforgeeks.org/problems/expression-contains-redundant-bracket-or-not/1

## Topic
Stack

## Core Concept
Stack scanning for a pair of parens enclosing zero operators.

## Intuition
A subexpression in parens is redundant iff no operator exists between the opening '(' and its matching ')'.

## Detailed Explanation
Push each char onto stack. On ')': pop until '('; if no operator was popped, it's redundant.

## Dry Run
expr='((a+b))' → innermost '(a+b)' ok; outer '(' ')' encloses only '(a+b)' → redundant.

## Approach
Stack parsing.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool hasRedundantBrackets(string s) {
    stack<char> st;
    for (char c : s) {
        if (c == ')') {
            bool hasOp = false;
            while (!st.empty() && st.top() != '(') {
                if (st.top() == '+' || st.top() == '-' || st.top() == '*' || st.top() == '/') hasOp = true;
                st.pop();
            }
            if (!st.empty()) st.pop();
            if (!hasOp) return true;
        } else st.push(c);
    }
    return false;
}
```

## Follow-up Questions
- Find position of redundant bracket.
- Remove redundant brackets.
- Evaluate expression validity.
