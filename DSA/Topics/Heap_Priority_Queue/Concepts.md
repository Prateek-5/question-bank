# Heap / Priority Queue — Concepts

## Core Theory
A heap is a complete binary tree where every parent satisfies a partial order with its children (min-heap: parent ≤ children; max-heap: parent ≥ children). It provides O(log n) insertion and extraction of the top element and O(1) peek. In C++, `std::priority_queue` is a max-heap by default; use `greater<>` comparator for a min-heap.

## Common Patterns
- **Top-K filtering:** maintain a bounded heap of size k (max-heap for k smallest, min-heap for k largest).
- **Streaming median:** two heaps (lo max-heap, hi min-heap) balanced to differ by at most 1.
- **Greedy merging:** combine smallest elements repeatedly (Huffman / connect ropes).
- **K-way merge:** push one head from each list; pop, emit, advance.
- **Graph shortest paths (Dijkstra):** min-heap keyed by distance.

## When to Use
When you need the minimum or maximum efficiently under insertions, or need to process items in priority order. Avoid when you need random access, sorted iteration, or frequent arbitrary updates to non-top items (use segment trees or indexed heaps instead).

## Template
```cpp
// Max-heap
priority_queue<int> pq;
// Min-heap
priority_queue<int, vector<int>, greater<int>> pq;
// Custom comparator (lambda)
auto cmp = [](const auto& a, const auto& b){ return a.cost > b.cost; };
priority_queue<Node, vector<Node>, decltype(cmp)> pq(cmp);
```

## Common Mistakes
- Forgetting that `priority_queue<int>` is a *max* heap by default.
- Using a heap where a sorted container is more appropriate.
- Pushing duplicate entries when modifying a key; use lazy deletion with a stale check.
- Not handling ties deterministically — include secondary keys.
