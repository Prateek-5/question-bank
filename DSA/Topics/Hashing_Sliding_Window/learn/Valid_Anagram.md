# Valid Anagram — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Valid_Anagram.md`](../Valid_Anagram.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/valid-anagram/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~15 minutes. This is **the introduction to frequency counting** — the most universal string-and-array technique you'll meet. Every later problem involving "count of distinct things in a string / window / array" uses some flavor of this.

**Map of this file (9 short sections):**

1. Read the problem
2. The natural first thought (sort and compare)
3. Why we want something better
4. The pivot — count characters instead
5. Fixed-alphabet array vs hashmap
6. Code
7. Trace it
8. Common pitfalls
9. The shape — frequency counting everywhere

---

## 1. Read the problem

You're given two strings `s` and `t`. Return `true` if `t` is an **anagram** of `s`, `false` otherwise.

**Anagram:** a rearrangement using the same characters with the same counts. Order can differ, but the multiset of characters must be identical.

**Examples:**

- `s = "anagram"`, `t = "nagaram"` → `true`. Both have 3 a's, 1 n, 1 g, 1 r, 1 m.
- `s = "rat"`, `t = "car"` → `false`. Different characters (s has `t`, t has `c`).
- `s = "aabb"`, `t = "abab"` → `true`. Both have 2 a's and 2 b's.
- `s = "ab"`, `t = "a"` → `false`. Different lengths.

**Note on case:** by default the problem is case-sensitive — `"abc"` and `"ABC"` are NOT anagrams. You'd normalize with `.toLowerCase()` if asked for case-insensitive.

> **Mini-refresher: multiset.**
>
> A "multiset" is a collection where repetitions matter. `{a, a, b}` is different from `{a, b}` even though they share the same DISTINCT elements. Anagram-equality is multiset-equality on the character collections.

---

## 2. The natural first thought (sort and compare)

If two strings are anagrams, sorting them should give the same string:

- `"anagram".sort() = "aaagmnr"`.
- `"nagaram".sort() = "aaagmnr"`.

Same → anagrams.

```cpp
bool isAnagram(string s, string t) {
    if (s.size() != t.size()) return false;
    sort(s.begin(), s.end());
    sort(t.begin(), t.end());
    return s == t;
}
```

**Time:** O(n log n) (sorting dominates).
**Space:** O(1) extra if sorted in place, otherwise O(n) for the sorted copies.

Works. Often acceptable in interviews. But there's a faster approach that also generalizes to other problems (group anagrams, sliding-window anagram detection, etc.).

---

## 3. Why we want something better

