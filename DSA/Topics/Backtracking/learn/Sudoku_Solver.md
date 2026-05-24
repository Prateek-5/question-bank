# Sudoku Solver — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Sudoku_Solver.md`](../Sudoku_Solver.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/sudoku-solver/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~26 minutes. **The senior-bar constraint-satisfaction problem.** The lesson: **three sets of BITMASKS (rows, cols, boxes) make constraint checks O(1). Backtrack cell-by-cell, trying digits 1-9 at each empty cell.** Extends naturally to N-Queens, Latin squares, graph coloring. **Read [`N_Queens.md`](../../Recursion/learn/N_Queens.md) first.**

**Map of this file (12 sections):**

1. Read the problem
2. The brute force (and why it works for 9×9)
3. The three constraint groups
4. Bitmask representation for O(1) checks
5. The box index formula
6. The backtracking algorithm
7. Code
8. Trace through reasoning
9. Why bitmasks beat scanning
10. Common pitfalls
11. Heuristics (next-cell selection)
12. The shape — constraint-satisfaction template

---

## 1. Read the problem

Solve a **partially-filled 9×9 Sudoku grid** by filling empty cells (marked `.`) such that:
- Each ROW contains digits 1-9 (each exactly once).
- Each COLUMN contains digits 1-9 (each exactly once).
- Each of the nine 3×3 BOXES contains digits 1-9 (each exactly once).

**Modify the board in place.** The problem guarantees the puzzle has a unique solution.

---

## 2. The brute force (and why it works for 9×9)

Try every digit 1-9 at every empty cell. Backtrack on conflict. Recursion depth ≤ 81 (the grid size). Branching factor ≤ 9 per cell.

Worst case: 9^81 ≈ 10^77 — astronomical. But CONSTRAINT PRUNING dramatically reduces this. In practice, modern backtracking solves any standard 9×9 in milliseconds.

The trick is making CONSTRAINT CHECKS O(1).

---

## 3. The three constraint groups

For a candidate digit `d` at cell `(r, c)` to be valid:
1. **`d` not already in ROW `r`.**
2. **`d` not already in COLUMN `c`.**
3. **`d` not already in BOX containing (r, c).**

If all three pass, `d` is a valid placement (so far).

> **Mini-refresher: box index.**
>
> Boxes are 3×3 subgrids. Box index from `(r, c)`:
> ```
> box = (r // 3) * 3 + (c // 3)
> ```
> Maps `(r, c)` to one of 9 boxes (indexed 0-8).
>
> Example: `(0, 0)` → box 0. `(0, 4)` → box 1. `(3, 3)` → box 4.

---

## 4. Bitmask representation for O(1) checks

Use 9-bit masks (one bit per digit 1-9, bit `d-1`):
- `rowMask[r]`: bitmask of digits already in row r.
- `colMask[c]`: bitmask of digits already in column c.
- `boxMask[b]`: bitmask of digits already in box b.

To check if d is valid at (r, c):

```
bit = 1 << (d - 1)
if (rowMask[r] | colMask[c] | boxMask[b]) & bit:
    # conflict — d is already in some constraint group
else:
    # valid
```

The combined mask `rowMask[r] | colMask[c] | boxMask[b]` is "digits forbidden at (r, c)." Test if `d`'s bit is in this set: O(1).

To PLACE digit d at (r, c):

```
rowMask[r] |= bit
colMask[c] |= bit
boxMask[b] |= bit
board[r][c] = '0' + d
```

To UNDO:

```
rowMask[r] ^= bit       # XOR toggles bit off (we know it was on)
colMask[c] ^= bit
boxMask[b] ^= bit
board[r][c] = '.'
```

All O(1).

---

## 5. The box index formula

For `(r, c)`:
```
box = (r / 3) * 3 + (c / 3)
```

`r / 3` (integer division) → which row-band (0, 1, or 2). `c / 3` → which column-band. Combine to get the 3×3 grid's index in row-major order.

Verify:
- `(0, 0)` → `0*3 + 0 = 0`. ✓
- `(0, 5)` → `0*3 + 1 = 1`. ✓ (column 5 is in column-band 1).
- `(4, 7)` → `1*3 + 2 = 5`. ✓
- `(8, 8)` → `2*3 + 2 = 8`. ✓

---

## 6. The backtracking algorithm

