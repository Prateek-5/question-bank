# Distinct Subsequences — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Distinct_Subsequences.md`](../Distinct_Subsequences.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/distinct-subsequences/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/distinct-subsequences/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: COUNT — not max/min — distinct ways to form t as a subsequence of s. 2D DP on prefixes. `f(i, j) = f(i-1, j) + (f(i-1, j-1) if s[i-1] == t[j-1])`. The recurrence SUMS the "use s[i-1]" and "skip s[i-1]" cases.**

**Map of this file (9 sections):**

1. Read the problem
2. Same vs different subsequences
3. The DP state and recurrence
4. Why "+" instead of max
5. Code (2D + 1D rolling)
6. Trace it
7. Overflow guard
8. Common pitfalls
9. The shape — counting DP on two strings

---

## 1. Read the problem

Given strings `s` and `t`, return the number of DISTINCT subsequences of s that equal t.

A subsequence keeps order but can skip chars. Two subsequences are "distinct" if their INDEX SELECTIONS in s differ — even if the resulting strings are the same.

**Example:** `s = "rabbbit", t = "rabbit"` → **3** ways (3 different middle-b choices).

---

## 2. Same vs different subsequences

> **Mini-refresher: distinctness is by INDEX SELECTION, not by resulting string.**
>
> Picking `{0, 1, 2, 3, 5, 6}` and `{0, 1, 2, 4, 5, 6}` from "rabbbit" both yield "rabbit." They count as TWO distinct subsequences.

---

## 3. The DP state and recurrence

> **Mini-refresher: condition on whether the last char of s is USED.**
>
> Let `f(i, j)` = number of distinct subsequences of `s[0..i)` that equal `t[0..j)`.
>
> - **Skip `s[i-1]`:** Match `t[0..j)` using only `s[0..i-1)` → `f(i-1, j)` ways.
> - **Use `s[i-1]` as `t[j-1]`** (only valid if `s[i-1] == t[j-1]`): then match `t[0..j-1)` with `s[0..i-1)` → `f(i-1, j-1)` ways.
>
> SUM both:
>
> ```
> f(i, j) = f(i-1, j) + (f(i-1, j-1) if s[i-1] == t[j-1] else 0)
> ```
>
> **Base:** `f(i, 0) = 1` for all i (one way to "match" the empty string — pick nothing). `f(0, j) = 0` for j > 0 (can't form non-empty t from empty s).

---

## 4. Why "+" instead of max

LCS / Edit Distance OPTIMIZE (max/min). This problem COUNTS. Each distinct way is counted ONCE, and the two cases ("skip" vs "use") are MUTUALLY EXCLUSIVE — so we SUM, not take max.

---

## 5. Code (2D + 1D rolling)

**C++ — 2D:**

```cpp
int numDistinct(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<unsigned long long>> f(n + 1, vector<unsigned long long>(m + 1, 0));
    for (int i = 0; i <= n; ++i) f[i][0] = 1;

    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            f[i][j] = f[i-1][j];
            if (s[i-1] == t[j-1]) f[i][j] += f[i-1][j-1];
        }
    }
    return (int)f[n][m];
}
```

**C++ — 1D rolling (iterate j right-to-left):**

```cpp
int numDistinct(string s, string t) {
    int n = s.size(), m = t.size();
    vector<unsigned long long> f(m + 1, 0);
    f[0] = 1;
    for (int i = 1; i <= n; ++i) {
        for (int j = m; j >= 1; --j) {
            if (s[i-1] == t[j-1]) f[j] += f[j-1];
            // else f[j] stays the same (equivalent to f[j] = f[j])
        }
    }
    return (int)f[m];
}
```

Right-to-left iteration in the inner loop preserves `f[j-1]` as the previous row's value when we read it.

Complexity: **O(n · m)** time. Space **O(n · m)** or **O(m)**.

---

## 6. Trace it

`s = "aaa", t = "aa"` (expect 3).

```
f[0] = [1, 0, 0]   (empty s row)

Row i=1 (s[0]='a'):
  j=1: s[0]==t[0] → f[1][1] = f[0][1] + f[0][0] = 0 + 1 = 1.
  j=2: s[0]==t[1] → f[1][2] = f[0][2] + f[0][1] = 0 + 0 = 0.
  f[1] = [1, 1, 0].

Row i=2 (s[1]='a'):
  j=1: match → f[2][1] = f[1][1] + f[1][0] = 1 + 1 = 2.
  j=2: match → f[2][2] = f[1][2] + f[1][1] = 0 + 1 = 1.
  f[2] = [1, 2, 1].

Row i=3 (s[2]='a'):
  j=1: match → f[3][1] = f[2][1] + f[2][0] = 2 + 1 = 3.
  j=2: match → f[3][2] = f[2][2] + f[2][1] = 1 + 2 = 3.

f[3][2] = 3.  ✓
```

---

## 7. Overflow guard

> **Mini-refresher: counts can grow LARGE.**
>
> For long s and short t, the count can exceed 2^31. The problem typically guarantees the FINAL answer fits in int32, but intermediate cells might not. Use `unsigned long long` (or Python's bignum) to be safe.

---

## 8. Common pitfalls

1. **Wrong base case.** `f[i][0] = 1` (one way to form empty t). Forgetting this gives all zeros.
2. **`max` instead of `+`.** This is COUNTING, not optimizing.
3. **Left-to-right rolling in 1D.** Overwrites `f[j-1]` before you need it. Iterate j RIGHT-TO-LEFT.
4. **Forgetting the "skip s[i-1]" case.** The recurrence has TWO branches; the skip is unconditional.
5. **Off-by-one on the match check.** `s[i-1] == t[j-1]`, NOT `s[i] == t[j]`.
6. **Counting empty subsequences as 0.** Empty t is matchable in EXACTLY ONE way (pick nothing).

---

## 9. The shape — counting DP on two strings

The pattern: **same 2D DP shape as LCS/Edit Distance, but the OPERATOR is `+` (counting), not max/min.**

| Problem | Aggregator |
|---|---|
| LCS | max (length) |
| Edit Distance | min (cost) |
| **This problem** | + (count) |
| Wildcard / Regex Matching | OR (boolean) |
| Interleaving String | OR (boolean) |
| Shortest Common Supersequence | derived from LCS |

**Pattern to internalize:**

> "Two-string DP with COUNTING aggregator: `f(i, j) = f(i-1, j) [skip s[i-1]] + (f(i-1, j-1) if match) [use s[i-1] as t[j-1]]`. Right-to-left 1D rolling for O(m) space."

---

> **Self-check — the question to ask next time.**
>
> When the question is "count distinct ways to form t as a subsequence of s":
>
> > **"`f(i, j) = f(i-1, j) + (f(i-1, j-1) if match)`. The two cases are SKIP s[i-1] vs USE it. Sum, don't max."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Distinct_Subsequences.md`](../Distinct_Subsequences.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Longest_Common_Subsequence.md`](./Longest_Common_Subsequence.md), [`Edit_Distance.md`](./Edit_Distance.md).
  - Coming next: [`Decode_Ways.md`](./Decode_Ways.md), [`Interleaving_String.md`](./Interleaving_String.md), [`Regular_Expression_Matching.md`](./Regular_Expression_Matching.md).
