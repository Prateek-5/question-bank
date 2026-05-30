# Sudoku Solver

**Problem Link:**
<a href="https://leetcode.com/problems/sudoku-solver/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/sudoku-solver/</a>

**Topic:**
Backtracking

----------------------------------------

## Step 1: The Rules of Sudoku

You have a 9×9 grid, partially filled with digits 1-9. Empty cells are marked with `.`. Fill them in such that:
- Every row contains each digit 1-9 exactly once.
- Every column contains each digit 1-9 exactly once.
- Every 3×3 sub-box (there are 9 of them) contains each digit 1-9 exactly once.

Modify the input board in place. The problem guarantees a unique solution.

----------------------------------------

## Step 2: Brute Force Idea

For each empty cell, try digits 1 through 9. If a choice violates Sudoku rules, try the next. If no choice works, backtrack to the previous cell and try a different digit there.

This is classical **backtracking**:
- Pick an empty cell.
- Try each digit 1-9.
- For each: if valid in all three constraints (row, column, box), place it and recurse.
- If recursion fails, undo and try next digit.

If we make it through every cell with valid placements, we've found the solution.

----------------------------------------

## Step 3: How to Validate a Placement Fast

For each cell (r, c), a candidate digit `d` is valid if:
- No other cell in row r contains d.
- No other cell in column c contains d.
- No other cell in the 3×3 box containing (r, c) contains d.

Naive check: scan the row, column, and box each time — O(27) per check. Workable but slow for large backtracking trees.

Faster: maintain **three sets of bitmasks** — one per row, one per column, one per box. Each bitmask's bit `d-1` is set if digit d is present in that row/column/box.

- `rowMask[r]`: 9-bit mask of digits present in row r.
- `colMask[c]`: same for column c.
- `boxMask[b]`: same for box b (where `b = (r/3)*3 + c/3`).

To check if d is valid at (r, c): test if bit d-1 is set in **any** of `rowMask[r]`, `colMask[c]`, `boxMask[b]`. If not set anywhere, valid.

To place: set bit d-1 in all three.
To remove: unset bit d-1 in all three.

Each op O(1).

----------------------------------------

## Step 4: The Backtracking Algorithm

```
initialize rowMask, colMask, boxMask from the existing filled cells

def solve():
    find next empty cell (r, c)
    if no empty cell: return True   # solved!
    
    for d in 1..9:
        bit = 1 << (d - 1)
        if (rowMask[r] | colMask[c] | boxMask[box(r, c)]) & bit: continue  # not valid
        
        # place d
        board[r][c] = d
        rowMask[r] |= bit
        colMask[c] |= bit
        boxMask[box(r, c)] |= bit
        
        if solve(): return True
        
        # undo
        board[r][c] = '.'
        rowMask[r] ^= bit
        colMask[c] ^= bit
        boxMask[box(r, c)] ^= bit
    
    return False   # no digit worked
```

Recursion explores all choices. The masks let validity checks be O(1).

"Find next empty cell" can be a linear scan starting from the current position (preserving order), or optimized by maintaining an index.

----------------------------------------

## Step 5: Why Backtracking Works for Sudoku

Sudoku has a tree of decisions: each empty cell is a branching point with up to 9 children. With strict constraints pruning invalid choices early, most branches fail quickly.

The worst case is exponential, but in practice Sudoku puzzles are constrained enough that good backtracking finishes in milliseconds. Modern solvers can solve any 9×9 Sudoku almost instantly.

----------------------------------------

## Step 6: Practical Notes

**Choosing the next cell:** just picking the first empty cell in row-major order is fine. Fancier heuristics ("most-constrained cell first") can speed things up significantly, but they complicate the code.

**Initial mask population:** before the recursion starts, iterate the board once and populate rowMask, colMask, boxMask based on pre-filled cells.

**Undo step:** we use XOR (`^=`) to toggle bits. Since we only ever add then remove the same bit, toggling twice cancels out.

----------------------------------------

## Step 7: Walk Through a Small Thought Experiment

Consider a simpler case: a 2×2 puzzle (for illustration only — real Sudoku is 9×9). Suppose we have:
```
1 .
. 2
```

Empty cells: (0, 1) and (1, 0). Constraints: each row and column has each of {1, 2} exactly once.

- (0, 1): row 0 has 1. Can be 2. Place 2.
- (1, 0): row 1 has 2. Column 0 has 1. Can be 1? No, column 0 already has 1. Can be 2? No, row 1 has 2. Fail. Backtrack.
- Back to (0, 1): already tried 2. Out of options. Backtrack further — no further. Problem unsolvable.

For a valid 9×9 Sudoku, the branching is massive but pruning keeps it tractable.

----------------------------------------

## Step 8: Name It

This is **constraint-propagation backtracking**. The constraints (row, column, box uniqueness) are maintained incrementally via bitmasks, and the recursion explores the decision tree.

Related patterns:
- N-Queens (similar structure; different constraints).
- Latin Squares.
- Crossword puzzle solving.
- SAT solvers (a generalization).

Sudoku is actually NP-hard in general (for n×n grids), but for small fixed sizes like 9, it's always solvable in practice.

----------------------------------------

## Step 9: Complexity

**Time**: worst case exponential, but the constraints prune the search dramatically. For standard 9×9, under a millisecond usually.

**Space**: O(1) extra memory beyond the board (just three 9-element arrays and recursion depth ≤ 81).

----------------------------------------

## Step 10: C++ Implementation

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
        // populate masks from existing digits
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

Reading the code:
- `solve(r, c)`: try to fill cell (r, c) and beyond.
- If cell is already filled, move to the next.
- Otherwise, try each digit; for each, check validity via the three masks; if valid, place and recurse.
- On recursion failure, undo and try the next digit.

----------------------------------------

## Step 11: Follow-up Questions

- **Count the number of valid solutions.** Don't return on first; continue searching and count. (Normally Sudoku has one, but custom puzzles may have more.)
- **Solve a partially-filled puzzle with constraints violated in the input.** Detect the violation during initial mask population (bit already set means conflict).
- **Solve 16×16 or 25×25 Sudoku.** Same algorithm; adjust constants. Bitmasks still fit in 32 bits for 16×16.
- **Dance-Links / Algorithm X.** Knuth's algorithm for exact-cover problems. Much more efficient for Sudoku than naive backtracking.
- **Deduction-based preprocessing.** Apply logical deduction rules (naked singles, hidden singles, pairs, etc.) before/during backtracking to prune.
- **Detect if a Sudoku has multiple solutions.** Continue search after the first solution; if another is found, the puzzle isn't well-formed.
