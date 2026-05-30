# Course Schedule II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Course_Schedule_II.md`](../Course_Schedule_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/course-schedule-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/course-schedule-ii/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The lesson: "do A before B" + "find a valid order" = TOPOLOGICAL SORT. KAHN'S BFS works by repeatedly removing zero-in-degree nodes. If the output is short of n, a CYCLE exists — no valid order.**

**Map of this file (10 sections):**

1. Read the problem
2. The graph reframe
3. Why a topological order exists iff no cycle
4. Kahn's algorithm (BFS in-degree)
5. Code
6. Trace it
7. Cycle detection — fall-out, no extra work
8. DFS post-order alternative
9. Common pitfalls
10. The shape — topological sort

---

## 1. Read the problem

`numCourses` courses labeled `0..numCourses-1`. A pair `prerequisites[i] = [a, b]` means "to take a, you must first finish b."

Return ANY valid order of courses. If no valid order exists (because of a cycle), return `[]`.

**Examples:**

- `numCourses = 4, prerequisites = [[1,0], [2,0], [3,1], [3,2]]` → 0 unlocks 1 and 2; both unlock 3. Valid order: `[0, 1, 2, 3]` (or `[0, 2, 1, 3]`).
- `numCourses = 2, prerequisites = [[0,1], [1,0]]` → cycle. Return `[]`.

---

## 2. The graph reframe

> **Mini-refresher: precedence is a DIRECTED edge.**
>
> `[a, b]` means "b before a" → directed edge **b → a** ("b unlocks a").
>
> Each course = node. Each prerequisite pair = directed edge. We want a linear order of nodes such that every edge u → v has u BEFORE v in the output. That's the definition of a TOPOLOGICAL ORDER.

---

## 3. Why a topological order exists iff no cycle

If `a → b → c → a` (a cycle), then a must come before b, b before c, and c before a — impossible.

Conversely, any DAG (directed acyclic graph) admits a topological order — pick a node with no incoming edge (must exist; otherwise tracing predecessors forever produces a cycle), output it, remove it, repeat.

So: **valid order exists iff graph is a DAG.** Cycle ⇔ no order.

---

## 4. Kahn's algorithm (BFS in-degree)

> **Mini-refresher: Kahn's algorithm = repeatedly remove zero-in-degree nodes.**
>
> 1. Compute `indegree[v]` for every node (how many prerequisites it has).
> 2. Initialize a queue with every node whose indegree is 0 (no prerequisites — ready immediately).
> 3. While queue non-empty:
>    - Pop u, append to output.
>    - For each neighbor v (course that u unlocks), decrement `indegree[v]`. If it hits 0, enqueue v.
> 4. If `len(output) == numCourses`, return output. Else cycle → return `[]`.

The pop order is a valid topological order. Cycle detection is automatic: nodes in a cycle never reach indegree 0, so they're never enqueued, so the output is short.

---

## 5. Code

**C++:**

```cpp
vector<int> findOrder(int numCourses, vector<vector<int>>& prerequisites) {
    vector<vector<int>> graph(numCourses);
    vector<int> indegree(numCourses, 0);
    for (auto& p : prerequisites) {
        int a = p[0], b = p[1];   // b → a
        graph[b].push_back(a);
        indegree[a]++;
    }

    queue<int> q;
    for (int i = 0; i < numCourses; ++i) {
        if (indegree[i] == 0) q.push(i);
    }

    vector<int> order;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        order.push_back(u);
        for (int v : graph[u]) {
            if (--indegree[v] == 0) q.push(v);
        }
    }

    return (int)order.size() == numCourses ? order : vector<int>{};
}
```

**Python:**

```python
from collections import deque

def findOrder(numCourses, prerequisites):
    graph = [[] for _ in range(numCourses)]
    indegree = [0] * numCourses
    for a, b in prerequisites:
        graph[b].append(a)
        indegree[a] += 1

    q = deque(i for i in range(numCourses) if indegree[i] == 0)
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in graph[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                q.append(v)

    return order if len(order) == numCourses else []
```

Complexity: **O(V + E)** time, **O(V + E)** space.

---

## 6. Trace it

**`numCourses = 4, prerequisites = [[1,0], [2,0], [3,1], [3,2]]`:**

Build:
```
graph[0] = [1, 2]
graph[1] = [3]
graph[2] = [3]
graph[3] = []
indegree = [0, 1, 1, 2]
```

Initial queue: nodes with indegree 0 → `[0]`.

