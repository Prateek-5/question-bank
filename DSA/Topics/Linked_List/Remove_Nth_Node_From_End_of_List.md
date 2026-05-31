# Remove Nth Node From End of List

**Problem Link:**
<a href="https://leetcode.com/problems/remove-nth-node-from-end-of-list/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/remove-nth-node-from-end-of-list/</a>

**Topic:**
Linked List

----------------------------------------

## Step 1: Restate the Problem

Given the head of a linked list and an integer `n`, remove the n-th node **from the end**, and return the updated head.

Example: `1 → 2 → 3 → 4 → 5`, `n = 2`. The 2nd-from-end is node `4` (counting backward: 5 is 1st, 4 is 2nd). Result: `1 → 2 → 3 → 5`.

Edge cases worth considering up front:
- `n` could equal the length — we remove the head.
- The list could have exactly one node and `n = 1` — we return null.

----------------------------------------

## Step 2: The Two-Pass Solution First

The obvious approach: first count the length `L`, then walk to the `(L - n)`-th node from the start, and remove the one after it. That's fine and straightforward.

```cpp
int L = 0;
for (auto* p = head; p; p = p->next) L++;
// remove node at position (L - n) from the start (0-indexed)
auto* p = dummy;
for (int i = 0; i < L - n; ++i) p = p->next;
p->next = p->next->next;
```

Two passes, O(L). Works cleanly, but we're asked — implicitly by interviewers, and often explicitly — whether we can do it in **one pass**.

Why would one pass even be possible? The problem is that when we reach the end, we'd need to know about a node `n` positions back. Can we somehow "keep track" of that node as we walk?

----------------------------------------

## Step 3: The Gap Trick

Here's an idea. What if we had **two pointers separated by a fixed gap of `n`?**

- Pointer A is at some node.
- Pointer B is `n` nodes ahead of A.

Now advance both in sync. When B reaches the end (null or last node), A is exactly `n` nodes back from B — which is exactly where the n-th-from-end lives (or just before it, depending on how we count).

This is the classic "gap of n" trick. It converts "where is the n-th-from-end?" from a backward question into a forward one, using two pointers.

Let me nail down the exact gap and loop condition.

----------------------------------------

## Step 4: Precise Setup — Remove, Not Just Find

We don't just want to *find* the target; we want to **remove** it. To remove a node in a singly linked list, we need access to the **node before it** (so we can set `prev.next = prev.next.next`).

So we want A to land **one step before** the target, and B to land at the end (or specifically, at `null` so our termination is clean).

If A is at position `prev_target` (0-indexed, just before the target), and B is at position `length` (null), then `B - A = length - prev_target`. We need this gap to equal `n + 1` (because `prev_target = length - n - 1` when `target = length - n`).

Wait, let me derive it with a concrete example.

`1 → 2 → 3 → 4 → 5`, `n = 2`. Target is node 4 (position 3, 0-indexed). `prev_target` is node 3 (position 2). We want A to end at position 2, B to end at position 5 (null). Gap = 5 - 2 = 3. And `n + 1 = 3`. ✓

So **advance B by `n + 1` steps first**, then walk A and B in sync until B is null. A ends up at the node just before the target.

----------------------------------------

## Step 5: Handling the "Remove the Head" Case

If `n == length`, the target is the head itself. Then `prev_target` doesn't exist in the original list — there's nothing before the head. Special-casing this is annoying.

The **dummy head trick** fixes it. Create a dummy node with `dummy.next = head`. Now the "node before the head" exists — it's the dummy. Walking `A` from the dummy with our gap-of-n+1 trick now works uniformly for all n.

```
dummy → 1 → 2 → 3 → 4 → 5
```

For `n = 5` (remove the head, which is node 1), we want A to end at dummy (position 0 if we count dummy as 0), B to end at null (position 6). Gap = 6 - 0 = 6 = n + 1. ✓

----------------------------------------

## Step 6: The Algorithm

