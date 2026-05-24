# Minimum Window Substring — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Minimum_Window_Substring.md`](../Minimum_Window_Substring.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/minimum-window-substring/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~40 minutes. **This is the hardest sliding-window problem in standard interviews** — the algorithm involves a "satisfaction counter" alongside the frequency map. Once you understand WHY the satisfaction counter is needed (and why it's faster than just comparing counts directly), you've internalized the deepest pattern in sliding-window problems. **Read [`Longest_Substring_Without_Repeating_Characters.md`](./Longest_Substring_Without_Repeating_Characters.md) first** so the basic sliding-window template is in your head.

**Map of this file (13 short sections):**

1. Read the problem
2. Tiny cases by hand
3. The brute force
4. The sliding window idea
5. The challenge — how to check "window contains all of t"
6. Naive check vs efficient counter
7. Introducing `need`, `have`, `matched`, `required`
8. Why `matched` counts DISTINCT chars satisfied (not total)
9. The grow / shrink rhythm
10. Code
11. Trace it
12. Common pitfalls
13. The shape — variable window with satisfaction counter

---

## 1. Read the problem

You're given two strings `s` and `t`. Return the **shortest substring of `s`** that contains **every character of `t`** (counting duplicates). If no such window exists, return `""`.

**Important details:**

- "Substring" = contiguous slice of `s`.
- "Every character of `t` (counting duplicates)" = the window must have at least as many of each character as `t` does. If `t = "AABC"`, the window must have ≥ 2 A's, ≥ 1 B, ≥ 1 C.
- The window can contain EXTRA characters; that's fine. It just has to have ALL of t's characters present.

**Example 1:** `s = "ADOBECODEBANC"`, `t = "ABC"`.

We need a window of `s` containing at least 1 A, 1 B, 1 C.

- `"ADOBEC"` (positions 0-5) has A, B, C, plus extras (D, O, E). Length 6. Valid.
- `"BANC"` (positions 9-12) has B, A, N, C. Has A, B, C. Length 4. Valid.

**Shortest valid window: `"BANC"`. Length 4.**

**Example 2:** `s = "a"`, `t = "a"`. Window is `"a"`. Return `"a"`.

**Example 3:** `s = "a"`, `t = "aa"`. We need TWO `a`s, but `s` only has one. No valid window. Return `""`.

---

## 2. Tiny cases by hand

`s = "aabbc"`, `t = "abc"`. Need 1 a, 1 b, 1 c.

Windows of `s`:

- Length 5: `"aabbc"` — has a, b, c (with extras). Valid.
- Length 4: `"aabb"` (no c), `"abbc"` (has a, b, c). `"abbc"` valid.
- Length 3: `"aab"` (no c), `"abb"` (no c), `"bbc"` (no a). None valid.

Shortest: `"abbc"`, length 4.

`s = "aab"`, `t = "aab"`. Need 2 a's, 1 b. Only window with all those: `"aab"` itself. Return `"aab"`.

---

## 3. The brute force

Try every substring of `s` and check whether it contains all of `t`.

```cpp
string minWindow(string s, string t) {
    int n = s.size();
    string best = "";
    for (int i = 0; i < n; i++) {
        for (int j = i; j < n; j++) {
            string window = s.substr(i, j - i + 1);
            if (containsAllChars(window, t)) {
                if (best.empty() || (j - i + 1) < (int)best.size()) {
                    best = window;
                }
            }
        }
    }
    return best;
}
```

- Outer + inner loops: O(n²) substrings.
- `containsAllChars` check: O(window length + |t|).
- Total: **O(n³)** roughly. Way too slow.

We need a smarter approach — and that's the sliding window.

---

## 4. The sliding window idea

Imagine a window `[l, r]` in `s`. As `r` moves right, the window grows — eventually it contains all of `t`'s characters. The moment that happens, the window is **VALID**. We want to:

1. **Record the valid window's length** as a candidate answer.
2. **Try to shrink from the left** to find an even shorter valid window.
3. When we can't shrink without losing validity, **grow `r` again** to find the next valid window.

Both `l` and `r` move forward only. Total work: O(n) — same monotonicity argument as the basic sliding window.

The hard part is **how do we efficiently check whether the window contains all of `t`'s characters?**

---

## 5. The challenge — how to check "window contains all of t"

We can't afford to scan the entire window every time we change it (that would make the algorithm O(n²)). We need to maintain "does the window have all of t's chars?" incrementally as we add and remove characters.

Two ideas:

