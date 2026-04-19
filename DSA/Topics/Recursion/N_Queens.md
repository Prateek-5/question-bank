# N-Queens

**Problem Link:**
https://leetcode.com/problems/n-queens/

**Topic:**
Recursion

----------------------------------------

## Step 1: Understand Queens' Attack

In chess, a queen attacks any square on its row, its column, or its diagonals (both main and anti). The **N-Queens** problem: place `n` queens on an `n × n` board so that no two queens attack each other. Return all valid placements.

For `n = 4`:

```
. Q . .          . . Q .
. . . Q          Q . . .
Q . . .          . . . Q
. . Q .          . Q . .
```

Two valid placements. These are the *only* valid placements (excluding rotations and reflections, which are still considered distinct boards).

For `n = 1`: one queen, nothing to attack. 1 solution. `n = 2` and `n = 3`: no solutions (provable by case analysis). `n = 4`: 2 solutions.

----------------------------------------

## Step 2: Where Do We Even Start?

Brute force: try all possible placements. With n² cells and choose-n-of-them, that's `C(n², n)` configurations — for n = 8, about 4 billion. Infeasible.

Can we use problem structure to reduce this?

**Observation:** any valid solution has exactly **one queen per row** (since two queens in the same row attack each other). Same for columns. So a solution is characterized by: for each row, which column holds that row's queen.

That collapses the search space: instead of `C(n², n)`, it's `n^n` at worst. For n = 10, that's 10 billion — still big but more tractable. And we can prune much further.

----------------------------------------

## Step 3: Row-by-Row Backtracking

Place a queen in row 0. Then row 1. Then row 2. At each row, try each column — if placing at that column doesn't conflict with any already-placed queen, recurse. If all rows placed → valid solution.

Conflicts to check for the new queen at row `r`, column `c`:
- **Column:** no queen in column `c` in earlier rows.
- **Main diagonal** (top-left to bottom-right): no queen with same `row - col` value.
- **Anti-diagonal** (top-right to bottom-left): no queen with same `row + col` value.

Why `row - col` and `row + col`? On the main diagonal, as you move down-right, row and col both increase by 1, so `row - col` stays constant. On the anti-diagonal, as you move down-left, row increases by 1 and col decreases by 1, so `row + col` stays constant.

----------------------------------------

## Step 4: Data Structures for O(1) Conflict Checks

Maintain three sets (or boolean arrays):
- `cols[c] = true` if some earlier row has a queen in column `c`.
- `diag1[r - c]` = true if some earlier row has a queen on the main diagonal with that `r - c` key.
- `diag2[r + c]` = true if some earlier row has a queen on the anti-diagonal with that `r + c` key.

For `r - c`, the value ranges from `-(n-1)` to `n-1`. Shift it by `n-1` to make it 0-indexed: `diag1[r - c + n - 1]`.
For `r + c`, the value ranges from `0` to `2n - 2`. Use `diag2[r + c]` directly.

With these, checking "is (r, c) safe?" is three boolean lookups — O(1).

----------------------------------------

## Step 5: The Backtracking Skeleton

```
solve(r):
    if r == n:
        record current board
        return
    for c in 0..n-1:
        if cols[c] or diag1[r-c+n-1] or diag2[r+c]:
            continue   # conflict, skip
        place queen at (r, c)
        mark cols[c] = diag1[r-c+n-1] = diag2[r+c] = true
        solve(r + 1)
        unmark them
        remove queen
```

Classic apply-recurse-undo pattern.

----------------------------------------

## Step 6: Trace for n = 4

Place queens row by row. I'll show the board and which markers are set. Notation: (r, c) means row r, column c.

