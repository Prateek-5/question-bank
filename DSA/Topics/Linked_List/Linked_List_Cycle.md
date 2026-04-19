# Linked List Cycle

## Problem Link
https://leetcode.com/problems/linked-list-cycle/

## Topic
Linked List

## Core Concept
Floyd's tortoise and hare — two pointers at different speeds.

## Intuition
If there is a cycle, a fast pointer (2 steps) will eventually lap a slow pointer (1 step) inside the cycle.

## Detailed Explanation
slow=fast=head. While fast && fast->next: slow=slow->next; fast=fast->next->next; if they meet return true. Else false.

## Dry Run
1→2→3→4→2. fast cycles and meets slow.

## Approach
Two-pointer cycle detection.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
struct ListNode { int val; ListNode* next; };
bool hasCycle(ListNode* h) {
    auto s = h, f = h;
    while (f && f->next) {
        s = s->next; f = f->next->next;
        if (s == f) return true;
    }
    return false;
}
```

## Follow-up Questions
- Detect cycle start (Cycle II).
- Length of the cycle.
- Multi-cycle scenarios (impossible in singly linked lists).
