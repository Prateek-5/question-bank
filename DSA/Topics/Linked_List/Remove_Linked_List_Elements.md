# Remove Linked List Elements

## Problem Link
https://leetcode.com/problems/remove-linked-list-elements/

## Topic
Linked List

## Core Concept
Dummy head with filter pass.

## Intuition
A dummy head simplifies removing the actual head. Walk with a prev pointer skipping nodes whose value matches.

## Detailed Explanation
dummy->next=head. prev=dummy. While prev->next: if prev->next->val==val unlink; else advance prev.

## Dry Run
List 1→2→6→3→6, val=6 → 1→2→3.

## Approach
Single pass.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
struct ListNode { int val; ListNode* next; ListNode(int x):val(x),next(nullptr){} };
ListNode* removeElements(ListNode* h, int v) {
    ListNode d(0); d.next = h;
    auto p = &d;
    while (p->next) {
        if (p->next->val == v) p->next = p->next->next;
        else p = p->next;
    }
    return d.next;
}
```

## Follow-up Questions
- Remove all duplicates (keep distinct).
- Recursive version.
- Remove by predicate function.
