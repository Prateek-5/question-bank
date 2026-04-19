# Heap / Priority Queue — Concepts Guide

----------------------------------------

## 1. Introduction

A heap is a specialized data structure that gives you quick access to the maximum (or minimum) element in a collection. It's the data structure you reach for whenever the question asks for *'the largest so far'*, *'the k smallest'*, or *'process items by priority'*. Without a heap, those questions would require repeated sorting — slow and wasteful. A heap does the job in O(log n) per update.

----------------------------------------

## 2. Real-Life Analogy

Think of a hospital emergency room. Patients arrive in some random order, but they're *not* treated first-come-first-served — they're treated by priority. The nurse at the triage desk is the heap: at any moment, she can tell you who the highest-priority patient is. When a new patient arrives, she slots them into the right priority position. That's exactly what a heap does with numbers (or any comparable items).

----------------------------------------

## 3. Core Idea

A heap is a complete binary tree with one strict rule: every parent satisfies a comparison with its children (parent ≤ children for a min-heap, parent ≥ children for a max-heap). This invariant means the root is always the extremum — the minimum or the maximum of the entire set. Because the tree is complete, we can store it compactly in an array: the children of index i live at 2i+1 and 2i+2. When we insert, we place the new element at the end and 'bubble up' to restore the invariant. When we extract the root, we replace it with the last element and 'sift down'. Both operations are O(log n) because the tree has log n levels.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Reach for a heap when any of these signals appear in a problem:

- **'Top k'** or **'k-th largest/smallest'** — maintain a bounded heap of size k.
- **Streaming median** — two heaps, one for each half of the data, balanced by size.
- **Scheduling by priority** — highest-priority task first.
- **Greedy merges** — repeatedly combine the two smallest elements (Huffman coding, connect ropes).
- **K-way merge** — push one head from each list into a min-heap, pop, advance, repeat.
- **Dijkstra's algorithm** — extract the next-nearest node via a min-heap keyed on distance.

If you see any of these keywords or structures, a heap is almost certainly the right tool.

----------------------------------------

## 5. Types / Variations

**Min-Heap vs Max-Heap:** a min-heap's root is the smallest element; a max-heap's root is the largest. In C++, `priority_queue<int>` is a max-heap by default. To build a min-heap, use `priority_queue<int, vector<int>, greater<int>>`.

**Indexed (Mutable) Heap:** a regular heap doesn't allow decreasing a specific key. For problems like Dijkstra with updates to intermediate distances, we either use lazy deletion (push a new entry and ignore stale ones on pop) or maintain an index map for O(log n) decrease-key.

**d-ary Heap:** instead of binary, children are d-ary. Useful when decrease-key is cheaper than extract-min.

**Fibonacci Heap:** theoretical O(1) amortized decrease-key. Rarely used in practice but worth knowing exists.

----------------------------------------

## 6. Step-by-Step Working

**Insertion (push):**
1. Place the new element at the next array slot.
2. Compare with its parent (at index (i-1)/2).
3. If the heap property is violated, swap with the parent.
4. Repeat from step 2 until the property holds or we reach the root.

**Extraction (pop):**
1. Save the root as the returned value.
2. Move the last array element into the root slot.
3. Shrink the array by one.
4. Sift down: compare the root with its smaller child; if violated, swap. Repeat until the property holds or we reach a leaf.

Each of these operations walks at most one root-to-leaf path — that's log n steps.

----------------------------------------

## 7. Visual Explanation

Imagine this min-heap:

```
         2
       /   \
      5     3
     / \   / \
    7   9 6   4
```

Inserting `1`: place at the next slot (right of `4`), then bubble up.

```
         2                1
       /   \            /   \
      5     3    →     5     2
     / \   / \        / \   / \
    7   9 6   4      7   9 6   3
     \                \          \
      1                4          <- bubble path
```

After bubbling, `1` is the new root, and the heap property is restored everywhere.

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Max-heap (default)
priority_queue<int> max_pq;

// Min-heap
priority_queue<int, vector<int>, greater<int>> min_pq;

// Custom comparator (e.g., pair by second value)
auto cmp = [](const pair<int,int>& a, const pair<int,int>& b) {
    return a.second > b.second;  // min-heap on .second
};
priority_queue<pair<int,int>, vector<pair<int,int>>, decltype(cmp)> pq(cmp);

// Top-k smallest: keep a max-heap of size k
priority_queue<int> topK;
for (int x : nums) {
    topK.push(x);
    if ((int)topK.size() > k) topK.pop();
}
// topK now holds the k smallest; topK.top() is the k-th smallest.
```

----------------------------------------

## 9. Common Mistakes

- **Assuming `priority_queue<int>` is a min-heap.** It's a max-heap by default.
- **Using a heap when you need random access.** Heaps only guarantee fast access to the extremum, not to arbitrary elements.
- **Updating a key in place.** Heaps don't support this cleanly. Use lazy deletion or an indexed heap.
- **Forgetting tie-breakers.** Two equal-priority items have unspecified relative order unless your comparator breaks the tie.
- **Calling `top()` on an empty heap.** Always check `empty()` first — `top()` on an empty priority_queue is undefined behavior.

----------------------------------------

## 10. Interview Insights

When an interviewer gives you a problem involving 'top k', 'streaming', or 'merge', they're almost always testing whether you'll reach for a heap. The interviewer wants to see:

1. **Can you identify the pattern?** Just naming 'priority queue' in the first minute scores huge points.
2. **Can you pick the right polarity?** Knowing whether you need min-heap or max-heap (and why) shows you understand the mechanic, not just the name.
3. **Can you analyze complexity correctly?** 'n log k' vs 'n log n' matters; be ready to explain which one your approach achieves.
4. **Can you handle edge cases?** Empty input, k > n, and duplicates are the usual traps.

Under pressure, narrate your thinking out loud: 'I need the k smallest, so I'll use a max-heap of size k — every push is log k, and I pop when it exceeds k.' That sentence alone often convinces the interviewer you know what you're doing.
