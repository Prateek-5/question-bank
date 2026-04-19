# Palindrome Partitioning

**Problem Link:**
https://leetcode.com/problems/palindrome-partitioning/

**Topic:**
Backtracking

----------------------------------------

## Step 1: Read the Problem

Given a string `s`, partition it into substrings such that every substring is a palindrome. Return all possible such partitions.

Example: `s = "aab"`.

Partitions where every piece is a palindrome:
- ["a", "a", "b"] (each single char is trivially a palindrome).
- ["aa", "b"] ("aa" is a palindrome).

Return both.

Note: a "partition" covers the entire string, piece-by-piece, with no overlap.

----------------------------------------

## Step 2: Think About How Partitions Are Built

A partition is a sequence of non-overlapping substrings that cover s from left to right. We can build it by deciding, at each step, **where the next palindrome ends**.

Starting at index 0:
- We pick some `end` such that `s[0..end]` is a palindrome. That becomes the first piece.
- Then recursively partition `s[end+1..]`.

This is a natural backtracking formulation: at each recursive call, we try every possible "next palindrome" and recurse on the rest.

----------------------------------------

## Step 3: The Algorithm

```
def partition(s):
    result = []
    path = []

    def backtrack(start):
        if start == len(s):
            result.append(path.copy())
            return
        for end in start..len(s)-1:
            if s[start..end] is a palindrome:
                path.append(s[start..end])
                backtrack(end + 1)
                path.pop()

    backtrack(0)
    return result
```

- `start` is the next un-partitioned index.
- We try each possible end from `start` to `len(s) - 1`, checking if `s[start..end]` is a palindrome.
- If yes, commit it and recurse from `end + 1`.
- At `start == len(s)`, the path is a valid partition — snapshot it.

Backtracking: after the recursive call, pop the last added piece so the next iteration starts fresh.

----------------------------------------

## Step 4: Trace on "aab"

```
backtrack(0), path = []
  end=0: s[0..0]="a" palindrome. path=["a"]. backtrack(1):
    end=1: s[1..1]="a" palindrome. path=["a", "a"]. backtrack(2):
      end=2: s[2..2]="b" palindrome. path=["a", "a", "b"]. backtrack(3):
        start == len. RECORD ["a", "a", "b"].
      pop.
    pop.
    end=2: s[1..2]="ab" not palindrome. Skip.
    pop from here doesn't happen since nothing was added.
  pop.
  end=1: s[0..1]="aa" palindrome. path=["aa"]. backtrack(2):
    end=2: s[2..2]="b" palindrome. path=["aa", "b"]. backtrack(3):
      RECORD ["aa", "b"].
    pop.
  pop.
  end=2: s[0..2]="aab" not palindrome. Skip.
```

Results: `["a", "a", "b"]` and `["aa", "b"]`. ✓

Notice at the top level, we try three choices for the first piece: "a", "aa", "aab". "aab" isn't a palindrome so we don't recurse on it. For "a" and "aa" that succeed, we recurse and further partition the rest.

----------------------------------------

## Step 5: Palindrome Check — Make It Efficient

Each substring check is O(end - start). With n characters and up to n² substrings to check, total palindrome-check work is O(n³).

We can precompute palindromicity with DP:
```
is_pal[i][j] = True if s[i..j] is a palindrome

is_pal[i][i] = True
is_pal[i][i+1] = (s[i] == s[i+1])
for i < j-1: is_pal[i][j] = (s[i] == s[j] and is_pal[i+1][j-1])
```

Build this table in O(n²). Then each palindrome check during backtracking is O(1). Total time savings matter for longer strings.

For interview purposes, the naive O(n) palindrome check inside backtracking is usually fine. The O(n²) precomputation is an optimization.

----------------------------------------

## Step 6: Complexity

**Time** depends on how many partitions exist. In the worst case (like `s = "aaaa...a"`), every substring is a palindrome, and the number of partitions is **O(2^n)** — exponential. For each partition, we spend O(n) copying it into the result.

**Space** is O(n) for the recursion stack plus O(output).

With O(n²) precomputation, the palindrome check itself becomes O(1), so total time is O(2^n · n).

----------------------------------------

## Step 7: Name It

Classic **backtracking with constraint check**. The pattern:
- Make a choice (pick a palindrome prefix).
- Validate (check palindrome).
- Recurse on the remainder.
- Undo the choice (backtrack).

Same shape as:
- Word Break (all valid split points into dictionary words).
- Restore IP Addresses (partitions into 4 valid segments).
- Matchsticks to Square (partitions into 4 equal sums).

----------------------------------------

## Step 8: Complexity Summary

Time: **O(N · 2^N)** worst case — 2^N partitions, each of length up to N to copy.
Space: **O(N)** for recursion + output size.

----------------------------------------

## Step 9: C++ Implementation

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

Clean backtracking template. The `isPalindrome` helper is O(n) per call; could be O(1) with precomputation.

Optimized version with precomputed DP:

```cpp
class Solution {
    vector<vector<string>> result;
    vector<string> path;
    vector<vector<bool>> isPal;   // precomputed

    void backtrack(const string& s, int start) {
        if (start == (int)s.size()) {
            result.push_back(path);
            return;
        }
        for (int end = start; end < (int)s.size(); ++end) {
            if (isPal[start][end]) {
                path.push_back(s.substr(start, end - start + 1));
                backtrack(s, end + 1);
                path.pop_back();
            }
        }
    }

public:
    vector<vector<string>> partition(string s) {
        int n = s.size();
        isPal.assign(n, vector<bool>(n, false));
        for (int i = n - 1; i >= 0; --i) {
            for (int j = i; j < n; ++j) {
                if (i == j) isPal[i][j] = true;
                else if (i + 1 == j) isPal[i][j] = (s[i] == s[j]);
                else isPal[i][j] = (s[i] == s[j] && isPal[i + 1][j - 1]);
            }
        }
        backtrack(s, 0);
        return result;
    }
};
```

The DP table makes each palindrome check O(1). For long strings with many partitions, this is a significant speedup.

----------------------------------------

## Step 10: Follow-up Questions

- **Palindrome Partitioning II: minimum cuts.** Different objective. DP: min cuts for prefix s[0..i] using the `isPal` table.
- **Return only the count of partitions, not the partitions themselves.** Don't build the list; just count.
- **Partition into k palindromes (exactly).** Add a constraint in the base case.
- **Partition with "each piece appears only once" constraint.** Add a used-set; skip partitions using duplicate pieces.
- **Generalize to "each piece satisfies property P."** Replace palindrome check with P.
- **Why is this exponential?** Because the number of valid partitions can be exponential (2^n for all-same-characters). No way to avoid that when enumerating all.
