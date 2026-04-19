# Minimum Weight Cycle

**Problem Link:**
https://www.geeksforgeeks.org/problems/minimum-weight-cycle/1

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: What Is a Cycle's Weight?

In a weighted undirected graph, a **cycle** is a closed walk visiting distinct vertices (except start = end). A cycle's **weight** is the sum of its edge weights.

Goal: find the minimum-weight cycle in the graph. If no cycle exists, return -1 (or some sentinel).

Example graph: edges `(1-2, 5), (2-3, 3), (1-3, 4)`.
- Only cycle: 1 → 2 → 3 → 1, total weight 5 + 3 + 4 = 12. Minimum = **12**.

Example: graph with edges `(1-2, 1), (2-3, 1), (3-1, 1), (1-4, 1), (4-5, 1), (5-1, 1)`.
- Cycle 1-2-3-1: weight 3.
- Cycle 1-4-5-1: weight 3.
- Both equal. Minimum = **3**.

----------------------------------------

## Step 2: Key Observation — Cycle Through a Fixed Edge

Suppose we fix an edge `(u, v, w)`. A cycle passing through this edge consists of the edge `(u, v)` plus some **u-to-v path that doesn't use this edge**.

Weight of the cycle = `w + shortest_path(u, v, excluding edge (u, v))`.

If we can compute, for every edge, this "shortest path avoiding the edge itself", we can try every edge as the "cycle-closing edge" and take the overall minimum.

----------------------------------------

## Step 3: Compute Shortest-Paths-Without-an-Edge

For each edge `(u, v, w)`:
- Temporarily remove it from the graph.
- Run Dijkstra (or BFS for unweighted) from u to find shortest distance to v.
- If finite, candidate cycle weight = w + that distance.
- Restore the edge.

Track the minimum candidate across all edges.

If the graph has m edges, this is **m Dijkstra runs**, each O((V + E) log V). Total: O(E · (V + E) log V). For moderate graphs, fine.

For positive weights, Dijkstra. For edge weights = 1 (unweighted), BFS.

----------------------------------------

## Step 4: Why Does This Find the Minimum?

Any cycle contains at least one edge. If the true minimum cycle has edges `e_1, e_2, ..., e_k`, then for each of those edges `e_i` our algorithm tries: remove `e_i`, find shortest u-v path through the other `k-1` edges — which is exactly the rest of the cycle, weight = (total cycle weight) - w(e_i). Adding w(e_i) back gives the cycle's total weight.

