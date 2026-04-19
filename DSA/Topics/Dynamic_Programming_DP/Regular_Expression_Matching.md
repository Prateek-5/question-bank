# Regular Expression Matching

**Problem Link:**
https://leetcode.com/problems/regular-expression-matching/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: The Mini Regex Language

We implement a **stripped-down** regex that supports two metacharacters:
- `.` matches any single character.
- `*` matches **zero or more** of the *preceding* element.

Given a string `s` and a pattern `p`, return whether `p` matches the **entire** `s`.

Examples:
- `s = "aa"`, `p = "a"` → false (p only matches one `a`).
- `s = "aa"`, `p = "a*"` → true (`a*` matches zero or more a's).
- `s = "ab"`, `p = ".*"` → true (`.*` matches any sequence).
- `s = "aab"`, `p = "c*a*b"` → true (`c*` matches zero c's, `a*` matches two a's, `b` matches b).
- `s = "mississippi"`, `p = "mis*is*p*."` → false.

The trick is that `*` doesn't match anything on its own — it applies to the preceding character. `a*` is treated as a unit meaning "any number of a's including zero."

----------------------------------------

## Step 2: Try to Match By Hand

`s = "aab"`, `p = "c*a*b"`.

- `c*` at start: zero c's, consume no chars of s. Pattern advances 2 chars (past `c*`). s at 0.
- `a*` next: two a's match, consume s[0] and s[1]. Pattern advances 2. s at 2.
- `b` next: matches s[2]='b'. s at 3, end.
- Pattern fully consumed, s fully consumed. Match.

That worked. But notice there were choices: `c*` could match zero or one or more c's. `a*` could match zero, one, two, or three a's (bounded by how many a's are actually in s at that position). The algorithm has to explore choices.

What if we tried `s = "aa"`, `p = "a*a"`? `a*` could greedily match both a's, but then `a` has nothing left to match. Backing off, `a*` matches just one a, leaving the second for `a`. Match.

Choices matter. We need a principled way to handle them.

----------------------------------------

## Step 3: Define the DP State

Let `f(i, j)` = true if `p[0..j-1]` matches `s[0..i-1]` entirely.

Transitions depend on what `p[j-1]` is:

**Case A: `p[j-1]` is a regular char or `.`** (not `*`).

Then we need `s[i-1]` to match `p[j-1]`:
- If `p[j-1] == '.'` or `p[j-1] == s[i-1]`: the last chars match. Reduce to `f(i-1, j-1)`.
- Else: mismatch. `f(i, j) = false`.

**Case B: `p[j-1]` is `*`.**

This `*` applies to `p[j-2]`. We have two sub-options:
- **Match zero occurrences**: skip the `x*` pair in the pattern. `f(i, j) = f(i, j-2)`.
- **Match one or more**: requires `p[j-2]` to match `s[i-1]` (either `.` or same char). Then consume one char of s: `f(i, j) = f(i-1, j)`. (Notice: we don't advance j yet — because `x*` might match even more of s.)

Take the OR of these two.

**Base case: `f(0, 0) = true`** (empty pattern matches empty string).
**For `f(0, j)` with j > 0:** only true if pattern is of the form `x*y*z*...` — all star-pairs that match zero chars. Handle this by computing row 0 using the Case B rule.

**For `f(i, 0)` with i > 0:** `false` — empty pattern can't match non-empty string.

----------------------------------------

## Step 4: Why Two Sub-options for `*`?

This is the tricky part. Let me explain concretely.

Suppose `p[j-2..j-1] = "a*"` and we're computing `f(i, j)`.

- **"Match zero a's":** the `a*` contributes nothing. Pattern progresses past it. So the matching reduces to `p[0..j-3]` against `s[0..i-1]` — that's `f(i, j-2)`.
- **"Match at least one more a":** s[i-1] must match `a` (literal or via `.`). If so, we've used one more `a`. The `a*` is still available to match more. Pattern stays at j; s drops by 1. So `f(i, j) = f(i-1, j)`.

These cover all possibilities because a `*` matches some **integer count ≥ 0** of the preceding element. "Zero" is one option; "at least one" covers 1, 2, 3, ... and the recursion unrolls into those via iterated `f(i-1, j)`, `f(i-2, j)`, etc.

----------------------------------------

## Step 5: Trace "aab" vs "c*a*b"

n = 3, m = 5. `p = "c*a*b"` (indices 0..4).

Let me fill `f`.

Row 0 (i=0):
- f(0, 0) = T.
- f(0, 1): p[0]='c', not `*`. f = false (i=0, can't consume).
- f(0, 2): p[1]='*'. Try "match zero c's": f(0, 0) = T. → T.
- f(0, 3): p[2]='a', not `*`. F.
- f(0, 4): p[3]='*'. Try zero: f(0, 2) = T. → T.
- f(0, 5): p[4]='b', not `*`. F.

Row 1 (i=1, s[0]='a'):
- f(1, 0) = F.
- f(1, 1): p[0]='c'. s[0]='a' != 'c'. F.
- f(1, 2): p[1]='*'. Zero option: f(1, 0) = F. At-least-one: p[0]='c' vs s[0]='a'. Mismatch. F.
- f(1, 3): p[2]='a'. s[0]='a'. Match. f(0, 2) = T. → T.
- f(1, 4): p[3]='*'. Zero: f(1, 2) = F. At-least-one: p[2]='a' vs s[0]='a', match, f(0, 4) = T. → T.
- f(1, 5): p[4]='b'. s[0]='a' != 'b'. F.

Row 2 (i=2, s[1]='a'):
- f(2, 0) = F.
- f(2, 1): p[0]='c' vs s[1]='a'. F.
- f(2, 2): p[1]='*'. Zero: f(2, 0) = F. AL1: c vs a. F. F.
- f(2, 3): p[2]='a' vs s[1]='a'. Match. f(1, 2) = F. → F.
- f(2, 4): p[3]='*'. Zero: f(2, 2) = F. AL1: p[2]='a' vs s[1]='a', match, f(1, 4) = T. → T.
- f(2, 5): p[4]='b' vs s[1]='a'. F.

Row 3 (i=3, s[2]='b'):
- f(3, 0) = F.
- f(3, 1): c vs b. F.
- f(3, 2): Zero: f(3, 0) = F. AL1: c vs b. F.
- f(3, 3): p[2]='a' vs s[2]='b'. F.
- f(3, 4): p[3]='*'. Zero: f(3, 2) = F. AL1: p[2]='a' vs s[2]='b'. Mismatch. F.
- f(3, 5): p[4]='b' vs s[2]='b'. Match. f(2, 4) = T. → T.

f(3, 5) = **T**. ✓ Matches the hand analysis.

----------------------------------------

## Step 6: Why This Handles All Star Expansions

The recursion `f(i, j) = f(i-1, j)` for the "at-least-one more" branch is self-referential — the same `f(i-1, j)` itself recursively evaluates by trying both branches, including a further "at-least-one" branch that consumes another char, and so on.

So effectively, the DP considers all possible numbers of chars matched by `x*`: 0, 1, 2, ..., up to however many chars of s remain. We don't have to loop over these explicitly — the recurrence unrolls them implicitly.

----------------------------------------

## Step 7: Name the Pattern

This is the classic **regex-matching DP** — a standard interview problem that stress-tests your ability to handle multi-case transitions. The core skill: recognizing that the `*` operator introduces branching, and handling both branches explicitly in the recurrence.

The same 2D-DP shape solves wildcard matching (`*` matches any sequence, `?` matches any one char), where the cases differ slightly.

----------------------------------------

## Step 8: Complexity

Time: filling `(n+1)(m+1)` cells with O(1) work each. **O(n·m)**.
Space: **O(n·m)** for the table. Optimizable to O(m) with careful row-by-row updates.

----------------------------------------

## Step 9: C++ Implementation

```cpp
bool isMatch(string s, string p) {
    int n = s.size(), m = p.size();
    vector<vector<bool>> f(n + 1, vector<bool>(m + 1, false));
    f[0][0] = true;
    // row 0: only x* patterns can match empty s
    for (int j = 2; j <= m; ++j) {
        if (p[j - 1] == '*') f[0][j] = f[0][j - 2];
    }
    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            if (p[j - 1] == '*') {
                // zero occurrences
                f[i][j] = f[i][j - 2];
                // one or more — if preceding pattern char matches s[i-1]
                if (p[j - 2] == '.' || p[j - 2] == s[i - 1]) {
                    f[i][j] = f[i][j] || f[i - 1][j];
                }
            } else {
                if (p[j - 1] == '.' || p[j - 1] == s[i - 1]) {
                    f[i][j] = f[i - 1][j - 1];
                }
            }
        }
    }
    return f[n][m];
}
```

Reading the code: the first loop initializes row 0 with the "x* patterns that match empty" special case. The double loop then handles each cell: if the pattern char is `*`, apply the two-branch rule; otherwise, single-char match.

----------------------------------------

## Step 10: Follow-up Questions

- **Wildcard matching (`?` matches any char, `*` matches any sequence).** Similar DP, but `*` now greedily or non-greedily matches — different recurrence.
- **Support `+` (one or more).** Straightforward extension: `x+` is the same as `x` then `x*`.
- **Support `?` (zero or one).** Add a case: `f(i, j) = f(i, j-2) || (match && f(i-1, j-2))`.
- **Full regex (character classes, alternation, groups).** Much harder — use Thompson's NFA construction or backtracking.
- **Return the matched substring in s (not full match).** Change the semantics: `f(0, j) = true` for all j (match starts anywhere); answer is any `f(i, m) = true`.
- **Reconstruct matching groups.** Track parent pointers; walk back through the DP.
