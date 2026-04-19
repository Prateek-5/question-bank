# Shortest Unique prefix for every word

## Problem Link
https://www.geeksforgeeks.org/problems/shortest-unique-prefix-for-every-word/1

## Topic
Trie Bit Manipulation Trie

## Core Concept
Trie with prefix counts; walk to first node with count 1.

## Intuition
For each word, the shortest unique prefix is the first depth at which no other word passes through. Store at each node how many words traverse it.

## Detailed Explanation
Insert all words, incrementing cnt at each node. For each word, walk letters; first node with cnt==1 is its unique prefix end.

## Dry Run
Words: ['zebra','dog','duck','dove']. Results: ['z','dog','du','dov'].

## Approach
Trie with pass-count per node.

## Time and Space Complexity
Time: O(total chars). Space: O(total chars).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct N { N* c[26] = {}; int cnt = 0; };

vector<string> shortestUniquePrefix(vector<string>& words) {
    N* root = new N();
    for (auto& w : words) { auto* n = root; for (char ch : w) { if (!n->c[ch-'a']) n->c[ch-'a'] = new N(); n = n->c[ch-'a']; n->cnt++; } }
    vector<string> res;
    for (auto& w : words) {
        string p; auto* n = root;
        for (char ch : w) { p += ch; n = n->c[ch-'a']; if (n->cnt == 1) break; }
        res.push_back(p);
    }
    return res;
}
```

## Follow-up Questions
- Longest common prefix.
- Unique suffix (reverse).
- k-th shortest unique prefix.
