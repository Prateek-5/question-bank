# Kth Smallest Element in Sorted Matrix

**Problem Link:**
<a href="https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/</a>

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: Understand the Matrix Structure

Given an `n × n` matrix where:
- Each **row** is sorted ascending.
- Each **column** is sorted ascending.

Find the **k-th smallest** element.

Example:
```
matrix = [
    [ 1,  5,  9],
    [10, 11, 13],
    [12, 13, 15]
]
k = 8
```

Flattened and sorted: [1, 5, 9, 10, 11, 12, 13, 13, 15]. 8th smallest = **13** (the second 13).

Note: both rows and columns are sorted, but the full flattened matrix is **not** sorted (e.g., 5 < 10 is OK, but 9 > 5 comes after 1 in row-major order). So we can't just index directly.

----------------------------------------

## Step 2: Naive — Flatten and Sort

```cpp
vector<int> all;
for (auto& row : matrix) for (int x : row) all.push_back(x);
sort(all.begin(), all.end());
return all[k - 1];
```

O(n² log n) time. For large n, wasteful.

Can we exploit the sorted rows/columns?

----------------------------------------

## Step 3: Observation — Merging Sorted Rows

Each row is sorted. Merging n sorted sequences and taking the k-th element is the classic **k-way merge**.

Use a min-heap seeded with the first element of each row. Repeatedly:
- Pop the smallest (that's the next overall smallest).
- From the same row, push the next element if any.

After k pops, the last popped is the k-th smallest.

```
heap seeded with (matrix[i][0], i, 0) for each row i
for _ in range(k):
    (val, row, col) = heap.pop()
    if col + 1 < n: heap.push((matrix[row][col+1], row, col+1))
return val
```

Time: **O(k log n)**. Heap size ≤ n.

----------------------------------------

## Step 4: Trace on the Example

`matrix = [[1, 5, 9], [10, 11, 13], [12, 13, 15]]`, k = 8.

Seed heap: (1, 0, 0), (10, 1, 0), (12, 2, 0).

Pops (1-indexed):
```
1: pop (1, 0, 0). Push (5, 0, 1). Heap: {5, 10, 12}.
2: pop (5, 0, 1). Push (9, 0, 2). Heap: {9, 10, 12}.
3: pop (9, 0, 2). No next in row 0. Heap: {10, 12}.
4: pop (10, 1, 0). Push (11, 1, 1). Heap: {11, 12}.
5: pop (11, 1, 1). Push (13, 1, 2). Heap: {12, 13}.
6: pop (12, 2, 0). Push (13, 2, 1). Heap: {13, 13}.
7: pop (13, ?, ?). Let's say the one from row 1. Push nothing or the next depending on position.
  Actually after 7 pops, we've popped 1, 5, 9, 10, 11, 12, 13. Next pop is the 8th.
8: pop (13, ...). That's our 13.
```

Return 13. ✓

----------------------------------------

## Step 5: Even Better — Binary Search on Value

There's a slicker O(n log(max - min)) approach.

The answer lies in [matrix[0][0], matrix[n-1][n-1]]. Binary search over this **value range**.

For any candidate value `v`, count how many matrix elements are `≤ v`. Since rows and columns are sorted, we can count efficiently using a staircase walk from the top-right (or bottom-left).

Counting in O(n) per check:
```
count = 0
row = n - 1, col = 0
while row >= 0 and col < n:
    if matrix[row][col] <= v:
        count += row + 1    # all cells in this column from 0..row are ≤ v
        col++
    else:
        row--
```

Binary search on v; total time: O(n · log(max - min)).

Which to pick: for typical constraints, both are fine. Heap is simpler. Binary search is tighter when max-min is small.

----------------------------------------

## Step 6: Why the Heap Approach Is Correct

**Claim:** after k pops from the min-heap, the last popped is the k-th smallest.

**Proof sketch:** heap always holds one candidate from each "active" row — the smallest un-popped element. Popping the heap's top gives us the global minimum among all un-popped elements. Inductively, k pops yield the k smallest, in order.

Why don't we need to track columns? Each row's "current" column starts at 0 and advances each time we pop from that row. The heap entry `(val, row, col)` tells us where to go next.

----------------------------------------

## Step 7: Name It

**K-way merge via min-heap.** Same structure as Merge K Sorted Lists, just applied to the rows of a sorted matrix.

The binary-search-on-value approach is a different pattern: **"search the answer space when the answer is numeric."**

----------------------------------------

## Step 8: Complexity

Heap approach: **O(k log n)** time, **O(n)** space.
Binary search approach: **O(n log(max - min))** time, **O(1)** space.

For k = O(n²) both are comparable.

----------------------------------------

## Step 9: C++ Implementation

**Heap version:**

```cpp
int kthSmallest(vector<vector<int>>& matrix, int k) {
    int n = matrix.size();
    // Min-heap of tuples (value, row, col).
    priority_queue<tuple<int, int, int>, vector<tuple<int, int, int>>, greater<>> heap;
    for (int i = 0; i < n; ++i) {
        heap.push({matrix[i][0], i, 0});
    }

    int val = 0;
    for (int i = 0; i < k; ++i) {
        auto [v, r, c] = heap.top(); heap.pop();
        val = v;
        if (c + 1 < n) heap.push({matrix[r][c + 1], r, c + 1});
    }
    return val;
}
```

**Binary search version:**

```cpp
int kthSmallest(vector<vector<int>>& matrix, int k) {
    int n = matrix.size();
    int lo = matrix[0][0], hi = matrix[n - 1][n - 1];

    auto countLessOrEqual = [&](int v) {
        int count = 0;
        int row = n - 1, col = 0;
        while (row >= 0 && col < n) {
            if (matrix[row][col] <= v) {
                count += row + 1;
                col++;
            } else {
                row--;
            }
        }
        return count;
    };

    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (countLessOrEqual(mid) < k) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
```

Both return the correct k-th smallest.

----------------------------------------

## Step 10: Follow-up Questions

- **K-th largest in the same matrix.** Symmetric — max-heap or binary search with "count ≥".
- **K-th smallest in an M-sorted-by-row matrix (but not column-sorted).** Heap works; binary search becomes trickier.
- **Return the (row, col) of the k-th smallest.** Augment the heap entry.
- **Multiple queries for different k's.** Precomputing a sorted flat array once is O(n² log n) then O(1) per query. Good for many queries.
- **Streaming matrix (rows arrive over time).** Merge incoming rows into the heap as they appear.
