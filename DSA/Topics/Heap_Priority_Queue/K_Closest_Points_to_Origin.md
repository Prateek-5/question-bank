# K Closest Points to Origin

**Problem Link:**
https://leetcode.com/problems/k-closest-points-to-origin/

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: State the Problem Precisely

You have an array of 2D points `points`, where `points[i] = [xi, yi]`, and an integer `k`. Return the `k` points closest to the origin `(0, 0)` by Euclidean distance. The answer can be in any order.

Example: `points = [[1, 3], [-2, 2]]`, k = 1.
- Distance from (1, 3): √(1 + 9) = √10 ≈ 3.16.
- Distance from (-2, 2): √(4 + 4) = √8 ≈ 2.83.

(-2, 2) is closer. Return `[[-2, 2]]`.

A useful simplification: Euclidean distance is `√(x² + y²)`. Since sqrt is monotonic, comparing `x² + y²` (squared distance) preserves the ordering. Use squared distance to avoid floating-point.

----------------------------------------

## Step 2: Sort Everything — Simple but Wasteful

Sort all n points by squared distance. Take the first k.

```cpp
sort(points by x² + y² ascending);
return first k points;
```

O(n log n) time. Fine for n = 10^4. But if n = 10^5 and k = 10, we're sorting 10^5 points to pick the 10 closest — wasteful.

Can we avoid sorting the losers?

----------------------------------------

## Step 3: Bounded Max-Heap

Here's the classic "bounded heap" trick. Maintain a max-heap of size k. For each incoming point:
- Push it.
- If the heap has more than k points, pop the **farthest** (the top of a max-heap).

At the end, the heap holds the k closest.

Why max-heap? Because we want to kick out the **farthest** when overfull — and the farthest of the current k+1 is naturally at a max-heap's top. We keep the k smallest by continually discarding the current largest.

This is O(n log k). Better when k is small.

```
heap: max-heap of size k keyed by squared distance.

for each point (x, y):
    dist = x² + y²
    push (dist, point) onto heap
    if heap size > k: pop the top (farthest)

return heap contents
```

----------------------------------------

## Step 4: Quickselect — Average O(n)

For the tightest asymptotic: **quickselect** partitions the array around a pivot (like quicksort), recursing only into the half containing the k-th element.

After quickselect completes, the first k elements (by distance) are on one side of the partition (unordered, but they're the right k).

```
quickselect(points, 0, n-1, k)
return points[0..k-1]
```

Expected time **O(n)**; worst case O(n²) (pathological partitioning — randomize pivot to avoid).

For interviewers who don't mind, quickselect is the most elegant answer. For simpler code, the heap version is fine.

----------------------------------------

## Step 5: Pick an Approach

Comparison:
| Approach | Time | Space |
|---|---|---|
| Sort | O(n log n) | O(1) |
| Max-heap size k | O(n log k) | O(k) |
| Quickselect | O(n) expected | O(1) |

For interviews, I'd usually show the heap version (easy to code, great worst-case) and mention quickselect for optimal average time.

----------------------------------------

## Step 6: Trace Heap Approach

`points = [[3, 3], [5, -1], [-2, 4]]`, k = 2.

Distances squared:
- (3, 3) → 18.
- (5, -1) → 26.
- (-2, 4) → 20.

Heap is max-heap, keyed by distance.

```
Push (18, [3,3]). heap: [(18, [3,3])]. size 1 ≤ k.
Push (26, [5,-1]). heap: [(26, [5,-1]), (18, [3,3])]. size 2 ≤ k.
Push (20, [-2,4]). heap: [(26, [5,-1]), (18, [3,3]), (20, [-2,4])]. size 3 > k.
  Pop top: (26, [5,-1]). heap: [(20, [-2,4]), (18, [3,3])]. size 2.
```

Final heap: [(20, [-2,4]), (18, [3,3])]. Points: [-2, 4] and [3, 3].

Correct — (5, -1) was the farthest, kicked out. ✓

----------------------------------------

## Step 7: Why Max-Heap for "Smallest K"

Intuition: we're maintaining a "reservoir" of k candidates. The weakest candidate (farthest, since we want closest) is always the most vulnerable to being replaced. Keeping the weakest at the top (max-heap) lets us check and evict in O(log k).

If we used a min-heap (smallest at top), we'd need O(k) to find and kick out the largest — much slower.

This polarity inversion is the classic "keep top-k using a heap of opposite orientation" trick. Max-heap for k-smallest, min-heap for k-largest.

----------------------------------------

## Step 8: Complexity

Heap approach: **O(n log k)** time, **O(k)** space.
Quickselect: **O(n)** average, **O(1)** space.

----------------------------------------

## Step 9: C++ Implementation

**Max-heap version:**

```cpp
vector<vector<int>> kClosest(vector<vector<int>>& points, int k) {
    // Max-heap of pairs (distance², point index).
    priority_queue<pair<int, int>> heap;

    auto distSq = [&](int i) {
        return points[i][0] * points[i][0] + points[i][1] * points[i][1];
    };

    for (int i = 0; i < (int)points.size(); ++i) {
        heap.push({distSq(i), i});
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

Using indices (not full points) in the heap to minimize copying.

**Quickselect version:**

```cpp
class Solution {
    int distSq(vector<int>& p) { return p[0] * p[0] + p[1] * p[1]; }

    void quickselect(vector<vector<int>>& pts, int lo, int hi, int k) {
        if (lo >= hi) return;
        int pivot = distSq(pts[hi]);
        int i = lo;
        for (int j = lo; j < hi; ++j) {
            if (distSq(pts[j]) < pivot) swap(pts[i++], pts[j]);
        }
        swap(pts[i], pts[hi]);
        if (i == k) return;
        if (i > k) quickselect(pts, lo, i - 1, k);
        else quickselect(pts, i + 1, hi, k);
    }

public:
    vector<vector<int>> kClosest(vector<vector<int>>& points, int k) {
        quickselect(points, 0, points.size() - 1, k);
        return vector<vector<int>>(points.begin(), points.begin() + k);
    }
};
```

After quickselect, the first k points (unordered) are the k closest.

----------------------------------------

## Step 10: Follow-up Questions

- **K farthest points.** Same template, use min-heap (keep smallest distances out; keep largest distances in).
- **3D points.** Same distance formula, add z².
- **Manhattan distance instead.** Replace the squared-distance computation.
- **Stream of points.** Heap approach works online; sort doesn't.
- **Concurrent top-k.** Needs locking or lock-free heap.
- **Why not just use distance (not squared)?** Floating-point comparisons risk precision issues. Squared distance uses integers (safer) and preserves ordering.
