# Delete Node in a Linked List — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Delete_Node_in_a_Linked_List.md`](../Delete_Node_in_a_Linked_List.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/delete-node-in-a-linked-list/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **This is a famous "lateral thinking" puzzle.** The lesson: **when you can't reach the node BEFORE the target, you can change WHAT THE TARGET HOLDS instead of WHICH NODE EXISTS.** This "alias and shift" trick reappears in many in-place modification problems. **Read [`Design_Linked_List.md`](./Design_Linked_List.md) first** for the basic node mechanics.

**Map of this file (8 short sections):**

1. Read the problem (this one's unusual)
2. Why the standard approach can't work
3. The pivot — change the VALUE, not the structure
4. The trick
5. Code
6. Trace it
7. The "not the tail" caveat
8. Common pitfalls + transfer

---

## 1. Read the problem (this one's unusual)

**Standard linked-list deletion:** given the head and a target node (or value), walk the list, find the predecessor, splice out.

**This problem:** you're given ONLY the node to delete — **NOT the head**.

Constraints:
- The given node is NOT the tail (it has a `next`).
- You cannot access the head.
- You cannot walk backward (singly linked).

Delete the node such that the list's VALUE SEQUENCE behaves as if that node is gone.

**Example:**

```
List:  4 → 5 → 1 → 9 → null
              ^ given (value 5)

After deletion, the list should be:
       4 → 1 → 9 → null
```

The values `4, 5, 1, 9` become `4, 1, 9`.

---

## 2. Why the standard approach can't work

The usual "delete node X" algorithm:

```
walk from head until cur.next == X
prev = cur
prev.next = X.next      # splice X out
free X
```

This needs `prev` — the node BEFORE X. To find it, you walk FROM THE HEAD.

But the problem says **you don't have the head**. Without the head, you can't walk. Without a `prev` pointer (singly linked), you can't find prev.

From X itself, you can only walk FORWARD. You cannot reach the node before X.

So the standard approach is impossible.

---

## 3. The pivot — change the VALUE, not the structure

> **Mini-refresher: a list is its sequence of VALUES.**
>
> From the OUTSIDE, you observe a linked list by printing or iterating its values. The PHYSICAL NODES are an implementation detail — what matters is `[4, 5, 1, 9]` printing as `[4, 1, 9]` after the operation.
>
> So "delete node X" doesn't HAVE to mean "remove the memory holding X." It can mean "make the value sequence behave as if X is gone."

If you can't remove X PHYSICALLY (no access to the predecessor), can you make X HOLD A DIFFERENT VALUE — specifically, the value of the node AFTER X? Then physically remove the node AFTER X (which you CAN reach, via X.next).

Sequence of changes:
- **Before:** `... → X(val=5) → M(val=1) → 9`
- **Step 1:** copy M's value into X. Now X holds value 1: `... → X(val=1) → M(val=1) → 9`
- **Step 2:** make X skip M: `... → X(val=1) → 9`

After: `... → 1 → 9`. The value sequence has been reduced by one element, and the "5" is logically gone. The physical node X is still there, but it now represents what was M.

---

## 4. The trick

The two-step solution:

```
node.val = node.next.val      # alias: X now holds the value of the next node
node.next = node.next.next    # unlink the next node, since its role has been absorbed
```

That's it. **Two lines.**

The physical node passed in (X) survives but takes on the identity of its successor. The successor's physical node is now unreachable (orphaned).

---

## 5. Code

**C++:**

```cpp
void deleteNode(ListNode* node) {
    node->val = node->next->val;
    node->next = node->next->next;
}
```

**Python:**

```python
def deleteNode(node):
    node.val = node.next.val
    node.next = node.next.next
```

**JavaScript:**

```javascript
function deleteNode(node) {
    node.val = node.next.val;
    node.next = node.next.next;
}
```

Complexity: **O(1) time, O(1) space.**

> **Mini-refresher: in C++, the unlinked next node leaks.**
>
> After `node.next = node.next.next`, the original `node.next` is orphaned. In a GC language (Java, Python, JS), garbage collection reclaims it. In C++, technically you should `delete` it:
>
> ```cpp
> void deleteNode(ListNode* node) {
>     ListNode* toDelete = node->next;
>     node->val = toDelete->val;
>     node->next = toDelete->next;
>     delete toDelete;
> }
> ```
>
> LeetCode usually doesn't test for this (test harness owns memory), so the 2-liner is accepted.

---

## 6. Trace it

`4 → 5 → 1 → 9 → null`. Given pointer N to the node with value 5. Call the next node M (value 1).

```
Before:
   4 → 5 → 1 → 9 → null
       N   M

Step 1: N.val = N.next.val = M.val = 1.
Now the physical node N holds value 1:
   4 → 1 → 1 → 9 → null
       N   M

Step 2: N.next = N.next.next = M.next = (node with 9).
   4 → 1 → 9 → null
       N

Node M is now orphaned (no pointers to it from the list).
```

External view: the list values are now `4, 1, 9`. The "5" is gone. ✓

---

## 7. The "not the tail" caveat

If `node` were the tail, `node.next` would be null. Step 1 would crash on null dereference.

The problem GUARANTEES the given node isn't the tail — so we don't need to handle that case. But it's worth understanding WHY:

- We're "stealing" the next node's value to absorb. If there's no next, nothing to steal.
- For a true tail deletion, we'd need to update the previous node's `next` to null — but we don't have access to the previous node.

In a real-world API that might delete the tail, you'd need a doubly-linked list (so `prev` is accessible), or pass in the head as well, or use some other workaround.

---

## 8. Common pitfalls + transfer

**Pitfalls:**

1. **Trying to walk from the given node to find a "previous."** Impossible in a singly-linked list. The given node IS the trick — accept the constraint.

2. **Confusing "delete" with "modify in place."** The physical node passed in DOES survive — it just changes identity. If your test compared "is the original pointer still valid?", you'd say yes. If it compared "is the original VALUE still in the list?", you'd say no.

3. **Forgetting the two-line sequence.** Both lines are needed:
   - Just `node.val = node.next.val` produces a DUPLICATED value: `4 → 1 → 1 → 9`.
   - Just `node.next = node.next.next` keeps the OLD value (5) intact: `4 → 5 → 9` — wrong.

4. **Reversing the order:**
   ```
   node.next = node.next.next   # FIRST update next pointer
   node.val = node.next.val      # then copy value
   ```
   This actually still works (since we read `node.next.val` AFTER the update, but now `node.next` is the "1+1 next" — wait, that's the 9, so `node.val` would become 9). Buggy. Stick to the canonical order.

5. **Trying to use a stack or vector to "reconstruct."** Overkill — the trick is O(1).

**Transfer to other problems:**

| Problem | The "alias and shift" idea |
|---|---|
| **This problem** | overwrite node with next, drop next |
| Move Zeroes (in-place) | overwrite with non-zero, then zero-out tails |
| Remove Element (LC #27) | overwrite target with later non-target |
| Apply Operations to an Array | overwrite via two-pointer trick |
| Concurrent linked-list deletion (lock-free) | similar alias trick used in real systems |

**Pattern to internalize:**

> "When you can't restructure (no predecessor pointer, no head access), see if you can REWRITE THE CURRENT POSITION'S CONTENT instead. The list's externally observable SEQUENCE OF VALUES is what matters, not the identity of the underlying nodes."

---

> **Self-check — the question to ask next time.**
>
> When a constraint blocks you from doing the "obvious" pointer manipulation, ask:
>
> > **"Is the externally-observable sequence of VALUES what really matters? Can I rewrite values to simulate the desired structural change?"**
>
> If yes, the constraint melts.

---

## Cross-references

- **Reference card (post-mastery):** [`../Delete_Node_in_a_Linked_List.md`](../Delete_Node_in_a_Linked_List.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Design_Linked_List.md`](./Design_Linked_List.md) — node mechanics.
  - Coming next: [`Remove_Linked_List_Elements.md`](./Remove_Linked_List_Elements.md) — standard deletion with dummy head.
