# Minimum Jumps to Reach Home — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Minimum_Jumps_to_Reach_Home.md`](../Minimum_Jumps_to_Reach_Home.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/minimum-jumps-to-reach-home/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: BFS over states `(position, last_was_backward)`. Min jumps + unit edge cost = BFS. The "last_was_backward" flag is essential because consecutive back-jumps are forbidden.**

**Map of this file (8 sections):**

1. Read the problem
2. Why state = (position, last_was_backward)
3. The bounded search space
4. BFS algorithm
5. Code
6. Trace it
7. Common pitfalls
8. The shape — BFS with auxiliary state

---

## 1. Read the problem

A bug starts at position 0 on a number line. It wants to reach position `x` (home). Each move:
- **Forward** `a` units — always allowed.
- **Backward** `b` units — allowed ONLY if the previous move was NOT also backward.

`forbidden[]` lists positions the bug can NEVER land on. Positions must be ≥ 0.

Return min jumps to reach x, or -1 if impossible.

**Example:** `forbidden=[14,4,18,1,15], a=3, b=15, x=9` → 0→3→6→9 = **3** jumps.

---

## 2. Why state = (position, last_was_backward)

> **Mini-refresher: the future legal moves depend on the LAST move's type.**
>
> If the last jump was backward, the NEXT jump CAN'T be backward — forward only.
> If the last jump was forward (or it's the first move), both directions are open.
>
> So the minimal state is `(position, last_was_backward)`. Without the flag, you can't decide which moves are legal.

---

## 3. The bounded search space

> **Mini-refresher: positions are theoretically infinite — we need a SAFE UPPER BOUND.**
>
> Going forward indefinitely doesn't help (we'd overshoot x and never come back). The constraint "no two backwards in a row" limits how much we can backtrack from far positions.
>
> A safe upper limit (for LeetCode constraints): **L = 6000** (or compute tighter analytically).

Without this bound, BFS could explore unboundedly.

---

## 4. BFS algorithm

```
forbiddenSet = set(forbidden)
visited = {(0, false)}
queue = [(0, false, jumps=0)]

while queue:
    (p, back, j) = pop front
    if p == x: return j
    # Forward:
    next_p = p + a
    if 0 <= next_p <= L and next_p ∉ forbidden and (next_p, false) ∉ visited:
        enqueue (next_p, false, j+1)
    # Backward (only if last was NOT backward):
    if not back:
        prev_p = p - b
        if 0 <= prev_p and prev_p ∉ forbidden and (prev_p, true) ∉ visited:
            enqueue (prev_p, true, j+1)

return -1
```

BFS guarantees the FIRST time we dequeue `(x, *)`, the jumps count is the minimum.

---

## 5. Code

**C++:**

```cpp
int minimumJumps(vector<int>& forbidden, int a, int b, int x) {
    unordered_set<int> bad(forbidden.begin(), forbidden.end());
    const int LIMIT = 6000;
    unordered_set<int> visited;
    visited.insert(0);   // (0, false) encoded as position*2 + 0

    queue<tuple<int, bool, int>> q;
    q.push({0, false, 0});

    while (!q.empty()) {
        auto [p, back, j] = q.front(); q.pop();
        if (p == x) return j;

        int fp = p + a;
        if (fp <= LIMIT && !bad.count(fp)) {
            int key = fp * 2;
            if (!visited.count(key)) {
                visited.insert(key);
                q.push({fp, false, j + 1});
            }
        }
        if (!back) {
            int bp = p - b;
            if (bp >= 0 && !bad.count(bp)) {
                int key = bp * 2 + 1;
                if (!visited.count(key)) {
                    visited.insert(key);
                    q.push({bp, true, j + 1});
                }
            }
        }
    }
    return -1;
}
```

Complexity: **O(L)** time (each state visited at most once), O(L) space.

---

## 6. Trace it

`forbidden = {14, 4, 18, 1, 15}, a=3, b=15, x=9`.

```
Init: visited = {(0, F)}. queue = [(0, F, 0)].

Pop (0, F, 0). p=0, not x.
  Forward to 3: not forbidden, unvisited. Enqueue (3, F, 1).
  Backward to -15: invalid. Skip.

Pop (3, F, 1). 
  Forward to 6: OK. Enqueue (6, F, 2).
  Backward to -12: invalid.

Pop (6, F, 2).
  Forward to 9: OK. Enqueue (9, F, 3).
  Backward: invalid.

Pop (9, F, 3). p == x. Return 3.  ✓
```

---

## 7. Common pitfalls

1. **State = position only.** Misses the "consecutive backward" rule.
2. **Unbounded upper limit.** BFS may explore forever; use L = 6000 (or a derived tighter bound).
3. **Allowing backward from a backward.** Carefully enforce `if not back`.
4. **Forgetting positions can't be negative.** Skip backward jumps that go below 0.
5. **Treating x itself as forbidden.** Problem allows x to be reached even if it would otherwise be unusual; trust the forbidden list and don't add x to it.
6. **Using DFS.** Wouldn't give minimum jumps — BFS is required.

---

## 8. The shape — BFS with auxiliary state

The pattern: **min-jumps / min-moves problem with state-dependent move rules → BFS on EXPANDED state.**

| Problem | Auxiliary state |
|---|---|
| **This problem** | last move was backward? |
| Open the Lock | none (state is just the code) |
| Snakes and Ladders | none (state is just position) |
| Race Car | speed sign |
| Sliding Puzzle | board configuration |
| Jump Game III | none (just position) |

**Pattern to internalize:**

> "Min jumps + state-dependent rules → BFS, augment state with relevant history flags. Unit edge cost → BFS gives shortest. Bound the state space to terminate."

---

> **Self-check — the question to ask next time.**
>
> When move rules depend on the previous move:
>
> > **"BFS with state = (position, recent-history flag). Bound position. First time we pop target = min jumps."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Minimum_Jumps_to_Reach_Home.md`](../Minimum_Jumps_to_Reach_Home.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Frog_Jump.md`](./Frog_Jump.md), [`Open_the_Lock.md`](../../Sorting_Divide_and_Conquer/learn/Open_the_Lock.md).
  - Coming next: [`Matrix_Chain_Multiplication.md`](./Matrix_Chain_Multiplication.md), [`Unique_Binary_Search_Trees.md`](./Unique_Binary_Search_Trees.md).