**Idea A: maintain `have[c]` (count of `c` in window) and `need[c]` (count of `c` in t). Window is valid iff `have[c] >= need[c]` for EVERY c that's a key in `need`.**

The validity check itself is O(|distinct chars in t|), which is fine. But we do this check at every step of `r`, so we want it to be cheap.

**Idea B: maintain a SINGLE integer `matched` = number of distinct characters whose `have[c] >= need[c]`.**

The window is valid iff `matched == required`, where `required = number of distinct chars in t`.

Updating `matched` is O(1) per `have[c]` change — we just need to detect the "threshold crossing" (when `have[c]` reaches or drops below `need[c]`).

**Idea B is cleaner and uniformly O(1) per step.** That's what we'll use.

---

## 6. Naive check vs efficient counter

> **Mini-refresher: why "satisfaction counter" beats "compare maps."**
>
> Idea A above requires comparing two maps at every step. Even if each comparison is O(K) (where K = distinct chars in t), the constant factor is annoying — and on every grow/shrink step, we'd recompute the entire comparison.
>
> Idea B is more elegant: we maintain a single integer `matched`. It increments by 1 each time a character first crosses the "satisfied" threshold (have[c] becomes >= need[c]), and decrements by 1 each time a character first drops below it (have[c] becomes < need[c]).
>
> Then "is the window valid?" is a single comparison: `matched == required`. O(1).
>
> The key insight is that `matched` only changes at THRESHOLD CROSSINGS — not every time we add or remove a character. Most adds and removes don't change `matched` at all (they just inflate or deflate `have[c]` away from the threshold).

---

## 7. Introducing `need`, `have`, `matched`, `required`

Four pieces of state:

- **`need[c]`** — for each character `c`, how many copies are needed (= count of `c` in `t`).
- **`have[c]`** — for each character `c`, how many copies are currently in the window.
- **`matched`** — number of DISTINCT characters `c` for which `have[c] >= need[c]`. (i.e., "satisfied" characters.)
- **`required`** — number of distinct characters in `t` (the maximum possible `matched`).

**The window is valid iff `matched == required`.**

When we add `s[r]` to the window:

- `have[s[r]]++`.
- If `s[r]` is in `need` AND `have[s[r]] == need[s[r]]` (we JUST hit the threshold), increment `matched`.

When we remove `s[l]` from the window:

- `have[s[l]]--`.
- If `s[l]` is in `need` AND `have[s[l]] < need[s[l]]` (we JUST dropped below), decrement `matched`.

These are O(1) operations.

---

## 8. Why `matched` counts DISTINCT chars satisfied (not total)

A subtle point: `matched` is the number of DISTINCT characters that are "satisfied." Not the total count of matched characters.

Why? Because once `have[c]` exceeds `need[c]`, we don't get any "credit" for the extras. The character is "satisfied" — adding more doesn't make the window more valid. The window is valid iff EVERY needed character is satisfied — so we count how many distinct characters are satisfied, and compare to `required` (the total distinct needed).

This makes the threshold check clean: `matched` only changes at the EXACT moment of crossing.

> **Mini-refresher: threshold crossing.**
>
> "Threshold crossing" is when a counter just reaches or just dips below a target value. If `have[c] = 5` and `need[c] = 3`, we're well above the threshold; adding or removing a `c` doesn't cross anything.
>
> The threshold crossings happen exactly at:
> - **Add:** `have[c]` transitions from `need[c] - 1` to `need[c]`. Now satisfied.
> - **Remove:** `have[c]` transitions from `need[c]` to `need[c] - 1`. Now no longer satisfied.
>
> These are O(1) detections. Everything else (have[c] moves away from the threshold) doesn't change `matched`.

---

## 9. The grow / shrink rhythm

The full algorithm:

```
build need[] from t
required = number of distinct chars in t

have[] = empty
matched = 0
l = 0
bestLen = ∞
bestStart = 0

for r in 0..|s|-1:
    c = s[r]
    have[c]++
    if c in need and have[c] == need[c]:
        matched++

    # Try to shrink as long as window is valid
    while matched == required:
        # Record this valid window
        if r - l + 1 < bestLen:
            bestLen = r - l + 1
            bestStart = l
        # Shrink
        leftC = s[l]
        have[leftC]--
        if leftC in need and have[leftC] < need[leftC]:
            matched--
        l++

return "" if bestLen == ∞ else s[bestStart : bestStart + bestLen]
```

The structure:

1. **Outer loop**: grow `r` one step at a time.
2. **Add `s[r]`** to the window, update `have[]` and `matched`.
3. **Inner while**: while the window is valid (`matched == required`), record its length and shrink `l`.
4. Repeat.

