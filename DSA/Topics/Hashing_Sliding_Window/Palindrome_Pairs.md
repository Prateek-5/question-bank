# Palindrome Pairs

**Problem Link:**
https://leetcode.com/problems/palindrome-pairs/

**Topic:**
Hashing / Sliding Window

----------------------------------------

## Step 1: Read the Problem

Given a list of **distinct** words, return all pairs of indices `(i, j)` (with i ≠ j) such that concatenating `words[i] + words[j]` forms a palindrome.

Example: `words = ["abcd", "dcba", "lls", "s", "sssll"]`.

Checking every ordering:
- "abcd" + "dcba" = "abcddcba" — palindrome. Pair: (0, 1).
- "dcba" + "abcd" = "dcbaabcd" — palindrome. Pair: (1, 0).
- "lls" + "sssll" = "llssssll" — palindrome. Pair: (2, 4).
- "s" + "lls" = "slls" — palindrome. Pair: (3, 2).

Output: `[[0, 1], [1, 0], [2, 4], [3, 2]]`.

Note: (i, j) and (j, i) are distinct pairs since the concatenation differs.

----------------------------------------

## Step 2: Brute Force and Its Cost

Try every ordered pair: O(n²) pairs × O(L) palindrome check = O(n² L). For n = 5000 and L = 100, that's 10^9 — too slow.

We need a smarter approach that reduces the O(n²) enumeration.

----------------------------------------

## Step 3: A Key Question — When Is `s + t` a Palindrome?

Let's carefully think about when concatenating two strings yields a palindrome.

Picture `s + t` as a combined string. For it to be a palindrome, it must read the same forward and backward. The first character matches the last, second matches second-to-last, and so on.

Let `|s| = a` and `|t| = b`. Three cases based on lengths:

**Case X: a = b.** For `s + t` to be a palindrome, `t` must be the **reverse of s**. Easy to check: look up reverse(s) in a hashmap.

**Case Y: a > b.** The first `b` chars of `s + t` are `s[0..b-1]`. These must match (in reverse) the last `b` chars of `s + t`, which are `t`. So `s[0..b-1]` reversed equals `t`. Additionally, the middle of `s + t` (which is `s[b..a-1]`) must be a **palindrome on its own**.

Restating: for `s + t` palindrome with a > b, `s` looks like `(reverse of t) + (palindrome)`.

**Case Z: a < b.** Symmetric: `t` looks like `(palindrome) + (reverse of s)`.

These three cases cover every possibility. (If a = b and s is self-reverse — i.e., a palindrome — t = reverse(s) = s, so we need another word equal to s. But problem says distinct; this only fires if another palindrome word of the same content exists.)

----------------------------------------

## Step 4: Rephrase Cases for a Hashmap Solution

Processing each word `s` one at a time, we want to find words `t` such that `s + t` is a palindrome. Transform the three cases:

**Case 1 (s is the "front"): `s + t` palindrome.**
Split s into a prefix and a suffix at some index k: `s = left + right`.
- If `right` is a palindrome, then we need `t = reverse(left)`. Then `s + t = left + right + reverse(left)` reads as a palindrome (because first `len(left)` chars match last `len(left)` reversed, and middle `right` is palindromic).

**Case 2 (s is the "back"): `t + s` palindrome.**
Split s again: `s = left + right`.
- If `left` is a palindrome, then we need `t = reverse(right)`. Then `t + s = reverse(right) + left + right` is a palindrome.

So: for each word s, for each split point k, check if the "non-matching" portion (right in Case 1, left in Case 2) is a palindrome. If yes, look up the reverse of the remaining portion in the hashmap. If found, we have a pair.

This handles all three cases (X, Y, Z) — split points where k = 0 or k = len(s) correspond to Case X (t = reverse(s) for empty left/right).

----------------------------------------

## Step 5: Avoid Double-Counting

One trap: Case 1 at `k = 0` and Case 2 at `k = len(s)` might both fire for the same (i, j) pair.

- Case 1 at k = 0: left = "", right = s. If s is a palindrome (and "" is considered palindromic trivially for left), then reverse("") = "" must be a word. Unlikely unless "" is in the list.
- Case 2 at k = len(s): left = s, right = "". If s is a palindrome, reverse("") = "" must be a word.

These only fire with empty-word present.

More subtle duplication: Case 1 at k = len(s) and Case 2 at k = 0 both try the "full reverse" pair (s paired with reverse(s)):
- Case 1 at k = len(s): left = s, right = "". Right is palindrome (empty). Look for reverse(s) in map → pair (i, map[reverse(s)]).
- Case 2 at k = 0: left = "", right = s. Left is palindrome (empty). Look for reverse(s) in map → pair (map[reverse(s)], i).

These give **different pairs** — (i, j) vs (j, i) — both valid. No double-counting.

