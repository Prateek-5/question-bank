# Longest Palindromic Subsequence

**Problem Link:**
https://leetcode.com/problems/longest-palindromic-subsequence/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Clarify Palindrome vs Subsequence

A **palindrome** reads the same forward and backward: `"aba"`, `"racecar"`, `"a"`.

A **subsequence** is what you get by deleting zero or more characters while preserving order (but not necessarily contiguously).

Put together: a **palindromic subsequence** is any subsequence of the input that happens to read as a palindrome.

Problem: given a string `s`, return the **length** of the longest palindromic subsequence.

Example: `s = "bbbab"`. Candidates:
- `"bbb"` — length 3, palindrome. ✓
- `"bab"` — length 3, palindrome. ✓
- `"bbbb"` — pick the 4 b's (indices 0, 1, 2, 4). That's length 4 and a palindrome.
- Length 5 would be the whole string — but `"bbbab"` isn't a palindrome.

Answer: **4**.

`s = "cbbd"`. Candidates: `"bb"` is length 2. Answer: **2**.

----------------------------------------

## Step 2: Try to Attack Small Cases

`s = "a"`. Only subsequence: `"a"`, length 1. Answer: 1.

`s = "ab"`. Palindromes: `"a"`, `"b"`. Max length 1.

`s = "aba"`. Palindromes: `"a"`, `"b"`, `"aba"`. Max 3.

`s = "abba"`. Palindromes include `"abba"` itself. Length 4.

`s = "abcd"`. Every character alone is a palindrome. No 2-length palindromic subsequence. Answer: 1.

So the answer is between 1 (if all characters are distinct) and n (if the string itself is a palindrome).

----------------------------------------

## Step 3: What Makes a Palindrome Tick?

A palindrome's defining feature: its first character equals its last. And whatever's in between is also a palindrome.

If we denote the longest palindromic subsequence of `s[i..j]` (inclusive) by `f(i, j)`, then consider the two endpoints:

**Case 1: `s[i] == s[j]`.** We can pair them up as the first and last characters of the palindrome. The rest of the palindrome lives inside `s[i+1..j-1]` — and we want the longest palindromic subsequence of *that* sub-range. So:

```
f(i, j) = 2 + f(i + 1, j - 1)
```

**Case 2: `s[i] != s[j]`.** These two endpoints can't both be in the palindromic subsequence's outer positions. At most one of them appears. So we try dropping each:

```
f(i, j) = max(f(i + 1, j), f(i, j - 1))
```

Base cases:
- Single character: `f(i, i) = 1`.
- Empty range `i > j`: `f(i, j) = 0`.

This recurrence is **complete** — it handles every possible case based on whether the endpoints match or not.

----------------------------------------

## Step 4: Verify on "bbbab"

Let me fill the table `f(i, j)` for `s = "bbbab"`, indices 0..4.

I'll work from the diagonal outward (since `f(i, j)` depends on ranges strictly smaller).

Base (length 1): `f(i, i) = 1` for i = 0..4.

Length 2 ranges (i, i+1):
- f(0, 1): s[0]='b', s[1]='b'. Match. `f = 2 + f(1, 0) = 2 + 0 = 2`.
- f(1, 2): 'b', 'b'. `2 + f(2, 1) = 2 + 0 = 2`.
- f(2, 3): 'b', 'a'. No match. `max(f(3, 3), f(2, 2)) = 1`.
- f(3, 4): 'a', 'b'. No match. `max(f(4, 4), f(3, 3)) = 1`.

Length 3 (i, i+2):
- f(0, 2): 'b', 'b'. Match. `2 + f(1, 1) = 3`.
- f(1, 3): 'b', 'a'. No match. `max(f(2, 3), f(1, 2)) = max(1, 2) = 2`.
- f(2, 4): 'b', 'b'. Match. `2 + f(3, 3) = 3`.

Length 4 (i, i+3):
- f(0, 3): 'b', 'a'. No match. `max(f(1, 3), f(0, 2)) = max(2, 3) = 3`.
- f(1, 4): 'b', 'b'. Match. `2 + f(2, 3) = 2 + 1 = 3`.

