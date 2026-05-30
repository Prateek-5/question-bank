# Surrounded Regions

**Problem Link:**
<a href="https://leetcode.com/problems/surrounded-regions/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/surrounded-regions/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Decode the Problem

You have a matrix of `'X'` and `'O'`. Capture any region of `'O'`s that is **completely surrounded by X's** — meaning flip those `O`s to `X`s. A region is "surrounded" iff no `O` in it touches the board's boundary.

Modify the board in place.

Example:
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

The `O` at (3, 1) is on the bottom row (boundary), so its region (just itself) is *not* captured. The other `O` region `{(1,1), (1,2), (2,2)}` is fully enclosed by X's, so it gets flipped to X.

----------------------------------------

## Step 2: A Negative-Space Reframing

Instead of "find surrounded regions," ask: **which `O`s are NOT surrounded**?

An `O` is not surrounded iff it's **reachable from some boundary `O`** via a path of O's. Because:
- If the O sits on the boundary, it's trivially not surrounded.
- If the O connects to a boundary O via other Os, it's also not surrounded — the chain touches the edge.

Everything else (O's not reachable from the boundary) **is** surrounded, and must flip to X.

This reframing is much easier to implement. Just:
1. Identify all O's reachable from any boundary O. Mark them (say, temporarily to 'S').
2. Flip all unmarked O's to X.
3. Restore the marked 'S's back to 'O'.

Much simpler than explicitly enumerating "closed regions."

----------------------------------------

## Step 3: The Algorithm

```
Step 1: Scan the boundary. For each cell on the border that is 'O',
        flood-fill it (and its connected O's) to 'S' (safe marker).

Step 2: Walk every cell. If it's 'O', flip to 'X' (it was unreachable from the border).
        If it's 'S', restore to 'O'.
```

Two passes plus the flood-fill. All linear in the grid size.

----------------------------------------

## Step 4: Trace on the Example

```
X X X X
X O O X
X X O X
X O X X
```

Step 1: scan boundary.
- Row 0: all X's. Skip.
- Row 3: (3, 0) X, (3, 1) O — border O. Flood-fill to S.
  The O at (3, 1) has neighbors: (2, 1) X, (3, 0) X, (3, 2) X. No O neighbors. Only (3, 1) itself becomes S.
- (3, 2), (3, 3): X.
- Columns 0 and 3: already scanned via rows 0 and 3, all X except (3, 1) which is already an S. No other border Os.

Grid after Step 1:
```
X X X X
X O O X
X X O X
X S X X
```

Step 2: walk every cell.
- O cells: (1, 1), (1, 2), (2, 2) → flip to X.
- S cell: (3, 1) → restore to O.

Final:
```
X X X X
X X X X
X X X X
X O X X
```
✓

----------------------------------------

## Step 5: Why "Reachable from Boundary" Is Exactly "Not Surrounded"

**Claim:** An O-region is "surrounded" iff none of its cells touch the boundary.

**Proof sketch:** A region's O's are all connected. If any one is on the boundary, the region isn't fully enclosed — it reaches out. If none are on the boundary, every edge of the region is adjacent to an X or out-of-bounds (but "out-of-bounds" can't happen since no cell of the region is on the boundary) → every edge is adjacent to an X → surrounded.

So boundary-reachable = not surrounded. Negate that for what we want to flip.

----------------------------------------

## Step 6: Flood Fill Details

Use DFS or BFS from each border O. Mark cells as 'S' (or any temporary marker) so we don't flip them in step 2.

DFS version:
```
def dfs(r, c):
    if r out of bounds, c out of bounds, or board[r][c] != 'O': return
    board[r][c] = 'S'
    dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)
```

Iterate the border:
```
for r in 0..m-1:
    dfs(r, 0); dfs(r, n-1)
for c in 0..n-1:
    dfs(0, c); dfs(m-1, c)
```

BFS is equally fine; just use a queue.

----------------------------------------

## Step 7: Name It

We used **flood fill** (DFS or BFS), seeded from the **boundary**. The technique:
1. Start from "known safe" cells.
2. Expand to connected cells, marking them safe.
3. At the end, what remains unmarked is the complement — the cells we want to modify.

This **complement reasoning** shows up often. Examples:
- Number of Enclaves (same technique, just count instead of flip).
- Pacific Atlantic Water Flow (two flood fills from two boundaries).
- Escape Large Maze.

Whenever "surrounded" or "enclosed" is the constraint, flood-fill from the boundary is typically the cleanest attack.

----------------------------------------

## Step 8: Complexity

Time: each cell is visited O(1) times across the flood fills. Plus one O(m·n) scan at the end. Total **O(m · n)**.
Space: O(m · n) for recursion or queue in the worst case (if the entire grid is one big O region).

----------------------------------------

## Step 9: C++ Implementation

```cpp
void solve(vector<vector<char>>& board) {
    int m = board.size();
    if (m == 0) return;
    int n = board[0].size();

    function<void(int, int)> dfs = [&](int r, int c) {
        if (r < 0 || c < 0 || r >= m || c >= n) return;
        if (board[r][c] != 'O') return;
        board[r][c] = 'S';     // mark safe
        dfs(r + 1, c);
        dfs(r - 1, c);
        dfs(r, c + 1);
        dfs(r, c - 1);
    };

    // Step 1: flood fill from all border O's.
    for (int r = 0; r < m; ++r) {
        dfs(r, 0);
        dfs(r, n - 1);
    }
    for (int c = 0; c < n; ++c) {
        dfs(0, c);
        dfs(m - 1, c);
    }

    // Step 2: final cleanup.
    for (int r = 0; r < m; ++r) {
        for (int c = 0; c < n; ++c) {
            if (board[r][c] == 'O') board[r][c] = 'X';        // was isolated
            else if (board[r][c] == 'S') board[r][c] = 'O';   // was safe
        }
    }
}
```

Key details:
- Use a temporary marker ('S') to distinguish safe O's from soon-to-be-flipped O's.
- Two loops for step 1: one for left/right boundary columns, one for top/bottom rows.
- Step 2 iterates all cells, applying the flip/restore based on the marker.

For deep grids, recursion could overflow the stack. Switch to BFS with a queue if that's a concern.

----------------------------------------

## Step 10: Follow-up Questions

- **Count surrounded regions (not flip).** Count the number of connected components of O's that have **no** boundary cell. Use DFS/BFS with a "touches boundary" flag.
- **Capture regions within regions (nested).** The problem as stated is a single pass, but multi-level capture would be harder.
- **Diagonal connectivity.** Add diagonal neighbors to the flood fill.
- **Multiple characters involved (X, O, Y, Z, ...).** Apply similar boundary-flood to each character type.
- **Grid is very large / distributed.** Segmented flood fills with boundary messaging.
- **Why mark 'S' rather than use a separate visited matrix?** Saves O(m·n) auxiliary space. Cost: we must restore afterward.
