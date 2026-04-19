# Course Schedule II

**Problem Link:**
https://leetcode.com/problems/course-schedule-ii/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Translate the Problem

You have `numCourses` courses labeled `0` to `numCourses-1`. Some courses have **prerequisites**: a pair `[a, b]` means "to take course `a`, you must first finish course `b`". Return any valid order to finish all courses. If it's impossible (there's a cycle), return an empty array.

Example: `numCourses = 4`, `prerequisites = [[1,0], [2,0], [3,1], [3,2]]`.

Reading it:
- Course 1 depends on 0.
- Course 2 depends on 0.
- Course 3 depends on 1 and 2.

So we must start with 0, then do 1 and 2 (in either order), then 3. A valid output: `[0, 1, 2, 3]` or `[0, 2, 1, 3]`.

----------------------------------------

## Step 2: Think About It As a Graph

Each course is a node. The pair `[a, b]` says `b → a` (take `b`, then `a` is unlocked). These directed edges describe a **precedence graph**.

A valid finishing order is exactly a **linear ordering of the nodes** where, for every edge `b → a`, `b` comes before `a`. In graph theory, this is called a **topological ordering**.

Key observation: a topological ordering exists iff the graph has **no cycle**. If courses form a cycle (say `a → b → c → a`), then `a` depends on `b`, which depends on `c`, which depends on `a` — impossible to finish any of them first.

----------------------------------------

## Step 3: First Idea — Repeatedly Finish Courses With No Pending Prerequisites

At any moment, a course is "ready to be taken" if all its prerequisites have been finished. At time 0, ready courses are those with **no prerequisites at all** (in-degree 0 in the graph).

Once we take a ready course `u`, we mark it done. That might unblock its dependents — for each edge `u → v`, `v` has one fewer pending prerequisite. If `v` now has zero pending prerequisites, it becomes ready.

Repeat: pick a ready course, record it, decrement its dependents' counters, add any newly-ready ones to the ready pool.

When the ready pool is empty:
- If we've recorded all `numCourses` courses, great — we have a valid order.
- Otherwise, the remaining courses must be in a cycle (or depend on one), so no valid order exists.

----------------------------------------

## Step 4: Making It Concrete

1. Build the graph as an adjacency list: `graph[b]` = list of courses that depend on `b`.
2. Compute `indegree[a]` = number of prerequisites `a` has.
3. Initialize a queue with all courses having `indegree == 0`.
4. While the queue is non-empty:
   - Pop `u`. Append to output.
   - For each `v` in `graph[u]`, decrement `indegree[v]`. If it hits 0, enqueue `v`.
5. If output size equals `numCourses`, return output. Else return empty.

This is **Kahn's algorithm** for topological sort. But again — we derived it from first principles ("find ready courses, process them, update dependents") without naming it first.

----------------------------------------

## Step 5: Trace on the Example

`numCourses = 4`, `prerequisites = [[1,0], [2,0], [3,1], [3,2]]`.

Build:
- `graph[0] = [1, 2]` (0's completion unlocks 1 and 2).
- `graph[1] = [3]`.
- `graph[2] = [3]`.
- `graph[3] = []`.
- `indegree = [0, 1, 1, 2]`.

Initial ready queue: courses with in-degree 0. Only course 0. `q = [0]`.

```
Iter 1: pop 0. output = [0].
  graph[0] = [1, 2]. Decrement indegree[1] → 0, indegree[2] → 0.
  Enqueue both. q = [1, 2].

Iter 2: pop 1. output = [0, 1].
  graph[1] = [3]. indegree[3] 2 → 1. Not yet 0.
  q = [2].

Iter 3: pop 2. output = [0, 1, 2].
  graph[2] = [3]. indegree[3] 1 → 0. Enqueue.
  q = [3].

Iter 4: pop 3. output = [0, 1, 2, 3].
  graph[3] = []. Nothing to update.
  q = [].

Queue empty. output.size() == numCourses → return [0, 1, 2, 3].
```

Valid. ✓

Let me also imagine a cyclic case: `numCourses = 2`, `prerequisites = [[0,1], [1,0]]`. Both have in-degree 1. Initial queue empty. Loop doesn't run. output.size() = 0 ≠ 2. Return `[]`. ✓

----------------------------------------

## Step 6: Why In-Degree 0 Always Corresponds to "No Pending Prerequisites"

**Invariant:** when we enqueue a node, all of its prerequisites have already been processed (added to output).

Base: nodes with original in-degree 0 have no prerequisites, so the invariant holds trivially.

Induction: when we enqueue `v`, it's because its in-degree just hit 0 as a consequence of popping its last outstanding prerequisite. That prerequisite was added to output (by the popping step). So all of `v`'s prerequisites are in output. ✓

This invariant guarantees that the output order respects all precedence constraints.

----------------------------------------

## Step 7: Alternative — DFS-Based Topological Sort

A completely different way to compute a topological order: do a **post-order DFS** and reverse the result. At each node, finish exploring its descendants before marking it "done." Prepend done nodes to the output (equivalently, append and reverse at the end).

Cycle detection comes from coloring: WHITE = unvisited, GRAY = on stack, BLACK = done. If DFS encounters a GRAY node, cycle detected.

Both Kahn's BFS and DFS post-order are valid topological sorts. I prefer Kahn's for this problem because cycle detection falls out naturally ("didn't all nodes get processed?") without needing colors.

----------------------------------------

## Step 8: Complexity

Time: we touch every node and every edge exactly once. **O(V + E)** where V = numCourses and E = number of prerequisites.

Space: graph and in-degree arrays are O(V + E). Queue holds at most V. **O(V + E)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
vector<int> findOrder(int numCourses, vector<vector<int>>& prerequisites) {
    vector<vector<int>> graph(numCourses);
    vector<int> indegree(numCourses, 0);
    for (auto& p : prerequisites) {
        int a = p[0], b = p[1];   // b must come before a
        graph[b].push_back(a);
        indegree[a]++;
    }

    queue<int> q;
    for (int i = 0; i < numCourses; ++i)
        if (indegree[i] == 0) q.push(i);

    vector<int> order;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        order.push_back(u);
        for (int v : graph[u])
            if (--indegree[v] == 0) q.push(v);
    }

    return (int)order.size() == numCourses ? order : vector<int>{};
}
```

Notice the `--indegree[v] == 0` shorthand — decrement and check in one step. Common and clean.

----------------------------------------

## Step 10: Follow-up Questions

- **Just detect if all courses can be finished (Course Schedule I).** Same algorithm, but we only care whether the output size equals numCourses.
- **Find the minimum number of semesters to finish all courses (one per semester limit is 0).** BFS by levels: each level processes all currently-ready courses in parallel.
- **Return the lexicographically smallest valid order.** Use a min-heap instead of a queue, so we always pop the smallest ready course.
- **Handle duplicate edges or self-loops.** Deduplicate when building; self-loops immediately mean a cycle (in-degree ≥ 1 forever).
- **Dynamic course additions/removals.** Incremental topological sort — harder, uses ordered data structures; beyond scope here.
