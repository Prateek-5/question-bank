# Number of Islands

**Problem Link:**
<a href="https://leetcode.com/problems/number-of-islands/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/number-of-islands/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Read the Problem

You have an `m × n` grid of `'1'` (land) and `'0'` (water). An **island** is a group of land cells connected horizontally or vertically (4-directional). Water bounds the grid edges effectively. Count how many distinct islands there are.

Tiny example:
```
1 1 0
0 1 0
0 0 1
```

Reading it by eye: the top-left 1s at (0,0), (0,1), and (1,1) are all touching (horizontally/vertically) — that's one island. The lone 1 at (2,2) is another. Total: **2 islands**.

----------------------------------------

## Step 2: How Would a Human Solve This?

If I pointed at a grid on paper and asked you to count islands, what would you do?

You'd probably pick a `1` you haven't crossed out yet, trace all its connected `1`s with your finger, cross them out, and count `+1`. Then repeat until no `1`s remain.

That's the algorithm in plain English. Two things need clarifying:

1. **"Trace all connected 1s"** — visit every cell reachable via adjacent `1`s.
2. **"Cross them out"** — mark visited cells so we don't count the same island twice.

That's literally all we need. No fancy theory, just paper-and-pencil reasoning mechanized.

----------------------------------------

## Step 3: How Do We "Trace" Programmatically?

When we stand on a cell, we want to visit all 4 neighbors that are `1` and unvisited, then recursively do the same from each of them. That's **depth-first search (DFS)** — but that label isn't what matters. What matters is the behavior: "from here, spread to adjacent land cells, repeat."

We can write it recursively:

```cpp
void flood(vector<vector<char>>& g, int r, int c) {
    if (r < 0 || c < 0 || r >= (int)g.size() || c >= (int)g[0].size()) return;
    if (g[r][c] != '1') return;   // water or already visited
    g[r][c] = '0';                 // mark visited (by converting to water)
    flood(g, r+1, c);
    flood(g, r-1, c);
    flood(g, r, c+1);
    flood(g, r, c-1);
}
```

One trick worth noticing: instead of a separate `visited` matrix, I'm mutating the grid itself — converting `'1'` to `'0'` when visited. This saves memory but mutates the input, which is sometimes acceptable and sometimes not (check the problem's conventions).

----------------------------------------

## Step 4: The Outer Loop

Now the main algorithm. Scan every cell. When we find a `'1'` we haven't yet flooded, call `flood` and increment the island count. The `flood` function will sink the entire island to `'0'`, so we won't count it again when we encounter its other cells.

```cpp
int numIslands(vector<vector<char>>& g) {
    int islands = 0;
    for (int r = 0; r < (int)g.size(); ++r) {
        for (int c = 0; c < (int)g[0].size(); ++c) {
            if (g[r][c] == '1') {
                islands++;
                flood(g, r, c);
            }
        }
    }
    return islands;
}
```

That's the whole solution. Four nested directions inside a DFS, wrapped by a scan-the-grid outer loop.

----------------------------------------

## Step 5: Dry Run on the Tiny Example

```
Grid:
1 1 0
0 1 0
0 0 1
```

Outer loop iterates (r,c) from (0,0) to (2,2).

```
(0,0): g=1. islands=1. flood(0,0):
  mark g[0][0]=0.
  flood(1,0): g[1][0]=0. return.
  flood(-1,0): out of bounds. return.
  flood(0,1): g[0][1]=1. mark g[0][1]=0.
    flood(1,1): g[1][1]=1. mark g[1][1]=0.
      flood(2,1): g[2][1]=0. return.
      flood(0,1): g[0][1]=0 now. return.
      flood(1,2): g[1][2]=0. return.
      flood(1,0): g[1][0]=0. return.
    flood(-1,1): OOB. return.
    flood(0,2): g[0][2]=0. return.
    flood(0,0): g[0][0]=0. return.
  flood(0,-1): OOB. return.
After (0,0) flood: grid is
  0 0 0
  0 0 0
  0 0 1

(0,1) through (2,1): all 0, skip.
(2,2): g=1. islands=2. flood(2,2):
  mark g[2][2]=0. All neighbors OOB or 0. Return.

End. islands = 2.
```

Matches our hand count.

----------------------------------------

## Step 6: BFS Instead of DFS — Same Idea, Different Walk

DFS recurses deep. For very large islands, recursion can blow the stack (imagine a 1000x1000 grid that's all 1s — 10^6 recursive calls deep). Safer is BFS with an explicit queue:

```cpp
void flood_bfs(vector<vector<char>>& g, int sr, int sc) {
    int m = g.size(), n = g[0].size();
    queue<pair<int,int>> q;
    q.push({sr, sc});
    g[sr][sc] = '0';
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    while (!q.empty()) {
        auto [r, c] = q.front(); q.pop();
        for (int k = 0; k < 4; ++k) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nc < 0 || nr >= m || nc >= n) continue;
            if (g[nr][nc] != '1') continue;
            g[nr][nc] = '0';
            q.push({nr, nc});
        }
    }
}
```

Whether BFS or DFS, each cell is visited once. The count of islands doesn't depend on traversal order — only on which cells are connected.

----------------------------------------

## Step 7: Giving It a Name (at Last)

This is a **connected-components** problem, and we solved it via flood-fill. If you squint, the grid is an implicit graph: each land cell is a node; edges connect horizontally/vertically adjacent land cells. The number of islands = the number of connected components in that graph.

You could also use **Union-Find (DSU)** here: initially each land cell is its own component, merge horizontally/vertically adjacent land cells, count distinct roots. That's often overkill for a one-shot query but becomes essential when land cells are added over time (dynamic connectivity).

Again — we didn't start from "this is a flood-fill problem" or "this is a connected-components problem". We started from "how would I count islands on paper?" and the algorithm emerged.

----------------------------------------

## Step 8: Complexity

Time: every cell is visited at most a constant number of times (once by the outer loop, once by flood). **O(m · n)**.

Space: in the DFS version, the recursion stack depth can be up to m · n in the worst case (one giant island). In the BFS version, the queue can hold up to m · n cells. **O(m · n)** worst case.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class Solution {
    int m, n;
    void flood(vector<vector<char>>& g, int r, int c) {
        if (r < 0 || c < 0 || r >= m || c >= n || g[r][c] != '1') return;
        g[r][c] = '0';
        flood(g, r+1, c);
        flood(g, r-1, c);
        flood(g, r, c+1);
        flood(g, r, c-1);
    }
public:
    int numIslands(vector<vector<char>>& g) {
        m = g.size(); n = g[0].size();
        int islands = 0;
        for (int r = 0; r < m; ++r)
            for (int c = 0; c < n; ++c)
                if (g[r][c] == '1') { islands++; flood(g, r, c); }
        return islands;
    }
};
```

----------------------------------------

## Step 10: Follow-up Questions

- **Largest island by area.** Instead of counting, have `flood` return the size of the island; track the max.
- **8-directional connectivity (include diagonals).** Add four more neighbor offsets. The algorithm is unchanged otherwise.
- **Grid updates: land added dynamically, answer queries after each add.** Switch to Union-Find — on each add, merge with any adjacent land cells and maintain a component count. Queries are O(α(n)) per update.
- **Can't mutate the grid.** Use a separate `visited[m][n]` boolean matrix — O(m·n) extra space, otherwise identical.
- **Count islands that touch the border.** Do DFS only starting from border `1`s; count those sources.
- **Shape-based island counting (distinct shapes).** Normalize each island's cell coordinates (canonical form) and hash — count distinct hashes.
