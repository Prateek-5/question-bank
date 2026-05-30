# Valid Sudoku — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Valid_Sudoku.md`](../Valid_Sudoku.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/valid-sudoku/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/valid-sudoku/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. The problem teaches **multi-set tracking** — maintaining several independent hash sets (or bitmasks) at the same time, one per "constraint group." The pattern reappears in N-Queens, graph coloring, schedule conflict detection, and many other "uniqueness within groups" problems.

**Map of this file (10 short sections):**

1. Read the problem (with picture)
2. The three rules — rows, columns, 3×3 boxes
3. The natural brute force
4. The pivot — track uniqueness per group
5. The box-index formula
6. Hashset version (cleaner to read)
7. Bitmask version (fastest)
8. Code + trace
9. Common pitfalls
10. The shape — multi-set tracking elsewhere

---

## 1. Read the problem (with picture)

You're given a 9×9 grid representing a Sudoku board. Each cell is either a digit `'1'..'9'` or `'.'` (empty). Determine if the partially-filled board is **valid** so far — meaning no rule is violated by the digits currently placed.

**Important:** the board doesn't have to be SOLVABLE or COMPLETE. We're just checking whether the existing digits respect the rules.

Sample valid board (partial — some cells empty):

```
       col 0 1 2   3 4 5   6 7 8
row 0: [5][3][.] |[.][7][.]|[.][.][.]
row 1: [6][.][.] |[1][9][5]|[.][.][.]
row 2: [.][9][8] |[.][.][.]|[.][6][.]
       ──────────┼─────────┼─────────
row 3: [8][.][.] |[.][6][.]|[.][.][3]
row 4: [4][.][.] |[8][.][3]|[.][.][1]
row 5: [7][.][.] |[.][2][.]|[.][.][6]
       ──────────┼─────────┼─────────
row 6: [.][6][.] |[.][.][.]|[2][8][.]
row 7: [.][.][.] |[4][1][9]|[.][.][5]
row 8: [.][.][.] |[.][8][.]|[.][7][9]
```

The bold borders divide the grid into nine 3×3 **sub-boxes** (top-left, top-middle, top-right, middle-left, ..., bottom-right).

---

## 2. The three rules — rows, columns, 3×3 boxes

For the board to be valid, ALL THREE must hold:

1. **Row rule:** within each row, each digit appears at most once. (So row 0 here has `5, 3, 7` — three different digits, no repeats. ✓)
2. **Column rule:** within each column, each digit appears at most once.
3. **Box rule:** within each 3×3 box, each digit appears at most once.

Empty cells (`.`) don't count — they're "no constraint applied yet."

If ALL three rules hold for every digit in the grid, return `true`. Otherwise return `false`.

---

## 3. The natural brute force

For each digit, scan its row, column, and box for duplicates.

```cpp
bool isValidSudoku(vector<vector<char>>& board) {
    for (int r = 0; r < 9; r++) {
        for (int c = 0; c < 9; c++) {
            char d = board[r][c];
            if (d == '.') continue;

            // scan row r (excluding this cell)
            for (int cc = 0; cc < 9; cc++) {
                if (cc != c && board[r][cc] == d) return false;
            }
            // scan column c
            for (int rr = 0; rr < 9; rr++) {
                if (rr != r && board[rr][c] == d) return false;
            }
            // scan 3×3 box
            int br = (r / 3) * 3, bc = (c / 3) * 3;
            for (int rr = br; rr < br + 3; rr++) {
                for (int cc = bc; cc < bc + 3; cc++) {
                    if ((rr != r || cc != c) && board[rr][cc] == d) return false;
                }
            }
        }
    }
    return true;
}
```

For each filled cell (up to 81), we scan 9 + 9 + 9 = 27 other cells. Total: ~81 × 27 = ~2200 ops. Fast.

But it's wasteful — we rescan the same row, column, and box many times (once for each digit in them).

**Pivot question:** can we make one pass through the grid, building up uniqueness-tracking state, instead of repeating scans?

---

## 4. The pivot — track uniqueness per group

There are exactly **27 "uniqueness groups"** in Sudoku:

- 9 rows.
- 9 columns.
- 9 boxes.

For each group, we want to know: "has digit `d` appeared in this group yet?" If yes when we try to place `d`, it's a conflict.

**The trick:** maintain a **set per group** (27 sets total) tracking which digits have appeared. Walk the grid once. For each filled cell, before recording the digit, check all three relevant groups (row, column, box) for prior occurrences. If any group already contains the digit → conflict, return `false`. Otherwise add to all three groups and continue.

**One linear pass through the grid. O(1) per cell. Total O(81) = O(1) since the board size is fixed.**

---

## 5. The box-index formula

