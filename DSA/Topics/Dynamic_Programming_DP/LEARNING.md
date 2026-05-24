# Dynamic Programming — Learning Path

> **Stage:** Advanced   |   **Prereqs:** [Recursion/](../Recursion/LEARNING.md), [Arrays_and_Matrices/](../Arrays_and_Matrices/LEARNING.md)   |   **Problems:** 28
>
> The biggest, hardest topic. Eight sub-patterns; do them in order. Each pattern unlocks a class of problems.
>
> **Two-tier format:** each problem has a **reference card** (linked first below) AND a paced **teaching walkthrough** in [`learn/`](./learn/) for first-time learners.

---

## How to study this topic

Strict order, do not jump ahead:

1. **1D linear DP** — Fibonacci-shape; cement the recurrence reflex.
2. **Grid DP** — 2D `dp[i][j] = combine(dp[i-1][j], dp[i][j-1])`.
3. **String DP — sequences** — LIS, LCS family.
4. **String DP — matching** — edit distance, interleaving, regex.
5. **Knapsack** — 0/1, subset sum, partition.
6. **Interval DP** — `dp[i][j]` for ranges.
7. **DP + stack / hybrid** — Maximal Rectangle.
8. **Reverse / digit DP** — Dungeon Game; digit-constrained counting.

For each problem: try to **derive the recurrence by hand**, then check.

---

## Problems in study order

### 1D linear DP — Fibonacci family

1. **[Climbing_Stairs.md](./Climbing_Stairs.md)**  ·  [walkthrough →](./learn/Climbing_Stairs.md) — `f(n) = f(n-1) + f(n-2)`. THE intro. **must-do**
2. **[Min_Cost_Climbing_Stairs.md](./Min_Cost_Climbing_Stairs.md)**  ·  [walkthrough →](./learn/Min_Cost_Climbing_Stairs.md) — Variant with costs.
3. **[Maximum_Subarray.md](./Maximum_Subarray.md)**  ·  [walkthrough →](./learn/Maximum_Subarray.md) — Kadane: `dp[i] = max(nums[i], dp[i-1] + nums[i])`. **must-do**

### Grid DP

4. **[Unique_Paths.md](./Unique_Paths.md)**  ·  [walkthrough →](./learn/Unique_Paths.md) — `dp[i][j] = dp[i-1][j] + dp[i][j-1]`. **must-do**
5. **[Unique_Paths_II.md](./Unique_Paths_II.md)**  ·  [walkthrough →](./learn/Unique_Paths_II.md) — With obstacles.
6. **[Minimum_Path_Sum.md](./Minimum_Path_Sum.md)**  ·  [walkthrough →](./learn/Minimum_Path_Sum.md) — Cost grid; min-sum path. **must-do**
7. **[Triangle.md](./Triangle.md)**  ·  [walkthrough →](./learn/Triangle.md) — Bottom-up rows; in-place. **must-do**

### String DP — sequences (LIS, LCS family)

8. **[Longest_Increasing_Subsequence.md](./Longest_Increasing_Subsequence.md)**  ·  [walkthrough →](./learn/Longest_Increasing_Subsequence.md) — `dp[i]` = LIS ending at i; O(n²) or O(n log n) with binary search. **must-do**
9. **[Longest_Arithmetic_Subsequence.md](./Longest_Arithmetic_Subsequence.md)**  ·  [walkthrough →](./learn/Longest_Arithmetic_Subsequence.md) — `dp[i][diff]` (map per i).
10. **[Russian_Doll_Envelopes.md](./Russian_Doll_Envelopes.md)**  ·  [walkthrough →](./learn/Russian_Doll_Envelopes.md) — Sort + LIS on heights. **must-do**
11. **[Maximum_Height_by_Stacking_Cuboids.md](./Maximum_Height_by_Stacking_Cuboids.md)**  ·  [walkthrough →](./learn/Maximum_Height_by_Stacking_Cuboids.md) — 3D LIS variant.
12. **[Longest_Common_Subsequence.md](./Longest_Common_Subsequence.md)**  ·  [walkthrough →](./learn/Longest_Common_Subsequence.md) — Classic 2D LCS. **must-do**
13. **[Longest_Palindromic_Subsequence.md](./Longest_Palindromic_Subsequence.md)**  ·  [walkthrough →](./learn/Longest_Palindromic_Subsequence.md) — LCS of `s` with `reverse(s)`.

### String DP — matching

14. **[Edit_Distance.md](./Edit_Distance.md)**  ·  [walkthrough →](./learn/Edit_Distance.md) — Insert / delete / replace. THE classic. **must-do**
15. **[Distinct_Subsequences.md](./Distinct_Subsequences.md)**  ·  [walkthrough →](./learn/Distinct_Subsequences.md) — Count occurrences.
16. **[Decode_Ways.md](./Decode_Ways.md)**  ·  [walkthrough →](./learn/Decode_Ways.md) — `dp[i] = (single ok ? dp[i-1] : 0) + (double ok ? dp[i-2] : 0)`. **must-do**
17. **[Interleaving_String.md](./Interleaving_String.md)**  ·  [walkthrough →](./learn/Interleaving_String.md) — 2D DP from two source strings.
18. **[Regular_Expression_Matching.md](./Regular_Expression_Matching.md)**  ·  [walkthrough →](./learn/Regular_Expression_Matching.md) — `.` and `*` cases. Senior bar.
19. **[Frog_Jump.md](./Frog_Jump.md)**  ·  [walkthrough →](./learn/Frog_Jump.md) — State `(stone, last_jump)`; map of stone → reachable jumps.

