# Palindrome Linked List

**Problem Link:**
<a href="https://leetcode.com/problems/palindrome-linked-list/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/palindrome-linked-list/</a>

**Topic:**
Linked List

----------------------------------------

## Step 1: State the Question

Given the head of a singly linked list, return true if it reads the same forward and backward (a palindrome), false otherwise.

Examples:
- `1 → 2 → 2 → 1`: palindrome. True.
- `1 → 2`: not palindrome. False.
- `1`: trivially palindrome (single element). True.

The challenge: the problem often asks for **O(n) time and O(1) space**. For arrays this is easy — two pointers. For linked lists, it's trickier because we don't have backward access.

----------------------------------------

## Step 2: Naïve Approaches

**Approach A: Copy to an array, then two-pointer.** O(n) time, O(n) space. Simple:
```cpp
vector<int> v;
while (head) { v.push_back(head->val); head = head->next; }
int l = 0, r = v.size() - 1;
while (l < r) {
    if (v[l] != v[r]) return false;
    l++; r--;
}
return true;
```

**Approach B: Push values onto a stack during first pass, then compare.** Same O(n) memory.

Both work. They fail the "constant space" target.

How do we check a palindrome with O(1) memory when we can only traverse forward? The key is that the back half of a palindrome is the **reverse** of the front half. So if we could somehow walk backward through the back half while walking forward through the front, we'd compare them in O(1) extra memory.

And **reversing a linked list in place** is something we can do easily. That's the clue.

----------------------------------------

## Step 3: Plan — Reverse Half, Then Compare

Three steps:
1. **Find the middle** of the list (slow/fast pointer).
2. **Reverse the second half** in place.
3. **Compare front half with reversed back half**, walking both forward.

If they match all the way through, palindrome. Otherwise, not.

Optional: at the end, reverse the second half again to restore the list — respectful to callers.

----------------------------------------

## Step 4: Let's Walk Through Each Step

**Step 1: Find the middle.**
Slow/fast pointer trick: slow moves 1, fast moves 2. When fast hits the end, slow is at the middle.

For odd length `1 → 2 → 3 → 4 → 5`, slow ends at 3.
For even length `1 → 2 → 3 → 4`, slow ends at 3 (the later of the two middles). The "back half" starts at slow in both cases.

**Step 2: Reverse from slow to end.**
Standard in-place linked-list reversal. At the end of this, the original "slow" now leads a list that reads the original back half **in reverse**.

**Step 3: Compare.**
Have two pointers: one starting at the original head, one starting at the reversed second half's new head. Walk both forward, comparing values. If any mismatch, return false. If we finish (one hits null first), return true.

Note: for odd-length lists, the middle value is shared — we don't need to compare it. Walking until one pointer is null handles this naturally.

----------------------------------------

## Step 5: Trace on `1 → 2 → 2 → 1`

**Step 1: Find middle.**
- slow=1, fast=1.
- Move: slow=2, fast=2.
- Move: slow=2 (second), fast=1 (last). fast.next = null, stop.
- slow ends at the second '2' (index 2).

**Step 2: Reverse from slow to end.**
Reverse `2 → 1` → `1 → 2 → null`. Now the list looks (conceptually) like:
```
1 → 2 → 2      (front half, unchanged)
1 → 2          (reversed back half, starting at where slow was)
```

Actually the in-place reversal *does* modify pointers throughout, so the original list no longer exists as before. But the two chains — front from `head` and back from the reversed-slow — are what we walk.

**Step 3: Compare.**
- head=1, revHead=1. Match.
- next: 2, 2. Match.
- next: 2 (third node of original, which is the start of reversed chain). Wait, I'm getting tangled.

Let me redo this more carefully. For `1 → 2 → 2 → 1`:

Slow ends at node 3 (the second '2', 0-indexed from head).
Reverse starting from slow: originally `2 → 1`, reversed to `1 → 2`. New head of the reversed half is the old last node (value 1).

Now walk:
- `head` points to 1 (first node).
- `revHead` points to 1 (originally the last node).
- Compare 1 == 1. ✓ Move both forward.
- head.next = 2. revHead.next = 2. Compare 2 == 2. ✓ Move both.
- head.next = 2. revHead.next = null. Loop exits (one pointer is null).
- Return true.

Palindrome confirmed. ✓