> **Mini-refresher: which 3×3 box does cell (r, c) belong to?**
>
> The grid has 3 row-bands (rows 0-2, 3-5, 6-8) and 3 column-bands (cols 0-2, 3-5, 6-8). A cell's box index is determined by which row-band and column-band it's in.
>
> - Row-band: `r / 3` (integer division). Values 0, 1, 2.
> - Column-band: `c / 3`. Values 0, 1, 2.
>
> Number the 9 boxes 0..8 in row-major order. Then:
>
> ```
> box_index = (r / 3) × 3 + (c / 3)
> ```
>
> Examples:
> - `(0, 0)`: `0/3=0`, `0/3=0` → box 0.
> - `(2, 5)`: `2/3=0`, `5/3=1` → box `0×3 + 1 = 1`.
> - `(4, 4)`: `4/3=1`, `4/3=1` → box `1×3 + 1 = 4`.
> - `(8, 8)`: `8/3=2`, `8/3=2` → box `2×3 + 2 = 8`.
>
> Each cell maps to exactly one box, 0..8.

---

## 6. Hashset version (cleaner to read)

Use three arrays-of-sets:

```cpp
unordered_set<char> rowSet[9], colSet[9], boxSet[9];

for (int r = 0; r < 9; r++) {
    for (int c = 0; c < 9; c++) {
        char d = board[r][c];
        if (d == '.') continue;

        int b = (r / 3) * 3 + (c / 3);

        if (rowSet[r].count(d) || colSet[c].count(d) || boxSet[b].count(d)) {
            return false;
        }

        rowSet[r].insert(d);
        colSet[c].insert(d);
        boxSet[b].insert(d);
    }
}
return true;
```

Three lookups, three inserts per filled cell. Clean.

> **Mini-refresher: `unordered_set::count`.**
>
> `count(x)` returns `1` if `x` is in the set, `0` otherwise (since the set has no duplicates). In a boolean context, `count(x)` is "truthy" if present. Equivalent to `set.contains(x)` in newer C++ (C++20).

---

## 7. Bitmask version (fastest)

For each row/column/box, use a 9-bit integer where bit `d-1` is set if digit `d` has appeared.

```cpp
int rowMask[9] = {0};
int colMask[9] = {0};
int boxMask[9] = {0};

for (int r = 0; r < 9; r++) {
    for (int c = 0; c < 9; c++) {
        char d = board[r][c];
        if (d == '.') continue;

        int bit = 1 << (d - '1');           // d = '1'..'9' → bit 0..8
        int b = (r / 3) * 3 + (c / 3);

        if ((rowMask[r] & bit) || (colMask[c] & bit) || (boxMask[b] & bit)) {
            return false;
        }

        rowMask[r] |= bit;
        colMask[c] |= bit;
        boxMask[b] |= bit;
    }
}
return true;
```

> **Mini-refresher: bitmask for set membership.**
>
> An integer can encode a small set: each bit represents one element. For a 9-element universe (digits 1-9), use bits 0..8.
>
> - **Test membership:** `mask & (1 << k)` — non-zero if bit k is set.
> - **Add an element:** `mask |= (1 << k)`.
> - **Remove:** `mask &= ~(1 << k)`.
>
> All operations are O(1). Bitmasks are typically faster than hash sets when the universe is small (< 32 or 64 elements depending on integer size).

Bitmask is the fastest version — no hashing overhead, just bit ops.

---

## 8. Code + trace

**Bitmask version (C++):**

```cpp
bool isValidSudoku(vector<vector<char>>& board) {
    int rowMask[9] = {0};
    int colMask[9] = {0};
    int boxMask[9] = {0};

    for (int r = 0; r < 9; r++) {
        for (int c = 0; c < 9; c++) {
            char d = board[r][c];
            if (d == '.') continue;

            int bit = 1 << (d - '1');
            int b = (r / 3) * 3 + (c / 3);

            if ((rowMask[r] & bit) || (colMask[c] & bit) || (boxMask[b] & bit)) {
                return false;
            }

            rowMask[r] |= bit;
            colMask[c] |= bit;
            boxMask[b] |= bit;
        }
    }
    return true;
}
```

**Python (hashset version, clearest):**

```python
def isValidSudoku(board):
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]

    for r in range(9):
        for c in range(9):
            d = board[r][c]
            if d == '.':
                continue
            b = (r // 3) * 3 + (c // 3)
            if d in rows[r] or d in cols[c] or d in boxes[b]:
                return False
            rows[r].add(d)
            cols[c].add(d)
            boxes[b].add(d)
    return True
```

**Trace** on a simplified 3×3-cell scenario (just the top-left chunk):

