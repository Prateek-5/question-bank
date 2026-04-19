# K Closest Points to Origin

## Problem Link
https://leetcode.com/problems/k-closest-points-to-origin/

## Topic
Heap Priority Queue

## Core Concept
Max-heap of size k keyed by squared distance — keeps k smallest.

## Intuition
We want the k points nearest to the origin. A max-heap of size k acts as a filter: if a new point has smaller distance than the heap top, it replaces it. After processing, the heap holds the k closest.

## Detailed Explanation
For each point, compute d² = x²+y² (avoid sqrt to keep integers). Push into a max-heap. If size exceeds k, pop the largest. After the loop, the heap contains the k closest. Alternatively, use nth_element / quickselect for O(n) average.

## Dry Run
points = [[1,3],[-2,2]], k=1. d² = 10 and 8. Heap after insert: [10]. Next push 8, size>1, pop 10 → heap [8]. Result: point with d²=8 → [-2,2].

## Approach
Heap of size k with custom comparator by distance. Pop when size > k. Output the heap contents.

## Time and Space Complexity
Time: O(n log k). Space: O(k).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

vector<vector<int>> kClosest(vector<vector<int>>& points, int k) {
    auto cmp = [](auto& a, auto& b){
        return a[0]*a[0]+a[1]*a[1] < b[0]*b[0]+b[1]*b[1];
    };
    priority_queue<vector<int>, vector<vector<int>>, decltype(cmp)> pq(cmp);
    for (auto& p : points) {
        pq.push(p);
        if ((int)pq.size() > k) pq.pop();
    }
    vector<vector<int>> res;
    while (!pq.empty()) { res.push_back(pq.top()); pq.pop(); }
    return res;
}
```

## Follow-up Questions
- Solve in O(n) average using Quickselect.
- Solve when points stream in one by one.
- Support weighted distances (e.g., Manhattan).
