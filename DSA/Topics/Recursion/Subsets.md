# Subsets

**Problem Link:**
https://leetcode.com/problems/subsets/

**Topic:**
Recursion

----------------------------------------

## Step 1: What Are We Asked

Given an array of distinct integers, return **all possible subsets** (the power set). The result can be in any order, but no duplicate subsets.

Example: `nums = [1, 2, 3]`. Subsets:

```
[], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]
```

That's 8 subsets, which is `2^3`. A set of `n` elements has `2^n` subsets — each element is either in or out, 2 choices per element, n elements → `2^n`.

----------------------------------------

## Step 2: Start Small

**n = 0, `[]`:** only subset is `[]`. Count = 1.

**n = 1, `[a]`:** subsets are `[]` and `[a]`. Count = 2.

**n = 2, `[a, b]`:** `[]`, `[a]`, `[b]`, `[a,b]`. Count = 4.

**n = 3, `[a, b, c]`:** looking at the `n = 2` subsets, each either **includes `c`** or not.

- Subsets without `c`: `[], [a], [b], [a,b]` — exactly the `n = 2` result.
- Subsets with `c`: `[c], [a,c], [b,c], [a,b,c]` — each subset from `n = 2` plus `c`.

So `subsets([a,b,c]) = subsets([a,b]) ∪ (subsets([a,b]) each extended with c)`.

That's the recurrence! Each new element **doubles** the number of subsets.

----------------------------------------

## Step 3: Two Natural Algorithms Fall Out

### Approach A — Iterative doubling

```cpp
vector<vector<int>> result = {{}};
for (int x : nums) {
    int sz = result.size();
    for (int i = 0; i < sz; ++i) {
        auto copy = result[i];
        copy.push_back(x);
        result.push_back(copy);
    }
}
```

Start with the single empty subset. For each new element, copy every existing subset and add the new element to the copy. Done.

Let me trace `[1, 2, 3]`:

```
Start: [ [] ]
After 1: [ [], [1] ]
After 2: [ [], [1], [2], [1,2] ]
After 3: [ [], [1], [2], [1,2], [3], [1,3], [2,3], [1,2,3] ]
```

That's all 8 subsets.

### Approach B — Recursive include/exclude

For each element, we decide: include it or not. That's a binary choice, and with n elements we have 2^n branches.

```cpp
void dfs(vector<int>& nums, int i, vector<int>& cur, vector<vector<int>>& res) {
    if (i == (int)nums.size()) { res.push_back(cur); return; }
    // Option 1: don't include nums[i]
    dfs(nums, i + 1, cur, res);
    // Option 2: include nums[i]
    cur.push_back(nums[i]);
    dfs(nums, i + 1, cur, res);
    cur.pop_back();
}
```

The recursion tree is a binary tree of depth n with 2^n leaves. Each leaf corresponds to one subset.

### Approach C — "Start-index" backtracking

A slightly different style. For each subset, we pick elements in increasing order of index:

```cpp
void dfs(vector<int>& nums, int start, vector<int>& cur, vector<vector<int>>& res) {
    res.push_back(cur);
    for (int i = start; i < (int)nums.size(); ++i) {
        cur.push_back(nums[i]);
        dfs(nums, i + 1, cur, res);
        cur.pop_back();
    }
}
```

We record the current subset at every recursion entry (not just leaves). Each call extends the subset by one of the remaining elements in order.

All three approaches work and enumerate exactly the same 2^n subsets.

----------------------------------------

## Step 4: Trace the Backtracking Version

Let's trace Approach C on `[1, 2, 3]`.

```
dfs(start=0, cur=[]):
  record []
  i=0: push 1, dfs(start=1, cur=[1]):
         record [1]
         i=1: push 2, dfs(start=2, cur=[1,2]):
                record [1,2]
                i=2: push 3, dfs(start=3, cur=[1,2,3]):
                       record [1,2,3]
                       (no more i)
                     pop 3
                (no more i)
              pop 2
         i=2: push 3, dfs(start=3, cur=[1,3]):
                record [1,3]
              pop 3
       pop 1
  i=1: push 2, dfs(start=2, cur=[2]):
         record [2]
         i=2: push 3, dfs(start=3, cur=[2,3]):
                record [2,3]
              pop 3
       pop 2
  i=2: push 3, dfs(start=3, cur=[3]):
         record [3]
       pop 3
```

Recorded in order: `[], [1], [1,2], [1,2,3], [1,3], [2], [2,3], [3]`. All 8 subsets. ✓

The `start` parameter prevents us from picking earlier elements in later recursions, which would produce duplicates like `[2, 1]` (reorderings).

----------------------------------------

## Step 5: A Bit-Masking Version (Bonus)

Since each of n elements is either in or out, we can represent a subset as an n-bit number. Bit k set means element k is included. Then enumerate masks from 0 to 2^n - 1:

```cpp
vector<vector<int>> subsets(vector<int>& nums) {
    int n = nums.size();
    vector<vector<int>> res;
    for (int mask = 0; mask < (1 << n); ++mask) {
        vector<int> sub;
        for (int i = 0; i < n; ++i)
            if (mask & (1 << i)) sub.push_back(nums[i]);
        res.push_back(sub);
    }
    return res;
}
```

This is elegant for small n (≤ 20 or so), but of course it's still 2^n work.

----------------------------------------

## Step 6: Why the "Start" Parameter Matters

Without the `start` parameter — i.e., if we simply loop over all `i` from 0 each time — we'd generate each subset multiple times. For example, `[1, 2]` and `[2, 1]` would both be generated, but they're the same subset.

The `start` constraint enforces an ordering on how we build subsets: we always pick the elements in ascending index order. This guarantees each subset is built exactly once.

This is the same trick that appears in Combination Sum, Subsets II, and similar problems. When you want *combinations* (order-independent) rather than *permutations* (order-dependent), you fix the traversal order using `start`.

----------------------------------------

## Step 7: Complexity

Time: `2^n` subsets, each of average size `n/2`, total work **O(n · 2^n)**. There's no way to go faster because the output itself has that size.

Space: **O(n · 2^n)** for the output, **O(n)** extra for the recursion stack or the temporary subset buffer.

----------------------------------------

## Step 8: C++ Implementation

```cpp
void dfs(vector<int>& nums, int start, vector<int>& cur, vector<vector<int>>& res) {
    res.push_back(cur);
    for (int i = start; i < (int)nums.size(); ++i) {
        cur.push_back(nums[i]);
        dfs(nums, i + 1, cur, res);
        cur.pop_back();
    }
}

vector<vector<int>> subsets(vector<int>& nums) {
    vector<vector<int>> res;
    vector<int> cur;
    dfs(nums, 0, cur, res);
    return res;
}
```

Clean backtracking template. The `res.push_back(cur)` at every call records every partial subset — which are exactly all subsets.

----------------------------------------

## Step 9: Follow-up Questions

- **Subsets II (input may have duplicates).** Sort first, then at each `start`, skip any element equal to the previous one (at the same recursion depth). This avoids generating duplicate subsets.
- **Subsets summing to a target.** Use backtracking with a running sum; only record when the sum matches, and prune branches where it's already too big.
- **Combinations of a fixed size k.** Modify the base case to `if (cur.size() == k) record; return;`.
- **Lex-ordered subsets.** The start-parameter backtracking above produces them in lex order naturally.
- **Generating subsets on a stream with n very large but k small.** Use `std::next_combination` style — iterate only the size-k subsets.
