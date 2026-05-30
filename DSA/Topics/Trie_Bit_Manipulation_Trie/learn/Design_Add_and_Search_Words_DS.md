# Design Add and Search Words DS — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Design_Add_and_Search_Words_DS.md`](../Design_Add_and_Search_Words_DS.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/design-add-and-search-words-data-structure/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/design-add-and-search-words-data-structure/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: extend the basic trie with a `.` WILDCARD via DFS branching — on `.`, recurse into ALL children.** This pattern generalizes to regex-like search. **Read [`Implement_Trie_Prefix_Tree.md`](./Implement_Trie_Prefix_Tree.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. Why hashset doesn't work
3. Trie + DFS for wildcards
4. The recursive search
5. Code
6. Trace it
7. Common pitfalls
8. The shape — wildcards via branching

---

## 1. Read the problem

Design a class `WordDictionary` supporting:
- `addWord(word)`: add a word.
- `search(word)`: return true if any added word matches. `word` may contain `.` characters, which match ANY SINGLE letter.

**Example:**
```
add("bad"), add("dad"), add("mad")
search("pad") → false
search("bad") → true
search(".ad") → true   (matches "bad", "dad", "mad")
search("b..") → true   (matches "bad")
```

---

## 2. Why hashset doesn't work

A hashset gives O(1) `addWord` and O(1) EXACT `search`. But for wildcard search, you'd need to compare the pattern to every stored word — O(n × L) per query. Slow.

A TRIE handles exact prefix walks in O(L). For wildcards, we EXPLORE multiple paths at each `.`.

---

## 3. Trie + DFS for wildcards

Same trie structure as Implement Trie (`children[26]` + `isEnd`).

For search with wildcards:
- Normal letter at position i: recurse into the SPECIFIC child for that letter.
- `.` at position i: recurse into EVERY non-null child.

If any branch succeeds (reaches end of word with `isEnd = true`), return true.

> **Mini-refresher: branching DFS.**
>
> The `.` wildcard creates a BRANCH POINT in the search. Up to 26 children might match. We try them one by one; if any subsequent recursion succeeds, propagate "true" up. Otherwise return false.
>
> Classic DFS with early return.

---

## 4. The recursive search

```
def dfs(word, idx, node):
    if idx == len(word):
        return node.isEnd
    
    ch = word[idx]
    if ch == '.':
        for child in node.children:
            if child and dfs(word, idx + 1, child):
                return True
        return False
    else:
        c = node.children[ch_index]
        if c is None: return False
        return dfs(word, idx + 1, c)
```

Two branches:
- `.`: try every child.
- Letter: only the specific child.

Base case: end of pattern, check `isEnd`.

---

## 5. Code

**C++:**

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

**Python:**

```python
class WordDictionary:
    def __init__(self):
        self.children = {}
        self.is_end = False
    
    def addWord(self, word):
        cur = self
        for ch in word:
            if ch not in cur.children:
                cur.children[ch] = WordDictionary()
            cur = cur.children[ch]
        cur.is_end = True
    
    def search(self, word):
        def dfs(idx, node):
            if idx == len(word):
                return node.is_end
            ch = word[idx]
            if ch == '.':
                for child in node.children.values():
                    if dfs(idx + 1, child):
                        return True
                return False
            else:
                if ch not in node.children:
                    return False
                return dfs(idx + 1, node.children[ch])
        return dfs(0, self)
```

Complexity:
- `addWord`: **O(L)**.
- `search` (no wildcards): **O(L)**.
- `search` (with wildcards): **O(26^W × L)** worst case (W = # wildcards), much better in practice due to trie pruning.

---

## 6. Trace it

After `addWord("bad")`, `addWord("dad")`, `addWord("mad")`:

```
root
 ├── b → a → d*
 ├── d → a → d*
 └── m → a → d*
```

**`search(".ad")`:**
```
dfs(0, root): ch='.', try each child.
  Try 'b' → dfs(1, b_node): ch='a'. b.children['a'] exists.
    dfs(2, ba_node): ch='d'. ba.children['d'] exists (= bad_node).
      dfs(3, bad_node): idx == len(word). isEnd = true. RETURN TRUE.
  → TRUE propagates.

Return TRUE.  ✓
```

We didn't even need to try 'd' or 'm'.

**`search("b..")`:**
```
dfs(0, root): ch='b'. root.children['b'] exists.
  dfs(1, b_node): ch='.'. Try each child of b_node.
    Only 'a' exists. dfs(2, ba_node): ch='.'. Try each child of ba_node.
      Only 'd' exists. dfs(3, bad_node): idx == len. isEnd=true. RETURN TRUE.

Return TRUE.  ✓
```

---

## 7. Common pitfalls

1. **Treating `.` as matching ZERO OR MORE characters.** It matches EXACTLY ONE character. ".ad" must have length 3.

2. **Forgetting to check isEnd at the recursion base.** Reaching the end of the pattern doesn't mean a word ends — must verify.

3. **Not iterating over ALL children for `.`.** Some implementations only try one child — misses matches.

4. **Returning AFTER finding a path.** Wait — we DO return true on first success (early exit). That's correct. The pitfall would be NOT returning early, slowing things down.

5. **Using a list instead of a 26-array for children.** Iterating list-of-children for `.` wildcard is fine; the 26-array works too. Pick one.

6. **Recursive stack overflow for very long words.** L is typically small (≤ 25 in LeetCode constraints). Iterative version possible but complex.

---

## 8. The shape — wildcards via branching

The pattern:

> **"Wildcards in pattern matching = BRANCHING DFS through the data structure. On a wildcard, try ALL POSSIBILITIES; on a fixed character, follow ONE path."**

| Problem | Branching condition |
|---|---|
| **This problem** | `.` matches any one letter |
| Regular Expression Matching | `*` and `.`; more complex with `*` matching zero-or-more |
| Wildcard Matching | `?` (one char) and `*` (any chars) |
| Word Search II | DFS in grid + trie of words |
| Stream of Characters | trie of reversed words + state on stream |
| Replace Words | trie + DFS through dictionary |

**Pattern to internalize:**

> "DFS branches into all possibilities at wildcards. Trie naturally supports this — each trie node has up to 26 children to choose from."

---

## Cross-references

- **Reference card (post-mastery):** [`../Design_Add_and_Search_Words_DS.md`](../Design_Add_and_Search_Words_DS.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Implement_Trie_Prefix_Tree.md`](./Implement_Trie_Prefix_Tree.md).
  - Coming next: [`Maximum_XOR_of_Two_Numbers.md`](./Maximum_XOR_of_Two_Numbers.md) — BINARY trie.
