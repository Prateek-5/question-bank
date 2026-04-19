# Longest Common Subsequence

**Problem Link:**
https://leetcode.com/problems/longest-common-subsequence/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: What's a "Common Subsequence"?

Given two strings `s` and `t`, a **common subsequence** is any string that appears as a subsequence in both. A subsequence means you pick characters in order (without rearranging), but you can skip characters. So `"ace"` is a subsequence of `"abcde"` (pick a, c, e; skip b, d).

Find the **longest** common subsequence, and return its length.

Example: `s = "abcde"`, `t = "ace"`. A common subsequence: `"ace"` (length 3). Nothing longer is possible. Answer: **3**.

Another: `s = "abc"`, `t = "def"`. No characters in common → LCS length 0.

----------------------------------------

## Step 2: Try a Small Case by Hand

`s = "ab"`, `t = "ba"`.

Common subsequences: `""` (length 0), `"a"` (pick s[0] and t[1]), `"b"` (pick s[1] and t[0]). Length 1. Can we get 2? That would require both `a` and `b` in the same order in both strings. In `s`, `a` comes before `b`. In `t`, `b` comes before `a`. So no common length-2 subsequence. LCS = 1.

`s = "abc"`, `t = "ac"`:
- `"a"` — length 1.
- `"c"` — length 1.
- `"ac"` — pick a from s[0] and t[0], c from s[2] and t[1]. Both orders match. Length 2.
- Length 3? No way — `t` has only 2 characters.

So LCS("abc", "ac") = 2.

----------------------------------------

## Step 3: Focus on the Last Characters

This is a string-alignment pattern that pays off: think about what happens at the **last character** of each string.

Define `f(i, j)` = length of LCS of `s[0..i-1]` and `t[0..j-1]`. (Using prefix lengths rather than indices simplifies base cases.)

Two cases based on whether the last characters match:

**Case 1: `s[i-1] == t[j-1]`.**

Great — these matching characters can be included in the LCS. Use them, then find the LCS of the remaining prefixes.

```
f(i, j) = 1 + f(i - 1, j - 1)
```

**Case 2: `s[i-1] != t[j-1]`.**

The matching character at this position can't use both. So the last character of the LCS either came from `s` (not using `t[j-1]`) or from `t` (not using `s[i-1]`) — or from neither. We pick the better of:
- Skip `s`'s last → `f(i - 1, j)`.
- Skip `t`'s last → `f(i, j - 1)`.

```
f(i, j) = max(f(i - 1, j), f(i, j - 1))
```

Base cases: `f(0, j) = 0` for any j (LCS with an empty string is 0). Same for `f(i, 0) = 0`.

That's the recurrence. Let me verify on `s = "abcde"`, `t = "ace"`.

----------------------------------------

## Step 4: Build the Table

Let me fill `f` for `s = "abcde"` (rows, i from 0 to 5) and `t = "ace"` (columns, j from 0 to 3).

```
       ""  a  c  e
""     0   0  0  0
a      0   ?  ?  ?
ab     0   ?  ?  ?
abc    0   ?  ?  ?
abcd   0   ?  ?  ?
abcde  0   ?  ?  ?
```

**f(1, 1):** `s[0] = 'a'`, `t[0] = 'a'`. Match. `f(1, 1) = 1 + f(0, 0) = 1`.
**f(1, 2):** `s[0] = 'a'`, `t[1] = 'c'`. No match. `f(1, 2) = max(f(0, 2), f(1, 1)) = max(0, 1) = 1`.
**f(1, 3):** `s[0] = 'a'`, `t[2] = 'e'`. No match. `f(1, 3) = max(f(0, 3), f(1, 2)) = max(0, 1) = 1`.

**f(2, 1):** `s[1] = 'b'`, `t[0] = 'a'`. No match. `max(f(1, 1), f(2, 0)) = max(1, 0) = 1`.
**f(2, 2):** `s[1] = 'b'`, `t[1] = 'c'`. No match. `max(f(1, 2), f(2, 1)) = max(1, 1) = 1`.
**f(2, 3):** `s[1] = 'b'`, `t[2] = 'e'`. No match. `max(f(1, 3), f(2, 2)) = max(1, 1) = 1`.

