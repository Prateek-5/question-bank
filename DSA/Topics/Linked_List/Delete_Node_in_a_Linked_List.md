# Delete Node in a Linked List

**Problem Link:**
https://leetcode.com/problems/delete-node-in-a-linked-list/

**Topic:**
Linked List

----------------------------------------

## Step 1: The Strange Setup

Normally, "delete a node from a linked list" means: given the head and a target value, traverse and remove the node.

This problem is different. You're given **only the node to delete** — not the head. The node is **guaranteed not to be the tail** (i.e., there's a next node).

Delete that node such that the list's values, as a sequence, are effectively reduced by one.

Example: List is `4 → 5 → 1 → 9`. Given a pointer to node with value 5, the list should become `4 → 1 → 9`.

----------------------------------------

## Step 2: Why This Is Tricky

Usual deletion: walk to the node BEFORE the target, then rewire `prev.next = target.next`. But we don't have access to the previous node (no head to walk from, no prev pointer).

Brute force: walk the list from the target onward, remembering the data but shifting nothing. That doesn't help because we can't reach prev.

**Clever trick:** instead of deleting the given node, **overwrite its value with the next node's value** and then delete the next node.

After:
- Given node N with value 5. Next node M with value 1.
- Copy M's value into N: N.val = 1.
- N.next = M.next.
- Result: the list looks like 4 → 1 → 9, with the actual node M unlinked.

We haven't physically removed the "5" node — we've **effectively relabeled it** and unlinked the one after it.

----------------------------------------

## Step 3: Implementation

```
def deleteNode(node):
    node.val = node.next.val
    node.next = node.next.next
```

Two lines. That's the entire solution.

Why does this work?
- The list's **values** are what matter externally (printing, iterating, etc.).
- We change the given node's value to what the next node had. Then unlink the next node.
- Semantically equivalent to "removing the original node."

----------------------------------------

## Step 4: Trace on `4 → 5 → 1 → 9`

Given: pointer to the node with value 5. Call it N.

```
Before:
  4 -> 5 -> 1 -> 9
       N

Step 1: N.val = N.next.val = 1. Now the "5" node holds value 1.
  4 -> 1 -> 1 -> 9
       N    M

Step 2: N.next = N.next.next = 9 (skipping M).
  4 -> 1 -> 9
       N
```

Result: values are 4, 1, 9. Effectively, the "5" was deleted. ✓

The original physical node holding "5" is still in memory, but it's been repurposed to hold "1". The physical node holding "1" originally is now unreachable (and can be garbage collected / freed).

----------------------------------------

## Step 5: Why "Not the Tail" Matters

If the given node were the tail, it wouldn't have a next node — nothing to "slide into its place." We'd need access to the previous node, which we don't have.

The problem's guarantee that the given node isn't the tail is what makes the trick applicable.

In real-world code that might encounter tails, we'd handle it separately (possibly with a "NULL sentinel" or by refusing to delete the tail without a prev pointer).

----------------------------------------

## Step 6: Name It

This is a clever **pointer aliasing trick**. Rather than physically removing the node, we alias it to the next node's role and remove the next one instead.

Related ideas:
- Copying-before-deletion in concurrent structures.
- Tombstone marking in garbage-collected systems.
- Indirect-deletion via role-shifting.

It's a reminder that "remove this node" at a high level can be implemented by "overwrite its contents" at a low level.

----------------------------------------

## Step 7: Complexity

Time: **O(1)** — two pointer operations, no traversal.
Space: **O(1)**.

----------------------------------------

## Step 8: C++ Implementation

```cpp
void deleteNode(ListNode* node) {
    node->val = node->next->val;
    node->next = node->next->next;
}
```

Two lines. The "node" passed in is no longer logically the same node — it's been retooled to be its successor.

Subtle point in C++: the original `node->next` node is now orphaned. In a garbage-collected language (Java, Python), this gets reclaimed automatically. In C++, we should technically `delete` the old next node to avoid a memory leak:

```cpp
void deleteNode(ListNode* node) {
    ListNode* next = node->next;
    node->val = next->val;
    node->next = next->next;
    delete next;
}
```

Depending on how the list was constructed (nodes may not own their memory), this may or may not be safe. LeetCode typically doesn't test for the leak, so the two-line version is accepted.

----------------------------------------

## Step 9: Follow-up Questions

- **What if we allow deleting the tail?** Need prev pointer — walk from head, or use a doubly-linked list.
- **Delete all nodes with a specific value.** Walk with a prev pointer; standard algorithm.
- **Delete the k-th node from the end.** Use two pointers (like Remove Nth from End).
- **Doubly linked list version.** Trivially O(1) because we have prev pointers.
- **What if the value is sensitive and we can't copy it?** Need a different approach — must have prev pointer somehow.
- **Modify the algorithm to delete *two* nodes (this one and the next).** Skip one more: `node.val = node.next.next.val; node.next = node.next.next.next`.