So the minimum cycle will be detected (exactly once per cycle edge, but we're taking a min — duplicates are fine).

----------------------------------------

## Step 5: Algorithm

```
best = +∞
for each edge (u, v, w):
    remove edge (u, v) from graph temporarily
    d = dijkstra(u)[v]   # shortest u-to-v without this edge
    if d < ∞:
        best = min(best, w + d)
    restore edge (u, v)

return best if best < ∞ else -1
```

For parallel edges (multigraph): when we "remove" the edge, only remove this specific instance; other parallel edges remain and offer alternative paths. (Typical competitive programming setup assumes simple graph.)

----------------------------------------

## Step 6: Trace on a Triangle

Graph: nodes 1, 2, 3. Edges: (1-2, 5), (2-3, 3), (1-3, 4).

**Try edge (1-2, 5):** remove it. Dijkstra from 1 without edge (1-2): 1 → 3 (cost 4) → 2 (cost 4 + 3 = 7). Candidate = 5 + 7 = 12.

**Try edge (2-3, 3):** remove it. Dijkstra from 2 without edge (2-3): 2 → 1 (cost 5) → 3 (cost 5 + 4 = 9). Candidate = 3 + 9 = 12.

**Try edge (1-3, 4):** remove it. Dijkstra from 1 without edge (1-3): 1 → 2 (cost 5) → 3 (cost 5 + 3 = 8). Candidate = 4 + 8 = 12.

All three give 12 — the same cycle, discovered from three perspectives. Minimum = **12**. ✓

----------------------------------------

## Step 7: Alternative — Floyd-Warshall for Small Graphs

If V is small (≤ 400), Floyd-Warshall can find all-pairs shortest distances in O(V³). Then:
- For each edge (u, v, w), the shortest cycle through u-v has weight `w + shortest_path_through_others(u, v)`.
- With Floyd-Warshall we precompute all-pairs once and iterate edges.

Caveat: standard Floyd-Warshall allows using the edge (u, v) itself as a direct path. So removing the edge requires care — either recompute excluding it, or use a smarter formulation.

A cleaner approach for minimum cycle with Floyd-Warshall: for each pair of vertices (i, j), if there's an edge between them with weight w, then any path not using this edge directly (but through some intermediate k) combined with w forms a cycle of weight `w + dist[i][k] + dist[k][j]`. Minimize.

----------------------------------------

## Step 8: Name It

**Minimum cycle via edge-removal Dijkstra.** A standard technique in graph theory, sometimes called the "Dijkstra one-out" trick.

Related problems:
- Girth of a graph (minimum cycle length in unweighted graph — BFS variant).
- Second-shortest path (remove edges from the first shortest path).
- Minimum spanning tree "cycle cancellation" proofs use similar per-edge reasoning.

----------------------------------------

## Step 9: Complexity

Let V = vertices, E = edges.

- **Dijkstra per edge**: O(E · (V + E) log V).
- **Floyd-Warshall** (alternative): O(V³), better when V is small and E is large (dense graph).
- **BFS per edge** (unweighted): O(E · (V + E)).

Space: O(V + E) for the graph + per-Dijkstra arrays.

----------------------------------------

## Step 10: C++ Implementation (Dijkstra per Edge)

```cpp
int minimumWeightCycle(int n, vector<vector<int>>& edges) {
    // Build adjacency list; each edge stores an "index" so we can skip exactly one edge.
    vector<vector<tuple<int,int,int>>> adj(n + 1);  // (neighbor, weight, edge_id)
    for (int i = 0; i < (int)edges.size(); ++i) {
        int u = edges[i][0], v = edges[i][1], w = edges[i][2];
        adj[u].push_back({v, w, i});
        adj[v].push_back({u, w, i});
    }

    auto dijkstraSkip = [&](int src, int dst, int skipId) {
        vector<int> dist(n + 1, INT_MAX);
        dist[src] = 0;
        priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
        pq.push({0, src});
        while (!pq.empty()) {
            auto [d, u] = pq.top(); pq.pop();
            if (d > dist[u]) continue;
            for (auto [v, w, id] : adj[u]) {
                if (id == skipId) continue;
                if (d + w < dist[v]) {
                    dist[v] = d + w;
                    pq.push({dist[v], v});
                }
            }
        }
        return dist[dst];
    };

    int best = INT_MAX;
    for (int i = 0; i < (int)edges.size(); ++i) {
        int u = edges[i][0], v = edges[i][1], w = edges[i][2];
        int d = dijkstraSkip(u, v, i);
        if (d != INT_MAX) best = min(best, w + d);
    }
    return best == INT_MAX ? -1 : best;
}
```

Key trick: store an edge `id` in the adjacency entries. When Dijkstra is run with `skipId = i`, edge i is ignored — this cleanly handles multigraphs too (only THIS specific edge is skipped).

----------------------------------------

## Step 11: Follow-up Questions

- **Girth (unweighted minimum cycle length).** Use BFS from each vertex; detect when BFS re-visits an ancestor through a different path. O(V · E).
- **Return the cycle itself, not just weight.** Track parents in Dijkstra; reconstruct path from u to v when edge (u, v) is skipped.
- **Negative-weight edges.** Dijkstra fails; use Bellman-Ford per edge (slower).
- **Directed graph.** Same approach: remove edge (u → v), Dijkstra from v back to u. Edge directions matter.
- **Dense graphs (V small).** Floyd-Warshall all-pairs + per-edge check is often faster.
- **Why not just detect any cycle and report?** Because we want the **minimum-weight** cycle, not any.
