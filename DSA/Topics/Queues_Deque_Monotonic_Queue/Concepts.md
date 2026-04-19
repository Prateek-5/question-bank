# Queues / Deque / Monotonic Queue — Concepts

## Core Theory
Queues and deques provide FIFO access. Monotonic deques maintain elements in monotonic order, supporting sliding window min/max in O(n).

## Common Patterns
- **BFS queue** for level-order traversal.
- **Monotonic deque** for sliding window extremes.
- **Implementing stack via queues** and vice versa (design).

## When to Use
For breadth-first traversal, fairness, or sliding-window extremum queries.

## Template
```cpp
deque<int> dq;
for (int i = 0; i < n; ++i) {
    while (!dq.empty() && a[dq.back()] <= a[i]) dq.pop_back();
    dq.push_back(i);
    if (dq.front() <= i - k) dq.pop_front();
}
```

## Common Mistakes
- Pushing values instead of indices loses position info.
- Incorrect popping direction for min vs max queue.
- Using `queue` instead of `deque` when both ends are needed.
