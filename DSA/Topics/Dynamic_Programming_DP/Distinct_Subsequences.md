# Distinct Subsequences

**Problem Link:**
https://leetcode.com/problems/distinct-subsequences/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Reread the Prompt Slowly

Given two strings `s` and `t`, count the number of **distinct subsequences** of `s` that equal `t`.

A subsequence keeps relative order but may skip characters. So if `s = "rabbbit"`, we could pick indices {0, 1, 3, 6} to form "rabit"... wait that's not a match for `t = "rabbit"`. Let me find matches.

`t = "rabbit"`.
- `s = "rabbbit"` has r-a-b-b-b-i-t. We need to pick 'r', 'a', 'b', 'b', 'i', 't' in order.
- Option 1: indices 0, 1, 2, 3, 5, 6 — chars r, a, b, b, i, t = "rabbit". ✓
- Option 2: indices 0, 1, 2, 4, 5, 6 — r, a, b, b, i, t. ✓
- Option 3: indices 0, 1, 3, 4, 5, 6 — r, a, b, b, i, t. ✓

Three distinct index selections all form `"rabbit"`. Answer: **3**.

Different index selections that yield the *same* subsequence string still count as distinct — the problem is about how many distinct *ways* to form t as a subsequence, not distinct *strings*.

----------------------------------------

## Step 2: Small Cases

`s = "abc"`, `t = ""`. Number of ways to form empty string from any s: always 1 (pick no characters). Answer: 1.

`s = ""`, `t = "a"`. Need at least one 'a' from an empty string. Impossible. Answer: 0.

`s = "aaa"`, `t = "a"`. Ways to pick one 'a' from "aaa" — three choices (index 0, 1, or 2). Answer: 3.

`s = "aaa"`, `t = "aa"`. Ways to pick two a's in order from three a's — C(3, 2) = 3 choices. Answer: 3.

`s = "ab"`, `t = "ab"`. Only one way: pick both in order. Answer: 1.

`s = "ba"`, `t = "ab"`. Order matters. Can we get a-b from b-a? No. Answer: 0.

A pattern forms: the answer depends on how many ways matching characters can be chosen while preserving order.

----------------------------------------

## Step 3: Set Up the DP State

Let `f(i, j)` = number of distinct subsequences of `s[0..i)` (first i characters of s) that equal `t[0..j)` (first j characters of t).

We want `f(|s|, |t|)`.

How does `f(i, j)` relate to smaller subproblems? Consider the last character we use from s, i.e., `s[i-1]`:

**Case A: we *don't* use `s[i-1]`** as the last-matched character. Then we're matching `t[0..j)` using only `s[0..i-1)`. So this contributes `f(i-1, j)`.

