# Recursion — Learning Path

> **Stage:** Structures   |   **Prereqs:** Arrays   |   **Problems:** 6
>
> Choose → explore → unchoose. Master subsets and permutations and the backtracking template is yours.

---

## How to study this topic

Order is strictly by difficulty: subsets first (binary include/exclude), then permutations (used[] array), then with duplicates (sort + skip), then constraint-driven (N-Queens).

After this topic, **[Backtracking/](../Backtracking/LEARNING.md)** has constraint-driven problems.

---

## Problems in study order

### Subsets — include/exclude

1. **[Subsets.md](./Subsets.md)** — At each index, branch include/exclude. Or bitmask iteration. **must-do**
2. **[Subsets_II.md](./Subsets_II.md)** — Sort + skip duplicate at the same depth.

### Permutations — used[] flag set

3. **[Permutations.md](./Permutations.md)** — For each position, try each unused element. **must-do**
4. **[Permutations_II.md](./Permutations_II.md)** — Sort + `!used[i-1] && nums[i] == nums[i-1] → skip` dedup. The classic subtle rule.

### Combination with pruning

5. **[Combination_Sum_II.md](./Combination_Sum_II.md)** — Sort + skip duplicates + early break when sum > target.

### Constraint-driven — N-Queens

6. **[N_Queens.md](./N_Queens.md)** — Track cols, diag1 (r-c), diag2 (r+c) as Sets for O(1) check. Sets > board-scan. **must-do**

---

## Patterns established

- **Backtracking template:** `if complete: snapshot; for each choice: if valid: choose; recurse; unchoose;`.
- **Snapshot copy:** Push `[...current]`, never the live `current` array.
- **Used-flag set vs start index:** Permutations track `used[]`; subsets/combinations use a `start` index to avoid duplicates and re-use order.
- **Sort + skip dedup:** When input has duplicates, sort, then skip `nums[i] == nums[i-1]` at the same depth (`i > start` for combinations; `!used[i-1]` for permutations).
- **O(1) constraint sets in N-Queens:** Track conflicts via cols, diag1 (r-c), diag2 (r+c) Sets.

---

## Common traps

- **Push live state, not copy.** All entries end up referencing the empty post-backtrack state.
- **Forget unchoose.** State accumulates; results explode.
- **Dedup at wrong level.** `nums[i] == nums[i-1]` only at the *same recursion depth*; check via `i > start` (for combinations) or `!used[i-1]` (for permutations).
- **Exponential blowup without pruning.** Combination Sum II without early break is much slower.

---

## After this topic

- **[Backtracking/](../Backtracking/LEARNING.md)** — harder constraint-driven problems (Sudoku, Palindrome Partition).
- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — many DPs start as recursion + memo.
- **[Trees_Binary_Trees/](../Trees_Binary_Trees/LEARNING.md)** — recursion shines on trees.
