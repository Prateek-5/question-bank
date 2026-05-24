# Linked List Cycle — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Linked_List_Cycle.md`](../Linked_List_Cycle.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/linked-list-cycle/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **This is Floyd's tortoise-and-hare algorithm.** The lesson: **two pointers moving at different speeds on a CYCLIC structure WILL meet.** The "why" is short modular arithmetic. **Read [`Middle_of_the_Linked_List.md`](./Middle_of_the_Linked_List.md) first** — slow/fast for finding the middle is the warmup; this is the same pointers used for a completely different goal.

**Map of this file (10 short sections):**

1. Read the problem
2. The hashset approach (and why we want better)
3. The thought experiment — runners on a track
4. Why fast WILL catch slow inside the cycle
5. The exact loop condition
6. Code
7. Trace cyclic and acyclic
8. Edge cases
9. Common pitfalls
10. The shape — cycle detection beyond linked lists

---

## 1. Read the problem

Given the head of a singly-linked list, return `true` if the list has a **cycle** in it; otherwise return `false`.

A cycle exists if some node in the list can be reached again by continuously following the `next` pointer. Internally, the cycle is described by a `pos` parameter (the index where the tail's `next` points back to). But your function doesn't see `pos` — you just have the head.

**Examples:**

- `1 → 2 → 3 → 4 → null` → no cycle. Return `false`.
- `3 → 2 → 0 → -4 → (back to 2)` (the `-4` node's `next` points to the `2` node) → cycle. Return `true`.
- `1 → 1` (single node pointing to itself) → cycle. Return `true`.
- `null` → no cycle. Return `false`.

> **Mini-refresher: what a "cycle" looks like in memory.**
>
> ```
> 1 → 2 → 3 → 4 → 5 → 6
>             ↑           ↓
>             └─────────────
> ```
>
> Node 6's `next` doesn't point to `null` — it points back to node 3. So walking the list, you go `1 → 2 → 3 → 4 → 5 → 6 → 3 → 4 → 5 → 6 → ...` forever.
>
> Detecting this in code is non-trivial because following `.next` blindly never terminates.

---

## 2. The hashset approach (and why we want better)

Walk the list, remembering every node you've visited. If you re-visit a node — cycle. If you reach `null` — no cycle.

```
seen = empty set
while head != null:
    if head in seen:
        return true
    seen.add(head)
    head = head.next
return false
```

Time: **O(n)**. Space: **O(n)** (the hashset).

Works. But the space cost bothers us — storing potentially millions of pointers to answer a yes/no question. Can we do better?

> **Mini-refresher: when constant-space alternatives matter.**
>
> For small inputs, the hashset is fine. But interviewers often probe: "Can you do it in O(1) space?" The answer here is yes — Floyd's algorithm. The insight (two pointers at different speeds) is more important than the space saving.

---

## 3. The thought experiment — runners on a track

Imagine a running track. Two runners start at the same point:
- **Slow** runs at 1 lap-unit per second.
- **Fast** runs at 2 lap-units per second.

On a STRAIGHT track (no cycle), Fast simply pulls ahead and reaches the end first.

On a CIRCULAR track (cycle), Fast keeps gaining 1 lap-unit per second on Slow. Eventually Fast LAPS Slow — they end up at the same point.

Mapping to linked lists:
- Straight track = acyclic list. Fast hits `null` first.
- Circular track (or partial-circular: a non-cyclic prefix leading INTO a cycle) = list with cycle. Fast eventually catches Slow.

**Implementation:** two pointers from head. Slow advances 1 node per iteration; Fast advances 2. If they meet (point to the same node), there's a cycle. If Fast hits null, no cycle.

---

## 4. Why fast WILL catch slow inside the cycle

> **Mini-refresher: the modular-arithmetic argument.**
>
> Suppose the cycle has length `C`. Once both pointers are inside the cycle, measure their positions MODULO C.
>
> - Slow's position advances by 1 (mod C) per iteration.
> - Fast's position advances by 2 (mod C) per iteration.
> - The GAP (fast - slow) (mod C) advances by `2 - 1 = 1` per iteration.
>
> Starting with some initial gap `d` (when slow first enters the cycle), the gap takes values `d, d+1, d+2, ..., d+C-1` mod C — cycling through every residue. At some point the gap hits 0, meaning fast caught slow.
>
> So within at most `C` iterations after slow enters the cycle, they MUST meet. Not "probably" — guaranteed by basic modular arithmetic.

If there's no cycle, the argument doesn't apply (fast just falls off the end). The loop terminates when `fast` or `fast.next` is null.

---

## 5. The exact loop condition

Fast advances 2 steps per iteration: `fast = fast.next.next`. For this to be safe (no null dereference):

- `fast` must be non-null (to do `fast.next`).
- `fast.next` must be non-null (to do `(fast.next).next`).

So the loop condition: `while fast != null and fast.next != null`.

Inside the loop:
- `slow = slow.next`
- `fast = fast.next.next`
- Check `slow == fast` → cycle found.

If the loop EXITS (fast becomes null or fast.next becomes null) before finding a match, no cycle.

> **Mini-refresher: same loop condition as "find the middle."**
>
> The slow/fast structure is identical to Middle of the Linked List. The DIFFERENCE is what we check:
> - Middle: check nothing special; loop until fast hits the end. Slow is the middle.
> - Cycle detection: check `slow == fast` each iteration. If they meet, cycle. Else loop until fast hits end.
>
> Same machinery, different question.

---

## 6. Code

**C++:**

```cpp
bool hasCycle(ListNode* head) {
    ListNode* slow = head;
    ListNode* fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return true;
    }
    return false;
}
```

**Python:**

```python
def hasCycle(head):
    slow = head
    fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False
```

**JavaScript:**

```javascript
function hasCycle(head) {
    let slow = head;
    let fast = head;
    while (fast && fast.next) {
        slow = slow.next;
        fast = fast.next.next;
        if (slow === fast) return true;
    }
    return false;
}
```

Complexity: **O(n) time, O(1) space.**

---

## 7. Trace cyclic and acyclic

**Cyclic example:** `3 → 2 → 0 → -4 → (back to 2)`. Label nodes A=3, B=2, C=0, D=-4. Cycle: B → C → D → B.

```
Initial: slow = A, fast = A.

Iter 1: slow = B, fast = C. Not equal.
Iter 2: slow = C, fast = B (D → B). Not equal.
Iter 3: slow = D, fast = D (B → C → D). EQUAL. Return true.  ✓
```

**Acyclic example:** `1 → 2 → 3 → null`.

```
Initial: slow = 1, fast = 1.

Check: fast=1, fast.next=2 → enter.
  slow = 2, fast = 3.
Check: fast=3, fast.next=null → EXIT.

Return false.  ✓
```

The acyclic case terminates because Fast hits the end.

---

## 8. Edge cases

- **Empty list (`head = null`):** Loop doesn't enter (`fast = null`). Return false. ✓
- **Single node, no cycle (`1 → null`):** Loop doesn't enter (`fast.next = null`). Return false. ✓
- **Single node with self-loop (`1.next = 1`):** 
  - `fast = 1, fast.next = 1` → both non-null, enter loop.
  - `slow = 1, fast = 1`. EQUAL. Return true. ✓
- **Two-node cycle (`A → B → A`):**
  - Iter 1: `slow = B, fast = A` (A→B→A). Not equal.
  - Iter 2: `slow = A, fast = A`. EQUAL. Return true. ✓

All four edge cases handled by the standard code with no extra branches.

---

## 9. Common pitfalls

1. **Wrong loop condition.** `while fast != null` alone crashes on `fast.next.next` when `fast.next` is null. Always check BOTH.

2. **Checking equality BEFORE advancing.** Then on the very first iteration, `slow == fast = head` always — return true even when there's no cycle. Advance FIRST, then check.

3. **Initializing slow and fast differently.** Some implementations start `fast = head.next`. This works (with a slight loop-condition tweak) but is non-canonical. The standard form starts both at `head`.

4. **Using the hashset when O(1) is requested.** Hashset is fine for correctness but not for the "constant space" version. Know both.

5. **Trying to detect cycles by counting iterations.** "If I've walked n+1 steps, must be a cycle." Works in principle but you'd need to know `n` first — i.e., you'd need to traverse. Pointless.

6. **Returning `slow` or `fast` instead of `true`/`false`.** This problem asks for a boolean. Don't return the node.

7. **Forgetting that the meeting point in a cycle is NOT necessarily the cycle ENTRANCE.** That's Linked List Cycle II's problem (next file). For THIS problem, we only need to know if there's a cycle at all.

---

## 10. The shape — cycle detection beyond linked lists

Floyd's algorithm extends to ANY structure where each state has a UNIQUE NEXT STATE:

| Domain | "next state" |
|---|---|
| **This problem** | `node.next` |
| Iterated function detection | `x → f(x)` |
| Pollard's rho (integer factoring) | `x → (x² + c) mod n` |
| Cycle detection in pseudo-random number generators | `seed → next_seed` |
| Finding cycles in functional graph traversal | each node has exactly one outgoing edge |
| Happy Number (LC #202) | `n → sum of digit squares of n` |
| Find the Duplicate Number (LC #287) | treat array as function: `i → nums[i]` |

**Pattern to internalize:**

> "If a structure has UNIQUE outgoing transitions (each state goes to exactly one next state), two iterators at different speeds will MEET if and only if a cycle exists. O(1) space."

The recognition cue: any "iterated function" or "unique-next-pointer" problem. Floyd's applies.

---

> **Self-check — the question to ask next time.**
>
> When you face cycle detection in any structure with unique next-transitions, ask:
>
> > **"Can I run two pointers at different speeds — slow at 1, fast at 2? If they meet, there's a cycle; if fast hits the end, there isn't."**
>
> If yes, you've solved cycle detection in O(1) space.

---

## Cross-references

- **Reference card (post-mastery):** [`../Linked_List_Cycle.md`](../Linked_List_Cycle.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Middle_of_the_Linked_List.md`](./Middle_of_the_Linked_List.md) — same machinery, different question.
  - Coming next: [`Linked_List_Cycle_II.md`](./Linked_List_Cycle_II.md) — FIND the cycle entrance, not just detect.
