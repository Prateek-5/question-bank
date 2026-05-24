# Regular Expression Matching — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Regular_Expression_Matching.md`](../Regular_Expression_Matching.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/regular-expression-matching/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The lesson: 2D DP. `.` matches any single char. `*` is the hard case: it allows ZERO or MORE of the PRECEDING element. Recurrence: when pattern char is `*`, try "match zero" (skip `x*` pair) OR "match at least one" (consume one s char, stay on the `*`).**

**Map of this file (10 sections):**

1. Read the problem
2. The two metacharacters
3. The DP state
4. Case A — regular char or `.`
5. Case B — `*` (two sub-options)
6. Base case for row 0
7. Code
8. Trace it
9. Common pitfalls
10. The shape — pattern-driven DP

---

## 1. Read the problem

Given string `s` and pattern `p`, return whether `p` matches the ENTIRE `s` under these rules:

- `.` matches any single character.
- `*` matches ZERO OR MORE of the PRECEDING element.

**Examples:**

- `s="aa", p="a"` → false (p only matches one a).
- `s="aa", p="a*"` → true (`a*` matches zero or more a's).
- `s="ab", p=".*"` → true (any sequence).
- `s="aab", p="c*a*b"` → true.
- `s="mississippi", p="mis*is*p*."` → false.

---

## 2. The two metacharacters

> **Mini-refresher: `*` applies to the PRECEDING element.**
>
> `a*` means "zero or more a's." `a*` is a unit — the `*` modifies the `a`.
>
> `.*` means "zero or more of any char" — effectively wildcard for any prefix.

`*` is the hard case because it introduces BRANCHING: should we match 0 occurrences, 1, 2, etc.?

---

## 3. The DP state

> **Mini-refresher: 2D DP on prefix lengths.**
>
> `dp[i][j]` = does `p[0..j)` match `s[0..i)`?
>
> **Base:** `dp[0][0] = true`. Other base cases via the recurrence.
>
> Answer: `dp[n][m]`.

---

## 4. Case A — regular char or `.`

If `p[j-1]` is a literal char or `.`:
- If `p[j-1] == '.'` or `p[j-1] == s[i-1]`: match, recurse on smaller prefixes. `dp[i][j] = dp[i-1][j-1]`.
- Else: mismatch. `dp[i][j] = false`.

---

## 5. Case B — `*` (two sub-options)

If `p[j-1] == '*'`: the `*` modifies `p[j-2]`. Two sub-options:

> **Mini-refresher: zero occurrences OR at least one.**
>
> - **Zero occurrences:** skip the `x*` pair. `dp[i][j] = dp[i][j-2]`.
> - **At least one:** requires `p[j-2]` to match `s[i-1]` (literal or `.`). Then consume one s char; STAY on the `*` (it can match more). `dp[i][j] |= dp[i-1][j]`.

The second option SELF-RECURSES on the same `*`, effectively matching any number of repetitions.

---

## 6. Base case for row 0

`dp[0][j]` (empty s, pattern of length j): only true if pattern is shaped like `x*y*z*...` (every metacharacter pair matches zero chars).

```
for j in 2..m:
    if p[j-1] == '*': dp[0][j] = dp[0][j-2]
```

(Single chars in p can't match empty s, so dp[0][1] = false unless p[0] is `*` — which doesn't happen since `*` always has a preceding char.)

---

## 7. Code

**C++:**

```cpp
bool isMatch(string s, string p) {
    int n = s.size(), m = p.size();
    vector<vector<bool>> f(n + 1, vector<bool>(m + 1, false));
    f[0][0] = true;
    for (int j = 2; j <= m; ++j) {
        if (p[j-1] == '*') f[0][j] = f[0][j-2];
    }
    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            if (p[j-1] == '*') {
                f[i][j] = f[i][j-2];   // zero occurrences
                if (p[j-2] == '.' || p[j-2] == s[i-1]) {
                    f[i][j] = f[i][j] || f[i-1][j];   // one or more
                }
            } else {
                if (p[j-1] == '.' || p[j-1] == s[i-1]) {
                    f[i][j] = f[i-1][j-1];
                }
            }
        }
    }
    return f[n][m];
}
```

Complexity: **O(n · m)** time, **O(n · m)** space.

---

## 8. Trace it

`s = "aab", p = "c*a*b"`. n = 3, m = 5.

Row 0: `dp[0][0] = T`. `dp[0][2] = dp[0][0] = T` (c*). `dp[0][4] = dp[0][2] = T` (a*). Others F.

Row 1 (s[0]='a'):
- (1,1) p[0]='c' vs 'a': F.
- (1,2) p[1]='*': zero → dp[1][0] = F. AL1: 'c' vs 'a' mismatch → no add. F.
- (1,3) p[2]='a' vs 'a': match → dp[0][2] = T. T.
- (1,4) p[3]='*': zero → dp[1][2] = F. AL1: 'a' vs 'a' match → dp[0][4] = T. T.
- (1,5) p[4]='b' vs 'a': F.

Row 2 (s[1]='a'):
- (2,4) p[3]='*': zero → dp[2][2] = F. AL1: 'a' vs 'a' match → dp[1][4] = T. T.
- (2,5) p[4]='b' vs 'a': F.

Row 3 (s[2]='b'):
- (3,4) p[3]='*': zero → dp[3][2] = F. AL1: 'a' vs 'b' mismatch → no add. F.
- (3,5) p[4]='b' vs 'b' match → dp[2][4] = T. **T**.  ✓

---

## 9. Common pitfalls

1. **Treating `*` standalone as a wildcard for any sequence.** `*` requires a preceding element. `*` doesn't appear at index 0.
2. **Forgetting the "zero occurrences" branch.** `x*` can match the empty string — without this, `s="b", p="a*b"` would fail.
3. **Self-recursion in the "at least one" branch.** Use `f[i-1][j]` (NOT `f[i-1][j-2]`) — staying on the `*` is what allows multiple matches.
4. **Initializing row 0 wrong.** Only `x*` patterns can match empty s.
5. **`p[j-1] == s[i-1]` literal check.** Don't forget the `.` wildcard ALSO triggers a match.
6. **Greedy matching.** Don't try to match `*` greedily then backtrack — DP handles all branches naturally.

---

## 10. The shape — pattern-driven DP

The pattern: **2D DP where transitions depend on the PATTERN char's TYPE (literal, wildcard, repetition).**

| Problem | Pattern features |
|---|---|
| **This problem** | `.` (any one), `*` (zero or more of preceding) |
| Wildcard Matching | `?` (any one), `*` (any sequence — different from `*` here!) |
| Regex with `+` | `+` (one or more of preceding) |
| Regex with `?` | `?` (zero or one of preceding) |
| Full regex (with groups, alternation) | NFA construction, beyond simple DP |

**Pattern to internalize:**

> "Pattern matching with metacharacters: 2D DP. For `*`-like operators, branch on `zero occurrences` (skip pair) vs `one or more` (self-recurse on same column)."

---

> **Self-check — the question to ask next time.**
>
> When you see `*` for "zero or more of preceding":
>
> > **"f[i][j] = f[i][j-2] (zero) OR (f[i-1][j] if preceding matches s[i-1]). The self-recursion on column j unrolls any number of repetitions."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Regular_Expression_Matching.md`](../Regular_Expression_Matching.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Edit_Distance.md`](./Edit_Distance.md), [`Interleaving_String.md`](./Interleaving_String.md), [`Distinct_Subsequences.md`](./Distinct_Subsequences.md).
  - Coming next: [`Frog_Jump.md`](./Frog_Jump.md), [`Partition_Equal_Subset_Sum.md`](./Partition_Equal_Subset_Sum.md).
