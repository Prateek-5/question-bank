# Palindrome Linked List

## Problem Link
https://leetcode.com/problems/palindrome-linked-list/

## Topic
Linked List

## Core Concept
Find middle, reverse second half, compare halves.

## Intuition
Comparing across the list with O(1) memory needs us to mirror the second half by reversing.

## Detailed Explanation
Find middle (slow/fast). Reverse slow (second half). Walk both halves comparing values. Optionally restore the list.

## Dry Run
1→2→2→1. Middle at 2 (second). Reverse second → 1→2. Compare 1,2 with 1,2 → palindrome.

## Approach
In-place O(1) memory.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
struct ListNode { int val; ListNode* next; };
ListNode* rev(ListNode* h) { ListNode* p = nullptr; while (h) { auto* n = h->next; h->next = p; p = h; h = n; } return p; }
bool isPalindrome(ListNode* h) {
    auto s = h, f = h;
    while (f && f->next) { s = s->next; f = f->next->next; }
    auto r = rev(s);
    while (r) { if (h->val != r->val) return false; h = h->next; r = r->next; }
    return true;
}
```

## Follow-up Questions
- Without modifying the list (stack-based).
- Doubly linked list palindrome.
- Palindromic partitions.
