# Dungeon Game — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Dungeon_Game.md`](../Dungeon_Game.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/dungeon-game/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/dungeon-game/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: REVERSE DP. The "HP > 0 always" constraint is best expressed as a LOWER BOUND on HP at each cell, looking BACKWARD from the destination. `need[i][j] = max(1, min(need[i+1][j], need[i][j+1]) - dungeon[i][j])`.**

**Map of this file (9 sections):**

1. Read the problem
2. Why forward DP is messy
3. The reverse reformulation
4. The recurrence
5. Code
6. Trace it
7. Why reverse is cleaner
8. Common pitfalls
9. The shape — reverse DP

---

## 1. Read the problem

`m × n` grid (the dungeon). A knight starts at top-left, must reach the princess at bottom-right (move only RIGHT or DOWN). Each cell has a value:
- Positive: heals (HP increases).
- Negative: damages (HP decreases).

HP must stay STRICTLY > 0 at every moment (else knight dies). Find the MINIMUM STARTING HP needed.

**Example:**
```
-2  -3   3
-5 -10   1
10  30  -5
```
Min starting HP = **7**.

---

## 2. Why forward DP is messy

A naive forward DP would track "max HP achievable at each cell." But maximizing HP doesn't help — what we care about is whether HP DROPS BELOW 1 at any point.

Two paths with the same final HP can have very different MINIMUM HP along the way. So we'd need state `(cell, min HP seen so far)` — extra dimension.

---

## 3. The reverse reformulation

> **Mini-refresher: flip the question.**
>
> Instead of "what's the max HP I have at (i, j)?", ask: **"What's the MINIMUM HP I need ENTERING (i, j) to survive to the end?"**
>
> Let `need[i][j]` = min HP to enter (i, j) such that some path to (m-1, n-1) keeps HP > 0 throughout.
>
> This question DECOMPOSES backwards naturally.

The constraint "HP > 0 always" is a SUFFIX constraint — it's about the rest of the journey from (i, j). Backward DP isolates it cleanly.

---

## 4. The recurrence

> **Mini-refresher: the BACKWARD recurrence.**
>
> Base (princess cell): `need[m-1][n-1] = max(1, 1 - dungeon[m-1][n-1])`. We need HP after applying the princess cell to be ≥ 1 — so HP entering = max(1, 1 - cell_value).
>
> General: at (i, j), after applying dungeon[i][j], we need ≥ `min(need[i+1][j], need[i][j+1])` HP. Pick the easier child (smaller need). So:
>
> ```
> need[i][j] = max(1, min(need[i+1][j], need[i][j+1]) - dungeon[i][j])
> ```
>
> `max(1, ...)` ensures we never compute "need 0 HP" — knight must be alive.

Answer: `need[0][0]`.

---

## 5. Code

**C++:**

```cpp
int calculateMinimumHP(vector<vector<int>>& d) {
    int m = d.size(), n = d[0].size();
    vector<vector<int>> need(m + 1, vector<int>(n + 1, INT_MAX));
    need[m][n - 1] = need[m - 1][n] = 1;   // sentinels beyond the goal
    for (int i = m - 1; i >= 0; --i) {
        for (int j = n - 1; j >= 0; --j) {
            int minNext = min(need[i + 1][j], need[i][j + 1]);
            need[i][j] = max(1, minNext - d[i][j]);
        }
    }
    return need[0][0];
}
```

Complexity: **O(m · n)** time, **O(m · n)** space (reducible to **O(n)**).

---

## 6. Trace it

Dungeon:
```
-2  -3   3
-5 -10   1
10  30  -5
```

Fill `need` from bottom-right:

- need[2][2] = max(1, 1 - (-5)) = **6**.
- need[2][1] = max(1, 6 - 30) = **1**.
- need[2][0] = max(1, 1 - 10) = **1**.
- need[1][2] = max(1, 6 - 1) = **5**.
- need[1][1] = max(1, min(1, 5) - (-10)) = max(1, 11) = **11**.
- need[1][0] = max(1, min(1, 11) - (-5)) = max(1, 6) = **6**.
- need[0][2] = max(1, 5 - 3) = **2**.
- need[0][1] = max(1, min(11, 2) - (-3)) = max(1, 5) = **5**.
- need[0][0] = max(1, min(6, 5) - (-2)) = max(1, 7) = **7**.  ✓

---

## 7. Why reverse is cleaner

Forward DP: state must track CURRENT HP AND MINIMUM HP SEEN. Two dimensions.

Reverse DP: state is just "what HP do I need entering here to survive?" One scalar per cell. The "min HP > 0" constraint is encoded by the `max(1, ...)` clip.

The key insight: a SUFFIX constraint ("from here to the end, HP must stay positive") aligns with backward DP. Forward DP would require tracking enough STATE to evaluate that constraint later — much messier.

---

## 8. Common pitfalls

1. **Forward DP with single HP tracker.** Fails because two paths with same final HP can have different minima along the way.
2. **Forgetting `max(1, ...)`.** Without it, a heal can produce 0 or negative "need" — but knight must be alive (HP ≥ 1).
3. **Initializing sentinels to 0.** Should be 1 just past the goal (so the goal computes correctly).
4. **Treating princess cell value as ignored.** It still applies — affects the knight's HP at the end.
5. **Using min instead of max for the clip.** Wrong direction — we want the LARGEST sensible HP requirement.
6. **Iterating forward (i: 0→m-1, j: 0→n-1).** Backward DP needs reverse iteration (i: m-1→0, j: n-1→0).

---

## 9. The shape — reverse DP

The pattern: **when constraints look BACKWARD (from end), flip the DP direction.**

| Problem | Backward reasoning |
|---|---|
| **This problem** | min HP to survive REST of journey |
| Cherry Pickup | reverse for two simultaneous paths |
| Jump Game II | min jumps from position to end |
| Stone Game IV | win/lose evaluated from terminal states |
| Longest Common Subsequence (variants) | sometimes cleaner backward |
| Coin Change | min coins (often forward, but can go either way) |

**Pattern to internalize:**

> "When the CONSTRAINT is about the FUTURE/SUFFIX (HP > 0 till the end, reachability from here, etc.), reverse DP. When it's about the PAST/PREFIX (max sum so far, reached cells), forward DP."

---

> **Self-check — the question to ask next time.**
>
> When the problem requires a "running min/max stays in bounds" constraint:
>
> > **"Can I reverse the DP — ask 'what do I NEED at this cell?' looking from the destination back? Often this collapses the state from 2D to 1D scalar."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Dungeon_Game.md`](../Dungeon_Game.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Minimum_Path_Sum.md`](./Minimum_Path_Sum.md), [`Triangle.md`](./Triangle.md), [`Unique_Paths.md`](./Unique_Paths.md).
  - Coming next: [`Numbers_at_Most_N_Given_Digit_Set.md`](./Numbers_at_Most_N_Given_Digit_Set.md).
