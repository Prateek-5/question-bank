# Reverse Linked List

## Problem Link
https://leetcode.com/problems/reverse-linked-list/

## Topic
Linked List

## Core Concept
Iterative pointer rotation.

## Intuition
Walk the list reversing each next pointer by remembering the previous node.

## Detailed Explanation
prev=null, cur=head. While cur: next=cur->next; cur->next=prev; prev=cur; cur=next. Return prev.

## Dry Run
1→2→3 → 3→2→1.

## Approach
Three-pointer sweep.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
struct ListNode { int val; ListNode* next; };
ListNode* reverseList(ListNode* h) {
    ListNode* prev = nullptr;
    while (h) { auto* n = h->next; h->next = prev; prev = h; h = n; }
    return prev;
}
```

## Follow-up Questions
- Recursive reverse.
- Reverse only a sub-range (Reverse II).
- Reverse in groups of k.
