# Linked List Cycle II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Linked_List_Cycle_II.md`](../Linked_List_Cycle_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/linked-list-cycle-ii/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **This is Floyd's algorithm Phase 2 — the beautiful "reset and walk" trick.** The lesson: **after the slow/fast meeting, the distance from the meeting point BACK to the cycle start equals the distance from the head to the cycle start.** A piece of modular arithmetic with surprising power. **Read [`Linked_List_Cycle.md`](./Linked_List_Cycle.md) first** — Phase 1 is identical.

**Map of this file (10 short sections):**

1. Read the problem
2. Recap Phase 1
3. Setting up the math — μ and C
4. The key claim
5. Proof in 5 lines
6. The algorithm — Phase 1 + Phase 2
7. Code
8. Trace it on two examples
9. Common pitfalls
10. The shape — why this matters

---

## 1. Read the problem

Given the head of a linked list, return the node where the **cycle BEGINS** (the first node of the cycle). If no cycle, return `null`.

**Example:**

```
1 → 2 → 3 → 4 → 5 → 6
            ↑           ↓
            └────────────
```

Node 6's `next` is node 4. The CYCLE begins at node 4 (it's the first node you can return to). Return node 4.

If the list is acyclic, return `null`.

> **Mini-refresher: "where the cycle begins" — precisely.**
>
> The cycle begins at the **first node that has two predecessors**. In the example, node 4 has two predecessors: node 3 (the "tail of the lead-in") and node 6 (the "tail of the cycle"). It's the first such node walking from head.

---

## 2. Recap Phase 1

From Linked List Cycle I, we know how to DETECT a cycle:

```
slow = head, fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next
    if slow == fast:
        # cycle exists; slow == fast at some point INSIDE the cycle (the "meeting point")
        break
else:
    return null   # no cycle
```

At the meeting point, slow and fast point to the same node — call it `M`. The question now: how do we get from `M` to the cycle ENTRANCE?

---

## 3. Setting up the math — μ and C

Let's define some lengths:

- **μ** (mu) = number of nodes from `head` to the **cycle start**. (The "lead-in" length.)
- **C** = number of nodes in the cycle (its length).
- **x** = number of nodes from cycle start to the meeting point `M` (going forward in the cycle).

> **Mini-refresher: small example to anchor the variables.**
>
> ```
> 1 → 2 → 3 → 4 → 5 → 6
>             ↑           ↓
>             └────────────
> ```
>
> - μ = 3 (from head 1: walk through 1, 2, 3 to reach the cycle start at node 4).
>   Wait — let me be precise. μ = "number of EDGES from head to the cycle start", or equivalently "number of `.next` traversals." Some define it as the number of NODES BEFORE the cycle start. Let's say μ = number of `.next` steps from head to reach the cycle start. For the example: head → 1, 1→2, 2→3, 3→4. That's 3 steps. μ = 3.
> - C = 3 (the cycle is 4 → 5 → 6 → 4, so 3 nodes, 3 edges).
> - x = depends on where slow and fast meet (computed below).

---

## 4. The key claim

Floyd's elegant result:

> **The distance from the head to the cycle start (`μ`) EQUALS the distance from the meeting point M to the cycle start (going forward around the cycle).**

This is what makes Phase 2 work:
- Put a new pointer `walker` at `head`.
- Leave `slow` at `M` (the meeting point).
- Advance BOTH by 1 per iteration.
- They meet exactly at the **cycle start**.

Why? Because `walker` walks `μ` steps to reach the cycle start. `slow`, starting at `M`, also walks `μ` steps to reach the cycle start (per the claim). They arrive simultaneously.

---

## 5. Proof in 5 lines

When slow and fast meet at M:
- Slow has walked some distance `D_slow`. It's `μ + x` (lead-in + into the cycle by x).
- Fast has walked `D_fast = 2 · D_slow`.
- Fast has lapped slow `k` times around the cycle (some k ≥ 1).
- So `D_fast - D_slow = k · C`. Substituting: `(μ + x) = k · C`.

Rearranging: **`μ = k · C - x`** (mod C: `μ ≡ -x (mod C)`, equivalently `μ + x ≡ 0 (mod C)`).

Now consider walking forward `μ` more steps from M:
- `M` is at position `x` inside the cycle. After `μ` more steps, the new position (mod C) is `x + μ ≡ x + (kC - x) = kC ≡ 0` (the cycle start).

So `μ` steps from M lands EXACTLY at the cycle start. And `μ` steps from `head` lands at the cycle start by definition. Two pointers at the same speed starting from head and M reach the cycle start together. **QED.**

> **Mini-refresher: the takeaway from the math.**
>
> You don't need to remember the proof verbatim. You need to remember **the insight**: "from meeting point to cycle start = head to cycle start." That equality is what justifies the "reset and walk" trick.

---

## 6. The algorithm — Phase 1 + Phase 2

```
# Phase 1: detect cycle (Linked List Cycle I)
slow = head
fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next
    if slow == fast:
        break
else:
    return null     # no cycle

# At this point, slow == fast at meeting point M.

# Phase 2: find cycle start
walker = head
while walker != slow:
    walker = walker.next
    slow = slow.next
return walker
```

Two phases, both O(n). No extra space.

---

## 7. Code

**C++:**