The real duplication concern: same (i, j) could be produced twice by Case 1 at one k and Case 2 at a different k. The standard fix: in Case 2, skip k = 0 (which would duplicate Case 1 at k = len(s) in its symmetric mirror — but that's for a different word being processed, not the same). Actually, the cleanest rule is:

- Case 1: all k from 0 to len(s) (inclusive).
- Case 2: all k from 1 to len(s) - 1 (exclusive of endpoints).

This way, Case 2 at k = 0 and k = len(s) are skipped (their counterparts already handled by Case 1 at different k, for the same or different words).

----------------------------------------

## Step 6: Walk Through the Example

`words = ["abcd", "dcba", "lls", "s", "sssll"]`. Map: `{"abcd":0, "dcba":1, "lls":2, "s":3, "sssll":4}`.

Process i = 0, s = "abcd".
- k = 0: left = "", right = "abcd".
  - Case 1: right palindrome? No. Skip.
  - (k=0, skipping Case 2 per rule.)
- k = 1: left = "a", right = "bcd".
  - Case 1: right palindrome? No.
  - Case 2: left palindrome? Yes. reverse(right) = "dcb". In map? No.
- k = 2: left = "ab", right = "cd". Neither palindrome. No match.
- k = 3: left = "abc", right = "d".
  - Case 1: right palindrome? Yes. reverse(left) = "cba". In map? No.
  - Case 2: left palindrome? No.
- k = 4: left = "abcd", right = "".
  - Case 1: right palindrome (empty)? Yes. reverse(left) = "dcba". In map at index 1. Pair (0, 1). ✓

Process i = 1, s = "dcba".
- Similar scan. At k = 4: right = "", reverse(left) = "abcd" = words[0]. Pair (1, 0). ✓

Process i = 2, s = "lls".
- k = 0: skip Case 2.
- k = 1: left = "l", right = "ls". L palindrome yes, reverse(right) = "sl" not in map.
- k = 2: left = "ll", right = "s". L palindrome yes, reverse(right) = "s" in map at 3. Pair (3, 2). ✓
- k = 3: left = "lls", right = "". Case 1: right palindrome yes, reverse(left) = "sll". In map? No.

Process i = 3, s = "s".
- k = 0: skip Case 2.
- k = 1: left = "s", right = "". Case 1: right palindrome yes, reverse(left) = "s". In map at 3, but that's self — skip.

Process i = 4, s = "sssll".
- k = 3: left = "sss", right = "ll". Case 1: right palindrome yes, reverse(left) = "sss". In map? No. Case 2: left palindrome yes, reverse(right) = "ll". In map? No.
- k = 2: left = "ss", right = "sll". Case 1: right palindrome? No. Case 2: left palindrome yes, reverse(right) = "lls" = words[2]. Pair (2, 4). ✓

All four pairs found. ✓

----------------------------------------

## Step 7: Complexity

For each of n words, we do O(L) splits. For each split, palindrome check is O(L), hashmap lookup is O(L) (hashing cost on strings). Total: **O(n · L²)**.

For typical inputs, this is a big win over O(n² · L).

Space: O(n · L) for the hashmap.

----------------------------------------

## Step 8: Name It

**Hashmap-based palindrome pair detection using split-and-check.** The technique:
1. Precompute `word → index` hashmap.
2. For each word s, split at every position and use case analysis to find matching partners.
3. Leverage hashmap for O(1) lookup of reversed halves.

Alternative: **trie of reversed words**. Walk the trie from each source word; whenever we reach a word-end node and the remaining portion is palindromic, record a pair. Trie is more extensible but similar complexity.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class Solution {
    bool isPalindrome(const string& s, int l, int r) {
        while (l < r) {
            if (s[l] != s[r]) return false;
            l++; r--;
        }
        return true;
    }

public:
    vector<vector<int>> palindromePairs(vector<string>& words) {
        unordered_map<string, int> indexOf;
        for (int i = 0; i < (int)words.size(); ++i) indexOf[words[i]] = i;

        vector<vector<int>> result;

        for (int i = 0; i < (int)words.size(); ++i) {
            const string& s = words[i];
            int n = s.size();
            for (int k = 0; k <= n; ++k) {
                // Case 1: right [k..n-1] palindrome, find reverse(left) = s[0..k-1]
                if (isPalindrome(s, k, n - 1)) {
                    string rev_left(s.begin(), s.begin() + k);
                    reverse(rev_left.begin(), rev_left.end());
                    auto it = indexOf.find(rev_left);
                    if (it != indexOf.end() && it->second != i) {
                        result.push_back({i, it->second});
                    }
                }
                // Case 2: left palindrome, find reverse(right) = s[k..n-1]
                // Skip k = 0 (duplicate of Case 1 at k = n from a different word's pov)
                // Skip k = n (empty right, would match empty left from Case 1).
                if (k != 0 && k != n && isPalindrome(s, 0, k - 1)) {
                    string rev_right(s.begin() + k, s.end());
                    reverse(rev_right.begin(), rev_right.end());
                    auto it = indexOf.find(rev_right);
                    if (it != indexOf.end() && it->second != i) {
                        result.push_back({it->second, i});
                    }
                }
            }
        }
        return result;
    }
};
```

Key implementation details:
- `it->second != i`: skip self-pairs (word paired with itself).
- `k != 0 && k != n` in Case 2: prevents double-counting.
- `isPalindrome(s, l, r)` checks substring [l..r] inclusive without making a copy.

----------------------------------------

## Step 10: Follow-up Questions

- **Trie-based solution.** Insert reversed words into a trie. For each word, walk the trie matching its characters; when we find a terminal node with a matching palindrome remainder, record a pair. More complex code but similar O(n · L²) performance.
- **Handle duplicate words.** Not in this problem (distinct guaranteed), but if allowed, map to a list of indices.
- **Pairs where words[i] + words[j] is **almost** a palindrome (off by k chars).** Much harder; approximate matching.
- **Online: words arrive over time.** Insert into map as they come; for each new word, perform the split-and-lookup against existing entries.
- **Empty strings in input.** Can pair with any palindrome word. Handled naturally.
- **What if we want pairs where the reverse ordering also forms a palindrome?** Filter results accordingly.
