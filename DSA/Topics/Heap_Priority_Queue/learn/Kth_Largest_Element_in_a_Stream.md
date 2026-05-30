# Kth Largest Element in a Stream — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Kth_Largest_Element_in_a_Stream.md`](../Kth_Largest_Element_in_a_Stream.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/kth-largest-element-in-a-stream/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/kth-largest-element-in-a-stream/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The introduction to the SIZE-K BOUNDED HEAP pattern.** The lesson: **for "k-th largest in a stream," maintain a MIN-HEAP of SIZE K. The root is ALWAYS the k-th largest.** Inverted intuition (min-heap for k-th LARGEST) is the key. **Read [`Last_Stone_Weight.md`](./Last_Stone_Weight.md) first.**

**Map of this file (9 sections):**

1. Read the problem
2. The naive "store everything, sort" approach
3. The size-k bounded heap insight
4. Why MIN-heap for k-th LARGEST?
5. The pattern: push, pop-if-oversize, top
6. Code
7. Trace it
8. Common pitfalls
9. The shape — bounded heaps

---

## 1. Read the problem

Design a class `KthLargest`:
- Constructor: takes `k` and an initial integer array `nums`.
- `int add(val)`: adds `val` to the stream. Returns the **k-th LARGEST** element seen so far.

**Example:** `k = 3`, initial `[4, 5, 8, 2]`.

- Initially, sorted desc: [8, 5, 4, 2]. 3rd largest = 4.
- `add(3)`: stream now [4, 5, 8, 2, 3]. Sorted: [8, 5, 4, 3, 2]. 3rd = 4. Return 4.
- `add(5)`: stream + 5. Sorted: [8, 5, 5, 4, 3, 2]. 3rd = 5. Return 5.
- `add(10)`: 3rd = 5.
- `add(9)`: 3rd = 8.
- `add(4)`: 3rd = 8.

---

## 2. The naive "store everything, sort" approach

Keep all values in a list. On `add(val)`, append and SORT. Return list[n-k].

O(n log n) per `add`. For M adds, O(M × n log n). Too slow for streaming.

We're re-doing work — most of the past data doesn't change.

---

## 3. The size-k bounded heap insight

