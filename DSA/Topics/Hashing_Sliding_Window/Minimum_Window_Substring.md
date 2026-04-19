# Minimum Window Substring

**Problem Link:**
https://leetcode.com/problems/minimum-window-substring/

**Topic:**
Hashing / Sliding Window

----------------------------------------

## Step 1: Read the Problem Precisely

Given two strings `s` and `t`, find the shortest **substring of s** that contains **every character of t**, counting duplicates.

Two things to emphasize:
- "Substring" means contiguous. We're not picking scattered characters.
- "Counting duplicates" means if `t = "AABC"`, the window must contain two A's, one B, one C.

Example: `s = "ADOBECODEBANC"`, `t = "ABC"`. The shortest substring containing A, B, and C is `"BANC"` (length 4).

Edge cases:
- If `t` is longer than `s`: no valid window. Return `""`.
- If `t` is empty: technically any window works; typically return `""` per convention.
- If no valid window exists: return `""`.

----------------------------------------

## Step 2: Try Small Cases

`s = "a"`, `t = "a"`. Obviously the window is `"a"`.

`s = "ab"`, `t = "b"`. Window is `"b"`.

`s = "ab"`, `t = "ba"`. Windows containing both a and b: `"ab"` (length 2). Answer: `"ab"`.

`s = "aabbc"`, `t = "abc"`. Smallest window? Let me scan:
- `"aabbc"` (length 5) has everything.
- `"abbc"` (length 4) has everything.
- `"bbc"` (length 3) missing 'a'.
- `"abbc"` is the shortest containing all three? Actually let me check: `"abbc"` has a, b, b, c — yes. Length 4.
- Any length 3? Need a, b, c all present. `"abc"` would be ideal but isn't in s.
- Length 3 windows in s: `"aab"`, `"abb"`, `"bbc"`. First has no c; second has no c; third has no a. None work.

So shortest is length 4, which is `"abbc"`.

Hand-scanning even for length 5 takes real work. For large s, we need an algorithmic strategy.

----------------------------------------

## Step 3: The Brute Force

Try every substring of s: O(n²). For each, check if it contains all of t: O(|t| + window size). Total O(n³) or so. Too slow for typical inputs.

The waste: when we grow a window or shift it, we're not reusing previous work. Let's think about how to avoid that.

----------------------------------------

## Step 4: Think About the Window Growing and Shrinking

Imagine we have a window `[l, r]` in s. As `r` moves right, the window grows. At some point, the window contains all of t's characters — it's **valid**. When that happens, we want to *shrink* from the left as much as possible while still valid. The smallest valid window is a candidate for our answer.

Once we can't shrink further (removing the left character would break validity), we move `r` right again to find the next valid configuration. Grow, then shrink, then grow, then shrink...

This rhythm is the **sliding window pattern** with a grow-and-shrink cycle. Both `l` and `r` move monotonically forward (neither ever goes backward), giving O(n) total work.

The implementation detail: **how do we efficiently check whether the current window contains all of t's characters?**

----------------------------------------

## Step 5: Track Character Counts Incrementally

Instead of re-checking the window from scratch, we maintain running counts:

- `need[c]` = how many of character c we need (from t).
- `have[c]` = how many of c are currently in the window.

When `r` advances to include `s[r]`: `have[s[r]]++`.
When `l` advances to exclude `s[l]`: `have[s[l]]--`. Then move l.

Validity: the window contains all of t iff `have[c] >= need[c]` for **every** c that appears in t.

Checking this "for every c" requires scanning all 256 possible characters, which is technically O(1) but feels clunky. Can we track validity in a single number?

**Yes.** Introduce `matched` = the count of **distinct characters** whose `have[c] >= need[c]` currently. Let `required` = number of distinct characters in t.

The window is valid iff `matched == required`.

Whenever we increment `have[c]`: if we *just reached* `need[c]` (i.e., `have[c] == need[c]` after the increment, and only then), bump `matched`.

Whenever we decrement `have[c]`: if we *just dropped below* `need[c]` (i.e., `have[c] == need[c] - 1` after the decrement), drop `matched`.

These "just crossed the threshold" checks are why we use equality comparisons specifically, not inequality. The idea is that `matched` changes only at boundary moments, making the check O(1).

----------------------------------------

## Step 6: Why `matched` Counts *Distinct* Characters Satisfied

Let me be precise about why we track distinct characters, not total characters.

We could track "total matched character count" — sum of `min(have[c], need[c])` across all c. When that equals `|t|`, the window is valid. But updating this sum on every change requires a clamp operation, which is tricky.

Tracking *distinct chars satisfied* is cleaner because each character's threshold-crossing is a single discrete event. When `have[c]` goes from `need[c] - 1` to `need[c]`, that character switches from "not satisfied" to "satisfied." Clean flip.

Once `have[c]` exceeds `need[c]` by more, it stays satisfied — we don't want to re-count. Only the specific threshold-crossing matters for `matched`.

----------------------------------------

## Step 7: Clean Algorithm

```
build need[] from t, required = len(need)
have[] = empty, matched = 0, l = 0
bestLen = ∞, bestStart = 0

for r in 0..|s|-1:
    c = s[r]
    have[c]++
    if need[c] > 0 and have[c] == need[c]:  # just crossed into "satisfied"
        matched++
    
    while matched == required:
        # window [l, r] is valid — record and try to shrink
        if r - l + 1 < bestLen:
            bestLen = r - l + 1
            bestStart = l
        
        leftChar = s[l]
        have[leftChar]--
        if need[leftChar] > 0 and have[leftChar] == need[leftChar] - 1:
            matched--       # just dropped below threshold
        l++

return "" if bestLen == ∞ else s[bestStart : bestStart + bestLen]
```

