# Permutations II

**Problem Link:**
<a href="https://leetcode.com/problems/permutations-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/permutations-ii/</a>

**Topic:**
Recursion

----------------------------------------

## Step 1: Understand the Twist

**Permutations I** asked for all permutations of an array with **distinct** elements. Straightforward backtracking — n! permutations.

**Permutations II** allows **duplicates** in the input. We must return **unique** permutations (no duplicates in the output).

Example: `nums = [1, 1, 2]`. 

All 3! = 6 permutations:
- [1, 1, 2], [1, 2, 1], [1, 1, 2] (duplicate!), [1, 2, 1] (dup), [2, 1, 1], [2, 1, 1] (dup).

Unique: [1, 1, 2], [1, 2, 1], [2, 1, 1]. Count = 3.

We need to avoid generating duplicates. Naive: generate all 6 with standard backtracking, dedupe with a set. Works but wasteful.

Better: **prune duplicate branches during backtracking**.

----------------------------------------

## Step 2: Visualize the Duplicate Problem

In standard backtracking, at each recursion level, we pick an unused element and recurse. With duplicates `[1, 1, 2]`:

Level 0 (pick one of three positions):
- Pick index 0 (value 1). Subtree permutes [_, 1, 2].
- Pick index 1 (value 1). Subtree permutes [1, _, 2].
- Pick index 2 (value 2). Subtree permutes [1, 1, _].

Subtrees of index 0 and index 1 are **identical in structure** (both permute a 1 and a 2), producing the same set of permutations. Duplicates come from this.

Fix: at each level, **don't pick a value we've already picked at this level**.

----------------------------------------

## Step 3: The Skip-Duplicate-Sibling Rule

Sort `nums` first. Duplicates now sit adjacent.

At each level of backtracking, iterate through indices. Skip an index `i` if:
- We already used `i` in this permutation (standard `used[i]` check), OR
- `nums[i] == nums[i-1]` AND we haven't used `i-1` yet (`!used[i-1]`).

The second condition is the new rule: if the previous sibling with the same value is unused, skip `i`. Why? Because:
- Either `i-1` will be picked later at this level (creating a valid permutation starting with this duplicate value).
- Or `i-1` won't be picked — meaning this value is used zero or more times later from position `i` or beyond, also covered.

In either case, picking `i` instead of `i-1` would produce the same permutations, just with swapped indices (which the sorted invariant makes identical in value).

----------------------------------------

## Step 4: Why "`!used[i-1]`" and Not Just Skip All Duplicates?

Consider `nums = [1, 1, 2]` after sort. If we blindly skip all `nums[i] == nums[i-1]`, we'd never pick the second 1. But we DO want permutations like `[1, 1, 2]` that use both 1s.

The clever condition `!used[i-1]` allows:
- At the first level, skip i = 1 (since used[0] = false, the previous 1 is available — picking i = 0 first is canonical).
- After picking i = 0 (used[0] = true), at level 1 we can pick i = 1 (used[0] = true means the "skip" condition fails; we proceed).

So duplicates are picked in **left-to-right order**, never out of order. This canonicalizes the permutations by index, avoiding duplicates in the output.

----------------------------------------

## Step 5: The Algorithm

```
sort(nums)

def backtrack(used, current):
    if len(current) == n:
        result.append(current.copy())
        return
    for i in 0..n-1:
        if used[i]: continue
        if i > 0 and nums[i] == nums[i-1] and not used[i-1]: continue
        used[i] = True
        current.append(nums[i])
        backtrack(used, current)
        current.pop()
        used[i] = False

backtrack([False]*n, [])
return result
```

Standard Permutations I template + the skip-duplicate rule.

----------------------------------------

## Step 6: Trace on `[1, 1, 2]`

Sorted: [1, 1, 2]. (Already sorted.)

```
backtrack([F,F,F], []):
  i=0: used[0]=T, current=[1].
    backtrack([T,F,F], [1]):
      i=0: used. skip.
      i=1: nums[1]==nums[0], used[0]=T, so the skip rule doesn't fire. Proceed.
        used[1]=T, current=[1,1].
        backtrack([T,T,F], [1,1]):
          i=0, i=1: used.
          i=2: proceed. current=[1,1,2]. Full. RECORD [1,1,2].
          undo.
        undo.
      i=2: proceed. used[2]=T, current=[1,2].
        backtrack([T,F,T], [1,2]):
          i=0: used. skip.
          i=1: nums[1]==nums[0], used[0]=T. Proceed.
            current=[1,2,1]. Full. RECORD [1,2,1].
            undo.
          i=2: used.
        undo.
      undo.
    undo.
  
  i=1: nums[1]==nums[0], used[0]=F. SKIP (rule fires).
  
  i=2: proceed. current=[2].
    backtrack([F,F,T], [2]):
      i=0: current=[2,1].
        backtrack([T,F,T], [2,1]):
          i=1: nums[1]==nums[0], used[0]=T. Proceed.
            current=[2,1,1]. Full. RECORD [2,1,1].
            undo.
        undo.
      i=1: nums[1]==nums[0], used[0]=F. SKIP.
      i=2: used.
    undo.
```

Records: [1,1,2], [1,2,1], [2,1,1]. Three unique. ✓

The skip-rule fired twice (at level 0 when considering i=1, and deeper when considering i=1 after level-0 i=2). Both skips correctly prevented duplicate permutations.

----------------------------------------

## Step 7: Name It

**Backtracking with canonical ordering for duplicates.** The skip-duplicate-sibling rule imposes a total order on how duplicates can appear, eliminating symmetric branches.

Same pattern applies to:
- Subsets II (duplicates in input).
- Combination Sum II.
- Unique Paths with some ordering.

The rule "sort, then skip if same value as unused previous" is a go-to for duplicate handling.

----------------------------------------

## Step 8: Complexity

Time: O(n · n!) for output in the worst case (all distinct); less when duplicates reduce the set of unique permutations.
Space: O(n) for the used array and recursion stack.

----------------------------------------

## Step 9: C++ Implementation

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
            if (i > 0 && nums[i] == nums[i-1] && !used[i-1]) continue;
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

Two key ingredients: sort + the skip-duplicate-sibling rule.

----------------------------------------

## Step 10: Follow-up Questions

- **Count distinct permutations.** Instead of listing, increment a counter. Or use the formula `n! / (k1! · k2! · ... )` where ki is the count of each distinct value.
- **Next permutation with duplicates.** O(n) algorithm similar to standard next permutation.
- **k-th unique permutation.** Factorial decomposition with duplicate awareness.
- **Why not dedupe with a set at the end?** Works but wastes time generating duplicates and memory storing them. Pruning is more efficient.
- **The skip condition with `used[i-1]`.** An alternative formulation uses `used[i-1]` being true (not false); some texts differ. Both give correct algorithms; the logic is equivalent with different interpretations.
