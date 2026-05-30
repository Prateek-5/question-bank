# Implement Trie (Prefix Tree) — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Implement_Trie_Prefix_Tree.md`](../Implement_Trie_Prefix_Tree.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/implement-trie-prefix-tree/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/implement-trie-prefix-tree/</a>

---

## How to use this file

Paced for someone seeing tries for the first time. Reading time: ~18 minutes. **The introduction to the TRIE data structure.** The lesson: **a trie is a TREE where each EDGE is a character. Words share a prefix iff they share the same path from the root.** O(|word|) insert/search — independent of dictionary size. Master the template; everything else in this topic builds on it.

**Map of this file (10 short sections):**

1. What's a trie?
2. The TrieNode definition
3. Insert
4. Search
5. startsWith
6. Code
7. Trace it
8. Why trie over hashset?
9. Memory considerations
10. The shape — prefix operations

---

## 1. What's a trie?

> **Mini-refresher: trie = "prefix tree."**
>
> A **trie** is a tree where:
> - Each EDGE is labeled with a CHARACTER.
> - A PATH from the root to some node SPELLS OUT a string (the labels along the way).
> - A node is marked as END-OF-WORD if a stored word ends there.
>
> Multiple words share NODES wherever they share a PREFIX. So inserting `"apple"` and `"app"` shares the path `a → p → p`.

For lowercase strings, each node has up to **26 children** (one per letter).

**Picture after inserting "apple", "app", "bat":**
```
        (root)
       /      \
      a        b
      |        |
      p        a
      |        |
     [p]*      [t]*
      |
      l
      |
     [e]*
```
`[*]` = isEnd (a word ends here).

`search("app")` → reaches `[p]*`. isEnd ✓ → true.
`search("appl")` → reaches l (no `*`). isEnd ✗ → false.
`startsWith("app")` → reaches a real node. → true.

---

## 2. The TrieNode definition

```
class TrieNode:
    children = array of 26 TrieNode (or hashmap)  # null means "no child"
    isEnd = false
```

Root is a special node with NO character (just children).

> **Mini-refresher: 26-array vs hashmap children.**
>
> **Array of 26:** O(1) access by index `ch - 'a'`. Fast. Uses more memory if children are sparse.
>
> **Hashmap (`unordered_map<char, TrieNode*>`):** O(1) average access. More memory-efficient for sparse children. Slower constants.
>
> For lowercase ASCII, the 26-array is standard. For arbitrary chars or Unicode, use the hashmap.

---

## 3. Insert

Walk the trie character-by-character. Create missing nodes. Mark the last node as end-of-word.

```
def insert(word):
    cur = root
    for ch in word:
        if cur.children[ch] is null:
            cur.children[ch] = new TrieNode()
        cur = cur.children[ch]
    cur.isEnd = True
```

O(|word|). Independent of dictionary size.

---

## 4. Search

Walk the trie. If any character's child is missing, return false. At the end, check `isEnd`.

```
def search(word):
    cur = root
    for ch in word:
        if cur.children[ch] is null:
            return False
        cur = cur.children[ch]
    return cur.isEnd
```

