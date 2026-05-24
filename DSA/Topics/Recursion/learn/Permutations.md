# Permutations — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Permutations.md`](../Permutations.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/permutations/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The lesson: PERMUTATIONS differ from subsets in that ORDER MATTERS. Use a `used[]` flag array instead of a `start` index, so you can pick ANY unused element at each level.** n! permutations vs 2^n subsets — different combinatorics, slightly different code template. **Read [`Subsets.md`](./Subsets.md) first.**

**Map of this file (10 sections):**

1. Read the problem
2. Counting permutations — n!
3. Permutations vs subsets — what changes?
4. The recursion structure
5. The `used` array
6. Code
7. Trace it
8. The swap-in-place alternative
9. Common pitfalls
10. The shape — backtracking with used flags

---

## 1. Read the problem

Given an array `nums` of **DISTINCT** integers, return all possible **permutations** (orderings). Any order is acceptable.

**Examples:**

- `nums = [1, 2, 3]` → 6 permutations:
  ```
  [1,2,3], [1,3,2], [2,1,3], [2,3,1], [3,1,2], [3,2,1]
  ```
- `nums = [0, 1]` → `[[0, 1], [1, 0]]`.
- `nums = [1]` → `[[1]]`.

---

## 2. Counting permutations — n!

> **Mini-refresher: why n elements have n! permutations.**
>
> For the FIRST position, you can pick any of n elements.
> For the SECOND, any of the n - 1 remaining.
> For the THIRD, any of the n - 2 remaining.
> ...
>
> Total: n × (n-1) × (n-2) × ... × 1 = **n!**.
>
> Growth: 1! = 1, 5! = 120, 10! = 3.6 million, 12! = 479 million.

For n = 8, that's ~40,000 — fast. For n = 12, you're at the edge. For n ≥ 13, enumeration is impractical.

---

## 3. Permutations vs subsets — what changes?

| Aspect | Subsets (`{1,2}`) | Permutations (`[1,2]`, `[2,1]`) |
|---|---|---|
| Order matters? | NO | YES |
| Count for n elements | 2^n | n! |
| Pick same value twice? | NO | NO (still distinct elements) |
| Indexing constraint | `start ≤ i` (canonical order) | any unused index |

The KEY DIFFERENCE: for permutations, you need to be able to PICK ANY UNUSED ELEMENT at each level — not just elements after some `start`.

So we track availability with a `used[]` flag array (one bool per index).

---

## 4. The recursion structure

```
def dfs(current, used):
    if len(current) == n:
        record current.copy()
        return
    for i in 0..n-1:
        if used[i]: continue
        used[i] = True
        current.append(nums[i])
        dfs(current, used)
        current.pop()
        used[i] = False
```

At each level:
- Loop over ALL indices `0..n-1`.
- Skip any index whose value is already in `current` (marked `used`).
- Otherwise: mark used, recurse, unmark.

Terminal: `current` has `n` elements → it's a complete permutation, record it.

Each level "fills" one more position of the permutation. After n levels, the permutation is complete.

---

## 5. The `used` array

> **Mini-refresher: why `used[]`, not `start`?**
>
> In Subsets, we use `start` to enforce CANONICAL ORDER (always pick indices in increasing order). This avoids generating `[2, 1]` if `[1, 2]` was already generated — because in subsets, they're the SAME subset.
>
> In Permutations, `[2, 1]` and `[1, 2]` are DIFFERENT permutations and MUST BOTH be enumerated. So we can't restrict to "indices ≥ start." Instead, we need to track WHICH INDICES ARE ALREADY USED in the current partial permutation.
>
> The `used[]` array does this. It's index-specific (not value-specific), allowing duplicates in the input — though this problem promises distinct values.

The pattern: **set used[i] = true before recursing; reset to false after.** Backtracking's "apply / recurse / undo" applied to availability.

---

## 6. Code

**C++:**

```cpp
class Solution {
    void dfs(vector<int>& nums, vector<bool>& used,
             vector<int>& cur, vector<vector<int>>& res) {
        if (cur.size() == nums.size()) {
            res.push_back(cur);
            return;
        }
        for (int i = 0; i < (int)nums.size(); ++i) {
            if (used[i]) continue;
            used[i] = true;
            cur.push_back(nums[i]);
            dfs(nums, used, cur, res);
            cur.pop_back();
            used[i] = false;
        }
    }

public:
    vector<vector<int>> permute(vector<int>& nums) {
        vector<vector<int>> res;
        vector<bool> used(nums.size(), false);
        vector<int> cur;
        cur.reserve(nums.size());
        dfs(nums, used, cur, res);
        return res;
    }
};
```

**Python:**

```python
def permute(nums):
    res = []
    used = [False] * len(nums)
    cur = []
    
    def dfs():
        if len(cur) == len(nums):
            res.append(cur[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            cur.append(nums[i])
            dfs()
            cur.pop()
            used[i] = False
    
    dfs()
    return res
```

Complexity: **O(n × n!) time** (n! permutations, each n elements to copy), O(n) recursion stack.

