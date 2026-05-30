# Longest Consecutive Sequence

**Problem Link:**
<a href="https://leetcode.com/problems/longest-consecutive-sequence/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/longest-consecutive-sequence/</a>

**Topic:**
Hashing / Sliding Window

----------------------------------------

## Step 1: What's Being Asked

Given an **unsorted** array of integers, find the length of the longest sequence of **consecutive integers** present in the array (not necessarily contiguous within the array, but consecutive in value).

Example: `nums = [100, 4, 200, 1, 3, 2]`. Consecutive sequences we can form:
- `100` alone — length 1.
- `200` alone — length 1.
- `1, 2, 3, 4` — length 4 (since 1, 2, 3, 4 are all present).

Answer: **4**.

And the problem demands O(n) time. That's the catch — sorting would give us O(n log n), which feels intuitive but isn't allowed.

----------------------------------------

## Step 2: Why Sorting Feels Right (And Is Forbidden)

If we sort: `[1, 2, 3, 4, 100, 200]`. Walk the array, track the current streak of consecutive values, update the max. Simple. But sorting is O(n log n).

To beat that, we need to exploit a structure other than sort order. Let's think about what we have.

Hashing gives O(1) lookup. If I put all numbers into a `set`, I can ask "is `x + 1` in the set?" in constant time. That's a clue.

----------------------------------------

## Step 3: Naive "Start From Every Number" Approach

Idea: put everything in a set. For each number `x` in the array, check if `x + 1` is in the set, then `x + 2`, and so on until we hit a missing value. Record the streak length.

```cpp
unordered_set<int> s(nums.begin(), nums.end());
int best = 0;
for (int x : s) {
    int cur = x, len = 1;
    while (s.count(cur + 1)) { cur++; len++; }
    best = max(best, len);
}
```

This looks like it should be O(n) — one lookup per step. But wait: if the array is `[1, 2, 3, ..., n]`, then:
- Starting from 1, we walk `n` steps.
- Starting from 2, we walk `n - 1` steps.
- Starting from 3, `n - 2` steps.
- ...

Total: `n + (n-1) + ... + 1 = O(n²)`. Not linear.

The problem is that we're re-walking the same streak from every starting point. Most starting points aren't actually the starts of streaks.

----------------------------------------

## Step 4: The Fix — Only Start From Streak Starts

A number `x` is the **start** of a streak if `x - 1` is **not** in the set. If `x - 1` is in the set, we'd reach `x` eventually when walking from `x - 1` (or earlier), so starting from `x` is redundant.

So: only walk from numbers that are streak starts.

```cpp
unordered_set<int> s(nums.begin(), nums.end());
int best = 0;
for (int x : s) {
    if (s.count(x - 1)) continue;   // x is not a streak start, skip
    int cur = x, len = 1;
    while (s.count(cur + 1)) { cur++; len++; }
    best = max(best, len);
}
```

Now the total work is O(n). Let me explain why.

For any streak of length `L`, only its **first** element triggers the inner walk. That walk processes `L` numbers. Across all streaks, the total walk work sums to `n` (the total count of numbers). The outer loop iterates `n` times, but most iterations skip immediately (the `if` check fails). So total time: O(n).

----------------------------------------

## Step 5: Trace on the Example

`nums = [100, 4, 200, 1, 3, 2]`. Set: `{100, 4, 200, 1, 3, 2}`.

Iterate over the set (order is implementation-dependent; I'll iterate in insertion-like order):

```
x = 100: is 99 in set? No. Start of streak.
  while 101 in set? No. Streak length = 1.
  best = 1.

x = 4: is 3 in set? Yes. Skip.

x = 200: is 199 in set? No.
  while 201 in set? No. Length = 1.
  best = 1.

x = 1: is 0 in set? No.
  while 2 in set? Yes (cur=2, len=2).
  while 3 in set? Yes (cur=3, len=3).
  while 4 in set? Yes (cur=4, len=4).
  while 5 in set? No.
  best = 4.

x = 3: is 2 in set? Yes. Skip.

x = 2: is 1 in set? Yes. Skip.
```

Final best = **4**. ✓

Walked only 4 steps total in the inner loop (for the streak starting at 1). Linear overall.

----------------------------------------

## Step 6: Why This Works — The Amortization Argument

Let me state it cleanly. Every number appears in exactly one consecutive streak. When we "walk" a streak, we touch each of its numbers once in the inner loop. The condition `s.count(x - 1) == false` is true for exactly one number per streak — the smallest. So the inner loop runs exactly once per streak.

Total work in inner loops: sum of all streak lengths = n.
Total work in outer loop: n iterations, each doing O(1) work to check `x - 1`.
**Total: O(n).**

Duplicates in the array don't matter — the set deduplicates automatically.

----------------------------------------

## Step 7: Complexity

Time: **O(n)** average, because hashset operations are O(1) amortized. Worst case (adversarial hashing) is O(n²), but with a good hash function this is never hit on normal inputs.

Space: **O(n)** for the set.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int longestConsecutive(vector<int>& nums) {
    unordered_set<int> s(nums.begin(), nums.end());
    int best = 0;
    for (int x : s) {
        if (s.count(x - 1)) continue;    // not a streak start
        int cur = x, len = 1;
        while (s.count(cur + 1)) {
            cur++;
            len++;
        }
        best = max(best, len);
    }
    return best;
}
```

Three ideas pack into this short solution: set for O(1) lookup, "streak start" filter, extend-until-missing. Remove any one and it breaks.

----------------------------------------

## Step 9: Follow-up Questions

- **Return the actual sequence.** Track the range `[start, start + len - 1]` when updating `best`.
- **What if the array is huge and can't fit in memory?** Sort on disk and use the external-sort streak detection (O(n log n) disk ops) or a Bloom-filter-backed approximate version.
- **Longest consecutive sequence in a stream (you can't re-scan).** Harder — needs a data structure like a disjoint-set merge on `(x-1, x)` and `(x, x+1)` as each number arrives.
- **With a tolerance (at most `k` gaps allowed).** Totally different problem — probably needs sliding window on the sorted sequence.
- **2D version — longest diagonal streak in a matrix.** Different shape of problem; probably DP.