**f(3, 1):** `s[2] = 'c'`, `t[0] = 'a'`. No match. `max(f(2, 1), f(3, 0)) = max(1, 0) = 1`.
**f(3, 2):** `s[2] = 'c'`, `t[1] = 'c'`. Match! `f(3, 2) = 1 + f(2, 1) = 2`.
**f(3, 3):** `s[2] = 'c'`, `t[2] = 'e'`. No match. `max(f(2, 3), f(3, 2)) = max(1, 2) = 2`.

**f(4, 1):** `s[3] = 'd'`, `t[0] = 'a'`. No match. `max(1, 0) = 1`.
**f(4, 2):** `s[3] = 'd'`, `t[1] = 'c'`. No match. `max(2, 1) = 2`.
**f(4, 3):** `s[3] = 'd'`, `t[2] = 'e'`. No match. `max(2, 2) = 2`.

**f(5, 1):** `s[4] = 'e'`, `t[0] = 'a'`. No match. `max(1, 0) = 1`.
**f(5, 2):** `s[4] = 'e'`, `t[1] = 'c'`. No match. `max(2, 1) = 2`.
**f(5, 3):** `s[4] = 'e'`, `t[2] = 'e'`. Match! `f(5, 3) = 1 + f(4, 2) = 3`.

Final table:

```
       ""  a  c  e
""     0   0  0  0
a      0   1  1  1
ab     0   1  1  1
abc    0   1  2  2
abcd   0   1  2  2
abcde  0   1  2  3
```

Answer is `f(5, 3) = 3`. ✓

----------------------------------------

## Step 5: Why This Recurrence Is Complete

**Claim:** the LCS of `s[0..i-1]` and `t[0..j-1]` is either (a) the LCS of the pair's shorter prefixes extended by a matching last character, or (b) the LCS achievable by dropping the last character of one of the strings.

**Proof sketch:** the last character of the LCS must come from somewhere. If it came from matching `s[i-1]` with `t[j-1]`, we're in case (a). Otherwise the last character of the LCS is not `s[i-1]`, or not `t[j-1]`, or neither. "Not `s[i-1]`" means we could get the same LCS without using `s[i-1]` at all — so LCS is bounded by `f(i-1, j)`. "Not `t[j-1]`" gives `f(i, j-1)`. We pick the best.

Does case (a) ever miss a valid answer when characters don't match? No — if characters don't match, the LCS definitely doesn't end with both of them simultaneously, so (a) is inapplicable. Case (b) covers everything.

----------------------------------------

## Step 6: Name the Pattern

This is the classic **2D DP on two sequences**. The same "think about the last character" trick solves Edit Distance, Distinct Subsequences, Interleaving String, and Shortest Common Supersequence. They all have the `(i, j)` state and transitions that depend on `s[i-1] vs t[j-1]`.

Once you internalize this shape, many interview-style string problems collapse to the same structure.

----------------------------------------

## Step 7: Complexity

Time: we fill an `(n+1) × (m+1)` table with O(1) work per cell. **O(n · m)**.

Space: full table is **O(n · m)**. But each row only depends on the previous row — so we can keep just two rows (or even one, with careful update ordering) for **O(min(n, m))** space.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int longestCommonSubsequence(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<int>> dp(n + 1, vector<int>(m + 1, 0));
    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            if (s[i-1] == t[j-1]) dp[i][j] = 1 + dp[i-1][j-1];
            else dp[i][j] = max(dp[i-1][j], dp[i][j-1]);
        }
    }
    return dp[n][m];
}
```

Iterating `i` then `j` ensures dependencies (`dp[i-1][j-1]`, `dp[i-1][j]`, `dp[i][j-1]`) are all computed before we need them.

----------------------------------------

## Step 9: Follow-up Questions

- **Return the actual LCS string, not just the length.** Trace back through the table from `(n, m)` to `(0, 0)`, picking characters when we entered via the match case.
- **LCS of three strings.** 3D DP on `(i, j, k)` with similar case analysis. O(n · m · p).
- **Longest Common Substring (not subsequence — must be contiguous).** Different recurrence: reset to 0 when characters don't match.
- **Longest Palindromic Subsequence.** Equivalent to LCS of `s` and `reverse(s)`.
- **LCS when strings are huge but differ in only a few spots.** Hunt-Szymanski algorithm gives better performance when characters are largely distinct.
- **Space-optimize to O(min(n, m)).** Maintain just the previous row and current row, carefully handling the diagonal dependency.
