# N-Queens — Teaching Walkthrough

> **Reference card (post-mastery):** [`../N_Queens.md`](../N_Queens.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/n-queens/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~25 minutes. **The classic CONSTRAINT-BASED backtracking problem.** The lesson: **track conflict markers (cols, diagonals) as boolean arrays for O(1) constraint checks. Place row-by-row, trying each column; backtrack on conflict.** This template extends to Sudoku, graph coloring, and many other constraint-satisfaction problems. **Read [`Permutations.md`](./Permutations.md) first.**

**Map of this file (11 sections):**

1. Read the problem
2. The brute force
3. The "one queen per row" observation
4. Conflict types (column, two diagonals)
5. O(1) conflict checks via boolean arrays
6. The diagonal index trick
7. The algorithm
8. Code
9. Trace it for n=4
10. Common pitfalls
11. The shape — constraint-based backtracking

---

## 1. Read the problem

Place `n` queens on an `n × n` chessboard so that **NO TWO QUEENS ATTACK EACH OTHER**. Return ALL distinct solutions (board configurations).

A queen attacks any square in its row, column, or diagonals (both main and anti-).

**Examples:**

- `n = 4` → 2 solutions:
  ```
  .Q..      ..Q.
  ...Q      Q...
  Q...      ...Q
  ..Q.      .Q..
  ```
- `n = 1` → 1 solution.
- `n = 2`, `n = 3` → 0 solutions (provably impossible).
- `n = 8` → 92 solutions (famous historical case).

---

## 2. The brute force

Try every placement of n queens on n² cells: `C(n², n)` configurations. For n=8, that's ~4 billion. Infeasible.

We need to exploit structure.

---

## 3. The "one queen per row" observation

> **Mini-refresher: rows must have exactly one queen.**
>
> Two queens in the same row would attack each other. So **AT MOST one queen per row**.
>
> Also: we have n queens to place across n rows. So **EXACTLY one queen per row**.
>
> By symmetric argument: exactly one queen per COLUMN too.

This reduces the search space dramatically. A solution is characterized by: **for each row, which column holds that row's queen.** So we can enumerate by placing queens row-by-row.

For n rows, n columns each, that's up to `n^n` configurations — much better than `C(n², n)`. With pruning, it's far less.

---

## 4. Conflict types (column, two diagonals)

When we place a queen at `(r, c)`, the conflict-types with EARLIER queens (placed in rows 0..r-1) are:

1. **Column**: some earlier queen is in column `c`.
2. **Main diagonal** (top-left to bottom-right): some earlier queen `(r', c')` with `r' - c' == r - c`.
3. **Anti-diagonal** (top-right to bottom-left): some earlier queen with `r' + c' == r + c`.

(Same-row check is automatic since we place one per row.)

> **Mini-refresher: why r-c and r+c?**
>
> Main diagonal cells: as you walk down-right, both r and c increase by 1. So `r - c` stays constant. All cells on the SAME main diagonal share the same `r - c` value.
>
> Anti-diagonal cells: walking down-left, r increases and c decreases. So `r + c` stays constant.
>
> Use `r - c` and `r + c` as KEYS to identify diagonals.

---

## 5. O(1) conflict checks via boolean arrays

Maintain three boolean arrays as "occupied" markers:
- `cols[c]`: is column `c` occupied?
- `diag1[r - c]`: is main diagonal `r - c` occupied?
- `diag2[r + c]`: is anti-diagonal `r + c` occupied?

For an `n × n` board:
- `cols`: size `n`, indices `0..n-1`.
- `diag1`: `r - c` ranges from `-(n-1)` to `n-1`. Shift by `n-1` to make 0-indexed: `diag1[r - c + n - 1]`, size `2n - 1`.
- `diag2`: `r + c` ranges from `0` to `2n - 2`. Direct: `diag2[r + c]`, size `2n - 1`.

Checking conflict: 3 boolean lookups. **O(1).**

---

## 6. The diagonal index trick

> **Mini-refresher: offsetting negatives.**
>
> For `r - c` ranging from `-(n-1)` to `n-1`: we can't use negative indices in a fixed-size array. Add the offset `n - 1` to make all values in `[0, 2n - 2]`.
>
> ```
> diag1_idx = r - c + (n - 1)
> ```
>
> For `r + c` already in `[0, 2n - 2]` — no offset needed.

Both diagonal arrays have size `2n - 1`. Indexing is straightforward after the offset.

---

## 7. The algorithm

```
def solve(r):
    if r == n:
        record current board configuration
        return
    for c in 0..n-1:
        if cols[c] or diag1[r - c + n - 1] or diag2[r + c]:
            continue                                # conflict, skip
        # place queen at (r, c)
        board[r][c] = 'Q'
        cols[c] = diag1[r - c + n - 1] = diag2[r + c] = True
        solve(r + 1)
        # undo
        board[r][c] = '.'
        cols[c] = diag1[r - c + n - 1] = diag2[r + c] = False
```

Standard backtracking: try each column, mark conflicts, recurse, undo.

---

## 8. Code

**C++:**

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

**Python:**

```python
def solveNQueens(n):
    res = []
    board = [['.'] * n for _ in range(n)]
    cols = [False] * n
    d1 = [False] * (2 * n - 1)
    d2 = [False] * (2 * n - 1)

    def solve(r):
        if r == n:
            res.append([''.join(row) for row in board])
            return
        for c in range(n):
            if cols[c] or d1[r - c + n - 1] or d2[r + c]:
                continue
            board[r][c] = 'Q'
            cols[c] = d1[r - c + n - 1] = d2[r + c] = True
            solve(r + 1)
            board[r][c] = '.'
            cols[c] = d1[r - c + n - 1] = d2[r + c] = False

    solve(0)
    return res
```

Complexity: exponential, but pruning is aggressive — n=10 in milliseconds, n=15 still feasible.

---

## 9. Trace it for n=4

The two solutions are queens at:
- `(0, 1), (1, 3), (2, 0), (3, 2)` → `.Q..|...Q|Q...|..Q.`
- `(0, 2), (1, 0), (2, 3), (3, 1)` → `..Q.|Q...|...Q|.Q..`

Walking through the search would be tedious to fully trace. High-level flow:

```
solve(0):
  c=0: place (0,0). Mark cols[0], d1[3], d2[0].
    solve(1):
      c=0: cols[0] occupied. skip.
      c=1: d1[1-1+3=3] = true (from (0,0): d1[3]). skip.    ← same diagonal
      c=2: d1[1-2+3=2]=F, d2[3]=F, cols[2]=F. Safe. Place (1,2).
        solve(2): ... (all attempts fail; no valid c for row 2)
        backtrack.
      c=3: place (1,3).
        solve(2): try c=1 — diagonal conflict. try c=2 — conflict. All fail.
        backtrack.
    No success starting with (0,0). backtrack.

  c=1: place (0,1). Recurse...
    eventually finds (1,3), (2,0), (3,2). Solution 1 recorded.
    backtrack, try other configurations.

  c=2: place (0,2). Recurse...
    finds (1,0), (2,3), (3,1). Solution 2 recorded.

  c=3: place (0,3). Recurse... no solution (symmetric to c=0 case).
```

Two solutions found. ✓

---

## 10. Common pitfalls

1. **Forgetting to OFFSET `r - c` to non-negative.** `r - c` can be negative; without `+ n - 1`, array access crashes.

2. **Sizing diagonal arrays wrong.** Need `2n - 1` entries (range from `-(n-1)` to `n-1`).

3. **Not undoing markers.** Every backtracking pitfall — undo the booleans AND restore `board[r][c]` to `.`.

4. **Scanning the board for conflicts instead of using markers.** Works but O(n) per check, vs O(1) with markers. Markers are essential for performance.

5. **Confusing row and column iteration.** We iterate ROWS in the outer recursion; for each row, try each column.

6. **Treating same-row conflicts.** Not needed — we place exactly one per row by construction.

7. **Returning early after first solution.** This problem asks for ALL solutions. Don't return after one.

8. **For N-Queens II (count only), unnecessarily storing boards.** Just increment a counter; skip the board allocation.

---

## 11. The shape — constraint-based backtracking

The pattern:

> **"For each step, try each option. Reject options that violate constraints (via O(1) marker checks). Apply, recurse, undo."**

Where it applies:

| Problem | Constraints to track |
|---|---|
| **This problem** (N-Queens) | columns, two diagonals |
| Sudoku Solver | per row, per column, per 3x3 box |
| N-Queens II (count) | same as N-Queens |
| Graph Coloring | colors of neighbors |
| Knight's Tour | visited cells, valid knight moves |
| Latin Squares | rows and columns |
| Cryptarithmetic Puzzles | letter-to-digit assignments |
| Scheduling with conflict graphs | time slot occupancy |

**Pattern to internalize:**

> "When a problem is 'place N items satisfying constraints,' use backtracking with CONFLICT MARKERS (boolean arrays or sets) for O(1) checks. Place → mark → recurse → unmark."

The N-Queens template extends almost verbatim to any constraint-satisfaction problem with discrete choices.

---

> **Self-check — the question to ask next time.**
>
> When you face "place N items, no conflicts," ask:
>
> > **"Can I backtrack item-by-item, using BOOLEAN MARKERS for each conflict-type to check in O(1)?"**
>
> If yes, you've got constraint-based backtracking.

---

## Cross-references

- **Reference card (post-mastery):** [`../N_Queens.md`](../N_Queens.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Permutations.md`](./Permutations.md), [`Combination_Sum_II.md`](./Combination_Sum_II.md).
  - Recursion topic complete!
  - Coming later: Sudoku Solver (in Backtracking topic).
