# Rotting Oranges

**Problem Link:**
https://leetcode.com/problems/rotting-oranges/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Picture the Problem

You have an `m × n` grid where each cell is:
- `0` — empty
- `1` — fresh orange
- `2` — rotten orange

Every minute, any **fresh** orange that's 4-directionally adjacent to a **rotten** orange becomes rotten. Return the minimum number of minutes until there are no fresh oranges. If impossible, return -1.

Example:
```
2 1 1
1 1 0
0 1 1
```

Minute 0: the single rotten orange is at (0, 0).
Minute 1: adjacent fresh oranges at (0, 1) and (1, 0) become rotten.
Minute 2: their adjacent fresh oranges rot: (0, 2), (1, 1).
Minute 3: (2, 1) becomes rotten (adjacent to (1, 1)).
Minute 4: (2, 2) becomes rotten (adjacent to (2, 1)).

Total minutes: 4.

----------------------------------------

## Step 2: Think Physically

This is an infection-spreading problem. Rot is a disease; each minute, it spreads outward one step from every currently-rotten cell. We're asked: after how many minutes is everyone infected?

Mathematically, this is **minimum-distance-to-any-source** — for each fresh orange, how far is it (in 4-connected steps) from the *nearest* rotten orange? The answer to the whole question is the maximum of those distances (because we have to wait for the farthest one to rot).

But instead of computing distances from every rotten source individually (expensive), we notice that **all rotten oranges spread at the same rate simultaneously**. That's the cue for something called **multi-source BFS** — we'll derive it in a moment.

----------------------------------------

## Step 3: Single-Source Warm-Up

If there were only one rotten orange, we'd do a standard BFS from it, recording the distance to each cell. That distance is the minute when that cell rots. The overall answer is the max distance (among cells that originally had fresh oranges).

```
BFS from single source:
  q = [(source_r, source_c)]
  dist[source_r][source_c] = 0
  while q:
    (r, c) = q.pop_front()
    for each 4-direction neighbor (nr, nc):
      if in bounds and dist[nr][nc] not set:
        dist[nr][nc] = dist[r][c] + 1
        q.push((nr, nc))
```

This computes distances from the source to every reachable cell.

Now what if there are multiple rotten oranges at the start? We could run BFS from each, collect per-cell nearest-distances, and take max. That's O((n·m)²) — expensive.

Better idea: run BFS from **all sources at once**.

----------------------------------------

## Step 4: Why Multi-Source BFS Is a Thing

The BFS queue respects levels — nodes at distance k are dequeued before nodes at distance k+1. If we seed the queue with all sources at distance 0, the BFS naturally expands outward from all of them simultaneously. The first time a cell is reached, its distance is its **minimum distance from any source** — because BFS visits cells in increasing order of distance.

So the algorithm is:

1. Scan the grid. Enqueue every initially rotten orange with time 0. Count the fresh oranges.
2. BFS. Each time we rot a neighboring fresh orange, record its time = parent's time + 1. Track the maximum.
3. At the end:
   - If we rotted every fresh orange, the answer is the max time observed.
   - If any remain fresh, return -1 (they were unreachable — surrounded by empty cells).

----------------------------------------

## Step 5: Trace on the Example

Grid:
```
2 1 1
1 1 0
0 1 1
```

Initial scan: rotten at (0,0). Fresh: (0,1), (0,2), (1,0), (1,1), (2,1), (2,2) — that's 6 fresh.

Queue: `[(0, 0, time=0)]`.

