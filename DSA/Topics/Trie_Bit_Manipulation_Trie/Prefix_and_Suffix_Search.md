# Prefix and Suffix Search

**Problem Link:**
https://leetcode.com/problems/prefix-and-suffix-search/

**Topic:**
Trie / Bit Manipulation Trie

----------------------------------------

## Step 1: The Task

Design a class `WordFilter`:
- Constructor takes a list of `words`.
- `f(prefix, suffix)` returns the **largest index** of a word in the list that has the given `prefix` AND the given `suffix`. If none exists, return −1.

Example: `words = ["apple"]`.
- `f("a", "e")` — "apple" starts with "a" and ends with "e". Index 0.
- `f("b", "")` — no word starts with "b". Return −1.

With multiple words sharing the same prefix+suffix combo, pick the **largest** index. This favors later insertions — useful for "most recent wins" semantics.

----------------------------------------

## Step 2: Two Separate Searches — and Why It's Not Enough

The naive thought: build one trie for prefix lookups (forward trie) and another for suffix lookups (reverse trie, storing reversed words). For a query:
1. Find all words matching the prefix (set A).
2. Find all words matching the suffix (set B).
3. Return max(A ∩ B) or −1.

Works conceptually. But:
- Intersecting two possibly-large sets per query is expensive.
- For n words and q queries, worst-case O(n · q) — too slow when both are large.

We need a structure where a single lookup answers both constraints at once.

----------------------------------------

## Step 3: The Trick — Fuse Suffix and Prefix into One Key

What if we could encode **both** the suffix and the prefix into a single string that a trie can search?

For each word `w`, generate **every pair (suffix of w, w)**, joined by a delimiter like `#`:

```
"apple" produces:
  "#apple", "e#apple", "le#apple", "ple#apple",
  "pple#apple", "apple#apple"
```

That's `|w| + 1` entries per word (for each possible suffix, including empty).

Now a query `f(prefix, suffix)` becomes: search the combined trie for words starting with `suffix + "#" + prefix`. A single trie traversal picks up everything that matches both.

Why does this work? A generated key `"le#apple"` starts with `"le"` before the `#` and `"apple"` after. If a query string is `"le#ap"`, it matches this key's prefix (the key continues with `ple` after `"le#ap"`, which is fine — we're just checking the query is a prefix of the key).

So **suffix + # + prefix** lines up with our generated keys perfectly.

The `#` is a delimiter that isn't a letter, ensuring the suffix portion can't bleed into the prefix portion.

----------------------------------------

## Step 4: Storing the Word's Index

At every trie node, store the **maximum index** of any word whose generated key passes through that node. Why max? Because the problem asks for the largest index among matches.

When we insert word `words[i]`, walk the trie for each of its generated keys; at every node, update `node.max_index = max(node.max_index, i)`.

On query: traverse the trie with the query string. If we reach the end, return the `max_index` at the final node — that's the largest word-index whose generated key has this prefix. If we can't traverse (character missing), return −1.

----------------------------------------

## Step 5: Algorithm

```
class WordFilter:
    def __init__(words):
        root = Trie node.
        for i, w in enumerate(words):
            for k in 0..len(w):           # k = suffix start index
                key = w[k:] + "#" + w
                insert key into trie; at each node update max_index = max(..., i)

    def f(prefix, suffix):
        query = suffix + "#" + prefix
        cur = root
        for c in query:
            if c not in cur.children: return -1
            cur = cur.children[c]
        return cur.max_index
```

Insertion cost per word: O(|w|²) (|w|+1 suffixes × up to |w| chars each). Query cost: O(|prefix| + |suffix|).

----------------------------------------

## Step 6: Trace

`words = ["apple", "ape"]`. Insert both.

For "apple" (index 0), generate 6 keys:
- "apple#apple", "pple#apple", "ple#apple", "le#apple", "e#apple", "#apple"

For "ape" (index 1), generate 4 keys:
- "ape#ape", "pe#ape", "e#ape", "#ape"

As we insert keys, each node stores the max word-index passing through. Overlap happens, e.g., both "e#apple" (index 0) and "e#ape" (index 1) share prefix "e#a". Nodes along that prefix see both indices — store max = 1.

**Query `f("a", "e")`** — prefix "a", suffix "e". Query string: "e#a".

Walk the trie for "e#a":
- "e" → exists (both "apple" and "ape" generate "e#..." keys).
- "#" → exists.
- "a" → exists; max_index at this node is max(0, 1) = 1.

