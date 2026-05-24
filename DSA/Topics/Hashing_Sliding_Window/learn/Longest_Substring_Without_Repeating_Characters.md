# Longest Substring Without Repeating Characters — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Longest_Substring_Without_Repeating_Characters.md`](../Longest_Substring_Without_Repeating_Characters.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/longest-substring-without-repeating-characters/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~25 minutes. **This is THE introduction to the variable-size sliding window.** The shape — two forward-moving pointers, grow `r` while we can, shrink `l` while we must — is the most useful string/array technique you'll learn after frequency counting. Master this and you've unlocked Minimum Window Substring, Find All Anagrams, Longest Repeating Character Replacement, and many more.

**Map of this file (11 short sections):**

1. Read the problem
2. The natural brute force
3. Why brute force wastes work
4. The pivot — slide a window
5. The "last seen" trick (no need to clear the map)
6. Why `l` only moves forward (the monotonicity argument)
7. Why the algorithm is O(n)
8. Code
9. Trace it
10. Common pitfalls
11. The shape — sliding window template

---

## 1. Read the problem

Given a string `s`, find the **length of the longest substring** in which **every character appears at most once**.

> **Mini-refresher: substring vs subsequence.**
>
> **Substring** = a CONTIGUOUS slice. `s[l..r]` for some `l ≤ r`. The characters are next to each other in the original string.
>
> **Subsequence** = characters in order but possibly with gaps. `s[i_1], s[i_2], ..., s[i_k]` where `i_1 < i_2 < ... < i_k`.
>
> For `s = "abcabcbb"`:
> - `"abc"` is a SUBSTRING (positions 0, 1, 2 — contiguous).
> - `"acb"` is NOT a substring (would require positions 0, 2, 3 — but that skips and reorders).
> - `"abcb"` is NOT a substring of length 4 (would require non-contiguous chars).
>
> This problem asks for the SUBSTRING. Always contiguous.

**Example 1:** `s = "abcabcbb"`. Possible substrings without repeated characters:

- `"abc"` (positions 0-2). All distinct. Length 3.
- `"bca"` (positions 1-3). All distinct. Length 3.
- `"cab"` (positions 2-4). All distinct. Length 3.
- ... longer substrings always end up repeating some character.

Longest: **3**.

**Example 2:** `s = "bbbbb"`. Any 2+ character substring would have repeated `b`. Longest distinct: just `"b"`, length 1.

**Example 3:** `s = "pwwkew"`. Try:

- `"pw"` (length 2, distinct).
- `"pww"` — has two `w`s, NOT distinct.
- `"wke"` (positions 2-4) — distinct. Length 3.
- `"kew"` (positions 3-5) — distinct. Length 3.

Longest: **3**. Note `"pwke"` is NOT a substring (would need positions 0, 1, 3, 4 — not contiguous).

---

## 2. The natural brute force

For each starting position `i`, walk right adding characters until we hit a duplicate. Record the length. Repeat for every `i`.

```cpp
int lengthOfLongestSubstring(string s) {
    int n = s.size();
    int best = 0;
    for (int i = 0; i < n; i++) {
        unordered_set<char> seen;
        for (int j = i; j < n; j++) {
            if (seen.count(s[j])) break;
            seen.insert(s[j]);
        }
        best = max(best, (int)seen.size());
    }
    return best;
}
```

Two nested loops. Outer is O(n), inner can be O(n) per outer. **Worst case O(n²)** time, O(min(n, alphabet)) space per inner iteration.

For `n = 5 × 10⁴`, that's `2.5 × 10⁹` ops → TLE.

---

## 3. Why brute force wastes work

Suppose at `i = 0` we walked all the way to `j = 5` before hitting a repeat. The substring `s[0..4]` has 5 distinct characters.

When we restart at `i = 1`, we re-add `s[1], s[2], s[3], s[4]` to the set — characters we ALREADY know are distinct from each other! We're recomputing things.

**Pivot question:** is there a way to "shift" the start of the window from `i` to `i + 1` without rebuilding the set from scratch?

---

## 4. The pivot — slide a window

