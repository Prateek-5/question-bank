# Merge Two Sorted Lists — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Merge_Two_Sorted_Lists.md`](../Merge_Two_Sorted_Lists.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/merge-two-sorted-lists/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **This is the linked-list version of merge-sort's merge step.** The lesson: **two sorted sequences + monotonic pointers + a dummy head = O(n+m) merge in O(1) space.** Re-link existing nodes; don't copy. This pattern reappears in Merge K Sorted Lists, Sort Linked List, and Add Two Numbers. **Read [`Reverse_Linked_List.md`](./Reverse_Linked_List.md) and [`Remove_Linked_List_Elements.md`](./Remove_Linked_List_Elements.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. The card-shuffle analogy
3. Why a dummy head simplifies everything
4. The merge loop
5. Code
6. Trace it
7. Why we re-link instead of copying
8. Common pitfalls
9. The shape — merge appears everywhere

---

## 1. Read the problem

You're given the heads of two **sorted** (non-decreasing) singly-linked lists, `list1` and `list2`. Merge them into one **sorted** linked list and return its head.

You should splice TOGETHER the nodes of the two given lists (don't allocate new nodes — re-link).

**Examples:**

- `list1 = [1, 2, 4]`, `list2 = [1, 3, 4]` → merged: `[1, 1, 2, 3, 4, 4]`.
- `list1 = []`, `list2 = []` → `[]`.
- `list1 = []`, `list2 = [0]` → `[0]`.

---

## 2. The card-shuffle analogy

Imagine two sorted decks of cards face-up. To produce one merged sorted deck, you can:

1. Look at the top card of each deck.
2. Pick the smaller one. Place it on the OUTPUT deck.
3. Reveal the next card under the one you took.
4. Repeat until one deck is empty.
5. Append the remaining (non-empty) deck onto the output.

This is the entire algorithm. The deck "tops" are the heads. "Reveal next" = `head = head.next`. The OUTPUT deck is what we're building.

> **Mini-refresher: same as merge in merge-sort.**
>
> If you've done merge sort on arrays, the merge step is identical:
> - Two sorted arrays + two index pointers.
> - At each step, take the smaller-indexed element from one array.
> - When one array runs out, copy the rest of the other.
>
> Linked list version replaces "array index" with "node pointer." Same logic.

---

## 3. Why a dummy head simplifies everything

Without a dummy, the first iteration is awkward: we need to ESTABLISH the merged list's head, which could come from either `list1` or `list2`. Many implementations special-case this:

```
# Awkward, but functional:
if list1.val <= list2.val:
    head = list1; list1 = list1.next
else:
    head = list2; list2 = list2.next
tail = head
# now loop...
```

With a dummy head:

```
dummy = new Node(0)
tail = dummy
# loop and always do tail.next = pick; tail = tail.next
return dummy.next
```

The "set the head" logic disappears. After the loop, `dummy.next` is whatever the first picked node was.

> **Mini-refresher: dummy head when building a NEW list.**
>
> The dummy head is useful in TWO scenarios:
> 1. **Modifying an existing list** where the head might change (Remove Linked List Elements, Remove Nth From End).
> 2. **Building a new list** where the first node isn't yet determined (this problem, Add Two Numbers, Partition List).
>
> Both cases: dummy.next holds whatever the "current head" is at any moment. Return dummy.next at the end.

---

## 4. The merge loop

```
dummy = new Node(0)
tail = dummy

while list1 != null and list2 != null:
    if list1.val <= list2.val:
        tail.next = list1
        list1 = list1.next
    else:
        tail.next = list2
        list2 = list2.next
    tail = tail.next

# At most one of list1, list2 is non-null.
tail.next = (list1 if list1 else list2)

return dummy.next
```

Phases:
1. **Main merge:** while both lists have nodes, pick the smaller head, append, advance.
2. **Drain:** after one list is exhausted, append the remaining list wholesale (since it's already sorted).

Why the drain works: the remaining list is sorted, and all its values are ≥ the last appended value (we appended in order). So just hook the rest onto `tail`.

---

## 5. Code

**C++:**

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

**Python:**

```python
def mergeTwoLists(list1, list2):
    dummy = ListNode(0)
    tail = dummy
    while list1 and list2:
        if list1.val <= list2.val:
            tail.next = list1
            list1 = list1.next
        else:
            tail.next = list2
            list2 = list2.next
        tail = tail.next
    tail.next = list1 if list1 else list2
    return dummy.next
```

**JavaScript:**

```javascript
function mergeTwoLists(list1, list2) {
    const dummy = new ListNode(0);
    let tail = dummy;
    while (list1 && list2) {
        if (list1.val <= list2.val) {
            tail.next = list1;
            list1 = list1.next;
        } else {
            tail.next = list2;
            list2 = list2.next;
        }
        tail = tail.next;
    }
    tail.next = list1 ? list1 : list2;
    return dummy.next;
}
```

Complexity: **O(n + m) time, O(1) space.**

---

## 6. Trace it

`list1 = [1, 2, 4]`, `list2 = [1, 3, 4]`.

```
dummy.next = null. tail = dummy. a = 1A. b = 1B.   (A and B distinguish which list)

Iter 1: a.val=1, b.val=1. 1 <= 1, pick A. tail.next = 1A. a = 2A. tail = 1A.
        State: dummy → 1A. list1: 2A → 4A. list2: 1B → 3B → 4B.

Iter 2: a.val=2, b.val=1. 2 > 1, pick B. tail.next = 1B. b = 3B. tail = 1B.
        State: dummy → 1A → 1B. list1: 2A → 4A. list2: 3B → 4B.

Iter 3: a.val=2, b.val=3. 2 <= 3, pick A. tail.next = 2A. a = 4A. tail = 2A.
        State: dummy → 1A → 1B → 2A. list1: 4A. list2: 3B → 4B.

Iter 4: a.val=4, b.val=3. 4 > 3, pick B. tail.next = 3B. b = 4B. tail = 3B.
        State: dummy → 1A → 1B → 2A → 3B. list1: 4A. list2: 4B.

Iter 5: a.val=4, b.val=4. 4 <= 4, pick A. tail.next = 4A. a = null. tail = 4A.
        State: dummy → 1A → 1B → 2A → 3B → 4A. list1: empty. list2: 4B.

Loop exit (a is null).

Drain: tail.next = b = 4B.
       State: dummy → 1A → 1B → 2A → 3B → 4A → 4B.

Return dummy.next = 1A. Values: [1, 1, 2, 3, 4, 4]. ✓
```

Notice when values tied (iter 1 and iter 5), we picked from `list1`. The `<=` tie-breaker means `list1`'s nodes come first when equal — making the merge STABLE.

---

## 7. Why we re-link instead of copying

We're reusing the original nodes' memory. Each node from `list1` and `list2` eventually becomes part of the merged list — we just CHANGE THE `.next` pointers.

This is efficient (O(1) extra space) but has implications:
- The original `list1` and `list2` are MUTATED. After merge, `list1.next` and `list2.next` may point into the wrong list.
- If you need to preserve the originals, copy first (then merge), or make copies of nodes as you append.

For LeetCode, the spec allows this mutation. The caller hands you the lists with the understanding that they may be consumed.

> **Mini-refresher: in-place vs out-of-place.**
>
> "In-place" = reuse existing memory; mutate inputs.
> "Out-of-place" = allocate new memory for the result.
>
> In-place is preferred when memory matters and input doesn't need preserving. For sorting/merging linked lists, in-place via re-linking is the canonical approach.

---

## 8. Common pitfalls

1. **No dummy head.** Then the first iteration has a special case. Tolerable but uglier.

2. **Forgetting to advance `tail`.** `tail.next = picked_node; tail = tail.next`. Skipping the second line breaks the chain.

3. **Forgetting to drain.** After one list is empty, the other still has nodes — they must be appended. `tail.next = (whichever is non-null)`.

4. **Using `<` instead of `<=`.** Both work, but `<` makes the merge unstable for equal values (you pick from `list2`, then on the next iteration you pick from `list1`, etc.). Pick a tie-break direction and stay consistent.

5. **Allocating new nodes for the merged list.** Wasteful when re-linking suffices. Acceptable, but O(n+m) space and one allocation per node.

6. **Returning `tail` instead of `dummy.next`.** `tail` points to the LAST node, not the head. Return `dummy.next`.

7. **Stack overflow with recursive version.** A recursive merge (mergeTwoLists(a.next, b)) uses O(n+m) stack space. Iterative is safer for large lists.

8. **Modifying `dummy` after return.** In C++, if `dummy` is a stack variable inside the function, returning a POINTER to dummy itself would dangle. We return `dummy.next` (heap-allocated), which is fine.

---

## 9. The shape — merge appears everywhere

The two-pointer merge of sorted sequences is one of the most reused patterns in computer science.

| Problem | Inputs | Output |
|---|---|---|
| **This problem** | 2 sorted linked lists | 1 sorted linked list |
| Merge Sorted Array (LC #88) | 2 sorted arrays | 1 sorted array (in-place) |
| Merge K Sorted Lists (LC #23) | K sorted linked lists | 1 sorted linked list |
| Sort List (LC #148) | 1 unsorted linked list | sort via merge-sort |
| External merge sort (databases) | Multiple sorted runs on disk | 1 sorted run |
| Add Two Numbers (LC #2) | 2 linked-list numbers | 1 linked-list sum (similar dummy-head pattern) |
| Intersection of Sorted Arrays | 2 sorted arrays | common elements |

**Pattern to internalize:**

> "Two (or more) sorted sequences = merge with monotonic pointers + dummy head. Each output node picked in O(1) from a comparison of heads. Total O(n+m) time, O(1) space (for 2 sequences)."

When the problem mentions "sorted" + "merge" / "combine" / "intersect", reach for this pattern.

---

> **Self-check — the question to ask next time.**
>
> When you face "merge two (or more) sorted sequences," ask:
>
> > **"Can I walk both with one pointer each, picking the smaller head at every step, with a dummy head to anchor the result?"**
>
> If yes, you've got O(n+m).

---

## Cross-references

- **Reference card (post-mastery):** [`../Merge_Two_Sorted_Lists.md`](../Merge_Two_Sorted_Lists.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Remove_Linked_List_Elements.md`](./Remove_Linked_List_Elements.md), [`Reverse_Linked_List.md`](./Reverse_Linked_List.md) — node mechanics.
  - Coming next: [`Palindrome_Linked_List.md`](./Palindrome_Linked_List.md) — composes reverse + middle + zip.
  - Coming later: Merge_K_Sorted_Lists (in Heap_Priority_Queue) — generalizes this with a heap.
