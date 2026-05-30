# Edit Distance — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Edit_Distance.md`](../Edit_Distance.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/edit-distance/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/edit-distance/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: 2D DP on prefixes. THE Levenshtein recurrence: if chars match, no edit needed → `dp[i-1][j-1]`. Else `1 + min(insert, delete, replace)` = `1 + min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1])`.**

**Map of this file (9 sections):**

1. Read the problem
2. The three operations
3. State + recurrence
4. Why three cases cover everything
5. Code
6. Trace it
7. Recovering the actual edits
8. Common pitfalls
9. The shape — Wagner-Fischer

---

## 1. Read the problem

Given two strings `s` and `t`, return the MINIMUM number of single-character edits (INSERT, DELETE, REPLACE) needed to convert `s` into `t`.

**Example:** `s = "horse", t = "ros"` → **3**:
1. horse → rorse (replace 'h' → 'r').
2. rorse → rose (delete 'r').
3. rose → ros (delete 'e').

---

## 2. The three operations

> **Mini-refresher: three operations, one cost each.**
>
> - **Insert** a char into s: bring s closer to t.
> - **Delete** a char from s: shrink s.
> - **Replace** a char in s with another.
>
> Each operation costs 1. Order doesn't affect minimum count.

---

## 3. State + recurrence

> **Mini-refresher: state = (prefix length of s, prefix length of t).**
>
> Let `dp[i][j]` = min edits to convert `s[0..i-1]` into `t[0..j-1]`.
>
> **Base:** `dp[0][j] = j` (empty s → t: j inserts). `dp[i][0] = i` (s → empty: i deletes).
>
> **Recurrence:**
> - If `s[i-1] == t[j-1]`: last chars match, no edit needed → `dp[i][j] = dp[i-1][j-1]`.
> - Else: take the best of three:
>   - Replace `s[i-1]` with `t[j-1]`: `1 + dp[i-1][j-1]`.
>   - Delete `s[i-1]`: `1 + dp[i-1][j]`.
>   - Insert `t[j-1]` at the end of s: `1 + dp[i][j-1]`.
>
> `dp[i][j] = min(those three) + 1`.

Answer: `dp[n][m]`.

---

## 4. Why three cases cover everything

Any edit sequence transforms s into t. Look at the LAST step:

- The LAST char of t (i.e., `t[j-1]`) was achieved by either:
  - It matched `s[i-1]` directly (match case).
  - It came from REPLACING `s[i-1]`.
  - It came from INSERTING into s.
- OR: `s[i-1]` was DELETED (so the last char of t came from elsewhere).

Those four cases collapse to three when chars match (no edit on last position) or three operations when they don't.

---

## 5. Code

**C++:**

```cpp
int minDistance(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<int>> dp(n + 1, vector<int>(m + 1, 0));
    for (int i = 0; i <= n; ++i) dp[i][0] = i;
    for (int j = 0; j <= m; ++j) dp[0][j] = j;
    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            if (s[i-1] == t[j-1]) dp[i][j] = dp[i-1][j-1];
            else dp[i][j] = 1 + min({dp[i-1][j-1], dp[i-1][j], dp[i][j-1]});
        }
    }
    return dp[n][m];
}
```

**Python:**

```python
def minDistance(s, t):
    n, m = len(s), len(t)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): dp[i][0] = i
    for j in range(m + 1): dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s[i-1] == t[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j-1], dp[i-1][j], dp[i][j-1])
    return dp[n][m]
```

Complexity: **O(n · m)** time, **O(n · m)** space (reducible to **O(min(n, m))**).

---

## 6. Trace it

`s = "horse", t = "ros"`. Build dp (rows = prefixes of s, cols = prefixes of t):

```
       ""  r  o  s
""      0  1  2  3
h       1  1  2  3
ho      2  2  1  2
hor     3  2  2  2
hors    4  3  3  2
horse   5  4  4  3
```

Key cells:
- (1,1) 'h' vs 'r': mismatch → 1 + min(0,1,1) = 1.
- (2,2) 'o' vs 'o': match → dp[1][1] = 1.
- (3,1) 'r' vs 'r': match → dp[2][0] = 2.
- (4,3) 's' vs 's': match → dp[3][2] = 2.
- (5,3): mismatch → 1 + min(dp[4][2], dp[4][3], dp[5][2]) = 1 + min(3, 2, 4) = **3**.  ✓

---

## 7. Recovering the actual edits

Walk back from `dp[n][m]`:
- If match: i--, j--.
- Else, find which of the three (replace/delete/insert) produced the cell, take that step.

Requires the full DP table; can't recover with O(n) space.

---

## 8. Common pitfalls

1. **Forgetting base cases.** `dp[i][0] = i`, `dp[0][j] = j`. Without these, the DP gives wrong answers for strings with empty prefixes.
2. **Mixing up insert/delete directions.** Insert into s adds a char (uses `dp[i][j-1]`); delete removes (uses `dp[i-1][j]`). Don't swap them — though for unweighted edit distance it gives the same answer numerically.
3. **Off-by-one with prefix lengths.** `s[i-1]` not `s[i]` when looking at the i-th prefix.
4. **Trying to enumerate all edit sequences.** Exponential.
5. **Replace cost = 2 (= 1 delete + 1 insert).** In standard Levenshtein, replace is ONE operation. If your variant says replace = 2, drop that term and use only insert/delete.

---

## 9. The shape — Wagner-Fischer

The pattern: **string-to-string transformation via 2D DP on prefixes.**

| Problem | Match action | Mismatch action |
|---|---|---|
| **Edit Distance** | dp[i-1][j-1] | 1 + min(insert, delete, replace) |
| LCS | 1 + dp[i-1][j-1] | max(dp[i-1][j], dp[i][j-1]) |
| Distinct Subsequences | sum cases | dp[i-1][j] |
| Wildcard Matching | dp[i-1][j-1] | * cases |
| Interleaving String | combine 3 dims | combine 3 dims |
| Shortest Common Supersequence | derived | derived |

**Pattern to internalize:**

> "Two-string transformation problems → 2D DP, state (prefix lengths), case-split on s[i-1] vs t[j-1]. Wagner-Fischer is the canonical edit-distance instance."

---

> **Self-check — the question to ask next time.**
>
> When transforming one string into another via local edits:
>
> > **"State (i, j). Match → no cost, recurse on (i-1, j-1). Mismatch → 1 + min(three predecessors). O(n·m)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Edit_Distance.md`](../Edit_Distance.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Longest_Common_Subsequence.md`](./Longest_Common_Subsequence.md), [`Longest_Palindromic_Subsequence.md`](./Longest_Palindromic_Subsequence.md).
  - Coming next: [`Distinct_Subsequences.md`](./Distinct_Subsequences.md), [`Decode_Ways.md`](./Decode_Ways.md).
