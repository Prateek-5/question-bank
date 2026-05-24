# Linked List — Learning Path

> **Stage:** Foundation   |   **Prereqs:** none   |   **Problems:** 11
>
> Pointer manipulation without the safety net of random access. The canonical "do you think in pointers" topic.
>
> **Two-tier format:** each problem has a **reference card** (linked first below) AND a paced **teaching walkthrough** in [`learn/`](./learn/) for first-time learners.

---

## How to study this topic

1. Design and basic ops (build muscle memory for node manipulation).
2. Single-pass deletes with dummy-head trick.
3. In-place reverse (the iter pattern you'll reuse forever).
4. Slow/fast (Floyd) — middle, n-th-from-end, cycle.
5. Merge and palindrome (compose previous patterns).

---

## Problems in study order

### Design — implement the API

1. **[Design_Linked_List.md](./Design_Linked_List.md)**  ·  [walkthrough →](./learn/Design_Linked_List.md) — Build it yourself: `addAtHead`, `addAtTail`, `addAtIndex`, `get`, `delete`. Establishes every primitive you'll use later. **must-do**

### Single-node tricks

2. **[Delete_Node_in_a_Linked_List.md](./Delete_Node_in_a_Linked_List.md)**  ·  [walkthrough →](./learn/Delete_Node_in_a_Linked_List.md) — Copy-and-skip trick when you don't have the head. Clever puzzle.

### Dummy-head idiom

3. **[Remove_Linked_List_Elements.md](./Remove_Linked_List_Elements.md)**  ·  [walkthrough →](./learn/Remove_Linked_List_Elements.md) — Dummy head before iteration so you can delete the original head uniformly. **must-do**

### In-place reverse (THE pattern)

4. **[Reverse_Linked_List.md](./Reverse_Linked_List.md)**  ·  [walkthrough →](./learn/Reverse_Linked_List.md) — `prev / cur / nxt` three-pointer iterative reverse. Burn into reflex. **must-do**

### Slow / fast (Floyd's tortoise and hare)

5. **[Middle_of_the_Linked_List.md](./Middle_of_the_Linked_List.md)**  ·  [walkthrough →](./learn/Middle_of_the_Linked_List.md) — Slow moves 1, fast moves 2. **must-do**
6. **[Remove_Nth_Node_From_End_of_List.md](./Remove_Nth_Node_From_End_of_List.md)**  ·  [walkthrough →](./learn/Remove_Nth_Node_From_End_of_List.md) — Fixed-gap two-pointer; gap = n. **must-do**
7. **[Linked_List_Cycle.md](./Linked_List_Cycle.md)**  ·  [walkthrough →](./learn/Linked_List_Cycle.md) — Floyd's cycle detection. **must-do**
8. **[Linked_List_Cycle_II.md](./Linked_List_Cycle_II.md)**  ·  [walkthrough →](./learn/Linked_List_Cycle_II.md) — After detection, reset one pointer to head — they meet at the cycle start. The math is elegant. **must-do**

### Compose patterns — merge and palindrome

9. **[Merge_Two_Sorted_Lists.md](./Merge_Two_Sorted_Lists.md)**  ·  [walkthrough →](./learn/Merge_Two_Sorted_Lists.md) — Dummy head + zip-merge. Foundation for Merge K (in Heap). **must-do**
10. **[Palindrome_Linked_List.md](./Palindrome_Linked_List.md)**  ·  [walkthrough →](./learn/Palindrome_Linked_List.md) — Find middle + reverse second half + compare. Composes 3 patterns.

### Light traversal

11. **[Convert_Binary_Number_in_a_Linked_List_to_Integer.md](./Convert_Binary_Number_in_a_Linked_List_to_Integer.md)**  ·  [walkthrough →](./learn/Convert_Binary_Number_in_a_Linked_List_to_Integer.md) — Walk + accumulate. Warm-up if you need a break.

---

## Patterns established

- **Dummy head:** Adds a sentinel before the real head so insertion/deletion at index 0 doesn't need a special case.
- **Three-pointer iterative reverse:** `prev=null, cur=head; while (cur) { nxt = cur.next; cur.next = prev; prev = cur; cur = nxt; }`.
- **Slow / fast pointers:** Move `slow` by 1 and `fast` by 2. Used for middle, cycle detection, n-th from end (with gap variant).
- **Cycle entry point (Floyd):** After slow/fast meet, reset one to head; advance both by 1; they meet at the cycle entry.
- **Compose:** Middle + reverse-half + zip-traversal solves palindrome in O(1) extra space.

---

## Common traps

- **Losing the next pointer before reusing it.** Always save `nxt = cur.next` before overwriting `cur.next`.
- **Off-by-one on slow/fast for even-length lists.** Decide: do you want the lower-middle or the upper-middle?
- **Forgetting `fast && fast.next` in the loop condition.** Both must be checked before `fast.next.next`.
- **Modifying the list before the second pointer reaches the end** in fixed-gap problems.
- **Cycle detection ignoring single-node self-loop** (where `head.next == head`).

---

## After this topic

- **[Recursion/](../Recursion/LEARNING.md)** — many linked-list problems have elegant recursive forms; iterative is just clearer for interviews.
- **[Heap_Priority_Queue/](../Heap_Priority_Queue/LEARNING.md)** — Merge K Sorted Lists uses Merge Two as a primitive.
- **[Two_Pointers/](../Two_Pointers/LEARNING.md)** — slow/fast IS two-pointer on linked structures.
