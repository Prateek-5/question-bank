# Combination Sum II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Combination_Sum_II.md`](../Combination_Sum_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/combination-sum-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/combination-sum-ii/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: combine THREE backtracking techniques — sort, sibling-dedup, early-break pruning — for a sum-target combinatorial enumeration.** Each candidate used at most ONCE. **Read [`Subsets_II.md`](./Subsets_II.md) first** for the dedup rule.

**Map of this file (8 short sections):**

1. Read the problem
2. The backtracking skeleton
3. Three pruning/dedup tricks
4. Code
5. Trace it
6. Common pitfalls
7. Compared to Combination Sum I
8. The shape — sum-target backtracking

---

## 1. Read the problem

Given a collection of candidates `candidates` (may have duplicates) and a target `target`, find all UNIQUE combinations where the chosen numbers sum to `target`. Each candidate may be used **AT MOST ONCE** per combination.

**Examples:**

- `candidates = [10, 1, 2, 7, 6, 1, 5]`, `target = 8` → 
  ```
  [[1, 1, 6], [1, 2, 5], [1, 7], [2, 6]]
  ```
- `candidates = [2, 5, 2, 1, 2]`, `target = 5` →
  ```
  [[1, 2, 2], [5]]
  ```

---

## 2. The backtracking skeleton

Standard backtracking. Pick candidates one at a time, recursing with the remainder.

```
def backtrack(start, remaining, path):
    if remaining == 0:
        record path
        return
    for i in start..n-1:
        path.append(candidates[i])
        backtrack(i + 1, remaining - candidates[i], path)    # i+1: don't reuse
        path.pop()
```

