# Design Add and Search Words DS

**Problem Link:**
https://leetcode.com/problems/design-add-and-search-words-data-structure/

**Topic:**
Trie / Bit Manipulation Trie

----------------------------------------

## Step 1: The Spec

Design a class supporting:
- `addWord(word)`: add a word to the dictionary.
- `search(word)`: return true if the dictionary contains any word matching the input. The input may include `'.'` which matches **any single character**.

Example:
- addWord("bad"), addWord("dad"), addWord("mad").
- search("pad") → false.
- search("bad") → true.
- search(".ad") → true (matches "bad", "dad", or "mad").
- search("b..") → true (matches "bad").

Wildcards are single-character, so ".ad" has length 3 and matches any length-3 word ending in "ad".

----------------------------------------

## Step 2: Which Data Structure?

Storing all words in a hashset gives O(1) `addWord` and O(1) exact `search`. But wildcard search would require scanning all stored words — O(n) per query. Bad for large dictionaries.

A **trie** (prefix tree) handles exact search in O(|word|). For wildcards, we'd explore all matching paths at each '.'.

Trie + DFS is the right tool.

----------------------------------------

## Step 3: Trie Mechanics

Same trie structure as Implement Trie:
- Each node has `children[26]` (for lowercase letters a-z) and an `isEnd` flag.
- `addWord` walks/creates the trie path for the word; marks end.

For search with wildcards:
- If current char is a normal letter, recurse into that specific child.
- If current char is `.`, try **every** non-null child.

If any branch reaches the end with `isEnd = true`, return true.

----------------------------------------

## Step 4: DFS Search With Wildcards

```
def search(word):
    return dfs(word, 0, root)

def dfs(word, idx, node):
    if idx == len(word):
        return node.isEnd
    ch = word[idx]
    if ch == '.':
        for child in node.children:
            if child is not null and dfs(word, idx + 1, child):
                return True
        return False
    else:
        c = node.children[ch - 'a']
        if c is null: return False
        return dfs(word, idx + 1, c)
```

Non-wildcard case: standard trie traversal. Wildcard case: try each child.

If at any point we run out of children to try (non-wildcard char missing), fail.

----------------------------------------

## Step 5: Trace on the Example

Add "bad", "dad", "mad":

Trie:
```
root
 ├── b → a → d*
 ├── d → a → d*
 └── m → a → d*
```

All three words share structure under 'a' and 'd', with different prefix letters.

search("pad"):
- idx 0, ch 'p'. root.children['p'] is null. Return false. ✓

search("bad"):
- idx 0, ch 'b'. Enter 'b' node.
- idx 1, ch 'a'. Enter 'a' node.
- idx 2, ch 'd'. Enter 'd' node.
- idx 3, len. d.isEnd = true. Return true. ✓

search(".ad"):
- idx 0, ch '.'. Try each non-null child of root.
  - Try 'b' child. Recurse with ("ad", 1, b_node).
    - idx 1, ch 'a'. Enter b.a node.
    - idx 2, ch 'd'. Enter b.a.d node.
    - idx 3, len. isEnd. Return true. ✓ Return true.
  
  (We don't even need to try 'd' or 'm'.)

search("b..")
- idx 0, ch 'b'. Enter 'b' node.
- idx 1, ch '.'. b has only 'a' child. Recurse with ("b..", 2, b.a node).
  - idx 2, ch '.'. b.a has only 'd' child. Recurse (idx 3, b.a.d node).
    - idx 3, len. isEnd. Return true. ✓ 

----------------------------------------

## Step 6: Why DFS Is Natural for Wildcards

Each wildcard creates a branching point with up to 26 children. DFS explores branches one at a time; if one succeeds, we return true early. If none succeed at some level, backtrack.

BFS would also work but is less natural — level-by-level traversal in a trie isn't as clean as depth-first exploration.

The worst case for wildcard search is when many '.' appear: exploring 26^k paths for k wildcards. In practice, the trie structure prunes heavily.

----------------------------------------

## Step 7: Complexity

- **addWord**: O(|word|).
- **search** (no wildcards): O(|word|).
- **search** (with wildcards): O(26^W · |word|) worst case, where W is the number of wildcards. In practice much better due to trie pruning.

Space: O(total characters of all added words) — proportional to trie nodes.

----------------------------------------

## Step 8: C++ Implementation

```cpp
class WordDictionary {
    struct Node {
        Node* children[26] = {nullptr};
        bool isEnd = false;
    };
    Node* root;

    bool dfs(const string& word, int idx, Node* node) {
        if (idx == (int)word.size()) return node->isEnd;
        char ch = word[idx];
        if (ch == '.') {
            for (int i = 0; i < 26; ++i) {
                if (node->children[i] && dfs(word, idx + 1, node->children[i])) {
                    return true;
                }
            }
            return false;
        } else {
            Node* c = node->children[ch - 'a'];
            if (!c) return false;
            return dfs(word, idx + 1, c);
        }
    }

public:
    WordDictionary() : root(new Node()) {}

    void addWord(string word) {
        Node* cur = root;
        for (char ch : word) {
            int idx = ch - 'a';
            if (!cur->children[idx]) cur->children[idx] = new Node();
            cur = cur->children[idx];
        }
        cur->isEnd = true;
    }

    bool search(string word) {
        return dfs(word, 0, root);
    }
};
```

`dfs` handles both the wildcard and exact-char cases cleanly. The recursive structure mirrors the trie's branching.

----------------------------------------

## Step 9: Follow-up Questions

- **Support '*' (zero or more characters).** More complex — match at any position. Requires careful DFS with variable length.
- **Case-insensitive search.** Normalize to lowercase on add and search.
- **Multiple wildcards in a single pattern.** Same algorithm handles it — just more branches.
- **Return all matching words.** Modify DFS to collect words when `isEnd` is reached.
- **Limit the maximum number of wildcards to avoid explosion.** Restrict at input validation.
- **Regex-like patterns.** Generalize: each pattern-char might be a character class. DFS still works but becomes more complex.