> **Mini-refresher: only the top-K matter.**
>
> The k-th LARGEST is determined ENTIRELY by the K LARGEST values seen so far. Everything smaller is IRRELEVANT.
>
> Maintain a collection of exactly the K LARGEST values. When a new value `val` arrives:
> - If `val` is bigger than the current SMALLEST in our top-K → include it, KICK OUT the old smallest.
> - Otherwise → ignore it (it can't displace any of the top-K).
>
> Either way, the SMALLEST of our top-K is the k-th LARGEST.

So: maintain the top-K. The "weakest link" is the smallest of the K. We want O(log K) access to it.

**A MIN-HEAP of size K is exactly that.**

---

## 4. Why MIN-heap for k-th LARGEST?

> **Mini-refresher: inverted intuition.**
>
> The k-th LARGEST is the SMALLEST of the top-K largest. To efficiently track "the smallest of top-K," use a MIN-heap (its top is the smallest).
>
> **MIN-heap stores k LARGEST.** **MAX-heap stores k SMALLEST** (for the "k-th smallest" version).
>
> This polarity is COUNTERINTUITIVE but critical. Get it wrong and the problem becomes O(K) per query instead of O(log K).

Why does the inversion work? Because we want O(1) access to the BOUNDARY of our top-K (the element most at-risk of being kicked out). For top-K largest, the at-risk one is the SMALLEST in our set → min-heap on top.

---

## 5. The pattern: push, pop-if-oversize, top

For each `add(val)`:

```
heap.push(val)
if heap.size() > k:
    heap.pop()    # remove the smallest (was added either now or earlier)
return heap.top() # k-th largest
```

**Push first, then pop if oversize.** Simpler than "check before push" — fewer branches.

After the operation:
- Heap size is exactly K (or less, during early adds).
- Heap's top is the SMALLEST of the K largest = the k-th largest.

---

## 6. Code

**C++:**

```cpp
class KthLargest {
    priority_queue<int, vector<int>, greater<int>> heap;   // MIN-heap
    int k;

public:
    KthLargest(int k_, vector<int>& nums) : k(k_) {
        for (int x : nums) add(x);
    }

    int add(int val) {
        heap.push(val);
        if ((int)heap.size() > k) heap.pop();
        return heap.top();
    }
};
```

**Python:**

```python
import heapq

class KthLargest:
    def __init__(self, k, nums):
        self.k = k
        self.heap = []
        for x in nums:
            self.add(x)
    
    def add(self, val):
        heapq.heappush(self.heap, val)         # min-heap by default
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]                     # smallest = k-th largest
```

**JavaScript** (manual heap or library).

Complexity:
- Constructor: O(N log K).
- `add`: O(log K) per call.
- Space: O(K).

---

## 7. Trace it

`k = 3`, initial `[4, 5, 8, 2]`.

```
heap = [].

add(4): push 4. heap = [4]. size 1 ≤ 3. Return heap[0] = 4.
add(5): push 5. heap = [4, 5]. size 2 ≤ 3. Return 4.
add(8): push 8. heap = [4, 5, 8]. size 3 = 3. Return 4.
add(2): push 2. heap = [2, 4, 5, 8] (min-heap). size 4 > 3. Pop 2. heap = [4, 5, 8]. Return 4.

Now stream queries:
add(3): push 3. heap = [3, 4, 5, 8]. Pop 3. heap = [4, 5, 8]. Return 4.  ✓
add(5): push 5. heap = [4, 5, 5, 8]. Pop 4. heap = [5, 5, 8]. Return 5.  ✓
add(10): push 10. heap = [5, 5, 8, 10]. Pop 5. heap = [5, 8, 10]. Return 5.  ✓
add(9): push 9. heap = [5, 8, 9, 10]. Pop 5. heap = [8, 9, 10]. Return 8.  ✓
add(4): push 4. heap = [4, 8, 9, 10]. Pop 4. heap = [8, 9, 10]. Return 8.  ✓
```

All match expected. The heap's top tracks the k-th largest after each add.

---

## 8. Common pitfalls

1. **Using a max-heap for k-th LARGEST.** That tracks ALL elements, not just top-K. Wrong polarity.

2. **Forgetting to pop on oversize.** Heap grows unbounded; queries take O(K) to find min.

3. **Checking size BEFORE push.** Works but more conditionals. Just push then pop.

4. **Returning `heap.top()` when heap.size() < k.** During the first few adds (before the stream has k elements), there's no valid "k-th largest." The problem usually guarantees the constructor accumulates ≥ k elements, but during construction's add()'s, you might query intermediate states. Watch the problem spec.

5. **Confusing 1-indexed vs 0-indexed "k".** This problem is 1-indexed: k=1 means the LARGEST.

6. **Heap of pairs/tuples without a comparator.** For value-only, a simple int heap suffices. For value + metadata, use tuples or custom comparators.

---

## 9. The shape — bounded heaps

The pattern:

> **"For TOP-K queries on STREAMS, maintain a BOUNDED HEAP of SIZE K. The root is the K-th element of interest. O(log K) per insert."**

| Problem | Heap polarity | K-th |
|---|---|---|
| **This problem** (k-th largest) | min-heap | smallest of top-K largest |
| K-th Smallest in a Stream | max-heap | largest of top-K smallest |
| Top K Frequent Elements | min-heap by frequency | least-frequent of top-K |
| K Closest Points to Origin | max-heap by distance | farthest of K closest |
| Sliding Window Median | two heaps (max-low, min-high) | balance midpoint |

**Pattern to internalize:**

> "Top-K bounded heap: maintain exactly K elements; the 'weakest link' (boundary) is the answer to 'k-th in some ordering.' Polarity is INVERTED — min-heap for top-K largest, max-heap for top-K smallest."

---

> **Self-check — the question to ask next time.**
>
> When you need the K-th largest/smallest in a stream, ask:
>
> > **"Can I maintain a SIZE-K BOUNDED HEAP whose top is the K-th element?"**
>
> Polarity inverted: min-heap for largest, max-heap for smallest.

---

## Cross-references

- **Reference card (post-mastery):** [`../Kth_Largest_Element_in_a_Stream.md`](../Kth_Largest_Element_in_a_Stream.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Last_Stone_Weight.md`](./Last_Stone_Weight.md).
  - Coming next: [`Top_K_Frequent_Elements.md`](./Top_K_Frequent_Elements.md), [`Kth_Largest_Element_in_an_Array.md`](./Kth_Largest_Element_in_an_Array.md).
  - [`../../Sorting_Divide_and_Conquer/learn/Kth_Largest_Element_in_an_Array.md`](../../Sorting_Divide_and_Conquer/learn/Kth_Largest_Element_in_an_Array.md) — quickselect alternative.
