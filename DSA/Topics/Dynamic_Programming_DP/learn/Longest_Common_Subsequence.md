# Longest Common Subsequence — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Longest_Common_Subsequence.md`](../Longest_Common_Subsequence.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/longest-common-subsequence/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/longest-common-subsequence/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: 2D DP on two strings. State = prefix lengths (i, j). Case-split on whether the LAST characters match. If yes: `dp[i][j] = 1 + dp[i-1][j-1]`. If no: `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`. THE template for two-string DP.**

**Map of this file (9 sections):**

1. Read the problem
2. The "match the last char?" reframe
3. The recurrence
4. Code
5. Trace it
6. Why this covers everything
7. Recovering the actual LCS
8. Common pitfalls
9. The shape — 2D string DP

---

## 1. Read the problem

Given two strings `s` and `t`, return the length of their LONGEST COMMON SUBSEQUENCE (LCS) — a sequence appearing in both, in order, but not necessarily contiguous.

**Example:** `s = "abcde", t = "ace"` → LCS `"ace"` → **3**.

---

## 2. The "match the last char?" reframe

> **Mini-refresher: condition on the LAST character of each prefix.**
>
> Define `dp[i][j]` = LCS length of `s[0..i-1]` and `t[0..j-1]` (the first i chars of s and first j of t).
>
> Case-split on whether `s[i-1] == t[j-1]`:
> - **Match:** the LCS can END with this common character. Take it, then recurse on smaller prefixes: `dp[i][j] = 1 + dp[i-1][j-1]`.
> - **No match:** the last chars don't both belong to the LCS. The LCS comes from either dropping `s[i-1]` or dropping `t[j-1]`: `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`.

---

## 3. The recurrence

```
dp[0][j] = 0  for all j   (LCS with empty prefix = 0)
dp[i][0] = 0  for all i

if s[i-1] == t[j-1]:
    dp[i][j] = 1 + dp[i-1][j-1]
else:
    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```

Answer: `dp[n][m]`.

---

## 4. Code

**C++:**

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

**Python:**

```python
def longestCommonSubsequence(s, t):
    n, m = len(s), len(t)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s[i-1] == t[j-1]:
                dp[i][j] = 1 + dp[i-1][j-1]
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[n][m]
```

Complexity: **O(n · m)** time, **O(n · m)** space (reducible to **O(min(n, m))** with rolling rows).

---

## 5. Trace it

`s = "abcde", t = "ace"`. Build dp:

```
     ""  a  c  e
""    0  0  0  0
a     0  1  1  1
ab    0  1  1  1
abc   0  1  2  2
abcd  0  1  2  2
abcde 0  1  2  3
```

dp[5][3] = **3**.

Key matches:
- (1,1): 'a'='a' → 1 + dp[0][0] = 1.
- (3,2): 'c'='c' → 1 + dp[2][1] = 2.
- (5,3): 'e'='e' → 1 + dp[4][2] = 3.

Other cells take max of "drop s last" vs "drop t last."

---

## 6. Why this covers everything

> **Mini-refresher: every LCS has a definite "last character" status.**
>
> For each pair of prefixes `s[..i]`, `t[..j]`, ask: does the optimal LCS use the chars `s[i-1]` and `t[j-1]` simultaneously?
>
> - YES (only possible if they're equal) → match case.
> - NO → at least one of them is unused; drop that one and recurse.
>
> These cases are EXHAUSTIVE. The recurrence captures every valid LCS.

---

## 7. Recovering the actual LCS

Walk back through dp from (n, m):

```python
i, j = n, m
out = []
while i > 0 and j > 0:
    if s[i-1] == t[j-1]:
        out.append(s[i-1])
        i -= 1; j -= 1
    elif dp[i-1][j] > dp[i][j-1]:
        i -= 1
    else:
        j -= 1
out.reverse()
```

Need the full table; can't recover with O(min(n,m)) space alone.

---

## 8. Common pitfalls

1. **Off-by-one on string indices.** `dp[i][j]` uses prefixes of length i and j. Refer to `s[i-1]`, NOT `s[i]`.
2. **Forgetting `dp[i][0] = dp[0][j] = 0`.** The default zero-init handles it, but be explicit if unsure.
3. **Returning `dp[n-1][m-1]`.** Answer is `dp[n][m]` (table is sized `(n+1) × (m+1)`).
4. **Trying brute-force enumeration.** 2^n subsequences → exponential. DP is essential.
5. **Using LCS for "longest common SUBSTRING."** Different recurrence — substring requires contiguous; reset to 0 on mismatch.

---

## 9. The shape — 2D string DP

The pattern: **two strings → 2D DP on (i, j) prefix lengths; case-split on last chars.**

| Problem | Match action | Mismatch action |
|---|---|---|
| **LCS** | 1 + dp[i-1][j-1] | max(dp[i-1][j], dp[i][j-1]) |
| Edit Distance | dp[i-1][j-1] | 1 + min(insert, delete, replace) |
| Distinct Subsequences | dp[i-1][j-1] + dp[i-1][j] | dp[i-1][j] |
| Wildcard Matching | dp[i-1][j-1] | * cases |
| Longest Palindromic Subseq | LCS(s, reverse(s)) | (reduces to LCS) |
| Shortest Common Supersequence | derived from LCS | derived from LCS |

**Pattern to internalize:**

> "Two strings + 'common/edit/match' question = 2D DP, prefix-length state, case-split on s[i-1] vs t[j-1]. The 'last character' reframe is the key move."

---

> **Self-check — the question to ask next time.**
>
> When the problem involves two sequences and a "common/distance/match" objective:
>
> > **"State = (prefix length of s, prefix length of t). Case-split on whether s[i-1] equals t[j-1]. The recurrence writes itself."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Longest_Common_Subsequence.md`](../Longest_Common_Subsequence.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Longest_Increasing_Subsequence.md`](./Longest_Increasing_Subsequence.md), [`Maximum_Height_by_Stacking_Cuboids.md`](./Maximum_Height_by_Stacking_Cuboids.md).
  - Coming next: [`Longest_Palindromic_Subsequence.md`](./Longest_Palindromic_Subsequence.md), [`Edit_Distance.md`](./Edit_Distance.md), [`Distinct_Subsequences.md`](./Distinct_Subsequences.md).
