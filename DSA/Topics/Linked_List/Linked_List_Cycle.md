# Linked List Cycle

**Problem Link:**
<a href="https://leetcode.com/problems/linked-list-cycle/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/linked-list-cycle/</a>

**Topic:**
Linked List

----------------------------------------

## Step 1: What's the Problem?

You're given the head of a singly linked list. Determine whether it contains a cycle — meaning, if you keep following `.next` pointers, do you ever revisit a node?

Example of a cycle: `1 → 2 → 3 → 4 → 2 → 3 → 4 → 2 → ...` (node 4 points back to node 2).
Example of no cycle: `1 → 2 → 3 → null`.

----------------------------------------

## Step 2: The Most Obvious Idea First

As I walk the list, I could remember every node I've visited. If I ever arrive at a node I've seen before — cycle. If I reach `null` — no cycle.

```cpp
bool hasCycle(ListNode* head) {
    unordered_set<ListNode*> seen;
    while (head) {
        if (seen.count(head)) return true;
        seen.insert(head);
        head = head->next;
    }
    return false;
}
```

This works. Time O(n), space O(n). But the space bothers me — we're allocating a hashmap of potentially millions of pointers just to ask a yes/no question. Is there a way without extra memory?

----------------------------------------

## Step 3: Thinking Physically

Imagine two people walking along the list from the head. Walker A moves one node per step. Walker B moves two nodes per step (B is faster).

- **If the list has no cycle:** B will reach `null` first, and we can stop.
- **If the list has a cycle:** once both walkers enter the cycle, they're trapped in a loop. B gains on A by exactly 1 node per step. Eventually B catches up to A, like a faster runner lapping a slower one on a circular track.

This is the classic "tortoise and hare" intuition. Let me work out *why* B is guaranteed to catch A and not, say, miss them by skipping ahead.

----------------------------------------

## Step 4: Proving the Fast Walker Always Catches the Slow One

Suppose both walkers are inside the cycle. Let the cycle length be `C`. Measure each walker's position *modulo C* (as an offset around the cycle). A's position advances by 1 mod C per step. B advances by 2 mod C per step.

Now look at the gap: `(B - A) mod C` starts at some value `d` (when both first entered the cycle). Each step, A advances 1, B advances 2, so the gap grows by `(2 - 1) = 1` modulo C. So after C steps, the gap has increased by C ≡ 0, which means the gap has cycled through every value 0, 1, 2, ..., C-1 before returning. At some point in that cycle, the gap hits 0 — that's when B catches A.

That's why the meeting is guaranteed. Not magic. It's modular arithmetic on the cycle.

If there's no cycle, B reaches `null` first (or B's next is `null`), and we exit.

----------------------------------------

## Step 5: Converting to Code

Two pointers, `slow` and `fast`. Both start at `head`. Each step:

- Move `slow` by 1.
- Move `fast` by 2 (which requires that `fast->next` isn't null, else we'd segfault).
- If `slow == fast`, there's a cycle.
- If `fast` or `fast->next` is null, we've reached the end — no cycle.

```cpp
bool hasCycle(ListNode* head) {
    auto slow = head;
    auto fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return true;
    }
    return false;
}
```

Compare to the hashmap version: same O(n) time, but now O(1) space. We're using pointer comparisons instead of allocating memory.

----------------------------------------

## Step 6: Trace on a Concrete Cycle

List: `3 → 2 → 0 → -4 → (back to 2)`. Indices I'll use for clarity: `A → B → C → D → B`.

```
Initial: slow = A, fast = A.

Iter 1: slow = B, fast = C. Not equal.
Iter 2: slow = C, fast = B (fast went D → B). Not equal.
Iter 3: slow = D, fast = D. Equal! Return true.
```

Works. Now for a non-cyclic list `1 → 2 → 3 → null`:

```
Initial: slow = 1, fast = 1.

Iter 1: slow = 2, fast = 3. Not equal.
Iter 2: slow = 3, fast = null (3's next is null, fast = 3->next->next = null... wait, 3->next is null, so we can't do 3->next->next).
```

Ah, so actually in iter 2 the while condition fails first: `fast->next` is null. We exit the loop and return `false`. Correct.

----------------------------------------

## Step 7: Edge Cases

- **Empty list (`head == null`).** The while loop doesn't execute. Return false. ✓
- **Single node, no self-loop.** `fast = head`, `fast->next = null`. Loop fails. Return false. ✓
- **Single node with self-loop (`head->next == head`).** `fast = head->next = head`, which is not null. Inside: `slow = head`, `fast = head->next->next = head->next = head`. `slow == fast`. Return true. ✓
- **Two-node cycle (A → B → A).** `slow = B`, `fast = A`. Not equal. Next iter: `slow = A`, `fast = A`. Equal. Return true. ✓

These edge cases are easy to get wrong with naïve pointer code, but the simple `while (fast && fast->next)` guard handles all of them.

----------------------------------------

## Step 8: Complexity

Time: If there's a cycle, within at most ~C iterations after both pointers enter the cycle, they meet. Before entering the cycle, both pointers walk the non-cyclic prefix of length `μ`. Total: O(μ + C) = **O(n)**.

Space: two pointers. **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
bool hasCycle(ListNode* head) {
    auto slow = head, fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return true;
    }
    return false;
}
```

This algorithm is known as **Floyd's tortoise-and-hare**. But — following our own rule — we didn't reach for it by name. We reached for it by thinking: can two walkers at different speeds detect a loop? They can, and the why-does-it-work argument is modular arithmetic on the cycle.

----------------------------------------

## Step 10: Follow-up Questions

- **Find the node *where* the cycle begins** (Linked List Cycle II). Once slow and fast meet, reset slow to `head` and advance both by 1; they meet at the cycle entrance. The proof is another nice exercise in modular arithmetic.
- **Cycle length.** After the meeting, keep `fast` stationary and walk `slow` until they meet again — the number of steps is the cycle length.
- **Remove the cycle.** Find the entrance (as above), walk around the cycle until the node whose `next` is the entrance, and set that `next` to null.
- **Why doesn't fast move 3 steps instead of 2?** It still works, but 2 is the minimum speed that guarantees meeting in one cycle traversal with the cleanest proof. More general: any speed difference ≥ 1 works.
- **Does this work on doubly-linked lists?** Yes, same logic — we only use `->next`.
