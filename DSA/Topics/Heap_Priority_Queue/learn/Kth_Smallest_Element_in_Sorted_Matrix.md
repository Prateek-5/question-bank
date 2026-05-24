# Kth Smallest Element in Sorted Matrix — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Kth_Smallest_Element_in_Sorted_Matrix.md`](../Kth_Smallest_Element_in_Sorted_Matrix.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **Two distinct approaches: HEAP (K-way merge of sorted rows) and BINARY SEARCH on VALUE.** Both reach optimal complexity. The lesson: **K-way merge generalizes — if the data is "K sorted streams," use a min-heap.** **Read [`Find_K_Pairs_with_Smallest_Sums.md`](./Find_K_Pairs_with_Smallest_Sums.md) first.**

**Map of this file (8 sections):**

1. Read the problem
2. The naive flatten + sort
3. K-way merge of rows
4. Binary search on value
5. Code (both)
6. Trace it
7. Comparing approaches
8. The shape — K-way merge

---

## 1. Read the problem

Given an `n × n` matrix where each ROW is sorted ascending AND each COLUMN is sorted ascending, find the **K-th SMALLEST** element.

**Example:**
```
matrix = [[ 1,  5,  9],
          [10, 11, 13],
          [12, 13, 15]]
k = 8
```

Sorted flatten: `[1, 5, 9, 10, 11, 12, 13, 13, 15]`. 8th smallest = **13**.

(The matrix is NOT globally sorted in row-major order — e.g., 9 (row 0) > 5 (row 0) but the next row starts at 10. Rows and columns are each sorted, but the global flatten is mixed.)

---

## 2. The naive flatten + sort

```
flatten = [v for row in matrix for v in row]
flatten.sort()
return flatten[k-1]
```

O(n² log n). Doesn't exploit row/column sortedness.

---

## 3. K-way merge of rows

> **Mini-refresher: each ROW is a sorted sequence; merge k of them.**
>
> Seed a min-heap with the FIRST element of each row: `(matrix[i][0], i, 0)` for i = 0..n-1.
>
> Pop the smallest. The "next" candidate from the SAME ROW is at column j+1. Push it.
>
> Repeat K times. The K-th pop is the answer.

```
heap = min-heap of (value, row, col)
for i in 0..n-1: heap.push((matrix[i][0], i, 0))

for _ in range(k):
    (v, r, c) = heap.pop()
    if c + 1 < n: heap.push((matrix[r][c+1], r, c+1))

return v   # last popped
```

O(K log n) time, O(n) space.

---

## 4. Binary search on value

Alternative: BINARY-SEARCH the value range [matrix[0][0], matrix[n-1][n-1]]. For each candidate value `v`, count how many matrix entries are ≤ v.

Counting can be done in O(n) using a "staircase" walk:
- Start at top-right (or bottom-left).
- If current ≤ v: this cell AND everything in this column (or all rows above) is ≤ v. Move right (or down).
- Else: move down (or up).

Adjust the search until count == k AND v is in the matrix.

```
lo, hi = matrix[0][0], matrix[n-1][n-1]
while lo < hi:
    mid = (lo + hi) // 2
    if count_le(matrix, mid) < k:
        lo = mid + 1
    else:
        hi = mid
return lo
```

O(n log(max - min)) time, O(1) space.

---

## 5. Code (both)

**C++ — heap:**

```cpp
int kthSmallest(vector<vector<int>>& matrix, int k) {
    int n = matrix.size();
    using T = tuple<int, int, int>;
    priority_queue<T, vector<T>, greater<>> heap;
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

**C++ — binary search:**

```cpp
int kthSmallest(vector<vector<int>>& matrix, int k) {
    int n = matrix.size();
    int lo = matrix[0][0], hi = matrix[n - 1][n - 1];

    auto countLE = [&](int v) {
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
        if (countLE(mid) < k) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}
```

Complexity:
- Heap: O(K log n).
- Binary search: O(n log(max - min)).

---

## 6. Trace it

**Heap on the example, k = 8:**

Seed: heap = [(1, 0, 0), (10, 1, 0), (12, 2, 0)].

```
i=1: pop (1, 0, 0). Push (5, 0, 1). Heap = [(5, 0, 1), (10, 1, 0), (12, 2, 0)].
i=2: pop (5, 0, 1). Push (9, 0, 2). Heap = [(9, 0, 2), (10, 1, 0), (12, 2, 0)].
i=3: pop (9, 0, 2). No more in row 0. Heap = [(10, 1, 0), (12, 2, 0)].
i=4: pop (10, 1, 0). Push (11, 1, 1). Heap = [(11, 1, 1), (12, 2, 0)].
i=5: pop (11, 1, 1). Push (13, 1, 2). Heap = [(12, 2, 0), (13, 1, 2)].
i=6: pop (12, 2, 0). Push (13, 2, 1). Heap = [(13, 1, 2), (13, 2, 1)].
i=7: pop (13, ?). Heap = [(13, ?)].
i=8: pop (13, ?). Return 13.  ✓
```

---

## 7. Comparing approaches

| Approach | Time | Space | When to prefer |
|---|---|---|---|
| **Heap (K-way merge)** | O(K log n) | O(n) | When K ≤ n² is moderate; clean code |
| **Binary search on value** | O(n log(max-min)) | O(1) | When K is large (close to n²); memory-tight |

Both are accepted on LeetCode. Heap is more intuitive; binary search is more elegant.

---

## 8. The shape — K-way merge

The pattern:

> **"For K SORTED SEQUENCES (lists, rows, columns), merge them via a MIN-HEAP. Heap size ≤ K, total cost O(N log K)."**

| Problem | The K sequences |
|---|---|
| **This problem** | matrix rows |
| Merge K Sorted Lists | linked lists |
| Find K Pairs with Smallest Sums | conceptual rows of the pair grid |
| Smallest Range Covering Elements from K Lists | similar |
| Merge K Sorted Files (external) | files on disk |

**Pattern to internalize:**

> "K-way merge = MIN-HEAP of K candidate heads. Pop the smallest, push its successor. O(N log K) total — much better than a separate full sort."

---

## Cross-references

- **Reference card (post-mastery):** [`../Kth_Smallest_Element_in_Sorted_Matrix.md`](../Kth_Smallest_Element_in_Sorted_Matrix.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Find_K_Pairs_with_Smallest_Sums.md`](./Find_K_Pairs_with_Smallest_Sums.md), [`Minimum_Cost_to_Connect_Ropes.md`](./Minimum_Cost_to_Connect_Ropes.md).
  - Coming next: [`Merge_K_Sorted_Lists.md`](./Merge_K_Sorted_Lists.md), [`Find_Median_from_Data_Stream.md`](./Find_Median_from_Data_Stream.md).
