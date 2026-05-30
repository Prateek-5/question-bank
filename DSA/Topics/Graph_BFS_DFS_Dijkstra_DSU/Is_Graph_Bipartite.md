# Is Graph Bipartite

**Problem Link:**
<a href="https://leetcode.com/problems/is-graph-bipartite/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/is-graph-bipartite/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: What's the Problem Really Asking?

Given an undirected graph, decide whether you can color each node with one of **two colors** such that no edge connects two nodes of the same color.

Less technically: can we split the nodes into **two groups** where every edge goes between groups, never within a group?

Example (graph shown as adjacency list):
```
0 ↔ 1
0 ↔ 3
1 ↔ 2
2 ↔ 3
```

Try to 2-color: put 0 in group A. Then 1 must be in B (edge to 0). 3 must be in B (edge to 0). 2 must be in A (edge to 1) and A (edge to 3) — consistent. All edges cross groups. **Bipartite.**

Now add an edge `1 ↔ 3`. 1 is in B, 3 is in B — edge within B. **Not bipartite.**

----------------------------------------

## Step 2: What Makes It Impossible?

Let me think about when 2-coloring fails. If we have a triangle (three nodes all pairwise connected), any 2-coloring creates a same-color edge. A triangle has an **odd cycle** (length 3).

More generally: if the graph has any cycle of odd length, 2-coloring fails. If all cycles are even length, it works. This is a famous theorem: **a graph is bipartite iff it contains no odd cycles**.

I won't try to search for cycles explicitly. Instead, let me try a greedy coloring and see where it breaks.

----------------------------------------

## Step 3: The Coloring Procedure

Pick any uncolored node. Color it, say, 0. Look at all its neighbors. They must be color 1. Color them. Look at *their* neighbors. They must be color 0 (the opposite). And so on.

This is exactly **BFS** (or DFS) where each step alternates colors. If we ever try to color a node with a color different from its existing color, we have a conflict — the graph is not bipartite.

Concretely:
- `color[i]` = 0, 1, or -1 (uncolored).
- Start BFS from each uncolored node (to handle disconnected components).
- When we visit a neighbor, assign it the opposite color. If it was already colored with the correct opposite, fine. If it was colored the same as the current node — conflict, return false.

----------------------------------------

## Step 4: Trace on the Non-Bipartite Example

Graph: `0-1, 0-3, 1-2, 2-3, 1-3`.

```
color = [-1, -1, -1, -1]

Start BFS from 0. color[0] = 0. queue = [0].

Pop 0.
  Neighbor 1: uncolored, set color[1] = 1. Enqueue.
  Neighbor 3: uncolored, set color[3] = 1. Enqueue.

queue = [1, 3].

Pop 1.
  Neighbor 0: color[0]=0. 0 != color[1]=1 → different colors, good.
  Neighbor 2: uncolored, set color[2] = 0. Enqueue.
  Neighbor 3: color[3]=1. Same as color[1]=1 → CONFLICT. Return false.
```

Caught. ✓

And for the bipartite graph (without 1-3), when we pop 1 and look at neighbor 3, color[3] was 1 (same as color[1])... wait, that's also 1-3 visited through 0, both getting color 1. Hmm.

Actually let me re-trace the bipartite case (no 1-3 edge):

```
Pop 0. Color neighbors 1, 3 with 1.
Pop 1. Neighbors: 0 (color 0, ok), 2 (uncolored, set to 0).
Pop 3. Neighbors: 0 (ok), 2 (color 0, ok — 0 != color[3]=1).
Pop 2. Neighbors: 1 (color 1, ok), 3 (color 1, ok).
Done. No conflicts.
```

Good. So the "conflict" check is: when we find a neighbor that's already colored, does its color match what we'd assign it? If yes, fine. If no, conflict.

----------------------------------------

## Step 5: Why BFS / DFS Is Guaranteed to Detect Conflicts

Suppose the graph has an odd cycle `v_0, v_1, ..., v_{2k}, v_0` (length 2k+1, odd). BFS starts coloring: v_0 gets color 0, v_1 gets 1, v_2 gets 0, ..., v_{2k} gets 0 (since 2k is even). But then v_{2k} has an edge back to v_0, both colored 0 — conflict.

Conversely, if no odd cycle exists, the BFS coloring is consistent. Why? Because in a graph without odd cycles, every node's "distance from the starting node" has a well-defined parity, and we can color by parity.

So the algorithm exactly detects what makes bipartiteness fail.

----------------------------------------

## Step 6: Handling Disconnected Graphs

If the graph has multiple components, BFS from one node won't touch the others. So loop over every node, and if it's uncolored, start a new BFS. Each BFS colors one component.

The graph is bipartite iff every component is bipartite.

----------------------------------------

## Step 7: Complexity

Time: each node is visited once. Each edge is inspected twice (once from each endpoint). **O(V + E)**.

Space: the color array is O(V). BFS queue can hold up to O(V). **O(V)**.

----------------------------------------

## Step 8: C++ Implementation

```cpp
bool isBipartite(vector<vector<int>>& graph) {
    int n = graph.size();
    vector<int> color(n, -1);
    for (int s = 0; s < n; ++s) {
        if (color[s] != -1) continue;     // already colored (part of prior component)
        queue<int> q;
        q.push(s);
        color[s] = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (int v : graph[u]) {
                if (color[v] == -1) {
                    color[v] = 1 - color[u];     // opposite color
                    q.push(v);
                } else if (color[v] == color[u]) {
                    return false;                 // conflict!
                }
            }
        }
    }
    return true;
}
```

Implementation notes:
- Start with `color[s] = 0`, then alternate via `1 - color[u]`.
- The outer loop `for (int s = 0; s < n; ++s)` handles disconnected components.
- We never modify a node's color once set — so "already colored, does it match what we'd assign" is `color[v] != color[u]` (opposite is `1 - color[u]`, so same would mean `color[v] == color[u]`).

A DFS version is equally valid:

```cpp
bool dfs(int u, int c, vector<int>& color, vector<vector<int>>& g) {
    color[u] = c;
    for (int v : g[u]) {
        if (color[v] == -1) {
            if (!dfs(v, 1 - c, color, g)) return false;
        } else if (color[v] == c) {
            return false;
        }
    }
    return true;
}
```

BFS vs DFS: same logic, different traversal order. Both O(V + E).

----------------------------------------

## Step 9: Name the Result

We just derived a **2-coloring BFS**. The name highlights what we do (assign colors) and how (breadth-first). Bipartite detection via 2-coloring is the canonical technique.

Related problems:
- Graph coloring with k colors (NP-hard for k ≥ 3).
- Matchings in bipartite graphs (König's theorem, augmenting paths).
- Odd cycle detection (use a different BFS variant to find the cycle itself).

----------------------------------------

## Step 10: Follow-up Questions

- **Return one of the two partitions** (not just yes/no). Keep the `color` array; after confirming bipartite, nodes with color 0 form one partition, color 1 the other.
- **Bipartite by edge labels (e.g., positive vs negative edges must alternate).** Extend the color rule to take edge labels into account.
- **K-coloring (chromatic number).** NP-hard. Exponential-time brute force or heuristics.
- **Dynamic bipartite check (edges added / removed online).** Harder — requires link-cut trees or similar structures.
- **Weighted bipartite matching.** Hungarian algorithm or min-cost flow.
