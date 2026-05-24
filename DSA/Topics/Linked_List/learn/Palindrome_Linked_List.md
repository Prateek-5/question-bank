# Palindrome Linked List — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Palindrome_Linked_List.md`](../Palindrome_Linked_List.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/palindrome-linked-list/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **This is a "composition" problem** — combine three primitives (find middle + reverse + compare) into one O(n) time, O(1) space algorithm. The lesson: **complex linked-list problems often decompose into chains of simpler primitives.** Master each primitive separately, then notice when they snap together. **Read [`Middle_of_the_Linked_List.md`](./Middle_of_the_Linked_List.md) and [`Reverse_Linked_List.md`](./Reverse_Linked_List.md) first.**

**Map of this file (10 short sections):**

1. Read the problem
2. The easy O(n) space version
3. The pivot — back half reversed = forward half (if palindrome)
4. The three-step plan
5. Code
6. Trace it on even and odd lengths
7. Why "walk until one is null" handles both parities
8. Common pitfalls
9. The shape — composition of primitives
10. Cross-references

---

## 1. Read the problem

Given the head of a singly-linked list, return `true` if it's a **palindrome** (reads the same forward and backward), `false` otherwise.

**Examples:**

- `1 → 2 → 2 → 1` → true (palindrome).
- `1 → 2` → false.
- `1` → true (single element, vacuously palindrome).
- `1 → 2 → 3 → 2 → 1` → true (odd-length palindrome).
- `1 → 0 → 1` → true.

**The challenge:** the obvious approach uses O(n) extra space. Can you do it in **O(n) time AND O(1) space**?

---

## 2. The easy O(n) space version

Walk the list, copy values to an array, then two-pointer check:

```python
def isPalindrome(head):
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    l, r = 0, len(vals) - 1
    while l < r:
        if vals[l] != vals[r]:
            return False
        l += 1; r -= 1
    return True
```

O(n) time, O(n) space. **Correct but uses extra memory.**

The constant-space approach requires more cleverness.

---

## 3. The pivot — back half reversed = forward half (if palindrome)

If `1 → 2 → 3 → 2 → 1` is a palindrome, then:
- Front half: `1 → 2`.
- Back half: `2 → 1`. **Reversed:** `1 → 2`.

The reversed back half equals the front half. **That's the definition of a palindrome.**

So if we can:
1. Find the MIDDLE of the list.
2. REVERSE the back half (in place).
3. WALK the front half and the reversed back half in lockstep, comparing values.

If all comparisons match, palindrome. Else not.

> **Mini-refresher: why this works.**
>
> A palindrome reads the same backward as forward. Reversing the back half MAKES the back half READ THE SAME DIRECTION as the front half. So they should now match element-by-element.
>
> If not a palindrome, some position mismatches, and we return false.

Why is this O(1) space? Because reversing a linked list in place uses O(1) extra space (three pointers, see Reverse Linked List). Finding the middle uses O(1). Comparing uses O(1). Total: O(1).

---

## 4. The three-step plan

### Step 1: Find the middle (slow/fast pointer)

Use the slow/fast technique. When fast hits the end, slow is at the start of the back half (the second middle for even-length, the actual middle for odd-length).

For `1 → 2 → 2 → 1` (even, length 4): slow ends at index 2 (the second `2`).
For `1 → 2 → 3 → 2 → 1` (odd, length 5): slow ends at index 2 (the `3`).

### Step 2: Reverse from slow to end

Apply the three-pointer iterative reverse starting at `slow`. The original tail becomes the new head of this sub-list. Call this `rev`.

After:
- Front half (from `head`): unchanged in this region.
- Back half (from `rev`): reversed.

### Step 3: Walk and compare

Two pointers: `a = head`, `b = rev`. Walk both forward, compare values. Stop when one hits null.

If any mismatch: return false. If we get through: return true.

---

## 5. Code

**C++:**

