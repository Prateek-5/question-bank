# Delete Node in a Linked List

## Problem Link
https://leetcode.com/problems/delete-node-in-a-linked-list/

## Topic
Linked List

## Core Concept
Copy next node's data and bypass it.

## Intuition
Without access to head or prev, we can't unlink this node. Instead, overwrite its value with next's, then unlink next.

## Detailed Explanation
node.val = node.next.val; node.next = node.next.next;

## Dry Run
List 4→5→1→9, delete 5. Copy 1 into 5's slot → 4→1→1→9. Remove the duplicate by linking to 9 → 4→1→9.

## Approach
Overwrite-next trick.

## Time and Space Complexity
O(1).

## C++ Implementation
```cpp
struct ListNode { int val; ListNode* next; };
void deleteNode(ListNode* n) { n->val = n->next->val; n->next = n->next->next; }
```

## Follow-up Questions
- When the node is the tail — undefined; must have prev.
- Delete all occurrences of value (requires traversal).
- Delete range of nodes.
