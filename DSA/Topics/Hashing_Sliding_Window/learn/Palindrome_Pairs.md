# Palindrome Pairs — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Palindrome_Pairs.md`](../Palindrome_Pairs.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/palindrome-pairs/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/palindrome-pairs/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~35 minutes. This is **the hardest hash-based problem in standard interviews** — the algorithmic insight (case-analysis on word lengths + split-point reformulation) is genuinely tricky. The lesson: **when concatenation behavior depends on relative lengths, enumerate cases and reduce each to a structured hashmap lookup.**

**Map of this file (11 short sections):**

1. Read the problem
2. The natural brute force
3. Why we need a smarter approach
4. What makes a concatenation a palindrome — three cases
5. Reframing as "split-point + hashmap lookup"
6. Avoiding double-counting
7. Code
8. Trace it
9. Common pitfalls
10. Alternative — trie of reversed words
11. The shape — case analysis with hash lookup

---

## 1. Read the problem

You're given a list of **distinct** words. Return all index pairs `(i, j)` with `i ≠ j` such that **concatenating `words[i] + words[j]` forms a palindrome**.

> **Mini-refresher: palindrome.**
>
> A string is a **palindrome** if it reads the same forward and backward. Examples: `"racecar"`, `"abba"`, `"a"`, `""` (empty string — trivially palindromic).
>
> Check: `s` is a palindrome iff `s == reverse(s)`. Or equivalently: for each i, `s[i] == s[len(s) - 1 - i]`.

**Example:** `words = ["abcd", "dcba", "lls", "s", "sssll"]`.

Concatenations to check:

- `"abcd" + "dcba" = "abcddcba"`. Palindrome? Read forward = backward? Yes. ✓ Pair `(0, 1)`.
- `"dcba" + "abcd" = "dcbaabcd"`. Palindrome? Yes. ✓ Pair `(1, 0)`.
- `"lls" + "sssll" = "llssssll"`. Palindrome? Yes. ✓ Pair `(2, 4)`.
- `"s" + "lls" = "slls"`. Palindrome? Yes. ✓ Pair `(3, 2)`.

Output: `[[0, 1], [1, 0], [2, 4], [3, 2]]`.

Note: `(i, j)` and `(j, i)` are DIFFERENT pairs since the concatenation order differs. `"abcd" + "dcba"` may be palindromic while `"dcba" + "abcd"` may or may not be — check both.

---

## 2. The natural brute force

Try every ordered pair `(i, j)` with `i ≠ j`. For each, concatenate and check.

```cpp
vector<vector<int>> palindromePairs(vector<string>& words) {
    vector<vector<int>> result;
    int n = words.size();
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (i == j) continue;
            string concat = words[i] + words[j];
            if (isPalindrome(concat)) {
                result.push_back({i, j});
            }
        }
    }
    return result;
}
```

- Pairs: O(n²).
- Concatenation + palindrome check: O(L) per pair where L = average word length.
- Total: **O(n² · L)**.

For `n = 5000` and `L = 100`, that's `2.5 × 10⁹` ops → TLE.

---

## 3. Why we need a smarter approach

For each pair `(i, j)`, we spend O(L) on the palindrome check. Across O(n²) pairs, that's O(n² · L). We want to do better.

**Pivot question:** instead of testing every pair, can we find, for each word `s`, the **specific other words** that would concatenate with `s` to form a palindrome? If we have a hashmap `word → index`, we could look up these specific other words directly.

The trick: figure out, given `s`, what `t` would make `s + t` a palindrome. If we can describe `t` precisely (e.g., "reverse of s's prefix"), we can look it up in O(L) — and there are only O(L) such candidates per `s` (one per split position).

That gives **O(n · L²)** total — a major win when n >> L.

---

## 4. What makes a concatenation a palindrome — three cases

Let me carefully think about when `s + t` is a palindrome.

Let `|s| = a` and `|t| = b`. Picture the concatenation as one string of length `a + b`. For it to be a palindrome, the first character must match the last, the second must match the second-to-last, and so on toward the middle.

The relationship between `a` and `b` determines which structural shape the palindrome takes.

**Case X: `a == b`** (equal lengths).

The mirror line of the palindrome lies exactly between `s` and `t`. So `s[i] == t[b − 1 − i]` for all i, which means `t == reverse(s)`.

So we need `t = reverse(s)`. Hashmap lookup: does `reverse(s)` exist as a word?

**Case Y: `a > b`** (s is longer than t).

The first `b` characters of `s + t` are `s[0..b-1]`. These must match (reading from the end of `s + t`) the LAST `b` characters, which are `t`.

Specifically: `s[i] == (s + t)[a + b - 1 - i] = t[b - 1 - i]` for `0 ≤ i ≤ b - 1`.

