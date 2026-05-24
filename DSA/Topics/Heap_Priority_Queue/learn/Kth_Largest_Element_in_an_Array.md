# Kth Largest Element in an Array (Heap version) — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Kth_Largest_Element_in_an_Array.md`](../Kth_Largest_Element_in_an_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/kth-largest-element-in-an-array/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **Heap-based solution. Same problem as in Sorting topic (quickselect there), different tradeoffs.** The lesson: **MIN-HEAP of size K for K-th largest. O(n log k) time, O(k) space. Compare with quickselect's O(n) average.** **Read [`Kth_Largest_Element_in_a_Stream.md`](./Kth_Largest_Element_in_a_Stream.md) and [`Kth_Largest_Element_in_an_Array.md`](../../Sorting_Divide_and_Conquer/learn/Kth_Largest_Element_in_an_Array.md) (quickselect) first.**

**Map of this file (7 short sections):**

1. Read the problem
2. The naive full-sort
3. The size-K min-heap
4. Code
5. Trace it
6. Comparing with quickselect
7. Common pitfalls + the shape

---

## 1. Read the problem

Given an integer array `nums` and integer `k`, return the **K-th LARGEST** element.

**Examples:**

- `nums = [3, 2, 1, 5, 6, 4]`, `k = 2` → **5**.
- `nums = [3, 2, 3, 1, 2, 4, 5, 5, 6]`, `k = 4` → **4**.

(K is 1-indexed: k=1 means LARGEST.)

---

## 2. The naive full-sort

```
nums.sort(reverse=True)
return nums[k - 1]
```

O(n log n). Simplest. For small inputs, fine.

For large n and small k, wasteful — we sort the whole array but only need the top K.

---

## 3. The size-K min-heap

> **Mini-refresher: min-heap for K-th LARGEST.**
>
> Maintain a min-heap of size K. For each element:
> - Push.
> - If size > K: pop the SMALLEST.
>
> After processing all elements, the heap holds the K largest. Its TOP (smallest) IS the K-th largest.

```
heap = empty min-heap
for x in nums:
    heap.push(x)
    if heap.size > k: heap.pop()
return heap.top()
```

O(n log k) time. O(k) space.

---

## 4. Code

**C++:**

```cpp
int findKthLargest(vector<int>& nums, int k) {
    priority_queue<int, vector<int>, greater<int>> minHeap;
    for (int x : nums) {
        minHeap.push(x);
        if ((int)minHeap.size() > k) minHeap.pop();
    }
    return minHeap.top();
}
```

**Python:**

```python
import heapq

def findKthLargest(nums, k):
    heap = []
    for x in nums:
        heapq.heappush(heap, x)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap[0]
```

Complexity: **O(n log k) time, O(k) space.**

---

## 5. Trace it

`nums = [3, 2, 1, 5, 6, 4]`, `k = 2`.

```
heap = [].

push 3: heap = [3]. size 1.
push 2: heap = [2, 3]. size 2. (min on top)
push 1: heap = [1, 3, 2]. size 3 > 2 → pop 1. heap = [2, 3].
push 5: heap = [2, 3, 5]. size 3 > 2 → pop 2. heap = [3, 5].
push 6: heap = [3, 5, 6]. size 3 > 2 → pop 3. heap = [5, 6].
push 4: heap = [4, 6, 5]. size 3 > 2 → pop 4. heap = [5, 6].

heap.top() = 5.
```

Return **5**. ✓

The heap consistently held the K = 2 largest seen so far. After all are processed, top = K-th largest.

---

## 6. Comparing with quickselect

| Approach | Time | Space | When to prefer |
|---|---|---|---|
| **Min-heap (size K)** | O(n log k) | O(k) | Streaming; small k; reliable worst-case |
| **Quickselect** | O(n) avg, O(n²) worst | O(log n) | Static array; need optimal AVERAGE time |
| **Full sort** | O(n log n) | O(1) (in-place) | Simplest; small n |

> **Mini-refresher: heap vs quickselect tradeoffs.**
>
> - HEAP: works on STREAMS (process elements one at a time); O(k) memory; predictable performance.
> - QUICKSELECT: needs full array; O(n) average — faster when k is large; O(n²) worst-case (mitigate with random pivot).
>
> For LeetCode interviews, EITHER is acceptable. Heap is easier to explain; quickselect is asymptotically faster.

---

## 7. Common pitfalls + the shape

**Pitfalls:**

1. **Using max-heap and popping K-1 times.** O(n + k log n). Works but worse than O(n log k) heap-of-size-k when k is small.

2. **Forgetting to pop on oversize.** Heap grows unbounded; the answer is hidden somewhere.

3. **Treating K-th LARGEST as K-th SMALLEST.** Polarity matters. K-th largest → min-heap.

**The shape:**

> **"For K-th element queries: SIZE-K BOUNDED HEAP. Polarity OPPOSITE to what you'd naively expect. Min-heap for K-th LARGEST."**

Same pattern as Kth Largest in Stream. The stream version emphasizes incremental updates; the array version emphasizes alternatives (quickselect).

---

## Cross-references

- **Reference card (post-mastery):** [`../Kth_Largest_Element_in_an_Array.md`](../Kth_Largest_Element_in_an_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Kth_Largest_Element_in_a_Stream.md`](./Kth_Largest_Element_in_a_Stream.md).
  - [`../../Sorting_Divide_and_Conquer/learn/Kth_Largest_Element_in_an_Array.md`](../../Sorting_Divide_and_Conquer/learn/Kth_Largest_Element_in_an_Array.md) — quickselect alternative.
  - Coming next: [`Find_K_Closest_Elements.md`](./Find_K_Closest_Elements.md), [`Minimum_Cost_to_Connect_Ropes.md`](./Minimum_Cost_to_Connect_Ropes.md).