```
board[0][0] = '5', board[0][1] = '3', board[1][3] = '1', board[1][4] = '9',
board[1][5] = '5'.

Walk:

(0, 0) '5':  bit = 1 << 4 = 16.  b = 0.
    rowMask[0] = 0, colMask[0] = 0, boxMask[0] = 0. No conflict.
    rowMask[0] = 16, colMask[0] = 16, boxMask[0] = 16.

(0, 1) '3':  bit = 1 << 2 = 4.   b = 0.
    rowMask[0] = 16 (only bit 4). Check bit 2 of 16: 0. No conflict.
    rowMask[0] = 16 | 4 = 20.  colMask[1] = 4.  boxMask[0] = 16 | 4 = 20.

(1, 3) '1':  bit = 1.  b = 1.   ← box index: (1/3)*3 + (3/3) = 0 + 1 = 1.
    All masks empty for these indices. No conflict.
    rowMask[1] = 1.  colMask[3] = 1.  boxMask[1] = 1.

(1, 4) '9':  bit = 1 << 8 = 256.  b = 1.
    rowMask[1] = 1 (no bit 8). colMask[4] = 0. boxMask[1] = 1.   No conflict.
    rowMask[1] = 1 | 256 = 257. colMask[4] = 256. boxMask[1] = 1 | 256 = 257.

(1, 5) '5':  bit = 16.  b = 1.
    rowMask[1] = 257. (bit 4 of 257? 257 = 0b100000001 — bit 4 is 0.) No conflict on row.
    colMask[5] = 0. No conflict.
    boxMask[1] = 257. Bit 4 not set. No conflict.
    rowMask[1] = 257 | 16 = 273.  colMask[5] = 16.  boxMask[1] = 257 | 16 = 273.

... (continue) ...

If at any point we see, say, board[1][0] = '5' — bit 16, b=0:
    colMask[0] = 16 (set from board[0][0]). 16 & 16 = 16 ≠ 0. CONFLICT.
    Return false.
```

The check-then-set pattern catches all three types of conflict (row, column, box) uniformly.

---

## 9. Common pitfalls

1. **Wrong box index formula.** `(r / 3) * 3 + (c / 3)` is correct. NOT `(r / 3) + (c / 3)` (would map cells to wrong boxes) and NOT `r / 3 * 3 + c / 3` if operator precedence trips you up (in C++ this happens to evaluate correctly due to left-to-right `/` then `*`, but use parentheses for safety).

2. **Confusing the box's "row band" with the literal row number.** `(r / 3)` gives 0, 1, or 2 — the BAND index, not the row.

3. **Using `d - '0'` instead of `d - '1'` for bit position.** The digits are `'1'..'9'`, mapping to bits `0..8`. `d - '1'` gives the right bit. `d - '0'` would give bits 1..9 — out of range for `int` if you stop at bit 31, but more importantly off-by-one.

4. **Forgetting the `'.' continue`.** Empty cells must be skipped, otherwise you'd try to compute `'.' - '1' = -3` for the bit — completely wrong.

5. **Returning `false` for valid empty boards.** An entirely empty board (`.` everywhere) is valid — no digits placed yet. The algorithm handles this because we never enter the conflict-check branch.

6. **Trying to check if the board is SOLVABLE.** That's a much harder problem (Sudoku Solver). Valid Sudoku only checks the current state — no further deductions required.

7. **Pre-built C++ `vector<unordered_set<int>>` syntax.** In C++, `vector<unordered_set<char>> rows(9);` creates 9 empty sets. The hashset version compiles only if you have the right STL declarations.

---

## 10. The shape — multi-set tracking elsewhere

The "maintain one tracker per constraint group; check membership before adding" pattern shows up everywhere:

| Problem | Constraint groups | Tracker |
|---|---|---|
| **This problem** (Valid Sudoku) | 9 rows + 9 cols + 9 boxes | bitmask or hashset per group |
| N-Queens | 1 used-cols set + 2 used-diagonals sets | hashset or bitmask |
| Sudoku Solver | same as Valid Sudoku, but with backtracking | bitmask + try-undo |
| Schedule conflict detection | meetings per room | per-room interval list |
| Graph coloring validation | color per neighbor group | per-node color check |
| Word Search II | already-used cells per path | bitmask or set on path |
| Detecting duplicates in a stream within K positions | sliding window | hashset of last-K |

**Pattern to internalize:**

> "When a problem has SEVERAL different 'no duplicates allowed within group X' rules, maintain ONE membership tracker per group. Walk the input once; before each placement, check all relevant trackers; on no conflict, add to all of them; on any conflict, you can immediately reject."

The data structure choice is usually:

- **Bitmask** for small fixed universes (digits 1-9, alphabet a-z, small enums) — fastest.
- **Hashset** for large or open-ended universes — flexible.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem with **multiple "must be unique within this group" constraints**, before nesting loops to recheck membership, ask:
>
> > **"Can I maintain one membership tracker (bitmask or hashset) PER constraint group, and do a single walk with O(1) check-then-add per element?"**
>
> If yes, you've collapsed redundant scans into a single linear pass.

---

## Cross-references

- **Reference card (post-mastery):** [`../Valid_Sudoku.md`](../Valid_Sudoku.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Anagram.md`](./Valid_Anagram.md) — simpler "frequency count then compare" pattern (1 tracker, not 27).
  - Coming next in this topic: Subarray_Sum_Equals_K — prefix-sum frequency map.
  - Coming later in Backtracking: Sudoku Solver — combines this validity-check pattern with recursive backtracking.
  - Coming later in Recursion: N-Queens — same multi-set-tracking idiom (cols + 2 diagonals).
