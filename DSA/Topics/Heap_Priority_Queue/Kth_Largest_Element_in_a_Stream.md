# Kth Largest Element in a Stream

## Problem Link
https://leetcode.com/problems/kth-largest-element-in-a-stream/

## Topic
Heap Priority Queue

## Core Concept
Bounded min-heap of size k maintained across add calls.

## Intuition
For any incoming value, we only care about keeping track of the k largest seen so far. A min-heap of size k where the top is the k-th largest is perfect and each add is O(log k).

## Detailed Explanation
Initialize: push all initial values, pop while size > k. For add(x): push x, pop if size > k, return top. This maintains invariant that heap contains the top-k values and its top is the k-th largest.

## Dry Run
k=3, nums=[4,5,8,2]. Heap=[4,5,8]. add(3): push → [3,4,5,8], pop → [4,5,8], return 4. add(5): push → [4,5,5,8], pop → [5,5,8], return 5.

## Approach
Min-heap of fixed size k. Only one heap needed.

## Time and Space Complexity
Init: O(n log k). Per add: O(log k). Space: O(k).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

class KthLargest {
    priority_queue<int, vector<int>, greater<int>> pq;
    int k;
public:
    KthLargest(int k, vector<int>& nums): k(k) {
        for (int x : nums) add(x);
    }
    int add(int x) {
        pq.push(x);
        if ((int)pq.size() > k) pq.pop();
        return pq.top();
    }
};
```

## Follow-up Questions
- What if k changes over time?
- Support delete operations.
- Return the top-k list on demand.
