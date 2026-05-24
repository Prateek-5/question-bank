# Remove Nth Node From End of List — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Remove_Nth_Node_From_End_of_List.md`](../Remove_Nth_Node_From_End_of_List.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/remove-nth-node-from-end-of-list/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. The lesson: **a FIXED GAP between two pointers turns "n-th from end" into "where pointer A is when pointer B hits the end" — solvable in one pass.** Combines slow/fast pointers with the dummy-head idiom. **Read [`Middle_of_the_Linked_List.md`](./Middle_of_the_Linked_List.md) (slow/fast) and [`Remove_Linked_List_Elements.md`](./Remove_Linked_List_Elements.md) (dummy head) first.**

**Map of this file (10 short sections):**

1. Read the problem
2. The two-pass solution
3. The gap trick — convert backward to forward
4. Computing the exact gap
5. Why we need the dummy head
6. The algorithm
7. Code
8. Trace it
9. Common pitfalls
10. The shape — fixed-gap pointers

---

## 1. Read the problem

Given the head of a linked list and an integer `n`, remove the **n-th node from the END** and return the head.

**Counting from the end:**
- 1st from end = tail.
- 2nd from end = node before tail.
- n-th from end = `length - n` from start (0-indexed).

**Example 1:** `head = [1, 2, 3, 4, 5]`, `n = 2`. The 2nd-from-end is `4`. Remove it. → `[1, 2, 3, 5]`.

**Example 2:** `head = [1]`, `n = 1`. The 1st-from-end is `1` (the only node). Remove it. → `[]`.

**Example 3:** `head = [1, 2]`, `n = 1`. Remove tail. → `[1]`.

**Example 4:** `head = [1, 2]`, `n = 2`. Remove HEAD (the 2nd from end). → `[2]`.

The trickiest case is `n == length` — we'd remove the head, and need to update the external pointer.

---

## 2. The two-pass solution

Easy: count first, then walk.

```
L = length of list
walk to position (L - n - 1) from start    # the node BEFORE the target
splice out the next node
```

Two passes, O(L). Works. But the interviewer asks: **one pass?**

Why is one pass even possible? Walking forward gives forward distances. The target is at distance `n` FROM THE END — we don't know where "the end" is until we get there. Can we somehow START maintaining a relationship that will be ABOUT-TO-FIND `n-th from end` once we reach the end?

---

## 3. The gap trick — convert backward to forward

> **Mini-refresher: the "fixed gap" idea.**
>
> Maintain two pointers `A` and `B` such that `B` is always exactly some FIXED NUMBER of nodes ahead of `A`. Advance them in lockstep.
>
> When `B` hits the end of the list (becomes null), `A` is exactly that fixed number of nodes BEFORE the end.
>
> Adjust the gap to land `A` exactly where you need it.

For our problem: when `B` reaches the position JUST PAST the tail (`null`), `A` should be at the node JUST BEFORE the n-th-from-end (i.e., the predecessor of the node to delete).

To delete in a singly-linked list, you need access to the PREDECESSOR. So `A` should land at the predecessor, not at the target itself.

---

## 4. Computing the exact gap

Let `L` be the list length. Indexes from 0 (head) to `L - 1` (tail).

- The **target** to delete: position `L - n`.
- The **predecessor** of the target: position `L - n - 1`.

We want `A` to end up at the predecessor.

If `B` ends at position `L` (just past the tail, which is `null`), the gap between `A` and `B` is `L - (L - n - 1) = n + 1`.

**So: `B` is `n + 1` steps ahead of `A`.**

Setup: start both at the same node, then advance `B` by `n + 1` steps. Then walk both in lockstep until `B == null`.

---

## 5. Why we need the dummy head

Consider `n == L` — we're removing the head itself.

