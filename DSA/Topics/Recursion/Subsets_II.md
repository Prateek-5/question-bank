# Subsets II

**Problem Link:**
<a href="https://leetcode.com/problems/subsets-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/subsets-ii/</a>

**Topic:**
Recursion

----------------------------------------

## Step 1: Problem Setup

Given an integer array `nums` that **may contain duplicates**, return all possible subsets (the power set) **without duplicates**.

Example: `nums = [1, 2, 2]`.

All 2^3 = 8 subsets if we considered positions:
- {} (empty)
- {1}, {2 @ pos 1}, {2 @ pos 2}
- {1, 2 @ pos 1}, {1, 2 @ pos 2}, {2, 2}
- {1, 2, 2}

Ignoring position (subsets are unordered multisets):
- {}, {1}, {2}, {1, 2}, {2, 2}, {1, 2, 2}

6 unique subsets. Return them.

----------------------------------------

## Step 2: Subsets I Recap

For distinct inputs, standard backtracking produces all 2^n subsets:

```
def backtrack(start, current):
    result.append(current.copy())
    for i in start..n-1:
        current.append(nums[i])
        backtrack(i + 1, current)
        current.pop()
```

For `[1, 2, 3]`, this produces {}, {1}, {1,2}, {1,2,3}, {1,3}, {2}, {2,3}, {3}. 8 subsets.

But for `[1, 2, 2]`, this would produce duplicates: picking 2 @ pos 1 alone and 2 @ pos 2 alone both yield subset {2}.

----------------------------------------

## Step 3: Skip Sibling Duplicates

**Same trick as Permutations II / Combination Sum II:** sort, then at each level skip indices that are duplicates of their previous sibling.

Specifically: within a single level (one recursion depth, one iteration of the for-loop), skip `i` if `i > start` and `nums[i] == nums[i-1]`.

Why "within a level, not globally"? Because across different recursion depths, duplicates might be legitimately chosen (e.g., we DO want {2, 2} in the output — that uses both 2s). Skipping globally would over-prune.

The condition `i > start` is the key: we allow the first occurrence of a value at each level; we skip subsequent same-valued indices at the same level.

----------------------------------------

## Step 4: Algorithm

```
sort(nums)

def backtrack(start, current):
    result.append(current.copy())
    for i in start..n-1:
        if i > start and nums[i] == nums[i-1]: continue
        current.append(nums[i])
        backtrack(i + 1, current)
        current.pop()

backtrack(0, [])
return result
```

----------------------------------------

## Step 5: Trace on `[1, 2, 2]`

Sort: [1, 2, 2]. (Already sorted.)

```
backtrack(start=0, current=[]):
  RECORD [].
  i=0 (value 1):
    current=[1].
    backtrack(1, [1]):
      RECORD [1].
      i=1 (value 2):
        current=[1, 2].
        backtrack(2, [1, 2]):
          RECORD [1, 2].
          i=2 (value 2):
            current=[1, 2, 2].
            backtrack(3, [1, 2, 2]):
              RECORD [1, 2, 2].
              (no more i in range).
            undo.
        undo.
      i=2 (value 2): i > start=1 and nums[2]==nums[1]. SKIP.
    undo.
  i=1 (value 2):
    current=[2].
    backtrack(2, [2]):
      RECORD [2].
      i=2 (value 2):
        current=[2, 2].
        backtrack(3, [2, 2]):
          RECORD [2, 2].
        undo.
    undo.
  i=2 (value 2): i > start=0 and nums[2]==nums[1]. SKIP.
```

Recorded: [], [1], [1, 2], [1, 2, 2], [2], [2, 2]. Six subsets. ✓

Notice the skip fires twice: at the top-level (skipping to re-starting a subset with just the "second" 2), and inside the subtree rooted at picking the first 2 (skipping to re-pick a pair of 2s starting from the second 2).

Both skips correctly prevent duplicate outputs.

----------------------------------------

## Step 6: Why the Rule Works

**Claim:** "skip i if i > start and nums[i] == nums[i-1]" produces each unique subset exactly once.

**Proof sketch:** For any unique subset S, order its elements by the canonical sorted order. Each unique subset corresponds to exactly **one canonical index path**: pick elements in order of increasing index. When duplicates exist in `nums`, the canonical path picks the **first available** duplicate. The skip rule enforces this canonicalization: we never start a subset with a duplicate of a sibling at the same level.

So each unique subset is produced by exactly one backtracking path. No duplicates.

----------------------------------------

## Step 7: Name It

**Backtracking with sibling-duplicate skipping for unique subsets.** Same pattern applied across:
- Combination Sum II.
- Permutations II.
- Palindrome Partitioning.
- N-Queens variants.

The canonical form: sort, then skip repeated values at the same recursion level.

----------------------------------------

## Step 8: Complexity

Time: up to 2^n subsets, each of average length n/2 to copy. **O(n · 2^n)** worst case.
Space: **O(n)** for recursion + O(output size).

----------------------------------------

## Step 9: C++ Implementation

```cpp
class Solution {
    vector<vector<int>> result;
    vector<int> current;
    vector<int> nums;

    void backtrack(int start) {
        result.push_back(current);
        for (int i = start; i < (int)nums.size(); ++i) {
            if (i > start && nums[i] == nums[i-1]) continue;
            current.push_back(nums[i]);
            backtrack(i + 1);
            current.pop_back();
        }
    }

public:
    vector<vector<int>> subsetsWithDup(vector<int>& input) {
        nums = input;
        sort(nums.begin(), nums.end());
        backtrack(0);
        return result;
    }
};
```

Ten lines. The sort + skip-sibling-duplicates is the dedup mechanism.

----------------------------------------

## Step 10: Follow-up Questions

- **Subsets II but return only subsets of size k.** Add a size check before recording.
- **Count unique subsets without listing.** Use formula: product over each distinct value of (count+1). For [1, 2, 2]: (1+1)(2+1) = 6. ✓
- **Subsets of a multiset with a sum constraint.** Add a sum parameter to the recursion.
- **Iterative version.** Use the "for each element, double the current set" trick, but dedupe for each new duplicate.
- **Bitmask enumeration.** For small n (≤ 20), enumerate 2^n masks, deduplicate at the end.
- **Why is the skip condition `i > start` (not `i > 0`)?** Because we want to allow the same value to appear at different recursion depths; we only skip "same level" duplicates, which is captured by comparing `i` to `start`.
