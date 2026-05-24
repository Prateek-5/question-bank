# Subsets — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Subsets.md`](../Subsets.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/subsets/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The introduction to backtracking.** The lesson: **for each element, make a CHOICE — include or exclude. Recurse. The recursion tree's 2^n leaves enumerate all subsets.** Master this and you've got the template for combinations, permutations, partitions, and the entire backtracking family.

**Map of this file (10 sections):**

1. Read the problem
2. Counting subsets — 2^n
3. The recurrence
4. The include/exclude recursion
5. The "start-index" backtracking template
6. Code
7. Trace it
8. The bitmask alternative
9. Common pitfalls
10. The shape — backtracking template

---

## 1. Read the problem

Given an array `nums` of **DISTINCT** integers, return **all possible subsets** (the power set). The solution set must not contain duplicate subsets.

**Examples:**

- `nums = [1, 2, 3]` → 8 subsets:
  ```
  [], [1], [2], [1,2], [3], [1,3], [2,3], [1,2,3]
  ```
- `nums = [0]` → `[[], [0]]`.

---

## 2. Counting subsets — 2^n

> **Mini-refresher: why a set of n elements has 2^n subsets.**
>
> Each element has TWO independent choices: IN the subset, or NOT.
>
> For n elements, independent choices multiply: `2 × 2 × ... × 2 = 2^n`.
>
> For n=3: 2³ = 8 subsets. For n=10: 1024. For n=20: about 10⁶ (manageable). For n=30: 10⁹ (too many to enumerate in real time).

So we expect exactly 2^n subsets in the output. The algorithm must produce each EXACTLY ONCE (no dups).

---

## 3. The recurrence

How do subsets of `[1, 2, 3]` relate to subsets of `[1, 2]`?

**Claim:** every subset of `[1, 2, 3]` either CONTAINS 3 or doesn't.
- **Subsets WITHOUT 3** = subsets of `[1, 2]` = `[], [1], [2], [1,2]`.
- **Subsets WITH 3** = each subset of `[1, 2]` + element 3 = `[3], [1,3], [2,3], [1,2,3]`.

Subsets of `[1, 2, 3]` = (subsets of `[1, 2]`) ∪ (each subset of `[1, 2]` with 3 added).

This recurrence DOUBLES at each step. From `[]` (1 subset), to `[a]` (2), to `[a, b]` (4), to `[a, b, c]` (8).

> **Mini-refresher: doubling iterative approach.**
>
> ```
> result = [[]]
> for x in nums:
>     for sub in result.copy():
>         result.append(sub + [x])
> ```
>
> Starts with one empty subset. Each new element doubles the count by ADDING that element to a copy of every existing subset.
>
> Same 2^n subsets, no recursion.

---

## 4. The include/exclude recursion

The recurrence translates directly to a binary recursion:

```
def dfs(i, current):
    if i == n:
        record current
        return
    # Choice 1: exclude nums[i]
    dfs(i + 1, current)
    # Choice 2: include nums[i]
    current.append(nums[i])
    dfs(i + 1, current)
    current.pop()
```

At each index i, branch on include/exclude. 2^n leaves, each representing one subset.

Pattern: **explore branch 1, then explore branch 2, then undo (pop)** to restore state.

> **Mini-refresher: backtracking's "apply / recurse / undo" structure.**
>
> ```
> apply choice
> recurse
> undo choice
> ```
>
> The "undo" is what makes it BACKTRACKING (rather than just recursion). Mutating SHARED STATE (`current` here) means we MUST restore it after exploring a branch.
>
> Forget the undo, and the next branch sees STALE state from the previous.

---

## 5. The "start-index" backtracking template

A second style, slightly different but equivalent:

```
def dfs(start, current):
    record current             # record AT EVERY recursion (not just leaves)
    for i in start..n-1:
        current.append(nums[i])
        dfs(i + 1, current)
        current.pop()
```

Difference:
- Old style: binary recursion at each level. Record at LEAVES.
- This style: iterate over remaining elements. Record at EVERY recursion.

The `start` parameter prevents picking earlier elements, which would produce ordering duplicates like `[2, 1]` (we want `[1, 2]` only).

> **Mini-refresher: why `start` instead of "is used"?**
>
> For SUBSETS (combinations), order doesn't matter — `[1, 2]` and `[2, 1]` are the same subset. We canonicalize by picking elements in INDEX ORDER. `start` enforces this.
>
> For PERMUTATIONS (next file), order DOES matter — we need both `[1, 2]` and `[2, 1]`. There we use a `used[]` array instead, allowing any unused element at each level.

Each subset is built EXACTLY ONCE via this start-indexed walk.

---

## 6. Code

**C++ (start-index template):**

```cpp
void dfs(vector<int>& nums, int start, vector<int>& cur, vector<vector<int>>& res) {
    res.push_back(cur);              // record snapshot
    for (int i = start; i < (int)nums.size(); ++i) {
        cur.push_back(nums[i]);
        dfs(nums, i + 1, cur, res);
        cur.pop_back();              // undo
    }
}

vector<vector<int>> subsets(vector<int>& nums) {
    vector<vector<int>> res;
    vector<int> cur;
    dfs(nums, 0, cur, res);
    return res;
}
```

**Python:**

