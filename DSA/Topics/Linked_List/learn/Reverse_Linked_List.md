# Reverse Linked List — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Reverse_Linked_List.md`](../Reverse_Linked_List.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/reverse-linked-list/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/reverse-linked-list/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **This is THE foundational linked-list pattern.** Master the three-pointer iterative reverse and you've mastered the muscle memory for: Reverse Nodes in K-Group, Reorder List, Palindrome Linked List (half-list reverse), Reverse Linked List II (sublist reverse), Add Two Numbers II (reverse then add). **The lesson: visit each node, save its next, flip its pointer backward, advance.** Burn this into reflex. **Read [`Design_Linked_List.md`](./Design_Linked_List.md) first.**

**Map of this file (11 short sections):**

1. Read the problem
2. Tiny cases first
3. What does "reverse" mean in pointers?
4. The single-flip operation
5. The three-pointer dance
6. Initialization and termination
7. Code
8. Trace it
9. The recursive alternative (and why iterative wins)
10. Common pitfalls
11. The shape — three-pointer flip everywhere

---

## 1. Read the problem

Given the head of a singly-linked list `1 → 2 → 3 → 4 → null`, return the head of the reversed list `4 → 3 → 2 → 1 → null`.

In-place is expected — O(1) extra space.

Examples:
- `[1, 2, 3, 4, 5]` → `[5, 4, 3, 2, 1]`.
- `[1, 2]` → `[2, 1]`.
- `[]` → `[]`.
- `[1]` → `[1]`.

---

## 2. Tiny cases first

Always sanity-check on small inputs before designing a general algorithm.

- **Empty list (`head == null`):** nothing to reverse. Return null.
- **One node (`1 → null`):** already its own reverse. Return it unchanged.
- **Two nodes (`1 → 2 → null`):** want `2 → 1 → null`. We need to:
  - Flip node 1's pointer from `2` to `null` (since 1 is now the tail).
  - Flip node 2's pointer from `null` to `1`.
  - Return node 2 as the new head.
- **Three nodes (`1 → 2 → 3 → null`):** want `3 → 2 → 1 → null`. Three pointer flips.

