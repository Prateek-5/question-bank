# Shortest Path in Binary Matrix — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Shortest_Path_in_Binary_Matrix.md`](../Shortest_Path_in_Binary_Matrix.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/shortest-path-in-binary-matrix/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: GRID + UNIT EDGE COSTS + SHORTEST PATH = BFS. The only twist here is 8 directions (not 4). Return -1 if endpoints are blocked or destination is unreachable.**

**Map of this file (9 sections):**

1. Read the problem
2. Why BFS, not DFS
3. Grid-as-graph + 8 directions
4. BFS with distance tracking
5. Code
6. Trace it
7. Common pitfalls
8. Variants — 4-dir, weighted, more state
9. The shape — unweighted grid BFS

---

## 1. Read the problem

Given an `n × n` binary matrix where 0 = open and 1 = blocked, return the **NUMBER OF CELLS** in the shortest path from `(0, 0)` to `(n-1, n-1)` passing only through 0s. **Moves are 8-DIRECTIONAL** (horizontal, vertical, AND diagonal). Return -1 if no path exists.

**Example:**
```
grid = [[0, 0, 0],
        [1, 1, 0],
        [1, 1, 0]]
```

Path: (0,0) → (0,1) → (1,2) → (2,2). 4 cells. Each step uses an 8-direction move; (0,1) → (1,2) is a DIAGONAL step.

**Edge case:** if grid[0][0] or grid[n-1][n-1] is 1 → return -1 immediately.

---

## 2. Why BFS, not DFS

> **Mini-refresher: BFS finds shortest paths when edges have UNIT weight.**
>
> BFS visits nodes in order of increasing distance from the source. The FIRST time it dequeues a node, that's via the shortest path. With unit-weight moves, this gives optimal shortest paths.
>
> DFS goes deep first — it might find the destination via a long route before exploring shorter ones. DFS finds *some* path, not necessarily the shortest.

Every move here costs 1 cell → BFS is the right tool.

---

## 3. Grid-as-graph + 8 directions

Cells are nodes. Two cells are neighbors if they're within the 3×3 box centered on each (excluding the cell itself). Concretely, the 8 offsets:

```
dr = [-1, -1, -1,  0,  0,  1,  1,  1]
dc = [-1,  0,  1, -1,  1, -1,  0,  1]
```

When expanding cell `(r, c)`, generate the 8 candidates `(r + dr[k], c + dc[k])`. Keep only those:
- In bounds: `0 ≤ nr < n`, `0 ≤ nc < n`.
- Open (value 0).
- Unvisited.

---

## 4. BFS with distance tracking

Two equivalent ways to track depth:
- **dist[r][c] matrix**: store distance per cell.
- **Level counter + queue-size snapshots**: process all current-level cells, then increment depth.

I'll use the `dist` matrix — cleaner and supports path recovery if needed later.

```
dist[0][0] = 1                   # 1 cell visited so far
queue = [(0, 0)]
while queue:
    (r, c) = pop front
    if (r, c) == (n-1, n-1): return dist[r][c]
    for each of 8 offsets:
        nr, nc = r + dr, c + dc
        if in bounds, grid[nr][nc] == 0, and not visited:
            dist[nr][nc] = dist[r][c] + 1
            queue.push((nr, nc))
return -1
```

---

## 5. Code

**C++:**

```cpp
int shortestPathBinaryMatrix(vector<vector<int>>& grid) {
    int n = grid.size();
    if (grid[0][0] != 0 || grid[n - 1][n - 1] != 0) return -1;

    vector<vector<int>> dist(n, vector<int>(n, -1));
    queue<pair<int, int>> q;
    q.push({0, 0});
    dist[0][0] = 1;

    int dr[] = {-1, -1, -1, 0, 0, 1, 1, 1};
    int dc[] = {-1,  0,  1, -1, 1, -1, 0, 1};

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

Complexity: **O(n²)** time, **O(n²)** space — each cell processed once with up to 8 neighbors each.

---

## 6. Trace it

```
grid = [[0, 0, 0],
        [1, 1, 0],
        [1, 1, 0]]
n = 3.

