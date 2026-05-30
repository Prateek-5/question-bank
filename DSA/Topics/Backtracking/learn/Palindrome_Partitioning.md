# Palindrome Partitioning — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Palindrome_Partitioning.md`](../Palindrome_Partitioning.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/palindrome-partitioning/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/palindrome-partitioning/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: build partitions by choosing where each next palindrome ENDS. Try every prefix; if it's a palindrome, recurse on the suffix.** Same template solves Word Break, Restore IP Addresses, and many "split-into-parts" problems. **Read [`Generate_Parentheses.md`](./Generate_Parentheses.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. The "prefix + suffix" recurrence
3. Palindrome check
4. The algorithm
5. Code
6. Trace it
7. Optimization — precompute palindrome table
8. Common pitfalls
9. The shape — split-and-recurse

---

## 1. Read the problem

Given a string `s`, partition `s` into substrings such that every substring is a **PALINDROME**. Return all possible partitions.

A **partition** is a sequence of NON-OVERLAPPING substrings covering ALL of `s`.

**Examples:**

- `s = "aab"` →
  ```
  [["a", "a", "b"], ["aa", "b"]]
  ```
- `s = "a"` → `[["a"]]`.
- `s = "abc"` → `[["a", "b", "c"]]` (no multi-char palindromes).

---

## 2. The "prefix + suffix" recurrence

A partition of `s` = a palindrome **prefix** + a partition of the **suffix**.

Specifically: pick a prefix `s[0..end]` that's a palindrome. Recursively partition `s[end+1..]`. Combine.

```
partitions(s) = {
    [prefix] + partition for each:
        prefix = s[0..end] (palindrome)
        partition ∈ partitions(s[end+1..])
}
```

Base case: empty `s` → one partition `[]`.

This is a NATURAL backtracking decomposition: at each step, decide where the NEXT palindrome ENDS.

---

## 3. Palindrome check

A string is a palindrome iff it reads the same forward and backward.

```
def is_palindrome(s, l, r):
    while l < r:
        if s[l] != s[r]: return False
        l += 1; r -= 1
    return True
```

O(length). Called many times during backtracking — can become a bottleneck. See Section 7 for the precomputed O(1) variant.

---

## 4. The algorithm

```
def partition(s):
    res = []
    path = []
    
    def backtrack(start):
        if start == len(s):
            res.append(path[:])           # snapshot copy
            return
        for end in range(start, len(s)):
            if is_palindrome(s, start, end):
                path.append(s[start:end+1])
                backtrack(end + 1)
                path.pop()
    
    backtrack(0)
    return res
```

**Standard backtracking:**
- For each potential prefix end `end ≥ start`: if `s[start..end]` is a palindrome, push it and recurse.
- Base: `start == len(s)` (consumed all of s) → record this partition.

---

## 5. Code

**C++:**

```cpp
class Solution {
    vector<vector<string>> result;
    vector<string> path;

    bool isPalindrome(const string& s, int l, int r) {
        while (l < r) {
            if (s[l] != s[r]) return false;
            l++; r--;
        }
        return true;
    }

    void backtrack(const string& s, int start) {
        if (start == (int)s.size()) {
            result.push_back(path);
            return;
        }
        for (int end = start; end < (int)s.size(); ++end) {
            if (isPalindrome(s, start, end)) {
                path.push_back(s.substr(start, end - start + 1));
                backtrack(s, end + 1);
                path.pop_back();
            }
        }
    }

public:
    vector<vector<string>> partition(string s) {
        backtrack(s, 0);
        return result;
    }
};
```

**Python:**

```python
def partition(s):
    def is_pal(l, r):
        while l < r:
            if s[l] != s[r]: return False
            l += 1; r -= 1
        return True

    res = []
    path = []
    def backtrack(start):
        if start == len(s):
            res.append(path[:])
            return
        for end in range(start, len(s)):
            if is_pal(start, end):
                path.append(s[start:end + 1])
                backtrack(end + 1)
                path.pop()
    backtrack(0)
    return res
```

Complexity: exponential worst case (`s = "aaaa...a"` has 2^(n-1) partitions); O(n) per palindrome check.

---

## 6. Trace it

**`s = "aab"`:**

