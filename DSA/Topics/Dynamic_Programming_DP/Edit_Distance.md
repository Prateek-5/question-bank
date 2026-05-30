# Edit Distance

**Problem Link:**
<a href="https://leetcode.com/problems/edit-distance/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/edit-distance/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: The Problem Stated Plainly

You're given two strings, `s` and `t`. In one edit operation, you can:
- **Insert** a character anywhere in `s`.
- **Delete** a character from `s`.
- **Replace** a character in `s`.

Return the **minimum** number of edits to convert `s` into `t`.

Example: `s = "horse"`, `t = "ros"`. Answer: **3**.
- "horse" → "rorse" (replace h→r)
- "rorse" → "rose" (delete r)
- "rose" → "ros" (delete e)

----------------------------------------

## Step 2: Small Cases

**If `s` is empty:** we must insert every character of `t`. Edits = `|t|`.
**If `t` is empty:** we must delete every character of `s`. Edits = `|s|`.
**If `s == t`:** 0 edits.
**`s = "a"`, `t = "b"`:** one replace → 1 edit.
**`s = "ab"`, `t = "a"`:** delete `b` → 1 edit.
**`s = "a"`, `t = "ab"`:** insert `b` → 1 edit.
**`s = "ab"`, `t = "cd"`:** two replaces → 2 edits.

Nothing yet jumps out. Let me try a medium example to see if a pattern emerges.

**`s = "cat"`, `t = "cut"`:** only `a` differs from `u` → one replace → 1 edit.
**`s = "cat"`, `t = "ct"`:** delete `a` → 1 edit.
**`s = "ct"`, `t = "cat"`:** insert `a` → 1 edit.

So far, each operation affects one character. The edits "accumulate" across the string's length. But operations can affect different positions in tricky ways — especially inserts and deletes, which shift alignment.

----------------------------------------

## Step 3: Think About the Last Character

Here's a trick that works for many string-alignment problems. Instead of thinking about the whole strings, think about just the last characters.

Let `f(i, j)` = minimum edits to convert `s[0..i-1]` (first `i` chars of `s`) into `t[0..j-1]` (first `j` chars of `t`).

Consider the last operation in the optimal sequence. What are the possibilities?

**Case A: Last character of `s[0..i-1]` matches last character of `t[0..j-1]`.**
- If `s[i-1] == t[j-1]`, we can leave both alone. The remaining problem is converting `s[0..i-2]` to `t[0..j-2]`. So `f(i, j) = f(i-1, j-1)`.

**Case B: Last character doesn't match — we need to do *something* with it.**

Three sub-cases based on which operation was last:

- **Replace**: replace `s[i-1]` with `t[j-1]`, then we still need to convert `s[0..i-2]` to `t[0..j-2]`. Cost: `1 + f(i-1, j-1)`.

- **Delete from s**: remove `s[i-1]`, then convert `s[0..i-2]` to `t[0..j-1]`. Cost: `1 + f(i-1, j)`.

- **Insert into s**: insert `t[j-1]` at the end, so we've taken care of the last char of `t`; now convert `s[0..i-1]` to `t[0..j-2]`. Cost: `1 + f(i, j-1)`.

We pick the minimum.

So:

```
f(i, j) = f(i-1, j-1)                            if s[i-1] == t[j-1]
        = 1 + min(f(i-1, j-1), f(i-1, j), f(i, j-1))   otherwise
```

With base cases `f(0, j) = j` and `f(i, 0) = i`.

This is a 2D DP.

----------------------------------------

## Step 4: Why Those Three Options Cover Everything

It's worth pausing here. Why are there exactly three options (when characters don't match)?

Any sequence of edits transforms `s` into `t`. Consider the **final alignment**:

- Character `s[i-1]` ends up matched to `t[j-1]` (either unchanged or replaced).
- Character `s[i-1]` gets deleted.
- Character `t[j-1]` came from an insertion (not from anywhere in `s`).

Those three cover every possibility for what happens to the last character. The recurrence reflects this.

This is the same "parameterize on what happens to the last position" trick that appears in LCS, edit distance, regex matching, and many other string-alignment problems.

----------------------------------------

## Step 5: Build the Table for `"horse"` → `"ros"`

Let's fill `f` as a table. Rows indexed by `i` (length of `s` prefix), columns by `j` (length of `t` prefix).

```
       ""  r  o  s
""      0  1  2  3
h       1  1  2  3
ho      2  2  1  2
hor     3  2  2  2
hors    4  3  3  2    ← wait, let me recompute this carefully
horse   5  4  4  3
```

Let me be more careful.

`f(0, 0) = 0`.
`f(0, j) = j` for first row.
`f(i, 0) = i` for first column.

Now compute `f(1, 1)`. `s[0] = 'h'`, `t[0] = 'r'`. Mismatch. `f(1,1) = 1 + min(f(0,0), f(0,1), f(1,0)) = 1 + min(0, 1, 1) = 1`.