```
solve(0):
  try c=0: place (0, 0). cols={0}, d1={0}, d2={0}.
    solve(1):
      c=0: cols[0] → skip.
      c=1: d2[2]? not set. d1[1-1+3=3]? not set. (0)? not set. Wait, let me recompute.
           For (1, 1): d1 key = 1-1 = 0, shifted = 0+3 = 3. d2 key = 1+1 = 2.
           d2[2] not set yet. d1[3] not set. cols[1] not set. Safe? But conflict check: (0,0) and (1,1) — same diagonal. d1 key for (0,0) = 0-0 = 0, shifted = 3. And for (1,1), d1 key shifted = 3. SAME. So should conflict.
           I had d1 = {0} meaning d1[0-0+3=3] was set. So d1[3] IS set. Skip c=1.
      c=2: d1 key 1-2 = -1, shifted 2. d2 key 3. cols[2]=F, d1[2]=F, d2[3]=F. Safe.
           Place (1, 2). Markers: cols={0,2}, d1={3, 2}, d2={0, 3}.
        solve(2):
          c=0: cols[0]=T. skip.
          c=1: d2[3]=T. skip.
          c=2: cols[2]=T. skip.
          c=3: d1[2-3+3=2]=T. skip.
          All failed. Backtrack.
        Undo (1, 2) markers.
      c=3: d2[4]=F. d1[1-3+3=1]=F. cols[3]=F. Safe.
           Place (1, 3). Markers: cols={0,3}, d1={3, 1}, d2={0, 4}.
        solve(2):
          c=0: cols. skip.
          c=1: d1[2-1+3=4]=F, d2[3]=F, cols[1]=F. Safe.
               Place (2, 1). ...
            solve(3):
              c=0: cols. skip. c=1: cols. skip. c=2: d2[5]? Let me check. d1[3-2+3=4]=T. skip.
              c=3: cols. skip.
              All fail. Backtrack.
            Undo.
          c=2: d1[2-2+3=3]=T. skip. c=3: cols. skip.
          Backtrack.
        Undo.
  ...
```

Rather than tracing the entire thing, I'll trust the process. The algorithm eventually finds:
- `[. Q . . ; . . . Q ; Q . . . ; . . Q .]` (queens at (0,1), (1,3), (2,0), (3,2)).
- `[. . Q . ; Q . . . ; . . . Q ; . Q . .]` (queens at (0,2), (1,0), (2,3), (3,1)).

Two solutions for n = 4, as expected.

----------------------------------------

## Step 7: Why Pruning Is Dramatic

Without the three marker sets, we'd check conflicts by scanning all placed queens — O(n) per check, O(n²) per row → O(n³) per branch. With markers, conflict check is O(1), so per row it's O(n).

Even more importantly, **bad branches are pruned early**. As soon as we can't place a queen in any column of row r, we backtrack — avoiding all descendants. For large n (say, n = 14), pruning reduces work by millions of times.

Backtracking's power isn't in the search tree's size — it's in how aggressively we can cut off branches.

----------------------------------------

## Step 8: Name It

This is **constraint-based backtracking**. Solutions are built incrementally, each step must respect constraints, and violating a constraint prunes the entire subtree. The constraints (row, column, diagonals) are expressed as invariants over already-made choices.

The same template solves Sudoku (constraints per row, column, 3x3 box), Knight's Tour, Latin squares, graph coloring, and many other NP-hard-but-solvable problems at reasonable sizes.

----------------------------------------

## Step 9: Complexity

Time: the exact count is tricky (related to the number of N-Queens solutions, which grows roughly like `n!`). **Exponential in n** but with aggressive pruning, n = 15 or so is solvable in reasonable time.

Space: the markers use O(n) boolean arrays. The recursion stack is O(n) deep. The output is `O(solutions · n²)` because each solution is stored as a board.

----------------------------------------

## Step 10: C++ Implementation

```cpp
vector<vector<string>> solveNQueens(int n) {
    vector<vector<string>> res;
    vector<string> board(n, string(n, '.'));
    vector<bool> cols(n, false), d1(2 * n - 1, false), d2(2 * n - 1, false);

    function<void(int)> solve = [&](int r) {
        if (r == n) { res.push_back(board); return; }
        for (int c = 0; c < n; ++c) {
            if (cols[c] || d1[r - c + n - 1] || d2[r + c]) continue;
            board[r][c] = 'Q';
            cols[c] = d1[r - c + n - 1] = d2[r + c] = true;
            solve(r + 1);
            board[r][c] = '.';
            cols[c] = d1[r - c + n - 1] = d2[r + c] = false;
        }
    };

    solve(0);
    return res;
}
```

A quick sanity check of the indexing:
- `d1` indexed by `r - c + (n - 1)` — offset to make non-negative.
- `d2` indexed by `r + c` directly (already ≥ 0).
- Both arrays have size `2n - 1`, enough to hold all possible diagonals.

----------------------------------------

## Step 11: Follow-up Questions

- **N-Queens II (count only, no boards).** Same algorithm but increment a counter instead of pushing boards. Avoids the O(n²) board-copy.
- **Faster with bitmasks.** Represent cols/diagonals as integers; use bit-tricks to find the next valid column in O(1). Practical for n ≤ 32.
- **Allow multiple queens per diagonal (modified rules).** Adjust the invariants.
- **Other piece placements (knights that don't attack each other).** Different constraints; same backtracking template.
- **Graph coloring.** Exactly the same backtracking shape — try each color that doesn't conflict with neighbors.
- **3D N-Queens (on a cube).** Exists as a variant but not standard; constraint set becomes richer.