```
backtrack(start=0, path=[]):
  end=0: s[0..0]="a" is palindrome. path=["a"]. backtrack(1):
    end=1: s[1..1]="a" is pal. path=["a", "a"]. backtrack(2):
      end=2: s[2..2]="b" is pal. path=["a", "a", "b"]. backtrack(3):
        start == 3 == len(s). RECORD ["a", "a", "b"].
      pop "b".
    pop "a".
    end=2: s[1..2]="ab" not pal. Skip.
  pop "a".
  end=1: s[0..1]="aa" IS pal. path=["aa"]. backtrack(2):
    end=2: s[2..2]="b" pal. path=["aa", "b"]. backtrack(3):
      RECORD ["aa", "b"].
    pop "b".
  pop "aa".
  end=2: s[0..2]="aab" not pal. Skip.

Records: ["a","a","b"], ["aa","b"].  ✓
```

The exploration tries every prefix at every position; palindrome check filters invalid ones.

---

## 7. Optimization — precompute palindrome table

The palindrome check is O(n) per call, called up to O(n²) times across all recursions. Total: O(n³).

Precompute `is_pal[i][j]` = "is s[i..j] a palindrome?" in O(n²):

```
is_pal[i][i] = True
is_pal[i][i+1] = (s[i] == s[i+1])
is_pal[i][j] = (s[i] == s[j] and is_pal[i+1][j-1])    # j > i + 1
```

Build bottom-up. Then each palindrome check during backtracking is O(1).

Total time: O(n²) precompute + O(n × 2^n) backtracking = **O(n × 2^n)**.

> **Mini-refresher: DP for palindrome substrings.**
>
> `is_pal[i][j]` depends on `is_pal[i+1][j-1]` — the SMALLER inner range. So fill `is_pal` in order of INCREASING length: length 1, then 2, then 3, ..., up to n.
>
> Or: iterate `i` from n-1 down to 0, then j from i to n-1. The inner cell `is_pal[i+1][j-1]` is already computed.

---

## 8. Common pitfalls

1. **Forgetting to snapshot the path.** `res.append(path)` (without copy) shares references — all recorded partitions end up the same (empty).

2. **Not undoing the pop.** Path accumulates incorrectly.

3. **Off-by-one in `end + 1` recursion.** The next partition starts AT `end + 1`. Don't use `end` (would overlap).

4. **Trying to memoize.** Memoization on `start` (subproblems) helps for "count partitions" or "min cuts," but NOT for enumerating ALL partitions (the number can be exponential).

5. **Naive O(n) palindrome check per recursion.** Fine for small n; precompute for larger n.

6. **Slicing strings in Python (slow).** `s[start:end+1]` creates a new string each time. For large n, use indices and string view (or precompute).

7. **Forgetting empty-string base case.** `s = ""` → return `[[]]` (one partition: the empty one). But often the input guarantees non-empty.

---

## 9. The shape — split-and-recurse

The pattern:

> **"At each step, pick the END of the next PIECE. Validate the piece. Recurse on the remainder."**

| Problem | "Piece" criterion |
|---|---|
| **This problem** | piece is a palindrome |
| Word Break | piece is in the dictionary |
| Word Break II | same, return all sentences |
| Restore IP Addresses | piece is a valid IP octet (0-255, no leading zeros) |
| Concatenated Words | piece is a word from the input set |
| Decode Ways | piece is "1" through "26" (mapping to letters) |
| Match expression to template | piece matches some template segment |
| Palindrome Partitioning II (min cuts) | DP-version of this |

**Pattern to internalize:**

> "For 'split string into pieces satisfying property P' problems, backtrack: try each prefix end; if the prefix satisfies P, recurse on the suffix. Combine."

---

> **Self-check — the question to ask next time.**
>
> When you face "split / partition into pieces with property P," ask:
>
> > **"Can I try each prefix end, validate the piece, and recurse on the suffix? At base (start == n), record the path."**
>
> If yes, you've got split-and-recurse.

---

## Cross-references

- **Reference card (post-mastery):** [`../Palindrome_Partitioning.md`](../Palindrome_Partitioning.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Generate_Parentheses.md`](./Generate_Parentheses.md).
  - Coming next: [`Gray_Code.md`](./Gray_Code.md), [`Sudoku_Solver.md`](./Sudoku_Solver.md).
