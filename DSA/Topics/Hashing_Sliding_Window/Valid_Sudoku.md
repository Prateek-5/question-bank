# Valid Sudoku

**Problem Link:**
<a href="https://leetcode.com/problems/valid-sudoku/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/valid-sudoku/</a>

**Topic:**
Hashing / Sliding Window

----------------------------------------

## Step 1: What Makes a Sudoku Valid?

A 9×9 grid with digits 1-9 and `.` (empty). Check if it's a valid state (not necessarily solvable or complete). Three rules:

- **Row rule**: each row contains each digit at most once (ignoring '.').
- **Column rule**: each column contains each digit at most once.
- **Box rule**: each of the nine 3×3 sub-boxes contains each digit at most once.

We only check existing digits. `.`s don't contribute.

Return true if all rules hold; false otherwise.

Unlike Sudoku Solver, we're not filling anything — just verifying.

----------------------------------------

## Step 2: Brute-Force Thinking

For each digit in the grid, check that:
- It doesn't appear elsewhere in its row.
- Doesn't appear elsewhere in its column.
- Doesn't appear elsewhere in its 3×3 box.

Could scan the whole grid for each filled cell. O(81) cells × O(81) checks = ~6500 ops. Fast enough, but there's a cleaner way.

----------------------------------------

## Step 3: The Hashset Approach

Maintain three sets per "unit":
- 9 sets for rows.
- 9 sets for columns.
- 9 sets for boxes.

Walk through every cell in the grid once. For each filled cell (r, c) with value v:
- If v is already in `row_set[r]`, `col_set[c]`, or `box_set[b]` (where b is the 3×3 box index), return false.
- Else, insert v into all three sets.

If we finish without conflict, return true.

Cell's box index: `b = (r / 3) * 3 + c / 3`. This maps each (r, c) to one of 9 boxes (0 to 8).

----------------------------------------

## Step 4: Compact Via Encoded Strings

Instead of three separate sets per row/col/box (27 sets total), use one big hashset with **encoded strings**.

For each filled cell with value v:
- Insert "v in row r": encoded as `"v@row" + to_string(r)`.
- Insert "v in col c": encoded as `"v@col" + to_string(c)`.
- Insert "v in box b": encoded as `"v@box" + to_string(b)`.

Before inserting, check if any of these three keys already exists. If yes, conflict.

This trades 27 small sets for one big set. Memory-wise similar; code slightly cleaner.

----------------------------------------

## Step 5: Bitmask Approach (Fastest)

For each row/col/box, use a 9-bit integer. Bit d-1 is set if digit d is present.

For cell (r, c) with digit v:
- bit = 1 << (v - 1).
- Check: `rowMask[r] & bit`, `colMask[c] & bit`, `boxMask[b] & bit`. If any are non-zero, conflict.
- Else: `rowMask[r] |= bit; colMask[c] |= bit; boxMask[b] |= bit`.

This is the tightest implementation — no hash overhead, bit operations are constant-time.

----------------------------------------

## Step 6: Trace

Valid partial Sudoku:
```
5 3 . . 7 . . . .
6 . . 1 9 5 . . .
. 9 8 . . . . 6 .
...
```

Process (0, 0): value 5. Masks empty. No conflict. Set bit 4 in rowMask[0], colMask[0], boxMask[0].

Process (0, 1): value 3. rowMask[0] has bit 4 only. Bit 2 not set. No conflict. Set bit 2 in all three (row 0, col 1, box 0).

... continue ...

Process (0, 4): value 7. rowMask[0] is (bits 2, 4). Bit 6 not set. Set bit 6 in row 0, col 4, box 1 (since col 4, row 0 → box = 0*3 + 4/3 = 1).

The check-and-set pattern proceeds. If any check ever finds the bit already set, return false.

Suppose there were a conflict at (1, 0) with value 5 (already in col 0). Then `colMask[0] & (1 << 4) != 0`, conflict, return false.

----------------------------------------

## Step 7: Name It

**Hashset / bitmask per constraint group.** Same pattern appears in:
- Sudoku Solver (combines this with backtracking).
- N-Queens (row, col, two diagonals as constraint groups).
- Graph coloring validation.

The key insight: when constraints say "some set of elements must be unique within specific groups," maintain a membership tracker per group.

----------------------------------------

## Step 8: Complexity

Time: **O(1)** — the grid is fixed 9×9, so we do at most 81 cell-checks, each O(1). Constant time!

Space: **O(1)** for masks or sets (9 rows + 9 cols + 9 boxes, each O(9)).

----------------------------------------

## Step 9: C++ Implementation

**Bitmask version:**

```cpp
bool isValidSudoku(vector<vector<char>>& board) {
    int rows[9] = {0};
    int cols[9] = {0};
    int boxes[9] = {0};

    for (int r = 0; r < 9; ++r) {
        for (int c = 0; c < 9; ++c) {
            if (board[r][c] == '.') continue;
            int d = board[r][c] - '1';   // 0..8
            int bit = 1 << d;
            int b = (r / 3) * 3 + c / 3;

            if ((rows[r] & bit) || (cols[c] & bit) || (boxes[b] & bit)) {
                return false;
            }
            rows[r] |= bit;
            cols[c] |= bit;
            boxes[b] |= bit;
        }
    }
    return true;
}
```

Clean. The "check-then-set" pattern fits every filled cell.

**Hashset version:**

```cpp
bool isValidSudoku(vector<vector<char>>& board) {
    unordered_set<string> seen;
    for (int r = 0; r < 9; ++r) {
        for (int c = 0; c < 9; ++c) {
            char ch = board[r][c];
            if (ch == '.') continue;
            string rowKey = string(1, ch) + "@row" + to_string(r);
            string colKey = string(1, ch) + "@col" + to_string(c);
            string boxKey = string(1, ch) + "@box" + to_string((r / 3) * 3 + c / 3);

            if (!seen.insert(rowKey).second) return false;
            if (!seen.insert(colKey).second) return false;
            if (!seen.insert(boxKey).second) return false;
        }
    }
    return true;
}
```

`insert().second` is false if the key already existed. Neat shorthand for check-and-insert.

----------------------------------------

## Step 10: Follow-up Questions

- **Validate a 4×4 or 16×16 Sudoku variant.** Adjust constants.
- **Check if Sudoku is complete (no empty cells) and valid.** Add a pass to verify no '.'s remain.
- **Return which cell is conflicting.** Modify to output coordinates and value when conflict detected.
- **Count the number of violations.** Don't return on first violation; tally instead.
- **Partial Sudoku validity across updates.** Maintain the masks incrementally: update on each cell change.
- **What if the grid is huge (hypothetical)?** Same algorithm — constant per cell, linear in grid size.
