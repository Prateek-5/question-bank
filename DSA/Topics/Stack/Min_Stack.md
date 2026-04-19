# Min Stack

## Problem Link
https://leetcode.com/problems/min-stack/

## Topic
Stack

## Core Concept
Auxiliary stack tracking current minimum.

## Intuition
A parallel stack stores the running min at each depth, enabling O(1) getMin.

## Detailed Explanation
Push: record on data stack; also push min(currMin, x) on min stack. Pop: pop both. getMin: top of min stack.

## Dry Run
Push -2,0,-3. Mins [-2,-2,-3]. Pop → mins [-2,-2]. getMin = -2.

## Approach
Two stacks.

## Time and Space Complexity
All ops O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class MinStack {
    stack<int> s, m;
public:
    void push(int x) { s.push(x); if (m.empty() || x <= m.top()) m.push(x); else m.push(m.top()); }
    void pop() { s.pop(); m.pop(); }
    int top() { return s.top(); }
    int getMin() { return m.top(); }
};
```

## Follow-up Questions
- Single-stack encoding (difference trick).
- Max stack.
- Immutable functional stack.
