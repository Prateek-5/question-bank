# Valid Anagram

**Problem Link:**
https://leetcode.com/problems/valid-anagram/

**Topic:**
Hashing / Sliding Window

----------------------------------------

## Step 1: Define Anagram Clearly

Two strings are **anagrams** if one is a rearrangement of the other — same characters, same counts, possibly different order. Case matters (so `"abc"` is not an anagram of `"ABC"` by default).

Examples:
- `"anagram"` and `"nagaram"` — both have 3 a's, 1 n, 1 g, 1 r, 1 m. Anagrams. ✓
- `"rat"` and `"car"` — `"rat"` has r-a-t; `"car"` has c-a-r. Different letters. Not anagrams. ✗
- `"aabb"` and `"abab"` — both have 2 a's and 2 b's. Anagrams. ✓

So the definition is: as multisets of characters, they're equal.

----------------------------------------

## Step 2: First Idea — Sort and Compare

If I sort both strings alphabetically, anagrams become identical after sorting:
- `"anagram"` → `"aaagmnr"`.
- `"nagaram"` → `"aaagmnr"`.

Same string after sort → anagram. Different → not.

```cpp
bool isAnagram(string s, string t) {
    if (s.size() != t.size()) return false;
    sort(s.begin(), s.end());
    sort(t.begin(), t.end());
    return s == t;
}
```

Works. O(n log n) time. That's fine for most inputs. But we might be able to do better — and more importantly, the sorted-comparison trick doesn't generalize to related problems (like grouping anagrams or sliding-window anagram detection).

----------------------------------------

## Step 3: Count Characters Instead

Anagrams have the same **character counts**. That's a direct definition, so let's use it.

Count every character in `s` and every character in `t`. Compare the two counts. If they match → anagram.

If the alphabet is fixed (ASCII lowercase, 26 letters), we can use a 26-length integer array. Increment for `s`, decrement for `t`. If all entries are 0 at the end → anagram.

```cpp
bool isAnagram(string s, string t) {
    if (s.size() != t.size()) return false;
    int cnt[26] = {0};
    for (char c : s) cnt[c - 'a']++;
    for (char c : t) cnt[c - 'a']--;
    for (int x : cnt) if (x != 0) return false;
    return true;
}
```

Single pass through each string: O(n). The array-compare at the end is O(1) (fixed alphabet size).

----------------------------------------

## Step 4: Why the Length Check Matters

Before counting, we check `s.size() == t.size()`. This is essential. Why?

If one string is longer than the other, they can't be anagrams (different total character counts). Skipping this check isn't wrong — the final "all zeros" test would still fail — but it's faster to bail early.

Also, without the length check, a subtle bug can emerge: if you process one string fully and another partially, the counts don't reflect the true state. The length check makes the semantics clean.

----------------------------------------

## Step 5: Trace on `"anagram"` vs `"nagaram"`

```
cnt initial: all zeros.

Process "anagram":
  a: cnt[0]++ → 1
  n: cnt[13]++ → 1
  a: cnt[0]++ → 2
  g: cnt[6]++ → 1
  r: cnt[17]++ → 1
  a: cnt[0]++ → 3
  m: cnt[12]++ → 1

After s: cnt[0]=3, cnt[6]=1, cnt[12]=1, cnt[13]=1, cnt[17]=1. Others 0.

Process "nagaram":
  n: cnt[13]-- → 0
  a: cnt[0]-- → 2
  g: cnt[6]-- → 0
  a: cnt[0]-- → 1
  r: cnt[17]-- → 0
  a: cnt[0]-- → 0
  m: cnt[12]-- → 0

Final cnt: all zeros. Return true. ✓
```

And `"rat"` vs `"car"`:
```
After s: cnt[17]=1 (r), cnt[0]=1 (a), cnt[19]=1 (t).
After t: cnt[2]-- (c) = -1. cnt[0]-- = 0. cnt[17]-- = 0.
Final: cnt[2]=-1, cnt[19]=1.
Non-zero. Return false. ✓
```

Works nicely.

----------------------------------------

## Step 6: What If the Alphabet Is Larger?

If characters can be arbitrary Unicode (or just beyond `a-z`), swap the fixed-size array for a hashmap:

```cpp
bool isAnagram(string s, string t) {
    if (s.size() != t.size()) return false;
    unordered_map<char, int> cnt;
    for (char c : s) cnt[c]++;
    for (char c : t) if (--cnt[c] < 0) return false;
    return true;
}
```

The "short-circuit on negative" is a small optimization: as soon as we over-decrement any character, we know they're not anagrams.

For ASCII problems, the 26-length array is faster than the hashmap (better cache behavior, no hashing overhead). For Unicode, we need the hashmap.

----------------------------------------

## Step 7: Name It

This is **frequency counting**, and it's the bread and butter of string problems. Once you've internalized it, you'll spot it everywhere: group anagrams, find all anagrams in a string, longest substring with at most k distinct characters, minimum window substring.

The pattern: represent a string (or a window) by its character-count vector, and compare vectors.

----------------------------------------

## Step 8: Complexity

Time: **O(n)**, where n is the string length.
Space: **O(1)** for fixed alphabet (26 letters), or **O(k)** for unique characters if using a hashmap.

Faster than sorting (O(n log n)) and uses less space than storing sorted copies.

----------------------------------------

## Step 9: C++ Implementation

```cpp
bool isAnagram(string s, string t) {
    if (s.size() != t.size()) return false;
    int cnt[26] = {0};
    for (char c : s) cnt[c - 'a']++;
    for (char c : t) cnt[c - 'a']--;
    for (int x : cnt) if (x != 0) return false;
    return true;
}
```

Clean and direct. The `cnt[c - 'a']` indexing converts a lowercase letter to an index 0..25.

----------------------------------------

## Step 10: Follow-up Questions

- **Group Anagrams.** Hash each string by its sorted form (or by its count-vector serialization) and group.
- **Find All Anagrams in a String.** Sliding window with a counts array — the window moves through the text; compare window counts to target counts.
- **Minimum Window Substring (contains all chars of t).** Similar sliding-window approach with counts.
- **Anagram with up to k character swaps allowed.** Relaxed problem; count differences more carefully.
- **Anagrams where character case is ignored.** Normalize `s` and `t` to lowercase first.
- **If the strings can be huge and streaming.** Compute and compare hashes of their sorted versions — some constant-memory methods exist but are lossy.
