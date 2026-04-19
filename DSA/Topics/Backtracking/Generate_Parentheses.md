# Generate Parentheses

## Problem Link
https://leetcode.com/problems/generate-parentheses/

## Topic
Backtracking

## Core Concept
Backtracking on open/close counts.

## Intuition
Build string character by character; only append '(' if opens<n, only append ')' if closes<opens. Guarantees validity.

## Detailed Explanation
dfs(s, open, close): if s.length==2n record. If open<n: dfs with '('. If close<open: dfs with ')'.

## Dry Run
n=3 → ['((()))','(()())','(())()','()(())','()()()'].

## Approach
DFS with count constraints.

## Time and Space Complexity
Time: O(Catalan(n)). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
void dfs(int n, int o, int c, string& s, vector<string>& res) {
    if ((int)s.size() == 2*n) { res.push_back(s); return; }
    if (o < n) { s += '('; dfs(n, o+1, c, s, res); s.pop_back(); }
    if (c < o) { s += ')'; dfs(n, o, c+1, s, res); s.pop_back(); }
}
vector<string> generateParenthesis(int n) { vector<string> res; string s; dfs(n, 0, 0, s, res); return res; }
```

## Follow-up Questions
- Count only (Catalan numbers).
- Multiple bracket types.
- Lexicographic generation.
