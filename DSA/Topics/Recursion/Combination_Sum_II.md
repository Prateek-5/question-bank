# Combination Sum II

**Problem Link:**
<a href="https://leetcode.com/problems/combination-sum-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/combination-sum-ii/</a>

**Topic:**
Recursion

----------------------------------------

## Step 1: Understand the Problem

Given an array of candidates (may contain duplicates!) and a target, return all unique combinations of candidates summing to target. **Each candidate may be used at most once**. The result must not contain duplicate combinations.

Example: `candidates = [10, 1, 2, 7, 6, 1, 5]`, target = 8.

Unique combinations summing to 8:
- [1, 1, 6]
- [1, 2, 5]
- [1, 7]
- [2, 6]

Return those four.

Two key twists compared to Combination Sum I:
1. **"At most once"**: can't reuse the same element.
2. **Duplicates in input**: the two 1's are different array entries (same value), so combining them *is* allowed, but we shouldn't produce the same combination twice because we picked two different copies of a duplicate.

----------------------------------------

## Step 2: Small Case by Hand

`[1, 1, 2]`, target = 3. What combinations sum to 3?
- [1, 2] using the first 1 and the 2.
- [1, 2] using the second 1 and the 2.

Both are the same combination. Return just one.

Naive backtracking (without dedup) would generate both. We need a way to skip duplicates.

----------------------------------------

## Step 3: Sort, Then Skip Siblings

The standard technique: sort the array first. Then when doing backtracking, at each recursion level, skip candidates that are equal to the previous one at the same level.

Why sort? So duplicates are adjacent. Easy to identify "same as previous sibling."

Why skip at the same level (not globally)? Because within a combination, we *can* use duplicates — they're different array positions. But we shouldn't *start* two branches at the same recursion level with the same value (that would generate duplicate combinations).

The rule: at each recursion level, the first occurrence of a value is fine; subsequent occurrences at the same level are skipped.

Concretely, in the loop `for i in start..n-1`, skip when `i > start and candidates[i] == candidates[i-1]`.

----------------------------------------

## Step 4: Build the Algorithm

```
sort candidates

def backtrack(start, remaining, path):
    if remaining == 0:
        result.append(path.copy())
        return
    
    for i in start..n-1:
        if candidates[i] > remaining:
            break   # sorted, so further candidates also too big
        if i > start and candidates[i] == candidates[i-1]:
            continue   # skip duplicate sibling at this level
        
        path.append(candidates[i])
        backtrack(i + 1, remaining - candidates[i], path)   # i+1: don't reuse
        path.pop()
```

Three pieces:
- **Prune by value**: if current candidate > remaining, stop (sorted; later candidates also too big).
- **Skip duplicates**: within a single `for` loop (one level), skip repeated values.
- **Advance past i**: recurse with `i + 1`, not `i`, so we don't reuse the same element.

Base case: remaining == 0 → record a copy of the path.

----------------------------------------

## Step 5: Trace on `[10, 1, 2, 7, 6, 1, 5]`, target = 8

Sort: `[1, 1, 2, 5, 6, 7, 10]`.

