# Permutations II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Permutations_II.md`](../Permutations_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/permutations-ii/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: for permutations with DUPLICATES, the dedup rule is `nums[i] == nums[i-1] AND !used[i-1]`** — subtle but elegant. Different from Subsets II's `i > start` rule. **Read [`Permutations.md`](./Permutations.md) and [`Subsets_II.md`](./Subsets_II.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. Why standard permutations generates duplicates
3. The skip rule — `!used[i-1]`
4. Why `!used[i-1]` (not `used[i-1]`)
5. Code
6. Trace it
7. Common pitfalls
8. Compared to Subsets II's dedup rule
9. The shape — canonical ordering for duplicates

---

## 1. Read the problem

Given an integer array `nums` that **MAY CONTAIN DUPLICATES**, return ALL POSSIBLE UNIQUE permutations in any order.

**Examples:**

- `nums = [1, 1, 2]` → 3 unique: `[1,1,2], [1,2,1], [2,1,1]`.
- `nums = [1, 2, 3]` → 6 (no duplicates in input → standard Permutations).

---

## 2. Why standard permutations generates duplicates

With `[1, 1, 2]` and the standard Permutations template:

- Pick index 0 (value 1) first. Subtree permutes `[_, 1, 2]`. Yields: `[1,1,2], [1,2,1]`.
- Pick index 1 (value 1) first. Subtree permutes `[1, _, 2]`. Yields: `[1,1,2], [1,2,1]`. **Same as above!**
- Pick index 2 (value 2) first. Yields: `[2,1,1], [2,1,1]`. **One duplicate.**

The duplicates come from picking different INDICES that hold the same VALUE.

**Fix:** at each level, choose each VALUE at most once.

---

## 3. The skip rule — `!used[i-1]`

**Sort the input first.** Then duplicates are adjacent.

**Skip condition (at each level):**

```
if i > 0 and nums[i] == nums[i-1] and not used[i-1]:
    continue
```

In English: "if value at i equals value at i-1, AND i-1 is currently UNUSED (still available), skip i — it would duplicate a branch."

> **Mini-refresher: why `!used[i-1]`?**
>
> The rule canonicalizes the order in which duplicates appear: when there are multiple copies of the same value, they MUST be picked in LEFT-TO-RIGHT INDEX ORDER.
>
> - If `i-1` is currently unused: picking `i` first would generate a permutation that the `i-1`-first branch would ALSO generate. They're symmetric. Skip the later one.
> - If `i-1` is already used: picking `i` is fine — `i-1` was already chosen for an earlier position in this permutation.

So duplicates can be used MULTIPLE TIMES across a permutation, but they're always picked in INDEX ORDER (canonical).

---

## 4. Why `!used[i-1]` (not `used[i-1]`)

Subtle! Two interpretations exist; both can be made to work, but the standard one is `!used[i-1]`:

- `!used[i-1]` means: "skip if i-1 (the previous same-value index) hasn't been used yet." Picking i would be picking a SECOND copy WITHOUT picking the FIRST copy first → out of canonical order.

Let me illustrate with `[1, 1, 2]` (sorted):

**At top level, considering i=1:**
- `nums[1] == nums[0]` (both 1). `used[0]` is false.
- SKIP. Because `[1@idx1, ...]` would duplicate `[1@idx0, ...]`.

**Inside the branch where we picked i=0 first**, at level 1, considering i=1:
- `nums[1] == nums[0]`. `used[0]` is TRUE (we picked it at level 0).
- DON'T skip. The first 1 was picked; now using the second 1 is legitimate.

Beautiful. Canonical order enforced; duplicates within a permutation still allowed.

---

## 5. Code

**C++:**

```cpp
class Solution {
    vector<vector<int>> result;
    vector<int> current;
    vector<bool> used;
    vector<int> nums;

    void backtrack() {
        if (current.size() == nums.size()) {
            result.push_back(current);
            return;
        }
        for (int i = 0; i < (int)nums.size(); ++i) {
            if (used[i]) continue;
            if (i > 0 && nums[i] == nums[i - 1] && !used[i - 1]) continue;
            used[i] = true;
            current.push_back(nums[i]);
            backtrack();
            current.pop_back();
            used[i] = false;
        }
    }

public:
    vector<vector<int>> permuteUnique(vector<int>& input) {
        nums = input;
        sort(nums.begin(), nums.end());
        used.assign(nums.size(), false);
        backtrack();
        return result;
    }
};
```

**Python:**

```python
def permuteUnique(nums):
    nums.sort()
    res = []
    used = [False] * len(nums)
    cur = []
    def backtrack():
        if len(cur) == len(nums):
            res.append(cur[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            if i > 0 and nums[i] == nums[i-1] and not used[i-1]:
                continue
            used[i] = True
            cur.append(nums[i])
            backtrack()
            cur.pop()
            used[i] = False
    backtrack()
    return res
```

