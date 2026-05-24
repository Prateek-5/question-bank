# K Closest Points to Origin — Teaching Walkthrough

> **Reference card (post-mastery):** [`../K_Closest_Points_to_Origin.md`](../K_Closest_Points_to_Origin.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/k-closest-points-to-origin/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: SIZE-K MAX-HEAP for the K SMALLEST elements.** Inverted polarity: max-heap for top-K smallest, min-heap for top-K largest. **Read [`Kth_Largest_Element_in_a_Stream.md`](./Kth_Largest_Element_in_a_Stream.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. The squared-distance trick
3. The size-K max-heap approach
4. Code
5. Trace it
6. The quickselect alternative
7. Common pitfalls
8. The shape — top-K with inverted polarity

---

## 1. Read the problem

Given a list of 2D points and integer `k`, return the **K POINTS CLOSEST** to the origin `(0, 0)` by Euclidean distance.

Order of returned points doesn't matter.

**Example:** `points = [[1, 3], [-2, 2]]`, `k = 1`.

Distances:
- `(1, 3)`: √(1+9) ≈ 3.16.
- `(-2, 2)`: √(4+4) ≈ 2.83.

Closer: `(-2, 2)`. Return `[[-2, 2]]`.

---

## 2. The squared-distance trick

> **Mini-refresher: avoid sqrt — compare squared distances.**
>
> Euclidean distance = `sqrt(x² + y²)`. The `sqrt` is monotonic — comparing `sqrt(a)` vs `sqrt(b)` is the same as comparing `a` vs `b` (when both non-negative).
>
> So COMPARE SQUARED distances `x² + y²` directly. No floating-point. No precision issues.
>
> Faster and more reliable.

`distSq(x, y) = x*x + y*y`.

---

## 3. The size-K max-heap approach

> **Mini-refresher: max-heap for top-K SMALLEST.**
>
> We want the K SMALLEST distances. Maintain a max-heap of size K keyed by squared distance.
>
> For each point: push. If heap size > K, pop (kicks out the LARGEST distance — i.e., the FARTHEST point).
>
> At end, heap has the K closest.

**Why max-heap for smallest-K?** The "weakest link" (the one most likely to be displaced by a new arrival) is the LARGEST of our current K. A max-heap makes that O(1) to access.

```
heap = max-heap keyed by distance² (largest at top)
for each (x, y) in points:
    push (distSq, (x, y))
    if heap.size > k: heap.pop()
return heap contents
```

O(n log k) time, O(k) space.

---

## 4. Code

**C++ — max-heap:**

```cpp
vector<vector<int>> kClosest(vector<vector<int>>& points, int k) {
    priority_queue<pair<int, int>> heap;       // (distSq, index), max-heap
    for (int i = 0; i < (int)points.size(); ++i) {
        int d = points[i][0] * points[i][0] + points[i][1] * points[i][1];
        heap.push({d, i});
        if ((int)heap.size() > k) heap.pop();
    }
    vector<vector<int>> result;
    while (!heap.empty()) {
        result.push_back(points[heap.top().second]);
        heap.pop();
    }
    return result;
}
```

**Python:**

```python
import heapq

def kClosest(points, k):
    # Python heapq is min-heap; negate for max-heap of size k
    heap = []
    for x, y in points:
        d = x*x + y*y
        heapq.heappush(heap, (-d, x, y))    # negate for max-heap
        if len(heap) > k:
            heapq.heappop(heap)
    return [[x, y] for (_, x, y) in heap]
```

Complexity: **O(n log k) time, O(k) space.**

---

## 5. Trace it

`points = [[3, 3], [5, -1], [-2, 4]]`, `k = 2`.

Distances²:
- `(3, 3)`: 18.
- `(5, -1)`: 26.
- `(-2, 4)`: 20.

```
heap = [] (max-heap).

Push (18, 0). heap = [(18, 0)].
Push (26, 1). heap = [(26, 1), (18, 0)] (26 on top).
Push (20, 2). heap = [(26, 1), (18, 0), (20, 2)]. size 3 > k=2.
  Pop top (26, 1). heap = [(20, 2), (18, 0)].

Final: heap has indices 2 and 0. Return points[2]=[-2,4], points[0]=[3,3].
```

The farthest point `(5, -1)` was correctly kicked out. ✓

---

## 6. The quickselect alternative

For O(n) AVERAGE time (vs O(n log k)), use QUICKSELECT — partition the array around a pivot by distance, recurse only into the half containing index k.

```
def quickselect(points, lo, hi, k):
    if lo >= hi: return
    pivot = distSq(points[hi])
    i = lo
    for j in range(lo, hi):
        if distSq(points[j]) < pivot:
            points[i], points[j] = points[j], points[i]
            i += 1
    points[i], points[hi] = points[hi], points[i]
    if i == k: return
    if i > k: quickselect(points, lo, i-1, k)
    else: quickselect(points, i+1, hi, k)

quickselect(points, 0, n-1, k)
return points[:k]   # the k closest, unordered
```

O(n) average; O(n²) worst-case (mitigate with random pivot).

For interviews, the HEAP approach is the standard answer. Mention quickselect for tighter complexity.

---

## 7. Common pitfalls

1. **Using a min-heap.** Tracks K LARGEST distances. Wrong for K closest.

2. **Computing `sqrt` for comparisons.** Floating-point precision issues. Use squared distance.

3. **Forgetting to pop on oversize.** Heap grows unbounded.

4. **Storing full points in heap (vs indices).** Works but copies more data. Indices are lighter.

5. **Outputting sorted-by-distance.** The problem says ANY ORDER. Don't waste time re-sorting.

6. **Computing distance INSIDE the loop iterations.** Compute ONCE per point.

---

## 8. The shape — top-K with inverted polarity

The pattern:

> **"For top-K SMALLEST (closest, lowest, etc.) — use MAX-heap of size K. For top-K LARGEST — use MIN-heap. Polarity is INVERTED from what you'd expect."**

| Problem | Top-K what | Heap polarity |
|---|---|---|
| **This problem** | K closest (smallest distance) | MAX-heap |
| Kth Largest in Stream | K largest | MIN-heap |
| Top K Frequent | K most frequent | MIN-heap by frequency |
| Sliding Window Median | median | TWO heaps |
| Find K Closest Elements (sorted array) | K closest | binary search + window |

**Pattern to internalize:**

> "Top-K bounded heap: the OPPOSITE polarity. The 'weakest link' is the one at risk of replacement — it lives at the top."

---

## Cross-references

- **Reference card (post-mastery):** [`../K_Closest_Points_to_Origin.md`](../K_Closest_Points_to_Origin.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Kth_Largest_Element_in_a_Stream.md`](./Kth_Largest_Element_in_a_Stream.md), [`Top_K_Frequent_Elements.md`](./Top_K_Frequent_Elements.md).
  - Coming next: [`Kth_Largest_Element_in_an_Array.md`](./Kth_Largest_Element_in_an_Array.md), [`Find_K_Closest_Elements.md`](./Find_K_Closest_Elements.md), [`Minimum_Cost_to_Connect_Ropes.md`](./Minimum_Cost_to_Connect_Ropes.md).
