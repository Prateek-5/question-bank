# 01 Matrix — Teaching Walkthrough

> **Reference card (post-mastery):** [`../01_Matrix.md`](../01_Matrix.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/01-matrix/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **A canonical MULTI-SOURCE BFS problem.** The lesson: **for "distance to nearest 0," seed BFS with ALL 0s simultaneously.** Each 1 receives its min distance from any 0 automatically. **Read [`Rotting_Oranges.md`](./Rotting_Oranges.md) first.**

**Map of this file (7 sections):**

1. Read the problem
2. The naive approach (and why it's too slow)
3. The perspective flip — flood from 0s outward
4. Code
5. Trace it
6. Common pitfalls
7. The shape

---

## 1. Read the problem

Given an `m × n` binary matrix `mat`, return a matrix of the same shape where each cell holds its DISTANCE TO THE NEAREST `0` (4-directional steps).

`0`-cells have distance 0.

**Example:**
```
mat:
0 0 0
0 1 0
1 1 1

Output:
0 0 0
0 1 0
1 2 1
```

(2,1) is at distance 2 from the nearest 0 — e.g., (1, 0) or (1, 2).

---

## 2. The naive approach (and why it's too slow)

For each 1-cell, BFS to find the nearest 0. O((mn)²) — too slow for m=n=10³.

We need O(mn).

---

## 3. The perspective flip — flood from 0s outward

> **Mini-refresher: invert the question.**
>
> Instead of "for each 1, find nearest 0," ask: "for each 0, what 1s are at distance 1, 2, 3, ...?"
>
> Seed BFS with ALL 0s simultaneously (distance 0). Expand outward. The first time a 1 is reached, that's its min distance from any 0.

```
dist[i][j] = 0 if mat[i][j] == 0 else INF
queue = all (i, j) where mat[i][j] == 0

while queue:
    (r, c) = queue.popleft()
    for each 4-neighbor (nr, nc) with dist[nr][nc] == INF:
        dist[nr][nc] = dist[r][c] + 1
        queue.append((nr, nc))

return dist
```

O(mn) time, O(mn) space.

---

## 4. Code

**C++:**

```cpp
vector<vector<int>> updateMatrix(vector<vector<int>>& mat) {
    int m = mat.size(), n = mat[0].size();
    const int INF = INT_MAX;
    vector<vector<int>> dist(m, vector<int>(n, INF));
    queue<pair<int, int>> q;

    for (int r = 0; r < m; ++r) {
        for (int c = 0; c < n; ++c) {
            if (mat[r][c] == 0) {
                dist[r][c] = 0;
                q.push({r, c});
            }
        }
    }

    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};

    while (!q.empty()) {
        auto [r, c] = q.front(); q.pop();
        for (int k = 0; k < 4; ++k) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nc < 0 || nr >= m || nc >= n) continue;
            if (dist[nr][nc] != INF) continue;
            dist[nr][nc] = dist[r][c] + 1;
            q.push({nr, nc});
        }
    }

    return dist;
}
```

**Python:**

```python
from collections import deque

def updateMatrix(mat):
    m, n = len(mat), len(mat[0])
    dist = [[float('inf')] * n for _ in range(m)]
    q = deque()
    for r in range(m):
        for c in range(n):
            if mat[r][c] == 0:
                dist[r][c] = 0
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and dist[nr][nc] == float('inf'):
                dist[nr][nc] = dist[r][c] + 1
                q.append((nr, nc))
    return dist
```

Complexity: **O(mn) time, O(mn) space.**

---

## 5. Trace it

```
mat:
0 0 0
0 1 0
1 1 1
```

Initial dist:
```
0 0 0
0 ∞ 0
∞ ∞ ∞
```

Queue: all 0s = `[(0,0), (0,1), (0,2), (1,0), (1,2)]`.

Process (0,0): no INF neighbors.
Process (0,1): (1,1) = INF → dist=1, enqueue.
Process (0,2): no INF.
Process (1,0): (2,0) = INF → dist=1, enqueue.
Process (1,2): (2,2) = INF → dist=1, enqueue.

Process (1,1): (2,1) = INF → dist=2, enqueue.
Process (2,0): (2,1) already set.
Process (2,2): (2,1) already set.

Process (2,1): no INF neighbors.

Final:
```
0 0 0
0 1 0
1 2 1
```
✓

---

## 6. Common pitfalls

1. **Single-source BFS from each 1.** O((mn)²) TLE. Use multi-source.

2. **Forgetting to seed ALL 0s.** Missing some 0 in the initial queue means some 1s get over-estimated distance.

3. **Updating dist AFTER pop instead of BEFORE enqueue.** Causes duplicate enqueues.

4. **Not initializing 0-cells to dist=0.** They need to be in the queue with distance 0 to propagate correctly.

5. **DFS instead of BFS.** DFS doesn't give shortest distance. Use BFS.

---

## 7. The shape

> **"For 'distance to NEAREST member of set S' on a grid, use multi-source BFS seeded with all members of S."**

| Problem | Set S |
|---|---|
| **This problem** | 0-cells |
| Rotting Oranges | rotten cells |
| Walls and Gates | gates |
| As Far From Land As Possible | land cells |
| Map of Highest Peak | water cells |

---

## Cross-references

- **Reference card (post-mastery):** [`../01_Matrix.md`](../01_Matrix.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Rotting_Oranges.md`](./Rotting_Oranges.md).
  - Coming next: [`Surrounded_Regions.md`](./Surrounded_Regions.md), [`Number_of_Enclaves.md`](./Number_of_Enclaves.md).
