# Spiral Matrix II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Spiral_Matrix_II.md`](../Spiral_Matrix_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/spiral-matrix-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/spiral-matrix-ii/</a>

---

## How to use this file

Paced for someone seeing the problem for the first time. Reading time: ~25 minutes. This problem teaches **direction vectors** — a tiny coding idiom that unlocks every grid-walking problem (DFS/BFS on grids, simulations, robot/snake puzzles, board games). Spend the time here; you'll reuse this idiom dozens of times.

**Map of this file (11 short sections):**

1. Read the problem (visual)
2. The shape of a spiral
3. How do I make the algorithm "turn"?
4. Direction vectors — the encoding
5. Cycling through directions (the `% 4` trick)
6. The two turn conditions
7. The full algorithm
8. Trace it for `n = 3`
9. The boundary-shrinking alternative
10. Code (both versions)
11. Pitfalls + the shape (direction vectors transfer)

---

## 1. Read the problem (visual)

Given a positive integer `n`, build an `n × n` matrix filled with the integers `1` through `n²` in **spiral order**, starting at the top-left and walking **clockwise inward**.

`n = 3`:

```
1  2  3
8  9  4
7  6  5
```

`n = 4`:

```
 1  2  3  4
12 13 14  5
11 16 15  6
10  9  8  7
```

`n = 1`: just `[[1]]`.

Trace the numbers `1, 2, 3, ...` on the `n = 3` grid in order. You'll see them go:

- right across the top row (`1, 2, 3` at row 0),
- down the right column (`4, 5` at column 2),
- left across the bottom row (`6, 7` at row 2),
- up the left column (`8` at column 0),
- then the center (`9`).

Same pattern at every scale, spiraling inward until everything is filled.

---

## 2. The shape of a spiral

A spiral is **a sequence of four-segment loops**, each loop one "layer" of the matrix.

```
Layer 1 (outermost) walks the perimeter of the n×n matrix:
   ─→─→─→─→
   ↑       ↓
   ↑       ↓
   ←─←─←─←─

Layer 2 walks the perimeter of an inner (n-2)×(n-2) matrix.
Layer 3 walks an (n-4)×(n-4) perimeter, and so on.
```

We could code this directly — "do the right edge, then bottom edge, then left edge, then top edge, then shrink and repeat" — and that's the **boundary-shrinking** approach we'll cover in section 9.

But there's a more elegant way that scales beautifully to any grid-walking problem: **track a single position and a direction, and turn when blocked**. That's the approach we'll build first.

---

## 3. How do I make the algorithm "turn"?

We're going to walk one cell at a time, writing `1, 2, 3, ...` as we go. The walker has:

- A **position** `(r, c)` — current row and column.
- A **direction** it's facing — right, down, left, or up.

Each step:

1. Write the current number at `mat[r][c]`.
2. Compute where we'd go next if we kept walking in the same direction.
3. **If that next cell is out-of-bounds OR already filled**, we can't keep going — turn clockwise.
4. Move to the (possibly new direction's) next cell.
5. Increment the number.

The walker turns exactly when the spiral needs to turn — at the corners and the moments it would otherwise re-enter the already-spiraled region.

The key question now: **how do we encode a "direction" so that "step forward" and "turn clockwise" are simple operations?**

---

## 4. Direction vectors — the encoding

> **Mini-refresher: direction vectors.**
>
> Instead of storing direction as a string like `"right"` or an enum like `RIGHT`, we store it as a **pair of small integers** `(dr, dc)` that describe how `r` and `c` change when we step forward.
>
> The four cardinal directions:
>
> ```
> Direction       (dr, dc)      What it means
> ───────────     ────────      ─────────────────────────────
> right           (0, +1)       row stays the same; column +1
> down            (+1, 0)       row +1; column stays the same
> left            (0, -1)       row stays; column -1
> up              (-1, 0)       row -1; column stays
> ```
>
> "Step forward" is then just `r = r + dr; c = c + dc`. One pair of additions, regardless of which direction we're facing. That's the magic of direction vectors.

So with this encoding, taking one step is:

```
nr = r + dr
nc = c + dc
```

Easy.

> **Why those particular numbers?** Look at the matrix coordinate convention: `r` increases as you go down, `c` increases as you go right. So "right" must mean `c` goes up by 1 → `(0, +1)`. "Down" means `r` goes up by 1 → `(+1, 0)`. The minus signs for "left" and "up" follow.

---

## 5. Cycling through directions (the `% 4` trick)

We need to "turn clockwise." Right → down → left → up → right → ...

Store the four directions in an array, in **clockwise order**:

```
dr = [0, 1, 0, -1]    # right, down, left, up
dc = [1, 0, -1, 0]
```

Keep an index `dir` (initial value `0` for "right"). The current direction's deltas are `(dr[dir], dc[dir])`.

> **Mini-refresher: the `% 4` modular cycling trick.**
>
> To turn clockwise, we want `dir` to advance through `0 → 1 → 2 → 3 → 0 → 1 → ...`. After `up` (index 3), the next direction is `right` (index 0) — i.e., the count wraps around.
>
> The expression **`dir = (dir + 1) % 4`** does exactly that:
>
> ```
> dir = 0  →  (0 + 1) % 4 = 1
> dir = 1  →  (1 + 1) % 4 = 2
> dir = 2  →  (2 + 1) % 4 = 3
> dir = 3  →  (3 + 1) % 4 = 0   ← wraps!
> ```
>
> The `%` operator gives "remainder after dividing." Dividing by 4 always gives a remainder in `0, 1, 2, 3` — exactly our valid direction indices. So `% 4` "snaps back" any out-of-range index.
>
> This is the universal cycling idiom. To cycle through `k` states, use `(state + 1) % k`.

---

## 6. The two turn conditions

When does the walker need to turn?

**Condition A: the next cell would be OUT OF BOUNDS.** If we're at row 0 walking up, the next row would be `-1`, which doesn't exist. Time to turn.

**Condition B: the next cell is ALREADY FILLED.** When we've completed the outer layer and we're starting the next inner layer, continuing straight would walk us back onto a cell we already wrote a number into. That cell isn't `0` anymore — it has a number. Time to turn.

Both conditions are needed. Let me show why:

- Only checking out-of-bounds: We'd happily overwrite filled cells in the middle of the matrix when the spiral wants to start its inner loop. → wrong output.
- Only checking already-filled: When the spiral hits the edge of the matrix (e.g., the very first turn from the top row to the right column), it goes out of bounds before any cell is "filled with the next loop's stuff." We'd crash trying to read/write a bad index.

The full check:

```
nr = r + dr[dir]
nc = c + dc[dir]
if nr < 0 OR nr >= n OR nc < 0 OR nc >= n OR mat[nr][nc] != 0:
    # can't keep going — turn clockwise
    dir = (dir + 1) % 4
    nr = r + dr[dir]
    nc = c + dc[dir]
```

The line "`mat[nr][nc] != 0`" relies on the fact that we initialize the matrix to all zeros, and every cell we write gets a non-zero number (since we're writing `1` through `n²`). So `mat[nr][nc] != 0` means "already filled."

---

## 7. The full algorithm

```
mat = n × n matrix, all zeros
r, c = 0, 0                 # start at top-left
dir = 0                     # facing right
dr = [0, 1, 0, -1]
dc = [1, 0, -1, 0]

for num in 1..n*n:
    mat[r][c] = num         # write the current number

    nr = r + dr[dir]        # tentative next cell
    nc = c + dc[dir]

    if out of bounds OR mat[nr][nc] != 0:
        dir = (dir + 1) % 4  # turn clockwise
        nr = r + dr[dir]
        nc = c + dc[dir]

    r, c = nr, nc            # move to the next cell

return mat
```

The loop runs exactly `n²` times — once per cell. After placing `num = n*n`, the loop exits and we return.

Important detail: after writing `num = n*n` (the very last placement), we still compute a "next cell." That computation may even point at an invalid cell. But we never USE that next cell — the loop ends. So it's harmless.

---

## 8. Trace it for `n = 3`

We start: `mat` is all zeros, `(r, c) = (0, 0)`, `dir = 0` (right).

Direction vectors: `dr = [0, 1, 0, -1]`, `dc = [1, 0, -1, 0]`.

```
num = 1:
    mat[0][0] = 1.
    Next: (0+0, 0+1) = (0, 1). In bounds. mat[0][1] = 0 (empty).
    No turn. r, c = 0, 1.

num = 2:
    mat[0][1] = 2.
    Next: (0, 2). In bounds, empty. r, c = 0, 2.

num = 3:
    mat[0][2] = 3.
    Next: (0, 3). OUT OF BOUNDS (col 3 ≥ n=3). TURN.
    dir = (0 + 1) % 4 = 1 (down).
    Recompute next: (0 + 1, 2 + 0) = (1, 2). In bounds, empty. r, c = 1, 2.

num = 4:
    mat[1][2] = 4.
    Next: (2, 2). In bounds, empty. r, c = 2, 2.

num = 5:
    mat[2][2] = 5.
    Next: (3, 2). OUT OF BOUNDS (row 3 ≥ n=3). TURN.
    dir = (1 + 1) % 4 = 2 (left).
    Recompute next: (2 + 0, 2 + (-1)) = (2, 1). In bounds, empty. r, c = 2, 1.

num = 6:
    mat[2][1] = 6.
    Next: (2, 0). In bounds, empty. r, c = 2, 0.

num = 7:
    mat[2][0] = 7.
    Next: (2, -1). OUT OF BOUNDS (col -1 < 0). TURN.
    dir = (2 + 1) % 4 = 3 (up).
    Recompute next: (2 + (-1), 0 + 0) = (1, 0). In bounds, empty. r, c = 1, 0.

num = 8:
    mat[1][0] = 8.
    Next: (0, 0). In bounds, BUT mat[0][0] = 1 (already filled). TURN.
    dir = (3 + 1) % 4 = 0 (right).
    Recompute next: (1 + 0, 0 + 1) = (1, 1). In bounds, empty. r, c = 1, 1.

num = 9:
    mat[1][1] = 9.
    Next: (1, 2). mat[1][2] = 4 (already filled). TURN.
    (turn doesn't matter — loop ends)
    
Loop done.
```

Final matrix:

```
1  2  3
8  9  4
7  6  5
```

✓ Matches the expected output. Notice how `num = 8` triggered a turn because of the **already-filled** condition (the out-of-bounds wasn't the issue there — both turn conditions were needed).

---

## 9. The boundary-shrinking alternative

The direction-vector version is the most flexible, but there's a second, more declarative approach: **track four boundaries** (top row, bottom row, left column, right column) and write each edge of the rectangle in its own loop, then shrink the boundaries inward.

```
top = 0, bottom = n - 1, left = 0, right = n - 1
num = 1
while top <= bottom AND left <= right:
    # walk top edge left → right
    for c in left..right:  mat[top][c] = num++;   top++

    # walk right edge top → bottom
    for r in top..bottom:  mat[r][right] = num++; right--

    # walk bottom edge right → left
    if top <= bottom:                   # in case middle row was just consumed
        for c in right..left:  mat[bottom][c] = num++; bottom--

    # walk left edge bottom → top
    if left <= right:                   # in case middle column was just consumed
        for r in bottom..top:  mat[r][left] = num++; left++
```

Each iteration of the outer `while` writes one full perimeter of the current rectangle, then shrinks all four boundaries. When the rectangle collapses to nothing, we stop.

**The two `if` guards** at the bottom and left edges handle the case where, after walking the top and right edges, the remaining rectangle has degenerated (e.g., for an odd `n`, the final layer is a single middle cell — we'd otherwise write to it twice).

Comparison of the two approaches:

| Aspect | Direction-vector | Boundary-shrinking |
|---|---|---|
| Lines of code | ~10 | ~15 |
| Mental model | "walker with eyes — turn when blocked" | "rectangle peeled layer by layer" |
| Generalizes to | hexagonal grids, snake games, BFS, DFS, any direction-aware walk | only rectangles |
| Off-by-one risk | low (the turn rule handles it) | medium (the inner-edge guards) |
| Easiest to debug | check `mat` after each step | check boundary values after each layer |

Both produce identical output. Pick by taste.

---

## 10. Code (both versions)

**Direction-vector version (C++):**

```cpp
vector<vector<int>> generateMatrix(int n) {
    vector<vector<int>> mat(n, vector<int>(n, 0));
    int dr[] = {0, 1, 0, -1};
    int dc[] = {1, 0, -1, 0};
    int r = 0, c = 0, dir = 0;

    for (int num = 1; num <= n * n; num++) {
        mat[r][c] = num;

        int nr = r + dr[dir];
        int nc = c + dc[dir];

        // turn if next cell is out of bounds OR already filled
        if (nr < 0 || nr >= n || nc < 0 || nc >= n || mat[nr][nc] != 0) {
            dir = (dir + 1) % 4;
            nr = r + dr[dir];
            nc = c + dc[dir];
        }

        r = nr;
        c = nc;
    }

    return mat;
}
```

**Boundary-shrinking version (C++):**

```cpp
vector<vector<int>> generateMatrix(int n) {
    vector<vector<int>> mat(n, vector<int>(n, 0));
    int top = 0, bottom = n - 1, left = 0, right = n - 1;
    int num = 1;

    while (top <= bottom && left <= right) {
        for (int c = left; c <= right; c++) mat[top][c] = num++;
        top++;

        for (int r = top; r <= bottom; r++) mat[r][right] = num++;
        right--;

        if (top <= bottom) {
            for (int c = right; c >= left; c--) mat[bottom][c] = num++;
            bottom--;
        }

        if (left <= right) {
            for (int r = bottom; r >= top; r--) mat[r][left] = num++;
            left++;
        }
    }

    return mat;
}
```

Both are **O(n²)** time (we write each of the `n²` cells once with O(1) work) and **O(n²)** space (just the output matrix).

---

## 11. Pitfalls + the shape

### Common pitfalls

1. **Forgetting to check "already filled" in the direction-vector approach.** You'll seg-fault or get wrong output. Both turn conditions are needed.

2. **Using `mat[nr][nc] != 0` when 0 is a valid output value.** In Spiral Matrix II it's not (we fill with `1..n²`), but if the problem's outputs include 0, use a sentinel like `-1` or a separate `visited` matrix.

3. **Off-by-one in the `% 4` direction.** Make sure your `dr`, `dc` arrays match the **clockwise** order: right, down, left, up. Swapping any two breaks the spiral.

4. **In the boundary-shrinking version, forgetting the inner `if` guards.** For odd `n`, the inner loops will overwrite a cell (or attempt to). Always guard `if (top <= bottom)` and `if (left <= right)` before the second pair of edges.

5. **Allocating a matrix of the wrong default value.** `vector<vector<int>>(n, vector<int>(n, 0))` is critical — the "already filled" check relies on initial 0s.

### The shape — where direction vectors transfer

Direction vectors are one of the most reused idioms in problem-solving. Any time you "walk a grid":

| Problem | Direction count | Notes |
|---|---|---|
| **Spiral Matrix II** | 4 | this problem |
| Spiral Matrix I (read order) | 4 | same algorithm, read instead of write |
| **Number of Islands** (flood fill) | 4 | enumerate neighbors |
| Knight's Tour | 8 | knight moves: `dr = [-2,-2,-1,-1,1,1,2,2]`, `dc = [-1,1,-2,2,-2,2,-1,1]` |
| Shortest Path in Binary Matrix | 8 | including diagonals |
| Rotting Oranges | 4 | BFS neighbors |
| Word Search | 4 | DFS neighbors |
| Snake game simulation | 4 | direction changes per input |

The **idiom to internalize**:

```cpp
int dr[] = {/* row deltas in your direction order */};
int dc[] = {/* col deltas */};
for (int k = 0; k < dr.length; k++) {
    int nr = r + dr[k], nc = c + dc[k];
    // do something with neighbor (nr, nc)
}
```

This 4-line skeleton handles "for each neighbor" cleanly. No `if/else` chains for each direction. No bugs from typos. Once you have it in muscle memory, grid problems get a LOT easier.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem that involves **walking, traversing, or filling a grid in some pattern**, before writing nested loops for each direction, ask:
>
> > **"Can I express the movement as direction vectors `(dr, dc)`? If yes, can I unify all directions into a single `for k` loop?"**
>
> If yes, your code shrinks by 3–4× and bug surface area drops dramatically. This is the single most important idiom for grid problems.

---

## Cross-references

- **Reference card (post-mastery):** [`../Spiral_Matrix_II.md`](../Spiral_Matrix_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:** [`Matrix_Diagonal_Sum.md`](./Matrix_Diagonal_Sum.md) (warm-up index-formula problem)
- **Coming later (same idiom):** Number of Islands, Rotting Oranges, Word Search — all use direction vectors.