```
solve(r, c):
    if r == 9: return True             # all cells processed
    
    # Compute next cell
    nr, nc = (r + 1, 0) if c == 8 else (r, c + 1)
    
    if board[r][c] != '.':
        return solve(nr, nc)            # cell already filled, move on
    
    for d in 1..9:
        bit = 1 << (d - 1)
        b = (r / 3) * 3 + (c / 3)
        if (rowMask[r] | colMask[c] | boxMask[b]) & bit:
            continue                     # conflict
        
        # place
        board[r][c] = '0' + d
        rowMask[r] |= bit
        colMask[c] |= bit
        boxMask[b] |= bit
        
        if solve(nr, nc): return True
        
        # undo
        board[r][c] = '.'
        rowMask[r] ^= bit
        colMask[c] ^= bit
        boxMask[b] ^= bit
    
    return False                          # no digit worked
```

Cell-by-cell in row-major order. At each empty cell, try digits 1-9. Skip on conflict. On success: recurse. On failure: undo and try next.

If recursion bubbles all the way back without finding a placement → return False. (Shouldn't happen for valid Sudoku inputs.)

---

## 7. Code

**C++:**

```cpp
class Solution {
    int rowMask[9] = {0}, colMask[9] = {0}, boxMask[9] = {0};
    vector<vector<char>>* board;

    int boxIdx(int r, int c) { return (r / 3) * 3 + c / 3; }

    bool solve(int r, int c) {
        if (r == 9) return true;
        int nr = (c == 8) ? r + 1 : r;
        int nc = (c == 8) ? 0 : c + 1;

        if ((*board)[r][c] != '.') return solve(nr, nc);

        for (int d = 1; d <= 9; ++d) {
            int bit = 1 << (d - 1);
            int b = boxIdx(r, c);
            if ((rowMask[r] | colMask[c] | boxMask[b]) & bit) continue;

            (*board)[r][c] = '0' + d;
            rowMask[r] |= bit;
            colMask[c] |= bit;
            boxMask[b] |= bit;

            if (solve(nr, nc)) return true;

            (*board)[r][c] = '.';
            rowMask[r] ^= bit;
            colMask[c] ^= bit;
            boxMask[b] ^= bit;
        }
        return false;
    }

public:
    void solveSudoku(vector<vector<char>>& bd) {
        board = &bd;
        for (int r = 0; r < 9; ++r) {
            for (int c = 0; c < 9; ++c) {
                if (bd[r][c] != '.') {
                    int d = bd[r][c] - '0';
                    int bit = 1 << (d - 1);
                    rowMask[r] |= bit;
                    colMask[c] |= bit;
                    boxMask[boxIdx(r, c)] |= bit;
                }
            }
        }
        solve(0, 0);
    }
};
```

**Python:**

```python
def solveSudoku(board):
    row_mask = [0] * 9
    col_mask = [0] * 9
    box_mask = [0] * 9
    
    def box_idx(r, c):
        return (r // 3) * 3 + c // 3
    
    # Initialize masks
    for r in range(9):
        for c in range(9):
            if board[r][c] != '.':
                d = int(board[r][c])
                bit = 1 << (d - 1)
                row_mask[r] |= bit
                col_mask[c] |= bit
                box_mask[box_idx(r, c)] |= bit
    
    def solve(r, c):
        if r == 9:
            return True
        nr, nc = (r + 1, 0) if c == 8 else (r, c + 1)
        
        if board[r][c] != '.':
            return solve(nr, nc)
        
        for d in range(1, 10):
            bit = 1 << (d - 1)
            b = box_idx(r, c)
            if (row_mask[r] | col_mask[c] | box_mask[b]) & bit:
                continue
            
            board[r][c] = str(d)
            row_mask[r] |= bit
            col_mask[c] |= bit
            box_mask[b] |= bit
            
            if solve(nr, nc):
                return True
            
            board[r][c] = '.'
            row_mask[r] ^= bit
            col_mask[c] ^= bit
            box_mask[b] ^= bit
        
        return False
    
    solve(0, 0)
```

Complexity: exponential worst case, but practical Sudoku solves in milliseconds.

---

## 8. Trace through reasoning

A FULL trace of a 9×9 puzzle would be hundreds of lines. A small 2×2-style illustration:

Imagine a partial 4×4 Sudoku variant with 2×2 boxes:
```
1 .
. 2
```

Empty cells: (0, 1) and (1, 0).

`(0, 1)`: row 0 has {1}. col 1 has {2}. box 0 has {1}. Allowed: {3, 4} for 4×4 variant. Try 3.
`(1, 0)`: row 1 has {2}. col 0 has {1}. box 0 has {1, 3} (from above). Allowed: {4}. Try 4.

End: filled grid:
```
1 3
4 2
```

Check: all rows/cols/boxes contain {1,2,3,4}? In 4×4, yes — each contains the set {1, 2, 3, 4}.

For 9×9 Sudoku, the same logic with much larger branching and pruning.

---

## 9. Why bitmasks beat scanning

> **Mini-refresher: scanning vs bitmask.**
>
> SCAN check: for each candidate `d`, iterate row r, col c, box b. Check if d appears. O(9) per group → O(27) per check.
>
> BITMASK check: `(rowMask[r] | colMask[c] | boxMask[b]) & bit`. **One** bitwise operation. **O(1).**
>
> Across millions of constraint checks during a hard puzzle's backtracking, this is a HUGE speedup.

Bitmasks also encode "which digits are missing" in a single integer, enabling further optimizations (e.g., iterate only over missing digits via bit manipulation).

---

## 10. Common pitfalls

1. **Scanning for conflicts** (O(9) per check) instead of bitmasks (O(1)). Dramatic slowdown.

2. **Forgetting to populate masks from initial board.** Without this, the algorithm thinks the board is empty and may place duplicates.

3. **Wrong box index formula.** Use `(r / 3) * 3 + c / 3`, not `r / 3 + c / 3 * 3` (would mess up the mapping).

4. **Not handling already-filled cells.** When `board[r][c] != '.'`, just skip to the next cell without trying digits.

5. **Wrong "next cell" computation.** `(r + 1, 0)` if `c == 8`, else `(r, c + 1)`. Off-by-one is common.

6. **Returning false instead of recursing**. After successful placement, return only if `solve(nr, nc)` succeeds — propagate the true.

7. **Forgetting to undo on backtrack.** XOR each bit off (since you XOR'd it on).

8. **Trying memoization.** Doesn't help — each cell has board-dependent constraints. Memoizing would require massive state hashing.

9. **For very hard puzzles**: naive next-cell-in-order can be slow. Pick the most-constrained cell first (Section 11).

---

## 11. Heuristics (next-cell selection)

For competitive solving, an advanced heuristic dramatically speeds up:

> **Most-Constrained Variable (MCV):** at each step, pick the empty cell with the FEWEST possible digits.

Why? Branching on a cell with only 1-2 options has small branching factor; branching on a cell with 9 options blows up.

Implementation: for each empty cell, count the bits set in `~(rowMask[r] | colMask[c] | boxMask[b]) & 0x1FF`. Pick the cell with fewest possible digits.

For interview: the standard "next cell in row-major order" usually suffices. Mention the heuristic if asked about performance.

---

## 12. The shape — constraint-satisfaction template

The pattern:

> **"Place items into a structure under constraints. Use BITMASKS (or sets) to track each constraint's occupancy. Backtrack with O(1) constraint checks."**

| Problem | Constraints |
|---|---|
| **This problem** (Sudoku) | row, col, 3×3 box |
| N-Queens | column, two diagonals |
| Graph Coloring | colors of neighbors |
| Latin Squares | row and column |
| Crossword Solver | grid + word fits |
| Cryptarithmetic | letter-to-digit mapping |
| Sliding Puzzle | adjacency rules |

**Pattern to internalize:**

> "For constraint-satisfaction with discrete choices, track each constraint group with a BITMASK. Check via OR-and-AND. Place, recurse, undo. With heuristics (MCV) for serious performance."

---

> **Self-check — the question to ask next time.**
>
> When you face a "place items satisfying multiple constraint groups" problem, ask:
>
> > **"Can I represent each constraint group as a BITMASK and check O(1) via OR-and-AND? Place, recurse, undo (XOR to toggle)?"**
>
> If yes, you've got an efficient constraint-satisfaction backtracker.

---

## Cross-references

- **Reference card (post-mastery):** [`../Sudoku_Solver.md`](../Sudoku_Solver.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Generate_Parentheses.md`](./Generate_Parentheses.md), [`Palindrome_Partitioning.md`](./Palindrome_Partitioning.md).
  - [`../../Recursion/learn/N_Queens.md`](../../Recursion/learn/N_Queens.md) — same template, different constraints.
  - Backtracking topic complete!
