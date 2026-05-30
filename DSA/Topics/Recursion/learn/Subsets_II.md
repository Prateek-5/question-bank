# Subsets II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Subsets_II.md`](../Subsets_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/subsets-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/subsets-ii/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: when input has DUPLICATES, sort first and skip same-valued siblings at the same recursion depth.** This is the "sort + skip" dedup pattern, used in: Subsets II, Permutations II, Combination Sum II, and many other backtracking problems. **Read [`Subsets.md`](./Subsets.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. Why standard subsets generates duplicates
3. The sort + skip rule
4. Why `i > start`, not `i > 0`
5. Code
6. Trace it
7. Common pitfalls
8. The shape — sibling-dedup template

---

## 1. Read the problem

Given an integer array `nums` that **may contain DUPLICATES**, return ALL possible subsets, with NO DUPLICATE subsets.

**Examples:**

- `nums = [1, 2, 2]` → `[[], [1], [2], [1,2], [2,2], [1,2,2]]`. 6 unique subsets.
- `nums = [0]` → `[[], [0]]`.
- `nums = [4, 4, 4, 1, 4]` → ...

---

## 2. Why standard subsets generates duplicates

If we apply the standard Subsets template to `[1, 2, 2]`:

```
dfs(0, [])
  pick 1: dfs(1, [1])
    pick 2 (first): dfs(2, [1, 2])
      pick 2 (second): dfs(3, [1, 2, 2])
    pick 2 (second): dfs(3, [1, 2])     ← DUPLICATE with [1, 2] from above
  pick 2 (first): dfs(2, [2])
    pick 2 (second): dfs(3, [2, 2])
  pick 2 (second): dfs(3, [2])           ← DUPLICATE with [2]
```

The duplicates come from picking either copy of `2` independently. We get `[1, 2]` twice and `[2]` twice.

**Fix:** at each recursion level, choose each VALUE at most once.

---

## 3. The sort + skip rule

> **Mini-refresher: sort + skip dedup pattern.**
>
> 1. **SORT** the input. This brings equal values next to each other.
> 2. In the recursion, at each level (in the for-loop), SKIP elements equal to the previous (sibling) one.
> 3. The skip applies only to SIBLINGS in the recursion tree — within ONE recursion level. Different levels can still use the duplicated value.

Concretely, in the for-loop inside `dfs(start, current)`:

```
for i in start..n-1:
    if i > start and nums[i] == nums[i-1]:
        continue       # skip duplicate sibling
    current.append(nums[i])
    dfs(i + 1, current)
    current.pop()
```

The condition `i > start` ensures the FIRST occurrence at each level is always processed. Subsequent equal-value indices at the SAME level are skipped.

---

## 4. Why `i > start`, not `i > 0`

> **Mini-refresher: skip ONLY siblings, not all duplicates.**
>
> If we used `i > 0`, we'd skip duplicates EVERYWHERE — including different recursion depths. But we WANT to use the same value at different depths to build subsets like `[2, 2]`.
>
> Specifically:
> - At top level (start=0), pick first 2 (i=1). Recurse.
> - At next level (start=2), the for-loop starts at i=2. We want to pick the second 2 here to build `[2, 2]`. With `i > start` (i.e., `2 > 2` is false), we PROCEED — correctly.
> - Back at top level, we'd try i=2 (start=0). `i > start` (2 > 0) is true, AND `nums[2] == nums[1]`. SKIP. We avoid the duplicate `[2]`.

The rule: **first sibling at each level is fine; later siblings with the same value are skipped.**

`i > start` checks "am I a LATER sibling at this level?" — i.e., are there more elements to my left at THIS level (which would have started at `start`)?

---

## 5. Code

**C++:**

```cpp
class Solution {
    vector<vector<int>> result;
    vector<int> current;
    vector<int> nums;

    void dfs(int start) {
        result.push_back(current);
        for (int i = start; i < (int)nums.size(); ++i) {
            if (i > start && nums[i] == nums[i - 1]) continue;
            current.push_back(nums[i]);
            dfs(i + 1);
            current.pop_back();
        }
    }

public:
    vector<vector<int>> subsetsWithDup(vector<int>& input) {
        nums = input;
        sort(nums.begin(), nums.end());
        dfs(0);
        return result;
    }
};
```

**Python:**

