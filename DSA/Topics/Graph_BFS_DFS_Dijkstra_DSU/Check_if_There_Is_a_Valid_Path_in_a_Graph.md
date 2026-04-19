# Check if There Is a Valid Path in a Graph

**Problem Link:**
https://leetcode.com/problems/find-if-path-exists-in-graph/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Understand the Task

An **undirected** graph with `n` nodes (labeled 0 to n-1) and a list of edges. Given a source `source` and destination `destination`, return true if there's a path from source to destination.

Example: `n = 3`, `edges = [[0, 1], [1, 2], [2, 0]]`, source = 0, destination = 2.

Edges form a triangle: 0-1, 1-2, 2-0. A path from 0 to 2 exists (direct edge). Return true.

Example: `n = 6`, `edges = [[0, 1], [0, 2], [3, 5], [5, 4], [4, 3]]`, source = 0, destination = 5.

Edges split into two components: {0, 1, 2} and {3, 4, 5}. No path from 0 to 5. Return false.

----------------------------------------

## Step 2: It's Reachability, Again

This is a pure reachability question: can we get from source to destination following edges?

Three standard ways:
1. **BFS from source.** Stop if we reach destination.
2. **DFS from source.** Stop if we reach destination.
3. **Union-Find.** Union all edges; check if find(source) == find(destination).

All are O(V + E). Union-Find is nice if we're asked many such queries on the same graph; BFS/DFS is natural for a single query.

----------------------------------------

## Step 3: BFS Approach

Build the adjacency list. BFS from source, marking visited. If we dequeue destination, return true. If BFS exhausts, return false.

```
adj = adjacency list from edges
visited = [False] * n
queue = [source]
visited[source] = True

while queue not empty:
    u = queue.pop_front()
    if u == destination: return True
    for v in adj[u]:
        if not visited[v]:
            visited[v] = True
            queue.push(v)

return False
```

Straightforward. O(V + E).

----------------------------------------

## Step 4: Union-Find Approach

For each edge, union the two endpoints. After processing all edges, two nodes are connected iff find(u) == find(v).

```
dsu = DSU(n)
for (a, b) in edges: dsu.unite(a, b)
return dsu.find(source) == dsu.find(destination)
```

O((V + E) · α(n)) — essentially linear.

Union-Find is preferred when:
- We have many queries on the same graph.
- The graph is built incrementally.
- We need to maintain connectivity under additions.

For this single query, either works.

----------------------------------------

## Step 5: Trace Quickly

`n = 3, edges = [[0, 1], [1, 2], [2, 0]]`, source = 0, dest = 2.

**BFS:**
```
adj[0] = [1, 2], adj[1] = [0, 2], adj[2] = [0, 1].
queue = [0]. visited[0] = true.

Dequeue 0. 0 != 2. Neighbors 1, 2. Set visited[1] = true, visited[2] = true. Enqueue both.
Dequeue 1. 1 != 2. Neighbors 0 (visited), 2 (visited). Nothing new.
Dequeue 2. 2 == dest. Return true.
```

**Union-Find:**
```
DSU: parent = [0, 1, 2].
Edge (0, 1): union → parent = [1, 1, 2] (or similar).
Edge (1, 2): union → all in one component.
Edge (2, 0): already same component.

find(0) == find(2)? Yes. Return true.
```

Both approaches work. ✓

----------------------------------------

## Step 6: Why Union-Find Shines With Multiple Queries

If we had many (source, destination) queries on the same graph, the BFS would redo work for each query — O((V + E) per query).

Union-Find processes all edges once — O((V + E) · α(n)) total setup. Each subsequent query is O(α(n)). For Q queries, total is O((V + E + Q) · α(n)) — much better than O(Q · (V + E)).

For a single query, the complexity is the same.

----------------------------------------

## Step 7: Name It

**Graph reachability** — the simplest graph query. Solvable by BFS, DFS, or Union-Find. Choice depends on the setting:
- Single-shot query on a static graph: BFS/DFS.
- Many queries on a static graph: Union-Find precomputation.
- Dynamic graph (edge additions): Union-Find.
- Dynamic graph (edge deletions): neither simply; advanced techniques needed.

----------------------------------------

## Step 8: Complexity

Both approaches: **O(V + E)** single query.
Space: **O(V + E)** for adj list or DSU.

----------------------------------------

## Step 9: C++ Implementation

**BFS version:**

```cpp
bool validPath(int n, vector<vector<int>>& edges, int source, int destination) {
    vector<vector<int>> adj(n);
    for (auto& e : edges) {
        adj[e[0]].push_back(e[1]);
        adj[e[1]].push_back(e[0]);
    }
    vector<bool> visited(n, false);
    queue<int> q;
    q.push(source);
    visited[source] = true;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        if (u == destination) return true;
        for (int v : adj[u]) {
            if (!visited[v]) {
                visited[v] = true;
                q.push(v);
            }
        }
    }
    return false;
}
```

**Union-Find version:**

```cpp
class DSU {
    vector<int> parent;
public:
    DSU(int n) : parent(n) { iota(parent.begin(), parent.end(), 0); }
    int find(int x) { return parent[x] == x ? x : parent[x] = find(parent[x]); }
    void unite(int a, int b) { parent[find(a)] = find(b); }
};

bool validPath(int n, vector<vector<int>>& edges, int source, int destination) {
    DSU dsu(n);
    for (auto& e : edges) dsu.unite(e[0], e[1]);
    return dsu.find(source) == dsu.find(destination);
}
```

The Union-Find version is shorter for this problem.

----------------------------------------

## Step 10: Follow-up Questions

- **Shortest path (number of edges).** BFS naturally finds this.
- **Weighted edges — cheapest path.** Dijkstra.
- **Path with specific property (e.g., visiting certain nodes).** More complex DFS or state-search.
- **Count paths.** Counting paths can be exponential; need DP or careful enumeration.
- **Return the actual path.** Track parent pointers during BFS.
- **Directed graph.** Build directed adjacency list; algorithm otherwise unchanged.
