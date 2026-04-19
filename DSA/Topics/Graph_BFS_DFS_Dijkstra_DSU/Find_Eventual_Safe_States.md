# Find Eventual Safe States

**Problem Link:**
https://leetcode.com/problems/find-eventual-safe-states/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: What Makes a Node "Safe"?

You have a directed graph. From any node, you can start walking along outgoing edges. A **terminal** node has no outgoing edges — once you reach one, your walk ends.

A node is called **safe** if **every possible walk** from it eventually reaches a terminal. Otherwise, some walk from it can get stuck in an infinite loop (a cycle).

Return the list of safe nodes, sorted ascending.

----------------------------------------

## Step 2: Play With a Small Example

Graph (directed edges):
- 0 → 1, 0 → 2
- 1 → 2, 1 → 3
- 2 → 5
- 3 → 0
- 4 → 5
- 5: terminal
- 6: terminal

From node 0:
- Path 0 → 1 → 3 → 0 → 1 → 3 → ... cycle. Not all walks terminate. So 0 is **not safe**.

From node 4:
- Only edge: 4 → 5 (terminal). All walks from 4 reach 5. **Safe**.

From node 2:
- Only edge: 2 → 5 (terminal). **Safe**.

From node 1:
- Edge 1 → 2 (safe, leads to terminal). Edge 1 → 3.
- 1 → 3 → 0 → ... cycle. So 1 is **not safe**.

Terminal nodes 5, 6 are trivially safe.

Safe set: {2, 4, 5, 6}.

----------------------------------------

## Step 3: Rephrase "Safe" Recursively

Look at the pattern. A node is safe iff **all of its out-neighbors are safe**.

- Terminal nodes (no out-neighbors) are safe vacuously — the condition "all out-neighbors are safe" holds over an empty set.
- A node with all safe out-neighbors is safe.
- A node with even one unsafe out-neighbor (or a self-loop, or a cycle) is unsafe.

This is the kind of recursive definition that screams "DP or BFS on graphs." But there's a subtlety: cycles. When two nodes point at each other, we can't say "A is safe iff B is safe" because we'd loop forever.

We need a way to resolve the cycle issue.

----------------------------------------

## Step 4: First Attempt — DFS with Cycle Detection

Do DFS from each node, tracking which nodes are currently on the path. If we encounter a node already on the current path, that's a cycle — current node (and all path ancestors to the cycle) are unsafe.

Use three colors:
- WHITE (unvisited) = not processed yet.
- GRAY (on stack) = currently being explored via DFS.
- BLACK (finished) = DFS from this node has completed.

Algorithm:
- When entering a WHITE node, mark it GRAY.
- If we see a GRAY neighbor during exploration, we found a back-edge (cycle). The current node is unsafe.
- If all outgoing edges lead to safe (BLACK with "safe" attribute) nodes, the current node is safe.
- After exploring all neighbors without finding a cycle, mark the current node as safe and BLACK.

Key observation: once we've fully processed a node (BLACK), we know if it's safe or not. So future DFS visits just read the cached answer.

----------------------------------------

## Step 5: Let Me Trace DFS

Using the example graph:

```
0 → 1, 2     1 → 2, 3     2 → 5     3 → 0     4 → 5     5: (terminal)     6: (terminal)
```

Start DFS from 0.

```
dfs(0): color[0] = GRAY.
  Explore 0 → 1. dfs(1): color[1] = GRAY.
    Explore 1 → 2. dfs(2): color[2] = GRAY.
      Explore 2 → 5. dfs(5): color[5] = GRAY. No edges. color[5] = BLACK. Safe.
      5 returned safe. Continue.
      (no more edges for 2)
      color[2] = BLACK. Safe.
    2 returned safe. Continue with 1's edges.
    Explore 1 → 3. dfs(3): color[3] = GRAY.
      Explore 3 → 0. color[0] = GRAY. CYCLE DETECTED. 3 is unsafe.
      color[3] = BLACK. Unsafe.
    3 returned unsafe. So 1 is unsafe (at least one unsafe out-neighbor).
    color[1] = BLACK. Unsafe.
  1 returned unsafe. So 0 is unsafe.
  color[0] = BLACK. Unsafe.

dfs(4): color[4] = GRAY.
  Explore 4 → 5. 5 is BLACK, safe. Continue.
  color[4] = BLACK. Safe.

dfs(5), dfs(6): already handled or trivial terminals.

Final: color[] and safety:
  0: unsafe, 1: unsafe, 2: safe, 3: unsafe, 4: safe, 5: safe, 6: safe.
```

Safe nodes: {2, 4, 5, 6}. ✓

The key moment was dfs(3) seeing GRAY on node 0, which told us 3 is on a cycle → unsafe. This propagated up: 1 is unsafe (because it has unsafe 3 as neighbor), and 0 is unsafe (because it has unsafe 1 as neighbor).