This is the **grow-and-shrink** sliding window. Both pointers move forward only.

---

## 10. Code

**C++:**

```cpp
string minWindow(string s, string t) {
    if (t.empty() || s.size() < t.size()) return "";

    unordered_map<char, int> need;
    for (char c : t) need[c]++;
    int required = need.size();

    unordered_map<char, int> have;
    int matched = 0;
    int l = 0;
    int bestLen = INT_MAX;
    int bestStart = 0;

    for (int r = 0; r < (int)s.size(); r++) {
        char c = s[r];
        have[c]++;
        if (need.count(c) && have[c] == need[c]) {
            matched++;
        }

        while (matched == required) {
            if (r - l + 1 < bestLen) {
                bestLen = r - l + 1;
                bestStart = l;
            }
            char leftC = s[l];
            have[leftC]--;
            if (need.count(leftC) && have[leftC] < need[leftC]) {
                matched--;
            }
            l++;
        }
    }

    return bestLen == INT_MAX ? "" : s.substr(bestStart, bestLen);
}
```

**Python:**

```python
def minWindow(s, t):
    if not t or len(s) < len(t):
        return ""
    from collections import Counter
    need = Counter(t)
    required = len(need)
    have = {}
    matched = 0
    l = 0
    best_len = float('inf')
    best_start = 0

    for r, c in enumerate(s):
        have[c] = have.get(c, 0) + 1
        if c in need and have[c] == need[c]:
            matched += 1

        while matched == required:
            if r - l + 1 < best_len:
                best_len = r - l + 1
                best_start = l
            left_c = s[l]
            have[left_c] -= 1
            if left_c in need and have[left_c] < need[left_c]:
                matched -= 1
            l += 1

    return "" if best_len == float('inf') else s[best_start:best_start + best_len]
```

Both O(n + m) time where n = |s|, m = |t|.

---

## 11. Trace it

**`s = "ADOBECODEBANC"`, `t = "ABC"`:**

Build:
```
need = {A: 1, B: 1, C: 1}.   required = 3.
have = {}.   matched = 0.   l = 0.   bestLen = ∞.
```

Walk through `r`:

```
r=0 c='A':  have[A]=1. A in need, have[A] == need[A]=1. matched=1.
            matched (1) < required (3). No shrink.

r=1 c='D':  have[D]=1. D not in need. matched unchanged.

r=2 c='O':  have[O]=1. matched=1.

r=3 c='B':  have[B]=1. B in need, have[B]==1. matched=2.

r=4 c='E':  have[E]=1. matched=2.

r=5 c='C':  have[C]=1. C in need, have[C]==1. matched=3. VALID!
            
            While matched == required:
                Window length = 5 - 0 + 1 = 6. bestLen=6, bestStart=0.   ← "ADOBEC"
                Shrink left:
                    leftC = s[0] = 'A'. have[A]=0. A in need, 0 < 1. matched=2.
                    l = 1.
            Exit while.

r=6 c='O':  have[O]=2. matched=2.
r=7 c='D':  have[D]=2. matched=2.
r=8 c='E':  have[E]=2. matched=2.

r=9 c='B':  have[B]=2. B in need but have[B]=2, need[B]=1. Not a fresh match (we're ABOVE threshold). matched=2.

r=10 c='A': have[A]=1. A in need, have[A]==1 (just reached). matched=3. VALID!

             While matched == required:
                 Window length = 10 - 1 + 1 = 10. bestLen still 6 (no improvement).
                 Shrink:
                     leftC = s[1] = 'D'. have[D]=1. D not in need. matched stays.
                     l = 2.
                 Window length = 10 - 2 + 1 = 9. Still no improvement.
                 leftC = s[2] = 'O'. have[O]=1. Not in need.
                 l = 3. Length 8.
                 leftC = s[3] = 'B'. have[B]=1. B in need, 1 < 1? No (1 == 1, not strictly less).
                                                          (Actually have[B] is now 1, and need[B]=1; not "dropped below.")
                 So matched stays.
                 l = 4. Length 7.
                 leftC = s[4] = 'E'. Not in need. l=5. Length 6 — TIE.
                 leftC = s[5] = 'C'. have[C]=0. C in need, 0 < 1. matched=2.
                 l = 6.
             Exit while.

r=11 c='N': have[N]=1. matched=2.

r=12 c='C': have[C]=1. C in need, 1==1. matched=3. VALID!

             While matched == required:
                 Length = 12-6+1 = 7. Not better.
                 leftC = s[6] = 'O'. Not in need. l=7. Length 6 — TIE (we already had 6).
                 leftC = s[7] = 'D'. Not in need. l=8. Length 5. BETTER. bestLen=5, bestStart=8.   ← "EBANC"
                 leftC = s[8] = 'E'. Not in need. l=9. Length 4. BETTER. bestLen=4, bestStart=9.   ← "BANC"
                 leftC = s[9] = 'B'. have[B]=0. B in need, 0 < 1. matched=2.
                 l=10.
             Exit while.

End of loop.
Return s.substr(9, 4) = "BANC".  ✓
```

