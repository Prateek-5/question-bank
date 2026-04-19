# Merge Two Sorted Lists

## Problem Link
https://leetcode.com/problems/merge-two-sorted-lists/

## Topic
Linked List

## Core Concept
Iterative or recursive merge using a dummy head.

## Intuition
At each step pick the smaller head and advance. Continue until one list empties, then attach the rest.

## Detailed Explanation
Dummy head d; tail=d. While both non-null: pick smaller, attach, advance. Attach remaining list.

## Dry Run
A:1→2→4, B:1→3→4. Merged: 1→1→2→3→4→4.

## Approach
Two-pointer merge with dummy.

## Time and Space Complexity
Time: O(n+m). Space: O(1).

## C++ Implementation
```cpp
struct ListNode { int val; ListNode* next; ListNode(int x):val(x),next(nullptr){} };
ListNode* mergeTwoLists(ListNode* a, ListNode* b) {
    ListNode d(0); auto t = &d;
    while (a && b) {
        if (a->val <= b->val) { t->next = a; a = a->next; }
        else { t->next = b; b = b->next; }
        t = t->next;
    }
    t->next = a ? a : b;
    return d.next;
}
```

## Follow-up Questions
- Merge k sorted lists (heap).
- Merge in place without dummy.
- Merge by a custom comparator.
