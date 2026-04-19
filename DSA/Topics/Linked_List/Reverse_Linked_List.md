# Reverse Linked List

**Problem Link:**
https://leetcode.com/problems/reverse-linked-list/

**Topic:**
Linked List

----------------------------------------

## Step 1: Picture the Problem Before Any Code

You're given the head of a singly linked list: something like `1 → 2 → 3 → 4 → null`. You need to return the head of the reversed list: `4 → 3 → 2 → 1 → null`.

Sounds simple. And conceptually it is. The catch is that in a singly linked list, a node only knows *who comes after it*, not who came before. So to truly reverse, we'd need every node's `next` pointer to flip direction. That's a lot of surgery on the pointers.

----------------------------------------

## Step 2: Tiny Cases First

**Empty list (`head == null`):** nothing to reverse. Return `null`.

**One node (`1 → null`):** already its own reverse. Return it.

**Two nodes (`1 → 2 → null`):** we want `2 → 1 → null`. So `2.next` should be `1`, and `1.next` should be `null`. We need to flip exactly one pointer (and the head moves from 1 to 2).

**Three nodes (`1 → 2 → 3 → null`):** target `3 → 2 → 1 → null`. We flip two pointers: `2→1` and `3→2`. Head moves to 3.

Pattern: for n nodes, we flip n-1 pointers. Each flip is a local operation on one node's `next`. The tricky part is that once we flip a node's `next`, we've "lost" the pointer to its original next node. We need to save it before we overwrite it.

----------------------------------------

## Step 3: Thinking Through a Single Flip

Let me focus on the moment I want to flip a single node's `next`. Say I'm at node `cur`, and I want to make `cur.next` point *backward* to whatever came before `cur` (call that `prev`).

If I just do `cur.next = prev`, I've overwritten `cur`'s original next pointer — meaning I can no longer reach the rest of the list!

So **before** I overwrite, I need to remember the original `cur.next`. Let me call it `nxt`.

```
nxt = cur.next        # save pointer to the rest of the list
cur.next = prev       # flip cur's pointer to backward
prev = cur            # now cur is the new "previous" for the next iteration
cur = nxt             # advance to the next node to process
```

Four lines. That's one iteration.

Now it all clicks. We walk the list once, keeping three pointers in motion: `prev`, `cur`, `nxt`. Each iteration flips one pointer and advances.

----------------------------------------

## Step 4: Initialization and Termination

- **Initially:** `prev = null` (the original head has nothing before it; after reversal, the original head's `next` should point to `null`).
- **Initially:** `cur = head`.
- **Loop while `cur != null`.**
- **At the end:** `prev` is the new head.

Why does `prev` become the new head? Because in the last iteration, we moved `cur` one past the final node, and set `prev` to that final node. The final node's `next` was already flipped to point to the previous one. So `prev` is the top of the reversed list.

----------------------------------------

## Step 5: Trace on `1 → 2 → 3 → null`

I'll denote the list state as we go. Initially:

```
prev = null, cur = 1
List still looks like: 1 → 2 → 3 → null
```

**Iter 1:**
```
nxt = cur.next = 2
cur.next = prev = null       →  node 1 now points to null
prev = cur = 1
cur = nxt = 2

State: null ← 1    2 → 3 → null
             (prev)  (cur)
```

**Iter 2:**
```
nxt = cur.next = 3
cur.next = prev = 1          →  node 2 now points to 1
prev = cur = 2
cur = nxt = 3

State: null ← 1 ← 2    3 → null
                 (prev)  (cur)
```

**Iter 3:**
```
nxt = cur.next = null
cur.next = prev = 2          →  node 3 now points to 2
prev = cur = 3
cur = nxt = null

State: null ← 1 ← 2 ← 3
                   (prev)
```

Loop exits because `cur == null`. Return `prev = 3`. New list: `3 → 2 → 1 → null`. ✓

----------------------------------------

## Step 6: A Recursive Alternative

There's a recursive way to solve this too, and it's worth knowing. It goes: reverse the sublist `head.next → ... → tail`, then attach `head` at the end.

```cpp
ListNode* reverseList(ListNode* head) {
    if (!head || !head->next) return head;
    ListNode* newHead = reverseList(head->next);
    head->next->next = head;   // the node after head now points back to head
    head->next = nullptr;       // head becomes the tail
    return newHead;
}
```

The recursion bottoms out when we reach the last node, and unwinds flipping pointers on the way up. Elegant, but it uses O(n) stack space — and for a million-node list, the recursion would blow the stack. The iterative version is safer for unbounded lists.

I like the iterative version for this reason, plus it's easier to reason about under pressure.

----------------------------------------

## Step 7: Complexity

Time: we visit each node exactly once, constant work per node. **O(n)**.
Space: three pointers regardless of list size. **O(1)** for iterative. **O(n)** stack for the recursive version.

----------------------------------------

## Step 8: C++ Implementation

```cpp
ListNode* reverseList(ListNode* head) {
    ListNode* prev = nullptr;
    ListNode* cur = head;
    while (cur) {
        ListNode* nxt = cur->next;  // save next before we overwrite
        cur->next = prev;            // flip
        prev = cur;                  // advance prev
        cur = nxt;                   // advance cur
    }
    return prev;
}
```

Five statements inside the loop. Notice the fixed ordering: save-next, flip, move-prev, move-cur. Mess up the order (especially forgetting to save `nxt` before overwriting `cur.next`) and the list becomes unreachable past the current node.

----------------------------------------

## Step 9: Follow-up Questions

- **Reverse only between positions `left` and `right` (Reverse Linked List II).** Same idea, but isolate the sub-range first and splice it back.
- **Reverse in groups of k (Reverse Nodes in k-Group).** Repeatedly reverse k-length chunks; handle a final partial group per the problem spec.
- **Reverse a doubly-linked list.** Swap `next` and `prev` at every node; head and tail swap roles.
- **Can we reverse in constant time by just relabeling head and tail?** Only if the list structure supports walking both directions (like a doubly-linked list with a "direction flag" — a clever hack).
- **How do you detect that the list you're reversing has a cycle?** Pre-check with Floyd's algorithm; reversing a cyclic list leads to infinite loops.
