# Find Eventual Safe States — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_Eventual_Safe_States.md`](../Find_Eventual_Safe_States.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/find-eventual-safe-states/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The lesson: a node is "safe" iff every walk from it eventually terminates — equivalently, iff it can't reach a CYCLE. Detect cycles with 3-COLOR DFS (white/gray/black) and propagate "unsafe" up the call stack.**

**Map of this file (10 sections):**

1. Read the problem
2. What "safe" really means
3. The recursive definition
4. The cycle problem
5. 3-color DFS (white / gray / black)
6. Code
7. Trace it
8. Why it works (proof sketch)
9. Common pitfalls
10. The shape — cycle detection with cached results

---

## 1. Read the problem

You have a directed graph. From any node, you can walk along outgoing edges. A node is **TERMINAL** if it has no outgoing edges.

A node is **SAFE** iff **EVERY** possible walk from it eventually reaches a terminal. Return the sorted list of safe nodes.

**Example:**

Edges:
- `0 → 1, 0 → 2`
- `1 → 2, 1 → 3`
- `2 → 5`
- `3 → 0`
- `4 → 5`
- `5, 6`: terminal

From 0: walk `0 → 1 → 3 → 0 → ...` loops forever → 0 is **unsafe**.
From 4: walk `4 → 5` terminates → 4 is **safe**.
From 2: walk `2 → 5` terminates → 2 is **safe**.

Safe set: `{2, 4, 5, 6}`.

---

## 2. What "safe" really means

A node is safe iff it CAN'T reach a cycle. Equivalently:

- Terminal nodes are safe (no walks at all → trivially "all walks terminate").
- A non-terminal node is safe iff **EVERY out-neighbor is safe**.
- Any node ON a cycle is unsafe (the walk that follows the cycle never terminates).
- Any node that REACHES a cycle (via some neighbor) is unsafe (that walk exists).

---

## 3. The recursive definition

> **Mini-refresher: "safe" is a closed-form recursion with one obstacle.**
>
> ```
> safe(u) = True              if u has no out-edges (terminal)
> safe(u) = all(safe(v) for v in neighbors(u))  otherwise
> ```
>
> This looks like a clean post-order recursion. But it has a problem: if there's a cycle `u → v → u`, computing `safe(u)` needs `safe(v)`, which needs `safe(u)` — infinite loop.

We need to detect "we've re-entered an in-progress node" and treat that as a cycle.

---

## 4. The cycle problem

A "back-edge" to a node still on the recursion stack means we've found a cycle. We need a way to distinguish three states of each node during DFS:

- **Untouched** — DFS hasn't visited this node yet.
- **In progress** — DFS entered this node but hasn't finished it.
- **Finished** — DFS completed; we know if this node is safe.

The classic solution: **3-color DFS.**

---

## 5. 3-color DFS (white / gray / black)

> **Mini-refresher: WHITE / GRAY / BLACK trichotomy.**
>
> - **WHITE (0)** = unvisited.
> - **GRAY (1)** = currently on the DFS stack (in progress).
> - **BLACK (2)** = finished AND safe.
>
> Encountering a GRAY neighbor means a BACK-EDGE → cycle found → current node is unsafe → leave it GRAY (it will never become BLACK).
>
> Finishing DFS without finding a cycle through `u` → upgrade `u` to BLACK.
>
> At the end, `BLACK` = safe; `GRAY` = unsafe (was on a doomed path); `WHITE` doesn't happen if you call DFS on every node.

The two states `GRAY` and `BLACK` carry both "is processed" and "is safe" in a single field.

---

## 6. Code

**C++:**

```cpp
vector<int> eventualSafeNodes(vector<vector<int>>& graph) {
    int n = graph.size();
    enum { WHITE, GRAY, BLACK };
    vector<int> color(n, WHITE);

    function<bool(int)> dfs = [&](int u) -> bool {
        if (color[u] != WHITE) return color[u] == BLACK;   // cached
        color[u] = GRAY;
        for (int v : graph[u]) {
            if (color[v] == GRAY) return false;            // back-edge → cycle
            if (!dfs(v)) return false;                     // neighbor unsafe
        }
        color[u] = BLACK;
        return true;
    };

    for (int u = 0; u < n; ++u) dfs(u);

    vector<int> safe;
    for (int u = 0; u < n; ++u) if (color[u] == BLACK) safe.push_back(u);
    return safe;
}
```

**Python:**

