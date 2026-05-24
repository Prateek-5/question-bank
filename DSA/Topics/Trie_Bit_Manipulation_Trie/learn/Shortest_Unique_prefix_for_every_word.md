# Shortest Unique Prefix for Every Word — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Shortest_Unique_prefix_for_every_word.md`](../Shortest_Unique_prefix_for_every_word.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://www.geeksforgeeks.org/find-all-shortest-unique-prefixes-to-represent-each-word-in-a-given-list/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The lesson: AUGMENT each trie node with a COUNT of words passing through it. For each word, the shortest unique prefix ends at the first node with count = 1.** Classic trie-augmentation technique. **Read [`Implement_Trie_Prefix_Tree.md`](./Implement_Trie_Prefix_Tree.md) first.**

**Map of this file (7 short sections):**

1. Read the problem
2. The trie + count augmentation
3. Walking for each word
4. Code
5. Trace it
6. Common pitfalls
7. The shape — trie augmentation

---

## 1. Read the problem

Given an array of words, return for each word the **shortest PREFIX** that is unique (not a prefix of any OTHER word in the array).

**Example:** `["zebra", "dog", "duck", "dove"]`.

- "zebra" → "z" (no other word starts with z).
- "dog" → "dog" (others starting with d: duck, dove — neither starts with "do" → wait, "dov" and "do" both share "do" with "dog"). Actually "do" matches dog and dove. "dog" disambiguates. Answer "dog".
- "duck" → "du" (others starting with "du": none).
- "dove" → "dov".

Output: `["z", "dog", "du", "dov"]`.

---

## 2. The trie + count augmentation

> **Mini-refresher: trie nodes track how many words pass through.**
>
> Build a trie. Add a `count` field to each TrieNode. As we INSERT each word, increment `count` at every visited node.
>
> After all insertions, `node.count` = number of WORDS whose path passes through this node = number of words with this prefix.

```
def insert(word):
    cur = root
    for ch in word:
        if ch not in cur.children: cur.children[ch] = TrieNode()
        cur = cur.children[ch]
        cur.count += 1
```

---

## 3. Walking for each word

For each word, walk its path through the trie. The FIRST node with `count == 1` is the END of its shortest unique prefix (only this word passes through here).

```
def find_unique_prefix(word):
    cur = root
    prefix = ""
    for ch in word:
        cur = cur.children[ch]
        prefix += ch
        if cur.count == 1:
            return prefix
    return prefix      # word is a prefix of another; use full word
```

---

## 4. Code

**C++:**

```cpp
struct TrieNode {
    TrieNode* children[26] = {nullptr};
    int count = 0;
};

class Solution {
    TrieNode* root;

    void insert(const string& word) {
        TrieNode* cur = root;
        for (char ch : word) {
            int idx = ch - 'a';
            if (!cur->children[idx]) cur->children[idx] = new TrieNode();
            cur = cur->children[idx];
            cur->count++;
        }
    }

    string findPrefix(const string& word) {
        TrieNode* cur = root;
        string prefix;
        for (char ch : word) {
            prefix += ch;
            cur = cur->children[ch - 'a'];
            if (cur->count == 1) return prefix;
        }
        return prefix;
    }

public:
    vector<string> findPrefixes(vector<string>& words) {
        root = new TrieNode();
        for (const string& w : words) insert(w);
        vector<string> result;
        for (const string& w : words) result.push_back(findPrefix(w));
        return result;
    }
};
```

Complexity: **O(N × L) time + space** (N words, L avg length).

---

## 5. Trace it

`["zebra", "dog", "duck", "dove"]` → counts at each trie node:

```
root
├── z[1] → e[1] → b[1] → r[1] → a[1]
└── d[3]
    ├── o[2]
    │    ├── g[1]
    │    └── v[1] → e[1]
    └── u[1] → c[1] → k[1]
```

For each word, find first count=1:
- "zebra": z has count 1 → return "z".
- "dog": d(3) → o(2) → g(1) → return "dog".
- "duck": d(3) → u(1) → return "du".
- "dove": d(3) → o(2) → v(1) → return "dov".

Output: `["z", "dog", "du", "dov"]`. ✓

---

## 6. Common pitfalls

1. **Incrementing count on the ROOT.** No — only after entering a child.

2. **Looking for count = 0 (or count > 1).** First count = 1 is the EARLIEST unique prefix.

3. **Not handling words that are prefixes of others.** E.g., "do" and "dog" both inserted: at node `o` count = 2, at `g` count = 1. For "do", we'd never find count = 1 → use the full word. The algorithm correctly returns "do" in this edge case (though it's the same length as the original; nothing shorter exists).

4. **Duplicate words.** Sometimes the input may have duplicates; counts inflate. Algorithm still works (returns a longer prefix), but edge-case behavior depends on requirements.

5. **Treating "shortest" as char-by-char rather than node-by-node.** They're the same since edges are single characters.

---

## 7. The shape — trie augmentation

The pattern:

> **"Augment trie nodes with AGGREGATE data (count, sum, max-priority, etc.) to answer richer queries in O(L)."**

| Augmentation | Use case |
|---|---|
| **This problem** (count) | shortest unique prefix |
| sum_of_word_weights | weighted autocomplete |
| max_priority_in_subtrie | most-popular word with prefix |
| isEnd flag | word vs prefix distinction (basic trie) |
| word_index | which word ends here (for substring search) |

**Pattern to internalize:**

> "Tries become MUCH MORE POWERFUL when each node stores AGGREGATE INFORMATION about words passing through. The COUNT augmentation is the simplest and most useful."

---

## Cross-references

- **Reference card (post-mastery):** [`../Shortest_Unique_prefix_for_every_word.md`](../Shortest_Unique_prefix_for_every_word.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Implement_Trie_Prefix_Tree.md`](./Implement_Trie_Prefix_Tree.md), [`Design_Add_and_Search_Words_DS.md`](./Design_Add_and_Search_Words_DS.md).
  - Coming next: [`Prefix_and_Suffix_Search.md`](./Prefix_and_Suffix_Search.md), [`Subarrays_with_XOR_Less_Than_K_Concept.md`](./Subarrays_with_XOR_Less_Than_K_Concept.md), [`Count_Substrings_That_Differ_by_One_Character.md`](./Count_Substrings_That_Differ_by_One_Character.md).
