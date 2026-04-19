# Determine Color of a Chessboard Square

**Problem Link:**
https://leetcode.com/problems/determine-color-of-a-chessboard-square/

**Topic:**
Math

----------------------------------------

## Step 1: The Task

Given a string like `"a1"` or `"h8"` representing a chessboard square, return `true` if the square is **white**, `false` if **black**.

Chessboard convention:
- Columns are letters `a` through `h` (left to right from White's perspective).
- Rows are digits `1` through `8` (bottom to top).
- The **bottom-left corner `a1` is black**. The **bottom-right `h1` is white**. Colors alternate like a checker.

Example: `"a1"` → black → `false`. `"h3"` → ? Let's figure it out.

----------------------------------------

## Step 2: Study the Alternation Pattern

On a chessboard, adjacent squares (sharing an edge) have different colors. So if we move one step horizontally or vertically, the color flips.

Let's assign coordinates: column `a` = 1, `b` = 2, ..., `h` = 8. Row is already 1..8.

- `a1` = (1, 1). Black.
- `b1` = (2, 1). Adjacent to a1 horizontally — white.
- `a2` = (1, 2). Adjacent to a1 vertically — white.
- `b2` = (2, 2). Adjacent to both b1 and a2 — black.

Notice the pattern:
- `a1` (1+1=2, even) → black.
- `b1` (2+1=3, odd) → white.
- `a2` (1+2=3, odd) → white.
- `b2` (2+2=4, even) → black.

**Column + row is even → black. Odd → white.**

That's the rule. We can verify with `h1`: column h = 8, row 1 → 8+1 = 9 (odd) → white. ✓

----------------------------------------

## Step 3: Parse the Input

The input is a 2-character string:
- First char: letter `a`..`h`. Column = `s[0] - 'a' + 1`, so 1..8.
- Second char: digit `1`..`8`. Row = `s[1] - '0'`.

Sum them. If the sum is **odd**, the square is white; if **even**, black.

Return `(col + row) % 2 == 1`.

----------------------------------------

## Step 4: Trace

- `"a1"`: col = 1, row = 1. Sum = 2. Even. Black. Return `false`. ✓
- `"h3"`: col = 8, row = 3. Sum = 11. Odd. White. Return `true`.
- `"c7"`: col = 3, row = 7. Sum = 10. Even. Black. Return `false`.
- `"h8"`: col = 8, row = 8. Sum = 16. Even. Black. Return `false`.

Check `h8` against the board: the top-right corner on a standard board is white... wait, is that right?

Reference rule: *"white on the right"* — the bottom-right of the board (from White's perspective) is a **white** square. That's `h1`, sum = 9, odd → white by our rule. ✓

`h8` is diagonally opposite to `a1`. In 7 column-steps and 7 row-steps from `a1`, we flip color 14 times — back to black. So `h8` = black. ✓

Our formula matches.

----------------------------------------

## Step 5: Why Parity Works

Start at `a1`. Moving one step horizontally OR one step vertically flips the color. After k total steps (any mix), the color has flipped k times — same as `a1` iff k is even, opposite iff k is odd.

From `a1 = (1, 1)` to `(col, row)`, the Manhattan distance is `(col - 1) + (row - 1) = col + row - 2`. The **parity** of this distance matches the parity of `col + row` (the −2 doesn't change parity).

So: `col + row` even → same color as `a1` (black). Odd → opposite (white).

Pure parity argument. No case work, no lookup table.

----------------------------------------

## Step 6: Name It

**Parity of coordinates** — the universal trick for checkerboard coloring. Applications:
- Determining 2-colorability of a bipartite grid.
- Knight's-tour problems (knight always moves between opposite colors).
- Problems like "domino tiling of a board" (a domino covers one black + one white; infeasibility follows from parity imbalance).
- Conway's Game of Life and cellular automata parity invariants.

Whenever you see a grid with alternating structure, `(row + col) % 2` is your friend.

----------------------------------------

## Step 7: Complexity

Time: **O(1)**. Just arithmetic on the two characters.
Space: **O(1)**.

----------------------------------------

## Step 8: C++ Implementation

```cpp
bool squareIsWhite(string coordinates) {
    int col = coordinates[0] - 'a' + 1;
    int row = coordinates[1] - '0';
    return (col + row) % 2 == 1;
}
```

Parse → sum → parity. Three lines.

**Even shorter:** since we're checking parity and `'a' - '0'` is some constant, you can XOR the two chars' low bits directly. But the above is clearer.

----------------------------------------

## Step 9: Follow-up Questions

- **Return the color as a string ("white"/"black").** Trivial modification.
- **Generalize to an N×N board with same checker pattern.** Same formula; no dependence on board size.
- **What color is `a1` exactly? Why black by convention?** Standard chess convention: dark square in the bottom-left corner from White's perspective.
- **Color of two squares: are they the same color?** Compare parities: `(c1 + r1) % 2 == (c2 + r2) % 2`.
- **On a 3D board (e.g., for 3D chess variants).** Color = `(x + y + z) % 2`. Same parity trick, extra dimension.
- **Why doesn't column case (uppercase vs lowercase) matter?** Problem specifies lowercase, but `A - a = 32` doesn't affect parity since 32 is even.
