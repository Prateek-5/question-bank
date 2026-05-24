# Backtracking — Learning Path

> **Stage:** Structures   |   **Prereqs:** [Recursion/](../Recursion/LEARNING.md)   |   **Problems:** 4
>
> Constraint-driven recursion. Pruning is the whole game.
>
> **Two-tier format:** each problem has a **reference card** (linked first below) AND a paced **teaching walkthrough** in [`learn/`](./learn/) for first-time learners.

---

## How to study this topic

Short topic. Order: constraint-shaped → string-based → bit-pattern → hardest.

---

## Problems in study order

1. **[Generate_Parentheses.md](./Generate_Parentheses.md)**  ·  [walkthrough →](./learn/Generate_Parentheses.md) — Two counters (`open`, `close`); place `(` if `open < n`, place `)` if `close < open`. Catalan C(n) outputs. **must-do**
2. **[Palindrome_Partitioning.md](./Palindrome_Partitioning.md)**  ·  [walkthrough →](./learn/Palindrome_Partitioning.md) — At each index, try all palindrome prefixes; recurse on the rest. **must-do**
3. **[Gray_Code.md](./Gray_Code.md)**  ·  [walkthrough →](./learn/Gray_Code.md) — Generate by XOR pattern (`i ^ (i >> 1)`) or recursive mirror-prefix.
4. **[Sudoku_Solver.md](./Sudoku_Solver.md)**  ·  [walkthrough →](./learn/Sudoku_Solver.md) — Backtracking with three constraint Sets (rows, cols, boxes). The hardest. **must-do** for senior interviews.

---

## Patterns established

- **Counter-based pruning:** Generate Parentheses uses two counters to never produce invalid state.
- **Prefix-then-recurse:** Palindrome Partitioning splits `s = prefix + suffix` and recurses on suffix.
- **Constraint state via Sets:** Rows, cols, boxes (or diagonals in N-Queens) for O(1) feasibility checks.
- **In-place mutation + restore:** Sudoku grid is mutated and restored on backtrack — no copy.

---

## Common traps

- **No pruning → exponential explosion.** Generate Parentheses without the two-counter pruning enumerates all 4^n strings instead of C(n).
- **Wrong restore on backtrack.** Must mirror every mutation.
- **Choosing the wrong cell-selection heuristic in Sudoku.** Pick the most-constrained cell next (smallest domain) for serious speedup.

---

## After this topic

- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — many backtracking solutions are DP candidates with memoization.
- **[Graph_BFS_DFS_Dijkstra_DSU/](../Graph_BFS_DFS_Dijkstra_DSU/LEARNING.md)** — graph backtracking (Hamiltonian path).