dist[0][0] = 1. queue = [(0, 0)].

Pop (0, 0). dist = 1. 8 neighbors:
  (-1,-1), (-1,0), (-1,1): OOB.
  (0,-1): OOB. (0,1): grid=0, unvisited. dist[0][1] = 2, enqueue.
  (1,-1): OOB. (1,0): grid=1, skip. (1,1): grid=1, skip.

queue = [(0, 1)].

Pop (0, 1). dist = 2. Neighbors:
  (-1,*): OOB. (0,0): visited. (0,2): grid=0, unvisited. dist[0][2] = 3, enqueue.
  (1,0): grid=1. (1,1): grid=1. (1,2): grid=0, unvisited. dist[1][2] = 3, enqueue.

queue = [(0, 2), (1, 2)].

Pop (0, 2). Neighbors mostly OOB or visited. (1,1) blocked.

Pop (1, 2). dist = 3. Neighbors:
  (0,1), (0,2): visited. (0,3): OOB.
  (1,1): grid=1, skip. (1,3): OOB.
  (2,1): grid=1, skip. (2,2): grid=0, unvisited. dist[2][2] = 4, enqueue.
  (2,3): OOB.

queue = [(2, 2)].

Pop (2, 2). r == n-1 && c == n-1 → return dist = 4.  ✓
```

The diagonal moves `(0,1) → (1,2)` and `(1,2) → (2,2)` are crucial for the 4-cell path — without diagonals, you'd need at least 5 cells.

---

## 7. Common pitfalls

1. **Returning the number of MOVES instead of CELLS.** The problem asks for visited-cell count, so the source counts as 1 (not 0).
2. **Forgetting to check the endpoints.** If `grid[0][0]` or `grid[n-1][n-1]` is 1, no path exists — return -1 BEFORE starting BFS.
3. **Using DFS.** Finds paths but not necessarily the shortest.
4. **Using only 4 directions.** Misses diagonal shortcuts; gives wrong answer.
5. **Marking visited only on POP, not on PUSH.** Same cell can be pushed multiple times — queue blows up.
6. **Skipping the early-return check when popping the destination.** Still correct, but wastes the last few iterations.

---

## 8. Variants — 4-dir, weighted, more state

| Variant | Algorithm |
|---|---|
| 4-directional moves only | same BFS, 4 offsets |
| Cells have different costs to step on | Dijkstra with min-heap |
| Path must collect keys / pass gates | BFS over expanded state `(r, c, keys)` |
| Knight moves on a chessboard | BFS with 8 knight offsets |
| 0-1 weighted (some moves free) | 0-1 BFS with deque |

The skeleton (queue, visited, neighbor expansion) stays the same — only the state and the move set change.

---

## 9. The shape — unweighted grid BFS

The pattern: **"shortest path on a grid with unit-cost moves = BFS from source until destination is popped."**

> **Mini-refresher: a grid is just a graph in disguise.**
>
> n² cells, up to 8n² edges. BFS is O(V + E) = O(n²). Don't overthink it — write the offsets table, push the source, dequeue and expand.

**Pattern to internalize:**

> "Grid + unit costs + shortest path = BFS. Track dist via a matrix; mark visited on PUSH, not POP."

---

> **Self-check — the question to ask next time.**
>
> When you see "grid, move in 4/8 directions, find shortest path," ask:
>
> > **"Unit cost? Then BFS. Are the endpoints accessible? Are all 8 moves allowed? Mark visited on enqueue."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Shortest_Path_in_Binary_Matrix.md`](../Shortest_Path_in_Binary_Matrix.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Islands.md`](./Number_of_Islands.md), [`01_Matrix.md`](./01_Matrix.md), [`Rotting_Oranges.md`](./Rotting_Oranges.md), [`Shortest_Path_in_an_Undirected_Graph.md`](./Shortest_Path_in_an_Undirected_Graph.md).
  - Coming next: [`Check_if_There_Is_a_Valid_Path_in_a_Graph.md`](./Check_if_There_Is_a_Valid_Path_in_a_Graph.md), [`Course_Schedule_II.md`](./Course_Schedule_II.md).
