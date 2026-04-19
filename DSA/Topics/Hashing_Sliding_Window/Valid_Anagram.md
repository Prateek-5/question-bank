# Valid Anagram

## Problem Link
https://leetcode.com/problems/valid-anagram/

## Topic
Hashing Sliding Window

## Core Concept
Character frequency comparison.

## Intuition
Two strings are anagrams iff each character occurs the same number of times.

## Detailed Explanation
Count each char in s; decrement from t; all counts zero → anagram.

## Dry Run
s='anagram', t='nagaram' → counts match → true.

## Approach
26-element array.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
bool isAnagram(string s, string t) {
    if (s.size() != t.size()) return false;
    int c[26] = {};
    for (char ch : s) c[ch-'a']++;
    for (char ch : t) if (--c[ch-'a'] < 0) return false;
    return true;
}
```

## Follow-up Questions
- Anagram groups.
- Unicode anagrams.
- Check with streaming chars.