```cpp
class Solution {
    ListNode* reverse(ListNode* head) {
        ListNode* prev = nullptr;
        ListNode* cur = head;
        while (cur) {
            ListNode* nxt = cur->next;
            cur->next = prev;
            prev = cur;
            cur = nxt;
        }
        return prev;
    }

public:
    bool isPalindrome(ListNode* head) {
        // Step 1: find middle
        ListNode* slow = head;
        ListNode* fast = head;
        while (fast && fast->next) {
            slow = slow->next;
            fast = fast->next->next;
        }

        // Step 2: reverse from slow to end
        ListNode* rev = reverse(slow);

        // Step 3: compare front with reversed back
        ListNode* a = head;
        ListNode* b = rev;
        while (b) {
            if (a->val != b->val) return false;
            a = a->next;
            b = b->next;
        }
        return true;
    }
};
```

**Python:**

```python
def isPalindrome(head):
    # Step 1: find middle
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next

    # Step 2: reverse second half
    prev = None
    cur = slow
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    rev = prev

    # Step 3: compare
    a, b = head, rev
    while b:
        if a.val != b.val:
            return False
        a = a.next
        b = b.next
    return True
```

Complexity: **O(n) time, O(1) space.**

---

## 6. Trace it on even and odd lengths

**Even: `1 → 2 → 2 → 1`.**

**Step 1: find middle.**

```
slow=1, fast=1.
Iter 1: slow=2, fast=2. (fast was 1→2; second move to its next-next: 2)

Wait, let me redo. fast was 1, fast.next was 2. fast.next.next is the second 2. So fast = second 2.

slow=2 (first 2), fast=2 (second 2).

Iter 2: fast=2 (second), fast.next=1, fast.next.next=null. enter? Yes (fast.next is 1, non-null).
  slow = 2 (second 2), fast = null.

Iter 3: fast=null → exit.

slow ended at second 2 (index 2).
```

**Step 2: reverse from slow (second 2) to end.**

Original tail: `2 → 1 → null`. Reversed: `1 → 2 → null`. `rev` = node previously holding 1.

**Step 3: compare.**

```
a = first 1. b = rev = 1.

Iter 1: a.val=1, b.val=1. Match. a = 2 (first 2). b = 2.
Iter 2: a.val=2, b.val=2. Match. a = ?. b = null.

Exit (b is null).
Return true.  ✓
```

**Odd: `1 → 2 → 3 → 2 → 1`.**

**Step 1: find middle.**

```
slow=1, fast=1.
Iter 1: slow=2, fast=3.
Iter 2: slow=3, fast=1 (last). fast.next=null → exit.

slow ended at 3 (the middle).
```

**Step 2: reverse from 3 to end.**

Original: `3 → 2 → 1 → null`. Reversed: `1 → 2 → 3 → null`. `rev` = node previously holding the last 1.

**Step 3: compare.**

```
a = first 1. b = rev = 1.

Iter 1: 1 == 1. Match. a = 2 (first), b = 2.
Iter 2: 2 == 2. Match. a = 3 (middle), b = 3 (originally middle, now still there).
Iter 3: 3 == 3. Match. a = ?, b = null.

Exit. Return true.  ✓
```

Notice the middle element (3) is compared TO ITSELF in iter 3. That's a self-match — always true — so no harm done. The "walk until b is null" handles odd-length cleanly without special casing.

---

## 7. Why "walk until one is null" handles both parities

After reversing the back half:
- For **even length** (n = 2k): front half has k nodes (indices 0..k-1); reversed back half has k nodes (originally indices k..2k-1). Both halves have the same length. Walking until one ends compares all k pairs.
- For **odd length** (n = 2k+1): front half has k nodes (indices 0..k-1); reversed back half has k+1 nodes (originally indices k..2k, with the middle included). The reversed back half is one longer. Walking until b ends compares all k+1 elements; the extra comparison is the middle vs itself.

