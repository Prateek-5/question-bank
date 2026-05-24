# Interleaving String — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Interleaving_String.md`](../Interleaving_String.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/interleaving-string/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: 2D DP on (i, j) = pointers into s1 and s2. The index into s3 is implicit: k = i + j. Each cell: came from s1's last char OR from s2's last char.**

**Map of this file (8 sections):**

1. Read the problem
2. The length pre-check
3. The 2D state — and why we don't need k
4. The recurrence
5. Code
6. Trace it
7. Common pitfalls
8. The shape — 2D DP on two strings

---

## 1. Read the problem

Given strings `s1, s2, s3`, return true iff `s3` can be formed by INTERLEAVING `s1` and `s2` (preserving each one's internal order, mixed freely).

**Example:** `s1 = "aab", s2 = "axy", s3 = "aaxaby"` → **true** (one valid interleave: a₁, a₁, x₂, a₁, b₁, y₂ — using s1 chars marked ₁, s2 marked ₂).

---

## 2. The length pre-check

> **Mini-refresher: |s1| + |s2| must equal |s3|.**
>
> If not, no interleaving exists — return false immediately.

After this guard, assume the lengths line up.

---

## 3. The 2D state — and why we don't need k

> **Mini-refresher: state = (i, j) only.**
>
> `dp[i][j]` = can `s3[0..i+j)` be formed from `s1[0..i)` and `s2[0..j)`?
>
> The position in s3 is determined: `k = i + j`. No third dimension needed.

This is a beautiful collapse — a 3D-feeling problem reduces to 2D because the index into s3 is fully determined by the others.

---

## 4. The recurrence

`dp[i][j]` is true iff EITHER:
- **Last char came from s1:** `s1[i-1] == s3[i+j-1]` AND `dp[i-1][j]`.
- **Last char came from s2:** `s2[j-1] == s3[i+j-1]` AND `dp[i][j-1]`.

Base: `dp[0][0] = true`. For i = 0, only s2 contributes; for j = 0, only s1.

---

## 5. Code

**C++:**

```cpp
bool isInterleave(string s1, string s2, string s3) {
    int n = s1.size(), m = s2.size();
    if (n + m != (int)s3.size()) return false;
    vector<vector<bool>> dp(n + 1, vector<bool>(m + 1, false));
    dp[0][0] = true;
    for (int i = 0; i <= n; ++i) {
        for (int j = 0; j <= m; ++j) {
            if (i == 0 && j == 0) continue;
            bool fromS1 = i > 0 && dp[i-1][j] && s1[i-1] == s3[i+j-1];
            bool fromS2 = j > 0 && dp[i][j-1] && s2[j-1] == s3[i+j-1];
            dp[i][j] = fromS1 || fromS2;
        }
    }
    return dp[n][m];
}
```

Complexity: **O(n · m)** time, **O(n · m)** space (reducible to O(min(n, m))).

---

## 6. Trace it

`s1 = "aab", s2 = "axy", s3 = "aaxaby"`. n = m = 3.

Key cells (computing left-to-right, top-to-bottom):

- (1, 0): s1[0]='a' == s3[0]='a', dp[0][0]=T → T.
- (0, 1): s2[0]='a' == s3[0]='a', dp[0][0]=T → T.
- (1, 1): from s1 (s1[0]='a' vs s3[1]='a', dp[0][1]=T) OR from s2 (s2[0]='a' vs s3[1]='a', dp[1][0]=T) → T.
- (1, 2): from s2 (s2[1]='x' vs s3[2]='x', dp[1][1]=T) → T.
- (2, 2): from s1 (s1[1]='a' vs s3[3]='a', dp[1][2]=T) → T.
- (3, 2): from s1 (s1[2]='b' vs s3[4]='b', dp[2][2]=T) → T.
- (3, 3): from s2 (s2[2]='y' vs s3[5]='y', dp[3][2]=T) → T.

dp[3][3] = **true**.  ✓

---

## 7. Common pitfalls

1. **Adding a third dimension k.** k = i + j is implicit — don't waste memory.
2. **Off-by-one with s3 indexing.** `s3[i+j-1]` is the LAST char of the s3 prefix of length i+j.
3. **OR-ing without checking the prerequisite.** Need both `dp[i-1][j]` AND char match for the s1 branch; same for s2.
4. **Forgetting length pre-check.** Some inputs trivially fail; early return.
5. **Setting `dp[i][0] = true` always for first column.** Only true if `s3[0..i)` matches `s1[0..i)` — not unconditional. The general recurrence handles it correctly when we OR from s1 only (j=0 → fromS2 = false).

---

## 8. The shape — 2D DP on two strings

The pattern: **two source strings + one target, 2D DP indexed by their consumed lengths.**

| Problem | Combining rule |
|---|---|
| **This problem** | OR over "last from s1" / "last from s2" |
| LCS | match → +1, else max |
| Edit Distance | match → no cost, else 1 + min |
| Distinct Subsequences | sum: skip vs use |
| Wildcard / Regex Matching | OR with pattern-specific cases |

**Pattern to internalize:**

> "Two-source DP: condition on which source contributed the LAST char. Each branch contributes if both the char matches AND the predecessor is true."

---

> **Self-check — the question to ask next time.**
>
> When mixing two sequences to form a third, ask:
>
> > **"State (i, j) — position in each source. The third index is implicit (i+j). Each cell: from s1 last? from s2 last? OR them."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Interleaving_String.md`](../Interleaving_String.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Longest_Common_Subsequence.md`](./Longest_Common_Subsequence.md), [`Edit_Distance.md`](./Edit_Distance.md), [`Distinct_Subsequences.md`](./Distinct_Subsequences.md).
  - Coming next: [`Regular_Expression_Matching.md`](./Regular_Expression_Matching.md), [`Frog_Jump.md`](./Frog_Jump.md).