Return **1** ("ape"). Correct — both "apple" and "ape" match prefix "a" + suffix "e", and 1 is the larger index.

**Query `f("ap", "le")`** — query string: "le#ap".

Walk:
- "l" → exists in trie? Only from "apple" keys (index 0). ✓
- "e" → ✓ (next in "le#apple").
- "#" → ✓.
- "a", "p" → ✓.

Final node's max_index = 0. Return **0**. Only "apple" matches "ap" + "le". ✓

**Query `f("b", "")`** — query string: "#b".

Walk: "#" ✓, "b" → doesn't exist (no word starts with "b"). Return **−1**. ✓

----------------------------------------

## Step 7: Why the Delimiter `#` Matters

Suppose we didn't use `#`. Key for "apple" would include "leapple" (suffix "le" + word "apple"). A query with prefix "leap" and suffix "" would produce query string "leap" — and "leap" is a prefix of "leapple". False positive.

`#` (not a letter) prevents the letters of suffix from blending into letters of the word. It's a **guard character**, making the boundary unambiguous. Any character that never appears in words works.

Also, storing suffix **first** (before prefix) is important: the prefix portion of the key sits at the *end*, which means word-length variation doesn't prevent match-by-prefix. Try it the other way (prefix + # + suffix) and the match logic breaks.

----------------------------------------

## Step 8: Name It

**Dual-key trie** or **suffix-concatenation trick**. A specific pattern for combining two independent constraints (prefix + suffix match) into a single trie lookup.

Related ideas:
- **Suffix trees / suffix automata** for arbitrary substring queries.
- **Aho-Corasick** for multi-pattern matching.
- In general, when you need to index strings for multiple query types, consider **key augmentation** — concatenating with delimiters to encode both constraints into one structure.

----------------------------------------

## Step 9: Complexity

Let L = max word length, n = number of words, m = query prefix + suffix lengths.

- **Construction**: O(n · L²) time and space (per word: L+1 suffixes × L chars).
- **Query**: O(m) per call.

For n · L² within memory budget (typically both ≤ 10), this is fast.

----------------------------------------

## Step 10: C++ Implementation

```cpp
class WordFilter {
    struct Node {
        Node* ch[27] = {};      // 26 letters + '#'
        int idx = -1;
    };
    Node* root = new Node();

    int chIndex(char c) {
        return c == '#' ? 26 : c - 'a';
    }

    void insert(const string& s, int wordIdx) {
        Node* cur = root;
        for (char c : s) {
            int k = chIndex(c);
            if (!cur->ch[k]) cur->ch[k] = new Node();
            cur = cur->ch[k];
            cur->idx = max(cur->idx, wordIdx);
        }
    }

public:
    WordFilter(vector<string>& words) {
        for (int i = 0; i < (int)words.size(); ++i) {
            const string& w = words[i];
            for (int k = 0; k <= (int)w.size(); ++k) {
                insert(w.substr(k) + "#" + w, i);
            }
        }
    }

    int f(string prefix, string suffix) {
        string q = suffix + "#" + prefix;
        Node* cur = root;
        for (char c : q) {
            int k = chIndex(c);
            if (!cur->ch[k]) return -1;
            cur = cur->ch[k];
        }
        return cur->idx;
    }
};
```

Key lines:
- Insert every **suffix + # + word** combination with the word's index.
- At each node, track the **max** word index passing through (later insertions overwrite for ties).
- Query: walk `suffix + # + prefix`; if the walk completes, return the node's idx.

----------------------------------------

## Step 11: Follow-up Questions

- **Memory concern for longer words.** For L = 20 and n = 15000, n · L² = 6M nodes — big but typically OK. For larger L, consider a **suffix array** + **prefix trie** hybrid or Aho-Corasick.
- **Return all matching words instead of just the max-index one.** At each node, store a list (or sorted set) of indices; still O(answer count) per query.
- **Insertion after construction.** Same trie supports live inserts; just update max_index at traversed nodes.
- **Why store max index, not just presence?** Problem requires the **largest** index; storing max at each node avoids scanning all matches.
- **What if words contain `#`?** Pick a different delimiter. In practice, use a character outside the problem's alphabet.
- **Alternative approach: two tries + suffix indices.** Build a prefix trie and suffix trie, each node holding a sorted list of word indices. Query: intersect the two lists, take max. Memory-efficient but per-query intersection cost makes it slower.
