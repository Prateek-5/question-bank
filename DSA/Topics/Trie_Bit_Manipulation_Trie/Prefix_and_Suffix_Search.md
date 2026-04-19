# Prefix and Suffix Search

## Problem Link
https://leetcode.com/problems/prefix-and-suffix-search/

## Topic
Trie Bit Manipulation Trie

## Core Concept
Trie indexed by 'suffix#prefix' concatenations.

## Intuition
Insert every (suffix + '#' + word) variant into a trie; a prefix+suffix query becomes a single trie lookup for 'suf#pre'. Store word index at each node for latest match.

## Detailed Explanation
For each word at index i, for each suffix s, insert s + '#' + word; at each node mark idx = i. Query: walk trie on 'suffix#prefix'; return stored idx or -1.

## Dry Run
Words ['apple']. Suffixes 'apple','pple','ple','le','e',''. Insert each + '#apple'. Query ('a','e'): 'e#a' → node has idx 0.

## Approach
Trie with combined key.

## Time and Space Complexity
Build O(sum L²). Query O(P+S).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class WordFilter {
    struct N { N* c[27] = {}; int idx = -1; };
    N* root = new N();
    int cix(char ch) { return ch == '#' ? 26 : ch - 'a'; }
public:
    WordFilter(vector<string>& words) {
        for (int i = 0; i < (int)words.size(); ++i) {
            string w = words[i];
            for (int s = 0; s <= (int)w.size(); ++s) {
                string key = w.substr(s) + "#" + w;
                auto* n = root;
                for (char ch : key) { if (!n->c[cix(ch)]) n->c[cix(ch)] = new N(); n = n->c[cix(ch)]; n->idx = i; }
            }
        }
    }
    int f(string pre, string suf) {
        string key = suf + "#" + pre;
        auto* n = root;
        for (char ch : key) { n = n->c[cix(ch)]; if (!n) return -1; }
        return n->idx;
    }
};
```

## Follow-up Questions
- With weighted words.
- Online insertions.
- Overlapping prefix/suffix.
