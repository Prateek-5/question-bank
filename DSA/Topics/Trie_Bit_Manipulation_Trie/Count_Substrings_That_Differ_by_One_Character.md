# Count Substrings That Differ by One Character

**Problem Link:**
https://leetcode.com/problems/count-substrings-that-differ-by-one-character/description/

**Topic:**
Trie / Bit Manipulation Trie (solvable via DP too)

----------------------------------------

## Step 1: The Task

Given two strings `s` and `t`, count the number of substring pairs `(s[i..i+L-1], t[j..j+L-1])` — same length L — that differ in **exactly one character** (the same position, same length, exactly one mismatch).

Example: `s = "aba"`, `t = "baba"`.
- "a" vs "b" (1-char substring, differ) → pair.
- "a" vs "a" (same — not 1 diff) → not a pair.
- "ab" vs "ba" (differ in both) → not a pair.
- "ab" vs "ab" (same) → not a pair.
- "ab" vs "bb" (1 diff) → pair.
- And so on.

Count = **6** for this example (per LeetCode).

----------------------------------------

## Step 2: Brute Force

For each pair (i, j) of starting positions in s and t, for each length L such that both substrings fit, count mismatches and add 1 if exactly 1.

Three nested loops; worst O(|s| · |t| · min(|s|, |t|)²). Way too slow.

We need structural reuse.

----------------------------------------

## Step 3: Key Observation — Pairs Grow From a Mismatch

Fix a starting pair (i, j) in (s, t). As we extend L = 1, 2, 3, ..., the number of mismatches in the prefix is a non-decreasing function of L.

Consider the **first mismatch** at offset k (so s[i+k] ≠ t[j+k], but s[i..i+k-1] == t[j..j+k-1]). After that mismatch, any substring of length k+1 at (i, j) has exactly 1 mismatch. As we extend further, we count pairs of length k+1 + r as long as s[i+k+1..] and t[j+k+1..] match for r characters — each r = 0, 1, ..., until the next mismatch.

So for a fixed starting pair (i, j):
- Let `k` = first mismatch offset.
- Let `right(i+k+1, j+k+1)` = number of matching characters starting at (i+k+1, j+k+1).
- Contribution from this starting pair = `1 + right(i+k+1, j+k+1)` substring pairs of exactly-1 mismatch.

Reason: length k+1 (ends at first mismatch) → 1 mismatch ✓. Length k+2 → 1 mismatch iff s[i+k+1] == t[j+k+1]. In general, lengths k+1, k+2, ..., k+1+right all have exactly 1 mismatch.

After that, the next mismatch at offset k2 means length k2 has 2 mismatches — no longer valid.

----------------------------------------

## Step 4: Precompute Left and Right Matches

Define two 2D arrays:

```
left[i][j] = longest prefix of s[i..] and t[j..] that matches  (going forward)
right[i][j] = longest suffix, same idea, going backward
```

Actually a cleaner formulation: for each pair (i, j), compute
- `forward[i][j]` = length of longest common prefix of s[i:] and t[j:].
- `backward[i][j]` = length of longest common suffix of s[:i+1] and t[:j+1] (i.e., match going left).

Then count contributions: for each pair (i, j) where `s[i] ≠ t[j]` (a potential "single mismatch position"), the number of valid substring pairs that have **this** as the mismatch position is:

```
(backward[i-1][j-1] + 1) * (forward[i+1][j+1] + 1)
```

Reason: the substring pair can extend `0..backward[i-1][j-1]` characters to the left (staying matched), and `0..forward[i+1][j+1]` to the right. Each combination yields a unique (length, starting index) substring pair with exactly this single mismatch.

Sum over all mismatch positions (i, j).

----------------------------------------

## Step 5: Computing Forward and Backward

`forward[i][j]` = 1 + forward[i+1][j+1] if s[i] == t[j], else 0. Fill right-to-left, bottom-up.

`backward[i][j]` = 1 + backward[i-1][j-1] if s[i] == t[j], else 0. Fill left-to-right, top-down.

Both in O(|s| · |t|).

----------------------------------------

## Step 6: Algorithm

```
m, n = len(s), len(t)
forward = 2D array (m+1) x (n+1), init 0
backward = 2D array (m+1) x (n+1), init 0

# Backward
for i in 0..m-1:
    for j in 0..n-1:
        if s[i] == t[j]:
            backward[i][j] = backward[i-1][j-1] + 1 (or 1 if i or j = 0)

# Forward
for i from m-1 down to 0:
    for j from n-1 down to 0:
        if s[i] == t[j]:
            forward[i][j] = forward[i+1][j+1] + 1 (or 1 if i or j at boundary)

count = 0
for i in 0..m-1:
    for j in 0..n-1:
        if s[i] != t[j]:
            left_extend = backward[i-1][j-1] if i>0 and j>0 else 0
            right_extend = forward[i+1][j+1] if i<m-1 and j<n-1 else 0
            count += (left_extend + 1) * (right_extend + 1)

return count
```

Two O(m · n) passes for the precomputation, one O(m · n) final counting pass. **O(m · n)** total time.

