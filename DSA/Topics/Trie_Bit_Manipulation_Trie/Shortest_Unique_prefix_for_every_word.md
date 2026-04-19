# Shortest Unique Prefix for Every Word

**Problem Link:**
https://www.geeksforgeeks.org/find-all-shortest-unique-prefixes-to-represent-each-word-in-a-given-list/

**Topic:**
Trie / Bit Manipulation Trie

----------------------------------------

## Step 1: Read the Problem

Given an array of words, for each word, find the **shortest prefix** that is unique to that word (no other word in the array starts with that prefix).

Example: `["zebra", "dog", "duck", "dove"]`.
- "zebra": starts with 'z', unique. Shortest prefix: "z".
- "dog": starts with 'd'. But "duck", "dove" also start with 'd'. Try "do" — matches "dog", "dove". Try "dog" — unique (other d-words: duck doesn't start with "dog", dove doesn't). Answer: "dog".
- "duck": "d" not unique. "du" — matches "duck" only (others are dog, dove which don't start "du"). Answer: "du".
- "dove": "d" not unique. "do" matches dog and dove. "dov" — unique. Answer: "dov".

Output: `["z", "dog", "du", "dov"]`.

----------------------------------------

## Step 2: Brute-Force Thought

For each word, try prefix lengths 1, 2, 3, ... Check whether the prefix appears as a prefix of any other word. Return the shortest unique one.

O(n² · L²) — n words, n prefix-checks per word, L length per check. Too slow for large inputs.

----------------------------------------

## Step 3: A Trie Makes This Natural

Build a trie of all words. For each node in the trie, count **how many words pass through it** (how many words share this prefix).

Once the trie is built and prefix counts known, for each word, walk its characters down the trie. The shortest prefix whose count is **1** (only this word passes through) is the answer.

Specifically: for each word, walk down the trie character by character, tracking the count at each node. The first node where count == 1 marks the end of the shortest unique prefix.

----------------------------------------

## Step 4: Build the Trie

Each trie node stores a `count` — how many words pass through this node.

```
insert(word):
    cur = root
    for ch in word:
        if cur.children[ch] is null: cur.children[ch] = new Node()
        cur = cur.children[ch]
        cur.count += 1
```

After inserting all words, each node's count is the number of words whose prefix reaches this node.

----------------------------------------

## Step 5: Find Each Word's Unique Prefix

For each word, walk characters in order; output the prefix up to and including the first node with `count == 1`.

```
findPrefix(word):
    cur = root
    prefix = ""
    for ch in word:
        prefix += ch
        cur = cur.children[ch]
        if cur.count == 1:
            return prefix
    return prefix   # in case word itself is a prefix of another (unusual)
```

If we never find count == 1 along the way, the word is a prefix of another word. In that case, the entire word is the "unique prefix" (but actually, there's no shorter unique prefix; using the whole word is acceptable).

----------------------------------------

## Step 6: Trace on `["zebra", "dog", "duck", "dove"]`

Build trie. Show count at each node:

```
root (count = irrelevant)
├── z (1)
│   └── e (1) → b (1) → r (1) → a (1)
└── d (3)
    ├── o (2)
    │   ├── g (1)
    │   └── v (1) → e (1)
    └── u (1) → c (1) → k (1)
```

For "zebra":
- 'z' count 1. Return "z".

For "dog":
- 'd' count 3. Continue.
- 'o' count 2. Continue.
- 'g' count 1. Return "dog".

For "duck":
- 'd' count 3. Continue.
- 'u' count 1. Return "du".

For "dove":
- 'd' count 3. Continue.
- 'o' count 2. Continue.
- 'v' count 1. Return "dov".

Output: ["z", "dog", "du", "dov"]. ✓

----------------------------------------

## Step 7: Why Count == 1 Is the Cutoff

If count at a node is `c`, there are `c` words that share this prefix. If `c == 1`, only one word passes through — this node is a unique prefix.

Going one character further into the trie doesn't help — it's already uniquely identifying.

Going one character less doesn't uniquely identify — the count at the previous node was `> 1`.

So the first node with count == 1 marks the shortest unique prefix endpoint.

----------------------------------------

## Step 8: Name It

**Trie with prefix counts.** A standard augmentation: store aggregate info (count) at each node for O(L) prefix queries.

Related:
- Autocomplete (count via popularity).
- Spell-check (find closest word via edit distance + trie).
- IP routing (longest-prefix match).

Once you have a trie, augmenting it with per-node stats unlocks many query types.

----------------------------------------

## Step 9: Complexity

Build: **O(total characters)** = O(n · L) where L = average word length.
Query per word: **O(L)**.
Total: **O(n · L)** for all words.

Space: **O(total characters)** for the trie.

Much better than brute-force O(n² · L²).

----------------------------------------

## Step 10: C++ Implementation

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
        return prefix;   // word is a prefix of another; use whole word
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

Two passes: insert all words, then query each. Clean.

----------------------------------------

## Step 11: Follow-up Questions

- **Handle duplicate words in input.** The count at leaf nodes can be > 1 even for the word itself. Algorithm still works if we pick the first count==1 node along the path (may not exist — all counts may be ≥ 2).
- **Words with shared suffixes.** Trie indexed by forward prefix doesn't help for suffix queries; use a reverse trie.
- **Online: words arrive over time, query current unique prefixes.** Update counts on insert; handle deletions similarly.
- **Unique suffixes instead.** Build a trie of reversed words; same algorithm.
- **Memory optimization.** Use hashmap children for sparse alphabets.
- **Output the longest unique prefix (not shortest).** Different question — walk until count changes or word ends.
