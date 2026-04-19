# Find Median from Data Stream

## Problem Link
https://leetcode.com/problems/find-median-from-data-stream/

## Topic
Heap Priority Queue

## Core Concept
Two heaps: max-heap for lower half, min-heap for upper half.

## Intuition
The median is the middle of a sorted stream. Maintain two halves — the smaller half (max-heap on top) and the larger half (min-heap on top). Balance sizes so the median is either the top of the larger heap or the average of both tops.

## Detailed Explanation
On add: push into max-heap, then move its top into the min-heap (to keep ordering). If min-heap grows larger, move its top back to max-heap. This keeps max-heap size ≥ min-heap size by at most 1. Median is max-heap top (odd total) or average of both tops (even total).

## Dry Run
Add 1 → lo=[1], hi=[]; median=1. Add 2 → lo=[1], hi=[2]; median=1.5. Add 3 → lo=[2,1], hi=[3]; median=2. Add 4 → lo=[2,1], hi=[3,4]; median=2.5.

## Approach
Use std::priority_queue (max-heap by default) and one with greater<> (min-heap). Rebalance after every insert. O(log n) insert, O(1) query.

## Time and Space Complexity
Time: O(log n) per add, O(1) per median. Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

class MedianFinder {
    priority_queue<int> lo; // max-heap
    priority_queue<int, vector<int>, greater<int>> hi; // min-heap
public:
    void addNum(int x) {
        lo.push(x);
        hi.push(lo.top()); lo.pop();
        if (hi.size() > lo.size()) { lo.push(hi.top()); hi.pop(); }
    }
    double findMedian() {
        if (lo.size() > hi.size()) return lo.top();
        return (lo.top() + hi.top()) / 2.0;
    }
};
```

## Follow-up Questions
- What if the stream contains only integers in [0,100]? Use a bucket/count array.
- What if 99% of values are in [0,100] but some are outside?
- Support removeNum(x) — use multisets or lazy deletion.
