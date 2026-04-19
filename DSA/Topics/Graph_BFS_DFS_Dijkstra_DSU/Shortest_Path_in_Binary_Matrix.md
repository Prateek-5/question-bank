# Shortest Path in Binary Matrix

**Problem Link:**
https://leetcode.com/problems/shortest-path-in-binary-matrix/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Parse the Rules

Given an `n × n` binary matrix (cells are 0 or 1), find the length of the shortest path from top-left `(0, 0)` to bottom-right `(n-1, n-1)`. The path must go through **only 0s** and can move in **8 directions** (up, down, left, right, and the four diagonals). Return the number of cells visited (including both endpoints), or -1 if no path exists.

Example:
```
0 0 0
1 1 0
1 1 0
```

From (0,0) to (2,2): the only 0s are in the top row and right column. Path: (0,0) → (0,1) → (0,2) → (1,2) → (2,2) — 5 cells. Or a diagonal shortcut: (0,0) → (1,1)? But (1,1) is 1. Blocked.

Try: (0,0) → (0,2) diagonally? Not allowed — diagonals move by 1 cell, not 2.

So the answer is 4 cells taking the direct 8-direction path: (0,0) → (0,1) → (1,2) → (2,2). Four cells. Let me verify each is 0: (0,0)=0, (0,1)=0, (1,2)=0, (2,2)=0. ✓ Length 4.

----------------------------------------

## Step 2: What Kind of Graph Is This?

Each cell is a node. Each cell has up to 8 neighbors (the 8 adjacent cells in all directions). A neighbor is "reachable" if it's inside the grid and holds 0.

All edges have **unit weight** (every move costs 1 cell). We want the shortest path from source to destination — classic unweighted shortest path.

When edges are unweighted, the ideal algorithm is **BFS**. BFS visits nodes in non-decreasing order of distance from the source, so the first time we dequeue the destination, we've found the shortest path.

----------------------------------------

## Step 3: BFS on a Grid — Nothing Fancy

The algorithm:
1. If `grid[0][0]` or `grid[n-1][n-1]` is 1, return -1 (blocked at endpoints).
2. Start BFS from (0, 0). Distance to (0, 0) is 1 (counting it).
3. For each dequeued cell, expand to all 8 neighbors that are in-bounds, equal to 0, and not yet visited. Mark them with distance `currentDist + 1`.
4. When we visit (n-1, n-1), return its distance.
5. If BFS exhausts without reaching destination, return -1.

Standard. The only wrinkle specific to this problem is the 8-direction neighbor set (instead of the usual 4).

----------------------------------------

## Step 4: Trace Quickly

Grid:
```
0 0 0
1 1 0
1 1 0
```

n = 3. Start BFS from (0,0). dist[0][0] = 1. Queue: [(0,0)].

Dequeue (0,0). 8 neighbors:
- (-1,-1), (-1,0), (-1,1), (-1,-2): out of bounds.
- (0,-1), (0,1): (0,-1) OOB. (0,1): in bounds, 0, unvisited. Set dist=2. Push.
- (1,-1), (1,0), (1,1): (1,-1) OOB. (1,0)=1, skip. (1,1)=1, skip.

Queue: [(0,1)].

Dequeue (0,1). dist=2. Neighbors of (0,1):
- (-1,0), (-1,1), (-1,2): OOB.
- (0,0): already visited. (0,2): 0, unvisited. Set dist=3. Push.
- (1,0), (1,1): both 1. (1,2): 0, unvisited. Set dist=3. Push.

Queue: [(0,2), (1,2)].

Dequeue (0,2). Neighbors: (1,1)=1 skip. (1,2) visited. (1,3) OOB. Nothing new.

Dequeue (1,2). Neighbors:
- (0,1), (0,2), (0,3): (0,3) OOB, others visited.
- (1,1)=1 skip. (1,3) OOB.
- (2,1), (2,2), (2,3): (2,1)=1 skip. (2,2)=0, unvisited. Set dist=4. Push. (2,3) OOB.

Destination reached! `dist[2][2] = 4`. Return 4.

Matches expected. ✓

----------------------------------------

## Step 5: Why BFS Guarantees Shortest Path

BFS explores cells in a "ripple" — first all cells at distance 1 from source, then distance 2, then 3, and so on. Because all edges have the same cost (1), the first time a cell is reached is via the shortest path.

If we used DFS instead, we might hit the destination via a long winding route before finding the short one. DFS can still find *a* path, but not necessarily the shortest.

----------------------------------------

## Step 6: Implementation Details

Two common approaches to tracking distance:
- **Separate dist[][] matrix.** Explicit, clean, but uses extra memory.
- **Overwrite the grid in place.** Abuse the grid: mark visited cells with a special value. Saves memory but modifies the input.

I'll use the dist-matrix approach for clarity.

Alternative: track the BFS level via queue-size snapshots (no dist matrix needed — increment a counter per level).

----------------------------------------

## Step 7: Name It

We used **unweighted grid BFS with 8-directional movement**. Variants of this pattern solve:
- Standard grid shortest paths (4-directional).
- Snakes and Ladders.
- Minesweeper (reveal cells).
- Word Ladder (words as nodes, edit-distance-1 as edges).

When edges have non-uniform weights, replace BFS with Dijkstra. When you need to track an additional state (like "keys collected"), expand the state space.

----------------------------------------

## Step 8: Complexity

Time: each cell is processed at most once; each has up to 8 neighbors. **O(n²)** (where the grid is n×n, so there are n² cells).

Space: **O(n²)** for the distance matrix and BFS queue.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int shortestPathBinaryMatrix(vector<vector<int>>& grid) {
    int n = grid.size();
    if (grid[0][0] != 0 || grid[n - 1][n - 1] != 0) return -1;

    vector<vector<int>> dist(n, vector<int>(n, -1));
    queue<pair<int, int>> q;
    q.push({0, 0});
    dist[0][0] = 1;

    int dr[] = {-1, -1, -1, 0, 0, 1, 1, 1};
    int dc[] = {-1, 0, 1, -1, 1, -1, 0, 1};

    while (!q.empty()) {
        auto [r, c] = q.front(); q.pop();
        if (r == n - 1 && c == n - 1) return dist[r][c];
        for (int k = 0; k < 8; ++k) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nr >= n || nc < 0 || nc >= n) continue;
            if (grid[nr][nc] != 0) continue;
            if (dist[nr][nc] != -1) continue;
            dist[nr][nc] = dist[r][c] + 1;
            q.push({nr, nc});
        }
    }
    return -1;
}
```

Details:
- The 8-direction offset arrays `dr[]` and `dc[]` cover all 8 neighbors compactly.
- We check start and end aren't blocked before starting BFS — saves effort on impossible inputs.
- `dist[nr][nc] != -1` acts as the "visited" check; we only enqueue unvisited cells.
- We can return early when we dequeue the destination.

----------------------------------------

## Step 10: Follow-up Questions

- **4-directional movement instead of 8.** Same algorithm, use only 4 neighbors.
- **Find the shortest path's coordinates (not just length).** Track parent pointers during BFS; reconstruct by walking back.
- **Weighted cells (different costs to step on each).** Switch from BFS to Dijkstra with a min-heap keyed by total cost.
- **Limited fuel / turn constraints.** State becomes (cell, fuel_left) or (cell, turn_parity).
- **Allow teleportation between pairs of special cells.** Add teleport edges to the graph; BFS handles.
- **Bidirectional BFS for speed.** Expand from both endpoints; meet in the middle.
