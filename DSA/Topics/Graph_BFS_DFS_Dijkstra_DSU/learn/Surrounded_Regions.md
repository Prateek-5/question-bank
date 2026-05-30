# Surrounded Regions — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Surrounded_Regions.md`](../Surrounded_Regions.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/surrounded-regions/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/surrounded-regions/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: instead of "find SURROUNDED regions," find their COMPLEMENT — flood-fill from the BOUNDARY.** Cleaner and faster. Same template solves Number of Enclaves. **Read [`Number_of_Islands.md`](./Number_of_Islands.md) first.**

**Map of this file (7 sections):**

1. Read the problem
2. The complement reframing
3. Flood-fill from the boundary
4. Code
5. Trace it
6. Common pitfalls
7. The shape — boundary flood-fill

---

## 1. Read the problem

Given an `m × n` board with `'X'` and `'O'` cells. **Capture** every region of `'O'`s that is SURROUNDED by `'X'`s — flip those `O`s to `X`s. A region is surrounded iff NONE of its `O`s touches the board's boundary.

Modify the board in place.

**Example:**
```
Input:
X X X X
X O O X
X X O X
X O X X

Output:
X X X X
X X X X
X X X X
X O X X
```

The `O` at (3, 1) touches the bottom boundary → its region (just itself) is NOT captured.
The other O-region `{(1,1), (1,2), (2,2)}` is surrounded → flipped to X.

---

## 2. The complement reframing

> **Mini-refresher: SAFE = boundary-reachable; CAPTURED = the rest.**
>
> Instead of "find surrounded regions" (hard to characterize directly), find their COMPLEMENT:
>
> **An `O` is NOT surrounded iff it's reachable from a BOUNDARY O via a path of O's.**
>
> Algorithm:
> 1. Mark all boundary-reachable O's as SAFE (temp marker 'S').
> 2. Flip remaining O's (the surrounded ones) to X.
> 3. Restore 'S' marks back to 'O'.

This negative-space reframing is much cleaner than directly identifying surrounded regions.

---

## 3. Flood-fill from the boundary

Walk the FOUR BORDERS. For each border `O`, flood-fill its component, marking as 'S'.

```
def dfs(r, c):
    if out of bounds or board[r][c] != 'O': return
    board[r][c] = 'S'    # mark safe
    dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)

# Scan all 4 borders
for r in 0..m-1: dfs(r, 0); dfs(r, n-1)
for c in 0..n-1: dfs(0, c); dfs(m-1, c)

# Final cleanup
for r, c:
    if board[r][c] == 'O': board[r][c] = 'X'   # surrounded → flip
    elif board[r][c] == 'S': board[r][c] = 'O' # safe → restore
```

O(mn) time, O(mn) recursion in the worst case.

---

## 4. Code

**C++:**

```cpp
void solve(vector<vector<char>>& board) {
    int m = board.size();
    if (m == 0) return;
    int n = board[0].size();

    function<void(int, int)> dfs = [&](int r, int c) {
        if (r < 0 || c < 0 || r >= m || c >= n) return;
        if (board[r][c] != 'O') return;
        board[r][c] = 'S';
        dfs(r + 1, c); dfs(r - 1, c); dfs(r, c + 1); dfs(r, c - 1);
    };

    for (int r = 0; r < m; ++r) {
        dfs(r, 0); dfs(r, n - 1);
    }
    for (int c = 0; c < n; ++c) {
        dfs(0, c); dfs(m - 1, c);
    }

    for (int r = 0; r < m; ++r) {
        for (int c = 0; c < n; ++c) {
            if (board[r][c] == 'O') board[r][c] = 'X';
            else if (board[r][c] == 'S') board[r][c] = 'O';
        }
    }
}
```

**Python:**

```python
def solve(board):
    if not board: return
    m, n = len(board), len(board[0])
    
    def dfs(r, c):
        if r < 0 or r >= m or c < 0 or c >= n: return
        if board[r][c] != 'O': return
        board[r][c] = 'S'
        dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)
    
    for r in range(m): dfs(r, 0); dfs(r, n-1)
    for c in range(n): dfs(0, c); dfs(m-1, c)
    
    for r in range(m):
        for c in range(n):
            if board[r][c] == 'O': board[r][c] = 'X'
            elif board[r][c] == 'S': board[r][c] = 'O'
```

Complexity: **O(mn) time and space.**

---

## 5. Trace it

```
Initial:
X X X X
X O O X
X X O X
X O X X
```

Step 1 — flood from borders:
- Row 0: all X. Skip.
- Row 3, col 0 = X. Col 1 = O → dfs(3,1): mark 'S'. Neighbors all X. Done.
- Row 3, col 2,3 = X.
- Other borders: all X.

Grid after Step 1:
```
X X X X
X O O X
X X O X
X S X X
```

Step 2 — final cleanup:
- (1,1) = O → X.
- (1,2) = O → X.
- (2,2) = O → X.
- (3,1) = S → O.

Final:
```
X X X X
X X X X
X X X X
X O X X
```
✓

---

## 6. Common pitfalls

1. **Trying to identify SURROUNDED regions directly.** Hard. The COMPLEMENT (boundary-reachable) is easier.

2. **Forgetting to use a temporary marker ('S').** Without it, you can't distinguish "safe O" from "surrounded O" after the flood.

3. **Restoring 'S' to 'O' before flipping 'O' to 'X'.** Order matters! Flip 'O' to 'X' first (or in one pass like the code does).

4. **Diagonal connectivity.** This problem is 4-DIRECTIONAL.

5. **Stack overflow on huge grids.** Use BFS or iterative DFS.

---

## 7. The shape — boundary flood-fill

The pattern:

> **"For 'find ENCLOSED / SURROUNDED regions,' find the COMPLEMENT — flood-fill from the boundary."**

| Problem | What flood-fill finds |
|---|---|
| **This problem** | safe O's (reachable from boundary) |
| Number of Enclaves | land reachable from boundary |
| Pacific Atlantic Water Flow | cells reachable from each ocean |
| Escape the Maze | reachable cells from start |

**Pattern to internalize:**

> "When the question is 'which cells are ENCLOSED?', flood from the OPPOSITE perspective — start at the boundary, mark everything you can reach. The COMPLEMENT is enclosed."

---

## Cross-references

- **Reference card (post-mastery):** [`../Surrounded_Regions.md`](../Surrounded_Regions.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Islands.md`](./Number_of_Islands.md), [`01_Matrix.md`](./01_Matrix.md), [`Rotting_Oranges.md`](./Rotting_Oranges.md).
  - Coming next: [`Number_of_Enclaves.md`](./Number_of_Enclaves.md) — same technique.
