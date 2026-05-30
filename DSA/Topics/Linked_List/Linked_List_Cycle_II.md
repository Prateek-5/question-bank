# Linked List Cycle II

**Problem Link:**
<a href="https://leetcode.com/problems/linked-list-cycle-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/linked-list-cycle-ii/</a>

**Topic:**
Linked List

----------------------------------------

## Step 1: Recap Linked List Cycle I

In **Linked List Cycle I**, we just asked: does the list have a cycle? The answer was Floyd's tortoise-and-hare: two pointers, slow moves 1 step per tick, fast moves 2. If there's a cycle, they'll meet. If fast hits null, no cycle.

Now we're asked something stronger: **where** does the cycle begin? That is, return the **first node** of the cycle.

Example:
```
1 → 2 → 3 → 4 → 5 → 6
            ↑           ↓
            └────────────
```
Node 4 is where the cycle starts (5 → 6 → 4 wraps back). Return node 4.

If no cycle, return null.

----------------------------------------

## Step 2: Warm-Up Analysis

Let me set up some variables.
- `μ` = distance from head to cycle start. ("mu")
- `λ` = length of the cycle. ("lambda")

Once slow enters the cycle, it moves at speed 1; fast moves at speed 2. Within the cycle, fast gains on slow by 1 step per tick. So they'll meet somewhere inside the cycle.

Where exactly do they meet? Let's trace. When slow enters the cycle (after μ steps), fast has also taken μ steps — but fast has moved 2μ cells, which means fast is μ cells into the cycle (after the cycle start), assuming μ ≥ λ (otherwise fast wrapped around).

In general, inside the cycle, fast is "some offset ahead" of slow. They meet when fast catches up.

Here's the elegant result:

**Claim:** when slow and fast first meet inside the cycle, the distance from the meeting point going *forward* back to the cycle start equals μ (the distance from head to cycle start).

This is Floyd's famous insight.

----------------------------------------

## Step 3: Proof of the Claim

Let `m` = the point where slow and fast meet.
- Distance slow has walked: μ + x, where x is slow's position from the cycle start (0 ≤ x < λ).
- Distance fast has walked: 2(μ + x).

The difference must be a whole number of cycle lengths (since fast has lapped slow some number of times inside the cycle):
```
2(μ + x) - (μ + x) = k·λ
μ + x = k·λ
μ = k·λ - x
```

Now consider starting two new walkers:
- One from head.
- One from the meeting point `m`.

Both move 1 step per tick. After some steps, they should meet at the cycle start.

How many steps until they meet?
- Walker from head reaches cycle start in exactly μ steps.
- Walker from m: m is x cells into the cycle. To return to cycle start, it must walk λ - x cells forward around the cycle, then nothing more (once it reaches cycle start, it stops or both continue same direction). Actually, the walker from m keeps going; after μ steps, it's at position `m + μ` (inside the cycle, positions wrap mod λ). That's `x + μ = x + k·λ - x = k·λ ≡ 0 (mod λ)` — the cycle start.

So both walkers meet at the cycle start after μ steps.

**Algorithm:** after slow and fast meet at m, place a new pointer at head. Move both at speed 1. They meet at the cycle start.

----------------------------------------

## Step 4: The Complete Algorithm

```
# Phase 1: detect cycle with Floyd's
slow = head, fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next
    if slow == fast:
        break
else:
    return null  # no cycle

# Phase 2: find cycle start
walker = head
while walker != slow:
    walker = walker.next
    slow = slow.next
return walker
```

Clean. The "else" after while is Python-ish — in C++ we'd use a flag or break-else structure. Below is the clean C++ version.

----------------------------------------

## Step 5: Trace on the Example

List: `1 → 2 → 3 → 4 → 5 → 6 → 4 (cycle back)`.
μ = 3 (from head 1 to cycle start 4). λ = 3 (cycle length: 4, 5, 6).

**Phase 1:**
```
slow=1, fast=1.
Iter 1: slow=2, fast=3.
Iter 2: slow=3, fast=5.
Iter 3: slow=4, fast=4 (fast jumped 6→4). They meet at node 4!
```

Wait, slow ends at 4 and fast ends at 4 at iter 3? Let me re-trace.

