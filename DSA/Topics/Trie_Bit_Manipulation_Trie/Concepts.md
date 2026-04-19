# Trie / Bit Manipulation Trie — Concepts

## Core Theory
Tries store strings (or bit sequences) by prefixes, enabling fast prefix queries, spell-check, dictionary lookups, and XOR maximization. Each node has one child per alphabet letter or bit.

## Common Patterns
- **Word insert/search** (classic trie).
- **Prefix + suffix search** by concatenating suffix#word variants.
- **Bit-trie for max XOR** — traverse greedily preferring opposite bits.
- **Wildcard search via DFS**.

## When to Use
When prefix-based queries dominate or when the alphabet is small and fixed. For arbitrary strings, hashmaps may be simpler unless prefix operations are essential.

## Template
```cpp
struct TrieNode { TrieNode* c[26] = {}; bool end = false; };
```

## Common Mistakes
- Memory blowup with large alphabets; consider hashmap children.
- Forgetting the end-of-word marker.
- Off-by-one when computing trie depth vs string length.
