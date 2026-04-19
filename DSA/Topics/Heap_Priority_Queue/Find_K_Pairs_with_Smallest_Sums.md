# Find K Pairs with Smallest Sums

## Problem Link
https://leetcode.com/problems/find-k-pairs-with-smallest-sums/

## Topic
Heap Priority Queue

## Core Concept
Min-heap over pair indices — BFS-like expansion from the smallest sum.

## Intuition
Sorted arrays nums1 and nums2 mean the smallest possible sum is nums1[0] + nums2[0]. The next smallest comes from expanding either the first-array or second-array index. Treat it like a shortest-path expansion in a grid of sums.

## Detailed Explanation
Push (nums1[0]+nums2[0], 0, 0) into a min-heap. Pop the smallest pair, record it, and push its neighbors (i+1, j) and (i, j+1). Use a visited set to avoid duplicates. Stop when we have k pairs or the heap is empty. This explores sums in non-decreasing order.

## Dry Run
nums1 = [1,7,11], nums2 = [2,4,6], k = 3. Heap: (3,0,0). Pop (1,2). Push (5,1,0),(7,0,1). Pop (5,1,0) → (7,2). Push (9,2,0),(11,1,1). Pop (7,0,1) → (1,4). Result = [[1,2],[7,2],[1,4]].

## Approach
Start at corner (0,0), grow the frontier via a min-heap of sums. Mark visited cells. This yields the k smallest sums efficiently without enumerating all n*m pairs.

## Time and Space Complexity
Time: O(k log k). Space: O(k) for heap and visited set.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

vector<vector<int>> kSmallestPairs(vector<int>& a, vector<int>& b, int k) {
    using T = tuple<int,int,int>;
    priority_queue<T, vector<T>, greater<T>> pq;
    set<pair<int,int>> seen;
    pq.push({a[0]+b[0], 0, 0});
    seen.insert({0,0});
    vector<vector<int>> res;
    while (k-- && !pq.empty()) {
        auto [s, i, j] = pq.top(); pq.pop();
        res.push_back({a[i], b[j]});
        if (i+1 < (int)a.size() && !seen.count({i+1,j})) {
            pq.push({a[i+1]+b[j], i+1, j}); seen.insert({i+1,j});
        }
        if (j+1 < (int)b.size() && !seen.count({i,j+1})) {
            pq.push({a[i]+b[j+1], i, j+1}); seen.insert({i,j+1});
        }
    }
    return res;
}
```

## Follow-up Questions
- Generalize to k sorted arrays (Merge k Sorted Lists).
- What if arrays are not sorted? Pre-sort first — O(n log n + k log k).
- Solve the k-th smallest sum (return only one value).
