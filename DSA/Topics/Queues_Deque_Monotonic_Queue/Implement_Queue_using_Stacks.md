# Implement Queue using Stacks

## Problem Link
https://leetcode.com/problems/implement-queue-using-stacks/

## Topic
Queues Deque Monotonic Queue

## Core Concept
Two stacks — in and out.

## Intuition
Push to 'in'. For peek/pop, if 'out' is empty transfer all from 'in' (reverses order), then operate on 'out'.

## Detailed Explanation
Push: in.push. Pop/Peek: if out empty, while in not empty move top to out. Then pop/peek out.

## Dry Run
Push 1,2. Pop: transfer to out=[2,1], pop 1. Push 3. Pop: out=[2], pop 2. Pop: out empty, transfer in=[3] → [3], pop 3.

## Approach
Amortized O(1) per op.

## Time and Space Complexity
Amortized O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class MyQueue {
    stack<int> in, out;
    void shift() { while (!in.empty()) { out.push(in.top()); in.pop(); } }
public:
    void push(int x) { in.push(x); }
    int pop() { if (out.empty()) shift(); int v = out.top(); out.pop(); return v; }
    int peek() { if (out.empty()) shift(); return out.top(); }
    bool empty() { return in.empty() && out.empty(); }
};
```

## Follow-up Questions
- Implement stack using queues.
- Double-ended queue.
- Concurrent queue.