```python
def subsetsWithDup(nums):
    nums.sort()
    res = []
    def dfs(start, cur):
        res.append(cur[:])
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i - 1]:
                continue
            cur.append(nums[i])
            dfs(i + 1, cur)
            cur.pop()
    dfs(0, [])
    return res
```

**Complexity:** O(n × 2^n) time and space (output-bound).

---

## 6. Trace it

**`nums = [1, 2, 2]` (already sorted):**

```
dfs(start=0, cur=[]):
  record []
  
  i=0 (val=1): cur=[1].
    dfs(start=1, cur=[1]):
      record [1]
      i=1 (val=2): cur=[1, 2].
        dfs(start=2, cur=[1, 2]):
          record [1, 2]
          i=2 (val=2): cur=[1, 2, 2].
            dfs(start=3, cur=[1, 2, 2]):
              record [1, 2, 2]
              (no more i)
            cur=[1, 2].
        cur=[1].
      i=2 (val=2): i > start=1 AND nums[2] == nums[1]. SKIP.
    cur=[].

  i=1 (val=2): cur=[2].
    dfs(start=2, cur=[2]):
      record [2]
      i=2 (val=2): cur=[2, 2].
        dfs(start=3, cur=[2, 2]):
          record [2, 2]
        cur=[2].
    cur=[].

  i=2 (val=2): i > start=0 AND nums[2] == nums[1]. SKIP.

Recorded: [], [1], [1, 2], [1, 2, 2], [2], [2, 2]. SIX subsets.  ✓
```

The skip fires twice:
1. At i=2 inside `dfs(1, [1])` — would have produced duplicate `[1, 2]`.
2. At top-level i=2 — would have produced duplicate `[2]`.

Both correctly skipped.

---

## 7. Common pitfalls

1. **Forgetting to sort.** Without sorting, equal values aren't adjacent. The skip rule (`nums[i] == nums[i-1]`) wouldn't find them.

2. **Using `i > 0` instead of `i > start`.** Skips legitimate duplicates at DIFFERENT depths. You'd lose `[2, 2]` from `[1, 2, 2]`.

3. **Using a Set of tuples to dedup AFTER generating.** Works but wasteful — you'd generate up to 2^n subsets, many duplicates, then filter. Sort + skip prevents duplicates UPSTREAM.

4. **Confusing this with Permutations II.** Permutations use a different skip condition (`!used[i-1]` instead of `i > start`). Don't mix.

5. **Not snapshotting `current`.** Same issue as in Subsets — always copy when recording.

6. **Sorting changes original order — does it matter?** For this problem, NO (we only care about unique subsets). For some problems, you'd need to track original indices.

7. **Off-by-one in `nums[i-1]`.** When `i == 0`, `nums[i-1]` is out of bounds — but `i > start` (with start ≥ 0) prevents this.

---

## 8. The shape — sibling-dedup template

The "sort + skip same-valued siblings" pattern is THE standard dedup technique for backtracking on multisets.

| Problem | Skip rule |
|---|---|
| **This problem** | `i > start and nums[i] == nums[i-1]` (Subsets II) |
| Combination Sum II | same condition |
| Permutations II | `i > 0 and nums[i] == nums[i-1] and not used[i-1]` (more subtle) |
| Palindrome Partitioning (with duplicates) | similar |
| K Sum problems with duplicates | similar |

**Pattern to internalize:**

> "When the input may have duplicates and you're enumerating subsets/combinations, sort first. Within each recursion level, skip elements equal to the previous sibling: `if i > start and nums[i] == nums[i-1]: continue`."

This produces each UNIQUE configuration EXACTLY ONCE. No post-processing needed.

---

> **Self-check — the question to ask next time.**
>
> When you face backtracking on input that may have duplicates, ask:
>
> > **"Can I SORT first, then SKIP same-valued siblings at the same recursion depth? `i > start && nums[i] == nums[i-1]` gives canonical dedup."**
>
> If yes, no duplicate enumeration.

---

## Cross-references

- **Reference card (post-mastery):** [`../Subsets_II.md`](../Subsets_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Subsets.md`](./Subsets.md) — the distinct case.
  - Coming next: [`Permutations.md`](./Permutations.md), [`Permutations_II.md`](./Permutations_II.md), [`Combination_Sum_II.md`](./Combination_Sum_II.md).
