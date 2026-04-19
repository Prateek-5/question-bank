# Design Add and Search Words DS

## Problem Link
https://leetcode.com/problems/design-add-and-search-words-data-structure/

## Topic
Trie Bit Manipulation Trie

## Core Concept
Trie with '.' wildcard handled via DFS.

## Intuition
A trie stores words prefix-compactly. Wildcard '.' at search time branches into all children of the current node.

## Detailed Explanation
addWord walks the trie creating nodes. search(word,node): if char '.', recurse on every existing child. Else follow exact child or fail. At end check node.isEnd.

## Dry Run
Add 'bad','dad','mad'. Search 'pad'→false. Search '.ad'→true. Search 'b..'→true.

## Approach
Standard Trie + DFS for wildcards.

## Time and Space Complexity
Add O(L), search O(26^w · L) worst-case.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class WordDictionary {
    struct N { N* c[26] = {}; bool end = false; };
    N* root = new N();
    bool dfs(const string& s, int i, N* n) {
        if (!n) return false;
        if (i == (int)s.size()) return n->end;
        char ch = s[i];
        if (ch == '.') {
            for (auto* k : n->c) if (dfs(s, i+1, k)) return true;
            return false;
        }
        return dfs(s, i+1, n->c[ch-'a']);
    }
public:
    void addWord(string w) {
        auto* n = root;
        for (char ch : w) { if (!n->c[ch-'a']) n->c[ch-'a'] = new N(); n = n->c[ch-'a']; }
        n->end = true;
    }
    bool search(string w) { return dfs(w, 0, root); }
};
```

## Follow-up Questions
- Support '*' (zero-or-more).
- Delete word from dictionary.
- Prefix search.