Complexity: **O(n × n!)** worst case (no duplicates), less with duplicates.

---

## 6. Trace it

**`nums = [1, 1, 2]` (sorted):**

```
backtrack(), cur=[], used=[F,F,F]:

  i=0 (val=1): used[0]=T, cur=[1].
    backtrack(), cur=[1], used=[T,F,F]:
      i=0: skip (used).
      i=1 (val=1): used[0]=T → !used[0]=F → CONDITION FAILS → don't skip.
        used[1]=T, cur=[1, 1].
        backtrack(), cur=[1,1], used=[T,T,F]:
          i=2: cur=[1, 1, 2]. RECORD.
      i=2: cur=[1, 2].
        backtrack(), used=[T,F,T]:
          i=0: skip.
          i=1: used[0]=T → don't skip. cur=[1, 2, 1]. RECORD.

  i=1 (val=1): i > 0, nums[1]==nums[0], !used[0] (true) → SKIP.

  i=2 (val=2): cur=[2].
    backtrack(), used=[F,F,T]:
      i=0: cur=[2, 1].
        backtrack(), used=[T,F,T]:
          i=1: used[0]=T → don't skip. cur=[2, 1, 1]. RECORD.
      i=1: nums[1]==nums[0], !used[0] → SKIP.

Recorded: [1,1,2], [1,2,1], [2,1,1].  ✓
```

The skip rule fires precisely twice (at top-level i=1, and inside the i=2 branch's level i=1). Both prevent duplicates without losing valid permutations.

---

## 7. Common pitfalls

1. **Forgetting to sort.** Duplicates aren't adjacent → `nums[i] == nums[i-1]` misses them.

2. **Using `used[i-1]` instead of `!used[i-1]`.** Reverses the logic. Either lose all duplicate permutations or fail to dedup.

3. **Using `i > 0 and nums[i] == nums[i-1]` (without `!used[i-1]`).** Like Subsets II's rule. WRONG for permutations — would over-prune (lose valid permutations like `[1,1,2]`).

4. **Using a set of tuples to dedup.** Works but wastes time and space.

5. **Not undoing both `cur` and `used`.** Both need to be restored.

6. **Confusing Permutations II's rule with Subsets II's.** They're DIFFERENT! See Section 8.

---

## 8. Compared to Subsets II's dedup rule

| Problem | Skip condition |
|---|---|
| **Subsets II** | `i > start and nums[i] == nums[i-1]` |
| **Permutations II** | `i > 0 and nums[i] == nums[i-1] and !used[i-1]` |

**Why different?**

- **Subsets**: we use a `start` index. Within each level (start fixed), we iterate `i = start..n-1`. The `i > start` test checks "am I a LATER sibling at this level?" Skip if same as the previous sibling.

- **Permutations**: we use a `used[]` array (no `start`). We iterate `i = 0..n-1`. We need to track NOT just "later sibling" but also "is the previous same-value element already used?" Because if it's used, this is a legitimate later use; if not, it's a duplicate branch.

So the SAME IDEA (skip equivalent siblings) but DIFFERENT MECHANICS due to the different state representation.

---

## 9. The shape — canonical ordering for duplicates

The pattern: **impose a CANONICAL ORDER on how duplicates can appear, eliminating symmetric branches.**

| Problem | Canonical rule |
|---|---|
| Subsets II | duplicates picked left-to-right; skip later siblings at same level |
| **This problem** (Permutations II) | duplicates picked left-to-right; skip if previous same-value index is unused |
| Combination Sum II | same as Subsets II |
| String permutation with duplicates | same as Permutations II |
| Path enumeration with repeated states | apply ordering on repeated transitions |

**Pattern to internalize:**

> "When the input has duplicates and you're enumerating arrangements, impose a CANONICAL ORDER (always pick duplicates left-to-right). Skip branches that would violate this order — they'd produce duplicate outputs."

This is one of the most beautiful ideas in backtracking — using state (`used[]`, `start`) to canonicalize and eliminate symmetric search.

---

> **Self-check — the question to ask next time.**
>
> When you face PERMUTATIONS / ORDERINGS with possible duplicates in the input, ask:
>
> > **"Can I sort first and then skip `nums[i] == nums[i-1] && !used[i-1]`? Enforces left-to-right pick of duplicates → no duplicate permutations."**
>
> If yes, dedup without post-processing.

---

## Cross-references

- **Reference card (post-mastery):** [`../Permutations_II.md`](../Permutations_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Permutations.md`](./Permutations.md), [`Subsets_II.md`](./Subsets_II.md).
  - Coming next: [`Combination_Sum_II.md`](./Combination_Sum_II.md), [`N_Queens.md`](./N_Queens.md).