----------------------------------------

## Step 8: Trace on `s = "ADOBECODEBANC"`, `t = "ABC"`

`need = {A:1, B:1, C:1}`, `required = 3`.

I'll track `have`, `matched`, and any window records:

```
r=0, c='A': have[A]=1. Was 0, just reached need=1. matched=1.
r=1, c='D': not in need. have[D]=1. matched still 1.
r=2, c='O': not in need. matched=1.
r=3, c='B': have[B]=1. Just reached need=1. matched=2.
r=4, c='E': not in need. matched=2.
r=5, c='C': have[C]=1. Just reached need=1. matched=3. VALID.
  Window "ADOBEC" (l=0 to r=5, length 6). bestLen=6, bestStart=0.
  Shrink:
    l=0, s[l]='A'. have[A] 1→0. Dropped below need. matched=2. l=1.
  Exit while (matched < required).

r=6, c='O': not in need. matched=2.
r=7, c='D': not in need. matched=2.
r=8, c='E': not in need. matched=2.
r=9, c='B': have[B] 1→2. Already satisfied (above need), matched unchanged.
r=10, c='A': have[A] 0→1. Just reached need. matched=3. VALID.
  Window "DOBECODEBA" (l=1, r=10, length 10). Not better than 6.
  Shrink:
    l=1, 'D': not in need. l=2.
    l=2, 'O': not in need. l=3.
    Window now l=3 to r=10, "BECODEBA" length 8.
    l=3, 'B': have[B] 2→1. Still >= need. matched unchanged. l=4.
    Window l=4..10, "ECODEBA" length 7.
    l=4, 'E': not in need. l=5. "CODEBA" length 6. Tie with best.
    l=5, 'C': have[C] 1→0. Dropped below. matched=2. l=6.
  Exit.

r=11, c='N': not in need. matched=2.
r=12, c='C': have[C] 0→1. Just reached need. matched=3. VALID.
  Window l=6..12, "ODEBANC" length 7. Not better.
  Shrink:
    l=6, 'O': l=7. Window l=7..12, "DEBANC" length 6. Tie.
    l=7, 'D': l=8. Window l=8..12, "EBANC" length 5. NEW BEST. bestStart=8.
    l=8, 'E': l=9. Window l=9..12, "BANC" length 4. NEW BEST. bestStart=9.
    l=9, 'B': have[B] 1→0. Dropped below. matched=2. l=10.
  Exit.
```

End of loop. bestLen=4, bestStart=9. Return `s.substr(9, 4) = "BANC"`. ✓

That was the correct answer. The trace shows the grow-shrink rhythm clearly: we never backtrack, we just advance r and then try to push l forward as much as possible.

----------------------------------------

## Step 9: Why It's O(n)

Both `l` and `r` advance monotonically. `r` goes from 0 to n-1 (n steps). `l` can at worst go from 0 to n (another n steps). Each step is O(1) — hashmap updates and threshold checks.

Total work: O(n). Brute force was O(n³). That's the sliding window's payoff.

----------------------------------------

## Step 10: Name It

This is a **variable-sized sliding window with a satisfaction counter**. Same template:
- Grow r to include more characters.
- Track when the window becomes "valid" via counting.
- Shrink l greedily while valid.
- Record the best window at every valid state.

Applied to:
- Find All Anagrams in a String (fixed-size window).
- Longest Substring with At Most K Distinct Characters.
- Longest Repeating Character Replacement.
- Subarrays with K Different Integers.

----------------------------------------

## Step 11: Complexity

Time: **O(n + m)** where n = |s|, m = |t|.
Space: **O(|Σ|)** for the count maps; effectively O(1) for fixed alphabets.

----------------------------------------

## Step 12: C++ Implementation

```cpp
string minWindow(string s, string t) {
    if (t.empty() || s.size() < t.size()) return "";

    unordered_map<char, int> need;
    for (char c : t) need[c]++;
    int required = need.size();

    unordered_map<char, int> have;
    int matched = 0;
    int l = 0;
    int bestLen = INT_MAX, bestStart = 0;

    for (int r = 0; r < (int)s.size(); ++r) {
        char c = s[r];
        have[c]++;
        if (need.count(c) && have[c] == need[c]) matched++;

        while (matched == required) {
            if (r - l + 1 < bestLen) {
                bestLen = r - l + 1;
                bestStart = l;
            }
            char leftC = s[l];
            have[leftC]--;
            if (need.count(leftC) && have[leftC] < need[leftC]) matched--;
            l++;
        }
    }

    return bestLen == INT_MAX ? "" : s.substr(bestStart, bestLen);
}
```

Implementation gotchas:
- Use `need.count(c)` to test "is c a character we care about?" before doing `have[c] == need[c]`. Without this guard, characters not in t still pass through the threshold check and cause bugs.
- Use `<` (not `<=`) when checking if we dropped below need. We drop matched only when `have[leftC]` *becomes* less than `need[leftC]`, which is exactly when the decrement brought it below.

----------------------------------------

## Step 13: Follow-up Questions

- **Find all minimum windows (return every length-`bestLen` window with target).** Continue the scan; record all windows equal to bestLen, not just the first.
- **Longest window containing any of multiple patterns.** Harder; might need Aho-Corasick or a counting extension.
- **Window containing *at most* k distinct characters.** Different validity check (count distinct in window ≤ k).
- **Streaming version.** The algorithm is already one-pass; it adapts naturally to streaming input.
- **Why not just sort t and s's window?** Sorting doesn't respect that we only need t's chars to be present, not equal. Plus it's slower.