So the first `b` chars of `s` must mirror `t`: i.e., `t == reverse(s[0..b-1])`.

Additionally, the "middle" of `s + t` is `s[b..a-1]` (the leftover of `s` not matched against `t`). This middle must be a **palindrome by itself** (it mirrors against itself within `s + t`).

So: **s = (reverse of t) followed by (palindrome)**. To find `t`, we ask: is there a word equal to `reverse(s[0..k-1])` for some k where `s[k..a-1]` is a palindrome?

**Case Z: `a < b`** (t is longer than s).

Symmetric to Case Y. **t = (palindrome) followed by (reverse of s)**. We ask: is there a word equal to `reverse(s)` preceded by a palindromic prefix in t? But since we don't have direct access to "all words ending in reverse(s)," we reformulate by iterating `t` from the perspective of `t`.

**This is the key reframing:** instead of trying to enumerate `t`s that pair with a given `s`, we can flip the question. For each word `s`, find pairs where `s` is the FIRST word (Cases X, Y) AND pairs where `s` is the SECOND word (Case Z). Then a single sweep over all words covers everything.

---

## 5. Reframing as "split-point + hashmap lookup"

The trick: for each word `s`, split it at every position `k` (from `0` to `|s|`). The split divides `s` into a **left** half `s[0..k-1]` and a **right** half `s[k..|s|-1]`.

**Reframed Case 1 (s is first in the pair):** for `s + t` to be a palindrome:

- The right half `s[k..]` is a palindrome.
- We need `t = reverse(left) = reverse(s[0..k-1])`.

This is exactly Case Y above, parameterized by where the "palindromic middle" begins.

**Reframed Case 2 (s is second in the pair):** for `t + s` to be a palindrome:

- The left half `s[0..k-1]` is a palindrome.
- We need `t = reverse(right) = reverse(s[k..|s|-1])`.

This is exactly Case Z (s is shorter, t comes before).

By iterating every split position `k = 0..|s|` and checking both cases, we cover all pairings involving `s` — whether `s` is on the left or right of the concatenation.

**Algorithm:**

```
Build map: word → index.

For each word s at index i:
    For each split position k = 0 to |s|:
        # Case 1: s + t palindrome
        if s[k..|s|-1] is a palindrome:
            candidate = reverse(s[0..k-1])
            if candidate in map AND map[candidate] != i:
                add pair (i, map[candidate])

        # Case 2: t + s palindrome
        if k != 0 AND k != |s| AND s[0..k-1] is a palindrome:
            candidate = reverse(s[k..|s|-1])
            if candidate in map AND map[candidate] != i:
                add pair (map[candidate], i)

Return all pairs.
```

The `k != 0 && k != |s|` guard in Case 2 prevents double-counting (see next section).

**Complexity:**

- For each word (n of them):
  - For each split position (L+1 of them):
    - Palindrome check on substring: O(L).
    - Reverse and hashmap lookup: O(L).

Total: **O(n · L²)**. For `n = 5000, L = 100`: `5 × 10⁷` ops. Fast.

---

## 6. Avoiding double-counting

The cases overlap at endpoints:

- **Case 1 at k = 0:** left = `""`, right = `s`. Right palindrome iff `s` is palindrome. We'd look for `reverse("")` = `""` in the map. Only matters if `""` is a word in the list (a trivial pair with the empty word).

- **Case 2 at k = |s|:** left = `s`, right = `""`. Same as above, by symmetry — finds the empty-word pairing if it exists.

- **Case 1 at k = |s|:** left = `s`, right = `""`. Right palindrome (empty is palindrome). We look for `reverse(s)`. If a word `reverse(s)` exists at index `j`, we add pair `(i, j)`.

- **Case 2 at k = 0:** left = `""`, right = `s`. Left palindrome (empty). We look for `reverse(s)`. If `reverse(s)` exists at `j`, we'd add pair `(j, i)`.

These last two are DIFFERENT pairs (`(i, j)` vs `(j, i)`) and BOTH should be counted (assuming both concatenations are palindromes). So Case 1 at k=|s| handles `(i, j)` and Case 2 at k=0 would handle `(j, i)` — but `(j, i)` is also handled by Case 1 at k=|words[j]| when processing word `j`!

To avoid double-counting, the standard rule is:

- **Case 1**: run for all k from 0 to |s| (inclusive).
- **Case 2**: skip k = 0 and k = |s|.

This way each pair is detected exactly once.

---

## 7. Code

**C++:**