```cpp
ListNode* detectCycle(ListNode* head) {
    ListNode* slow = head;
    ListNode* fast = head;

    // Phase 1
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) {
            // Phase 2
            ListNode* walker = head;
            while (walker != slow) {
                walker = walker->next;
                slow = slow->next;
            }
            return walker;
        }
    }

    return nullptr;  // no cycle
}
```

**Python:**

```python
def detectCycle(head):
    slow = head
    fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            walker = head
            while walker != slow:
                walker = walker.next
                slow = slow.next
            return walker
    return None
```

**JavaScript:**

```javascript
function detectCycle(head) {
    let slow = head, fast = head;
    while (fast && fast.next) {
        slow = slow.next;
        fast = fast.next.next;
        if (slow === fast) {
            let walker = head;
            while (walker !== slow) {
                walker = walker.next;
                slow = slow.next;
            }
            return walker;
        }
    }
    return null;
}
```

Complexity: **O(n) time, O(1) space.**

---

## 8. Trace it on two examples

**Example 1: cycle starts at the same position as the meeting point.**

List: `1 → 2 → 3 → 4 → 5 → 6 → (back to 4)`. μ = 3, C = 3.

**Phase 1:**

```
slow=1, fast=1.

Iter 1: slow=2, fast=3. Not equal.
Iter 2: slow=3, fast=5. Not equal.
Iter 3: slow=4, fast=4 (5→6→4). EQUAL. Meeting point M = node 4.
```

**Phase 2:**

```
walker=1, slow=4.

Iter 1: walker=2, slow=5.
Iter 2: walker=3, slow=6.
Iter 3: walker=4, slow=4. EQUAL. Return walker = node 4.  ✓
```

Cycle start = node 4. Correct.

**Example 2: meeting point ≠ cycle start.**

List: `A → B → C → D → E → (back to C)`. μ = 2 (head to C), C = 3 (cycle is C-D-E).

**Phase 1:**

```
slow=A, fast=A.

Iter 1: slow=B, fast=C.
Iter 2: slow=C, fast=E (C→D→E).
Iter 3: slow=D, fast=D (E→C→D). EQUAL. M = node D.
```

So slow and fast met at D, NOT at the cycle start C. Phase 2 will fix this.

**Phase 2:**

```
walker=A, slow=D.

Iter 1: walker=B, slow=E.
Iter 2: walker=C, slow=C (D→E→C; walker B→C). EQUAL. Return walker = C.  ✓
```

Cycle start = node C. Correct, even though M ≠ cycle start.

---

## 9. Common pitfalls

1. **Returning the meeting point M as the answer.** Wrong unless M happens to coincide with the cycle start. Always run Phase 2.

2. **Initializing `walker` from somewhere other than head.** Must be `head`. The whole math relies on head being μ steps from the cycle start.

3. **Advancing only `slow` or only `walker` in Phase 2.** Both must move at the same speed (1 step per iteration). They meet at the cycle start.

4. **Returning `null` from inside the Phase 2 loop.** Once cycle is detected (Phase 1 break), Phase 2 ALWAYS finds the cycle start — don't return null prematurely.

5. **Using a hashset.** Works (O(n) space), but Floyd's is O(1) and elegant. Know both.

6. **Forgetting to handle the "no cycle" case.** If Phase 1 completes without `slow == fast`, return `null`. The `while fast and fast.next` condition naturally handles this.

7. **Trying to reuse `fast` in Phase 2.** Don't — reset `walker` to `head` instead. (Some implementations use `fast` as the second pointer, advancing it from M. That works too because the variable name doesn't matter; just be consistent.)

8. **Misunderstanding the proof.** The result feels magical but it's just `D_fast = 2 · D_slow + (fast lapped k times)` → `μ + x = kC` → `μ = kC - x`. Walk through it once to feel it, then move on.

---

## 10. The shape — why this matters

The "reset and walk" technique extends beyond linked lists.

| Application | Variables |
|---|---|
| **This problem** | μ (lead-in length), C (cycle length), x (slow's offset into cycle) |
| Find the Duplicate Number (LC #287) | array as functional graph; cycle exists because of duplicate |
| Happy Number (LC #202) | iterated function; cycle detection answers "does it ever reach 1?" |
| Pollard's rho integer factoring | x → (x² + c) mod n; cycle in pseudo-random sequence reveals factor |
| Cycle entrance in any deterministic finite state machine | same algorithm |

**Pattern to internalize:**

> "Cycle entrance in unique-next-state structures = Floyd's Phase 1 (detect) + Phase 2 (head + meeting point, equal speed → meet at entrance). O(1) space. The why is: the lead-in length equals the in-cycle distance from meeting to entrance, by modular arithmetic on cycle length."

When you need to FIND the cycle entrance (not just detect), reach for Phase 2.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem about finding the start of a cycle (in a linked list, in an iterated function, in a state machine), ask:
>
> > **"Can I run Floyd's Phase 1 to detect + Phase 2 (reset one pointer to head, walk both at speed 1) to land at the cycle entrance? O(n) time, O(1) space, beautiful math."**
>
> If yes, you've got the canonical Floyd's solution.

---

## Cross-references

- **Reference card (post-mastery):** [`../Linked_List_Cycle_II.md`](../Linked_List_Cycle_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Linked_List_Cycle.md`](./Linked_List_Cycle.md) — Phase 1 only.
  - Coming next: [`Merge_Two_Sorted_Lists.md`](./Merge_Two_Sorted_Lists.md), [`Palindrome_Linked_List.md`](./Palindrome_Linked_List.md).
