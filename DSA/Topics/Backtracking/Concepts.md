# Backtracking — Concepts Guide

----------------------------------------

## 1. Introduction

Backtracking is DFS through a solution space with aggressive pruning. At each decision point, try an option, recurse, and undo. The key skill isn't the recursion — it's recognizing infeasible branches early and cutting them.

----------------------------------------

## 2. Real-Life Analogy

Think of a maze-solving robot. It tries a direction, walks until it hits a wall, then backs up and tries another direction. It never ignores a wall — instead, it *learns* from the failure and marks the dead-end so it doesn't retry it. That's backtracking: try, fail, rewind, try differently.

----------------------------------------

## 3. Core Idea

Backtracking is recursion with three reliable phases: (1) if the state is a solution, record it. (2) for each valid next choice, apply → recurse → undo. (3) return when no more choices. Without pruning, backtracking is exponential — with pruning, it can solve surprisingly large problems in reasonable time.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Signals for backtracking:

- **'Generate all solutions'** (permutations, combinations, subsets).
- **Constraint satisfaction** (N-Queens, Sudoku, crosswords).
- **Path enumeration** in trees or grids.
- **Combinatorial generation with constraints.**

----------------------------------------

## 5. Types / Variations

- **Subset / permutation generation** with skip-duplicate rules.
- **Constraint-based** (N-Queens, Sudoku with row/col/box masks).
- **Path enumeration** (palindrome partitioning).
- **Game-tree search** with alpha-beta pruning.

----------------------------------------

## 6. Step-by-Step Working

**Generic backtracking template:**
1. If current state satisfies the goal → record.
2. For each possible next move:
   - If not feasible (violates constraint), skip.
   - Apply move.
   - Recurse.
   - Undo move.

----------------------------------------

## 7. Visual Explanation

**N-Queens (4×4):**

```
. . . .
. . . .
. . . .
. . . .

Try col 0 row 0:
Q . . .
.(try row 2): . . Q .
. (try row 3): ?  no safe spot
  undo
.(try row 3):
. . . Q
. (try row 1): ? no safe spot
  undo
 undo
... continue ...
Final valid: [1, 3, 0, 2]
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Generate parentheses
void gen(int n, int o, int c, string& s, vector<string>& res) {
    if ((int)s.size() == 2*n) { res.push_back(s); return; }
    if (o < n) { s += '('; gen(n, o+1, c, s, res); s.pop_back(); }
    if (c < o) { s += ')'; gen(n, o, c+1, s, res); s.pop_back(); }
}

// N-Queens
vector<vector<string>> solveNQueens(int n) {
    vector<vector<string>> res;
    vector<string> board(n, string(n, '.'));
    vector<int> col(n, 0), d1(2*n, 0), d2(2*n, 0);
    function<void(int)> bt = [&](int r) {
        if (r == n) { res.push_back(board); return; }
        for (int c = 0; c < n; ++c) {
            if (col[c] || d1[r+c] || d2[r-c+n]) continue;
            board[r][c] = 'Q';
            col[c] = d1[r+c] = d2[r-c+n] = 1;
            bt(r + 1);
            board[r][c] = '.';
            col[c] = d1[r+c] = d2[r-c+n] = 0;
        }
    };
    bt(0);
    return res;
}
```

----------------------------------------

## 9. Common Mistakes

- **Forgetting to undo state** — corrupts later iterations.
- **Weak pruning** — TLE.
- **Skip-duplicate rules misapplied.**
- **Mutating shared state without backup.**

----------------------------------------

## 10. Interview Insights

Backtracking interviews test discipline. Interviewers want to see:

1. **Clean recursion with apply → recurse → undo.**
2. **Early pruning** based on constraints.
3. **Handling of duplicate inputs.**
4. **Clear base case and goal check.**
