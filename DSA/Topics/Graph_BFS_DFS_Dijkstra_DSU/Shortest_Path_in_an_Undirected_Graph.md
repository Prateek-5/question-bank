# Shortest Path in an Undirected Graph

**Problem Link:**
<a href="https://www.geeksforgeeks.org/problems/shortest-path-in-weighted-undirected-graph/1" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/problems/shortest-path-in-weighted-undirected-graph/1</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Frame the Task

You have an **undirected, weighted** graph with `n` nodes (1-indexed) and `m` edges. Edge weights are positive integers. Given a source (1) and destination (n), return the shortest-weight path as a **sequence of nodes**. If no path exists, return `[-1]`.

Two things to produce:
1. The **weight** of the shortest path.
2. The **actual path** (list of nodes from 1 to n).

Example: 5 nodes, edges `{(1,2,2), (2,5,5), (2,3,4), (1,4,1), (4,3,3), (3,5,1)}`. Shortest from 1 to 5?
- 1 → 2 → 5: 2 + 5 = 7.
- 1 → 4 → 3 → 5: 1 + 3 + 1 = 5.
- 1 → 2 → 3 → 5: 2 + 4 + 1 = 7.
- Shortest is **5**, path `[1, 4, 3, 5]`.

----------------------------------------

## Step 2: Which Shortest-Path Algorithm?

- **BFS:** works when all edges have the same weight. Here weights vary — so no.
- **Dijkstra:** works for non-negative weights. Here weights are positive — ✓.
- **Bellman-Ford:** handles negative edges; we don't need that generality, and it's slower.

Dijkstra it is. The twist: we must also recover the path, not just its weight.

----------------------------------------

## Step 3: Dijkstra Reminder

Dijkstra from source `s`:
- `dist[s] = 0`, all others `∞`.
- Min-heap of `(current_distance, node)`.
- Pop the smallest; for each neighbor v of u with edge weight w, if `dist[u] + w < dist[v]`, update `dist[v]` and push (new_dist, v).

After the heap empties, `dist[n]` holds the shortest-path weight.

For path recovery: whenever we relax an edge u → v, record `parent[v] = u`. Then reconstruct by walking from n back through parents.

----------------------------------------

## Step 4: Path Reconstruction

Suppose `parent[v]` stores the predecessor of v on the best path found so far. To rebuild the path from 1 to n:

```
path = []
cur = n
while cur != -1:
    path.append(cur)
    cur = parent[cur]
reverse(path)
```

If `path[0] != 1` (source unreachable, parent chain never reaches the source), no path exists — return `[-1]`.

Important: whenever we update `dist[v]` (find a shorter way), we must also update `parent[v]` to the new predecessor. Otherwise we'd end up with an outdated parent that points to a predecessor on a longer path — wrong reconstruction.

----------------------------------------

## Step 5: Algorithm

```
Build adjacency list from edges (undirected: add both directions).
dist[] = ∞ for all; dist[1] = 0.
parent[] = -1 for all.
heap = [(0, 1)].

while heap not empty:
    (d, u) = pop min.
    if d > dist[u]: skip stale entry.
    for each (v, w) in adj[u]:
        if dist[u] + w < dist[v]:
            dist[v] = dist[u] + w
            parent[v] = u
            push (dist[v], v)

if dist[n] == ∞: return [-1]

Reconstruct path from n by walking parent[].
return path.
```

----------------------------------------

## Step 6: Trace

Graph (undirected, with weights):
- 1 ↔ 2 (2), 1 ↔ 4 (1), 2 ↔ 3 (4), 2 ↔ 5 (5), 3 ↔ 4 (3), 3 ↔ 5 (1).

Initialize: dist = [_, 0, ∞, ∞, ∞, ∞] (ignoring index 0). parent = [_, -1, -1, -1, -1, -1]. heap = [(0, 1)].

