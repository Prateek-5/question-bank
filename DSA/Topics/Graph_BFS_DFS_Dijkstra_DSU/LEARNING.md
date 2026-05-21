# Graph (BFS / DFS / Dijkstra / DSU) — Learning Path

> **Stage:** Trees & Graphs   |   **Prereqs:** [Trees_Binary_Trees/](../Trees_Binary_Trees/LEARNING.md), [Queues_Deque_Monotonic_Queue/](../Queues_Deque_Monotonic_Queue/LEARNING.md), [Heap_Priority_Queue/](../Heap_Priority_Queue/LEARNING.md)   |   **Problems:** 27
>
> The biggest topic. Five sub-patterns: **grid BFS/DFS**, **graph traversal**, **topological sort**, **DSU (union-find)**, **shortest path family** (BFS / Dijkstra / Bellman-Ford / Floyd-Warshall).

---

## How to study this topic

Strict order — each sub-pattern builds on the previous:

1. Grid DFS basics → grid BFS → multi-source BFS → boundary tricks.
2. Graph traversal on adjacency lists (visited set, degree).
3. Bipartite / coloring.
4. Topological sort.
5. Shortest path family (BFS → Dijkstra → Bellman-Ford → Floyd-Warshall).
6. DSU (union-find).
7. Misc / advanced.

---

## Problems in study order

### Grid DFS (start here)

1. **[Number_of_Islands.md](./Number_of_Islands.md)** — DFS flood-fill on grid. **must-do**
2. **[Max_Area_of_Island.md](./Max_Area_of_Island.md)** — Same, track max area.
3. **[Number_of_Provinces.md](./Number_of_Provinces.md)** — Adjacency-matrix DFS or DSU. **must-do**

### Multi-source BFS

4. **[Rotting_Oranges.md](./Rotting_Oranges.md)** — Initialize queue with all sources; BFS levels = time. **must-do**
5. **[01_Matrix.md](./01_Matrix.md)** — Multi-source BFS from all 0s outward. **must-do**

### Boundary DFS

6. **[Surrounded_Regions.md](./Surrounded_Regions.md)** — Mark boundary-reachable Os; flip the rest. **must-do**
7. **[Number_of_Enclaves.md](./Number_of_Enclaves.md)** — Same idea.

### Simple graph DFS/BFS

8. **[Keys_and_Rooms.md](./Keys_and_Rooms.md)** — DFS/BFS; visited set. **must-do**
9. **[Find_the_Town_Judge.md](./Find_the_Town_Judge.md)** — In-degree / out-degree counting.
10. **[Find_Eventual_Safe_States.md](./Find_Eventual_Safe_States.md)** — Reverse-graph topo or DFS with 3-color cycle detection.

### Bipartite / coloring

11. **[Is_Graph_Bipartite.md](./Is_Graph_Bipartite.md)** — BFS coloring; adjacent nodes different colors. **must-do**

### Shortest path — unweighted (BFS)

12. **[Shortest_Path_in_an_Undirected_Graph.md](./Shortest_Path_in_an_Undirected_Graph.md)** — BFS gives shortest path on unweighted graphs. **must-do**
13. **[Shortest_Path_in_Binary_Matrix.md](./Shortest_Path_in_Binary_Matrix.md)** — Grid BFS with 8-direction moves.
14. **[Check_if_There_Is_a_Valid_Path_in_a_Graph.md](./Check_if_There_Is_a_Valid_Path_in_a_Graph.md)** — BFS reachability or DSU.

### Topological sort

15. **[Course_Schedule_II.md](./Course_Schedule_II.md)** — Kahn's algorithm (BFS on in-degree zero) or DFS post-order reversed. **must-do**

### Shortest path — weighted

16. **[Network_Delay_Time.md](./Network_Delay_Time.md)** — Dijkstra (min-heap of distances). **must-do**
17. **[Cheapest_Flights_Within_K_Stops.md](./Cheapest_Flights_Within_K_Stops.md)** — Bellman-Ford limited to K iterations OR Dijkstra with state `(node, stops)`. **must-do**
18. **[Find_the_City_With_the_Smallest_Number_of_Neighbors.md](./Find_the_City_With_the_Smallest_Number_of_Neighbors.md)** — Floyd-Warshall (all-pairs shortest path).

### DSU (union-find)

19. **[Number_of_Operations_to_Make_Network_Connected.md](./Number_of_Operations_to_Make_Network_Connected.md)** — DSU; count components. **must-do**
20. **[Redundant_Connection.md](./Redundant_Connection.md)** — DSU; first edge whose endpoints already connected. **must-do**
21. **[Accounts_Merge.md](./Accounts_Merge.md)** — Map emails to canonical owner via DSU. **must-do**
22. **[Most_Stones_Removed_with_Same_Row_or_Column.md](./Most_Stones_Removed_with_Same_Row_or_Column.md)** — DSU on rows + cols (use `n + col` to distinguish).
23. **[Satisfiability_of_Equality_Equations.md](./Satisfiability_of_Equality_Equations.md)** — Union the equals first; check the not-equals after.

### DP on graph / probability

24. **[Knight_Probability_in_Chessboard.md](./Knight_Probability_in_Chessboard.md)** — DP `prob[k][r][c]`. Iterate K moves.

### Misc / advanced

25. **[Count_Primes.md](./Count_Primes.md)** — Sieve of Eratosthenes (graph-adjacent topic).
26. **[Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md](./Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md)** — BFS on remainders (modular state).
27. **[Minimum_Weight_Cycle.md](./Minimum_Weight_Cycle.md)** — Hardest in the set.

---

## Patterns established

- **Grid DFS:** 4-direction neighbors; mark visited or mutate grid; recurse.
- **Multi-source BFS:** Enqueue ALL sources before the loop; BFS level count = time/distance.
- **Boundary trick:** For "surrounded" / "enclave" problems, walk inward from the boundary.
- **Topological sort (Kahn's):** Maintain in-degree; queue holds nodes with in-degree 0; decrement neighbors when popped.
- **Dijkstra:** Min-heap of `(distance, node)`. Skip stale entries (`if (dist > dist[node]) continue;`).
- **Bellman-Ford limited K:** Relax edges K times, snapshotting `dist[]` each iteration.
- **DSU primitives:** `find(x)` with path compression; `union(x, y)` with rank/size. Both nearly O(1) amortized.
- **DSU for components / equivalence classes:** Equality merges; inequality checks at the end.
- **DSU with virtual nodes:** For 2D row/col equivalence, use `n + col` as a virtual node.

---

## Common traps

- **Forgetting visited set** → infinite loop or duplicate work.
- **Marking visited at pop vs push.** Mark at push (otherwise duplicates enter the queue).
- **Dijkstra with negative weights** — doesn't work; use Bellman-Ford.
- **Multi-source BFS but only one source.** Don't forget multi-source for `01_Matrix` and `Rotting Oranges`.
- **Topological sort on a cyclic graph:** Kahn's leaves some nodes unprocessed → cycle.
- **DSU forgot path compression:** Tree degenerates to linked list; ops become O(n).
- **Disconnected components in shortest-path:** Some nodes unreachable → distance = `Infinity`.

---

## After this topic

- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — graph DP (knight probability, paths on DAG).
- **[Greedy/](../Greedy/LEARNING.md)** — interval scheduling has graph-coloring relatives.
- **[Segment_Tree_Range_Queries/](../Segment_Tree_Range_Queries/LEARNING.md)** — extension of trees + ranges.