**Critical:** the final `isEnd` check. Without it, "appl" would be considered a found word (we'd traverse a-p-p-l successfully but no word ends at l).

---

## 5. startsWith

Same as search, but DON'T check `isEnd` at the end. Just verify the prefix path EXISTS.

```
def startsWith(prefix):
    cur = root
    for ch in prefix:
        if cur.children[ch] is null:
            return False
        cur = cur.children[ch]
    return True
```

A successful walk = the prefix is some inserted word's prefix.

---

## 6. Code

**C++:**

```cpp
class Trie {
    struct Node {
        Node* children[26] = {nullptr};
        bool isEnd = false;
    };
    Node* root;

    Node* traverse(const string& s) {
        Node* cur = root;
        for (char ch : s) {
            int idx = ch - 'a';
            if (!cur->children[idx]) return nullptr;
            cur = cur->children[idx];
        }
        return cur;
    }

public:
    Trie() : root(new Node()) {}

    void insert(string word) {
        Node* cur = root;
        for (char ch : word) {
            int idx = ch - 'a';
            if (!cur->children[idx]) cur->children[idx] = new Node();
            cur = cur->children[idx];
        }
        cur->isEnd = true;
    }

    bool search(string word) {
        Node* cur = traverse(word);
        return cur && cur->isEnd;
    }

    bool startsWith(string prefix) {
        return traverse(prefix) != nullptr;
    }
};
```

**Python:**

```python
class Trie:
    def __init__(self):
        self.children = {}
        self.is_end = False
    
    def insert(self, word):
        cur = self
        for ch in word:
            if ch not in cur.children:
                cur.children[ch] = Trie()
            cur = cur.children[ch]
        cur.is_end = True
    
    def _traverse(self, s):
        cur = self
        for ch in s:
            if ch not in cur.children:
                return None
            cur = cur.children[ch]
        return cur
    
    def search(self, word):
        node = self._traverse(word)
        return node is not None and node.is_end
    
    def startsWith(self, prefix):
        return self._traverse(prefix) is not None
```

Complexity: **O(|word|) per operation**, **O(N × L) space** where N = #words, L = avg length.

---

## 7. Trace it

```
Trie t.
t.insert("apple"):
  root → 'a' (created) → 'p' (created) → 'p' (created) → 'l' (created) → 'e' (created), mark isEnd.

t.insert("app"):
  root → 'a' (exists) → 'p' (exists) → 'p' (exists), mark isEnd.

t.search("apple"):
  Walk root → a → p → p → l → e. isEnd = true. Return TRUE.  ✓

t.search("app"):
  Walk root → a → p → p. isEnd = true (set during insert("app")). Return TRUE.  ✓

t.search("appl"):
  Walk root → a → p → p → l. isEnd = false (only "apple" extends through here). Return FALSE.  ✓

t.startsWith("app"):
  Walk root → a → p → p. Path exists. Return TRUE.  ✓

t.startsWith("cap"):
  Walk root → 'c' → null. Return FALSE.  ✓
```

---

## 8. Why trie over hashset?

> **Mini-refresher: tries excel at PREFIX operations.**
>
> | Operation | Hashset | Trie |
> |---|---|---|
> | Insert | O(L) | O(L) |
> | Exact search | O(L) | O(L) |
> | startsWith(prefix) | O(N × L) (scan all words) | **O(L)** |
> | Autocomplete (find all words with prefix) | O(N × L) | O(L + total chars of matches) |
> | Longest common prefix | O(N × L) | O(L_min) |
>
> For PREFIX-related tasks, trie is dramatically faster.

Where tries shine: autocomplete, spell-check, IP routing tables, dictionary lookups with wildcards.

---

## 9. Memory considerations

Each TrieNode with `children[26]` uses ~26 pointer slots. For sparse tries (few children per node), most are null — wasted memory.

For a dictionary of 10,000 words averaging 5 chars: ~50,000 nodes × 26 pointers ≈ 5 million pointer slots. ~40 MB on 64-bit systems.

**Alternatives for tighter memory:**
- **Hashmap children**: only store used letters. Slower per-access; smaller for sparse.
- **Compressed trie / radix tree**: merge single-child chains into multi-character edges. Significant savings.
- **Ternary search tree**: hybrid of trie and BST. Good middle ground.

For interview purposes, the 26-array trie is standard.

---

## 10. The shape — prefix operations

The pattern:

> **"Tries are the SPECIALIZED tree for PREFIX operations on strings. O(|word|) insertion and lookup, independent of dictionary size. Each node represents a prefix; each edge a character."**

Where tries appear:

| Use case | Why trie |
|---|---|
| **This problem** | basic operations |
| Autocomplete | O(L + #matches) suggestions |
| Word Search II (multiple words in grid) | match many at once during DFS |
| IP routing tables | longest-prefix-match on IP bits |
| Compression (DEFLATE / LZW) | dictionary structure |
| Maximum XOR | binary trie on bits |
| Replace Words / Map Sum Pairs | LeetCode trie classics |

**Pattern to internalize:**

> "When the problem involves PREFIXES, MANY STRINGS, or WORD MATCHING, reach for a trie. The 26-array + isEnd + insert/search template is your foundation."

---

## Cross-references

- **Reference card (post-mastery):** [`../Implement_Trie_Prefix_Tree.md`](../Implement_Trie_Prefix_Tree.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Design_Add_and_Search_Words_DS.md`](./Design_Add_and_Search_Words_DS.md), [`Maximum_XOR_of_Two_Numbers.md`](./Maximum_XOR_of_Two_Numbers.md).
