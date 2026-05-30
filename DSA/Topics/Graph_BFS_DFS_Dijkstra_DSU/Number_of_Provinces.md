# Number of Provinces

**Problem Link:**
<a href="https://leetcode.com/problems/number-of-provinces/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/number-of-provinces/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Understand the Problem

Given an `n × n` matrix `isConnected` where `isConnected[i][j] == 1` means cities `i` and `j` are directly connected, return the number of **provinces**. A province is a group of cities where every pair is reachable (directly or indirectly).

Example:
```
isConnected = [
    [1, 1, 0],
    [1, 1, 0],
    [0, 0, 1]
]
```

City 0 and 1 are directly connected. City 2 is alone.
Provinces: {0, 1}, {2}. Count = **2**.

Another:
```
isConnected = [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]
]
```

Each city is isolated. Three provinces.

----------------------------------------

## Step 2: Recognize the Structure

"Cities connected directly or indirectly" is the definition of **connected components** in an undirected graph. A province is one connected component. The problem boils down to: **count connected components**.

The adjacency matrix `isConnected` fully describes the graph. `isConnected[i][i] == 1` always (every city is connected to itself), but that doesn't affect component count.

Standard ways to count components:
- **DFS/BFS**: from each unvisited node, do a traversal marking everything reachable; each traversal launch is one new component.
- **Union-Find**: union pairs of connected cities; count distinct roots at the end.

Both are valid here. Let me walk through DFS first.

----------------------------------------

## Step 3: DFS Approach

```
visited = [False] * n
count = 0

for i in 0..n-1:
    if not visited[i]:
        count++
        dfs(i)

def dfs(u):
    visited[u] = True
    for v in 0..n-1:
        if isConnected[u][v] == 1 and not visited[v]:
            dfs(v)

return count
```

The outer loop runs once per node. If a node is unvisited when we reach it, we've found a new component — increment counter, then DFS to mark the entire component visited.

----------------------------------------

## Step 4: Trace on the First Example

```
isConnected = [[1,1,0], [1,1,0], [0,0,1]]
visited = [F, F, F]

i=0: not visited. count=1. dfs(0):
  visited[0] = T.
  Neighbors: isConnected[0][0]=1 (self, skip since already visited), isConnected[0][1]=1. dfs(1).
    visited[1] = T.
    Neighbors: isConnected[1][0]=1 (visited), isConnected[1][1]=1 (self), isConnected[1][2]=0. No further dfs.
  isConnected[0][2]=0. Done.
visited = [T, T, F].

i=1: visited. Skip.

i=2: not visited. count=2. dfs(2):
  visited[2] = T.
  Neighbors: isConnected[2][0]=0, [2][1]=0, [2][2]=1 (self). No dfs.
visited = [T, T, T].

Return 2. ✓
```

Each DFS launch = one province.

----------------------------------------

## Step 5: Union-Find Approach

Alternatively, union-find:

```
dsu = DSU(n)
for i in 0..n-1:
    for j in i+1..n-1:    # upper triangle to avoid duplicate unions
        if isConnected[i][j] == 1:
            dsu.union(i, j)

count = number of distinct find(i) for i in 0..n-1
return count
```

For each pair (i, j) with a 1 in the matrix, union them. At the end, distinct roots = distinct components.

Both approaches are O(n²) because we have to at least examine the matrix.

----------------------------------------

## Step 6: Pick an Approach

Both DFS and Union-Find are natural here. Small tie-break:
- DFS: simpler to implement, natural recursion.
- Union-Find: slightly easier to extend if the graph is **dynamic** (edges added over time — each addition is one union).

For the static matrix given, DFS is the cleanest. Let me finalize on that.

----------------------------------------

## Step 7: Name It

Counting connected components is a foundational graph operation. Two canonical methods:
- **DFS/BFS component scan** (what we did).
- **Union-Find with root counting**.

Both run in O(n + m) for graphs expressed as adjacency lists; O(n²) for adjacency matrices like ours.

----------------------------------------

## Step 8: Complexity

Time: **O(n²)**. The adjacency matrix has n² entries, and we visit each once.
Space: **O(n)** for the visited array and recursion stack.

----------------------------------------

## Step 9: C++ Implementation

**DFS version:**

```cpp
int findCircleNum(vector<vector<int>>& isConnected) {
    int n = isConnected.size();
    vector<bool> visited(n, false);
    int count = 0;

    function<void(int)> dfs = [&](int u) {
        visited[u] = true;
        for (int v = 0; v < n; ++v) {
            if (isConnected[u][v] == 1 && !visited[v]) dfs(v);
        }
    };

    for (int i = 0; i < n; ++i) {
        if (!visited[i]) {
            count++;
            dfs(i);
        }
    }
    return count;
}
```

**Union-Find version:**

```cpp
class DSU {
    vector<int> parent;
public:
    DSU(int n) : parent(n) { iota(parent.begin(), parent.end(), 0); }
    int find(int x) {
        return parent[x] == x ? x : parent[x] = find(parent[x]);
    }
    void unite(int a, int b) {
        int ra = find(a), rb = find(b);
        if (ra != rb) parent[ra] = rb;
    }
};

int findCircleNum(vector<vector<int>>& isConnected) {
    int n = isConnected.size();
    DSU dsu(n);
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            if (isConnected[i][j] == 1) dsu.unite(i, j);
        }
    }
    unordered_set<int> roots;
    for (int i = 0; i < n; ++i) roots.insert(dsu.find(i));
    return roots.size();
}
```

Both 15-ish lines, similar complexity. Pick based on preference.

----------------------------------------

## Step 10: Follow-up Questions

- **Dynamic: edges added over time.** Union-Find shines — each addition is O(α(n)).
- **Very sparse graph (few 1s in the matrix).** Adjacency list would help, but the input is given as a matrix. Can't help O(n²) lower bound for matrix scan.
- **Return the provinces themselves, not just the count.** Collect nodes during DFS into per-component lists.
- **Weighted edges — find clusters with minimum-weight spanning forest.** Kruskal's MST on all edges.
- **Huge n.** O(n²) is unavoidable given the matrix input. If the graph is sparse, convert to adjacency list first (but that's still O(n²) to read the matrix).
- **Disconnected vs connected pattern recognition.** "Count components" is the keyword; DFS or DSU both work.
