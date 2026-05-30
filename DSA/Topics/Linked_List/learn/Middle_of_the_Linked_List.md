# Middle of the Linked List — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Middle_of_the_Linked_List.md`](../Middle_of_the_Linked_List.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/middle-of-the-linked-list/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/middle-of-the-linked-list/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **This is the introduction to the slow/fast pointer pattern (also called "tortoise and hare").** Two pointers walking at different speeds — when the fast one hits the end, the slow one is exactly halfway. The lesson: **speed ratios let you compute relative positions in one pass.** Same idea will catch cycles, find n-th-from-end, and split lists. **Read [`Reverse_Linked_List.md`](./Reverse_Linked_List.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. The two-pass solution
3. The thought experiment — two walkers at different speeds
4. The exact loop condition
5. Code
6. Trace odd-length and even-length
7. The "first middle" variant
8. Common pitfalls
9. The shape — slow/fast everywhere

---

## 1. Read the problem

Given the head of a singly-linked list, return the **middle node**. If the list has an even number of nodes, return the **SECOND of the two middles**.

**Examples:**

- `1 → 2 → 3 → 4 → 5` (5 nodes, odd): middle is `3`. Return the node containing 3 (and the rest of the list from there: `3 → 4 → 5`).
- `1 → 2 → 3 → 4 → 5 → 6` (6 nodes, even): two middles, 3 and 4. Return `4`.
- `1` (1 node): middle is `1`.
- `1 → 2`: two nodes, return the second (`2`).

You can't index a linked list — there's no `list[n/2]`. You'd have to walk.

---

## 2. The two-pass solution

Easiest: COUNT first, then walk.

```
n = 0
for p = head; p != null; p = p.next: n += 1

# walk floor(n/2) steps from head
p = head
for i in 0..floor(n/2)-1:
    p = p.next

return p
```

For `1 → 2 → 3 → 4 → 5` (n = 5), we walk 2 steps from head → node 3. ✓
For `1 → 2 → 3 → 4 → 5 → 6` (n = 6), we walk 3 steps → node 4. ✓

Two passes, O(n) time, O(1) space. Totally acceptable.

But interviewers often ask: **can you do it in ONE pass?**

---

## 3. The thought experiment — two walkers at different speeds

Imagine two walkers starting at the head:
- **Slow** walks 1 step per turn.
- **Fast** walks 2 steps per turn.

When Fast has walked `2k` nodes, Slow has walked `k` nodes — exactly half as far.

So when Fast reaches the END of the list (or one step before), Slow is at the MIDDLE of the list.

That's the entire idea. As they walk in lock-step (with different speeds), Slow always lags at the half-distance position.

> **Mini-refresher: relative position via speed ratio.**
>
> If `slow` advances at rate 1 and `fast` at rate 2:
> - When fast is at position `2k`, slow is at position `k`.
> - When fast hits the boundary (position ~n), slow is at position ~n/2.
>
> The speed ratio is what pins down the relative position. Other ratios work for other goals:
> - 1:3 (slow walks 1, fast walks 3) → slow at n/3 when fast hits end.
> - 1:n/k → slow at (k-1)/n position when fast hits end.

---

## 4. The exact loop condition

