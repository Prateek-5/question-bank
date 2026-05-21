# DSA — Learning Path

A topic ordering and study sequence for the 22 topics in this repo. Each topic folder has its own `LEARNING.md` that breaks problems into sub-patterns + study order; this file is the **macro** view across topics.

---

## How to use this file

- Each stage builds on the previous one. Don't skip stages even if a later topic looks more "interesting" — pattern recognition compounds.
- Within a stage, topics can be done in parallel if you prefer.
- For each topic: open its `LEARNING.md` first, NOT the alphabetical file list.
- `Concepts.md` in each topic is the **theory primer**; `LEARNING.md` is the **navigator**. Read Concepts first, then follow LEARNING's problem sequence.
- For a tight interview prep, attempt only the problems marked **must-do** in each topic's LEARNING.md.

---

## Stage 1 — Foundations (start here)

The "you must know these by reflex" tier. Skipping this stage breaks every later topic.

1. **[Arrays_and_Matrices/](./Topics/Arrays_and_Matrices/LEARNING.md)** — basic scans, simulation, matrix access.
2. **[1_D_and_2_D_Arrays/](./Topics/1_D_and_2_D_Arrays/LEARNING.md)** — prefix sums (1D + 2D), index mapping.
3. **[Two_Pointers/](./Topics/Two_Pointers/LEARNING.md)** — sorted-array two-pointer, k-sum, partitioning.
4. **[Hashing_Sliding_Window/](./Topics/Hashing_Sliding_Window/LEARNING.md)** — hash for O(1) lookup, fixed + variable window.
5. **[Stack/](./Topics/Stack/LEARNING.md)** — balanced parens, monotonic stack, expression eval.
6. **[Linked_List/](./Topics/Linked_List/LEARNING.md)** — dummy head, slow/fast, in-place reverse, cycle detection.
7. **[Searching_Binary_Search/](./Topics/Searching_Binary_Search/LEARNING.md)** — lower/upper bound, rotated array, binary search on answer.

---

## Stage 2 — Structures & Idioms

Specialized data structures and the algorithmic shapes that use them.

8. **[Math/](./Topics/Math/LEARNING.md)** — GCD, divisibility, digit ops.
9. **[Bit_Manipulation/](./Topics/Bit_Manipulation/LEARNING.md)** — popcount, XOR tricks, bit reversal.
10. **[Queues_Deque_Monotonic_Queue/](./Topics/Queues_Deque_Monotonic_Queue/LEARNING.md)** — stack ↔ queue, monotonic deque windows.
11. **[Sorting_Divide_and_Conquer/](./Topics/Sorting_Divide_and_Conquer/LEARNING.md)** — Dutch flag, quickselect, merge-sort applications.
12. **[Recursion/](./Topics/Recursion/LEARNING.md)** — choose / explore / unchoose; subsets & permutations.
13. **[Backtracking/](./Topics/Backtracking/LEARNING.md)** — pruning, constraint satisfaction.

---

## Stage 3 — Trees & Graphs

Hierarchical and graph structures. Tree problems are graph problems with fewer edges, so do Trees first.

14. **[Trees_Binary_Trees/](./Topics/Trees_Binary_Trees/LEARNING.md)** — pre/in/post/level traversal, path problems, construction.
15. **[Binary_Search_Tree_BST/](./Topics/Binary_Search_Tree_BST/LEARNING.md)** — BST property, inorder = sorted, LCA.
16. **[Trie_Bit_Manipulation_Trie/](./Topics/Trie_Bit_Manipulation_Trie/LEARNING.md)** — prefix tree, XOR trie.
17. **[Heap_Priority_Queue/](./Topics/Heap_Priority_Queue/LEARNING.md)** — top-K, K-way merge, two-heap median.
18. **[Graph_BFS_DFS_Dijkstra_DSU/](./Topics/Graph_BFS_DFS_Dijkstra_DSU/LEARNING.md)** — grid traversal, topo sort, DSU, shortest path family.

---

## Stage 4 — Optimization & Advanced

Pattern-heavy and harder. Strongest signal of senior bar.

19. **[Greedy/](./Topics/Greedy/LEARNING.md)** — sort-and-pick, interval scheduling, exchange argument.
20. **[Dynamic_Programming_DP/](./Topics/Dynamic_Programming_DP/LEARNING.md)** — 1D / 2D / grid / sequence / partition / interval / digit DP.
21. **[Segment_Tree_Range_Queries/](./Topics/Segment_Tree_Range_Queries/LEARNING.md)** — range queries with updates, lazy propagation.
22. **[Number_Theory_Misc/](./Topics/Number_Theory_Misc/LEARNING.md)** — primes, divisors, ad-hoc puzzles.

---

## Cross-cutting study tracks

If you're prepping for a specific interview type, follow one of these tracks instead of stage-by-stage:

### Fast-track (2-week sprint for a near-term interview)

Only the **must-do** problems from these topics, in this order:

1. Arrays_and_Matrices → 1_D_and_2_D_Arrays → Two_Pointers → Hashing_Sliding_Window
2. Stack → Linked_List → Searching_Binary_Search
3. Trees_Binary_Trees → BST → Heap_Priority_Queue
4. Graph_BFS_DFS_Dijkstra_DSU
5. Dynamic_Programming_DP (must-do tier only)
6. Recursion + Backtracking

That's ~80 problems vs all 230.

### "Frontend / fullstack" interview track

Less graph, more strings + arrays + DP-light:

Arrays_and_Matrices → Two_Pointers → Hashing_Sliding_Window → Stack → Linked_List → Trees_Binary_Trees → Recursion → DP (1D + LIS/LCS subset).

### "Backend / systems" interview track

More graph + DSU + heap (resource allocation, scheduling):

Stage 1 essentials → Heap → Graph (full) → Greedy (intervals/scheduling) → DP (knapsack subset) → Segment Tree.

### Competitive programming track

Add Number_Theory_Misc, Segment_Tree (full), Trie XOR variants, Bit Manipulation, and harder DP/Graph problems beyond must-do tier.

---

## Companion files in this repo

- **[`README.md`](./README.md)** — what's inside per problem.
- **[`CPP_Concepts.md`](./CPP_Concepts.md)** — STL + C++ idioms used in solutions.
- **[`Cheat_Sheet.md`](./Cheat_Sheet.md)** — complexity targets, patterns at a glance.
- **[`Quick_Revision_Guide.md`](./Quick_Revision_Guide.md)** — pre-interview skim.

---

## Per-problem study loop (recommended)

For each problem in a topic's `LEARNING.md`:

1. **Read only the problem link.** Think for 10-15 minutes. Write your plan.
2. **If stuck:** open the question file. Read sections in order — Core Concept → Intuition → Approach. Stop before the code.
3. **Implement.** Don't peek at the C++ solution.
4. **Compare.** Note differences in edge-case handling and complexity. Don't memorize — internalize the *shape*.
5. **Re-derive in 24h.** Real test: can you re-solve tomorrow without notes? If not, mark for re-attempt in 3 days.

A problem you can re-derive cold in under 15 minutes is a problem you own.
