# Middle of the Linked List

**Problem Link:**
<a href="https://leetcode.com/problems/middle-of-the-linked-list/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/middle-of-the-linked-list/</a>

**Topic:**
Linked List

----------------------------------------

## Step 1: What's the Problem Really?

You have a singly linked list. Return the middle node. If there are two middle nodes (even length), return the **second** of the two.

Examples:
- `1 → 2 → 3 → 4 → 5`: middle is `3`.
- `1 → 2 → 3 → 4 → 5 → 6`: two middles (3 and 4); return `4`.

Simple enough to say, but less obvious in a linked list because we can't just look up `list[n/2]`.

----------------------------------------

## Step 2: The Obvious First Attempt

If I knew the length `n`, the middle is the `(n/2)`-th node (0-indexed). So:

**Pass 1**: walk the list counting nodes. Now we know `n`.
**Pass 2**: walk `n/2` nodes from the head.

Two passes, O(n) time, O(1) space. Totally fine.

```cpp
ListNode* middleNode(ListNode* head) {
    int n = 0;
    for (auto* p = head; p; p = p->next) n++;
    auto* p = head;
    for (int i = 0; i < n / 2; ++i) p = p->next;
    return p;
}
```

But could we do it in **one pass**? Is there some way to arrive at the middle at the same time we arrive at the end?

----------------------------------------

## Step 3: A Thought Experiment — Two Walkers

Imagine two walkers. Walker A takes one step at a time. Walker B takes two steps at a time. They both start at the head.

- When B takes one "turn" (two steps), A takes one step.
- So whenever B has covered `2k` nodes, A has covered `k` nodes.

When B reaches the end of the list (walked `n` or close to `n` nodes), A has walked `n/2` nodes. **A is at the middle!**

That's the slow/fast pointer idea applied here. Let me nail down the exact termination condition so we don't overshoot.

----------------------------------------

## Step 4: Careful with Even and Odd Lengths

**Odd length, say n = 5:** the middle is at index 2 (0-indexed). A needs to stop at index 2. B walks 2 steps per A's 1 step. When A is at index 2, B would be at index 4 — which is the last node. So B's `next` is `null`, and we stop.

**Even length, say n = 6:** the problem wants the second middle, which is index 3. When A is at index 3, B is at index 6 — past the end. More precisely: after A advances to index 3, B tried to advance past the last node and found null. We should stop *before* B crashes.

So our loop condition needs to guard against both `B == null` and `B->next == null` (so that `B->next->next` is safe).

```
while (fast && fast->next) {
    slow = slow->next;
    fast = fast->next->next;
}
return slow;
```

Let's sanity-check both cases.

**n = 5, list: 1 → 2 → 3 → 4 → 5:**
```
slow=1, fast=1.
Iter 1: fast=1, fast.next=2 (both non-null). slow=2, fast=3.
Iter 2: fast=3, fast.next=4. slow=3, fast=5.
Iter 3: fast=5, fast.next=null → stop.
Return slow=3. ✓
```

**n = 6, list: 1 → 2 → 3 → 4 → 5 → 6:**
```
slow=1, fast=1.
Iter 1: fast=1, fast.next=2. slow=2, fast=3.
Iter 2: fast=3, fast.next=4. slow=3, fast=5.
Iter 3: fast=5, fast.next=6. slow=4, fast=null (5→6→null→null).

Wait, fast was 5 before the iteration. 5.next=6, 6.next=null. So fast advances to null. After the iteration: slow=4, fast=null.

Iter 4: fast=null → stop.
Return slow=4. ✓
```

Both cases return the expected middle.

----------------------------------------

## Step 5: What If They Asked for the *First* Middle on Even?

Small tweak: change the loop condition so B stops one step earlier.

Instead of `while (fast && fast->next)`, use `while (fast->next && fast->next->next)`. Now B stops when its next or next-next is null — which happens one step sooner on even lengths.

For `1 → 2 → 3 → 4`:
- Original: slow lands on 3 (second middle). 
- Tweaked: slow lands on 2 (first middle).

Good to know — the small boundary tweak changes the definition of "middle."

----------------------------------------

## Step 6: Why Two Pointers Is Fundamentally Right

You could read this problem and think "there must be some cleverness." And there is, but it's not about data structures or math tricks — it's about recognizing that **two linked traversals at different speeds have a synchronous relationship**. If A walks `k` steps for every `2k` steps of B, then A is *always* at position `k` when B is at `2k`. When B hits the boundary of the list, A is halfway through.

The same underlying idea appears in Linked List Cycle (Floyd's algorithm). There, two pointers at different speeds detect whether they lap each other. Here, we're not looking for a meeting — we're using the ratio of speeds to pinpoint a position.

----------------------------------------

## Step 7: Complexity

Time: one pass. B takes n/2 turns, each O(1). **O(n)**.
Space: two pointers. **O(1)**.

Same asymptotic complexity as the two-pass approach, but we do it in one pass. In practice it saves half the work when the list is very long.

----------------------------------------

## Step 8: C++ Implementation

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

This tiny function captures the whole insight.

----------------------------------------

## Step 9: Follow-up Questions

- **Return the first of the two middle nodes (even-length case).** Use the alternate loop condition `while (fast->next && fast->next->next)`.
- **What's the (n/3)-th node from the start, in one pass?** Use a trailing pointer that advances every 3 steps of the fast pointer.
- **What's the k-th node from the *end*?** Have a pointer move k steps ahead, then advance both in sync until the leader hits the end.
- **Splitting a linked list into two halves at the middle.** Find the middle, then split. `slow.next = null` after finding the middle, return (head, saved-next-of-slow).
- **Why does this work even if the list has a cycle?** It doesn't — Floyd detects cycles but the concept of "middle" doesn't cleanly apply to cyclic lists. Be careful.
