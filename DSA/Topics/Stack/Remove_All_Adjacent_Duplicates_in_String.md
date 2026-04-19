# Remove All Adjacent Duplicates in String

## Problem Link
https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/

## Topic
Stack

## Core Concept
Stack — cancel adjacent duplicates.

## Intuition
Treat the string as a stack of chars; pushing a char equal to top cancels both.

## Detailed Explanation
Iterate chars; if top==c pop, else push. Result is stack contents joined.

## Dry Run
'abbaca' → 'a','ab','abb'→'a','ac'→'ac','aca'.

## Approach
String as stack.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
string removeDuplicates(string s) {
    string r;
    for (char c : s) {
        if (!r.empty() && r.back() == c) r.pop_back();
        else r += c;
    }
    return r;
}
```

## Follow-up Questions
- Remove k consecutive equals.
- Remove via pattern-match.
- Streaming version.
