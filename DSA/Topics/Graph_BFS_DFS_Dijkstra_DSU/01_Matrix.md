# 01 Matrix

**Problem Link:**
<a href="https://leetcode.com/problems/01-matrix/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/01-matrix/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Understand the Output

You have a matrix of 0s and 1s. For each cell, output the **distance to the nearest 0** (using 4-directional steps).

Example input:
```
0 0 0
0 1 0
1 1 1
```

Cell-by-cell:
- Row 0: all 0s, distance 0 for each. Output row: `0 0 0`.
- Row 1: `0 ? 0`. The `1` at (1, 1) is adjacent to multiple 0s, distance 1.
- Row 2: `1 1 1`. Distances?
  - (2, 0): nearest 0 is (1, 0), distance 1.
  - (2, 1): nearest 0? (1, 0) distance 2, (1, 2) distance 2, (0, 0) distance 3, etc. Nearest = 2.
  - (2, 2): nearest 0 is (1, 2), distance 1.

Output:
```
0 0 0
0 1 0
1 2 1
```

----------------------------------------

## Step 2: Naïve Thinking

For each cell holding a 1, search for the nearest 0 via BFS from that cell. If the matrix is m × n with many 1s, this is O(m·n · m·n) = O((m·n)²) — far too slow.

Clearly we need something that processes the matrix once, not once per 1-cell.

----------------------------------------

## Step 3: Flip the Perspective

Instead of "for each 1, find the nearest 0," ask: "what if we start at every 0 simultaneously and spread outward?"

This is **multi-source BFS**. The insight: all 0s have distance 0. When we spread from them in lockstep, each 1-cell gets its distance from the nearest 0 — because BFS naturally visits cells in order of increasing distance, and starting from all 0s means the first time a cell is reached is the shortest distance from *any* 0.

Start state: queue contains all 0-cells, each with distance 0.
Expand: for each cell in the queue, check its 4 neighbors. If a neighbor is unvisited, set its distance to current + 1 and enqueue.

When done, every cell has its correct distance.

----------------------------------------

## Step 4: Why Multi-Source BFS Is Correct

In standard BFS from one source, we get the shortest distance from that source. In multi-source BFS (queue seeded with multiple starting points), we get the shortest distance from **any** source — because the first wave visits all sources, and subsequent waves spread simultaneously from all frontiers.

Formally: let f(v) = min distance from v to any source. Multi-source BFS computes exactly f.

----------------------------------------

## Step 5: Algorithm

```
Initialize a `dist` matrix with:
  dist[i][j] = 0 if mat[i][j] == 0
  dist[i][j] = UNVISITED otherwise

queue = [(i, j) for each cell with mat[i][j] == 0]

while queue is non-empty:
    (r, c) = queue.pop()
    for each neighbor (nr, nc) in 4 directions:
        if in bounds and dist[nr][nc] == UNVISITED:
            dist[nr][nc] = dist[r][c] + 1
            queue.push((nr, nc))

return dist
```

Seed queue with all 0-cells; BFS outward.

----------------------------------------

## Step 6: Trace on the Example

Input:
```
0 0 0
0 1 0
1 1 1
```

Initial `dist`:
```
0 0 0
0 ? 0
? ? ?
```
Queue: all 0-positions. `(0,0), (0,1), (0,2), (1,0), (1,2)`.

Round 1: pop each, look at neighbors.
- (0,0): neighbors (1,0) and (0,1) are already 0. No new cells.
  Actually wait — (1,0) has dist 0, not unvisited. OK.
- (0,1): neighbors (0,0), (0,2), (1,1). (1,1) is unvisited, set dist=1, enqueue.
- (0,2), (1,0), (1,2): similarly, they all try to update (1,1), but it's already set.
  - (1,0): neighbor (2,0) unvisited. Set dist=1, enqueue.
  - (1,2): neighbor (2,2) unvisited. Set dist=1, enqueue.

