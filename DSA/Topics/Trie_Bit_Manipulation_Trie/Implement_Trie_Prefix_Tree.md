# Implement Trie (Prefix Tree)

## Problem Link
https://leetcode.com/problems/implement-trie-prefix-tree/

## Topic
Trie Bit Manipulation Trie

## Core Concept
26-ary tree nodes; insert, search, startsWith operations.

## Intuition
Each node represents a prefix; children map letters to next nodes. Marked isEnd distinguishes word endings.

## Detailed Explanation
Each operation walks the tree creating (insert) or following (search/startsWith) child links by character.

## Dry Run
Insert 'apple'. Search 'apple'→true. Search 'app'→false. startsWith 'app'→true.

## Approach
Fixed-size array per node for simplicity.

## Time and Space Complexity
Each op O(L).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class Trie {
    struct N { N* c[26] = {}; bool end = false; };
    N* root = new N();
public:
    void insert(string w) {
        auto* n = root;
        for (char ch : w) { if (!n->c[ch-'a']) n->c[ch-'a'] = new N(); n = n->c[ch-'a']; }
        n->end = true;
    }
    bool search(string w) {
        auto* n = root;
        for (char ch : w) { n = n->c[ch-'a']; if (!n) return false; }
        return n->end;
    }
    bool startsWith(string p) {
        auto* n = root;
        for (char ch : p) { n = n->c[ch-'a']; if (!n) return false; }
        return true;
    }
};
```

## Follow-up Questions
- Memory-efficient Trie (unordered_map children).
- Compressed Trie / Radix Tree.
- Persistent Trie.
