# Convert Binary Number in a Linked List to Integer

## Problem Link
https://leetcode.com/problems/convert-binary-number-in-a-linked-list-to-integer/

## Topic
Linked List

## Core Concept
Left-shift accumulator while traversing.

## Intuition
Process bits from MSB to LSB: res = res*2 + node.val.

## Detailed Explanation
Traverse the list, updating res.

## Dry Run
1→0→1 → 101₂=5.

## Approach
Single pass.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
struct ListNode { int val; ListNode* next; };
int getDecimalValue(ListNode* h) {
    int r = 0;
    while (h) { r = r * 2 + h->val; h = h->next; }
    return r;
}
```

## Follow-up Questions
- Big integer (BigInt) support.
- Base other than 2.
- LSB-first list.