- Target position: `L - L = 0` (the head).
- Predecessor position: `-1` (doesn't exist!).

There's no predecessor for the head in the raw list. We can't land `A` at position -1.

**Dummy head fix:** prepend a dummy. Now the head's predecessor IS the dummy. With the dummy:

- The list becomes `dummy → 1 → 2 → 3 → 4 → 5 → null`. Total nodes including dummy: `L + 1`.
- Start `A = dummy` and `B = dummy`. Advance `B` by `n + 1` steps. Walk both in sync until `B = null`. `A` ends at the predecessor (which could be the dummy itself if `n == L`).

After splicing, return `dummy.next` (which may be the original head or a later node if the head was removed).

> **Mini-refresher: dummy head + two pointers.**
>
> Combining the dummy head with the gap trick is a powerful idiom. The dummy provides a "position -1" so removing the head is just removing-after-dummy. The gap trick handles ANY n from 1 to length uniformly.

---

## 6. The algorithm

```
dummy = new Node(0)
dummy.next = head
A = dummy
B = dummy

# Advance B by n + 1 steps
for i in 0..n:
    B = B.next

# Walk both in sync until B hits null
while B != null:
    A = A.next
    B = B.next

# A is at the predecessor of the target. Splice.
A.next = A.next.next

return dummy.next
```

Two phases:
1. **Gap phase:** advance B alone to create the gap of n+1.
2. **Sync phase:** advance both together until B falls off the end.

---

## 7. Code

**C++:**

```cpp
ListNode* removeNthFromEnd(ListNode* head, int n) {
    ListNode dummy(0);
    dummy.next = head;
    ListNode* A = &dummy;
    ListNode* B = &dummy;

    // Phase 1: advance B by n + 1 steps
    for (int i = 0; i <= n; ++i) B = B->next;

    // Phase 2: walk both in sync until B is null
    while (B) {
        A = A->next;
        B = B->next;
    }

    // A is at the predecessor of the target
    ListNode* target = A->next;
    A->next = target->next;
    delete target;     // C++: free memory (skip in GC languages)

    return dummy.next;
}
```

**Python:**

```python
def removeNthFromEnd(head, n):
    dummy = ListNode(0)
    dummy.next = head
    A = dummy
    B = dummy

    for _ in range(n + 1):
        B = B.next

    while B:
        A = A.next
        B = B.next

    A.next = A.next.next
    return dummy.next
```

**JavaScript:**

```javascript
function removeNthFromEnd(head, n) {
    const dummy = new ListNode(0);
    dummy.next = head;
    let A = dummy;
    let B = dummy;

    for (let i = 0; i <= n; i++) B = B.next;

    while (B) {
        A = A.next;
        B = B.next;
    }

    A.next = A.next.next;
    return dummy.next;
}
```

Complexity: **O(L) time, O(1) space.**

---

## 8. Trace it

**Example 1:** `[1, 2, 3, 4, 5]`, `n = 2`.

```
dummy → 1 → 2 → 3 → 4 → 5 → null. (L = 5)

A = dummy, B = dummy.

Phase 1: advance B by 3 (= n + 1) steps:
  step 1: B = 1.
  step 2: B = 2.
  step 3: B = 3.
A=dummy, B=3.

Phase 2: walk in sync until B is null:
  iter 1: A=1, B=4.
  iter 2: A=2, B=5.
  iter 3: A=3, B=null.

A = 3 (the predecessor of target 4).

A.next = A.next.next → node 3.next = node 5. Node 4 is unlinked.

Result: dummy → 1 → 2 → 3 → 5 → null.
Return dummy.next = node 1.

List: [1, 2, 3, 5]. ✓
```

**Example 2:** `[1]`, `n = 1`.

```
dummy → 1 → null.

A = dummy, B = dummy.

Phase 1: advance B by 2 steps:
  step 1: B = 1.
  step 2: B = null.

Phase 2: B is already null → loop doesn't execute.

A = dummy. A.next = node 1. A.next.next = null.
A.next = null.

Result: dummy → null.
Return dummy.next = null.

List: []. ✓
```

**Example 4:** `[1, 2]`, `n = 2` (remove the HEAD).

```
dummy → 1 → 2 → null. (L = 2)

A = dummy, B = dummy.

Phase 1: advance B by 3 steps:
  step 1: B = 1.
  step 2: B = 2.
  step 3: B = null.

Phase 2: B is null → loop doesn't execute.

A = dummy. A.next = node 1. A.next.next = node 2.
A.next = node 2.

Result: dummy → 2 → null.
Return dummy.next = node 2.

List: [2]. ✓
```

The dummy head correctly handled removing the original head — same code, no special case.

---

## 9. Common pitfalls

1. **Wrong gap size.** Common mistake: advance B by `n` instead of `n + 1`. Then A lands at the target itself, not the predecessor, and you can't splice. Use `n + 1`.

2. **Forgetting the dummy head.** Then removing the original head requires a special case. With dummy, it just works.

3. **Off-by-one in the phase 1 loop.** `for i in range(n + 1)` runs n+1 times. `for i in 1..=n+1` also runs n+1 times. `for i in 0..n` runs only n times — wrong. Sanity-check the iteration count.

4. **Crashing if `n > L`.** The problem usually guarantees `n ≤ L`, but if not, `B` walks off the end during phase 1. Add a null check if necessary.

5. **Walking with `while B != null` when B starts already null.** Make sure phase 2 correctly handles the case where B becomes null DURING phase 1 (happens when removing the head). The loop should be a no-op then. Test edge cases.

6. **Returning `head` instead of `dummy.next`.** If we removed the original head, `head` is now stale (or a freed pointer). Always return `dummy.next`.

7. **Reusing `A` or `B` after splicing.** After `A.next = A.next.next`, the old `A.next` (target) may be freed in C++. Don't access it afterwards.

8. **Off-by-one between "predecessor of n-th-from-end" and "n-th-from-end itself."** Always be clear on what your pointer points TO. The pattern: predecessor for splicing, target for inspection.

---

## 10. The shape — fixed-gap pointers

The fixed-gap variant of two-pointer walking generalizes:

| Problem | Gap |
|---|---|
| **This problem** | `n + 1` (so A lands at predecessor of n-th-from-end) |
| Find k-th from end | `k` (so A lands at the target itself) |
| Pair-wise distance check in a sliding window | `k` (window size) |
| Sliding-window min/max | `k` (window size) — with deque |
| Reordering / partitioning where bound is by distance | varies |

Compare to the SAME-SPEED variant (this problem) and DIFFERENT-SPEED variant (Middle of Linked List, Cycle Detection). All three are "two pointers" but use different mechanics:

| Variant | Speed of A | Speed of B | What you get |
|---|---|---|---|
| Same speed, fixed gap | 1 | 1 (after gap setup) | A at fixed distance from B |
| Different speed | 1 | 2 | A at half-distance when B hits end (middle, cycle) |

**Pattern to internalize:**

> "Two pointers at SAME SPEED with a FIXED GAP let you compute distance-from-end in one pass. Two pointers at DIFFERENT SPEEDS let you compute fractional position or detect cycles."

When the problem mentions "from the end" or "k apart," reach for the fixed-gap variant.

---

> **Self-check — the question to ask next time.**
>
> When a problem says "the k-th from the end" or "remove the k-th from the end," ask:
>
> > **"Can I use two pointers with a fixed gap of k (or k+1 for splicing), so when one hits the end, the other is exactly at the target?"**
>
> If yes, one-pass with O(1) space.

---

## Cross-references

- **Reference card (post-mastery):** [`../Remove_Nth_Node_From_End_of_List.md`](../Remove_Nth_Node_From_End_of_List.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Middle_of_the_Linked_List.md`](./Middle_of_the_Linked_List.md) — different-speed variant.
  - [`Remove_Linked_List_Elements.md`](./Remove_Linked_List_Elements.md) — dummy head idiom.
  - Coming next: Linked_List_Cycle, Linked_List_Cycle_II — different-speed for cycle detection.