----------------------------------------

## Step 6: Formalizing the DFS Code

Instead of a separate "safe" flag, we can encode everything in the color:
- WHITE = 0 (unvisited).
- GRAY = 1 (on stack, possibly part of cycle).
- BLACK = 2 (finished, safe).

We mark a node GRAY at entry. If DFS completes without finding a cycle through this node, we upgrade to BLACK. Otherwise, leave as GRAY (indicating unsafe; we'll never upgrade it).

Wait — after DFS returns, we want to distinguish "safe and processed" from "unsafe and processed." If we always transition GRAY → BLACK at the end, we lose that distinction.

Solution: only transition to BLACK if the DFS found no cycle. If a cycle was found, leave the node as GRAY (conceptually "unsafe processed"). Then after all DFS calls, a node is safe iff its color is BLACK.

```
colors = [WHITE] * n

def dfs(u):
    if colors[u] != WHITE:
        return colors[u] == BLACK   # revisit: return cached safety
    colors[u] = GRAY
    for v in graph[u]:
        if colors[v] == GRAY or not dfs(v):
            return False   # cycle or unsafe neighbor → this node unsafe
    colors[u] = BLACK
    return True

for u in 0..n-1:
    dfs(u)

safe = [u for u in 0..n-1 if colors[u] == BLACK]
```

The `colors[v] == GRAY` check detects a back-edge on a currently-exploring path. If found, return False immediately — don't upgrade to BLACK, leaving us GRAY → unsafe.

If all out-neighbors are safe (BLACK), we transition to BLACK and return True.

----------------------------------------

## Step 7: Why This Works

Inductive argument: after all dfs calls return, colors[u] is BLACK iff u is safe.

- **Terminal nodes** have no out-edges. DFS enters GRAY, the for-loop does nothing, upgrade to BLACK. ✓
- **Nodes with all safe out-neighbors** get upgraded to BLACK (no loop detection, no recursive-false return). ✓
- **Nodes with at least one unsafe out-neighbor** fail the recursive dfs(v) (returns False) or see GRAY (back-edge), returning False without upgrading. Color stays GRAY. ✓

So at the end, BLACK nodes are exactly the safe ones.

----------------------------------------

## Step 8: Alternative — Kahn-Style BFS (Optional)

The DFS approach is clean. There's also a BFS approach using in-degrees on the **reversed graph**, which some prefer.

Reverse all edges. Now terminals (in the original) become "source-only" (in-degree 0) in the reversed graph. Start BFS from those. Process nodes in reverse-topological order; confirm each as safe once all its reverse-neighbors have been processed.

This is Kahn's topological sort applied backward. Works fine, but the DFS version is more natural for this problem.

----------------------------------------

## Step 9: Complexity

Time: **O(V + E)** — each node and edge processed once.
Space: **O(V)** for colors and recursion stack.

----------------------------------------

## Step 10: C++ Implementation

```cpp
vector<int> eventualSafeNodes(vector<vector<int>>& graph) {
    int n = graph.size();
    const int WHITE = 0, GRAY = 1, BLACK = 2;
    vector<int> color(n, WHITE);

    function<bool(int)> dfs = [&](int u) -> bool {
        if (color[u] != WHITE) return color[u] == BLACK;

        color[u] = GRAY;
        for (int v : graph[u]) {
            if (color[v] == GRAY) return false;   // back-edge: cycle
            if (!dfs(v)) return false;             // neighbor is unsafe
        }
        color[u] = BLACK;
        return true;
    };

    for (int u = 0; u < n; ++u) dfs(u);

    vector<int> safe;
    for (int u = 0; u < n; ++u) {
        if (color[u] == BLACK) safe.push_back(u);
    }
    return safe;
}
```

Clean. The `if (color[u] != WHITE) return color[u] == BLACK;` at the top handles cached answers — for GRAY nodes encountered mid-DFS, this doesn't fire because we check `color[v] == GRAY` before calling `dfs(v)`.

----------------------------------------

## Step 11: Follow-up Questions

- **Return unsafe nodes instead.** Just flip the condition.
- **Detect and list the cycles themselves.** More work during DFS: track the path; on back-edge, report the cycle.
- **Multiple DFS colorings (e.g., for different properties).** Similar framework, different invariants.
- **Graph modifications (add/remove edges).** DSU doesn't help here; full re-run after each change.
- **Why do we say "GRAY means unsafe" at the end?** Because the only way to stay GRAY is to return False somewhere — either a back-edge or an unsafe child. Both imply unsafe.
- **What if multiple components exist?** The outer loop `for u in 0..n-1` starts DFS from every node, so disconnected components are handled.
