# Graph (BFS / DFS / Dijkstra / DSU) — Concepts

## Core Theory
Graphs model relations between nodes. Depending on the problem, choose representation (adjacency list / matrix), traversal (BFS, DFS), shortest path (Dijkstra, Bellman-Ford, Floyd-Warshall), cycle detection, topological sort, or connectivity (DSU).

## Common Patterns
- **BFS for shortest hops** in unweighted graphs; multi-source BFS for distance fields.
- **DFS for connectivity, topo order, strongly connected components, cycle detection.**
- **Dijkstra with min-heap** for non-negative weights.
- **Bellman-Ford** for negative weights or k-step constraints.
- **DSU (Union-Find)** for connectivity queries, Kruskal's MST, equation systems.

## When to Use
BFS for shortest unweighted path. DFS for recursive exploration and topo. Dijkstra for weighted shortest path. DSU when only connectivity matters and merges dominate queries.

## Template
```cpp
// DSU
struct DSU {
    vector<int> p, r;
    DSU(int n): p(n), r(n, 0) { iota(p.begin(), p.end(), 0); }
    int find(int x) { return p[x] == x ? x : p[x] = find(p[x]); }
    bool unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (r[a] < r[b]) swap(a, b);
        p[b] = a; if (r[a] == r[b]) r[a]++; return true;
    }
};
```

## Common Mistakes
- Forgetting to mark nodes visited causes infinite loops.
- Using `visited` inside Dijkstra's pop phase instead of checking on push.
- Directed vs undirected: omission of reverse edges or parent exclusion.
- Off-by-one when 1-indexed inputs meet 0-indexed adjacency arrays.