```
Pop 0. order = [0].
  graph[0] = [1, 2]. indegree[1] 1→0 (enqueue). indegree[2] 1→0 (enqueue).
  queue = [1, 2].

Pop 1. order = [0, 1].
  graph[1] = [3]. indegree[3] 2→1. Not yet 0.

Pop 2. order = [0, 1, 2].
  graph[2] = [3]. indegree[3] 1→0. Enqueue.

Pop 3. order = [0, 1, 2, 3].

Queue empty. len(order) == 4 == numCourses → return [0, 1, 2, 3].  ✓
```

**Cycle example: `numCourses = 2, prerequisites = [[0,1], [1,0]]`.**

```
indegree = [1, 1]. Queue starts empty.

Loop doesn't run. order = []. len = 0 ≠ 2 → return [].  ✓
```

---

## 7. Cycle detection — fall-out, no extra work

> **Mini-refresher: if the output is short, the rest must be in/around a cycle.**
>
> Every DAG node eventually reaches indegree 0 (after its predecessors are processed). If a node never reaches 0, it has at least one prerequisite that's also stuck — a cycle.
>
> The size check `len(order) == numCourses` is the cycle test. Free.

This is one of Kahn's biggest selling points compared to DFS — no separate cycle-detection logic.

---

## 8. DFS post-order alternative

You can also topo-sort via DFS:
- DFS from each unvisited node.
- After exploring all descendants of u, PREPEND u to the output (post-order, reversed).
- Use 3-color cycle detection: WHITE/GRAY/BLACK — back-edge means cycle.

```python
def findOrder_dfs(numCourses, prerequisites):
    graph = [[] for _ in range(numCourses)]
    for a, b in prerequisites:
        graph[b].append(a)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = [WHITE] * numCourses
    order = []

    def dfs(u):
        color[u] = GRAY
        for v in graph[u]:
            if color[v] == GRAY: return False
            if color[v] == WHITE and not dfs(v): return False
        color[u] = BLACK
        order.append(u)
        return True

    for u in range(numCourses):
        if color[u] == WHITE and not dfs(u): return []
    order.reverse()
    return order
```

Same O(V + E). I prefer Kahn's for this problem — cycle detection is automatic and the iterative form avoids deep recursion.

---

## 9. Common pitfalls

1. **Reversed edge direction.** `[a, b]` means "b before a" — edge b → a (not a → b). Easy to flip and get wrong answers.
2. **Forgetting to seed the queue with ALL zero-indegree nodes.** Multiple "root" courses can exist.
3. **Using indegree decrement without the `== 0` check.** Enqueuing nodes that still have pending prerequisites breaks correctness.
4. **Counting visited nodes instead of `len(order)`.** Subtle — same number, but make sure you're checking the recorded sequence, not just visits.
5. **Returning the order even if a cycle exists.** Length check is non-negotiable.
6. **Building only one direction of edges.** Topo sort uses directed edges only — no reverse.

---

## 10. The shape — topological sort

The pattern: **linear order respecting precedence on a DAG.**

| Problem | Twist |
|---|---|
| **This problem** | return any valid order |
| Course Schedule I (LC 207) | just "is it possible?" |
| Alien Dictionary | infer letter order from word list |
| Minimum Height Trees | reverse Kahn from leaves |
| Parallel Courses (LC 1136) | semester count, BFS in levels |
| Sort Items by Groups (LC 1203) | two-level topological sort |
| Build dependency resolution | classic real-world topo sort |

**Pattern to internalize:**

> "Precedence + linear order = topological sort. KAHN'S BFS with in-degrees: cycle detection is free; output a valid order in O(V + E)."

When you need parallel processing, modify Kahn's to process all currently-ready nodes per iteration ("BFS by levels").

---

> **Self-check — the question to ask next time.**
>
> When the problem says "do X before Y, find an order to do everything," ask:
>
> > **"Is this topological sort? Build adjacency + indegrees, seed queue with indegree-0 nodes, peel. Cycle if order is short."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Course_Schedule_II.md`](../Course_Schedule_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Find_Eventual_Safe_States.md`](./Find_Eventual_Safe_States.md), [`Is_Graph_Bipartite.md`](./Is_Graph_Bipartite.md).
  - Coming next: [`Network_Delay_Time.md`](./Network_Delay_Time.md), [`Cheapest_Flights_Within_K_Stops.md`](./Cheapest_Flights_Within_K_Stops.md).
