# Kth Largest Element in an Array

## Problem Link
https://leetcode.com/problems/kth-largest-element-in-an-array/

## Topic
Heap Priority Queue

## Core Concept
Min-heap of size k, or Quickselect.

## Intuition
Keep the k largest seen so far in a min-heap. The smallest among them (heap top) is the k-th largest overall after processing all elements.

## Detailed Explanation
Iterate numbers, push into a min-heap, and pop when size > k. Final heap top is the answer. Quickselect partitions around a pivot and recurses into the half containing the k-th index for O(n) average.

## Dry Run
nums=[3,2,1,5,6,4], k=2. Heap: 3, [2,3], [1,2,3] (pop 1) → [2,3], push 5 → pop 2 → [3,5], push 6 → pop 3 → [5,6], push 4 (size=3>2) pop 4 → [5,6]. Top=5.

## Approach
Heap is simple and stable. Quickselect is faster on average but has O(n²) worst case unless randomized.

## Time and Space Complexity
Heap: O(n log k). Quickselect: O(n) avg.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

int findKthLargest(vector<int>& nums, int k) {
    priority_queue<int, vector<int>, greater<int>> pq;
    for (int x : nums) {
        pq.push(x);
        if ((int)pq.size() > k) pq.pop();
    }
    return pq.top();
}
```

## Follow-up Questions
- Implement via Quickselect.
- Find the k-th smallest instead.
- Stream version with online updates.
