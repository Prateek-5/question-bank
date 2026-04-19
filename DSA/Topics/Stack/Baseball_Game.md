# Baseball Game

## Problem Link
https://leetcode.com/problems/baseball-game/

## Topic
Stack

## Core Concept
Stack of recent scores processing special tokens.

## Intuition
'+' is sum of last two, 'D' is double last, 'C' removes last, number is a new score. A stack matches these operations.

## Detailed Explanation
Iterate tokens; apply to stack accordingly. Final answer is the sum of stack.

## Dry Run
ops=['5','2','C','D','+']. Stack: [5]→[5,2]→[5]→[5,10]→[5,10,15]. Sum=30.

## Approach
Stack simulation.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int calPoints(vector<string>& ops) {
    vector<int> st;
    for (auto& o : ops) {
        if (o == "C") st.pop_back();
        else if (o == "D") st.push_back(2 * st.back());
        else if (o == "+") st.push_back(st[st.size()-1] + st[st.size()-2]);
        else st.push_back(stoi(o));
    }
    return accumulate(st.begin(), st.end(), 0);
}
```

## Follow-up Questions
- Undo across multiple Cs.
- Sum after each operation.
- Streaming tokens.