```
Pop (0, 0, 0). Neighbors:
  (1, 0) fresh → rot, time 1. Enqueue. Fresh count 5.
  (0, 1) fresh → rot, time 1. Enqueue. Fresh count 4.
Queue: [(1,0,1), (0,1,1)].

Pop (1, 0, 1). Neighbors:
  (2, 0) empty — skip.
  (1, 1) fresh → rot, time 2. Fresh 3.
  (0, 0) already rotten — skip.
Pop (0, 1, 1). Neighbors:
  (0, 0) rotten — skip.
  (0, 2) fresh → rot, time 2. Fresh 2.
  (1, 1) already rotted — skip.
Queue: [(1,1,2), (0,2,2)].

Pop (1, 1, 2). Neighbors:
  (2, 1) fresh → rot, time 3. Fresh 1.
  (1, 0) rotten. (0, 1) rotten. (1, 2) empty.
Pop (0, 2, 2). Neighbors:
  (1, 2) empty. (0, 1) rotten.
Queue: [(2,1,3)].

Pop (2, 1, 3). Neighbors:
  (2, 0) empty. (2, 2) fresh → rot, time 4. Fresh 0.
  (1, 1) rotten.
Queue: [(2,2,4)].

Pop (2, 2, 4). Neighbors all rotten or out-of-bounds.
Queue empty.
```

Fresh count = 0, max time = 4. Return **4**. ✓

If any cell had been fresh at the end (say, isolated by empty cells), the BFS wouldn't have reached it, and we'd return -1.

----------------------------------------

## Step 6: Why Multi-Source Gives Correct Results

**Claim:** the time at which a fresh cell is rotted equals the Manhattan-distance-constrained minimum path length to any initially-rotten cell.

BFS from a single source gives distances from that source. BFS from multiple sources simultaneously gives, for each cell, the minimum of its distances from each source — because BFS dequeues cells in order of their distance from the initial queue, and "initial queue" contains all sources at distance 0. The first time a cell is dequeued (or assigned a distance), it's at the minimum distance from the set of sources.

So each fresh cell's time is its minimum distance from any rotten cell. The overall answer is the maximum across all fresh cells, which is the time when the *last* fresh cell rots. That's what the problem asks.

----------------------------------------

## Step 7: Complexity

Time: every cell is visited at most once. **O(m · n)**.

Space: the queue can hold up to O(m · n) cells. **O(m · n)**.

We don't need a separate distance matrix — we can record the time directly in the queue entries or mutate the grid. I've used queue entries here for clarity.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int orangesRotting(vector<vector<int>>& g) {
    int m = g.size(), n = g[0].size();
    queue<tuple<int,int,int>> q;     // (r, c, time)
    int fresh = 0;

    for (int r = 0; r < m; ++r)
        for (int c = 0; c < n; ++c) {
            if (g[r][c] == 2) q.push({r, c, 0});
            else if (g[r][c] == 1) fresh++;
        }

    int maxTime = 0;
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
    while (!q.empty()) {
        auto [r, c, t] = q.front(); q.pop();
        maxTime = max(maxTime, t);
        for (int k = 0; k < 4; ++k) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nc < 0 || nr >= m || nc >= n) continue;
            if (g[nr][nc] != 1) continue;   // empty or already rotten
            g[nr][nc] = 2;
            fresh--;
            q.push({nr, nc, t + 1});
        }
    }

    return fresh == 0 ? maxTime : -1;
}
```

A subtle implementation choice: I mutate the grid (`g[nr][nc] = 2`). That doubles as "already visited" because we only enqueue cells that are still fresh. Clean.

----------------------------------------

## Step 9: Follow-up Questions

- **What if spread is 8-directional (including diagonals)?** Add 4 more neighbor offsets. Logic unchanged.
- **Variable spread rate per cell (some cells take 2 minutes to rot).** Use Dijkstra instead of BFS — distances aren't all 1 anymore.
- **What if there are multiple sources of different colors (say, rot and freeze)?** Multi-source BFS still works, but you need to track which type reached each cell first.
- **Minimum cost to rot all oranges if you can place one more rotten at time 0.** Try placing at every empty cell and pick the best — O(m·n) BFS runs unless you can be clever.
- **What if the grid is enormous and we only need an approximate answer?** Downsample or use heuristic search.
