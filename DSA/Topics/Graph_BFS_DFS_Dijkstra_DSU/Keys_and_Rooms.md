# Keys and Rooms

**Problem Link:**
https://leetcode.com/problems/keys-and-rooms/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Read the Problem

There are `n` rooms labeled 0 to n-1. Room 0 is unlocked; all others are locked. Each room `i` contains a list of keys — `rooms[i]` — opening other rooms.

Can you, starting from room 0, collect enough keys to visit **every** room? Return true or false.

Example: `rooms = [[1], [2], [3], []]`.
- Start room 0: has key 1. Visit room 1.
- Room 1: key 2. Visit room 2.
- Room 2: key 3. Visit room 3.
- Room 3: empty.

All rooms visited. Return true.

Example: `rooms = [[1, 3], [3, 0, 1], [2], [0]]`.
- Start room 0: keys 1, 3. Visit rooms 1, 3.
- Room 1: keys 3, 0, 1 — all already visited (0) or re-collected.
- Room 3: key 0 — already visited.
- Room 2: we never collected key 2, so room 2 remains locked.

Return false.

----------------------------------------

## Step 2: It's Just Graph Reachability

Think of rooms as nodes. An edge from room `i` to room `j` exists iff rooms[i] contains key `j`. The graph is directed.

The question becomes: starting from node 0, can we reach **every** other node in this directed graph?

This is classical reachability: do DFS or BFS from node 0, mark all reachable nodes, check if count equals n.

----------------------------------------

## Step 3: DFS / BFS Approach

```
visited = [False] * n
def dfs(u):
    visited[u] = True
    for v in rooms[u]:
        if not visited[v]:
            dfs(v)

dfs(0)
return all(visited)
```

O(V + E) where V is room count and E is total key count across all rooms. Standard.

BFS version uses a queue but same complexity. Either works.

----------------------------------------

## Step 4: Trace on the Failing Example

`rooms = [[1, 3], [3, 0, 1], [2], [0]]`.

```
dfs(0): visited = {0}. Keys: 1, 3.
  dfs(1): visited = {0, 1}. Keys: 3, 0, 1.
    dfs(3): visited = {0, 1, 3}. Keys: 0. Already visited. Return.
  dfs(3) already done. Return.
dfs(0) done.

visited = {0, 1, 3}. Room 2 not visited. Return false.
```

Correct — key 2 was never in any reachable room.

----------------------------------------

## Step 5: Why Reachability Is the Right Frame

The problem's "start in room 0, collect keys, open new rooms" dynamic sounds procedural, but it's identical to "follow edges from node 0 in the directed graph." Each key is an out-edge. Being locked = no inbound key from anywhere reachable.

Framing it as a graph problem gives us the standard algorithmic toolkit (DFS/BFS) and the standard O(V + E) complexity.

----------------------------------------

## Step 6: Implementation Detail — Avoid Revisiting

Without a visited set, DFS on a cycle (like Room 1 → Room 0 which has key 1) would infinite-loop. The `visited` array ensures we process each room at most once.

We visit room 0 first (it's the entry). The `visited[u] = True` sets before exploring children is critical.

----------------------------------------

## Step 7: Name It

**Graph reachability via DFS/BFS from a single source.** Same structure as:
- Number of Connected Components.
- Can We Reach Every Node? (as a variant).
- Reachable Nodes in a Graph (counting variant).

For "can I reach everything from X?" start DFS/BFS from X, count visited, compare.

----------------------------------------

## Step 8: Complexity

Time: **O(V + E)** where V = n rooms and E = total number of keys across all rooms.
Space: **O(V)** for visited + recursion stack (up to depth V).

----------------------------------------

## Step 9: C++ Implementation

```cpp
bool canVisitAllRooms(vector<vector<int>>& rooms) {
    int n = rooms.size();
    vector<bool> visited(n, false);

    function<void(int)> dfs = [&](int u) {
        visited[u] = true;
        for (int v : rooms[u]) {
            if (!visited[v]) dfs(v);
        }
    };

    dfs(0);
    for (bool v : visited) {
        if (!v) return false;
    }
    return true;
}
```

Seven functional lines. DFS from 0, check all visited.

Iterative BFS alternative:

```cpp
bool canVisitAllRooms(vector<vector<int>>& rooms) {
    int n = rooms.size();
    vector<bool> visited(n, false);
    queue<int> q;
    q.push(0);
    visited[0] = true;
    int count = 1;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int v : rooms[u]) {
            if (!visited[v]) {
                visited[v] = true;
                count++;
                q.push(v);
            }
        }
    }
    return count == n;
}
```

Same idea, iterative — safe for deep graphs.

----------------------------------------

## Step 10: Follow-up Questions

- **Count the minimum keys to unlock every room.** Different problem — BFS for levels.
- **Some keys require combinations.** State becomes (room, set of keys held) — can explode.
- **Rooms can change (keys added/removed dynamically).** Requires incremental connectivity.
- **Optimize for sparse graphs.** Already O(V + E); can't do better asymptotically.
- **Why DFS and not Dijkstra here?** No weights or "shortest path" requirement — just reachability.
- **How does this compare to finding connected components?** Connected components find all groups; this just finds the component containing node 0.
