# Backtracking — Concepts

## Core Theory
Backtracking is DFS through a solution space with pruning. At each decision point, try an option, recurse, and undo. Prune infeasible branches as early as possible.

## Common Patterns
- **Permutations, combinations, subsets** with skip-duplicate rules.
- **Constraint satisfaction** (N-Queens, Sudoku) with row/col/box masks.
- **Palindrome / substring partitioning**.

## When to Use
For combinatorial problems whose state space is exponential but heavily prunable. If no effective pruning is available, consider DP or smarter greedy.

## Template
```cpp
void bt(State& s, Solution& ans) {
    if (goal(s)) { ans.record(s); return; }
    for (auto c : choices(s)) if (feasible(s, c)) {
        apply(s, c); bt(s, ans); undo(s, c);
    }
}
```

## Common Mistakes
- Not undoing state → incorrect enumeration.
- Weak pruning → TLE.
- Duplicate-skip rules misapplied (sibling vs descendant).
