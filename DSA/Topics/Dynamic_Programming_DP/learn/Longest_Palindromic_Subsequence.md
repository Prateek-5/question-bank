# Longest Palindromic Subsequence — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Longest_Palindromic_Subsequence.md`](../Longest_Palindromic_Subsequence.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/longest-palindromic-subsequence/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/longest-palindromic-subsequence/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: INTERVAL DP. `dp[i][j]` = longest palindromic subseq in s[i..j]. Case-split on whether endpoints match. SHORTCUT: this equals `LCS(s, reverse(s))`.**

**Map of this file (8 sections):**

1. Read the problem
2. The palindrome structure
3. Interval DP recurrence
4. The LCS-with-reverse shortcut
5. Code (both versions)
6. Trace it
7. Common pitfalls
8. The shape — interval DP

---

## 1. Read the problem

Given string `s`, find the length of the LONGEST palindromic SUBSEQUENCE (NOT substring — characters need not be contiguous).

**Examples:**

- `s = "bbbab"` → `"bbbb"` (pick indices 0,1,2,4) → **4**.
- `s = "cbbd"` → `"bb"` → **2**.

---

## 2. The palindrome structure

> **Mini-refresher: a palindrome reads the same forward and backward.**
>
> Key structural fact: the FIRST and LAST chars are equal. Everything between is itself a palindrome.
>
> So we can think recursively about `s[i..j]`: do the endpoints match? If so, we can pair them up and recurse on `s[i+1..j-1]`.

---

## 3. Interval DP recurrence

> **Mini-refresher: state = range `[i, j]`.**
>
> Let `dp[i][j]` = longest palindromic subsequence of `s[i..j]`.
>
> - Base: `dp[i][i] = 1` (single char).
> - If `s[i] == s[j]`: `dp[i][j] = 2 + dp[i+1][j-1]` (pair them, recurse inside). When `j = i+1`, `dp[i+1][j-1]` is empty range → 0, giving `dp[i][j] = 2`.
> - Else: `dp[i][j] = max(dp[i+1][j], dp[i][j-1])` (drop one endpoint).
>
> Answer: `dp[0][n-1]`.

**Fill order:** by increasing range length, or equivalently `i` from n-1 down to 0 and `j` from i+1 up to n-1.

---

## 4. The LCS-with-reverse shortcut

> **Mini-refresher: longest palindromic subseq of s = LCS(s, reverse(s)).**
>
> Any palindromic subsequence of s reads the same forward and backward — so it appears in BOTH s and reverse(s) (as the same characters). Conversely, any common subsequence of s and reverse(s) corresponds to a palindromic structure.
>
> So you can REUSE your LCS code: `lcs(s, reverse(s))` gives the answer.

Both approaches are O(n²); use whichever you prefer.

---

## 5. Code (both versions)

**C++ — interval DP:**

```cpp
int longestPalindromeSubseq(string s) {
    int n = s.size();
    vector<vector<int>> dp(n, vector<int>(n, 0));
    for (int i = 0; i < n; ++i) dp[i][i] = 1;
    for (int i = n - 1; i >= 0; --i) {
        for (int j = i + 1; j < n; ++j) {
            if (s[i] == s[j]) {
                dp[i][j] = 2 + (i + 1 <= j - 1 ? dp[i+1][j-1] : 0);
            } else {
                dp[i][j] = max(dp[i+1][j], dp[i][j-1]);
            }
        }
    }
    return dp[0][n-1];
}
```

**C++ — via LCS of s and reverse:**

```cpp
int longestPalindromeSubseq(string s) {
    string t(s.rbegin(), s.rend());
    int n = s.size();
    vector<vector<int>> dp(n + 1, vector<int>(n + 1, 0));
    for (int i = 1; i <= n; ++i)
        for (int j = 1; j <= n; ++j)
            dp[i][j] = (s[i-1] == t[j-1]) ? 1 + dp[i-1][j-1] : max(dp[i-1][j], dp[i][j-1]);
    return dp[n][n];
}
```

Complexity: **O(n²)** time, **O(n²)** space. Both versions have the same asymptotic profile.

---

## 6. Trace it

`s = "bbbab"`. Filling `dp[i][j]` by increasing range:

- Length 1: dp[i][i] = 1 for all i.
- Length 2:
  - (0,1): 'b','b' match → 2 + 0 = 2.
  - (1,2): match → 2.
  - (2,3): 'b','a' → max(1, 1) = 1.
  - (3,4): 'a','b' → max(1, 1) = 1.
- Length 3:
  - (0,2): 'b','b' match → 2 + dp[1][1] = 3.
  - (1,3): 'b','a' → max(dp[2][3], dp[1][2]) = max(1, 2) = 2.
  - (2,4): 'b','b' match → 2 + dp[3][3] = 3.
- Length 4:
  - (0,3): 'b','a' → max(dp[1][3], dp[0][2]) = max(2, 3) = 3.
  - (1,4): 'b','b' match → 2 + dp[2][3] = 2 + 1 = 3.
- Length 5:
  - (0,4): 'b','b' match → 2 + dp[1][3] = 2 + 2 = **4**.  ✓

---

## 7. Common pitfalls

1. **Wrong fill order.** `dp[i][j]` depends on `dp[i+1][j-1]`, `dp[i+1][j]`, `dp[i][j-1]` — all SMALLER ranges. Iterate by range length, or i from n-1 down + j from i+1 up.
2. **Missing the length-2 base case.** When `j = i+1` and chars match, `dp[i+1][j-1]` is `dp[i+1][i]` — empty range, should be 0. Guard with `(i+1 <= j-1 ? dp[i+1][j-1] : 0)`.
3. **Confusing subsequence with substring.** "Substring" requires contiguous; different problem (use expand-around-center or Manacher's).
4. **Trying to enumerate all palindromic subsequences.** Exponential — DP avoids that.
5. **Returning `dp[0][n]` instead of `dp[0][n-1]`.** Indices are inclusive.

---

## 8. The shape — interval DP

The pattern: **`dp[i][j]` over a RANGE; recurrence shrinks the range by 1-2 indices.**

| Problem | Recurrence on [i, j] |
|---|---|
| **This problem** | match endpoints → +2 inside; else drop one endpoint |
| Matrix Chain Multiplication | min over split point k |
| Burst Balloons | "last balloon burst in range" trick |
| Palindrome Partitioning II | split into palindrome blocks |
| Minimum Cost to Cut a Stick | split at any cut |
| Strange Printer | merge adjacent equal chars |

**Pattern to internalize:**

> "Range-based questions over a 1D sequence: state = `dp[i][j]`. Recurrence shrinks one or both endpoints OR splits at an interior index. Fill by increasing range length."

---

> **Self-check — the question to ask next time.**
>
> When the question is over a contiguous range of a sequence, ask:
>
> > **"State `dp[i][j]`. Endpoint match? Endpoint dropping? Interior split? Fill by increasing range length."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Longest_Palindromic_Subsequence.md`](../Longest_Palindromic_Subsequence.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Longest_Common_Subsequence.md`](./Longest_Common_Subsequence.md).
  - Coming next: [`Edit_Distance.md`](./Edit_Distance.md), [`Distinct_Subsequences.md`](./Distinct_Subsequences.md), [`Decode_Ways.md`](./Decode_Ways.md).