The grow-and-shrink rhythm gives us THREE candidate valid windows during the scan: `"ADOBEC"` (len 6), `"CODEBA"` (len 6), and `"BANC"` (len 4 — the answer). We update `bestLen` only when strictly smaller, so we keep `"BANC"`.

---

## 12. Common pitfalls

1. **Updating `matched` based on `have[c] > need[c]`** instead of `have[c] == need[c]`. The threshold is only crossed at equality. Using `>` would double-count or miss the crossing.

2. **Forgetting the `need.count(c)` guard.** If `c` is NOT in `need`, the check `have[c] == need[c]` would compare against `need[c] = 0` (default), and incorrectly increment `matched` when `have[c]` reached 0 (impossible to test, but the check is sloppy). Always guard: only adjust `matched` for characters that are actually in `need`.

3. **Decrementing `matched` with `<=`** instead of `<` in the shrink. When we shrink and `have[leftC]` drops, it's the EXACT transition to `need[leftC] - 1` that loses satisfaction. The strict `<` captures this; `<=` would also fire when `have[leftC]` was already below the threshold (which never happens during a valid shrink, but the code's intent should be precise).

4. **Trying to compare entire maps every step.** Using "is `have` a superset of `need`?" naively costs O(K) per step → O(n·K) total. The `matched` counter avoids this — O(1) per step.

5. **Returning the WRONG window.** Track `bestStart` AND `bestLen` together. Returning `s.substr(0, bestLen)` instead of `s.substr(bestStart, bestLen)` gives a wrong substring with the right LENGTH.

6. **Forgetting the early exit for `s.size() < t.size()`.** Saves time and avoids running through the whole `s` when no answer is possible.

7. **Trying to use `int matched` to compare to `t.size()`** instead of `required` (distinct chars). `t.size()` is the TOTAL char count, including duplicates. The right comparison is against `required` = distinct count.

---

## 13. The shape — variable window with satisfaction counter

The `need / have / matched / required` pattern is the canonical solution to **"minimum window containing a multiset of requirements."** Variations:

| Problem | What's "required" |
|---|---|
| **This problem** (Minimum Window Substring) | window contains every char of t (with counts) |
| Permutation in String (LC #567) | window EQUALS t as a frequency map (fixed-size window) |
| Find All Anagrams in a String (LC #438) | window EQUALS t (fixed-size, return all positions) |
| Substring with Concatenation of All Words (LC #30) | window contains every word in a list (fixed-size, word-level) |
| Minimum Operations to Reduce X to Zero (LC #1658) | sum-based, but same shape — find shortest window with property |

**Pattern to internalize:**

> "When the problem is **'shortest window with multi-element requirement'**, use the sliding-window template with FOUR pieces of state: `need` (target counts), `have` (current counts), `matched` (count of distinct chars currently satisfied), `required` (target distinct count). Update `matched` only at threshold crossings — never recount the whole map."

The threshold-crossing trick is the key optimization. Once you see it, you'll recognize it in load balancing, deadline scheduling, and other "satisfied / unsatisfied" tracking problems.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem asking for the **shortest contiguous window satisfying a multi-element requirement** (window contains all of X, frequencies match Y, sum meets Z, etc.), before nesting loops, ask:
>
> > **"Can I use a sliding window with a SATISFACTION COUNTER that tracks how many distinct sub-requirements are met? Increment/decrement the counter only at threshold crossings — never recount the whole state."**
>
> If yes, you've turned O(n²) or O(n³) into O(n) and earned the senior bar.

---

## Cross-references

- **Reference card (post-mastery):** [`../Minimum_Window_Substring.md`](../Minimum_Window_Substring.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Longest_Substring_Without_Repeating_Characters.md`](./Longest_Substring_Without_Repeating_Characters.md) — sliding-window prereq.
  - [`Valid_Anagram.md`](./Valid_Anagram.md) — frequency-map foundation.
  - Coming later: Find All Anagrams in a String, Permutation in String (similar shape with FIXED-size window).
