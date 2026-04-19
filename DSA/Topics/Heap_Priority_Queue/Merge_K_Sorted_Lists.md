# Merge K Sorted Lists

## Problem Link
https://leetcode.com/problems/merge-k-sorted-lists/

## Topic
Heap Priority Queue

## Core Concept
Min-heap over the heads of each list.

## Intuition
To merge k sorted lists, we need the overall minimum repeatedly. A min-heap of the current heads gives that in O(log k). Each pop advances one list and pushes its next node.

## Detailed Explanation
Insert the first node of each non-empty list into a min-heap keyed by value. Pop the smallest, append to the output tail, and if it has a next pointer push that into the heap. Continue until the heap is empty.

## Dry Run
Lists: [1,4,5],[1,3,4],[2,6]. Heap heads: 1,1,2. Pop 1 (push 4). Pop 1 (push 3). Pop 2 (push 6). Heap: 3,4,4,5,6. Continue → merged: 1,1,2,3,4,4,5,6.

## Approach
Divide-and-conquer merge pairs (O(N log k)) or use a priority queue (same complexity).

## Time and Space Complexity
Time: O(N log k). Space: O(k).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct ListNode { int val; ListNode* next; ListNode(int x): val(x), next(nullptr) {} };

ListNode* mergeKLists(vector<ListNode*>& lists) {
    auto cmp = [](ListNode* a, ListNode* b){ return a->val > b->val; };
    priority_queue<ListNode*, vector<ListNode*>, decltype(cmp)> pq(cmp);
    for (auto* h : lists) if (h) pq.push(h);
    ListNode dummy(0); ListNode* tail = &dummy;
    while (!pq.empty()) {
        auto* n = pq.top(); pq.pop();
        tail->next = n; tail = n;
        if (n->next) pq.push(n->next);
    }
    return dummy.next;
}
```

## Follow-up Questions
- Pairwise merge using divide and conquer.
- External merge-sort (disk-based k-way).
- Stream-based merge with bounded memory.