### Knapsack

20. **[Partition_Equal_Subset_Sum.md](./Partition_Equal_Subset_Sum.md)**  ·  [walkthrough →](./learn/Partition_Equal_Subset_Sum.md) — 0/1 knapsack with target = sum/2. **must-do**
21. **[Ones_and_Zeroes.md](./Ones_and_Zeroes.md)**  ·  [walkthrough →](./learn/Ones_and_Zeroes.md) — 2D knapsack (m zeros, n ones budget).
22. **[Split_Array_with_Same_Average.md](./Split_Array_with_Same_Average.md)**  ·  [walkthrough →](./learn/Split_Array_with_Same_Average.md) — Subset with average; bitmask DP.
23. **[Minimum_Jumps_to_Reach_Home.md](./Minimum_Jumps_to_Reach_Home.md)**  ·  [walkthrough →](./learn/Minimum_Jumps_to_Reach_Home.md) — State-rich BFS/DP hybrid.

### Interval DP

24. **[Matrix_Chain_Multiplication.md](./Matrix_Chain_Multiplication.md)**  ·  [walkthrough →](./learn/Matrix_Chain_Multiplication.md) — `dp[i][j]` = min cost over range. **must-do**
25. **[Unique_Binary_Search_Trees.md](./Unique_Binary_Search_Trees.md)**  ·  [walkthrough →](./learn/Unique_Binary_Search_Trees.md) — Catalan-style interval DP.

### Hybrid / advanced

26. **[Maximal_Rectangle.md](./Maximal_Rectangle.md)**  ·  [walkthrough →](./learn/Maximal_Rectangle.md) — DP + Largest Rectangle in Histogram (stack). **must-do**
27. **[Dungeon_Game.md](./Dungeon_Game.md)**  ·  [walkthrough →](./learn/Dungeon_Game.md) — **Reverse DP** from bottom-right. Senior bar.

### Digit DP

28. **[Numbers_at_Most_N_Given_Digit_Set.md](./Numbers_at_Most_N_Given_Digit_Set.md)**  ·  [walkthrough →](./learn/Numbers_at_Most_N_Given_Digit_Set.md) — Digit-DP template. Senior bar.

---

## Patterns established

- **Identify the DP state:** What information do I need to make the next decision? That's the state.
- **Memoize top-down OR build bottom-up:** Both equivalent; bottom-up usually O(1) space via rolling arrays.
- **Knapsack:** Capacity is a dimension; loop order matters (1D rolling: capacity descending for 0/1).
- **LCS shape:** `dp[i][j]` based on `dp[i-1][j-1] + match` vs `max(dp[i-1][j], dp[i][j-1])`.
- **Edit distance shape:** `dp[i][j] = match ? dp[i-1][j-1] : 1 + min(insert, delete, replace)`.
- **Interval DP:** `dp[i][j] = min over k in (i, j) of split-cost(i, k, j)`.
- **Reverse DP:** When constraints flow backwards (Dungeon Game's HP must end ≥ 1).
- **Digit DP state:** `(position, tight, started)` with optional more constraints.
- **DP + stack hybrid:** Maximal Rectangle reduces to histogram per row.

---

## Common traps

- **DP without identifying state.** "I'll just memoize" without knowing what the function's signature should be.
- **Forgetting base cases.** `dp[0]` matters.
- **Wrong loop order in knapsack.** 0/1 knapsack needs **descending** capacity in 1D form (else same item counts twice).
- **LIS with O(n²) when O(n log n) is expected.** Binary search the tails array.
- **String DP off-by-one.** `dp[i][j]` typically means "first i of A, first j of B" — both 0-indexed inputs but DP table is 1-indexed.
- **Maximal Rectangle without thinking "per-row histogram heights."** Don't try to solve directly in 2D.
- **Reverse DP for Dungeon Game** — forward DP misses that you can't go below 1 HP.

---

## After this topic

- **[Segment_Tree_Range_Queries/](../Segment_Tree_Range_Queries/LEARNING.md)** — for DP with range queries / updates.
- **[Number_Theory_Misc/](../Number_Theory_Misc/LEARNING.md)** — digit DP appears there too.
- **[Greedy/](../Greedy/LEARNING.md)** — companion; many DP problems have greedy solutions.
- **[Graph_BFS_DFS_Dijkstra_DSU/](../Graph_BFS_DFS_Dijkstra_DSU/LEARNING.md)** — DP on graphs (Bellman-Ford is DP).
