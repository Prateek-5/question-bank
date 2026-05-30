# Last Stone Weight — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Last_Stone_Weight.md`](../Last_Stone_Weight.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/last-stone-weight/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/last-stone-weight/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The introduction to heaps.** The lesson: **whenever a problem REPEATEDLY asks for "the current MAX" (or min) and then MODIFIES the collection, use a HEAP.** Each operation is O(log n). This is the simplest heap problem — master the mechanics here.

**Map of this file (9 short sections):**

1. What's a heap?
2. Read the problem
3. The naive O(n²) approach
4. The heap-based O(n log n) approach
5. Code
6. Trace it
7. C++ priority_queue defaults
8. Common pitfalls
9. The shape — repeated extract-max

---

## 1. What's a heap?

> **Mini-refresher: heap (priority queue).**
>
> A **heap** is a tree-shaped data structure that supports:
> - **push(x)**: O(log n).
> - **top()** (peek at max or min): O(1).
> - **pop()** (remove max or min): O(log n).
>
> **Max-heap**: the root is always the MAXIMUM.
> **Min-heap**: the root is always the MINIMUM.
>
> Implementation: usually a complete binary tree stored in an ARRAY (with `parent = (i-1)/2`, `children = 2i+1, 2i+2`).
>
> Languages:
> - C++: `priority_queue<int>` (max-heap by default), `priority_queue<int, vector<int>, greater<>>` for min-heap.
> - Python: `heapq` (min-heap; negate for max).
> - Java: `PriorityQueue<>` (min-heap by default).

Heaps are PARTIALLY ORDERED — only the root is known to be the extreme. Useful when you don't need full sorting, just "always give me the current extreme."

---

## 2. Read the problem

You have stones with positive integer weights. Each round:
1. Pick the TWO HEAVIEST stones, `x` (smaller of the pair) and `y` (larger).
2. If `x == y`: both shatter to nothing.
3. If `x < y`: the smaller vanishes; the larger becomes `y - x`.

Repeat until at most ONE stone remains. Return the remaining stone's weight (or 0 if none).

**Example:** `stones = [2, 7, 4, 1, 8, 1]`.

- Round 1: pick 8 and 7. Push back 8-7=1. Stones: `[2, 4, 1, 1, 1]`.
- Round 2: pick 4 and 2. Push 2. Stones: `[2, 1, 1, 1]`.
- Round 3: pick 2 and 1. Push 1. Stones: `[1, 1, 1]`.
- Round 4: pick 1 and 1. Both gone. Stones: `[1]`.

Return **1**.

---

## 3. The naive O(n²) approach

For each round, scan the array to find the two largest. O(n) per round, up to n-1 rounds → O(n²).

```
while len(stones) >= 2:
    stones.sort()
    y = stones.pop()
    x = stones.pop()
    if y != x:
        stones.append(y - x)
return stones[0] if stones else 0
```

For small n (≤ 30), totally fine. For larger n, we want O(n log n).

---

## 4. The heap-based O(n log n) approach

**Use a MAX-HEAP.** Each round:
1. `y = heap.pop()` (largest).
2. `x = heap.pop()` (second largest).
3. If `y != x`: `heap.push(y - x)`.

```
while heap.size() >= 2:
    y = heap.pop()
    x = heap.pop()
    if y != x:
        heap.push(y - x)
return heap.top() if not heap.empty() else 0
```

Each round: 2 pops + at most 1 push = O(log n). Up to n-1 rounds → **O(n log n)**.

---

## 5. Code

**C++:**

```cpp
int lastStoneWeight(vector<int>& stones) {
    priority_queue<int> pq(stones.begin(), stones.end());   // max-heap
    while (pq.size() >= 2) {
        int y = pq.top(); pq.pop();
        int x = pq.top(); pq.pop();
        if (y != x) pq.push(y - x);
    }
    return pq.empty() ? 0 : pq.top();
}
```

The constructor `priority_queue<int> pq(stones.begin(), stones.end())` uses HEAPIFY — O(n) to build.

**Python:**

```python
import heapq

def lastStoneWeight(stones):
    # Python's heapq is min-heap; negate for max-heap behavior
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) >= 2:
        y = -heapq.heappop(heap)   # largest (un-negate)
        x = -heapq.heappop(heap)   # second-largest
        if y != x:
            heapq.heappush(heap, -(y - x))
    return -heap[0] if heap else 0
```

**JavaScript** (no built-in heap; need a library or roll your own).

Complexity: **O(n log n) time, O(n) space.**

---

## 6. Trace it

`stones = [2, 7, 4, 1, 8, 1]`.

Build max-heap: `[8, 7, 4, 2, 1, 1]` (top = 8).

```
Round 1: y=8, x=7. 8≠7 → push 1. Heap = [4, 2, 1, 1, 1] (top = 4).
Round 2: y=4, x=2. 4≠2 → push 2. Heap = [2, 1, 1, 1] (top = 2).
Round 3: y=2, x=1. 2≠1 → push 1. Heap = [1, 1, 1] (top = 1).
Round 4: y=1, x=1. Equal → no push. Heap = [1].

Size < 2 → exit. Return 1.  ✓
```

---

## 7. C++ priority_queue defaults

> **Mini-refresher: C++ priority_queue is MAX-HEAP by default.**
>
> ```cpp
> priority_queue<int> pq;                                              // max-heap
> priority_queue<int, vector<int>, greater<int>> pq;                   // min-heap
> priority_queue<pair<int,int>> pq;                                    // max-heap by pair
> ```
>
> For custom comparators, pass a function or struct as the third template argument.

This problem wants a MAX-HEAP — the default. Just `priority_queue<int>`.

---

## 8. Common pitfalls

1. **Using a sorted array and sorting every round.** O(n²) at best. Use heap.

2. **Confusing max-heap vs min-heap in different languages.** C++ default = max. Python heapq = min. Java PriorityQueue = min. Adjust accordingly.

3. **Popping only once per round.** Need TWO pops (x and y).

4. **Pushing even when x == y.** When equal, both destroyed — push NOTHING.

5. **Returning the wrong default for empty heap.** Empty → return 0.

6. **Checking `pq.size() > 2` instead of `>= 2`.** With exactly 2 stones, we still play a round.

7. **Building the heap one push at a time.** O(n log n). Use the constructor with iterators for O(n) heapify.

---

## 9. The shape — repeated extract-max

The pattern:

> **"When a problem REPEATEDLY needs the CURRENT MAX (or MIN) AND modifies the collection, use a HEAP. Each round: pop, compute, push. O(log n) per round."**

| Problem | Operation per round |
|---|---|
| **This problem** | pop 2 max, push diff |
| Minimum Cost to Connect Ropes | pop 2 min, push sum |
| Reorganize String | pop max-freq char, place it, push back if not done |
| Schedule meetings (count rooms) | pop earliest-ending meeting if non-conflict |
| Huffman coding | pop 2 smallest weights, merge |
| K-way merge | pop smallest, push next from same list |

**Pattern to internalize:**

> "Repeatedly extracting the extreme of a changing collection = heap. Don't use sort + repeated O(n) scans."

---

## Cross-references

- **Reference card (post-mastery):** [`../Last_Stone_Weight.md`](../Last_Stone_Weight.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Kth_Largest_Element_in_a_Stream.md`](./Kth_Largest_Element_in_a_Stream.md), [`Top_K_Frequent_Elements.md`](./Top_K_Frequent_Elements.md).