Subtle bit: fast advances 2 steps per turn. Before advancing, we must check that `fast.next` (the step we'd take next) AND `fast.next.next` (the step after) are valid — wait, actually we just need `fast.next.next` to be safe. Let's nail it.

Each iteration, we want to do:
- `slow = slow.next`
- `fast = fast.next.next`

For `fast.next.next` not to crash, both `fast` and `fast.next` must be non-null.

So the loop condition is:

```
while fast != null and fast.next != null:
    slow = slow.next
    fast = fast.next.next
```

After the loop, `slow` is the middle. Let's check both parities:

**Odd length (`n = 5`):** Fast walks 2, 4 — after the second iteration, `fast = 5` (last node). Now `fast.next = null` → loop exits. Slow walked 1, 2, 3 — wait, that's three iterations? Let me recount.

Actually let me start the trace from scratch with `slow = head, fast = head` (both at index 0):

```
n=5 list: 1(0) → 2(1) → 3(2) → 4(3) → 5(4) → null.

Initial: slow=1, fast=1.

Check: fast=1 (non-null), fast.next=2 (non-null) → enter.
  slow = 2, fast = 3.

Check: fast=3, fast.next=4 → enter.
  slow = 3, fast = 5.

Check: fast=5, fast.next=null → EXIT.

Return slow = 3. ✓ middle of odd-length 5-node list.
```

**Even length (`n = 6`):**

```
n=6 list: 1 → 2 → 3 → 4 → 5 → 6 → null.

Initial: slow=1, fast=1.

Check: fast=1, fast.next=2 → enter. slow=2, fast=3.
Check: fast=3, fast.next=4 → enter. slow=3, fast=5.
Check: fast=5, fast.next=6 → enter. slow=4, fast=null (5 → 6 → null → null).
Check: fast=null → EXIT.

Return slow = 4. ✓ the SECOND middle of even-length 6-node list.
```

Both cases return the right node with the SAME loop condition. ✓

---

## 5. Code

**C++:**

```cpp
ListNode* middleNode(ListNode* head) {
    ListNode* slow = head;
    ListNode* fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow;
}
```

**Python:**

```python
def middleNode(head):
    slow = head
    fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow
```

**JavaScript:**

```javascript
function middleNode(head) {
    let slow = head;
    let fast = head;
    while (fast && fast.next) {
        slow = slow.next;
        fast = fast.next.next;
    }
    return slow;
}
```

Complexity: **O(n) time, O(1) space.**

Same asymptotic complexity as two-pass, but in practice does half the work for long lists (one walk instead of two).

---

## 6. Trace odd-length and even-length

Already traced above (section 4). Let me verify a few more.

**`n = 1` (`head = 1`):**

```
slow=1, fast=1.
Check: fast.next=null → EXIT immediately.
Return slow = 1. ✓
```

**`n = 2` (`head = 1 → 2`):**

```
slow=1, fast=1.
Check: fast=1, fast.next=2 → enter. slow=2, fast=null (1→2→null).
Check: fast=null → EXIT.
Return slow = 2. ✓ (problem wants the second middle on even)
```

**`n = 3` (`head = 1 → 2 → 3`):**

```
slow=1, fast=1.
Check: fast=1, fast.next=2 → enter. slow=2, fast=3.
Check: fast=3, fast.next=null → EXIT.
Return slow = 2. ✓
```

All consistent.

---

## 7. The "first middle" variant

What if the problem wanted the FIRST of the two middles on even (i.e., for `[1, 2, 3, 4]` return `2`, not `3`)?

Small tweak in the loop condition. Make fast check one step further before advancing:

```
while fast.next != null and fast.next.next != null:
    slow = slow.next
    fast = fast.next.next
```

Now fast stops EARLIER on even-length lists. Trace `n = 4`:

```
slow=1, fast=1.
Check: fast.next=2, fast.next.next=3 → enter. slow=2, fast=3.
Check: fast.next=4, fast.next.next=null → EXIT.
Return slow = 2.   ← FIRST middle of 4-node list.
```

For `n = 5`, both variants return 3 (only one middle). For `n = 6`, the original returns 4, the variant returns 3.

The two variants differ ONLY on even-length lists. Pick the one that matches your spec.

> **Mini-refresher: loop conditions shape what "middle" means.**
>
> Tiny condition changes shift the answer by one position. Always test BOTH odd and even lengths to verify. Don't memorize "use this condition" — derive it from the parity behavior you want.

---

## 8. Common pitfalls

1. **Wrong loop condition.** `while fast != null` alone would crash on `fast.next.next` (when fast.next is null). Use `while fast && fast.next`.

2. **Initializing `slow` and `fast` differently.** Both should start at `head`. If `fast = head.next` (off by one), you change the parity behavior of which "middle" you get.

3. **Advancing fast by 2 but slow by 1 in different conditions.** Always advance BOTH inside the same loop body, with both inside the same iteration.

4. **Returning `slow.next` instead of `slow`.** Off-by-one error. Test on small cases.

5. **Trying to handle even/odd separately.** Unnecessary. The standard slow/fast loop handles both correctly — the "second middle" comes out naturally.

6. **Using a list to collect all nodes first, then indexing.** O(n) space, defeats the point. The slow/fast trick gives O(1) space.

7. **Running on a list with a cycle.** Slow/fast for "middle" doesn't terminate if there's a cycle — fast never reaches null. The cycle would have to be checked separately (see Linked List Cycle). For "middle" problems, the input is typically guaranteed acyclic.

---

## 9. The shape — slow/fast everywhere

Slow/fast (tortoise and hare) is one of the most reusable patterns in linked-list problems. Each instance just changes the SPEED RATIO or the STOPPING CONDITION.

| Problem | Slow speed | Fast speed | What we extract |
|---|---|---|---|
| **This problem** | 1 | 2 | slow at middle when fast hits end |
| Linked List Cycle (LC #141) | 1 | 2 | slow == fast → cycle exists |
| Linked List Cycle II (LC #142) | 1 | 2 | after meeting, reset and walk; meet at cycle start |
| Remove Nth From End (one-pass) | 1 | 1 (offset n) | slow at n-th-from-end when fast hits end |
| Palindrome Linked List | 1 | 2 | reach middle; reverse half; compare |
| Reorder List (LC #143) | 1 | 2 | split at middle |
| Happy Number (LC #202) | apply f once | apply f twice | detect cycle in sequence |

**Pattern to internalize:**

> "Two pointers walking at different speeds along the same linked structure can extract relative positions or detect cycles in ONE PASS with O(1) space."

The recognition cue: "find the middle / find the n-th from end / detect a cycle / split in half" — slow/fast.

---

> **Self-check — the question to ask next time.**
>
> When you face a linked-list problem about positions or cycles, ask:
>
> > **"Can two pointers walking at different speeds (or with a fixed gap) give me the answer in one pass?"**
>
> If yes, you've found the slow/fast template.

---

## Cross-references

- **Reference card (post-mastery):** [`../Middle_of_the_Linked_List.md`](../Middle_of_the_Linked_List.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Design_Linked_List.md`](./Design_Linked_List.md), [`Reverse_Linked_List.md`](./Reverse_Linked_List.md) — foundations.
  - Coming next: [`Remove_Nth_Node_From_End_of_List.md`](./Remove_Nth_Node_From_End_of_List.md) — fixed-gap variant of slow/fast.
  - Coming after: Linked_List_Cycle (Floyd's algorithm).
