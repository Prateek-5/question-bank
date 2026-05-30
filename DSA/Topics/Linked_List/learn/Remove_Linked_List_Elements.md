# Remove Linked List Elements — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Remove_Linked_List_Elements.md`](../Remove_Linked_List_Elements.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/remove-linked-list-elements/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/remove-linked-list-elements/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~15 minutes. **This is the canonical use of the dummy-head idiom.** The lesson: **prepend a dummy node so head-modification becomes just another in-list modification.** Once you've internalized this, every linked-list problem where "the head might change" gets dramatically easier. **Read [`Design_Linked_List.md`](./Design_Linked_List.md) first** for the dummy-head concept.

**Map of this file (9 short sections):**

1. Read the problem
2. Two cases that need handling
3. The dummy head idiom — what it solves
4. The walk with "do NOT advance after a removal"
5. Code
6. Trace it
7. Why not advance after a delete?
8. Common pitfalls
9. The shape — dummy head everywhere

---

## 1. Read the problem

Given the head of a singly-linked list and an integer `val`, **remove ALL nodes** in the list whose value equals `val`. Return the new head.

**Example 1:** `head = [1, 2, 6, 3, 4, 5, 6]`, `val = 6`. Output: `[1, 2, 3, 4, 5]`.

**Example 2:** `head = [7, 7, 7, 7]`, `val = 7`. Output: `[]` (empty list, new head is null).

**Example 3:** `head = []`, `val = 1`. Output: `[]`.

---

## 2. Two cases that need handling

A naïve traversal looks like:

```
prev = head
while prev.next is not null:
    if prev.next.val == val:
        prev.next = prev.next.next       # splice out matching node
    else:
        prev = prev.next                 # advance
```

**This handles case A: a non-head node matches.** Standard splicing — we have a `prev`, we can rewire.

**But what about case B: the HEAD itself matches?** The head has no `prev`. To remove it, we'd have to update the EXTERNAL head pointer (i.e., the value we eventually return). And what if SEVERAL head nodes match in a row (like Example 2)?

Without a dummy, you'd need:
```
while head and head.val == val:
    head = head.next       # special-case head removal
# then walk the rest with prev pointer
```

Two pieces of logic. Easy to get wrong.

---

## 3. The dummy head idiom — what it solves

**Prepend a dummy node** whose `.next` points to the original head. Now even the "real" head has a predecessor — the dummy. The dummy itself is never modified or returned; its only job is to provide a `prev` for the first real node.

After processing, return `dummy.next` (which may differ from the original `head`, if the original head was removed).

```
dummy = Node(any value)
dummy.next = head

# walk with prev = dummy
prev = dummy
while prev.next is not null:
    if prev.next.val == val:
        prev.next = prev.next.next
    else:
        prev = prev.next

return dummy.next
```

> **Mini-refresher: why the dummy makes a difference here.**
>
> Without dummy: the EXTERNAL head pointer might point to a node that gets deleted. You need to track when to update it — an extra branch.
>
> With dummy: there's only ONE pointer that could change — `dummy.next`. And that's updated through the SAME mechanism (`prev.next = prev.next.next`) as any internal deletion. **No special case.**
>
> The "head was deleted" case becomes invisible to the algorithm.

---

## 4. The walk with "do NOT advance after a removal"

A subtle but crucial point in the walk: when we delete `prev.next`, we DO NOT advance `prev` afterwards. Why?

Suppose we have `prev → 6 → 6 → 3 → null` and `val = 6`. After deleting the first 6:

```
prev → 6 → 3 → null      (second 6 is now prev.next)
```

If we advance `prev` to the new `prev.next`, we'd land on the second 6 — but then we'd evaluate `prev.next == 3`, miss the second 6, and never delete it.

By NOT advancing, we stay at the same `prev` and re-check: now `prev.next == 6` again, match, delete. Repeat until `prev.next != 6`, then advance.

```
if prev.next.val == val:
    prev.next = prev.next.next       # delete, stay at same prev
else:
    prev = prev.next                  # only advance when we DIDN'T delete
```

This handles any number of consecutive matches naturally.

---

## 5. Code

**C++:**

```cpp
ListNode* removeElements(ListNode* head, int val) {
    ListNode dummy(0);
    dummy.next = head;
    ListNode* prev = &dummy;

    while (prev->next) {
        if (prev->next->val == val) {
            ListNode* toDelete = prev->next;
            prev->next = prev->next->next;
            delete toDelete;
        } else {
            prev = prev->next;
        }
    }

    return dummy.next;
}
```

`dummy` is stack-allocated — fine because we never return a pointer to it (we return `dummy.next`).

**Python:**

```python
def removeElements(head, val):
    dummy = ListNode(0)
    dummy.next = head
    prev = dummy

    while prev.next:
        if prev.next.val == val:
            prev.next = prev.next.next
        else:
            prev = prev.next

    return dummy.next
```

**JavaScript:**

```javascript
function removeElements(head, val) {
    const dummy = new ListNode(0);
    dummy.next = head;
    let prev = dummy;

    while (prev.next) {
        if (prev.next.val === val) {
            prev.next = prev.next.next;
        } else {
            prev = prev.next;
        }
    }

    return dummy.next;
}
```

Complexity: **O(n) time, O(1) space.**

---

## 6. Trace it

