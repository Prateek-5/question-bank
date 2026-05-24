# Find K Pairs with Smallest Sums — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_K_Pairs_with_Smallest_Sums.md`](../Find_K_Pairs_with_Smallest_Sums.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/find-k-pairs-with-smallest-sums/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: when the answer space is a SORTED 2D GRID, explore it in PRIORITY ORDER using a min-heap. Push neighbors after popping.** This is K-way merge in 2D form. **Read [`Merge_Two_Sorted_Lists.md`](../../Linked_List/learn/Merge_Two_Sorted_Lists.md) and [`Last_Stone_Weight.md`](./Last_Stone_Weight.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. The brute-force O(nm) approach
3. The 2D sorted-grid insight
4. The min-heap exploration
5. Code
6. Trace it
7. The "seed first column" simplification
8. The shape — K-way merge on a grid

---

## 1. Read the problem

Given two **SORTED** integer arrays `nums1` and `nums2`, and an integer `k`, return the **K pairs `(u, v)`** with `u ∈ nums1` and `v ∈ nums2` having the **SMALLEST SUMS**.

**Example:** `nums1 = [1, 7, 11]`, `nums2 = [2, 4, 6]`, `k = 3`.

All sums sorted: 3 (1+2), 5 (1+4), 7 (1+6), 9 (7+2), 11 (7+4), 13 (7+6), 13 (11+2), 15, 17.

Top 3: `[(1,2), (1,4), (1,6)]`.

---

## 2. The brute-force O(nm) approach

Enumerate all n×m pairs, sort by sum, take first k.

```
pairs = [(nums1[i] + nums2[j], i, j) for i in 0..n-1 for j in 0..m-1]
pairs.sort()
return [(nums1[i], nums2[j]) for _, i, j in pairs[:k]]
```

O(nm log(nm)). For n = m = 10⁴, that's ~10⁸ × 8 ≈ 10⁹ — TLE.

We need to AVOID enumerating all pairs.

---

## 3. The 2D sorted-grid insight

> **Mini-refresher: the pair-sum grid is "monotone in both directions."**
>
> Imagine a 2D grid where `grid[i][j] = nums1[i] + nums2[j]`. Since both arrays are sorted:
> - Moving right (j↑): sum increases (nums2 is sorted).
> - Moving down (i↑): sum increases (nums1 is sorted).
>
> The grid is "MONOTONE." The smallest sum is at (0, 0). The k smallest sums form a STAIRCASE shape near the top-left.

We need to extract sums in increasing order WITHOUT visiting all cells.

---

## 4. The min-heap exploration

> **Mini-refresher: BFS-by-priority on a 2D grid.**
>
> Start at (0, 0) — the smallest sum. PUSH it onto a min-heap. Pop it (the global minimum); push its NEIGHBORS (i+1, j) and (i, j+1).
>
> Repeat k times: pop the smallest from the heap, record it, push its un-visited neighbors.
>
> Use a SEEN set to avoid duplicates (the same cell could be pushed from multiple predecessors).

```
heap = min-heap, push (nums1[0] + nums2[0], 0, 0)
seen = {(0, 0)}
result = []
while result.size < k and heap:
    (s, i, j) = heap.pop()
    result.append([nums1[i], nums2[j]])
    if i+1 < n and (i+1, j) not in seen:
        heap.push(nums1[i+1] + nums2[j], i+1, j)
        seen.add((i+1, j))
    if j+1 < m and (i, j+1) not in seen:
        heap.push(nums1[i] + nums2[j+1], i, j+1)
        seen.add((i, j+1))
return result
```

O(k log k) time. O(k) space.

---

## 5. Code

**C++:**

```cpp
vector<vector<int>> kSmallestPairs(vector<int>& nums1, vector<int>& nums2, int k) {
    int n = nums1.size(), m = nums2.size();
    using T = tuple<int, int, int>;
    priority_queue<T, vector<T>, greater<>> pq;
    set<pair<int, int>> seen;
    
    pq.push({nums1[0] + nums2[0], 0, 0});
    seen.insert({0, 0});
    
    vector<vector<int>> result;
    while ((int)result.size() < k && !pq.empty()) {
        auto [s, i, j] = pq.top(); pq.pop();
        result.push_back({nums1[i], nums2[j]});
        if (i + 1 < n && !seen.count({i + 1, j})) {
            pq.push({nums1[i + 1] + nums2[j], i + 1, j});
            seen.insert({i + 1, j});
        }
        if (j + 1 < m && !seen.count({i, j + 1})) {
            pq.push({nums1[i] + nums2[j + 1], i, j + 1});
            seen.insert({i, j + 1});
        }
    }
    return result;
}
```

Complexity: **O(k log k) time, O(k) space.**

---

## 6. Trace it

`nums1 = [1, 7, 11]`, `nums2 = [2, 4, 6]`, `k = 3`.

```
heap: [(3, 0, 0)]. seen: {(0, 0)}.

Pop (3, 0, 0). result = [(1, 2)]. Push (5, 0, 1), (9, 1, 0).
heap: [(5, 0, 1), (9, 1, 0)].

Pop (5, 0, 1). result = [(1, 2), (1, 4)]. Push (7, 0, 2), (11, 1, 1).
heap: [(7, 0, 2), (9, 1, 0), (11, 1, 1)].

Pop (7, 0, 2). result = [(1, 2), (1, 4), (1, 6)]. Push (13, 1, 2).

result.size = 3 = k → exit.

Return [(1,2), (1,4), (1,6)].  ✓
```

The heap NEVER held all 9 pairs — only the "frontier" of unexplored cells adjacent to processed ones.

---

## 7. The "seed first column" simplification

> **Mini-refresher: avoid the seen set by careful seeding.**
>
> Alternative: seed the heap with the FIRST COLUMN: `(nums1[i] + nums2[0], i, 0)` for each i. Then on each pop, only push the cell TO THE RIGHT — `(i, j+1)`.
>
> Each cell is reachable through EXACTLY ONE path now. No duplicates → no seen set needed.

```
for i in 0..min(k, n)-1:
    heap.push(nums1[i] + nums2[0], i, 0)

while result.size < k and heap:
    (s, i, j) = heap.pop()
    result.append([nums1[i], nums2[j]])
    if j+1 < m:
        heap.push(nums1[i] + nums2[j+1], i, j+1)
```

Cleaner code; same O(k log k).

---

## 8. The shape — K-way merge on a grid

The pattern:

> **"For SORTED-by-construction 2D answer spaces, explore in priority order using a MIN-HEAP. Push neighbors after each pop. Same as merging K sorted streams."**

| Problem | Sorted structure |
|---|---|
| **This problem** | grid of pair sums |
| Kth Smallest in Sorted Matrix | grid of matrix values |
| Merge K Sorted Lists | k separate sorted lists |
| Smallest Range Covering Elements from K Lists | similar k-way merge |
| Find Kth Smallest in N-arrays | k-way merge |

**Pattern to internalize:**

> "Whenever the answer space is a sorted 2D grid (or K sorted streams), use HEAP-DRIVEN BFS to extract elements in order. O(K log K) for the top K."

---

## Cross-references

- **Reference card (post-mastery):** [`../Find_K_Pairs_with_Smallest_Sums.md`](../Find_K_Pairs_with_Smallest_Sums.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Kth_Smallest_Element_in_Sorted_Matrix.md`](./Kth_Smallest_Element_in_Sorted_Matrix.md), [`Merge_K_Sorted_Lists.md`](./Merge_K_Sorted_Lists.md), [`Find_Median_from_Data_Stream.md`](./Find_Median_from_Data_Stream.md).