Either way, the algorithm correctly verifies the palindrome property.

> **Mini-refresher: the loop condition matters more than you'd think.**
>
> `while a and b` — walks until the SHORTER one ends. For even: stops at the right time. For odd: stops one early, missing the middle's self-check. Still correct (middle's self-check is trivially true).
>
> `while b` (we use this) — walks until b ends. For even: same. For odd: includes the middle's self-check.
>
> Both work. We use `while b` since it's slightly clearer that we're walking the reversed half.

---

## 8. Common pitfalls

1. **Forgetting to reverse the back half.** Then you're just comparing front-to-front — meaningless.

2. **Reversing the WHOLE list.** Then you've destroyed the original; you have nothing to compare against. Reverse ONLY the back half.

3. **Wrong middle.** For palindrome check, you can use either the "first middle" or "second middle" convention — but the reverse logic must match. The standard slow/fast (using `while fast and fast.next`) lands slow at the second middle for even, the actual middle for odd. Reversing from THERE works in both cases.

4. **Using `<` instead of `<=` in comparisons by accident.** This is a value-comparison problem (palindrome check), not an index-comparison problem. Compare `a.val` and `b.val`, not pointers.

5. **Modifying the list and not restoring it.** Some interviewers expect the list to be restored after the check. To restore: re-reverse the back half. For LeetCode, restoration isn't tested.

6. **Trying to use recursion.** A recursive solution works (recurse to end, compare on the way back) but uses O(n) stack space — defeats the constant-space goal.

7. **Trying to compare pointers instead of values.** `a == b` checks pointer equality (same node). For palindrome, you want `a.val == b.val` (same value).

8. **Forgetting that single-node lists are palindromes.** `[1]` returns true. The standard algorithm handles this naturally: slow stays at the head, reversing a single node is the same node, comparing gives one match.

---

## 9. The shape — composition of primitives

This problem is **three classical primitives chained**:

1. **Slow/fast pointer** (from [`Middle_of_the_Linked_List.md`](./Middle_of_the_Linked_List.md)).
2. **Three-pointer reverse** (from [`Reverse_Linked_List.md`](./Reverse_Linked_List.md)).
3. **Two-pointer zip-walk** (from many problems).

Once you've internalized each primitive separately, composing them feels obvious.

**Pattern to internalize:**

> "Complex linked-list problems often decompose into chains of simpler primitives. When you see 'check property X about the WHOLE list with O(1) space,' think: can I split into halves, transform one half, and compare?"

Other examples of "compose primitives":

| Problem | Composed primitives |
|---|---|
| **This problem** | middle + reverse + walk |
| Reorder List (LC #143) | middle + reverse second half + zip |
| Sort Linked List (merge sort variant) | split at middle + recurse + merge |
| Odd Even Linked List | partition + reconnect |
| Add Two Numbers II | reverse + add (like Add Two Numbers I) + reverse result |

---

> **Self-check — the question to ask next time.**
>
> When a linked-list problem demands O(1) space for a property that "feels" two-sided (palindrome, reorder, reverse-then-add), ask:
>
> > **"Can I find the middle, reverse the back half, and then walk both halves in lockstep?"**
>
> If yes, you've reduced the problem to three known primitives.

---

## 10. Cross-references

- **Reference card (post-mastery):** [`../Palindrome_Linked_List.md`](../Palindrome_Linked_List.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Middle_of_the_Linked_List.md`](./Middle_of_the_Linked_List.md), [`Reverse_Linked_List.md`](./Reverse_Linked_List.md) — the primitives.
  - [`Merge_Two_Sorted_Lists.md`](./Merge_Two_Sorted_Lists.md) — different composition (sort via merge).
  - Coming next: [`Convert_Binary_Number_in_a_Linked_List_to_Integer.md`](./Convert_Binary_Number_in_a_Linked_List_to_Integer.md) — Horner's method.