**`head = [1, 2, 6, 3, 4, 5, 6]`, `val = 6`:**

```
List:   dummy → 1 → 2 → 6 → 3 → 4 → 5 → 6 → null
prev = dummy.

Iter 1: prev.next = 1. 1 != 6 → advance. prev = Node(1).
Iter 2: prev.next = 2. 2 != 6 → advance. prev = Node(2).
Iter 3: prev.next = 6. MATCH → prev.next = Node(3). DO NOT advance.
        List: dummy → 1 → 2 → 3 → 4 → 5 → 6 → null. prev still at Node(2).
Iter 4: prev.next = 3. 3 != 6 → advance. prev = Node(3).
Iter 5: prev.next = 4. advance. prev = Node(4).
Iter 6: prev.next = 5. advance. prev = Node(5).
Iter 7: prev.next = 6. MATCH → prev.next = null. DO NOT advance.
        List: dummy → 1 → 2 → 3 → 4 → 5 → null. prev still at Node(5).
Iter 8: prev.next = null. Exit.

Return dummy.next = Node(1).   → List values: [1, 2, 3, 4, 5]. ✓
```

**`head = [7, 7, 7, 7]`, `val = 7`:**

```
List: dummy → 7 → 7 → 7 → 7 → null.
prev = dummy.

Iter 1: prev.next = 7. MATCH. prev.next = next 7. dummy → 7 → 7 → 7 → null.
Iter 2: prev.next = 7. MATCH. dummy → 7 → 7 → null.
Iter 3: prev.next = 7. MATCH. dummy → 7 → null.
Iter 4: prev.next = 7. MATCH. dummy → null.
Iter 5: prev.next = null. Exit.

Return dummy.next = null.  → empty list. ✓
```

Notice: the algorithm didn't need ANY special handling for "all heads match." The dummy made every match look the same.

---

## 7. Why not advance after a delete?

Already covered, but worth re-stating with the trace.

In iter 7 above: after deleting the second 6, `prev.next = null`. If we'd advanced `prev` to "the new prev.next" right after the deletion, we'd be at `null` — and the loop condition `prev.next != null` would crash on null dereference (no `.next` on a null pointer).

By NOT advancing on deletion, we re-examine `prev.next` on the next iteration. If it's null, the loop exits cleanly. If it's another matching value, we delete again.

The rule: **delete → re-check the same `prev`. Advance only when we DIDN'T delete.**

---

## 8. Common pitfalls

1. **No dummy head.** Then you need TWO loops or a special case: "skip leading head-matches, then walk the rest." More code, easier to bug.

2. **Advancing `prev` after a deletion.** Causes consecutive matches to be missed. The "do NOT advance" rule is the whole reason this algorithm is one-pass.

3. **Comparing `prev` instead of `prev.next`.** We're checking the NODE WE'RE ABOUT TO PASS, not the one we're standing on. Compare `prev.next.val` against `val`.

4. **Returning `head` instead of `dummy.next`.** If the original head was deleted, `head` now points to a freed (or stale) node. Always return `dummy.next`.

5. **Forgetting the null-check in the loop.** `while prev.next` (truthy check on the pointer) handles null. Don't write `while prev.next.val == val` — that crashes when `prev.next` is null.

6. **Allocating dummy on the heap and forgetting to delete it.** Stack-allocate for short-lived helpers. Or wrap in a smart pointer (`std::unique_ptr` in C++).

7. **Modifying `head` directly inside the loop.** Don't. Always work through `dummy.next`. Reassigning `head` doesn't affect the return value if you correctly return `dummy.next`.

8. **Recursive solution stack overflow.** A recursive version exists (`removeElements(head.next, val)`) but uses O(n) stack — for very long lists, it overflows.

---

## 9. The shape — dummy head everywhere

The dummy-head idiom is used wherever **the head MIGHT be modified**:

| Problem | What might change about the head |
|---|---|
| **This problem** | head deleted |
| Remove Nth from End | head deleted (if n == length) |
| Reverse Linked List II (sublist reverse) | head reversed (if range starts at 0) |
| Merge Two Sorted Lists | new head is the smaller of two starting heads |
| Add Two Numbers | new head from carry/digit |
| Partition List | result has new head (smaller-than-pivot section) |
| Odd Even Linked List | head reassembled |

**Pattern to internalize:**

> "Whenever a linked-list operation MIGHT modify the head pointer (insert, delete, reverse, merge), prepend a dummy. The dummy's `.next` always points to whatever the current head is. Return `dummy.next` at the end."

Once you start doing this reflexively, linked-list code becomes much shorter.

---

> **Self-check — the question to ask next time.**
>
> When you face a linked-list problem where the head might change (deletion, insertion-before, swap), ask:
>
> > **"Can I prepend a dummy node so 'modifying the head' is the same as 'modifying any internal node'? Then I write one loop with no head-special-case, and return dummy.next."**
>
> If yes, the algorithm simplifies dramatically.

---

## Cross-references

- **Reference card (post-mastery):** [`../Remove_Linked_List_Elements.md`](../Remove_Linked_List_Elements.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Design_Linked_List.md`](./Design_Linked_List.md), [`Delete_Node_in_a_Linked_List.md`](./Delete_Node_in_a_Linked_List.md).
  - Coming next: [`Reverse_Linked_List.md`](./Reverse_Linked_List.md) — THE foundational three-pointer iter pattern.
