# Remove Outermost Parentheses

## Problem Link
https://leetcode.com/problems/remove-outermost-parentheses/

## Topic
Stack

## Core Concept
Track depth; skip chars at depth 0↔1 transitions.

## Intuition
An outermost '(' starts a primitive (depth 0→1) and its matching ')' ends it (depth 1→0). Skip those transitions.

## Detailed Explanation
Iterate; open increments depth. Append char unless depth just became 1 (on '(') or just returned to 0 (on ')').

## Dry Run
s='(()())(())'. Result '()()()'.

## Approach
Depth counter.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
string removeOuterParentheses(string s) {
    string r; int d = 0;
    for (char c : s) {
        if (c == '(' && d++ > 0) r += c;
        else if (c == ')' && --d > 0) r += c;
    }
    return r;
}
```

## Follow-up Questions
- Balance types (multi-bracket).
- Depth-k outer removal.
- Parse primitives list.