```python
def subsets(nums):
    res = []
    def dfs(start, cur):
        res.append(cur[:])           # snapshot copy
        for i in range(start, len(nums)):
            cur.append(nums[i])
            dfs(i + 1, cur)
            cur.pop()
    dfs(0, [])
    return res
```

> **Mini-refresher: snapshot vs reference.**
>
> When you "record" `cur`, you MUST COPY it. `res.push_back(cur)` (C++) copies the vector. `res.append(cur[:])` (Python) makes a slice-copy. `res.append(cur)` would append a REFERENCE — and as we mutate `cur` later, ALL recorded "subsets" would change.
>
> This is the #1 bug in backtracking. Always snapshot.

Complexity: **O(n × 2^n) time** (2^n subsets, each up to n elements to copy), **O(n × 2^n) output space.**

---

## 7. Trace it

**`nums = [1, 2, 3]`:**

```
dfs(start=0, cur=[]):
  record []                                       → res = [[]]
  i=0: push 1. dfs(start=1, cur=[1]):
    record [1]                                    → res = [[], [1]]
    i=1: push 2. dfs(start=2, cur=[1,2]):
      record [1,2]                                → res = [..., [1,2]]
      i=2: push 3. dfs(start=3, cur=[1,2,3]):
        record [1,2,3]                            → res = [..., [1,2,3]]
        (no more i)
      pop 3.
    pop 2.
    i=2: push 3. dfs(start=3, cur=[1,3]):
      record [1,3]                                → ...
    pop 3.
  pop 1.
  i=1: push 2. dfs(start=2, cur=[2]):
    record [2]; i=2: push 3 → record [2,3].
  pop 2.
  i=2: push 3. dfs(start=3, cur=[3]):
    record [3].
  pop 3.

Final res = [[], [1], [1,2], [1,2,3], [1,3], [2], [2,3], [3]]. 8 subsets.  ✓
```

The order is depth-first (recurse fully into the leftmost branch before backtracking). Different traversal orders are also valid.

---

## 8. The bitmask alternative

Since each element is in/out (binary), use an n-bit mask to represent a subset.

```
for mask in 0..(1 << n) - 1:
    sub = []
    for i in 0..n-1:
        if mask & (1 << i):
            sub.append(nums[i])
    res.append(sub)
```

O(n × 2^n) — same as backtracking. Clean for n ≤ 20.

> **Mini-refresher: bit iteration enumerates all subsets.**
>
> For n bits, masks 0 to 2^n - 1 represent every possible subset choice:
> - mask 0: no bits set → empty subset.
> - mask `(1 << n) - 1`: all bits set → full subset.
>
> Each bit's position corresponds to an element's index.

Use bitmask when n is small (≤ 20). Backtracking is more flexible (extends to constraints).

---

## 9. Common pitfalls

1. **Pushing `cur` instead of a COPY.** All recorded subsets end up being references to the same vector — which is empty at the end. Always snapshot.

2. **Forgetting to undo.** State accumulates; results are wrong.

3. **Starting the inner loop from 0 instead of `start`.** Generates permutations, not subsets. We'd see `[1, 2]` AND `[2, 1]` (same subset twice).

4. **Recording only at leaves.** The start-index template records at EVERY call (including the initial empty cur). If you only record at leaves, you miss intermediate subsets.

5. **Off-by-one in `start`.** Use `start = i + 1` when recursing (move past the just-picked index).

6. **Treating distinct/duplicate inputs the same.** This problem promises DISTINCT inputs. For duplicates, use Subsets II's sort + skip rule.

7. **Computing subset count then trying to enumerate by index.** 2^n grows fast. For n = 30, you have ~10⁹ subsets — too many.

---

## 10. The shape — backtracking template

The **APPLY / RECURSE / UNDO** template is foundational:

```
def backtrack(state):
    if terminal:
        record state.copy()
        return
    for choice in options(state):
        apply(choice)
        backtrack(new state)
        undo(choice)
```

Where this generalizes:

| Problem | "Choice" | Terminal |
|---|---|---|
| **This problem** (Subsets) | include/exclude each element | all considered |
| Subsets II (duplicates) | include/exclude with dedup | all considered |
| Permutations | which element next | all placed |
| Combination Sum | which value next (with reuse) | sum reached |
| N-Queens | which column to place queen | all rows placed |
| Word Search | which adjacent cell to visit | found word |
| Sudoku Solver | which digit to place | board complete |

**Pattern to internalize:**

> "Backtracking = systematic exploration of a tree of choices. Apply choice, recurse, undo. Snapshot copies of complete states. The recursion tree's size is the search space size."

This template solves many problems. Master the choice/recurse/undo cycle, and you're ready for the entire backtracking topic.

---

> **Self-check — the question to ask next time.**
>
> When you face "enumerate all configurations" or "find all valid arrangements," ask:
>
> > **"Can I make a choice, recurse into the smaller problem, then undo? Each leaf of the recursion tree corresponds to one configuration."**
>
> If yes, you've got backtracking.

---

## Cross-references

- **Reference card (post-mastery):** [`../Subsets.md`](../Subsets.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Subsets_II.md`](./Subsets_II.md) — handle duplicates.
  - Coming next: [`Permutations.md`](./Permutations.md) — used-flag instead of start.
  - Coming later: [`N_Queens.md`](./N_Queens.md) — constraint-driven.
