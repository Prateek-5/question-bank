# Evaluate Reverse Polish Notation

## Problem Link
https://leetcode.com/problems/evaluate-reverse-polish-notation/

## Topic
Stack

## Core Concept
Stack of operands; on operator pop two, apply, push result.

## Intuition
RPN naturally evaluates with a stack — operators act on the top two values.

## Detailed Explanation
For each token: if numeric push; else pop b, a, compute a OP b, push result.

## Dry Run
tokens=['2','1','+','3','*']. Stack 2,1 → 3 → 3,3 → 9.

## Approach
Stack simulation.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int evalRPN(vector<string>& t) {
    stack<long long> st;
    for (auto& x : t) {
        if (x == "+" || x == "-" || x == "*" || x == "/") {
            long long b = st.top(); st.pop();
            long long a = st.top(); st.pop();
            if (x == "+") st.push(a + b);
            else if (x == "-") st.push(a - b);
            else if (x == "*") st.push(a * b);
            else st.push(a / b);
        } else st.push(stoll(x));
    }
    return (int)st.top();
}
```

## Follow-up Questions
- Convert infix to postfix.
- Handle unary minus.
- Add parentheses/precedence parser.