**Case B: we *do* use `s[i-1]` as the j-th character of t.** This is only possible if `s[i-1] == t[j-1]` (otherwise `s[i-1]` can't match `t[j-1]`). In that case, after matching `s[i-1]` with `t[j-1]`, we need to match `t[0..j-1)` with `s[0..i-1)`. Contributes `f(i-1, j-1)`.

Total: `f(i, j) = f(i-1, j) + (s[i-1] == t[j-1] ? f(i-1, j-1) : 0)`.

Base cases:
- `f(i, 0) = 1` for all i ≥ 0: one way to form the empty t from any prefix of s (by picking nothing).
- `f(0, j) = 0` for j > 0: no way to form a non-empty t from an empty s.

----------------------------------------

## Step 4: Verify on Small Cases

`s = "rabbbit"`, `t = "rabbit"`. n = 7, m = 6.

I won't fill the entire 7x6 table by hand but I'll compute `f(7, 6)` directly using the recurrence once I believe it's correct. Let me verify on smaller examples first.

`s = "aaa"`, `t = "aa"`, expect answer 3.

```
f(0, 0) = 1. f(0, 1) = 0. f(0, 2) = 0.
f(1, 0) = 1. s[0]='a'.
  f(1, 1): s[0]==t[0]='a' → f(0, 1) + f(0, 0) = 0 + 1 = 1.
  f(1, 2): s[0]==t[1]='a' → f(0, 2) + f(0, 1) = 0 + 0 = 0.
f(2, 0) = 1. s[1]='a'.
  f(2, 1): match → f(1, 1) + f(1, 0) = 1 + 1 = 2.
  f(2, 2): match → f(1, 2) + f(1, 1) = 0 + 1 = 1.
f(3, 0) = 1. s[2]='a'.
  f(3, 1): match → f(2, 1) + f(2, 0) = 2 + 1 = 3.
  f(3, 2): match → f(2, 2) + f(2, 1) = 1 + 2 = 3.
```

`f(3, 2) = 3`. ✓

`s = "rabbbit"`, `t = "rabbit"`. Computing this by the same recurrence (I'll trust the implementation) yields 3.

----------------------------------------

## Step 5: Why the Recurrence Is Exhaustive

For any subsequence-of-s that matches t, the last character of t (t[j-1]) must be matched by some character in s. The decision at level (i, j) is "does the j-th char of t match at position i-1 of s, or earlier?"

- If we match it at position i-1 (requires s[i-1] == t[j-1]), we reduce to matching t[0..j-1) with s[0..i-1) — that's `f(i-1, j-1)` ways.
- Otherwise, we match it earlier in s — equivalent to matching t[0..j) with s[0..i-1) — that's `f(i-1, j)` ways.

These two subcases are mutually exclusive (different positions where t[j-1] is matched) and cover all possibilities, so we add them.

This is the core DP trick: think about what happens at the "last step" of the subsequence alignment.

----------------------------------------

## Step 6: Space Optimization

Each cell depends on `f(i-1, j)` and `f(i-1, j-1)` — both from the previous row. So we can use a 1D array, updating it row by row.

But here's a subtlety. When updating `f[j]` (new row) we need `f[j]` (old row, for the first term) and `f[j-1]` (old row, for the second term). If we iterate `j` from left to right, we'd overwrite `f[j-1]` before we need it for `f[j]`.

Fix: iterate `j` from **right to left**, so `f[j-1]` is still from the old row when we compute `f[j]`.

```cpp
vector<long long> f(m + 1, 0);
f[0] = 1;
for (int i = 1; i <= n; ++i) {
    for (int j = m; j >= 1; --j) {
        if (s[i-1] == t[j-1]) f[j] = f[j] + f[j-1];
        // else f[j] stays the same (f(i, j) = f(i-1, j))
    }
}
return f[m];
```

O(m) space, O(n·m) time.

----------------------------------------

## Step 7: Name the Pattern

This is **counting DP on two sequences** — a close cousin to LCS, Edit Distance, and Interleaving String. All share the state `(i, j) = progress into s and into t` and transitions based on whether the current characters match.

The distinction: LCS and Edit Distance optimize some value; Distinct Subsequences **counts** configurations. The recurrence uses `+` instead of `max` or `min`, but the skeleton is the same.

----------------------------------------

## Step 8: Overflow Gotcha

The answer can grow quickly. The problem typically guarantees the answer fits in a 32-bit signed int, but intermediate computations with `long long` are a good habit — especially when the recurrence sums across many cells.

----------------------------------------

## Step 9: Complexity

Time: **O(n · m)**.
Space: **O(n · m)** full table, **O(m)** with the rolling array.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int numDistinct(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<unsigned long long>> f(n + 1, vector<unsigned long long>(m + 1, 0));
    for (int i = 0; i <= n; ++i) f[i][0] = 1;   // one way to form empty t

    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            f[i][j] = f[i - 1][j];   // case A: don't use s[i-1]
            if (s[i - 1] == t[j - 1]) {
                f[i][j] += f[i - 1][j - 1];   // case B: use s[i-1] as t[j-1]
            }
        }
    }
    return (int)f[n][m];
}
```

Notes:
- I use `unsigned long long` to guard against intermediate overflow. The final cast assumes the answer fits.
- The `f[i][0] = 1` initialization is crucial — every row in column 0 represents "empty t," which has exactly 1 way.

Space-optimized version:

```cpp
int numDistinct(string s, string t) {
    int n = s.size(), m = t.size();
    vector<unsigned long long> f(m + 1, 0);
    f[0] = 1;
    for (int i = 1; i <= n; ++i) {
        for (int j = m; j >= 1; --j) {
            if (s[i - 1] == t[j - 1]) f[j] += f[j - 1];
        }
    }
    return (int)f[m];
}
```

Right-to-left iteration in the inner loop preserves the "previous row" values we need.

----------------------------------------

## Step 11: Follow-up Questions

- **Count subsequences with a specific structure** (e.g., palindromic subsequences). Different DP state, similar structure.
- **Count distinct subsequences of s** (any string, not matching a specific t). Separate DP tracking "new subsequences introduced by each character."
- **Longest Common Subsequence (LCS).** Same shape of DP, but max instead of sum; answer is a length.
- **If we want the actual subsequences, not just the count.** Backtrack through the DP table; pick both branches when available.
- **What if t contains wildcards like `.` for any char?** Adjust the match check; everything else is identical.
