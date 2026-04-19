# Longest Substring Without Repeating Characters

**Problem Link:**
https://leetcode.com/problems/longest-substring-without-repeating-characters/

**Topic:**
Hashing / Sliding Window

----------------------------------------

## Step 1: What Are We Actually Asked?

Given a string `s`, find the length of the longest *substring* (contiguous slice) in which every character is unique.

Example: `s = "abcabcbb"`. Possible unique-character substrings include `"abc"`, `"bca"`, `"cab"`, etc. — all length 3. There's no length-4 substring with all unique characters. So the answer is `3`.

Another: `s = "pwwkew"` → best is `"wke"` of length 3 (note `"pwke"` isn't contiguous since it skips an index).

----------------------------------------

## Step 2: The Naïve Approach

For every starting index `i`, extend outward as long as characters stay unique. Track the max length.

```cpp
int best = 0;
for (int i = 0; i < n; ++i) {
    set<char> seen;
    for (int j = i; j < n; ++j) {
        if (seen.count(s[j])) break;
        seen.insert(s[j]);
    }
    best = max(best, (int)seen.size());
}
```

That's O(n²) in time and O(min(n, Σ)) space per outer iteration. For `n = 10^5` we really don't want that.

So the question is: why does the brute force waste work? When we advance `i` by one, we're throwing away a bunch of information we already collected for `i-1`. Can we reuse it?

----------------------------------------

## Step 3: The "Window" Idea

Let's think about it as a window `[l, r]` that slides across the string. The window always holds a substring with unique characters. We grow `r` whenever we can, and we shrink `l` whenever we *must*.

- **When can we grow `r`?** When adding `s[r]` keeps all characters unique in the window.
- **When must we shrink `l`?** When `s[r]` is already somewhere in the window — then we need to kick out the old occurrence of `s[r]` by moving `l` forward.

Here's the beautiful part: `l` only ever moves forward. It never moves backward. So across the whole run, `l` advances at most `n` times and `r` advances exactly `n` times. Total work: O(n).

Why doesn't `l` move backward? Because shrinking from the left only removes elements. Once we've confirmed the window `[l, r]` has unique characters, all its sub-windows do too — so moving `l` back couldn't help.

----------------------------------------

## Step 4: How to Detect a Duplicate Efficiently

When we want to add `s[r]`, we need to check: is `s[r]` already in the window `[l, r-1]`?

A hashmap / array of "last seen index" answers this in O(1):

- `last[c]` = the most recent index at which character `c` was seen, or `-1` if never.
- If `last[s[r]] >= l`, then `s[r]` is inside the window. We must shrink: set `l = last[s[r]] + 1`.
- Then update `last[s[r]] = r` and continue.

After each step, the window `[l, r]` has unique characters by construction, so we record `best = max(best, r - l + 1)`.

This is a **sliding window** — two pointers both moving forward, with a hashmap maintaining a per-character "last seen" index.

----------------------------------------

## Step 5: Dry Run on "abcabcbb"

I'll track `l`, `r`, `last`, and `best`.

```
Initially: l = 0, last = all -1, best = 0.

r = 0, s[r] = 'a'. last['a'] = -1 < 0 = l. No shrink.
       Update last['a'] = 0. Window = "a". best = 1.

r = 1, s[r] = 'b'. last['b'] = -1. No shrink.
       last['b'] = 1. Window = "ab". best = 2.

r = 2, s[r] = 'c'. last['c'] = -1. No shrink.
       last['c'] = 2. Window = "abc". best = 3.

r = 3, s[r] = 'a'. last['a'] = 0 >= l = 0. SHRINK. l = 0 + 1 = 1.
       last['a'] = 3. Window = "bca". best = max(3, 3) = 3.

r = 4, s[r] = 'b'. last['b'] = 1 >= l = 1. SHRINK. l = 1 + 1 = 2.
       last['b'] = 4. Window = "cab". best = 3.

r = 5, s[r] = 'c'. last['c'] = 2 >= l = 2. SHRINK. l = 3.
       last['c'] = 5. Window = "abc" (indices 3..5). best = 3.

r = 6, s[r] = 'b'. last['b'] = 4 >= l = 3. SHRINK. l = 5.
       last['b'] = 6. Window = "cb" (indices 5..6). best = 3.

r = 7, s[r] = 'b'. last['b'] = 6 >= l = 5. SHRINK. l = 7.
       last['b'] = 7. Window = "b" (index 7). best = 3.
```

Final answer: **3**. Matches the expected result.

Notice one subtle point: when we shrink, we don't manually remove entries from `last`. We just set `l` past the old occurrence. The `last[c] >= l` check is doing double duty — it implicitly ignores occurrences that are now outside the window. That's cleaner than actively cleaning up `last`.

----------------------------------------

## Step 6: The Correctness Argument

Let's convince ourselves this works.

**Claim 1:** After processing index `r`, the window `[l, r]` contains only unique characters.

*Proof:* Induction on `r`. Base case `r = 0` trivial. For the inductive step, suppose after `r-1` the window `[l_old, r-1]` is unique. At step `r`, we check if `s[r]` was seen at index `last[s[r]]`. If `last[s[r]] >= l_old`, `s[r]` is in the window, so we set `l = last[s[r]] + 1`, removing the old occurrence. The new window `[l, r]` has `s[r]` appearing exactly once (at position `r`), and by induction every other character appears exactly once too. ✓

**Claim 2:** `l` never moves backward.

*Proof:* When we shrink, `l_new = last[s[r]] + 1`. But `last[s[r]]` records an index `≥ l_old` (if the character is in the current window) — otherwise we wouldn't have shrunk. So `l_new ≥ l_old + 1 > l_old`. Monotonic forward. ✓

**Claim 3:** Total work is O(n).

*Proof:* `r` moves from 0 to n-1. `l` moves monotonically from 0 to at most n. Each pointer takes at most n steps. ✓

----------------------------------------

## Step 7: Complexity

Time: **O(n)** by the monotonicity argument above.
Space: **O(Σ)** where Σ is the alphabet size (256 for ASCII). Effectively constant.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int lengthOfLongestSubstring(string s) {
    vector<int> last(256, -1);
    int l = 0, best = 0;
    for (int r = 0; r < (int)s.size(); ++r) {
        if (last[s[r]] >= l) {
            l = last[s[r]] + 1;       // kick out the old occurrence
        }
        last[s[r]] = r;
        best = max(best, r - l + 1);
    }
    return best;
}
```

A small implementation detail: I use an array of size 256 (one slot per ASCII code) instead of `unordered_map<char, int>` because it's faster and simpler when the alphabet is small. For Unicode you'd want the hashmap.

----------------------------------------

## Step 9: Follow-up Questions

- **What if we allow at most `k` distinct characters?** Track count-per-char in the window. Shrink `l` while the number of distinct chars exceeds `k`.
- **What if we allow each char to appear at most `k` times?** Same structure, but track per-char counts and shrink while any count exceeds `k`.
- **Longest substring with all characters identical.** Much simpler — just count consecutive runs.
- **Can you reconstruct the actual substring, not just the length?** Yes — when you update `best`, also snapshot `l` and `r`. At the end, `s.substr(bestL, bestLen)`.
- **What if the string is streamed and you see each character once?** The algorithm already processes one character at a time — it works as-is, as long as you can keep the hashmap in memory.
