# Redundant Connection

**Problem Link:**
https://leetcode.com/problems/redundant-connection/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Carefully Parse What "Redundant" Means Here

You're given a list of edges. The original graph — before someone tampered with it — was a **tree** on n nodes. A tree has a crucial property: exactly n-1 edges, no cycles, connected.

Someone added one extra edge to this tree. Now we have n edges, and exactly one cycle has formed. Your job: identify which edge was added.

**If multiple edges could be "the added one"** (meaning they're all part of the cycle), return the one that **appears last** in the input order. This is how the problem disambiguates — otherwise any edge in the cycle would be a valid answer.

Example: `edges = [[1,2], [1,3], [2,3]]`.

Three edges, three nodes. A tree would need only 2 edges. The cycle here is 1-2-3-1. Any of the three edges could be considered "redundant" since removing it breaks the cycle. But the problem wants the **last** one in input order. That's `[2, 3]`.

----------------------------------------

## Step 2: Playing It Through By Hand

Let me simulate adding edges one at a time, watching when a cycle forms.

Start: 3 isolated nodes, no edges. Components: {1}, {2}, {3}.

Add `[1, 2]`: nodes 1 and 2 now connected. Components: {1, 2}, {3}. No cycle (they weren't connected before).

Add `[1, 3]`: node 1 (already in the first component) connects to node 3 (alone). Components merge to {1, 2, 3}. No cycle (1 and 3 weren't connected before).

Add `[2, 3]`: both nodes 2 and 3 are **already in the same component**. Adding this edge creates a path-plus-new-edge, which is a cycle.

**Key realization:** an edge creates a cycle iff its two endpoints are **already connected** at the moment we add it.

----------------------------------------

## Step 3: Does Left-to-Right Processing Give the Right Answer?

The problem says "if multiple edges could be the answer, return the one appearing last in input." Let me check whether our "return the first cycle-creating edge as we process left-to-right" matches this.

Since there's exactly **one** cycle in the final graph (it started as a tree, we added one edge, we get one cycle), and we're processing edges in order, the cycle forms the moment we add an edge connecting two already-connected nodes. That "cycle-forming" edge is a specific edge in the input — the last one (in input order) that completes the cycle.

So yes, the first edge that we *detect* as cycle-creating in our left-to-right scan is the answer. Our approach correctly returns the last-in-input edge of the cycle.

To be extra careful: imagine `edges = [[1,2], [2,3], [3,1]]`. All three form a cycle. Processing:
- `[1,2]`: components {1,2}, {3}. OK.
- `[2,3]`: connects {1,2} and {3}. Components {1,2,3}. OK.
- `[3,1]`: both already in {1,2,3}. **Cycle detected.** Return `[3, 1]`.

`[3,1]` is the last-in-input edge, matching what the problem wants.

----------------------------------------

## Step 4: Now, How Do We Efficiently Detect "Already Connected"?

This is the core technical question. Each time we want to add an edge (u, v), we need to answer: *"at this moment, are u and v already in the same connected component?"*

**Option A: Re-run BFS/DFS each time.** For each new edge, do BFS from u to see if v is reachable via previously-added edges. That's O(V + E) per edge. For n edges, total O(n·(V+E)) = O(n²). For small n, fine; for n = 10^4, feasible; for large n, slow.

**Option B: Maintain a structure that supports fast "are u and v connected?" and fast "merge u's and v's components into one."**

Such a structure exists — the **Union-Find** (or Disjoint Set Union, DSU) data structure. Each operation (find which component a node is in, or union two components) runs in amortized **inverse-Ackermann time**, α(n), which is effectively constant.

Union-Find is purpose-built for this kind of incremental connectivity question. So the observation "fast connectivity-with-merging" leads us to it.

----------------------------------------

## Step 5: Quick Tour of Union-Find

The data structure maintains a forest of "parent pointers." Each node has a parent; following parents eventually leads to a root. Nodes sharing the same root are in the same component.

- **`find(x)`**: walk parent pointers until reaching a root. To avoid re-walking long chains, apply **path compression**: after finding the root, set every node on the path to point directly to the root. This flattens the tree over time.

- **`union(u, v)`**: find roots of u and v. If the same, they're already connected — do nothing (or return a flag). Otherwise, attach one root under the other. To keep trees shallow, use **union-by-rank**: attach the shorter tree under the taller.

With both optimizations, any sequence of m operations on n elements takes O(m · α(n)) total. α is the inverse Ackermann function — it's at most 4 for any practical n.

----------------------------------------

## Step 6: The Algorithm

```
initialize DSU with n nodes (each its own component)
for each edge (u, v) in the input:
    if find(u) == find(v):
        # already connected — this edge creates the cycle
        return (u, v)
    union(u, v)
# (unreachable — the problem guarantees exactly one redundant edge)
```

We scan edges once, doing one `find` (possibly two, for the match test) and optionally one `union` per edge. Total amortized time: O(n · α(n)).

----------------------------------------

## Step 7: Trace on `[[1,2], [1,3], [2,3]]`

```
Initial parents: 1→1, 2→2, 3→3 (each is its own root).

Edge [1, 2]:
  find(1) = 1. find(2) = 2. Different. Union.
  Attach 2 under 1: parents = 1→1, 2→1, 3→3.

Edge [1, 3]:
  find(1) = 1. find(3) = 3. Different. Union.
  Attach 3 under 1: parents = 1→1, 2→1, 3→1.

Edge [2, 3]:
  find(2): 2→1, so root is 1. (Path compression flattens if needed.)
  find(3): 3→1, root is 1.
  Same root! Return [2, 3].
```

Correct. ✓

Note: after path compression, all nodes in a component point directly to the root, which makes future `find` calls O(1).

----------------------------------------

## Step 8: Name the Technique

We just used **Union-Find (DSU)** for incremental connectivity with cycle detection. This exact pattern shows up in:

- **Kruskal's MST algorithm**: sort edges by weight; add in order; skip if it creates a cycle.
- **Satisfiability of Equality Equations**: union variables that are equal, check inequalities against components.
- **Number of Islands II**: as cells turn from water to land, merge with neighboring land.
- **Dynamic connectivity in online systems.**

When you hear "add edges one at a time and ask about connectivity," DSU is almost always the right tool.

----------------------------------------

## Step 9: Complexity

Time: **O(n · α(n))** — effectively linear.
Space: **O(n)** for parent/rank arrays.

----------------------------------------

## Step 10: C++ Implementation

```cpp
class DSU {
    vector<int> parent, rnk;
public:
    DSU(int n) : parent(n + 1), rnk(n + 1, 0) {
        iota(parent.begin(), parent.end(), 0);     // parent[i] = i initially
    }

    int find(int x) {
        if (parent[x] != x) parent[x] = find(parent[x]);   // path compression
        return parent[x];
    }

    bool unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;        // already connected
        if (rnk[a] < rnk[b]) swap(a, b);
        parent[b] = a;
        if (rnk[a] == rnk[b]) rnk[a]++;
        return true;
    }
};

vector<int> findRedundantConnection(vector<vector<int>>& edges) {
    DSU dsu(edges.size());
    for (auto& e : edges) {
        if (!dsu.unite(e[0], e[1])) return e;   // unite failed → already connected
    }
    return {};
}
```

Implementation notes:
- `unite` returns false when the two endpoints are already in the same component — exactly our cycle signal.
- We use 1-indexed DSU (sized n+1) because the problem labels nodes 1..n.
- Path compression is applied inside `find`; union-by-rank inside `unite`.

----------------------------------------

## Step 11: Follow-up Questions

- **Redundant Connection II (directed graph).** Two failure modes: (1) a node with in-degree 2, and (2) a cycle. Case-split and handle both with DSU.
- **Kruskal's Minimum Spanning Tree.** Same DSU structure, but edges are processed in increasing weight order. Skip cycle-creators.
- **Dynamic connectivity with deletions.** DSU doesn't easily support "remove an edge." Use link-cut trees or offline techniques.
- **Why not DFS?** Works but slower per edge — O(V + E) per check. DSU is amortized constant.
- **What if nodes are identified by strings, not integers?** Map strings to integer IDs, then use DSU normally.
- **Smallest redundant edge (not last-in-input).** After detecting the cycle, find the edge's specific position.
