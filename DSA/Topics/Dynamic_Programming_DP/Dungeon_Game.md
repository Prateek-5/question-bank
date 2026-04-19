# Dungeon Game

**Problem Link:**
https://leetcode.com/problems/dungeon-game/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Set the Scene

The knight is at the top-left of an `m × n` dungeon grid, and he needs to reach the princess at the bottom-right. He can only move **right or down**. Each cell either damages him (negative value) or heals him (positive value). He starts with some health `H`. His HP must stay **strictly greater than 0** at every moment — if it ever hits 0 or below, he's dead.

Find the **minimum starting health** such that he survives.

Example:
```
-2  -3   3
-5 -10   1
10  30  -5
```

If he starts with 7, can he make it? Let's check one path: right, right, down, down: values -2, -3, 3, 1, -5. HP = 7 → 5 → 2 → 5 → 6 → 1. Never drops to 0. He survives.

If he starts with 6: 6 → 4 → 1 → 4 → 5 → 0. Dies at the last step.

So minimum is **7**.

Let me confirm that 7 is actually optimal for *some* path, and that no other path works with less. We'd need to search or reason carefully — which is exactly what the algorithm does.

----------------------------------------

## Step 2: Why This Isn't Just Minimum Path Sum

This feels superficially like Minimum Path Sum (same grid, same movement), but with a twist: **we don't care about total damage, we care about the worst moment**.

Maximizing total HP at the end isn't enough. A path that heals a lot at the start but requires -1000 HP midway is worse than a path that takes -10 damage consistently. We need to track the minimum HP experienced along the path.

So the naive "sum up cells, maximize sum" approach fails. The objective isn't additive over cells in a usable way — it's about a **running minimum** invariant.

----------------------------------------

## Step 3: Forward Is Too Hard

If we try to DP forward (from start to end), we'd need to track at each cell: "what's the HP I have when I get here, given I started with some specific amount?" But we don't know what amount to start with — that's what we're solving for.

A forward approach would require searching over starting amounts, which is wasteful.

What if we flip the question? Instead of "what's the max HP as I progress?", ask:

> **At each cell, what's the minimum HP I need *entering* this cell in order to survive from here to the end?**

This is a backward question. Answer it for the destination first, then work back to the start.

----------------------------------------

## Step 4: Set Up the Backward DP

Let `need[i][j]` = minimum HP we must have when entering cell (i, j) to survive from (i, j) to the princess.

**Base case (princess cell `(m-1, n-1)`):** After applying this cell's value, we need at least 1 HP. So the HP *before* applying is:

```
need[m-1][n-1] = max(1, 1 - dungeon[m-1][n-1])
```

If the cell is +5 (heals), we just need 1 HP entering — we'll be at 6 after, but we only require to be alive. If the cell is -10, we need 1 - (-10) = 11 HP entering — we'd survive at 1.

**General case:** at cell `(i, j)`, after we apply this cell's value, we need at least `min(need[i+1][j], need[i][j+1])` HP to enter the better of the two next cells. So before applying the current cell's value:

```
need[i][j] = max(1, min(need[i+1][j], need[i][j+1]) - dungeon[i][j])
```

The `max(1, ...)` ensures we never require less than 1 HP (the minimum for survival).

Answer: `need[0][0]`.

----------------------------------------

## Step 5: Trace on the Example

```
dungeon =
  -2  -3   3
  -5 -10   1
  10  30  -5
```

Bottom row up, right column first:

