# Middle of the Linked List

## Problem Link
https://leetcode.com/problems/middle-of-the-linked-list/

## Topic
Linked List

## Core Concept
Slow/fast pointers.

## Intuition
Fast moves 2 steps for slow's 1. When fast reaches the end, slow is at the middle.

## Detailed Explanation
slow=fast=head. While fast && fast->next: slow=slow->next; fast=fast->next->next. Return slow.

## Dry Run
1→2→3→4→5. slow ends at 3.

## Approach
Tortoise-hare.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
struct ListNode { int val; ListNode* next; };
ListNode* middleNode(ListNode* h) {
    auto s = h, f = h;
    while (f && f->next) { s = s->next; f = f->next->next; }
    return s;
}
```

## Follow-up Questions
- Return the first middle in even length.
- Find k-th from middle.
- Middle element removal.