Three observations:
1. Use `i + 1` (not `i`) when recursing — each candidate at most ONCE.
2. Use `start` to enforce canonical order (combinations, not permutations).
3. Need dedup for duplicate VALUES (input may have repeats).
4. Need pruning (don't recurse if candidate exceeds remaining).

---

## 3. Three pruning/dedup tricks

**Trick 1: Sort + early break.**

After sorting, if `candidates[i] > remaining`, ALL subsequent candidates (also ≥) exceed too. **BREAK** out of the loop entirely.

**Trick 2: Skip duplicate siblings (Subsets II rule).**

```
if i > start and candidates[i] == candidates[i - 1]:
    continue
```

Same rule as Subsets II: at each level, skip later occurrences of the same value.

**Trick 3: Base case `remaining == 0`.**

Don't keep recursing if we've already matched. The pruning by early break also handles `remaining > 0` cases efficiently.

> **Mini-refresher: pruning vs. dedup.**
>
> - **Pruning**: cut off branches that CAN'T succeed (sum already too big). Reduces search space.
> - **Dedup**: cut off branches that DUPLICATE earlier ones. Avoids redundant outputs.
>
> Both shave runtime. Pruning is about CORRECTNESS-bounded efficiency; dedup is about OUTPUT-uniqueness.

---

## 4. Code

**C++:**

```cpp
class Solution {
    vector<vector<int>> result;
    vector<int> path;

    void backtrack(vector<int>& candidates, int start, int remaining) {
        if (remaining == 0) {
            result.push_back(path);
            return;
        }
        for (int i = start; i < (int)candidates.size(); ++i) {
            if (candidates[i] > remaining) break;                       // prune
            if (i > start && candidates[i] == candidates[i - 1]) continue;   // dedup
            path.push_back(candidates[i]);
            backtrack(candidates, i + 1, remaining - candidates[i]);
            path.pop_back();
        }
    }

public:
    vector<vector<int>> combinationSum2(vector<int>& candidates, int target) {
        sort(candidates.begin(), candidates.end());
        backtrack(candidates, 0, target);
        return result;
    }
};
```

**Python:**

```python
def combinationSum2(candidates, target):
    candidates.sort()
    res = []
    path = []
    def backtrack(start, remaining):
        if remaining == 0:
            res.append(path[:])
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:
                break
            if i > start and candidates[i] == candidates[i-1]:
                continue
            path.append(candidates[i])
            backtrack(i + 1, remaining - candidates[i])
            path.pop()
    backtrack(0, target)
    return res
```

Complexity: exponential worst case, but typically efficient due to aggressive pruning.

---

## 5. Trace it

**`candidates = [10, 1, 2, 7, 6, 1, 5]`, `target = 8`. Sorted: `[1, 1, 2, 5, 6, 7, 10]`.**

```
backtrack(start=0, remaining=8, path=[]):
  i=0 (val=1): path=[1]. backtrack(1, 7):
    i=1 (val=1): path=[1, 1]. backtrack(2, 6):
      i=2 (val=2): path=[1, 1, 2]. backtrack(3, 4):
        i=3 (val=5): 5 > 4 → BREAK.
      pop.
      i=3 (val=5): path=[1, 1, 5]. backtrack(4, 1):
        i=4 (val=6): 6 > 1 → BREAK.
      pop.
      i=4 (val=6): path=[1, 1, 6]. backtrack(5, 0): RECORD [1, 1, 6].
      pop.
      i=5 (val=7): 7 > 0 → BREAK.
    pop.
    i=2 (val=2): path=[1, 2]. backtrack(3, 5):
      i=3 (val=5): path=[1, 2, 5]. backtrack(4, 0): RECORD [1, 2, 5].
      pop.
      i=4 (val=6): 6 > 5 → BREAK.
    pop.
    i=3 (val=5): path=[1, 5]. backtrack(4, 2): nothing fits, BREAK.
    pop.
    i=4 (val=6): path=[1, 6]. backtrack(5, 1): nothing fits.
    pop.
    i=5 (val=7): path=[1, 7]. backtrack(6, 0): RECORD [1, 7].
    pop.
    i=6 (val=10): 10 > 0 → BREAK. (Actually 10 > 1 also, BREAK earlier.)
  pop.
  i=1 (val=1): i > start (1 > 0), candidates[1]==candidates[0]. SKIP.
  i=2 (val=2): path=[2]. backtrack(3, 6):
    i=3 (val=5): path=[2, 5]. backtrack(4, 1): BREAK.
    pop.
    i=4 (val=6): path=[2, 6]. backtrack(5, 0): RECORD [2, 6].
    ... etc.

Results: [1, 1, 6], [1, 2, 5], [1, 7], [2, 6].  ✓
```

Notice the skip at top-level i=1 (would have duplicated combinations starting with the "second 1"). The skip works because the BRANCH starting from i=0 with value 1 already explored everything reachable with "starts with a 1."

---

## 6. Common pitfalls

1. **Recursing with `i` instead of `i + 1`.** That's Combination Sum I (REUSE allowed). For this problem, use `i + 1`.

2. **Forgetting sort.** Pruning (`candidates[i] > remaining` break) and dedup (`candidates[i] == candidates[i-1]` skip) both need sorted input.

3. **Using `continue` instead of `break` for pruning.** With sorted input, if current candidate is too big, ALL subsequent are also too big. Break entirely.

4. **Using `i > 0` instead of `i > start` for dedup.** Same mistake as in Subsets II.

5. **Not checking `remaining < 0`.** With the pruning (break on `candidates[i] > remaining`), this can't happen — but if pruning is omitted, you'd need an explicit `if remaining < 0: return`.

6. **Recording in the loop instead of base case.** If remaining > 0 at a leaf, no match — don't record.

7. **Sorting in a non-mutable way.** In Python, `sorted(candidates)` returns a new list; modify in place with `.sort()`.

---

## 7. Compared to Combination Sum I

**Combination Sum I:** input is distinct, candidates can be reused unlimited times.

```
# Combination Sum I:
def backtrack(start, remaining, path):
    if remaining == 0:
        record
        return
    for i in start..n-1:
        if candidates[i] > remaining: break
        path.append(candidates[i])
        backtrack(i, remaining - candidates[i], path)   # i, not i+1 — REUSE
        path.pop()
```

Two differences vs II:
1. Recurse with `i` (not `i+1`) → reuse same candidate.
2. No dedup skip needed (input is distinct).

**Combination Sum II** (this problem): each candidate used at most once, dedup needed.

Same TEMPLATE; small parameter changes.

---

## 8. The shape — sum-target backtracking

The pattern: **enumerate all subsets/multisets satisfying a SUM CONSTRAINT.**

| Problem | Variant |
|---|---|
| **This problem** | each candidate at most once, dedup if duplicates |
| Combination Sum I | unlimited reuse, distinct input |
| Combination Sum III | exactly K elements, fixed values 1..9 |
| Combination Sum IV | order matters (counts), DP-like |
| Coin Change | minimum coins (DP, not enumeration) |
| Subset Sum (decision) | does any subset sum to target? (DP) |
| Target Sum (LC #494) | with +/- signs, DP |

**Pattern to internalize:**

> "For SUM-TARGET combinatorial enumeration, sort first. Backtrack with `start` for canonical order. PRUNE when current candidate exceeds remaining. DEDUP siblings if duplicates allowed in input."

This pattern is the workhorse of "find all combinations summing to X" type problems.

---

> **Self-check — the question to ask next time.**
>
> When you face "find all combinations summing to target," ask:
>
> > **"Can I sort, backtrack with `start`, break on too-big candidates, and skip duplicate siblings? Recurse with `i` for reuse, `i + 1` for at-most-once."**
>
> If yes, you've got a clean exponential solution with aggressive pruning.

---

## Cross-references

- **Reference card (post-mastery):** [`../Combination_Sum_II.md`](../Combination_Sum_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Subsets.md`](./Subsets.md), [`Subsets_II.md`](./Subsets_II.md), [`Permutations.md`](./Permutations.md), [`Permutations_II.md`](./Permutations_II.md).
  - Coming next: [`N_Queens.md`](./N_Queens.md) — constraint-based backtracking.