`need[2][2] = max(1, 1 - (-5)) = 6`. (Need 6 HP entering the princess cell; she's at -5.)

`need[2][1] = max(1, need[2][2] - dungeon[2][1]) = max(1, 6 - 30) = 1`. (Healing +30 covers everything.)

`need[2][0] = max(1, need[2][1] - dungeon[2][0]) = max(1, 1 - 10) = 1`. (Heal +10 plus next needs 1 → need 1 HP entering.)

`need[1][2] = max(1, need[2][2] - dungeon[1][2]) = max(1, 6 - 1) = 5`.

`need[1][1] = max(1, min(need[2][1], need[1][2]) - dungeon[1][1]) = max(1, min(1, 5) - (-10)) = max(1, 11) = 11`. (Need 11 HP entering because it's -10 here and next cell needs at least 1.)

`need[1][0] = max(1, min(need[2][0], need[1][1]) - dungeon[1][0]) = max(1, min(1, 11) - (-5)) = max(1, 6) = 6`.

`need[0][2] = max(1, need[1][2] - dungeon[0][2]) = max(1, 5 - 3) = 2`.

`need[0][1] = max(1, min(need[1][1], need[0][2]) - dungeon[0][1]) = max(1, min(11, 2) - (-3)) = max(1, 5) = 5`.

`need[0][0] = max(1, min(need[1][0], need[0][1]) - dungeon[0][0]) = max(1, min(6, 5) - (-2)) = max(1, 7) = 7`.

Answer: **7**. ✓

Notice how the backward computation naturally aggregates: each cell's answer is the minimum "future need" adjusted for its own damage/heal.

----------------------------------------

## Step 6: Why Backward Works

Here's the structural reason. The survival constraint is "HP > 0 at all times." Written another way: "at every point along the path, remaining-cells-to-traverse must leave me alive." The "remaining cells to traverse" is a **suffix** of the path, and suffixes are natural to reason about from the end.

So we compute `need[i][j]` = "minimum health to enter (i, j) such that some path from here to the end keeps HP positive throughout." That's a well-defined, local quantity that depends only on cells further along.

The forward version would have to juggle the running minimum HP and the current HP simultaneously — a 2D state per cell, which is messy. Backward cleanly reduces to "what do I need to enter this cell?"

----------------------------------------

## Step 7: Name It

This is **grid DP computed in reverse**. The key trick is identifying that the constraint (HP > 0) is best expressed as a lower bound on initial HP at each cell, and that this lower bound satisfies a recurrence looking backward from the goal.

More broadly, the technique is: **when the forward direction forces a 2D state (current HP + min HP seen so far), try reversing the direction to collapse it to 1D**.

----------------------------------------

## Step 8: Complexity

Time: each cell computed once, O(1) per cell. **O(m · n)**.
Space: **O(m · n)** for the DP table. Can be optimized to **O(n)** by keeping just the previous row.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int calculateMinimumHP(vector<vector<int>>& d) {
    int m = d.size(), n = d[0].size();
    vector<vector<int>> need(m + 1, vector<int>(n + 1, INT_MAX));
    // Sentinels: beyond the grid, "need" is effectively infinite,
    // except just past the goal which we set to 1 (we need at least 1 alive).
    need[m][n - 1] = need[m - 1][n] = 1;
    for (int i = m - 1; i >= 0; --i) {
        for (int j = n - 1; j >= 0; --j) {
            int minNext = min(need[i + 1][j], need[i][j + 1]);
            need[i][j] = max(1, minNext - d[i][j]);
        }
    }
    return need[0][0];
}
```

Key implementation detail: the sentinel row/column of size `m+1, n+1` with `INT_MAX` everywhere except `need[m][n-1] = need[m-1][n] = 1`. Those two sentinels make the princess cell compute correctly: `need[m-1][n-1] = max(1, 1 - d[m-1][n-1])` as we derived.

----------------------------------------

## Step 10: Follow-up Questions

- **What if moves include diagonals?** Add a third term to `minNext`: `need[i+1][j+1]`.
- **What if HP can overflow an upper cap (knight maxes out at some value)?** Add a cap in the formula — `min(cap, need[i][j])`.
- **Return the actual path.** Track which direction (down vs. right) gave the min at each cell during DP.
- **Multiple knights cooperate (each takes a different path).** Much harder — combinatorial.
- **What if damage can revive (negative cells make you lose, positive ones can boost beyond cap)?** The DP logic still works as long as you define sensible bounds on "alive."
- **Why does forward DP fail here?** Because minimum HP seen along the path is a function of all cells passed, not just a local sum. A backward formulation isolates the local decision cleanly.