```python
def eventualSafeNodes(graph):
    n = len(graph)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = [WHITE] * n

    def dfs(u):
        if color[u] != WHITE:
            return color[u] == BLACK
        color[u] = GRAY
        for v in graph[u]:
            if color[v] == GRAY:
                return False
            if not dfs(v):
                return False
        color[u] = BLACK
        return True

    for u in range(n):
        dfs(u)
    return [u for u in range(n) if color[u] == BLACK]
```

Complexity: **O(V + E)** time (each node/edge processed once), **O(V)** space.

---

## 7. Trace it

Example graph from section 1.

```
dfs(0): color[0] = GRAY.
  dfs(1): color[1] = GRAY.
    dfs(2): color[2] = GRAY.
      dfs(5): color[5] = GRAY. No neighbors. color[5] = BLACK. Return True.
    All neighbors safe. color[2] = BLACK. Return True.
    dfs(3): color[3] = GRAY.
      Neighbor 0: color[0] == GRAY → BACK-EDGE. Return False.
    color[3] stays GRAY. Return False.
  Neighbor 3 returned False. color[1] stays GRAY. Return False.
Neighbor 1 returned False. color[0] stays GRAY. Return False.

dfs(2): cached BLACK. Skip.
dfs(3): cached non-BLACK (GRAY). Return False.
dfs(4): color[4] = GRAY.
  dfs(5): cached BLACK. Return True.
color[4] = BLACK. Return True.

dfs(5): cached BLACK. dfs(6): color[6] = GRAY → BLACK.

Final colors:
  0: GRAY (unsafe)
  1: GRAY (unsafe)
  2: BLACK (safe)
  3: GRAY (unsafe)
  4: BLACK (safe)
  5: BLACK (safe)
  6: BLACK (safe)

Safe set: {2, 4, 5, 6}.  ✓
```

The back-edge `3 → 0` (with `color[0] == GRAY`) is the moment we discover the cycle and propagate "unsafe" up.

---

## 8. Why it works (proof sketch)

**Claim:** at the end, `color[u] == BLACK` iff u is safe.

- (⇒) If `color[u] == BLACK`, then `dfs(u)` returned True. Inductively, every recursive call from u returned True (no back-edge or unsafe neighbor). So every walk from u eventually reaches a terminal.

- (⇐) If u is safe, then every walk terminates. DFS from u explores all paths; none hit a cycle; all recursive calls return True; u gets marked BLACK.

The key insight: a node stays GRAY at the end of all DFS iff some `dfs(u)` returned False, which happens iff a back-edge or unsafe child was found — both imply u is on or leads to a cycle.

---

## 9. Common pitfalls

1. **Skipping the GRAY check.** Without it, you'd recurse into a cycle forever.
2. **Marking BLACK before recursing.** Then a back-edge wouldn't see GRAY — you'd misidentify a cycle as safe.
3. **Forgetting to reset / cache.** Without the `color[u] != WHITE` short-circuit at the top, repeated DFS calls re-explore — O(V·(V+E)) instead of O(V+E).
4. **Returning the cached value as `color[u] != WHITE`** (just "processed") instead of `color[u] == BLACK` (specifically safe). The former marks unsafe nodes as safe.
5. **Iterating only from node 0.** Multi-component graphs need DFS started from every white node.

---

## 10. The shape — cycle detection with cached results

The pattern: **detect cycles in a directed graph + cache per-node verdicts.**

| Problem | Cycle question |
|---|---|
| **This problem** | which nodes don't reach a cycle? |
| Course Schedule (LC 207) | is there any cycle in prerequisites? |
| Course Schedule II (LC 210) | topological order if no cycle |
| Detect Cycle in Directed Graph | yes/no |
| Longest Path in DAG | requires no cycles |
| Find Redundant Connection II | which edge creates the cycle? |

**Pattern to internalize:**

> "For directed cycle problems, use 3-COLOR DFS. WHITE = unvisited, GRAY = on stack, BLACK = finished. Back-edge = encountering a GRAY neighbor."

The trichotomy makes the algorithm O(V + E) regardless of how many times nodes appear as neighbors elsewhere.

---

> **Self-check — the question to ask next time.**
>
> When the problem says "starting from a node, can we always escape?" or "does every walk terminate?", ask:
>
> > **"Is this 'doesn't reach a cycle'? Run 3-color DFS; BLACK nodes are the answer."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Find_Eventual_Safe_States.md`](../Find_Eventual_Safe_States.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Keys_and_Rooms.md`](./Keys_and_Rooms.md), [`Find_the_Town_Judge.md`](./Find_the_Town_Judge.md).
  - Coming next: [`Is_Graph_Bipartite.md`](./Is_Graph_Bipartite.md), [`Course_Schedule_II.md`](./Course_Schedule_II.md).