```
dummy = new node; dummy.next = head
A = dummy, B = dummy

# Advance B by n+1 steps
for i in 0..n:
    B = B.next

# Walk A and B in sync until B reaches null
while B:
    A = A.next
    B = B.next

# A is at the node before the target
A.next = A.next.next

return dummy.next
```

Clean and clear. Let's trace it.

----------------------------------------

## Step 7: Trace on `1 → 2 → 3 → 4 → 5`, `n = 2`

```
dummy → 1 → 2 → 3 → 4 → 5 → null

Initial: A = dummy, B = dummy.

Advance B by n+1 = 3:
  B = 1, B = 2, B = 3.

Now walk in sync:
  A = 1, B = 4.
  A = 2, B = 5.
  A = 3, B = null → stop.

A.next = 4, A.next.next = 5.
A.next = 5. (node 4 removed)

Result: dummy → 1 → 2 → 3 → 5.
Return dummy.next = 1.
```

The remaining list is `1 → 2 → 3 → 5`. ✓

Now try `n = 5` (remove the head):

```
dummy → 1 → 2 → 3 → 4 → 5

Advance B by 6: B = 1, 2, 3, 4, 5, null.

Now walk in sync: already B == null, skip the loop.

A.next = 1, A.next.next = 2.
A.next = 2. (node 1 removed)

Result: dummy → 2 → 3 → 4 → 5.
Return dummy.next = 2.
```

Exactly right.

----------------------------------------

## Step 8: Why This Works — One-Sentence Summary

Because a **fixed gap** between two pointers turns "n-th from end" into "where A is when B is at the end" — and that's a property we can maintain throughout a single forward pass.

The dummy-head trick handles the boundary where the head itself is being removed, without adding special-case code.

----------------------------------------

## Step 9: Complexity

Time: B walks the list once; A walks once too. **O(L)** where L is the list length.
Space: two pointers and a dummy node. **O(1)**.

Same asymptotic complexity as the two-pass version, but with one fewer traversal in practice.

----------------------------------------

## Step 10: C++ Implementation

```cpp
ListNode* removeNthFromEnd(ListNode* head, int n) {
    ListNode dummy(0);
    dummy.next = head;
    ListNode* A = &dummy;
    ListNode* B = &dummy;

    // Advance B by n + 1 steps so there's a gap of n + 1 between A and B
    for (int i = 0; i <= n; ++i) B = B->next;

    // Walk in sync until B hits null
    while (B) {
        A = A->next;
        B = B->next;
    }

    // A is just before the target; skip it
    A->next = A->next->next;
    return dummy.next;
}
```

----------------------------------------

## Step 11: Follow-up Questions

- **What if `n` is larger than the list length?** The gap trick would advance `B` past the end and then the sync loop wouldn't do what we expect. Validate `n ≤ L` first, or handle the overflow explicitly.
- **Remove the n-th node from the *start* (from the head).** Straightforward — just walk `n - 1` steps and skip.
- **Remove all nodes whose values satisfy a predicate.** Single-pass with a dummy head; advance or splice out based on value.
- **Remove multiple nodes from the end in one pass.** Keep a queue of the last k pointers; after the pass, the queue holds the candidates.
- **Doubly-linked list variant.** Easier — with back-pointers you don't need a dummy head at all.


---

## Interview Signals (from LeetLens)

This problem (or close variants) was reported in **2 real interview(s)** in the LeetLens dataset (snapshot 2026-05-31). Pay attention to the company context when practicing.

| Company | Difficulty | LeetLens ID | Match | Variant note |
|---|---|---|---|---|
| Google | Easy | `83842ad2` | 1.00 (exact-title) | Remove nth Node from end of list (2nd) |
| Google | Medium | `a6ea576b` | 1.00 (exact-title) | Remove nth Node from end of list |

_Source: LeetLens DB. Match methods: `substring` = direct hit; `token-coverage` = ≥70% of this card's filename tokens appear in the question; `jaccard`/`ratio` = fuzzy title similarity._
_See the parent folder's `EXTRACTED_QUESTIONS.md` §2 for the full list of incorporated questions._