For `1 → 2 → 3 → 2`: slow ends at node 3 (the '3'), back half "3 → 2" reversed to "2 → 3". Walk: 1 vs 2. Mismatch. Return false. Correct — not a palindrome.

For odd `1 → 2 → 1`: slow ends at node 2 (the middle '2'). Back half "2 → 1" reversed to "1 → 2". Walk: head=1 vs revHead=1. Match. Move to 2 vs 2. Match. Move; head=1, revHead=null (since reversed back had only 2 nodes). Exit. Return true. ✓

----------------------------------------

## Step 6: Why Stop When One Pointer Is Null

After reversal, the front half (head to slow-1) and the back half (slow to end, now reversed) may have different lengths by 1 (for odd-length lists, the middle belongs to the back half). That's fine — we compare up to the shorter length, which is the back half for even lists and the back half minus one for odd.

The middle element in odd-length lists pairs with itself — always a match — so we effectively skip comparing it. This falls out naturally from "walk until one null."

----------------------------------------

## Step 7: Name the Technique

This uses three classic linked-list tricks combined:
1. **Slow/fast pointer** for finding the middle.
2. **In-place linked-list reversal.**
3. **Two-pointer comparison** walking forward.

Each is a building block from basic linked-list problems. Putting them together solves this in O(n) time, O(1) space.

The real skill: recognizing that "back half reversed" is the structure that lets us compare without recording anything.

----------------------------------------

## Step 8: Complexity

Time: O(n) — each phase (find middle, reverse, compare) is O(n/2) = O(n).
Space: O(1) — we rewire pointers in place; no auxiliary structures.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class Solution {
    ListNode* reverse(ListNode* head) {
        ListNode* prev = nullptr;
        while (head) {
            ListNode* next = head->next;
            head->next = prev;
            prev = head;
            head = next;
        }
        return prev;
    }

public:
    bool isPalindrome(ListNode* head) {
        // Step 1: find middle (slow ends at start of back half)
        ListNode* slow = head;
        ListNode* fast = head;
        while (fast && fast->next) {
            slow = slow->next;
            fast = fast->next->next;
        }

        // Step 2: reverse the back half starting at slow
        ListNode* rev = reverse(slow);

        // Step 3: compare front with reversed back
        ListNode* a = head;
        ListNode* b = rev;
        bool palindrome = true;
        while (b) {   // back half is the shorter or equal; stop when we finish it
            if (a->val != b->val) { palindrome = false; break; }
            a = a->next;
            b = b->next;
        }

        // Optional: restore the list by reversing back (not required for correctness)

        return palindrome;
    }
};
```

A few details:
- We walk `while (b)` — the reversed back half is the shorter one (for odd-length lists). Stopping there compares all meaningful pairs.
- We could restore the list by re-reversing; omitted here since most interview problems don't test for it.

----------------------------------------

## Step 10: Follow-up Questions

- **Doubly-linked list palindrome check.** Two pointers at both ends, walk inward. No reversal needed.
- **Circular linked list palindrome check.** First detect and break the cycle; then apply this algorithm.
- **Can you check without modifying the list at all?** Yes, but O(n) extra memory (copy values or use recursion).
- **Recursive O(n) space solution.** Elegant: recurse to the end (effectively reversing via the call stack), then compare upward. Uses O(n) stack.
- **Time complexity of the "copy and two-pointer" approach vs this one.** Both O(n) time, but constants differ — array indexing is fast, pointer chasing slower.
- **What if the list has cycles?** Slow/fast finds the cycle meet point, not a middle. You'd handle cycles separately; for this problem, input is assumed acyclic.


---

## Interview Signals (from LeetLens)

This problem (or close variants) was reported in **2 real interview(s)** in the LeetLens dataset (snapshot 2026-05-31). Pay attention to the company context when practicing.

| Company | Difficulty | LeetLens ID | Match | Variant note |
|---|---|---|---|---|
| Google | Medium | `0713e877` | 1.00 (exact-title) | Palindrome Linked List (2nd) |
| Google | Medium | `ce1035ef` | 1.00 (exact-title) | Palindrome Linked List |

_Source: LeetLens DB. Match methods: `substring` = direct hit; `token-coverage` = ≥70% of this card's filename tokens appear in the question; `jaccard`/`ratio` = fuzzy title similarity._
_See the parent folder's `EXTRACTED_QUESTIONS.md` §2 for the full list of incorporated questions._
