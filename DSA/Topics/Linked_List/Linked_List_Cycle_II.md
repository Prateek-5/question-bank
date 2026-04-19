# Linked List Cycle II

## Problem Link
https://leetcode.com/problems/linked-list-cycle-ii/

## Topic
Linked List

## Core Concept
Floyd's algorithm — after meeting, reset one pointer to head.

## Intuition
If slow and fast meet inside the cycle, the distance from head to start equals the distance from meeting point to start (mod cycle length). Reset one to head and advance both one step at a time to find the cycle's entry.

## Detailed Explanation
Detect meeting. Then slow=head; move both one step until they meet — that's the cycle start.

## Dry Run
1→2→3→4→5→3. Slow/fast meet inside. Reset slow to 1; both step → meet at node 3.

## Approach
Floyd's phase 2.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
struct ListNode { int val; ListNode* next; };
ListNode* detectCycle(ListNode* h) {
    auto s = h, f = h;
    while (f && f->next) {
        s = s->next; f = f->next->next;
        if (s == f) { s = h; while (s != f) { s = s->next; f = f->next; } return s; }
    }
    return nullptr;
}
```

## Follow-up Questions
- Cycle length calculation.
- Remove the cycle.
- Multiple lists sharing nodes.
