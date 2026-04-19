# Implement Stack using Queues

## Problem Link
https://leetcode.com/problems/implement-stack-using-queues/

## Topic
Queues Deque Monotonic Queue

## Core Concept
Two queues or one-queue rotation.

## Intuition
One-queue approach: after every push, rotate queue by size-1 so the new element is always at front.

## Detailed Explanation
Push x: q.push(x); rotate size-1 times by pop-push. Top: q.front(). Pop: q.pop().

## Dry Run
Push 1 → [1]. Push 2 → [2,1]. Push 3 → [3,2,1]. Pop → 3.

## Approach
Queue rotation.

## Time and Space Complexity
Push O(n), pop/top O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class MyStack {
    queue<int> q;
public:
    void push(int x) { q.push(x); for (int i = 0; i < (int)q.size() - 1; ++i) { q.push(q.front()); q.pop(); } }
    int pop() { int v = q.front(); q.pop(); return v; }
    int top() { return q.front(); }
    bool empty() { return q.empty(); }
};
```

## Follow-up Questions
- Use two queues.
- Implement min-stack with queues.
- Thread-safe version.
