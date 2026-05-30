# Determine Color of a Chessboard Square — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Determine_Color_of_a_Chessboard_Square.md`](../Determine_Color_of_a_Chessboard_Square.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/determine-color-of-a-chessboard-square/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/determine-color-of-a-chessboard-square/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **A pure parity puzzle.** The lesson: **on any checkerboard, the color of `(row, col)` depends only on `(row + col) % 2`.** Knowing this saves you from any case work. The same parity argument generalizes to bipartite grids, knight-tour analyses, and tiling problems.

**Map of this file (8 short sections):**

1. Read the problem
2. The alternation pattern
3. Sum-of-coordinates parity
4. Parsing the input
5. Code
6. Trace it
7. Common pitfalls
8. The shape — parity arguments

---

## 1. Read the problem

You're given a two-character string `coordinates` representing a chessboard square in algebraic notation:
- First character: column letter, `'a'` through `'h'`.
- Second character: row digit, `'1'` through `'8'`.

Return `true` if the square is **WHITE**, `false` if **BLACK**.

**Convention (standard chess):**
- `'a1'` (bottom-left from White's perspective) is **black**.
- `'h1'` (bottom-right) is **white**. "White on the right."
- Colors alternate every step.

**Examples:**

- `"a1"` → black → `false`.
- `"h3"` → white → `true`.
- `"c7"` → black → `false`.

---

## 2. The alternation pattern

> **Mini-refresher: the checkerboard rule.**
>
> Adjacent squares (sharing an edge) ALWAYS have different colors. So:
> - Moving one step horizontally → flip color.
> - Moving one step vertically → flip color.
>
> From `a1` (black), going to `b1` (one step right) flips to white. From `b1` to `b2` (one step up) flips to black. Etc.

Assign coordinates:
- column: `a = 1, b = 2, ..., h = 8`.
- row: `1, 2, ..., 8`.

Let's tabulate:

| Square | col | row | col + row | Color |
|---|---|---|---|---|
| a1 | 1 | 1 | 2 | black |
| b1 | 2 | 1 | 3 | white |
| a2 | 1 | 2 | 3 | white |
| b2 | 2 | 2 | 4 | black |
| h1 | 8 | 1 | 9 | white |
| h8 | 8 | 8 | 16 | black |

**Pattern:** `(col + row)` even → black. `(col + row)` odd → white.

---

## 3. Sum-of-coordinates parity

Why does this work?

Start at `a1 = (1, 1)`, sum = 2 (even), color = black.

Any move (one step horizontally or one step vertically) changes ONE of the two coordinates by 1 — flipping the parity of the sum AND flipping the color.

After `k` total moves (any mix of horizontal and vertical), the parity has flipped `k` times. So `parity == initial XOR k`.

The Manhattan distance from `(1, 1)` to `(col, row)` is `(col - 1) + (row - 1) = col + row - 2`. The parity of this distance equals the parity of `col + row` (subtracting an even constant `-2` doesn't change parity).

So:
- `col + row` even (same parity as `1 + 1 = 2`): SAME COLOR as `a1` (black).
- `col + row` odd: OPPOSITE COLOR (white).

Pure parity reasoning. No special cases.

> **Mini-refresher: parity preservation.**
>
> Adding or subtracting an EVEN number doesn't change parity. Adding/subtracting an ODD number flips it.
>
> XOR-style reasoning often clarifies parity puzzles: each move XORs the "color bit." After k moves, the color bit is XORed k times. If k is even, back to start. If odd, flipped.

---

## 4. Parsing the input

The input string has exactly two characters:
- `s[0]`: a letter `a..h`. Convert to integer column: `s[0] - 'a' + 1`, giving 1 to 8.
- `s[1]`: a digit `1..8`. Convert to integer row: `s[1] - '0'`, giving 1 to 8.

(Strictly we don't need `+ 1` or `- 'a'` adjustments — what matters is the PARITY of the sum, and adjustments by constants don't affect parity. But staying with intuitive 1..8 values is clearer.)

---

## 5. Code

**C++:**

```cpp
bool squareIsWhite(string coordinates) {
    int col = coordinates[0] - 'a' + 1;
    int row = coordinates[1] - '0';
    return (col + row) % 2 == 1;
}
```

**Python:**

```python
def squareIsWhite(coordinates):
    col = ord(coordinates[0]) - ord('a') + 1
    row = int(coordinates[1])
    return (col + row) % 2 == 1
```

**JavaScript:**

```javascript
function squareIsWhite(coordinates) {
    const col = coordinates.charCodeAt(0) - 'a'.charCodeAt(0) + 1;
    const row = parseInt(coordinates[1]);
    return (col + row) % 2 === 1;
}
```

Complexity: **O(1) time, O(1) space.**

> **Mini-refresher: short version using XOR of char codes.**
>
> Since `'a'.charCodeAt() = 97` (odd) and `'1'.charCodeAt() = 49` (odd), the parity of `'a' XOR '1'` is `odd XOR odd = even`, giving a parity-preserving check.
>
> ```javascript
> return (coordinates.charCodeAt(0) + coordinates.charCodeAt(1)) % 2 === 1;
> ```
>
> Works because adding the offsets (97, 48) doesn't change parity. Concise but harder to read.

---

## 6. Trace it

- `"a1"`: col=1, row=1. Sum=2. Even → BLACK. Return false. ✓
- `"h3"`: col=8, row=3. Sum=11. Odd → WHITE. Return true. ✓
- `"c7"`: col=3, row=7. Sum=10. Even → BLACK. Return false. ✓
- `"h8"`: col=8, row=8. Sum=16. Even → BLACK. Return false. ✓ (Top-right corner is opposite color of bottom-right `h1`, which is white. So `h8` is black.)
- `"a8"`: col=1, row=8. Sum=9. Odd → WHITE. ✓

---

## 7. Common pitfalls

1. **Adding `+1` on row by mistake** (`int(s[1]) + 1`). Then the parity flips. Just use `int(s[1])`.

2. **Forgetting to convert characters to integers.** `'a' + '1'` is character arithmetic (gives `'b'` in C++). Use ord values for math.

3. **Returning the inverse.** Read the spec — `true` for white. The convention is `a1 = black`, so check `(col + row) % 2 == 1` for white.

4. **Confusing chess axes** (column vs row, file vs rank). The letter is the column (file); the digit is the row (rank). Don't swap.

5. **Trying to use a lookup table or simulation.** Wasteful. O(1) parity is the clean answer.

6. **Treating the row as 0-indexed.** It's 1-indexed in chess notation. Adjusting it to 0-indexed flips parity for every square — wrong answer for every input.

---

## 8. The shape — parity arguments

The pattern: **`(row + col) % 2`** is the universal CHECKERBOARD coloring formula.

| Problem | Where it appears |
|---|---|
| **This problem** | direct |
| Knight's tour problems | knight ALWAYS moves between opposite colors (knight's L-shape flips parity) |
| Domino tiling | each domino covers 1 black + 1 white; tiling impossible if counts unequal |
| Bipartite grid 2-coloring | the parity IS the 2-coloring |
| Game of Life parity invariants | certain patterns preserve parity |
| Path finding on a chessboard | parity tells you reachable destinations |
| Light-Out puzzles | parity-based invariants determine solvability |

**Pattern to internalize:**

> "Whenever you see a grid with ALTERNATING properties (color, type, label), reach for `(row + col) % 2`. It often replaces complex case work with a one-line parity check."

---

> **Self-check — the question to ask next time.**
>
> When you face a grid with alternating cells, ask:
>
> > **"Does `(row + col) % 2` (or some similar parity) capture the alternation directly?"**
>
> If yes, you've turned case work into O(1) arithmetic.

---

## Cross-references

- **Reference card (post-mastery):** [`../Determine_Color_of_a_Chessboard_Square.md`](../Determine_Color_of_a_Chessboard_Square.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Add_Digits.md`](./Add_Digits.md) — another O(1) closed-form puzzle.
  - Coming next: [`Count_of_Matches_in_Tournament.md`](./Count_of_Matches_in_Tournament.md), Day_of_the_Week.