**Pattern:** for `n` nodes, we flip `n` pointers (each node's `next` gets reassigned), and the head changes from the old head to the old tail.

---

## 3. What does "reverse" mean in pointers?

> **Mini-refresher: each node has ONE outgoing pointer.**
>
> In a singly-linked list, each node holds a value and a `next` pointer. To "reverse" the list, every node's `next` must point to the node that was BEFORE it (the one that PREVIOUSLY pointed to it).
>
> Before:  `1.next = 2`, `2.next = 3`, `3.next = null`.
> After:   `1.next = null`, `2.next = 1`, `3.next = 2`.

So reversing is just **redirecting every node's `next` pointer** to its PREDECESSOR in the original list. The challenge: as you walk forward, you have no built-in "previous" pointer to use.

You have to BRING the previous pointer with you as you walk.

---

## 4. The single-flip operation

Focus on the moment of flipping ONE node `cur`. We want `cur.next` to point to the previous node (`prev`).

```
cur.next = prev      # flip
```

Looks simple. But this OVERWRITES the original `cur.next`. After the flip, we've LOST the path to the rest of the list. The node we WERE going to visit next is no longer reachable.

**Solution: save the original `cur.next` BEFORE overwriting it.**

```
nxt = cur.next       # remember the path forward
cur.next = prev      # flip
```

Now `nxt` still holds the original successor, so we can advance to it after the flip.

> **Mini-refresher: the "save before overwriting" pattern.**
>
> Anytime you're about to overwrite a pointer/variable whose old value you'll still need, save it first. This applies to:
> - Linked-list reversal (this problem).
> - Swapping two variables (`tmp = a; a = b; b = tmp`).
> - Tree rotations.
> - Array shifts where you overwrite from one end.
>
> It's the most basic "be careful with shared state" discipline.

---

## 5. The three-pointer dance

Putting it together: at any moment during the walk we maintain THREE pointers:

- **`prev`**: the node JUST FLIPPED (or `null` at the very start). The "head of the reversed-so-far portion."
- **`cur`**: the node we're ABOUT TO FLIP.
- **`nxt`**: the node we'll advance to AFTER flipping `cur`. (Temporary, computed each iteration.)

One iteration:

```
nxt = cur.next         # save next BEFORE we overwrite cur.next
cur.next = prev         # flip cur's pointer to point backward
prev = cur              # cur is now the most recently flipped — becomes new prev
cur = nxt               # advance to the next node to process
```

Four lines. The order matters:

1. Save `nxt` first — if we don't, line 2 makes us lose the rest.
2. Flip `cur.next` — the actual work.
3. Advance `prev` to `cur` — the new "head of the flipped portion."
4. Advance `cur` to `nxt` — move on.

---

## 6. Initialization and termination

**Initial:**
- `prev = null` — the original head has nothing before it. After reversal, the original head's `next` should be `null`. So our initial "previous" is null.
- `cur = head` — start at the original head.
- `nxt` — not yet defined; computed inside the loop.

**Loop condition:** `while cur != null`. When `cur` is null, we've walked off the end — nothing more to flip.

**Return:** when the loop exits, `cur` is null, and `prev` is the LAST node we processed — the original tail, now the new head. **Return `prev`.**

---

## 7. Code

**C++:**

```cpp
ListNode* reverseList(ListNode* head) {
    ListNode* prev = nullptr;
    ListNode* cur = head;
    while (cur) {
        ListNode* nxt = cur->next;   // save next
        cur->next = prev;             // flip
        prev = cur;                   // advance prev
        cur = nxt;                    // advance cur
    }
    return prev;
}
```

**Python:**

```python
def reverseList(head):
    prev = None
    cur = head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev
```

**JavaScript:**

```javascript
function reverseList(head) {
    let prev = null;
    let cur = head;
    while (cur) {
        const nxt = cur.next;
        cur.next = prev;
        prev = cur;
        cur = nxt;
    }
    return prev;
}
```

Complexity: **O(n) time, O(1) space.**

---

## 8. Trace it

Input: `1 → 2 → 3 → null`. Initial state: `prev = null`, `cur = 1`.

**Iteration 1:** `cur = 1`.
```
nxt = cur.next = 2
cur.next = prev = null      → node 1's next now points to null
prev = cur = 1
cur = nxt = 2

Picture of pointers right now:
  null ← 1     2 → 3 → null
        (prev) (cur)
```

Node 1's `next` flipped to null. Node 2 and beyond still point forward.

**Iteration 2:** `cur = 2`.
```
nxt = cur.next = 3
cur.next = prev = 1          → node 2's next now points to node 1
prev = cur = 2
cur = nxt = 3

Picture:
  null ← 1 ← 2      3 → null
              (prev) (cur)
```

Node 2's `next` flipped to 1. The reversed portion now spans 2 nodes (2 → 1).

**Iteration 3:** `cur = 3`.
```
nxt = cur.next = null
cur.next = prev = 2          → node 3's next now points to node 2
prev = cur = 3
cur = nxt = null

Picture:
  null ← 1 ← 2 ← 3
                  (prev)  (cur = null)
```

Node 3's `next` flipped to 2. All three nodes' pointers now point backward.

**Loop exits** (`cur == null`). Return `prev = 3`. New head is 3, new list is `3 → 2 → 1 → null`. ✓

---

## 9. The recursive alternative (and why iterative wins)

The recursive form:

```
reverseList(head):
    if head is null or head.next is null:
        return head                          # base: 0 or 1 node — already reversed
    newHead = reverseList(head.next)         # reverse everything after head
    head.next.next = head                    # the node right after head now points back to head
    head.next = null                          # head becomes the new tail
    return newHead                           # the recursion returned the new head
```

> **Mini-refresher: the recursion's structure.**
>
> Imagine `1 → 2 → 3 → null`. We recurse on `2 → 3 → null`, getting `newHead = 3`. Now `head.next` is still node 2 (we haven't modified anything yet at this level). We set `head.next.next = head` → node 2's `next` becomes node 1. Then `head.next = null` → node 1 becomes the tail.
>
> Unwinding: each level flips ONE pointer, just like in the iterative version. The recursion supplies the "go forward to the end first" structure for free.

**Why iterative is preferred:**

- **Recursive uses O(n) stack space.** For a 100,000-node list, that's a deep stack. Some languages (Python) will hit a recursion limit. Some environments (C++ with default stack size) will stack-overflow.
- **Iterative is O(1) space.** Three pointers regardless of list size.
- **Iterative is easier to reason about under interview pressure.** No "what does the recursion return?" mental gymnastics.

Know both. Code the iterative.

---

## 10. Common pitfalls

1. **Forgetting to save `nxt` before overwriting `cur.next`.** Then the rest of the list becomes unreachable, and `cur = cur.next` (the original next) breaks. This is THE pitfall — the reason we need three pointers.

2. **Wrong initial value for `prev`.** It should be `null` (or `nullptr`). Setting `prev = head` causes a cycle: `head.next = head`, creating an infinite loop on the very first iteration.

3. **Returning `head` instead of `prev`.** `head` still points to the original first node, which is now the tail. Return `prev` (the new head).

4. **Wrong order of updates inside the loop.** The canonical order is:
   - `nxt = cur.next`
   - `cur.next = prev`
   - `prev = cur`
   - `cur = nxt`
   Mess up the order — especially flipping `cur.next` before saving `nxt`, or advancing `cur` before advancing `prev` — and you'll lose the list or create cycles.

5. **Off-by-one in the loop condition.** Use `while cur != null`, not `while cur.next != null`. The latter exits one node early and leaves the last node's pointer unflipped.

6. **Confusing reverse with sort.** "Reverse" preserves the ORDER, just walked back-to-front. Sort would arrange by value.

7. **Trying to reverse in place by swapping VALUES.** That works for THIS problem (and is O(n) extra space if you collect values first, O(1) if you swap from both ends). But it's not the canonical pattern — interviewers want pointer manipulation. Also doesn't generalize to "reverse a sublist between positions l and r."

8. **Stack overflow on the recursive version.** Use iterative for safety.

---

## 11. The shape — three-pointer flip everywhere

The three-pointer iterative reverse is the **fundamental linked-list operation**. It appears, often hidden inside larger algorithms, in:

| Problem | How three-pointer reverse appears |
|---|---|
| **This problem** | direct |
| Reverse Linked List II (LC #92) | reverse a SUBLIST between positions l and r |
| Reverse Nodes in K-Group (LC #25) | reverse each k-length chunk |
| Palindrome Linked List (LC #234) | reverse the second half, compare to first half |
| Reorder List (LC #143) | reverse second half, then interleave |
| Add Two Numbers II (LC #445) | reverse both lists, add as in I, reverse result |
| Swap Nodes in Pairs (LC #24) | reverse pairs (k=2 special case of K-Group) |

**Pattern to internalize:**

> "To reverse part of (or all of) a singly-linked list in O(1) space: walk forward with `prev`, `cur`, `nxt`. Save `nxt`, flip `cur.next` to `prev`, advance both. The new head is the last `prev`."

Burn it into reflex. Many interview problems are built on this primitive.

---

> **Self-check — the question to ask next time.**
>
> When you face any linked-list problem that involves "reverse," "k-group," "palindrome," or "reorder," ask:
>
> > **"Can I decompose this into one or more applications of the three-pointer reverse pattern (`prev / cur / nxt`)?"**
>
> If yes, you've found the core mechanic.

---

## Cross-references

- **Reference card (post-mastery):** [`../Reverse_Linked_List.md`](../Reverse_Linked_List.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Design_Linked_List.md`](./Design_Linked_List.md), [`Remove_Linked_List_Elements.md`](./Remove_Linked_List_Elements.md) — node mechanics.
  - Coming next: [`Middle_of_the_Linked_List.md`](./Middle_of_the_Linked_List.md), [`Remove_Nth_Node_From_End_of_List.md`](./Remove_Nth_Node_From_End_of_List.md) — slow/fast pointers.
  - Coming after: Palindrome Linked List — combines THIS reverse pattern with slow/fast.