```
Pop (0, 1). Neighbors: 2 (w=2), 4 (w=1).
  1 → 2: dist[2] = 2, parent[2] = 1. Push (2, 2).
  1 → 4: dist[4] = 1, parent[4] = 1. Push (1, 4).

Pop (1, 4). Neighbors: 1 (w=1), 3 (w=3).
  4 → 1: 1 + 1 = 2 > dist[1]=0. Skip.
  4 → 3: 1 + 3 = 4 < ∞. dist[3] = 4, parent[3] = 4. Push (4, 3).

Pop (2, 2). Neighbors: 1, 3, 5.
  2 → 3: 2 + 4 = 6 > dist[3]=4. Skip.
  2 → 5: 2 + 5 = 7 < ∞. dist[5] = 7, parent[5] = 2. Push (7, 5).

Pop (4, 3). Neighbors: 2, 4, 5.
  3 → 2: 4 + 4 = 8 > 2. Skip.
  3 → 4: 4 + 3 = 7 > 1. Skip.
  3 → 5: 4 + 1 = 5 < 7. dist[5] = 5, parent[5] = 3. Push (5, 5).

Pop (5, 5). Neighbors: 2, 3.
  5 → 2: 5 + 5 = 10 > 2. Skip.
  5 → 3: 5 + 1 = 6 > 4. Skip.

Pop (7, 5). d=7 > dist[5]=5. Skip stale.

Heap empty.
```

Final: dist[5] = 5. parent = [_, -1, 1, 4, 1, 3].

Reconstruct from 5:
- 5 → parent[5] = 3 → parent[3] = 4 → parent[4] = 1 → parent[1] = -1.
- Reverse: `[1, 4, 3, 5]`. ✓

----------------------------------------

## Step 7: Edge Cases

- **n = 1 (source = destination).** dist[1] = 0. Path is just `[1]`.
- **Disconnected graph, n unreachable.** dist[n] remains ∞. Return `[-1]`.
- **Multiple edges between same pair of nodes.** Dijkstra processes both; the shorter one wins naturally.
- **Self-loops.** Harmless — `dist[u] + w ≥ dist[u]`, so no relaxation happens.

Some variants of this problem expect the **weight** as the first element of the returned list, followed by the path. Check the exact output format.

----------------------------------------

## Step 8: Name It

**Dijkstra's algorithm with parent tracking**. Parent arrays are the standard path-recovery mechanism, used in:
- BFS (unweighted shortest path).
- Dijkstra (non-negative weighted).
- Bellman-Ford (handles negatives).
- A* search (heuristic-guided).

The algorithm itself (computing distances) is often 90% of the work — reconstructing the path is a mechanical afterthought once you've stored predecessors.

----------------------------------------

## Step 9: Complexity

Time: **O((n + m) log n)** with a binary heap.
Space: **O(n + m)** — adjacency list + dist + parent + heap.

----------------------------------------

## Step 10: C++ Implementation

```cpp
vector<int> shortestPath(int n, int m, vector<vector<int>>& edges) {
    vector<vector<pair<int,int>>> adj(n + 1);
    for (auto& e : edges) {
        int u = e[0], v = e[1], w = e[2];
        adj[u].push_back({v, w});
        adj[v].push_back({u, w});   // undirected
    }

    const int INF = INT_MAX;
    vector<int> dist(n + 1, INF), parent(n + 1, -1);
    dist[1] = 0;

    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    pq.push({0, 1});

    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        if (d > dist[u]) continue;   // stale
        for (auto& [v, w] : adj[u]) {
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                parent[v] = u;
                pq.push({dist[v], v});
            }
        }
    }

    if (dist[n] == INF) return {-1};

    vector<int> path;
    for (int cur = n; cur != -1; cur = parent[cur]) path.push_back(cur);
    reverse(path.begin(), path.end());
    return path;
}
```

Three pieces:
1. Adjacency list with undirected edges (both directions).
2. Dijkstra computes `dist` and records `parent` when relaxing.
3. Walk `parent` from n back to source; reverse.

----------------------------------------

## Step 11: Follow-up Questions

- **Return the weight too.** Prepend `dist[n]` to the path.
- **All pairs shortest paths.** Floyd-Warshall in O(n³), or Dijkstra from each source in O(n · (n+m) log n).
- **Negative edges.** Bellman-Ford; Dijkstra breaks.
- **Count shortest paths.** Track `count[v]` alongside `dist[v]`; when dist[v] gets tied, add count[u] instead of overwriting.
- **K-th shortest path.** Yen's algorithm or repeated Dijkstra with detours.
- **Why store parent instead of path lists?** Parent is O(n) space; storing full paths per node would be O(n²).
- **Why is the stale-check `d > dist[u]` needed?** Because we may push multiple entries per node; only the first pop of each is still-valid, the rest have been superseded.
