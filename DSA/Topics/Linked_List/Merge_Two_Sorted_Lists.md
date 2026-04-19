# Merge Two Sorted Lists

**Problem Link:**
https://leetcode.com/problems/merge-two-sorted-lists/

**Topic:**
Linked List

----------------------------------------

## Step 1: Understand the Goal

You get two linked lists, each already sorted in non-decreasing order. Combine them into one sorted linked list. You should splice the existing nodes together rather than creating copies — which affects memory usage, not correctness.

Example:
- List A: `1 → 2 → 4`
- List B: `1 → 3 → 4`
- Merged: `1 → 1 → 2 → 3 → 4 → 4`

Both inputs can be empty; handle that gracefully.

----------------------------------------

## Step 2: Think About How You'd Merge on Paper

Suppose you had two stacks of sorted cards face-up, and you wanted one merged sorted stack. The strategy is obvious: look at the top card of each stack, pick the smaller one, put it in the merged stack, reveal the next card underneath. Repeat. When one stack runs out, just append the rest of the other.

That's the whole algorithm. Now we just need to translate "look at the top" and "reveal the next" into linked-list operations.

In a linked list, "the top card" is the head. "Reveal the next" means `head = head.next`.

----------------------------------------

## Step 3: Making It Concrete in Pseudocode

```
tail = dummy node (we'll return dummy.next at the end)
while both a and b are non-null:
    if a.val <= b.val:
        tail.next = a
        a = a.next
    else:
        tail.next = b
        b = b.next
    tail = tail.next
# at most one of a, b is still non-null
tail.next = a if a else b
return dummy.next
```

The use of a **dummy head** deserves a moment. Without it, we'd need special logic for "the very first node" — is it from A or B? A dummy sidesteps that entirely: we always have a `tail` to append to. At the end, `dummy.next` points to the real merged head.

----------------------------------------

## Step 4: Why It's Safe to Just Re-link Existing Nodes

We're not copying values; we're reusing the original nodes and changing their `next` pointers. This works because:

1. Each node is only "consumed" from one input list, never from both.
2. Once we re-link a node's `next` via `tail.next = ...`, we never revisit the old pointer.
3. The tail of the merged list gets whatever remains when one input finishes — by setting `tail.next = (whichever list is still non-null)`.

No memory is leaked, nothing is copied. Just pointer reassignment.

----------------------------------------

## Step 5: Trace on the Example

Let me use `A: 1 → 2 → 4` and `B: 1 → 3 → 4`. Dummy's `next` will eventually point to the merged head.

```
dummy, tail=dummy, a=1A, b=1B

Iter 1: 1A <= 1B, tail.next = 1A, advance a to 2A. tail = 1A.
        Merged so far: dummy → 1A. A: 2A → 4A. B: 1B → 3B → 4B.

Iter 2: 2A > 1B, tail.next = 1B, advance b to 3B. tail = 1B.
        Merged: dummy → 1A → 1B. A: 2A → 4A. B: 3B → 4B.

Iter 3: 2A <= 3B, tail.next = 2A, advance a to 4A. tail = 2A.
        Merged: dummy → 1A → 1B → 2A. A: 4A. B: 3B → 4B.

Iter 4: 4A > 3B, tail.next = 3B, advance b to 4B. tail = 3B.
        Merged: ... → 3B. A: 4A. B: 4B.

Iter 5: 4A <= 4B, tail.next = 4A, advance a to null. tail = 4A.
        Merged: ... → 4A. A: null. B: 4B.

Loop exit (a is null).
tail.next = b = 4B.
Merged: 1A → 1B → 2A → 3B → 4A → 4B.
```

Values: `1, 1, 2, 3, 4, 4`. ✓

Notice that when `a.val == b.val` (iter 1), we picked from A. The `<=` is a tie-breaker — you could pick from B on ties with `<` and still get a sorted result. Choosing one direction consistently keeps the merge stable (A's nodes stay before equivalent B nodes).

----------------------------------------

## Step 6: Comparing to Array Merge

If you've written merge-sort's merge step, this feels identical — and it is. Merging two sorted arrays is an O(n + m) linear scan with two pointers. The linked list version is the same algorithm with pointer reassignments replacing array index increments. The algorithmic skeleton is universal: two sorted sequences plus monotonic pointers equals O(n + m) merge.

----------------------------------------

## Step 7: Complexity

Time: we touch each node exactly once. **O(n + m)**.
Space: no extra data structures, just a dummy and a tail pointer. **O(1)**.

If you wrote a recursive version (also elegant), you'd use O(n + m) stack space. The iterative version is the safer default.

----------------------------------------

## Step 8: C++ Implementation

```cpp
ListNode* mergeTwoLists(ListNode* a, ListNode* b) {
    ListNode dummy(0);
    ListNode* tail = &dummy;
    while (a && b) {
        if (a->val <= b->val) {
            tail->next = a;
            a = a->next;
        } else {
            tail->next = b;
            b = b->next;
        }
        tail = tail->next;
    }
    tail->next = a ? a : b;
    return dummy.next;
}
```

The dummy lives on the stack — local to the function. We return `dummy.next`, which points to a node that survives after the function ends (because heap-allocated input nodes persist).

Recursive version (for reference, not the recommended one in practice):

```cpp
ListNode* mergeTwoLists(ListNode* a, ListNode* b) {
    if (!a) return b;
    if (!b) return a;
    if (a->val <= b->val) { a->next = mergeTwoLists(a->next, b); return a; }
    else { b->next = mergeTwoLists(a, b->next); return b; }
}
```

Short and pretty, but O(n + m) stack depth.

----------------------------------------

## Step 9: Follow-up Questions

- **Merge k sorted lists.** Generalize with a min-heap of all the heads. Pop the smallest, push its `next`. O(N log k).
- **Merge without modifying the original lists (make copies).** Allocate new nodes as you go.
- **Merge in descending order.** Flip the comparison.
- **Merge where ties should interleave (stability-sensitive).** Be explicit about the tie-break direction; test with repeated values.
- **In-place merge of a linked list and an array.** Build a third list from the array first, then use the standard merge.