```cpp
class Solution {
    bool isPalindrome(const string& s, int l, int r) {
        while (l < r) {
            if (s[l] != s[r]) return false;
            l++;
            r--;
        }
        return true;
    }

public:
    vector<vector<int>> palindromePairs(vector<string>& words) {
        unordered_map<string, int> indexOf;
        for (int i = 0; i < (int)words.size(); i++) {
            indexOf[words[i]] = i;
        }

        vector<vector<int>> result;

        for (int i = 0; i < (int)words.size(); i++) {
            const string& s = words[i];
            int n = s.size();

            for (int k = 0; k <= n; k++) {
                // Case 1: s + t palindrome → right palindrome, t = reverse(left)
                if (isPalindrome(s, k, n - 1)) {
                    string rev_left(s.begin(), s.begin() + k);
                    reverse(rev_left.begin(), rev_left.end());
                    auto it = indexOf.find(rev_left);
                    if (it != indexOf.end() && it->second != i) {
                        result.push_back({i, it->second});
                    }
                }

                // Case 2: t + s palindrome → left palindrome, t = reverse(right)
                // Skip k = 0 and k = n to avoid double-counting
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

Key details:

- `isPalindrome(s, l, r)` checks the substring `s[l..r]` inclusive WITHOUT making a copy — pass by reference, scan with two pointers.
- `it->second != i` skips self-pairs (a word paired with itself).
- The double-counting prevention is `k != 0 && k != n` in Case 2.

**Python:**

```python
def palindromePairs(words):
    def is_palindrome(s, l, r):
        while l < r:
            if s[l] != s[r]:
                return False
            l += 1
            r -= 1
        return True

    index_of = {w: i for i, w in enumerate(words)}
    result = []

    for i, s in enumerate(words):
        n = len(s)
        for k in range(n + 1):
            # Case 1: s + t palindrome
            if is_palindrome(s, k, n - 1):
                rev_left = s[:k][::-1]
                if rev_left in index_of and index_of[rev_left] != i:
                    result.append([i, index_of[rev_left]])

            # Case 2: t + s palindrome (skip k=0 and k=n)
            if 0 < k < n and is_palindrome(s, 0, k - 1):
                rev_right = s[k:][::-1]
                if rev_right in index_of and index_of[rev_right] != i:
                    result.append([index_of[rev_right], i])

    return result
```

Both O(n · L²).

---

## 8. Trace it

`words = ["abcd", "dcba", "lls", "s", "sssll"]`. Map: `{"abcd": 0, "dcba": 1, "lls": 2, "s": 3, "sssll": 4}`.

**i = 0, s = "abcd":**

```
k=0: left="", right="abcd". Right palindrome? "abcd" — no. Case 1 skipped.
     (k=0 → Case 2 skipped per rule.)

k=1: left="a", right="bcd". 
     Case 1: right "bcd" palindrome? No.
     Case 2: left "a" palindrome? Yes. Reverse right = "dcb". Lookup → not in map.

k=2: left="ab", right="cd". Neither palindrome.

k=3: left="abc", right="d".
     Case 1: "d" palindrome? Yes. reverse("abc") = "cba". In map? No.
     Case 2: left "abc" palindrome? No.

k=4: left="abcd", right="".
     Case 1: "" palindrome? Yes. reverse("abcd") = "dcba". In map at 1. Add [0, 1].
     (k=4 = n → Case 2 skipped.)
```

Pairs so far: `[[0, 1]]`.

**i = 1, s = "dcba":**

By symmetry to i=0, at k=4: Case 1 finds reverse("dcba") = "abcd" at index 0. Add [1, 0].

Pairs: `[[0, 1], [1, 0]]`.

**i = 2, s = "lls":**

```
k=0: right="lls". Palindrome? "lls" — l != s. No.
k=1: left="l", right="ls".
     Case 1: "ls" palindrome? No.
     Case 2: "l" palindrome? Yes. reverse("ls") = "sl". Not in map.
k=2: left="ll", right="s".
     Case 1: "s" palindrome? Yes. reverse("ll") = "ll". Not in map.
     Case 2: "ll" palindrome? Yes. reverse("s") = "s". In map at 3. Add [3, 2].
k=3: left="lls", right="".
     Case 1: "" palindrome. reverse("lls") = "sll". Not in map.
```

Pairs: `[[0, 1], [1, 0], [3, 2]]`.

**i = 3, s = "s":**

```
k=0: right="s". Palindrome? Yes. reverse("") = "". Not in map.
k=1: left="s", right="". (n=1)
     Case 1: "" palindrome. reverse("s") = "s". In map at 3 — SELF. Skip.
```

No new pairs.

**i = 4, s = "sssll":**

```
k=0: right="sssll" palindrome? No.
k=1: left="s", right="ssll".
     Case 1: "ssll" palindrome? No.
     Case 2: "s" palindrome? Yes. reverse("ssll") = "llss". Not in map.
k=2: left="ss", right="sll".
     Case 1: "sll" palindrome? No.
     Case 2: "ss" palindrome? Yes. reverse("sll") = "lls". In map at 2. Add [2, 4].
