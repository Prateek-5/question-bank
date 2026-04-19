# Remove Nth Node From End of List

## Problem Link
https://leetcode.com/problems/remove-nth-node-from-end-of-list/

## Topic
Linked List

## Core Concept
Two-pointer gap of n+1 nodes.

## Intuition
If one pointer moves n+1 ahead, both pointers advancing together until the lead hits null leaves the trailing pointer just before the target.

## Detailed Explanation
Dummy head; fast=slow=dummy. Advance fast n+1 steps. Then advance both until fast==null. slow->next = slow->next->next.

## Dry Run
1→2→3→4→5, n=2. After gap, slow ends at 3; remove 4 → 1→2→3→5.

## Approach
Two-pointer single pass.

## Time and Space Complexity
Time: O(L). Space: O(1).

## C++ Implementation
```cpp
struct ListNode { int val; ListNode* next; ListNode(int x):val(x),next(nullptr){} };
ListNode* removeNthFromEnd(ListNode* h, int n) {
    ListNode d(0); d.next = h;
    auto s = &d, f = &d;
    for (int i = 0; i <= n; ++i) f = f->next;
    while (f) { s = s->next; f = f->next; }
    s->next = s->next->next;
    return d.next;
}
```

## Follow-up Questions
- Remove k-th from end in doubly linked.
- Remove multiple nodes at once.
- Insert nth-from-end node.