----------------------------------------

## Step 7: Trace on `s = "aba"`, `t = "baba"`

m=3, n=4.

backward[i][j] = longest match ending at (i, j):
```
     b  a  b  a
 a  [0, 1, 0, 1]
 b  [1, 0, 2, 0]
 a  [0, 2, 0, 3]
```

forward[i][j] = longest match starting at (i, j):
```
     b  a  b  a
 a  [0, 1, 0, 1]
 b  [1, 0, 2, 0]
 a  [0, 1, 0, 1]
```

Wait, let me recompute forward carefully.

forward[2][j] (last row of s, i.e., s[2]='a'): matches t[j]='a' → 1 if yes. t = "baba" → forward[2][0]=0 (s[2]=a,t[0]=b), forward[2][1]=1, forward[2][2]=0, forward[2][3]=1.

forward[1][j] (s[1]='b'): forward[1][0]=1 + forward[2][1]=1+1=2 (s[1]=b matches t[0]=b, then s[2]=a matches t[1]=a). forward[1][1]=0. forward[1][2]=1 + forward[2][3]=2. forward[1][3]=0.

forward[0][j] (s[0]='a'): forward[0][0]=0. forward[0][1]=1+forward[1][2]=1+2=3. forward[0][2]=0. forward[0][3]=1+forward[1][4]=1+0=1 (but forward[1][4] doesn't exist, treat as 0).

Count mismatches and contributions:

For each (i, j) where s[i] ≠ t[j]:
- (0, 0): s='a', t='b'. Different. left=0 (edge). right=forward[1][1]=0. Contribution = (0+1)(0+1) = 1.
- (0, 2): a vs b. left = backward[-1][1]=0. right = forward[1][3]=0. Contribution 1.
- (1, 1): b vs a. left = backward[0][0]=0. right = forward[2][2]=0. Contribution 1.
- (1, 3): b vs a. left = backward[0][2]=0. right = forward[2][4]=0. Contribution 1.
- (2, 0): a vs b. left = backward[1][-1]=0. right = forward[3][1]=0. Contribution 1.
- (2, 2): a vs b. left = backward[1][1]=0. right = forward[3][3]=0. Contribution 1.

Total = 6. ✓

----------------------------------------

## Step 8: Name It

**Precomputed LCP/LCS tables around a pivot.** The technique of fixing a "special position" and independently measuring the extents in both directions is powerful — it appears in:
- Longest palindromic substring (Manacher-style: expand around each center).
- Counting palindromes with one mismatch allowed.
- Edit-distance with exactly-one-edit queries.
- String matching with approximate matches.

The trie label in this topic is somewhat loose; the problem's clean solution is DP over string pairs.

----------------------------------------

## Step 9: Complexity

Time: **O(m · n)** for two precomputations + counting pass.
Space: **O(m · n)** for the two tables (reducible with rolling arrays if needed).

----------------------------------------

## Step 10: C++ Implementation

```cpp
int countSubstrings(string s, string t) {
    int m = s.size(), n = t.size();
    vector<vector<int>> forward(m + 1, vector<int>(n + 1, 0));
    vector<vector<int>> backward(m + 1, vector<int>(n + 1, 0));

    // Backward: longest match ending at (i, j)
    for (int i = 0; i < m; ++i)
        for (int j = 0; j < n; ++j)
            if (s[i] == t[j])
                backward[i + 1][j + 1] = backward[i][j] + 1;

    // Forward: longest match starting at (i, j)
    for (int i = m - 1; i >= 0; --i)
        for (int j = n - 1; j >= 0; --j)
            if (s[i] == t[j])
                forward[i][j] = forward[i + 1][j + 1] + 1;

    int count = 0;
    for (int i = 0; i < m; ++i)
        for (int j = 0; j < n; ++j)
            if (s[i] != t[j]) {
                int L = backward[i][j];          // match going left of (i, j)
                int R = forward[i + 1][j + 1];   // match going right of (i, j)
                count += (L + 1) * (R + 1);
            }
    return count;
}
```

Note: in the shifted indexing, `backward[i][j]` (in the +1 grid) holds what "backward[i-1][j-1]" was in the algorithmic description. This is a standard DP offset trick to avoid -1 edge cases.

----------------------------------------

## Step 11: Follow-up Questions

- **Exactly k mismatches instead of 1.** Generalize: for each starting pair, enumerate the set of first k mismatch positions. More involved.
- **Use a trie for this.** Insert all suffixes of s and t into a generalized suffix trie with edges labeled; traverse with "one mismatch budget." Theoretically possible but complex.
- **Very long strings (10^5 chars each).** O(m · n) = 10^10 — too slow. Need suffix automaton or hashing-based approach.
- **Return the pairs themselves, not just count.** Large output; track and emit.
- **At most 1 mismatch (including 0).** Add pairs with 0 mismatches: sum of LCP lengths. Or adapt the counting.
- **Why expand around mismatches?** Because the mismatch position is the "pivot" — everything matches on either side, at least until another mismatch.
