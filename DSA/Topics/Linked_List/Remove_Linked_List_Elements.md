# Remove Linked List Elements

**Problem Link:**
https://leetcode.com/problems/remove-linked-list-elements/

**Topic:**
Linked List

----------------------------------------

## Step 1: Setup

Given the head of a linked list and a value `val`, remove **all nodes** with that value. Return the new head.

Example: `head = [1, 2, 6, 3, 4, 5, 6]`, val = 6. Remove both 6s. Result: `[1, 2, 3, 4, 5]`.

Example: `head = [7, 7, 7, 7]`, val = 7. Remove everything. Result: `[]` (null head).

----------------------------------------

## Step 2: Two Cases That Need Care

**Case 1: A non-head node matches.** Standard unlinking:
- `prev.next = prev.next.next` (skips the matching node).
- Don't advance `prev` yet — the new `prev.next` might also match.

**Case 2: The head itself matches.** We can't rewire a "prev" (there is none). We'd need to update `head` itself.

Using a plain traversal requires special-casing this. Or we can use the classic **dummy head** trick.

----------------------------------------

## Step 3: Dummy Head to the Rescue

Prepend a dummy node whose `.next` points to `head`. Now the "real head" is dummy.next. Every node — including the original head — has a predecessor (dummy for the original head).

With the dummy, we use one loop and no special case:

```
dummy = new Node(0)
dummy.next = head
prev = dummy

while prev.next is not null:
    if prev.next.val == val:
        prev.next = prev.next.next   # skip the matching node
        # don't advance prev — check if new prev.next also matches
    else:
        prev = prev.next

return dummy.next
```

----------------------------------------

## Step 4: Trace on `[1, 2, 6, 3, 4, 5, 6]`, val = 6

```
dummy → 1 → 2 → 6 → 3 → 4 → 5 → 6 → null.
prev = dummy.

prev.next = 1. 1 != 6. Advance. prev = 1.
prev.next = 2. 2 != 6. Advance. prev = 2.
prev.next = 6. Match. prev.next = 3 (skip 6).
  Now: dummy → 1 → 2 → 3 → 4 → 5 → 6. prev still at 2.
prev.next = 3. 3 != 6. Advance. prev = 3.
prev.next = 4. Advance. prev = 4.
prev.next = 5. Advance. prev = 5.
prev.next = 6. Match. prev.next = null (skip 6).
  Now: dummy → 1 → 2 → 3 → 4 → 5.
prev.next = null. Exit loop.

Return dummy.next = 1.
```

Result: `[1, 2, 3, 4, 5]`. ✓

----------------------------------------

## Step 5: Why Not Advance `prev` After Removal

Scenario: consecutive matching nodes. E.g., `6 → 6 → 3`, val = 6.

If at `prev → 6 → 6 → 3`, we set `prev.next = prev.next.next = (second 6)`. List is now `prev → 6 → 3`. If we advance prev, we'd be at the second 6 — skipping the check for the still-matching node now in `prev.next` position.

By NOT advancing, we stay at the same prev and re-check: `prev.next = 6`, match again, skip to `3`. Now advance.

This pattern handles any number of consecutive matches naturally.

----------------------------------------

## Step 6: Trace `[7, 7, 7, 7]`, val = 7

```
dummy → 7 → 7 → 7 → 7.
prev = dummy.

prev.next = 7. Match. prev.next = 7 (second). List: dummy → 7 → 7 → 7.
prev.next = 7. Match. prev.next = 7 (third). List: dummy → 7 → 7.
prev.next = 7. Match. prev.next = 7 (fourth). List: dummy → 7.
prev.next = 7. Match. prev.next = null. List: dummy.
prev.next = null. Exit.

Return dummy.next = null.
```

Result: empty list. ✓

The algorithm handled the all-match case correctly thanks to the dummy.

----------------------------------------

## Step 7: Name It

**Linked list traversal with dummy head for clean deletion.** The dummy is a workhorse pattern:
- Simplifies head modifications.
- Lets a single loop handle all cases uniformly.
- Eliminates null-check special cases.

Related:
- Merge Two Sorted Lists (dummy head for building output).
- Reverse Linked List II (dummy head for cleaner boundary).
- Palindrome Linked List (not directly, but similar style).

Whenever a problem "might modify the head," use a dummy.

----------------------------------------

## Step 8: Complexity

Time: **O(n)** — single pass.
Space: **O(1)** — dummy is a single extra node.

----------------------------------------

## Step 9: C++ Implementation

```cpp
ListNode* removeElements(ListNode* head, int val) {
    ListNode dummy(0);
    dummy.next = head;
    ListNode* prev = &dummy;

    while (prev->next) {
        if (prev->next->val == val) {
            ListNode* toDelete = prev->next;
            prev->next = prev->next->next;
            delete toDelete;   // C++: free memory
        } else {
            prev = prev->next;
        }
    }

    return dummy.next;
}
```

I added `delete toDelete` to free the node's memory in C++. In garbage-collected languages, this isn't needed.

The dummy being a stack-allocated variable is fine — we return `dummy.next`, which is either null or a real heap-allocated node (passed in or not deleted).

----------------------------------------

## Step 10: Follow-up Questions

- **Remove only the first occurrence.** Add a `break` after one removal.
- **Remove all nodes matching a predicate (not just a value).** Parameterize the check.
- **Recursive version.**
  ```cpp
  ListNode* removeElements(ListNode* head, int val) {
      if (!head) return nullptr;
      head->next = removeElements(head->next, val);
      return head->val == val ? head->next : head;
  }
  ```
  Elegant but O(n) stack depth — not safe for very long lists.
- **Remove duplicates (not just a specific value).** Different problem — sort or use a hashset.
- **Keep only nodes matching the predicate.** Invert the logic.
- **Doubly-linked list variant.** Straightforward: update both prev/next pointers when removing.
