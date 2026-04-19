# Graph (BFS / DFS / Dijkstra / DSU) — Concepts Guide

----------------------------------------

## 1. Introduction

Graphs model relationships — between cities, between tasks, between people, between anything. The core algorithms (BFS, DFS, Dijkstra, Union-Find) let us answer questions like 'Can we get from A to B?', 'What's the shortest path?', and 'Are these two things connected?'. Master these four, and a surprising fraction of interview problems become routine.

----------------------------------------

## 2. Real-Life Analogy

Imagine a subway map. Each station is a node; each line between stations is an edge. 'How do I get from my apartment to the airport?' — that's BFS if every line takes the same time, or Dijkstra if lines take different times. 'Is Station X reachable from Station Y?' — that's DFS or Union-Find. 'Can I connect all stations with the fewest lines?' — that's a minimum spanning tree. Graphs are just this, abstracted.

----------------------------------------

## 3. Core Idea

A graph is a set of vertices V and edges E connecting them. Traversals (BFS, DFS) visit each vertex at most once by marking it visited, giving us O(V + E) time. BFS uses a queue and produces shortest-path distances in unweighted graphs because it explores level-by-level. DFS uses a stack (or recursion) and is the workhorse for topological sort, cycle detection, and connectivity. Dijkstra upgrades BFS with a priority queue for weighted graphs (non-negative weights). Union-Find (DSU) answers connectivity queries in near-constant time after O(α(n)) preprocessing per operation.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Signals for each algorithm:

- **'Shortest path in an unweighted graph'** → BFS.
- **'Shortest path with non-negative weights'** → Dijkstra.
- **'Shortest path with negative weights or k-stop constraint'** → Bellman-Ford.
- **'All-pairs shortest paths on a small graph'** → Floyd-Warshall.
- **'Connectivity, components, cycle detection'** → DFS or Union-Find.
- **'Topological order, course schedule'** → Kahn's BFS or DFS post-order.
- **'Bipartite check'** → 2-coloring via BFS/DFS.

----------------------------------------

## 5. Types / Variations

- **Directed vs Undirected:** directed edges require separate handling (in-degree matters for topo sort).
- **Weighted vs Unweighted:** BFS for unweighted, Dijkstra for weighted-positive, Bellman-Ford for weighted-general.
- **Dense vs Sparse:** adjacency matrix for dense (small n), adjacency list for sparse (large n).
- **Multi-source BFS:** start BFS from *multiple* nodes at once — used in 'nearest 0' or 'rotten oranges' style problems.
- **Bidirectional BFS:** BFS from both start and end simultaneously; meets in the middle for faster search.

----------------------------------------

## 6. Step-by-Step Working

**BFS:**
1. Enqueue the source; mark it visited.
2. Pop from the queue. For each unvisited neighbor, mark visited and enqueue.
3. Repeat until the queue is empty.

**DFS (recursive):**
1. Mark the current node visited.
2. Recurse on each unvisited neighbor.

**Dijkstra:**
1. Push (0, source) into a min-heap. Set dist[source] = 0.
2. Pop (d, u). If d > dist[u], skip (stale entry).
3. For each neighbor v with edge weight w, if dist[u] + w < dist[v], update dist[v] and push.
4. Repeat until the heap is empty.

**Union-Find:**
1. `find(x)` — walk parent pointers to the root, with path compression.
2. `union(a, b)` — attach the shorter tree under the taller; update ranks.

----------------------------------------

## 7. Visual Explanation

**BFS expanding layer by layer from source S:**

```
     Layer 0:   [S]
     Layer 1:   [A, B]
     Layer 2:   [C, D, E]
     Layer 3:   [F]
```

Each layer corresponds to one BFS round and represents all nodes at that distance from S.

**DSU component merges:**

```
  Initially: {0}, {1}, {2}, {3}, {4}
  union(0, 1): {0, 1}, {2}, {3}, {4}
  union(2, 3): {0, 1}, {2, 3}, {4}
  union(1, 3): {0, 1, 2, 3}, {4}
```

Once components merge, `find(0) == find(3)` because they're in the same set.

----------------------------------------

## 8. Code Templates (C++)

```cpp
// BFS
queue<int> q; q.push(src);
vector<int> dist(n, -1); dist[src] = 0;
while (!q.empty()) {
    int u = q.front(); q.pop();
    for (int v : g[u]) if (dist[v] == -1) {
        dist[v] = dist[u] + 1;
        q.push(v);
    }
}

// Dijkstra
priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
vector<int> dist(n, INT_MAX);
dist[src] = 0; pq.push({0, src});
while (!pq.empty()) {
    auto [d, u] = pq.top(); pq.pop();
    if (d > dist[u]) continue;
    for (auto [v, w] : g[u]) if (d + w < dist[v]) {
        dist[v] = d + w;
        pq.push({dist[v], v});
    }
}

// Union-Find
struct DSU {
    vector<int> p, r;
    DSU(int n): p(n), r(n, 0) { iota(p.begin(), p.end(), 0); }
    int find(int x) { return p[x] == x ? x : p[x] = find(p[x]); }
    bool unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (r[a] < r[b]) swap(a, b);
        p[b] = a;
        if (r[a] == r[b]) r[a]++;
        return true;
    }
};
```

----------------------------------------

## 9. Common Mistakes

- **Forgetting to mark visited** — causes infinite loops in cyclic graphs.
- **Using BFS for weighted shortest paths** — it only works for unweighted graphs.
- **Not skipping stale entries in Dijkstra** — can blow up the queue and complexity.
- **Directed vs undirected confusion** — always add reverse edges for undirected graphs.
- **Off-by-one in 0-indexed vs 1-indexed inputs.**
- **Stack overflow on deep DFS** — switch to iterative for very deep trees.

----------------------------------------

## 10. Interview Insights

Graph problems are a staple of interviews because they test multiple skills at once: modeling, algorithm selection, and implementation. Interviewers want to see:

1. **Can you model the problem as a graph?** Often the hardest step — recognizing that 'tasks with dependencies' is a graph with directed edges.
2. **Can you choose the right algorithm?** BFS vs DFS vs Dijkstra is a quick decision if you know the signals.
3. **Can you handle edge cases?** Isolated nodes, multiple components, self-loops, multigraphs.
4. **Can you implement cleanly?** Adjacency list setup, visited tracking, and pop/push order are all easy to mess up under pressure.

Narrate the graph in your head before coding: 'Nodes are cities, edges are flights with cost as weight — so this is Dijkstra with a positive-weight graph.' That narration alone saves you from going down the wrong path.
