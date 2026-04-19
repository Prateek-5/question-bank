# Permutations

**Problem Link:**
https://leetcode.com/problems/permutations/

**Topic:**
Recursion

----------------------------------------

## Step 1: What Are We Counting?

Given an array of distinct integers, return *all possible orderings* of the elements. Each ordering is a different "permutation."

For `[1]`: just one ordering, `[1]`.
For `[1, 2]`: two orderings, `[1, 2]` and `[2, 1]`.
For `[1, 2, 3]`: how many? Let me enumerate carefully:
- `[1, 2, 3]`, `[1, 3, 2]`, `[2, 1, 3]`, `[2, 3, 1]`, `[3, 1, 2]`, `[3, 2, 1]`. Six.

In general, n distinct elements give n! permutations. Why? Pick any of n for position 0, then any of (n-1) remaining for position 1, etc. Product is n!.

----------------------------------------

## Step 2: Look at How I Enumerated

Look at the structure of my n = 3 enumeration. I grouped them by first element:

- First = 1: `[1, 2, 3]`, `[1, 3, 2]`.
- First = 2: `[2, 1, 3]`, `[2, 3, 1]`.
- First = 3: `[3, 1, 2]`, `[3, 2, 1]`.

Each group has 2 items, which is 2! — the number of ways to arrange the remaining 2 elements. That's not a coincidence.

**Insight:** generating permutations of `[1, 2, 3]` is the same as: for each possible first element, recursively generate permutations of the remaining two, and prepend that first element.

This is the right way to think about it — the problem decomposes naturally into smaller versions of itself.

----------------------------------------

## Step 3: Draw the Recursion Tree for `[1, 2, 3]`

```
pick first:                [1, 2, 3]  -- starts with empty current, all three available
                          /    |    \
                         1     2      3
                         |     |      |
                 [2 or 3 left]    ... etc
                        /\
                       2  3
                       |  |
                       3  2
                       |  |
                      end end

Outcome: reading each leaf's path gives a permutation.
```

Each level of the tree picks one more element for the current position. Once n levels have been picked, we've built a full permutation.

At each level we have to pick **an unused element**. That's the tricky detail — we need to remember which elements are still available.

----------------------------------------

## Step 4: Data We Need to Track

Two pieces of state that change as we descend:
1. `current` — the partial permutation built so far.
2. `used` — boolean array marking which positions in the original array are already consumed.

When we pick element `nums[i]` at some level, we:
- Mark `used[i] = true`.
- Append `nums[i]` to `current`.
- Recurse.
- When recursion returns, **unmark** `used[i]` and **pop** from `current` so the next iteration has a clean state.

That undo step is critical. Without it, the second iteration at a level would see stale state from the first and produce garbage.

----------------------------------------

## Step 5: The Code Mirroring the Tree

```
def permute(nums):
    result = []
    used = [False] * len(nums)
    current = []

    def dfs():
        if len(current) == len(nums):
            result.append(current.copy())
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            current.append(nums[i])
            dfs()
            current.pop()
            used[i] = False

    dfs()
    return result
```

Reading the code: each level of recursion picks the next element. We iterate over all unused indices, pick one, recurse, then undo.

----------------------------------------

## Step 6: Trace for [1, 2, 3]

Tracking `current` and `used` as we go:

```
dfs(), current=[], used=[F,F,F]
  i=0: mark used[0]. current=[1].
    dfs(), used=[T,F,F]
      i=0 skip.
      i=1: mark used[1]. current=[1,2].
        dfs(), used=[T,T,F]
          i=0,1 skip.
          i=2: mark used[2]. current=[1,2,3].
            dfs(): len=3, RECORD [1,2,3].
          unmark. current=[1,2].
      unmark. current=[1].
      i=2: mark used[2]. current=[1,3].
        dfs()
          i=1: mark. current=[1,3,2].
            RECORD [1,3,2].
          unmark.
      unmark. current=[1].
  unmark. current=[].
  i=1: similar gives [2,1,3], [2,3,1].
  i=2: gives [3,1,2], [3,2,1].
```

Six total. ✓

Notice the zig-zag pattern: we go all the way down to record, then pop up, try a different choice, go back down. That's backtracking — try, go deeper, undo, try differently.

----------------------------------------

## Step 7: Why Undo Matters

If I forgot to unmark `used[i]` after recursing, the second top-level iteration (`i=1`) would see `used = [T, F, F]` instead of `[F, F, F]`. It would think element 0 is already picked and skip it. The enumeration would be wrong.

Similarly, forgetting to `current.pop()` would leave stale values in `current`. When I eventually record a full permutation, it'd contain leftover elements from earlier branches.

**Rule of backtracking:** each recursive call must leave shared state exactly as it found it. Apply, recurse, undo.

----------------------------------------

## Step 8: Alternate Version — Swap in Place

A slicker (but less beginner-friendly) version: at depth `d`, decide which element belongs at position `d` by swapping it into place. The "unused" elements are always `nums[d..]`.

```cpp
void dfs(vector<int>& nums, int d, vector<vector<int>>& res) {
    if (d == (int)nums.size()) { res.push_back(nums); return; }
    for (int i = d; i < (int)nums.size(); ++i) {
        swap(nums[d], nums[i]);
        dfs(nums, d + 1, res);
        swap(nums[d], nums[i]);   // undo
    }
}
```

No `used` array needed, but we mutate `nums` in place. Each swap pair leaves `nums` unchanged after the recursion. Works but less transparent.

----------------------------------------

## Step 9: Naming

Enumerating permutations is a classic **backtracking** problem — we incrementally build solutions, undoing choices when we're done with them. The template (apply → recurse → undo) covers a huge space of problems: subsets, combinations, N-Queens, Sudoku, word ladders, graph coloring.

----------------------------------------

## Step 10: Complexity

Time: we generate n! permutations; each takes O(n) to copy into the result. Total **O(n · n!)**. Asymptotically unavoidable — the output itself has that size.

Space: recursion depth is n (O(n) stack). Markers are O(n). Output excluded, O(n) extra.

----------------------------------------

## Step 11: C++ Implementation

```cpp
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
        cur.pop_back();       // undo
        used[i] = false;
    }
}

vector<vector<int>> permute(vector<int>& nums) {
    vector<vector<int>> res;
    vector<bool> used(nums.size(), false);
    vector<int> cur;
    cur.reserve(nums.size());
    dfs(nums, used, cur, res);
    return res;
}
```

Shared state (`used`, `cur`) is passed by reference. The apply-recurse-undo bracket is the load-bearing structure.

----------------------------------------

## Step 12: Follow-up Questions

- **Permutations with duplicates.** Sort the input; at each level, skip a value if it's the same as the previous one and that previous one is currently unused (otherwise we'd duplicate permutations).
- **Next permutation only (not all).** O(n) algorithm: find the rightmost "break" where nums[i] < nums[i+1], find the smallest value larger than nums[i] to its right, swap, reverse suffix.
- **k-th permutation in lex order.** Compute digit-by-digit using factorials; no enumeration needed.
- **Permutations of a string rather than an array.** Exactly the same — swap `vector<int>` for `string`.
- **Permutations of a fixed size r.** Stop recursing when `cur.size() == r`.
- **Permutations satisfying a custom constraint.** Add a check before the apply step; skip if violated.
