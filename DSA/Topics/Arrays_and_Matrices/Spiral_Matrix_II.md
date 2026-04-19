# Spiral Matrix II

**Problem Link:**
https://leetcode.com/problems/spiral-matrix-ii/

**Topic:**
Arrays & Matrices

----------------------------------------

## Step 1: What Does the Output Look Like?

Given an integer n, produce an `n × n` matrix filled with numbers `1` through `n²` arranged in a **spiral pattern** starting at top-left, moving right, then down, then left, then up, repeatedly — shrinking inward.

For n = 3:
```
1 2 3
8 9 4
7 6 5
```

Trace the numbers 1..9 in order on the grid: 1 at (0,0), 2 at (0,1), 3 at (0,2) — that's "right along the top row." Then 4 at (1,2), 5 at (2,2) — "down the right column." Then 6 at (2,1), 7 at (2,0) — "left along the bottom row." Then 8 at (1,0) — "up the left column." Finally 9 at (1,1) — the center.

For n = 4:
```
 1  2  3  4
12 13 14  5
11 16 15  6
10  9  8  7
```

Same spiral shape, scaled up.

----------------------------------------

## Step 2: Structure of a Spiral

A spiral visits the perimeter of the matrix, then shrinks inward to the perimeter of an (n-2) × (n-2) matrix, and so on. On each "layer" we walk right, down, left, up — four segments per layer (the last layer might have fewer segments if it's 1x1 or 1xn or nx1).

Tracking a spiral requires keeping track of **which direction we're facing** and **when to turn**.

----------------------------------------

## Step 3: Two Natural Approaches

**Approach A: Boundary shrinking.** Maintain four pointers: top, bottom, left, right. Each "loop iteration" fills one full rectangle perimeter and then shrinks boundaries.

**Approach B: Direction vector + turn rule.** Maintain a position (r, c) and a direction (dr, dc). At each step, try to advance in the current direction. If the next cell is out of bounds or already filled, turn clockwise.

Both work. B is slightly more elegant — it's fewer explicit loops and generalizes naturally to non-square spirals. A is more direct — easier to trace by eye.

I'll go with B because the "turn when you hit a wall or filled cell" rule is a fun pattern.

----------------------------------------

## Step 4: Direction Cycling

The four directions in clockwise order: right, down, left, up. As (dr, dc) pairs:
- Right: (0, 1)
- Down: (1, 0)
- Left: (0, -1)
- Up: (-1, 0)

When we turn clockwise, the next direction follows the cycle. Keeping an index `dir = 0..3` and using `dir = (dir + 1) % 4` advances through the cycle.

----------------------------------------

## Step 5: The Algorithm

```
mat = n × n zero matrix
r, c = 0, 0
dir = 0   # start facing right
directions = [(0,1), (1,0), (0,-1), (-1,0)]

for num in 1..n²:
    mat[r][c] = num
    nr, nc = r + dr[dir], c + dc[dir]
    # turn if next cell is out-of-bounds or already filled
    if nr < 0 or nr >= n or nc < 0 or nc >= n or mat[nr][nc] != 0:
        dir = (dir + 1) % 4
        nr, nc = r + dr[dir], c + dc[dir]
    r, c = nr, nc

return mat
```

Each iteration places one number, then decides the next cell. The turn rule "if out of bounds or already filled, rotate clockwise" naturally traces the spiral because:
- Along a straight run, the next cell is in-bounds and empty — keep going.
- At a corner, continuing straight would either leave the grid or hit a previously filled cell — turn.

Notice that after filling `n²` numbers, the matrix is complete. We don't need to worry about the "next cell" being invalid after the last placement, because the loop ends.

----------------------------------------

## Step 6: Trace for n = 3

Initial mat all zeros. Position (0, 0). Direction 0 (right).

```
num=1: mat[0][0]=1.
  Next: (0,1). In bounds, mat[0][1]=0. Keep direction.
  r,c=0,1.

num=2: mat[0][1]=2.
  Next: (0,2). In bounds, empty. r,c=0,2.

num=3: mat[0][2]=3.
  Next: (0,3). Out of bounds. Turn. dir=1 (down).
  New next: (1,2). In bounds, empty. r,c=1,2.

num=4: mat[1][2]=4.
  Next: (2,2). In bounds, empty. r,c=2,2.

num=5: mat[2][2]=5.
  Next: (3,2). OOB. Turn. dir=2 (left).
  New next: (2,1). In bounds, empty. r,c=2,1.

num=6: mat[2][1]=6.
  Next: (2,0). In bounds, empty. r,c=2,0.

num=7: mat[2][0]=7.
  Next: (2,-1). OOB. Turn. dir=3 (up).
  New next: (1,0). In bounds, empty. r,c=1,0.

num=8: mat[1][0]=8.
  Next: (0,0). mat[0][0]=1 (filled). Turn. dir=0 (right).
  New next: (1,1). In bounds, empty. r,c=1,1.

num=9: mat[1][1]=9.
  (loop ends — we've placed all 9)
```

Final:
```
1 2 3
8 9 4
7 6 5
```

✓ Matches.

Notice the turn at num=8: the "out of bounds" check wasn't the issue; it was the "already filled" check (cell (0,0) has 1).

----------------------------------------

## Step 7: Why Both Turn Conditions Matter

If we only turned on out-of-bounds, we'd fail at num=8 → (0,0): (0,0) is in bounds, so we'd happily overwrite it with 8. Wrong.

If we only turned on "already filled," we'd fail at num=3 → (0,3): (0,3) is out of bounds, not "filled," so we wouldn't turn and we'd try to write to a bad index (segfault).

Both conditions together correctly implement "turn whenever we can't go straight."

----------------------------------------

## Step 8: Boundary-Shrinking Alternative

The other approach — tracking four boundaries (top, bottom, left, right) — avoids the "already filled" check entirely:

```
top, bottom, left, right = 0, n-1, 0, n-1
num = 1
while top <= bottom and left <= right:
    for c in left..right: mat[top][c] = num++; top++
    for r in top..bottom: mat[r][right] = num++; right--
    if top <= bottom:
        for c in right..left step -1: mat[bottom][c] = num++; bottom--
    if left <= right:
        for r in bottom..top step -1: mat[r][left] = num++; left++
```

Four inner loops per layer. The `if` guards at the bottom-left and left-up segments handle the case where the inner rectangle degenerates (e.g., for odd n, a single middle cell).

Both versions are ~15 lines. The direction-vector version is slightly more flexible if you ever need non-rectangular spirals (hexagonal, etc.).

----------------------------------------

## Step 9: Complexity

Time: we place exactly `n²` numbers with O(1) work each. **O(n²)**.
Space: **O(n²)** for the output matrix (unavoidable — that's what we're producing).

----------------------------------------

## Step 10: C++ Implementation — Boundary-Shrinking Version

```cpp
vector<vector<int>> generateMatrix(int n) {
    vector<vector<int>> mat(n, vector<int>(n, 0));
    int top = 0, bottom = n - 1, left = 0, right = n - 1;
    int num = 1;
    while (top <= bottom && left <= right) {
        for (int c = left; c <= right; ++c) mat[top][c] = num++;
        top++;
        for (int r = top; r <= bottom; ++r) mat[r][right] = num++;
        right--;
        if (top <= bottom) {
            for (int c = right; c >= left; --c) mat[bottom][c] = num++;
            bottom--;
        }
        if (left <= right) {
            for (int r = bottom; r >= top; --r) mat[r][left] = num++;
            left++;
        }
    }
    return mat;
}
```

Direction-vector version (for comparison):

```cpp
vector<vector<int>> generateMatrix(int n) {
    vector<vector<int>> mat(n, vector<int>(n, 0));
    int dr[] = {0, 1, 0, -1};
    int dc[] = {1, 0, -1, 0};
    int r = 0, c = 0, dir = 0;
    for (int num = 1; num <= n * n; ++num) {
        mat[r][c] = num;
        int nr = r + dr[dir], nc = c + dc[dir];
        if (nr < 0 || nr >= n || nc < 0 || nc >= n || mat[nr][nc] != 0) {
            dir = (dir + 1) % 4;
            nr = r + dr[dir];
            nc = c + dc[dir];
        }
        r = nr; c = nc;
    }
    return mat;
}
```

----------------------------------------

## Step 11: Follow-up Questions

- **Spiral Matrix I (read a spiral from an existing matrix).** Same traversal pattern, but read instead of write.
- **Rectangular (non-square) spiral, m × n.** Both approaches adapt — the boundary version just uses different bounds.
- **Spiral starting from the center and going out.** Reverse the order or trace inward-to-outward.
- **Diagonal or zigzag traversals.** Different direction patterns; similar structural tricks.
- **3D spiral (through a cube).** Multidimensional extension; direction-vector approach generalizes more cleanly.
- **Fill with a custom sequence rather than 1..n².** Replace `num++` with your sequence generator.