`f(1, 2)`. `s[0]='h'`, `t[1]='o'`. Mismatch. `1 + min(f(0,1), f(0,2), f(1,1)) = 1 + min(1,2,1) = 2`.

`f(1, 3)`. `s[0]='h'`, `t[2]='s'`. Mismatch. `1 + min(f(0,2), f(0,3), f(1,2)) = 1 + min(2,3,2) = 3`.

`f(2, 1)`. `s[1]='o'`, `t[0]='r'`. Mismatch. `1 + min(f(1,0), f(1,1), f(2,0)) = 1 + min(1,1,2) = 2`.

`f(2, 2)`. `s[1]='o'`, `t[1]='o'`. Match. `f(2,2) = f(1,1) = 1`.

`f(2, 3)`. `s[1]='o'`, `t[2]='s'`. Mismatch. `1 + min(f(1,2), f(1,3), f(2,2)) = 1 + min(2,3,1) = 2`.

`f(3, 1)`. `s[2]='r'`, `t[0]='r'`. Match. `f(3,1) = f(2,0) = 2`.

`f(3, 2)`. Mismatch. `1 + min(f(2,1), f(2,2), f(3,1)) = 1 + min(2,1,2) = 2`.

`f(3, 3)`. Mismatch. `1 + min(f(2,2), f(2,3), f(3,2)) = 1 + min(1,2,2) = 2`.

`f(4, 1)`. `s[3]='s'`, `t[0]='r'`. Mismatch. `1 + min(f(3,0), f(3,1), f(4,0)) = 1 + min(3,2,4) = 3`.

`f(4, 2)`. `s[3]='s'`, `t[1]='o'`. Mismatch. `1 + min(f(3,1), f(3,2), f(4,1)) = 1 + min(2,2,3) = 3`.

`f(4, 3)`. `s[3]='s'`, `t[2]='s'`. Match. `f(4,3) = f(3,2) = 2`.

`f(5, 1)`. `s[4]='e'`, `t[0]='r'`. Mismatch. `1 + min(f(4,0), f(4,1), f(5,0)) = 1 + min(4,3,5) = 4`.

`f(5, 2)`. Mismatch. `1 + min(f(4,1), f(4,2), f(5,1)) = 1 + min(3,3,4) = 4`.

`f(5, 3)`. Mismatch. `1 + min(f(4,2), f(4,3), f(5,2)) = 1 + min(3,2,4) = 3`.

Final table:

```
       ""  r  o  s
""      0  1  2  3
h       1  1  2  3
ho      2  2  1  2
hor     3  2  2  2
hors    4  3  3  2
horse   5  4  4  3
```

`f(5, 3) = 3`. ✓

----------------------------------------

## Step 6: The Name

This is the **Wagner–Fischer algorithm** computing **Levenshtein distance** — the classical edit distance. But we derived the recurrence by asking "what happens to the last character?" and enumerating cases. The name is a tag, not an insight.

----------------------------------------

## Step 7: Complexity

Time: we fill an `(|s|+1) × (|t|+1)` table, O(1) per cell. **O(|s| · |t|)**.

Space: **O(|s| · |t|)** with the full table. But note: each cell only depends on `f(i-1, j-1)`, `f(i-1, j)`, `f(i, j-1)` — the previous row and the current row. So we can compress to two rows (or even one row with care), giving **O(min(|s|, |t|))** space.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int minDistance(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<int>> f(n + 1, vector<int>(m + 1, 0));
    for (int i = 0; i <= n; ++i) f[i][0] = i;
    for (int j = 0; j <= m; ++j) f[0][j] = j;
    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            if (s[i-1] == t[j-1]) f[i][j] = f[i-1][j-1];
            else f[i][j] = 1 + min({f[i-1][j-1], f[i-1][j], f[i][j-1]});
        }
    }
    return f[n][m];
}
```

Clean 12-line implementation. The recurrence does all the work.

----------------------------------------

## Step 9: Follow-up Questions

- **Return the actual edit sequence, not just the count.** Add parent pointers during the DP; walk them back from `(n, m)` to `(0, 0)`.
- **Weighted edits (insert, delete, replace have different costs).** Change the `1 + ...` terms to their respective weights; same recurrence.
- **Transpositions allowed (Damerau–Levenshtein).** Add a fourth case: `f(i, j) = 1 + f(i-2, j-2)` if `s[i-1]==t[j-2] && s[i-2]==t[j-1]`.
- **Hamming distance instead (only replaces, strings of equal length).** Linear scan counting mismatches.
- **Approximate string matching: find substrings of `t` within edit distance k of `s`.** Modify the DP initialization to allow the first row to be 0 everywhere.
- **Space optimization to O(min(n, m)).** Maintain just the previous row; carefully update with a temp variable for the diagonal dependency.
