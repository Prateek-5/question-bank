# Keys and Rooms — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Keys_and_Rooms.md`](../Keys_and_Rooms.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/keys-and-rooms/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/keys-and-rooms/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The lesson: a "procedural" story (collect keys, open new doors) is identical to GRAPH REACHABILITY from a single source.** Once you see it, DFS/BFS solves it in O(V + E).

**Map of this file (8 sections):**

1. Read the problem
2. The story-vs-graph reframe
3. The DFS / BFS skeleton
4. Code
5. Trace it
6. Why we need `visited`
7. Common pitfalls
8. The shape — single-source reachability

---

## 1. Read the problem

There are `n` rooms labeled `0..n-1`. Room 0 is unlocked; the rest are locked. Each room `i` contains a list of keys `rooms[i]` — each key opens some specific other room.

Starting in room 0, can you eventually open EVERY room? Return true/false.

**Examples:**

- `rooms = [[1], [2], [3], []]` → start at 0, key 1 opens room 1 (key 2 → room 2 → key 3 → room 3). All open → **true**.
- `rooms = [[1, 3], [3, 0, 1], [2], [0]]` → from 0 we collect keys 1, 3. Room 1 gives keys we already have. Room 3 gives key 0. We never see key 2 → room 2 stays locked → **false**.

---

## 2. The story-vs-graph reframe

> **Mini-refresher: every "explore and collect" puzzle is a graph.**
>
> Treat each room as a NODE. Treat each key `j` in `rooms[i]` as a DIRECTED EDGE `i → j` ("standing in i, I can open j").
>
> The question "can I open every room starting from 0?" becomes "starting at node 0, can I reach every node?" That's classic SINGLE-SOURCE REACHABILITY.

The procedural framing (collect keys, open doors, collect more keys) lures you into writing a fixed-point loop. The graph framing gives you the textbook tool: a single DFS or BFS.

---

## 3. The DFS / BFS skeleton

Standard reachability:

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

Or iteratively with BFS — same idea, queue instead of recursion.

Each room and each key are processed at most once → O(V + E).

---

## 4. Code

**C++ — DFS:**

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
    for (bool v : visited) if (!v) return false;
    return true;
}
```

**C++ — BFS (safer for deep graphs):**

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

Complexity: **O(V + E)** time, **O(V)** space.

---

## 5. Trace it

`rooms = [[1, 3], [3, 0, 1], [2], [0]]`.

```
dfs(0): visited = {0}. Keys: 1, 3.
  dfs(1): visited = {0, 1}. Keys: 3, 0, 1.
    dfs(3): visited = {0, 1, 3}. Keys: 0. Already visited. Return.
    0, 1 already visited. Return.
  dfs(3): already visited. Skipped.
Done.

visited = {0, 1, 3}. Room 2 never visited. Return false.  ✓
```

Key 2 was never in any reachable room, so room 2 can't be opened.

---

## 6. Why we need `visited`

Room 1 has key 0, and room 3 has key 0 — so without `visited`, DFS would re-enter room 0 forever (cycle 0 → 1 → 0). The visited array makes this O(V + E) instead of unbounded.

> **Mini-refresher: visited markers are the difference between DFS terminating and DFS looping.**
>
> Set `visited[u] = True` BEFORE recursing into neighbors — never after — or you'll re-enter u from one of its descendants.

---

## 7. Common pitfalls

1. **Treating the input as undirected.** Keys are one-way: `rooms[i] = [j]` means "i gives access to j," not vice versa. Don't add a reverse edge.
2. **Forgetting `visited[0] = True` in BFS.** You'll enqueue 0 again from one of its neighbors that holds key 0.
3. **Setting visited *after* recursing.** Allows revisits during the recursion.
4. **Counting `len(rooms[u])` keys instead of reachable rooms.** A room may contain duplicate keys or keys to already-open rooms.
5. **Returning false on an empty key list.** A room with no keys is fine — just don't recurse from it.

---

## 8. The shape — single-source reachability

The pattern: **"start at one node; reach the rest? DFS/BFS, O(V + E)."**

| Problem | Source node | Graph |
|---|---|---|
| **This problem** | room 0 | rooms (directed by keys) |
| Reachable Nodes from a Source | given start | given graph |
| Network Delay Time | given start | weighted graph (use Dijkstra) |
| Number of Provinces | every node (components) | undirected friendship |
| Word Ladder | start word | implicit graph over words |

**Pattern to internalize:**

> "If the question is 'starting at X, can I reach Y/all/some set?' — DFS/BFS from X, mark visited, read off the answer. O(V + E)."

---

> **Self-check — the question to ask next time.**
>
> When you see "process state A, which unlocks state B, which unlocks state C...," ask:
>
> > **"Is each transition a directed edge? Then this is reachability — one DFS from the start node."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Keys_and_Rooms.md`](../Keys_and_Rooms.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Islands.md`](./Number_of_Islands.md), [`Number_of_Provinces.md`](./Number_of_Provinces.md).
  - Coming next: [`Find_the_Town_Judge.md`](./Find_the_Town_Judge.md), [`Find_Eventual_Safe_States.md`](./Find_Eventual_Safe_States.md), [`Is_Graph_Bipartite.md`](./Is_Graph_Bipartite.md).