Actually iter 3:
- slow was at 3, moves to 4.
- fast was at 5, moves to 6 then to 4.
- They're both at 4. ✓

The meeting point m is node 4 (which happens to be the cycle start in this particular case).

**Phase 2:**
```
walker=1, slow=4.
Iter 1: walker=2, slow=5.
Iter 2: walker=3, slow=6.
Iter 3: walker=4, slow=4. Match! Return 4.
```

Great — they meet at the cycle start (node 4). ✓

In this example Phase 1's meeting point happened to coincide with the cycle start (because μ = λ). In general they won't coincide, but Phase 2 still finds the cycle start in exactly μ steps.

----------------------------------------

## Step 6: A Different Example Where Meeting ≠ Cycle Start

List: `A → B → C → D → E → C` (cycle starts at C, cycle is C-D-E).
μ = 2 (A, B before cycle). λ = 3.

```
slow=A, fast=A.
Iter 1: slow=B, fast=C.
Iter 2: slow=C, fast=E.
Iter 3: slow=D, fast=D. Meet at D!
```

Meeting point m = D. Now Phase 2:
```
walker=A, slow=D.
Iter 1: walker=B, slow=E.
Iter 2: walker=C, slow=C. Match. Return C.
```

Correct — cycle starts at C. The meeting point D is different from the cycle start C, but Phase 2's math lands us at the right place.

----------------------------------------

## Step 7: Why This Works Intuitively

The elegant observation: the distance from head to cycle start (μ) equals the distance from meeting point to cycle start (traversing forward through the cycle).

So starting simultaneous walkers — one from head, one from meeting point — both reach the cycle start after μ steps.

It's one of those cute results where a bit of modular-arithmetic insight gives an O(1)-memory algorithm for a problem that looks like it needs a hashset.

Without Floyd's: you could hash all visited nodes and return the first repeat. O(n) time and space. Floyd's gives O(1) space.

----------------------------------------

## Step 8: Name It

This is **Floyd's tortoise-and-hare cycle detection, phase 2**. Sometimes called **"Floyd's cycle-finding algorithm"** in full.

Same technique detects cycles in:
- Linked lists (this problem).
- Iterated functions (e.g., Pollard's rho algorithm for factoring integers).
- State-space graphs where each state has exactly one "next."

Brent's algorithm is a close cousin, sometimes faster in practice.

----------------------------------------

## Step 9: Complexity

Time: Phase 1 is O(μ + λ). Phase 2 is O(μ). Total **O(n)**.
Space: **O(1)** — two pointers throughout.

No hashset needed.

----------------------------------------

## Step 10: C++ Implementation

```cpp
ListNode* detectCycle(ListNode* head) {
    ListNode* slow = head;
    ListNode* fast = head;

    // Phase 1: find meeting point (or no cycle).
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) {
            // Phase 2: walk from head and meeting point at equal speed.
            ListNode* walker = head;
            while (walker != slow) {
                walker = walker->next;
                slow = slow->next;
            }
            return walker;
        }
    }

    return nullptr;   // no cycle
}
```

Compact. The `while (fast && fast->next)` guards against fast dereferencing null in the no-cycle case.

One small gotcha: I reuse the variable `slow` in Phase 2 after we've found the meet point. Some prefer renaming for clarity:
```cpp
ListNode* meet = slow;     // clearer
ListNode* walker = head;
while (walker != meet) { walker = walker->next; meet = meet->next; }
return walker;
```

Semantically identical.

----------------------------------------

## Step 11: Follow-up Questions

- **Cycle length.** Once phase 1 finds the meeting point, fix one pointer and walk the other forward until they meet again — that's the cycle length.
- **Remove the cycle.** Find the cycle start; walk around the cycle to find the node whose `next` is the cycle start; set its next to null.
- **Cycle in a graph (not just linked list).** Use DFS with three-color marking, or union-find for undirected.
- **Why does Floyd's "phase 2" use head + meeting point, not head + cycle start directly?** Because we don't yet *know* the cycle start — the meeting point is the only cycle-interior node we've identified. Floyd's math bridges from meeting point to cycle start.
- **Brent's algorithm comparison.** Brent's uses less *expected* time in practice by doubling the "teleport distance" of the fast pointer.
