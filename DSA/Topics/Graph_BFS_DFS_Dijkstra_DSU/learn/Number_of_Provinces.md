# Number of Provinces — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Number_of_Provinces.md`](../Number_of_Provinces.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/number-of-provinces/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/number-of-provinces/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **Counting CONNECTED COMPONENTS in an ADJACENCY MATRIX graph.** The lesson: **DFS from each unvisited node = ONE component. OR use Union-Find.** **Read [`Number_of_Islands.md`](./Number_of_Islands.md) first** (same idea on grids).

**Map of this file (7 short sections):**

1. Read the problem
2. Recognize connected components
3. DFS approach
4. Union-Find alternative
5. Code (both)
6. Trace it
7. The shape — components everywhere

---

## 1. Read the problem

Given an `n × n` matrix `isConnected` where `isConnected[i][j] == 1` means cities `i` and `j` are directly connected, return the number of **PROVINCES**.

A province is a maximal set of cities all reachable from one another (directly or via other cities).

**Example:** `isConnected = [[1,1,0], [1,1,0], [0,0,1]]`.

Cities 0 and 1 connected. City 2 alone. **2 provinces.**

---

## 2. Recognize connected components

> **Mini-refresher: provinces = connected components.**
>
> The MATRIX defines an undirected graph: edges where `isConnected[i][j] == 1`. A "province" is a CONNECTED COMPONENT (maximal set of mutually-reachable nodes).
>
> Counting components is a classical graph operation:
> 1. **DFS/BFS from each unvisited node.** Each launch = one component.
> 2. **Union-Find.** Union every connected pair. Count distinct roots.

Both work. DFS is simpler; Union-Find shines if edges arrive dynamically.

---

## 3. DFS approach

```
visited = [False] * n
count = 0

for i in 0..n-1:
    if not visited[i]:
        count += 1
        dfs(i)        # marks every node reachable from i

def dfs(u):
    visited[u] = True
    for v in 0..n-1:
        if isConnected[u][v] == 1 and not visited[v]:
            dfs(v)
```

Each DFS visit marks the whole component. The outer loop counts how many distinct DFS launches we make = number of components.

O(n²) (must read the entire matrix).

---

## 4. Union-Find alternative

For each pair `(i, j)` with `isConnected[i][j] == 1`, UNION them. At end, count distinct roots.

```
dsu = DSU(n)
for i in 0..n-1:
    for j in i+1..n-1:        # upper triangle to avoid duplicate unions
        if isConnected[i][j] == 1:
            dsu.union(i, j)

return number of distinct find(i) for i in 0..n-1
```

Each find/union is near-O(1) amortized. Total O(n² α(n)) ≈ O(n²).

---

## 5. Code (both)

**C++ — DFS:**

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
        if (!visited[i]) { count++; dfs(i); }
    }
    return count;
}
```

**C++ — Union-Find:**

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
    return (int)roots.size();
}
```

> **Mini-refresher: DSU (Union-Find) primitives.**
>
> - `find(x)`: returns the ROOT of x's set. Path compression: each call flattens the tree.
> - `union(a, b)`: merge the two sets.
> - Amortized **O(α(n))** ≈ O(1) per operation.

Complexity: **O(n²) time, O(n) space** for both.

---

## 6. Trace it

`isConnected = [[1,1,0], [1,1,0], [0,0,1]]`. n = 3.

**DFS:**
```
visited = [F, F, F]. count = 0.

i=0: not visited. count = 1. dfs(0):
  visited[0] = T.
  v=1: isConn[0][1]=1, not visited. dfs(1):
    visited[1] = T.
    v=0: visited. v=2: isConn[1][2]=0.
  v=2: isConn[0][2]=0.

i=1: visited. Skip.
i=2: not visited. count = 2. dfs(2):
  visited[2] = T. No neighbors.

Return 2.  ✓
```

---

## 7. The shape — components everywhere

The pattern:

> **"Counting / identifying / grouping CONNECTED COMPONENTS in an undirected graph: DFS or Union-Find."**

| Problem | Components of... |
|---|---|
| **This problem** | cities |
| Number of Islands | grid cells |
| Friend Circles | people |
| Number of Connected Components in an Undirected Graph | nodes |
| Accounts Merge | emails belonging to same person |
| Most Stones Removed | stones sharing row or column |

**Pattern to internalize:**

> "WHENEVER you need to count or identify GROUPS of related items where 'related' is transitive, you have a CONNECTED COMPONENTS problem. DFS or DSU both work — DFS is simpler, DSU is better for streaming updates."

---

## Cross-references

- **Reference card (post-mastery):** [`../Number_of_Provinces.md`](../Number_of_Provinces.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Islands.md`](./Number_of_Islands.md), [`Max_Area_of_Island.md`](./Max_Area_of_Island.md).
  - Coming next: [`Rotting_Oranges.md`](./Rotting_Oranges.md), [`01_Matrix.md`](./01_Matrix.md), [`Surrounded_Regions.md`](./Surrounded_Regions.md).