Queue now: `(1,1), (2,0), (2,2)` (all with dist 1).

Round 2:
- (1,1): neighbors (0,1), (2,1), (1,0), (1,2). All visited except (2,1). Set dist(2,1) = 2, enqueue.
- (2,0): neighbors (1,0), (2,1). (2,1) now visited. No new.
- (2,2): neighbors (1,2), (2,1). (2,1) visited. No new.

Queue now: `(2,1)`.

Round 3:
- (2,1): neighbors (1,1), (2,0), (2,2). All visited. Done.

Queue empty. Final dist:
```
0 0 0
0 1 0
1 2 1
```
✓

----------------------------------------

## Step 7: Why Multi-Source Is Correct — More Intuitively

Imagine you're a 0-cell (a "firefighter"), and every fire is a 1-cell. All firefighters move at 1 step per minute. When does fire at (r, c) get extinguished? When the nearest firefighter reaches it. That's the shortest Manhattan distance to any 0.

Multi-source BFS simulates this race perfectly.

This technique generalizes. Whenever a problem says "distance to the nearest of a set of sources," multi-source BFS is the answer.

----------------------------------------

## Step 8: Name It

**Multi-Source BFS** (or BFS from multiple starting points). The pattern:
1. Queue all sources at the start.
2. BFS as usual.
3. Result: distance from each cell to the nearest source.

Variants:
- **Rotting Oranges**: multi-source BFS where sources are rotten oranges.
- **Walls and Gates**: multi-source BFS from gates (0 cells) to rooms.
- **Shortest Bridge**: multi-source BFS starting from one island to find shortest path to another.

Whenever you see "distance to nearest X" for multiple X's in a grid, this pattern fits.

----------------------------------------

## Step 9: Complexity

Time: every cell is enqueued and dequeued once. **O(m · n)**.
Space: O(m · n) for the distance matrix and the queue.

Versus the naïve O((m·n)²), this is a huge win.

----------------------------------------

## Step 10: C++ Implementation

```cpp
vector<vector<int>> updateMatrix(vector<vector<int>>& mat) {
    int m = mat.size(), n = mat[0].size();
    const int UNVISITED = INT_MAX;
    vector<vector<int>> dist(m, vector<int>(n, UNVISITED));
    queue<pair<int, int>> q;

    // Seed queue with all 0-cells.
    for (int r = 0; r < m; ++r) {
        for (int c = 0; c < n; ++c) {
            if (mat[r][c] == 0) {
                dist[r][c] = 0;
                q.push({r, c});
            }
        }
    }

    int dr[] = {-1, 1, 0, 0};
    int dc[] = {0, 0, -1, 1};

    while (!q.empty()) {
        auto [r, c] = q.front(); q.pop();
        for (int k = 0; k < 4; ++k) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nc < 0 || nr >= m || nc >= n) continue;
            if (dist[nr][nc] != UNVISITED) continue;
            dist[nr][nc] = dist[r][c] + 1;
            q.push({nr, nc});
        }
    }

    return dist;
}
```

Implementation notes:
- Use `UNVISITED = INT_MAX` as a sentinel. Only 1-cells will still hold it after initialization.
- The `dist[nr][nc] != UNVISITED` check doubles as "visited" tracking.
- 4-directional movement via offset arrays.

----------------------------------------

## Step 11: Follow-up Questions

- **Distance to nearest specific character (not necessarily 0).** Generalize the seeding condition.
- **8-directional distance.** Replace 4-offset arrays with 8.
- **Weighted cells (different traversal costs).** Use Dijkstra instead of BFS.
- **Diagonal and straight-line distances differ.** Again, use weighted BFS or Dijkstra.
- **Huge sparse grid.** BFS works; consider hash-based visited tracking if the grid is defined lazily.
- **Dynamic: 1s and 0s can change.** Hard problem — need incremental algorithms.