> **Mini-refresher: what's a sliding window?**
>
> A **sliding window** is a substring `s[l..r]` (contiguous) where both pointers `l` and `r` move forward through the string. The window's contents change over time — sometimes growing (extend `r`), sometimes shrinking (advance `l`).
>
> Typical structure:
>
> ```
> l = 0
> for r = 0 .. n-1:
>     1. Add s[r] to the window's tracked state.
>     2. While the window is "invalid" (violates some condition):
>         remove s[l] from tracked state
>         l++
>     3. Record the window's metric if it's "best so far."
> ```
>
> The "tracked state" is usually a frequency map or a set. The "invalid" condition is problem-specific.

For OUR problem:

- **The window** is `s[l..r]`. We want it to always contain DISTINCT characters.
- **The state** is a set of characters currently in the window (we'll improve this to a "last seen index map" in the next section).
- **The invariant** to maintain: every character in `s[l..r]` appears exactly once.

The sliding-window template:

```
l = 0
inWindow = empty set
best = 0

for r = 0 .. n-1:
    while s[r] is already in inWindow:
        remove s[l] from inWindow
        l += 1
    add s[r] to inWindow
    best = max(best, r - l + 1)

return best
```

Each step:

1. Look at the next character `s[r]`.
2. If it's already in the window, shrink the left side until the duplicate is gone.
3. Now we can safely add `s[r]`. The window is again valid.
4. Record the new length.

This is O(n) — see section 7 for why.

---

## 5. The "last seen" trick (no need to clear the map)

The naive sliding-window code above uses a set, with operations to add and remove. There's a slicker version using a **last-seen-index map**.

> **Mini-refresher: "last seen index" idea.**
>
> Instead of a set tracking "which characters are in the window," maintain a map `last[c] = the most recent index where c was seen` (or `-1` if never seen).
>
> When we encounter `s[r] = c`:
> - If `last[c] >= l` (i.e., the previous occurrence is INSIDE the current window `[l, r-1]`), there's a duplicate. We must shrink to exclude that previous occurrence: set `l = last[c] + 1`.
> - Otherwise (previous occurrence is outside the window, or `c` was never seen), no shrink needed.
>
> Update `last[c] = r`.
>
> Why is this better than the set version? **We don't need to "remove" anything from the map.** The `last[c] >= l` check implicitly ignores stale entries (characters that USED to be in the window but are now outside).

The cleaner algorithm:

```
last = map<char, int>, all defaulting to -1
l = 0
best = 0

for r = 0 .. n-1:
    if last[s[r]] >= l:
        l = last[s[r]] + 1            # shrink past the duplicate
    last[s[r]] = r
    best = max(best, r - l + 1)

return best
```

The shrink is a JUMP, not a one-step-at-a-time advance. When we detect a duplicate, we can move `l` straight past the old occurrence in O(1).

---

## 6. Why `l` only moves forward (the monotonicity argument)

> **Claim:** the pointer `l` never moves backward.

**Why?** When we shrink, we set `l = last[s[r]] + 1`. The previous `l` was some value `l_old`. We ONLY shrink when `last[s[r]] >= l_old` (the duplicate is in the current window). So:

```
l_new = last[s[r]] + 1 >= l_old + 1 > l_old
```

`l_new` is strictly greater than `l_old`. The pointer moves forward.

This monotonicity is what makes the algorithm O(n): both `l` and `r` move forward at most `n` times total. Each move is O(1) work.

---

## 7. Why the algorithm is O(n)

> **Total work:**
>
> - `r` moves from 0 to `n - 1`. Each `r`-step does O(1) work (one map lookup, one update, one max comparison).
> - `l` moves forward at most `n` times overall (it never moves back; can advance at most `n − 1` times).
>
> **Total: O(n).**

This is one of the cleanest "two-forward-pointers" analyses. We could have stated it as: each of the `n` characters is "added to the window" once (by `r` passing over it) and "removed from the window" at most once (by `l` passing over it). Each add/remove is O(1). Total: O(n).

---

## 8. Code

**C++ (fixed-size ASCII array — fastest for English-only inputs):**

```cpp
int lengthOfLongestSubstring(string s) {
    vector<int> last(256, -1);                    // ASCII; each char index → last seen index
    int l = 0;
    int best = 0;

    for (int r = 0; r < (int)s.size(); r++) {
        if (last[(unsigned char)s[r]] >= l) {     // duplicate in window?
            l = last[(unsigned char)s[r]] + 1;    // shrink past old occurrence
        }
        last[(unsigned char)s[r]] = r;            // update last-seen
        best = max(best, r - l + 1);              // record length
    }
    return best;
}
```

The `(unsigned char)` cast is defensive in case `s` contains characters > 127. Without it, signed char would be a negative index.

**C++ (hashmap version — works for arbitrary characters):**

```cpp
int lengthOfLongestSubstring(string s) {
    unordered_map<char, int> last;
    int l = 0;
    int best = 0;

    for (int r = 0; r < (int)s.size(); r++) {
        auto it = last.find(s[r]);
        if (it != last.end() && it->second >= l) {
            l = it->second + 1;
        }
        last[s[r]] = r;
        best = max(best, r - l + 1);
    }
    return best;
}
```

**Python:**

```python
def lengthOfLongestSubstring(s):
    last = {}
    l = 0
    best = 0
    for r, c in enumerate(s):
        if c in last and last[c] >= l:
            l = last[c] + 1
        last[c] = r
        best = max(best, r - l + 1)
    return best
```

**JavaScript:**

```javascript
function lengthOfLongestSubstring(s) {
    const last = new Map();
    let l = 0, best = 0;
    for (let r = 0; r < s.length; r++) {
        const c = s[r];
        if (last.has(c) && last.get(c) >= l) {
            l = last.get(c) + 1;
        }
        last.set(c, r);
        best = Math.max(best, r - l + 1);
    }
    return best;
}
```

All O(n) time, O(min(n, alphabet)) space.

---

## 9. Trace it

**`s = "abcabcbb"`:**

```
last = {}.  l = 0.  best = 0.

r = 0, c = 'a':
    last['a'] not in map (or = -1). No shrink.
    last['a'] = 0.
    best = max(0, 0 - 0 + 1) = 1.    window = "a"

r = 1, c = 'b':
    last['b'] not in map. No shrink.
    last['b'] = 1.
    best = 2.                         window = "ab"

r = 2, c = 'c':
    No shrink.
    last['c'] = 2.
    best = 3.                         window = "abc"

r = 3, c = 'a':
    last['a'] = 0. 0 >= l=0?  Yes.  Shrink: l = 0 + 1 = 1.
    last['a'] = 3.
    best = max(3, 3 - 1 + 1) = 3.    window = "bca"

r = 4, c = 'b':
    last['b'] = 1. 1 >= l=1?  Yes.  Shrink: l = 2.
    last['b'] = 4.
    best = max(3, 4 - 2 + 1) = 3.    window = "cab"

r = 5, c = 'c':
    last['c'] = 2. 2 >= l=2?  Yes.  Shrink: l = 3.
    last['c'] = 5.
    best = 3.                         window = "abc"

r = 6, c = 'b':
    last['b'] = 4. 4 >= l=3?  Yes.  Shrink: l = 5.
    last['b'] = 6.
    best = 3.                         window = "cb"

r = 7, c = 'b':
    last['b'] = 6. 6 >= l=5?  Yes.  Shrink: l = 7.
    last['b'] = 7.
    best = 3.                         window = "b"

Return best = 3.  ✓
```

Watch `l`: it goes `0 → 0 → 0 → 1 → 2 → 3 → 5 → 7` — monotonically increasing. Each shrink is a JUMP (not a one-step move) made possible by the last-seen-index map.

**`s = "pwwkew"`:**

```
r=0 'p': last['p']=0. best=1. window "p"
r=1 'w': last['w']=1. best=2. window "pw"
r=2 'w': last['w']=1 >= l=0. SHRINK l=2. last['w']=2. best=max(2, 2-2+1=1)=2. window "w"
r=3 'k': last['k']=3. best=2 (2)... wait length = 3-2+1=2. best=2. window "wk"
r=4 'e': last['e']=4. length=3-2+1=3. best=3. window "wke"
r=5 'w': last['w']=2 >= l=2. SHRINK l=3. last['w']=5. length=5-3+1=3. best=3. window "kew"

Return 3.  ✓
```

The shrink at `r=2` correctly jumps past the duplicate `'w'`. The shrink at `r=5` jumps past the OLD `'w'` (which was at index 2). Both jumps move `l` forward by ONE — coincidentally — but in other inputs `l` could jump by many positions at once.

---

## 10. Common pitfalls

1. **Forgetting the `last[c] >= l` guard.** Without it, an OLD occurrence of `c` (outside the current window) would incorrectly trigger a shrink — moving `l` BACKWARD. Always check that the old occurrence is INSIDE the window.

2. **Trying to remove characters from the map when shrinking.** The "last seen index" trick avoids the need to clean up. The `>= l` check handles staleness implicitly. (If you went with the set version, you DO need to remove characters as `l` advances.)

3. **Off-by-one in window length.** Length is `r - l + 1` (both endpoints inclusive). NOT `r - l`. Easy to slip up if you're used to half-open intervals.

4. **Updating `last` BEFORE the shrink check.** If you set `last[c] = r` before checking the old value, you've lost the information about where it was previously. Order matters: check first, then update.

5. **Using `set` instead of `last-index map`.** Set works but requires explicit removal during shrink. Last-index map is cleaner and equally fast.

6. **Confusing this with "longest substring with at most K distinct."** Different problem (K-distinct uses a count-per-char map and shrinks while distinct count > K). The pattern is similar but not identical.

---

## 11. The shape — sliding window template

The variable-size sliding window template:

```
l = 0
state = some structure tracking the current window's contents

for r = 0 .. n-1:
    # 1. Update state to include s[r]
    add s[r] to state

    # 2. While the window is INVALID, shrink from the left
    while window-violates-invariant(state):
        remove s[l] from state
        l += 1

    # 3. Now the window [l, r] is valid; record its metric
    update_answer(r - l + 1, or whatever the metric is)
```

The variations:

| Problem | "Invariant" | State | Metric |
|---|---|---|---|
| **This problem** | every char appears ≤ 1 time | set of chars OR last-seen map | length |
| Longest Substring with At Most K Distinct | ≤ K distinct chars in window | char → count map; count of distinct | length |
| Longest Substring with Each Char ≤ K Times | each char count ≤ K | char → count map | length |
| Longest Repeating Character Replacement | (window length − max char count) ≤ K | char → count map | length |
| Minimum Window Substring | window contains all chars of t (with counts) | need/have/matched/required | window-length (minimize) |
| Find All Anagrams in a String | window matches t's frequency exactly | need/have counts | record positions when matched |

**Pattern to internalize:**

> "Sliding window: two pointers walking forward. Grow `r` to extend; shrink `l` when the window violates the problem's invariant. State tracking is a frequency map (or set, or last-index map). Total work O(n) by monotonicity."

Once you have this template, half of "substring" and "subarray" problems become "fill in: what's the state? what's the invariant? what's the metric?"

---

> **Self-check — the question to ask next time.**
>
> When you face a problem asking for the **longest (or shortest) contiguous substring/subarray with some property**, before nesting loops, ask:
>
> > **"Can I use a sliding window? What's the invariant (the property the window must satisfy)? What state do I track (frequency map, set, count)? When does adding `s[r]` make the window invalid, and how do I shrink `l` to restore validity?"**
>
> If yes, you've turned O(n²) into O(n).

---

## Cross-references

- **Reference card (post-mastery):** [`../Longest_Substring_Without_Repeating_Characters.md`](../Longest_Substring_Without_Repeating_Characters.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Anagram.md`](./Valid_Anagram.md) — frequency-counting building block.
  - Coming next: [`Minimum_Window_Substring.md`](./Minimum_Window_Substring.md) — the hardest sliding window in this topic; adds a "satisfied" counter.
  - Coming later: Find All Anagrams in a String, Longest Substring with K Distinct, Longest Repeating Character Replacement — all use this template.