---

## 7. Trace it

**`nums = [1, 2, 3]`:**

```
dfs(), cur=[], used=[F,F,F]

  i=0: mark used[0]. cur=[1].
    dfs(), cur=[1], used=[T,F,F]
      i=0: skip (used).
      i=1: mark used[1]. cur=[1, 2].
        dfs(), cur=[1,2], used=[T,T,F]
          i=0,1: skip.
          i=2: mark used[2]. cur=[1, 2, 3].
            dfs(): LEN=3 → RECORD [1, 2, 3].
          unmark, pop.
      unmark, pop.
      i=2: mark. cur=[1, 3].
        dfs()
          i=1: mark. cur=[1, 3, 2]. RECORD.
      unmark, pop.
  unmark, pop.

  i=1: mark used[1]. cur=[2]. Recursive expansion gives [2,1,3], [2,3,1].
  unmark.
  
  i=2: mark used[2]. cur=[3]. Recursive expansion gives [3,1,2], [3,2,1].
  unmark.

Recorded: [1,2,3], [1,3,2], [2,1,3], [2,3,1], [3,1,2], [3,2,1]. SIX.  ✓
```

The recursion tree has 6 leaves (one per permutation) and n levels (each level picks one position).

---

## 8. The swap-in-place alternative

There's a cleaner O(1)-extra-space version: at depth `d`, decide what goes in position `d` by SWAPPING the chosen element into position `d`. The "unused" elements are simply `nums[d..]`.

```
def dfs(d):
    if d == n:
        record nums.copy()
        return
    for i in d..n-1:
        swap(nums[d], nums[i])
        dfs(d + 1)
        swap(nums[d], nums[i])     # undo
```

**Trace on `[1, 2, 3]`:**

```
dfs(0): nums=[1,2,3].
  i=0: swap (no-op). dfs(1):
    i=1: swap (no-op). dfs(2):
      i=2: swap (no-op). dfs(3): RECORD [1,2,3].
    unswap.
    i=2: swap nums[1] and nums[2] → [1,3,2]. dfs(2):
      i=2: swap (no-op). dfs(3): RECORD [1,3,2].
      unswap → [1,3,2] (already).
    unswap → [1,2,3].
  unswap.
  ... etc
```

Pros: no `used` array (O(1) extra space).
Cons: MUTATES `nums` (inputs change mid-execution). Less transparent.

Both styles enumerate the same n! permutations.

---

## 9. Common pitfalls

1. **Not undoing.** Forgetting `used[i] = false` after recursion. Then `used` accumulates "true"s, and later iterations skip valid choices.

2. **Pushing `cur` without copying.** Same issue as Subsets — `res.append(cur)` (without copy) makes all entries reference the same (eventually empty) list.

3. **Using `start` instead of `used`.** Subsets pattern. Generates only n / "ordered combinations" — missing reverses like `[2, 1]`.

4. **Off-by-one in terminal check.** Use `len(cur) == n` (or `cur.size() == nums.size()`).

5. **Modifying input array without restoring** (in swap-in-place version). Leaves the array in a different order than passed in. Usually OK for backtracking but be aware.

6. **Confusing distinct/duplicate handling.** This problem promises distinct values. For duplicates, see Permutations II's dedup rule.

7. **Trying to use `itertools.permutations` and stop early.** Library exists in Python — use it if allowed. But interviewers usually want the manual version.

---

## 10. The shape — backtracking with used flags

The pattern:

> **"Enumerate orderings (where order matters) by tracking AVAILABILITY of each element via a `used[]` flag array."**

Where it appears:

| Problem | "Used" tracks |
|---|---|
| **This problem** | which array indices are placed |
| Permutations II (with duplicates) | same, with sibling-dedup |
| N-Queens | which columns/diagonals have a queen |
| Word Ladder Construction | which dictionary words have been used |
| Sudoku Solver | which (row, col, box) has each digit |
| Letter Tile Possibilities | which tile copies are picked |
| TSP enumeration | which cities are visited |

**Pattern to internalize:**

> "When ORDER MATTERS, replace `start`-index restrictions with a `used[]` flag array. Each level: pick any unused element. Apply → recurse → undo (both `cur` AND `used`)."

---

> **Self-check — the question to ask next time.**
>
> When you face "enumerate all ORDERINGS / ARRANGEMENTS," ask:
>
> > **"Can I use backtracking with a `used[]` array tracking availability? Apply (`used[i]=true`), recurse, undo (`used[i]=false`)."**
>
> If yes, you've got the permutations template.

---

## Cross-references

- **Reference card (post-mastery):** [`../Permutations.md`](../Permutations.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Subsets.md`](./Subsets.md), [`Subsets_II.md`](./Subsets_II.md).
  - Coming next: [`Permutations_II.md`](./Permutations_II.md) — handle duplicates.
  - Coming later: [`N_Queens.md`](./N_Queens.md), [`Combination_Sum_II.md`](./Combination_Sum_II.md).