For strings of length up to 5×10⁴ (LeetCode's constraint), O(n log n) gives ~5×10⁵ ops — fast enough. So in this PROBLEM the sort approach is fine.

But the **technique we want to teach** is more general. Sorting destroys the "frequency" information; we recover the answer by comparing sorted strings. There's a more direct route: **compute the character frequencies directly and compare them.**

That's the pivot we'll take. The reason: the technique transfers — once you see frequency counting, you'll reach for it in problems where sorting wouldn't help.

---

## 4. The pivot — count characters instead

Definition of anagram in plain language: "same character counts."

Direct algorithm:

```
1. Count how many of each character is in s.
2. Count how many of each character is in t.
3. Compare the two counts. Equal → anagrams.
```

Or more efficiently in one pass:

```
1. Make a "counter" with one slot per character.
2. For each character in s: increment.
3. For each character in t: decrement.
4. If all slots are 0 at the end → anagrams.
```

The increment-and-decrement trick is cute: we're computing the **difference** in character counts. Anagrams have a zero difference everywhere.

> **Why does the increment-decrement trick work?**
>
> For each character `c`:
> - Increment by `count_in_s(c)`.
> - Decrement by `count_in_t(c)`.
>
> Final value: `count_in_s(c) − count_in_t(c)`. If both strings have the SAME count of `c`, this is 0.
>
> If for EVERY character the final value is 0, the strings have equal character counts → anagrams.

---

## 5. Fixed-alphabet array vs hashmap

We need a data structure to hold the counts. Two options based on what characters can appear.

**Option A: lowercase English letters only (26 chars).**

Use an integer array of size 26: `cnt[26]`. Index character `c` as `cnt[c - 'a']`. Cheap, cache-friendly, no hashing overhead.

```cpp
int cnt[26] = {0};
for (char c : s) cnt[c - 'a']++;
```

> **Mini-refresher: `c - 'a'` to index by letter.**
>
> Characters in C++ (and most languages) are integer codes underneath. `'a'` is `97`, `'b'` is `98`, ..., `'z'` is `122`. So `c - 'a'` gives `0` for `'a'`, `1` for `'b'`, etc. — a clean 0-indexed slot.
>
> This is the standard idiom for "treat lowercase English letters as array indices."

**Option B: arbitrary characters (Unicode, mixed case, symbols).**

Use a hashmap: `unordered_map<char, int>` (C++) or `dict` (Python) or `Map` (JS). Slower per operation (hashing overhead), but works for any character.

```cpp
unordered_map<char, int> cnt;
for (char c : s) cnt[c]++;
```

For LeetCode #242 (lowercase English only), the array is preferred. For broader inputs, use the hashmap.

---

## 6. Code

**Array-based (LeetCode #242, lowercase a-z):**

```cpp
bool isAnagram(string s, string t) {
    if (s.size() != t.size()) return false;

    int cnt[26] = {0};
    for (char c : s) cnt[c - 'a']++;
    for (char c : t) cnt[c - 'a']--;

    for (int x : cnt) {
        if (x != 0) return false;
    }
    return true;
}
```

Eight lines.

**Hashmap-based (Unicode-safe):**

```cpp
bool isAnagram(string s, string t) {
    if (s.size() != t.size()) return false;

    unordered_map<char, int> cnt;
    for (char c : s) cnt[c]++;

    for (char c : t) {
        if (--cnt[c] < 0) return false;     // early exit on negative
    }
    return true;
}
```

The early-exit `if (--cnt[c] < 0)` is a small optimization: if any character in `t` "overflows" the count from `s`, they can't be anagrams.

**Python:**

```python
def isAnagram(s, t):
    if len(s) != len(t):
        return False
    from collections import Counter
    return Counter(s) == Counter(t)
```

`Counter` is Python's built-in frequency map. The comparison `Counter == Counter` checks "same keys, same values."

Or manual:

```python
def isAnagram(s, t):
    if len(s) != len(t): return False
    cnt = [0] * 26
    for c in s: cnt[ord(c) - ord('a')] += 1
    for c in t: cnt[ord(c) - ord('a')] -= 1
    return all(x == 0 for x in cnt)
```

**JavaScript:**

```javascript
function isAnagram(s, t) {
    if (s.length !== t.length) return false;
    const cnt = new Array(26).fill(0);
    for (const c of s) cnt[c.charCodeAt(0) - 97]++;
    for (const c of t) cnt[c.charCodeAt(0) - 97]--;
    return cnt.every(x => x === 0);
}
```

All O(n) time, O(1) space (for the fixed-alphabet versions).

---

## 7. Trace it

**`s = "anagram"`, `t = "nagaram"`:**

```
Length check: 7 == 7 ✓.
cnt = [0]*26.

Process s = "anagram":
    a: cnt[0]++  → cnt[0] = 1
    n: cnt[13]++ → cnt[13] = 1
    a: cnt[0]++  → cnt[0] = 2
    g: cnt[6]++  → cnt[6] = 1
    r: cnt[17]++ → cnt[17] = 1
    a: cnt[0]++  → cnt[0] = 3
    m: cnt[12]++ → cnt[12] = 1

cnt now: [0]=3, [6]=1, [12]=1, [13]=1, [17]=1, rest 0.

Process t = "nagaram":
    n: cnt[13]-- → 0
    a: cnt[0]--  → 2
    g: cnt[6]--  → 0
    a: cnt[0]--  → 1
    r: cnt[17]-- → 0
    a: cnt[0]--  → 0
    m: cnt[12]-- → 0

cnt now: all zeros.

Verify: all entries == 0 → return true.  ✓
```

**`s = "rat"`, `t = "car"`:**

```
Length: 3 == 3 ✓.

Process s:
    r: cnt[17]=1
    a: cnt[0]=1
    t: cnt[19]=1

Process t:
    c: cnt[2]-- → -1.   ← Already a problem.
    a: cnt[0]-- → 0.
    r: cnt[17]-- → 0.

cnt: [2]=-1, [19]=1, rest 0.

Verify: cnt[2] = -1, not zero → return false.  ✓
```

The `-1` value tells us "there's a `c` in t that's not in s" — captures the asymmetry.

---

## 8. Common pitfalls

1. **Forgetting the length check.** If `s.length != t.length`, they can't be anagrams. The frequency-count logic would still detect this (some entries would be non-zero), but the length check is faster and clearer.

2. **Using `c` directly as an array index.** `'a'` is `97`, NOT `0`. Without `c - 'a'`, you'd be accessing index 97+. Either size the array large enough (256 for ASCII), or use the subtraction. Most efficient: subtract `'a'` and size to 26.

3. **Case sensitivity.** `"Listen"` vs `"Silent"` — are they anagrams? Capital L (76) vs lowercase l (108) — different codes! By default the algorithm treats them as different. If case-insensitive is wanted, lowercase both first.

4. **Assuming `Counter == Counter` is O(1) in Python.** It's O(distinct keys), still very fast. But if you're benchmarking, know that the hash-based comparison is slower than the fixed-array comparison.

5. **Confusing "anagram" with "permutation" or "subsequence".** Anagram = same multiset. Permutation = same multiset arranged in a specific way (often same as anagram). Subsequence = the characters appear in order but not necessarily contiguous — entirely different problem.

6. **Trying to use a `set` (not a `map`).** A set tracks PRESENCE, not COUNT. For `"aab"` and `"abb"`, both have the same character SET `{a, b}` but different counts. A set says they're "anagrams" — WRONG.

---

## 9. The shape — frequency counting everywhere

Frequency counting (also called "character counting" or "multiset comparison") is THE workhorse for string and array problems:

| Problem | Frequency used for |
|---|---|
| **This problem** (Valid Anagram) | compare two strings |
| Group Anagrams | hash each string by its frequency vector; group |
| Find All Anagrams in a String | sliding window with frequency match |
| Permutation in String | sliding window with frequency match |
| Minimum Window Substring | frequency comparison + "need / have" counters |
| Top K Frequent Elements | frequency map + heap or bucket sort |
| First Unique Character in a String | frequency map; first letter with count 1 |
| Subarray Sum Equals K | prefix-sum frequency map |

**Pattern to internalize:**

> "When comparing strings (or arrays) by their CONTENT regardless of ORDER, build frequency maps and compare them. The map can be a fixed array (small alphabet) or a hashmap (arbitrary characters). Increment-and-decrement is a slick way to verify equality in a single combined pass."

The deeper lesson: a string's **canonical form** can be its **frequency vector**, not its sorted-letters string. Many problems become simpler when you stop thinking "string of characters" and start thinking "vector of counts."

---

> **Self-check — the question to ask next time.**
>
> When you face a problem asking about the **character content** of one or more strings (anagrams, permutations, "do these contain the same letters", "find a window with these letters"), before sorting, ask:
>
> > **"Can I represent each string as a FREQUENCY MAP / VECTOR and compare those instead?"**
>
> If yes, you've turned O(n log n) into O(n) AND opened the door to sliding-window techniques that sorting can't easily replicate.

---

## Cross-references

- **Reference card (post-mastery):** [`../Valid_Anagram.md`](../Valid_Anagram.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next in this topic: Valid_Sudoku (multi-key frequency tracking), Subarray_Sum_Equals_K (the prefix-sum + frequency-map combo)
  - Coming later: First Unique Character in a String (Maps & Sets in JS section uses the same frequency-counting pattern); Group Anagrams (Hash topic in some configurations); Minimum Window Substring (sliding window + frequency map).