```
backtrack(start=0, remaining=8, path=[])
  i=0: path=[1]. backtrack(1, 7):
    i=1: path=[1, 1]. backtrack(2, 6):
      i=2: path=[1, 1, 2]. backtrack(3, 4):
        i=3: 5 > 4 break.
      path=[1, 1].
      i=3: path=[1, 1, 5]. backtrack(4, 1):
        i=4: 6 > 1 break.
      path=[1, 1].
      i=4: path=[1, 1, 6]. backtrack(5, 0):
        remaining == 0. RECORD [1, 1, 6].
      path=[1, 1].
      i=5: 7 > 0 break.
    path=[1].
    i=2: path=[1, 2]. backtrack(3, 5):
      i=3: path=[1, 2, 5]. backtrack(4, 0): RECORD [1, 2, 5].
      path=[1, 2].
      i=4: 6 > 5 break.
    path=[1].
    i=3: path=[1, 5]. backtrack(4, 2):
      i=4: 6 > 2 break.
    path=[1].
    i=4: path=[1, 6]. backtrack(5, 1):
      i=5: 7 > 1 break.
    path=[1].
    i=5: path=[1, 7]. backtrack(6, 0): RECORD [1, 7].
    path=[1].
    i=6: 10 > 0 break.
  path=[].
  i=1: skip (i > start=0 and candidates[1]==candidates[0]=1).
  i=2: path=[2]. backtrack(3, 6):
    i=3: path=[2, 5]. backtrack(4, 1):
      i=4: 6 > 1 break.
    path=[2].
    i=4: path=[2, 6]. backtrack(5, 0): RECORD [2, 6].
    path=[2].
    i=5: 7 > 0 break.
  path=[].
  i=3: path=[5]. backtrack(4, 3):
    i=4: 6 > 3 break.
  path=[].
  i=4: path=[6]. backtrack(5, 2):
    i=5: 7 > 2 break.
  ...similar, no more matches.
```

Results: `[1, 1, 6], [1, 2, 5], [1, 7], [2, 6]`. ✓

The crucial moment: at `i=1` in the top-level call, we skipped because `candidates[1] == candidates[0]` — avoiding the duplicate combination starting with the "second 1" alone.

But notice: *deeper* in the recursion (after we'd already picked the first 1), the second 1 was perfectly usable — hence `[1, 1, 6]` is in the result. The skip only applies **at the same level**, not across levels.

----------------------------------------

## Step 6: Why the Dedup Rule Is Right

When we process `i` at some level with `candidates[i] == candidates[i-1]` and `i > start`: the previous iteration (i-1 at this level) has already explored every combination starting with this value. Exploring it again with a different copy of the same value produces no new combinations.

But when the previous was picked (and we're recursing deeper), `start` in the recursive call is `i` (the index after the picked one), so the current `i` is `start` in the deeper call — meaning the "skip" condition `i > start` fails, and we don't skip. So duplicates are usable within a combination, just not as duplicate starting points.

This is a subtle but elegant dedup rule.

----------------------------------------

## Step 7: Name It

Classic **sorted backtracking with sibling dedup**. Same template solves:
- Subsets II (duplicates allowed in input, unique subsets output).
- Permutations II.
- Combination Sum (similar, but elements can be reused — uses i instead of i+1 for recursion).

The sort + skip-sibling-if-equal pattern is essential when input has duplicates and output must be unique.

----------------------------------------

## Step 8: Complexity

Time: in the worst case we explore most subsets. Each subset takes O(target) to construct and copy. Exponential in n but with aggressive pruning via sorting + break on exceeded remaining.

Space: O(target) for recursion depth + O(target) for path.

----------------------------------------

## Step 9: C++ Implementation

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
            if (candidates[i] > remaining) break;          // sorted: prune
            if (i > start && candidates[i] == candidates[i - 1]) continue;  // skip dup

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

Three key pieces of the inner loop:
- `break` on too-big: exits early (sort means rest are also too big).
- Skip condition: `i > start && candidates[i] == candidates[i-1]`.
- Recurse with `i + 1` (no reuse of the current index).

----------------------------------------

## Step 10: Follow-up Questions

- **Combination Sum I (unlimited reuse).** Similar algorithm, but recurse with `i` (not `i+1`) to allow reuse. No dedup needed since input is distinct by problem statement.
- **Return distinct sums (not combinations).** Collect sums into a set; shorter answer.
- **Count combinations instead of list them.** Dynamic programming — subset sum count.
- **Minimum number of candidates to reach target.** BFS or DP with "fewest" objective.
- **Variation: exactly k elements summing to target.** Add a `len(path) == k` condition to the base case.
- **Why "i > start" instead of "i > 0"?** Because duplicates are fine within a combination — we only want to avoid duplicates as **starting** points at each level.