k=3: left="sss", right="ll".
     Case 1: "ll" palindrome? Yes. reverse("sss") = "sss". Not in map.
     Case 2: "sss" palindrome? Yes. reverse("ll") = "ll". Not in map.
k=4: left="sssl", right="l".
     Case 1: "l" palindrome. reverse("sssl") = "lsss". Not in map.
     Case 2: "sssl" palindrome? No.
k=5: left="sssll", right="".
     Case 1: "" palindrome. reverse("sssll") = "llsss". Not in map.
```

Pairs: `[[0, 1], [1, 0], [3, 2], [2, 4]]`. ✓

All 4 pairs found. Matches expected output.

---

## 9. Common pitfalls

1. **Forgetting to skip self-pairs.** A word `s` such that `s + s` is a palindrome (e.g., `s = "aaaa"`) would pair with itself if we don't check `it->second != i`. The problem requires `i ≠ j`.

2. **Failing to handle empty string.** If `""` is in the list, it pairs with every palindromic word — but our algorithm handles this naturally via the `k=0, k=|s|` cases (both right and left are empty, which is palindromic). The lookup correctly finds the empty word's index.

3. **Double-counting by not having the `k != 0 && k != n` guard in Case 2.** Without it, Case 1 at `k = n` and Case 2 at `k = 0` both find the same `(i, j)` pair for `t = reverse(s)`.

4. **Allocating substrings unnecessarily.** Repeatedly creating substring copies for palindrome checks slows things down. Pass `(string&, int l, int r)` to check in place.

5. **Confusing the case order.** Case 1 produces pair `(i, ...)`, Case 2 produces pair `(..., i)`. Verify the ordering matches "s is first" vs "s is second."

6. **Off-by-one in `isPalindrome(s, l, r)`.** This checks inclusive range `[l, r]`. If you pass `(s, k, n)` instead of `(s, k, n-1)`, you'll segfault or check empty incorrectly.

7. **Failing on words with only one character.** They're palindromes by themselves and concatenate with any reverse-of-other-word. The algorithm handles them naturally; just don't add edge-case logic that breaks them.

---

## 10. Alternative — trie of reversed words

An alternative O(n · L²) approach uses a **trie of reversed words**. For each query word `s`, walk the trie matching its characters; at each branching node, if the remaining trie path leads to a word AND the rest of `s` is palindromic (or vice versa), record a pair.

Pros: extensible to more complex string queries.
Cons: more code, harder to reason about.

For interview answers, the hashmap-based split-and-check version is usually preferred.

---

## 11. The shape — case analysis with hash lookup

The pattern of this problem:

> 1. **Enumerate cases** based on a structural property (here: relative lengths).
> 2. **For each case, derive a precise pattern** that the partner string must match.
> 3. **Use a hashmap** to look up partner candidates in O(L) per query.
> 4. **Avoid double-counting** by careful case-boundary rules.

Where else this pattern appears:

| Problem | Cases / structure | Hashmap key |
|---|---|---|
| **This problem** | s + t palindrome by length cases | reverse of a substring |
| Two Sum | (a + b == target) — just one case | `target - a` |
| 3Sum | fix one outer, two-pointer rest | (covered with two-pointer instead) |
| Sum of two squares | n = a² + b² → enumerate `a`, check `n - a²` | precomputed squares |
| Concatenated Words (LC #472) | word = w1 + w2 (... + wk) | each prefix that's a word |
| Word Break (LC #139) | DP, but enumerates splits | hashmap of dictionary words |

**Pattern to internalize:**

> "When a problem asks **'find pairs (or tuples) such that some structured concatenation/composition satisfies a property,'** enumerate possible structural cases and **for each case, reduce to a hashmap lookup of a derived pattern.**"

The art is **identifying the right cases** so each pair is found exactly once.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem asking for **pairs of items whose concatenation/composition has a property** (palindromic, sums to target, forms a word, etc.), before checking every pair, ask:
>
> > **"Can I do case analysis on the structure of the composition (lengths, parities, etc.) and, for each case, reduce to a hashmap lookup of a derived key?"**
>
> If yes, you've turned O(n² · L) into O(n · L²) — and for many real-world n >> L, that's the difference between TLE and AC.

---

## Cross-references

- **Reference card (post-mastery):** [`../Palindrome_Pairs.md`](../Palindrome_Pairs.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Anagram.md`](./Valid_Anagram.md), [`Valid_Sudoku.md`](./Valid_Sudoku.md), [`Subarray_Sum_Equals_K.md`](./Subarray_Sum_Equals_K.md) — hashmap foundations.
  - Coming later (Trie topic): Concatenated Words — similar shape with trie instead of hashmap.
  - Coming later (DP topic): Word Break — enumerates word splits via DP + hashmap.
