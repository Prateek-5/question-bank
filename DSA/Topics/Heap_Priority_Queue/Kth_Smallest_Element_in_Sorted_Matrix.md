# Kth Smallest Element in Sorted Matrix

## Problem Link
https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/

## Topic
Heap Priority Queue

## Core Concept
Min-heap BFS from top-left; or binary search on value range.

## Intuition
Rows and columns are sorted. The smallest element is at (0,0); the next smallest is among (0,1) or (1,0). A min-heap expands the frontier in non-decreasing order — the k-th pop is the answer.

## Detailed Explanation
Push (matrix[0][0], 0, 0) into a min-heap. Repeatedly pop the smallest and push its right and down neighbors, marking visited. After k-1 pops, the top is the answer. An alternative O(n log(max-min)) approach binary-searches the value range and counts how many are ≤ mid per row.

## Dry Run
matrix=[[1,5,9],[10,11,13],[12,13,15]], k=8. Heap order pops: 1,5,9,10,11,12,13,13. 8th pop = 13.

## Approach
Heap + visited set — simple and O(k log k). For large matrices prefer binary search on value.

## Time and Space Complexity
Heap: O(k log k). Binary search: O(n log(max-min)).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

int kthSmallest(vector<vector<int>>& mat, int k) {
    int n = mat.size();
    using T = tuple<int,int,int>;
    priority_queue<T, vector<T>, greater<T>> pq;
    vector<vector<int>> seen(n, vector<int>(n, 0));
    pq.push({mat[0][0], 0, 0}); seen[0][0] = 1;
    while (--k) {
        auto [v, r, c] = pq.top(); pq.pop();
        if (r+1 < n && !seen[r+1][c]) { pq.push({mat[r+1][c], r+1, c}); seen[r+1][c]=1; }
        if (c+1 < n && !seen[r][c+1]) { pq.push({mat[r][c+1], r, c+1}); seen[r][c+1]=1; }
    }
    return get<0>(pq.top());
}
```

## Follow-up Questions
- Solve in O(n) per query using binary search on value.
- Handle dynamic updates (row/col sorted, but values mutate).
- Generalize to k-way sorted streams.
