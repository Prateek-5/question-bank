# Linked List — Concepts

## Core Theory
Linked lists store nodes connected by pointers. Singly linked lists support O(1) insert/delete at known nodes but O(n) random access. Most operations benefit from a dummy head to simplify edge cases.

## Common Patterns
- **Slow/fast pointers** (middle, cycle, k-th from end).
- **Reverse a sublist** by pointer rearrangement.
- **Dummy head** for cleaner insert/delete.
- **Merge k sorted lists** via min-heap.

## When to Use
When dynamic sizes and fast insert/delete at known positions matter, and random access isn't needed.

## Template
```cpp
struct ListNode { int val; ListNode* next; };
ListNode* reverse(ListNode* h) {
    ListNode* p = nullptr;
    while (h) { auto n = h->next; h->next = p; p = h; h = n; }
    return p;
}
```

## Common Mistakes
- Forgetting to update the last node's next to null after reversal.
- Losing track of head when manipulating pointers.
- Using recursion and hitting stack-overflow on long lists.
