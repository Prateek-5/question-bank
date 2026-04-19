# Number of Operations to Make Network Connected

**Problem Link:**
https://leetcode.com/problems/number-of-operations-to-make-network-connected/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Understand the Setup

You have `n` computers numbered 0..n-1 and a list of cables `connections`, where each cable `[a, b]` directly connects computers a and b.

You can **unplug a cable from one pair and plug it between any other pair** — that's a single "operation." Goal: make **all computers connected** (i.e., any computer can reach any other through cables). Return the minimum number of operations, or -1 if impossible.

Example: `n = 4`, `connections = [[0,1],[0,2],[1,2]]`.
- Current: 0-1-2 form a triangle; 3 is isolated.
- One operation: take an unneeded cable (say the redundant 1-2 edge) and connect it between 0 and 3. Now everything's connected.
- Answer: **1**.

----------------------------------------

## Step 2: When Is It Impossible?

To connect n computers with cables, we need at least **n - 1 cables** total — that's the minimum for a tree spanning n nodes. If the input has fewer than n - 1 cables, no amount of rearranging can connect everything. Return **-1**.

Check first: if `connections.size() < n - 1`, return -1.

----------------------------------------

## Step 3: Reframe in Graph Language

Build the graph from the connections. Compute the number of **connected components** — say there are `c` of them.

To make the graph connected, we need to "link" all c components into 1. Each operation moves one cable to bridge two components — reducing the component count by 1.

So we need **c - 1 operations** to merge c components into one.

**But wait** — does an operation always have a cable to move? Each operation requires taking an existing cable from somewhere. If the graph has exactly n - 1 cables and c components, all cables are "tree edges" within components — none are redundant. Can we still perform c - 1 operations?

**Yes.** Here's why: with c components and total cable count ≥ n - 1, the redundancy count is:

```
redundant = total_cables - (n - c)   # because a spanning forest on c components needs n - c edges
```

Substituting total ≥ n - 1: redundant ≥ (n - 1) - (n - c) = c - 1. So we always have at least c - 1 redundant cables — enough to do the merging.

This means: **if total cables ≥ n - 1, answer is (c - 1). Otherwise -1.**

----------------------------------------

## Step 4: Count Components — DSU or DFS

Both work:
- **DFS**: start DFS from each unvisited node; increment component count each time we start a new DFS.
- **DSU (Union-Find)**: union every edge; count the number of distinct roots.

DSU is slightly cleaner for this kind of "count components" question, and generalizes to dynamic connectivity problems. DFS is more elementary.

Either gives O(n + m) effectively.

----------------------------------------

## Step 5: Algorithm

```
if connections.size() < n - 1: return -1

components = count_components(n, connections)
return components - 1
```

That's the whole algorithm. Two observations collapsed into a two-liner.

----------------------------------------

## Step 6: Trace

`n = 6`, `connections = [[0,1],[0,2],[0,3],[1,2],[1,3]]`. That's 5 cables, n - 1 = 5, enough.

Build graph. DFS:
- Start at 0. Visit {0, 1, 2, 3}. Component 1 done.
- Start at 4 (unvisited). Only 4 itself. Component 2 done.
- Start at 5 (unvisited). Only 5 itself. Component 3 done.

3 components. Answer: **3 - 1 = 2**. ✓

Verify: we need to move 2 cables (out of 5) to bridge the 3 components into 1.

----------------------------------------

## Step 7: Why This Works

The key mental shift: each "redundant" cable (extra beyond a spanning forest) can be relocated to bridge two components. With `c - 1` bridges, all components fuse into one.

The problem's operation count is a direct function of the component count — not the specific topology.

**Minimum cables needed** = n - 1 (spanning tree). **Redundant cables available** = `m - (n - c)` where m = total cables. Plugging in `m ≥ n - 1` gives redundant ≥ c - 1, confirming feasibility.

----------------------------------------

## Step 8: Name It

**Component counting + spanning-tree reasoning.** The combinatorial identity behind the solution is:

```
edges - (nodes - components) = edges in cycles (redundant edges)
```

This is the "cycle rank" of the graph. Spotting this ratio lets you convert "rewire cables" problems into "count components" problems.

Relatives:
- Spanning tree problems (Kruskal, Prim).
- Graph bridges / articulation points (when *can't* you afford to move?).
- Redundant Connection (closely related LeetCode problem).

----------------------------------------

## Step 9: Complexity

Time: **O(n + m · α(n))** with DSU, or **O(n + m)** with DFS.
Space: **O(n + m)** for the graph/DSU structures.

----------------------------------------

## Step 10: C++ Implementation

**Using DFS:**

```cpp
int makeConnected(int n, vector<vector<int>>& connections) {
    if ((int)connections.size() < n - 1) return -1;

    vector<vector<int>> adj(n);
    for (auto& e : connections) {
        adj[e[0]].push_back(e[1]);
        adj[e[1]].push_back(e[0]);
    }

    vector<bool> visited(n, false);
    function<void(int)> dfs = [&](int u) {
        visited[u] = true;
        for (int v : adj[u]) if (!visited[v]) dfs(v);
    };

    int components = 0;
    for (int u = 0; u < n; ++u) {
        if (!visited[u]) { dfs(u); components++; }
    }
    return components - 1;
}
```

**Using DSU:**

```cpp
struct DSU {
    vector<int> p, r;
    DSU(int n) : p(n), r(n, 0) { iota(p.begin(), p.end(), 0); }
    int find(int x) { return p[x] == x ? x : p[x] = find(p[x]); }
    void unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return;
        if (r[a] < r[b]) swap(a, b);
        p[b] = a;
        if (r[a] == r[b]) r[a]++;
    }
};

int makeConnected(int n, vector<vector<int>>& connections) {
    if ((int)connections.size() < n - 1) return -1;
    DSU dsu(n);
    for (auto& e : connections) dsu.unite(e[0], e[1]);
    int components = 0;
    for (int u = 0; u < n; ++u) if (dsu.find(u) == u) components++;
    return components - 1;
}
```

----------------------------------------

## Step 11: Follow-up Questions

- **Return the specific cables to move.** Track redundant edges (those forming cycles during DSU union); pair each with a bridge target.
- **Dynamic: nodes or cables added over time.** DSU supports incremental unions; recompute component count after each event.
- **Weighted version: minimize "length of new cable" instead of count.** Becomes a minimum spanning tree over components — Kruskal works.
- **Why `connections.size() < n - 1` is the -1 criterion?** A connected graph on n nodes needs at least n - 1 edges (spanning tree); fewer edges means no rearrangement can connect everything.
- **Why DSU over DFS?** Preference; DSU is more compact for pure component-counting and extends to online/dynamic scenarios.