Length 5 (entire string):
- f(0, 4): 'b', 'b'. Match. `2 + f(1, 3) = 2 + 2 = 4`.

Answer: **4**. ✓ Matches the hand analysis.

----------------------------------------

## Step 5: A Surprising Shortcut

Here's a fun observation: the longest palindromic subsequence of `s` equals the **longest common subsequence** of `s` and `reverse(s)`.

Why? Any palindromic subsequence of `s` reads the same forward and backward. It appears in `s` in its forward form, and in `reverse(s)` in its reverse form — which is the same string since it's a palindrome. So it's a common subsequence of both.

Conversely, any common subsequence of `s` and `reverse(s)` can be shown to correspond to some palindromic subsequence of `s` (with a bit more care).

So if you already have LCS code, you can solve this in one line by calling `LCS(s, reverse(s))`.

I prefer the direct DP above because the recurrence tracks the palindrome's structure, but either works.

----------------------------------------

## Step 6: Implementation Strategy — Fill Order

Because `f(i, j)` depends on `f(i+1, j-1)`, `f(i+1, j)`, and `f(i, j-1)` — all with smaller "range length" — we should iterate by increasing range length. Or equivalently, iterate `i` from `n-1` down to `0` and `j` from `i+1` up to `n-1`. Both orderings ensure dependencies are filled first.

```cpp
for (int i = n - 1; i >= 0; --i)
    for (int j = i + 1; j < n; ++j) {
        if (s[i] == s[j]) dp[i][j] = 2 + (i + 1 <= j - 1 ? dp[i+1][j-1] : 0);
        else dp[i][j] = max(dp[i+1][j], dp[i][j-1]);
    }
```

Small edge case: if `j - i == 1` and chars match, `dp[i+1][j-1]` would be `dp[i+1][i]` which is out of our defined range. We just treat it as 0 (empty range).

----------------------------------------

## Step 7: Name It

This is **interval DP on a string**, where the state is a range `[i, j]` and transitions are based on what happens at the endpoints. The same shape drives Palindrome Partitioning, Matrix Chain Multiplication, and the Burst Balloons problem (in a more complex form).

Calling it "LCS with reverse" highlights another powerful technique: turning a tricky symmetric problem into a well-known one by pairing it with its reverse.

----------------------------------------

## Step 8: Complexity

Time: O(n) ranges of each length, n length values → **O(n²)** cells, each with O(1) work.
Space: **O(n²)** for the table. Can be reduced to **O(n)** with careful row-by-row updating.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int longestPalindromeSubseq(string s) {
    int n = s.size();
    vector<vector<int>> dp(n, vector<int>(n, 0));
    for (int i = 0; i < n; ++i) dp[i][i] = 1;            // single chars
    for (int i = n - 1; i >= 0; --i) {
        for (int j = i + 1; j < n; ++j) {
            if (s[i] == s[j]) {
                dp[i][j] = 2 + (i + 1 <= j - 1 ? dp[i + 1][j - 1] : 0);
            } else {
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1]);
            }
        }
    }
    return dp[0][n - 1];
}
```

Reading the loop direction: we fill i from bottom (n-1) up, and j from i+1 forward. This guarantees `dp[i+1][j-1]`, `dp[i+1][j]`, and `dp[i][j-1]` are all computed before we need them.

----------------------------------------

## Step 10: Follow-up Questions

- **Longest palindromic *substring* (contiguous, not subsequence).** Different recurrence — can be solved in O(n²) with expand-around-center, or O(n) with Manacher's algorithm.
- **Count the number of distinct palindromic subsequences (not just the longest).** Harder DP — handle duplicates carefully.
- **Find the actual longest palindromic subsequence, not just the length.** Trace back through the DP table from (0, n-1), reconstructing characters.
- **Minimum insertions to make `s` a palindrome.** Answer is `n - longestPalindromicSubseq(s)`.
- **Palindromic subsequences of a specific length k.** Different DP — count paths through the interval tree at specific lengths.
