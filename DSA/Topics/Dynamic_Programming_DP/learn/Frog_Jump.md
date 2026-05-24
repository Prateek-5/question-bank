# Frog Jump — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Frog_Jump.md`](../Frog_Jump.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/frog-jump/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: state = (stone position, last jump size). The "last jump" must be part of the state because it constrains the next jumps to k-1, k, or k+1. DP via a hashmap of reachable jumps per stone.**

**Map of this file (8 sections):**

1. Read the problem
2. Why "last jump" must be in the state
3. The reachable-jumps map
4. Forward propagation algorithm
5. Code
6. Trace it
7. Common pitfalls
8. The shape — DP with auxiliary state

---

## 1. Read the problem

A frog starts at position 0 (the first stone). Stones are at sorted positions in `stones[]`. The frog wants to reach the LAST stone. From a stone, if the LAST JUMP was of size `k`, the NEXT JUMP can be `k-1`, `k`, or `k+1` (must be ≥ 1). The FIRST jump must be size 1. The frog must land EXACTLY on a stone (no swimming).

Return true if the frog can reach the last stone.

**Example:** `stones = [0, 1, 3, 5, 6, 8, 12, 17]` → **true**.

---

## 2. Why "last jump" must be in the state

> **Mini-refresher: the future depends on the last jump size.**
>
> From a stone alone, you can't decide what jumps are next legal. The constraint is k ± 1 around the LAST jump.
>
> So the minimal state is `(stone_position, last_jump_size)`. With this, the future is fully determined; without `last_jump_size`, it's not.

This pattern — adding state for "history that affects the future" — is essential in DP.

---

## 3. The reachable-jumps map

> **Mini-refresher: for each stone, track which jump-sizes can ARRIVE here.**
>
> `rj[pos]` = set of last-jump sizes that successfully reach stone at position `pos`.
>
> Initialize `rj[0] = {0}` (frog starts at 0; conceptually "no previous jump" → represented as 0). The first jump from 0 will be size 1 (0+1).

If `rj[lastStone]` is non-empty at the end, the frog can reach it.

---

## 4. Forward propagation algorithm

For each stone in sorted order, for each known last-jump-size k that reaches it:
- Try jumps k-1, k, k+1.
- For each valid next jump (≥ 1), compute the landing position.
- If the landing is a stone, ADD the jump size to that stone's `rj`.

```
stoneSet = set of stones
rj = {pos: empty set for pos in stones}
rj[0] = {0}

for pos in stones (in order):
    for k in rj[pos]:
        for delta in {-1, 0, 1}:
            next_k = k + delta
            if next_k <= 0: continue
            next_pos = pos + next_k
            if next_pos in stoneSet:
                rj[next_pos].add(next_k)

return rj[stones[-1]] is non-empty
```

---

## 5. Code

**C++:**

```cpp
bool canCross(vector<int>& stones) {
    unordered_set<int> stoneSet(stones.begin(), stones.end());
    unordered_map<int, unordered_set<int>> rj;
    for (int s : stones) rj[s] = {};
    rj[0] = {0};

    for (int pos : stones) {
        vector<int> jumps(rj[pos].begin(), rj[pos].end());
        for (int k : jumps) {
            for (int next_k : {k - 1, k, k + 1}) {
                if (next_k <= 0) continue;
                int next_pos = pos + next_k;
                if (stoneSet.count(next_pos)) {
                    rj[next_pos].insert(next_k);
                }
            }
        }
    }
    return !rj[stones.back()].empty();
}
```

Complexity: **O(n²)** worst case (each stone × each possible jump size). Space O(n²) for the maps.

---

## 6. Trace it

`stones = [0, 1, 3, 5, 6, 8, 12, 17]`.

```
rj[0] = {0}.

Process 0: k=0. next_k options: -1, 0, 1 → only 1 valid. 0+1=1 is stone. rj[1] = {1}.
Process 1: k=1. next_k: 0, 1, 2 → 1, 2 valid. 1+1=2 not stone. 1+2=3 stone. rj[3] = {2}.
Process 3: k=2. next_k: 1, 2, 3 → all valid. 3+1=4 not stone. 3+2=5 stone (rj[5] += 2). 3+3=6 stone (rj[6] += 3).
Process 5: k=2. next_k: 1, 2, 3. 5+1=6 stone (rj[6] += 1). 5+2=7 not. 5+3=8 stone (rj[8] += 3).
Process 6: jumps {1, 3}.
  k=1: next_k 1, 2. 6+1=7 not. 6+2=8 stone (rj[8] += 2).
  k=3: next_k 2, 3, 4. 6+2=8 (rj[8] += 2 already). 6+3=9 not. 6+4=10 not.
Process 8: jumps {2, 3}.
  k=2: 8+1=9 not. 8+2=10 not. 8+3=11 not.
  k=3: 8+2=10 not. 8+3=11 not. 8+4=12 stone (rj[12] += 4).
Process 12: k=4. next_k 3, 4, 5. 12+3=15 not. 12+4=16 not. 12+5=17 stone (rj[17] += 5).

rj[17] = {5}. Non-empty → true.  ✓
```

---

## 7. Common pitfalls

1. **State = position only.** Without "last jump," you can't decide which jumps are next legal. Need the pair.
2. **Allowing jump 0.** The next jump must be ≥ 1.
3. **Iterating the set while modifying it.** We add to `rj[next_pos]` where `next_pos > pos`, so we never add to the set we're currently iterating. Safe, but COPYING `rj[pos]` to a local vector is defensive.
4. **Treating the first jump as variable.** The FIRST jump MUST be size 1 — represented by `rj[0] = {0}` and the natural progression `0 → 1`.
5. **Using a vector instead of a set for rj.** Duplicates explode memory. Use a SET.

---

## 8. The shape — DP with auxiliary state

The pattern: **future moves depend on more than just position → add state.**

| Problem | Auxiliary state |
|---|---|
| **This problem** | last jump size |
| Knight's Tour variants | history of visited cells |
| Stock Trading (LC 309 etc.) | last action (buy/sell/cooldown) |
| Paint House | last color used |
| House Robber III (tree) | last node was robbed? |
| Cherry Pickup II | second player's position |

**Pattern to internalize:**

> "When the LEGAL future moves depend on past actions (not just current position), bake that history into the state. Don't try to factor it out — embrace the higher-dimensional state."

---

> **Self-check — the question to ask next time.**
>
> When the move rules depend on the PREVIOUS move:
>
> > **"State = (current position, previous move's relevant detail). DP over the expanded state. Forward propagation is often cleanest."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Frog_Jump.md`](../Frog_Jump.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Decode_Ways.md`](./Decode_Ways.md), [`Climbing_Stairs.md`](./Climbing_Stairs.md).
  - Coming next: [`Partition_Equal_Subset_Sum.md`](./Partition_Equal_Subset_Sum.md), [`Ones_and_Zeroes.md`](./Ones_and_Zeroes.md).
