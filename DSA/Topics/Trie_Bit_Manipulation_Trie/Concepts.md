# Trie / Bit Manipulation Trie — Concepts Guide

----------------------------------------

## 1. Introduction

A trie is a tree where each path from the root spells out a string (or a bit sequence). It's the Swiss Army knife of prefix-based problems: dictionary lookups, autocomplete, word-filter, and — with bits — maximum XOR queries. Tries share prefixes, so they're memory-efficient for structured data.

----------------------------------------

## 2. Real-Life Analogy

Imagine a library organized not by full book title, but by nested drawers: the top drawer contains books starting with 'A', inside which another drawer for 'AP', inside another for 'APP'. To find 'APPLE' you navigate five drawers. To find all books starting with 'APP' you just look inside that one drawer. That's a trie.

----------------------------------------

## 3. Core Idea

Each trie node has a child for each possible next character (or bit). Insert walks down the tree, creating missing nodes. Search walks down, failing at a missing child. For XOR tries, each node has two children (0 and 1). To maximize XOR with a query number, at each bit level greedily pick the opposite-bit child — if available, that bit contributes to the XOR.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Reach for a trie when:

- **You need prefix-based queries** (autocomplete, 'all words starting with X').
- **Dictionary membership with many lookups.**
- **Max XOR of a number with others** → bit trie.
- **Word filter with prefix + suffix** → combined-key trie.

----------------------------------------

## 5. Types / Variations

- **Character trie** for strings over an alphabet.
- **Bit trie** for integers (often 30 or 32 bits).
- **Compressed / Patricia trie** for sparse tries.
- **Suffix trie** for substring queries (related: suffix tree).

----------------------------------------

## 6. Step-by-Step Working

**Insert word:**
1. Start at root.
2. For each char c, go to `root.children[c]`; if missing, create it.
3. At the end, mark the node as `end = true`.

**Search word:**
1. Start at root.
2. For each char c, go to `root.children[c]`; if missing, return false.
3. Return `node.end`.

**Max XOR with x (bit trie):**
1. Start at root.
2. For each bit b from MSB to LSB:
   - Compute desired bit = 1 - (x's bit at b).
   - If child[desired] exists, go there and set bit b in the XOR value.
   - Else go to child[other].

----------------------------------------

## 7. Visual Explanation

**Trie after inserting 'app', 'apple', 'bat':**

```
            root
           /    \
          a      b
          |      |
          p      a
          |      |
          p*     t*
          |
          l
          |
          e*
```

`*` marks end-of-word. 'app' and 'apple' share the prefix 'app'.

----------------------------------------

## 8. Code Templates (C++)

```cpp
struct TrieNode {
    TrieNode* children[26] = {};
    bool end = false;
};

class Trie {
    TrieNode* root = new TrieNode();
public:
    void insert(const string& w) {
        auto* n = root;
        for (char c : w) {
            int idx = c - 'a';
            if (!n->children[idx]) n->children[idx] = new TrieNode();
            n = n->children[idx];
        }
        n->end = true;
    }
    bool search(const string& w) {
        auto* n = root;
        for (char c : w) {
            n = n->children[c - 'a'];
            if (!n) return false;
        }
        return n->end;
    }
    bool startsWith(const string& p) {
        auto* n = root;
        for (char c : p) {
            n = n->children[c - 'a'];
            if (!n) return false;
        }
        return true;
    }
};
```

----------------------------------------

## 9. Common Mistakes

- **Memory blowup** with large alphabets — consider unordered_map children.
- **Forgetting the end marker** — causes false positives in `search`.
- **Deleting nodes incorrectly** — reference counts / marker flags help.
- **Confusing `search` vs `startsWith`** — they differ by the end marker.

----------------------------------------

## 10. Interview Insights

Trie problems test whether you can build a non-trivial data structure on the fly. Interviewers want to see:

1. **Clean node structure.**
2. **Correct end-marker handling.**
3. **Prefix queries in linear-in-length time.**
4. **For XOR problems: greedy opposite-bit traversal.**

Tip: always diagram your trie state after 2–3 insertions. That cements correctness before you code the tricky operations.
