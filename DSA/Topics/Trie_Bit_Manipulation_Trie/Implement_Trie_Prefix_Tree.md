# Implement Trie (Prefix Tree)

**Problem Link:**
<a href="https://leetcode.com/problems/implement-trie-prefix-tree/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/implement-trie-prefix-tree/</a>

**Topic:**
Trie / Bit Manipulation Trie

----------------------------------------

## Step 1: What's a Trie?

Design a data structure supporting:
- `insert(word)`: add word to the trie.
- `search(word)`: return true if word is in the trie.
- `startsWith(prefix)`: return true if any word starts with the prefix.

Words are lowercase letters only.

Think of a trie as a **branching tree** where each edge is labeled with a character. Traversing from root along the edges spells out words.

Example after inserting "apple", "app", "bat":

```
       (root)
      /      \
    a          b
    |          |
    p          a
    |          |
    p*         t*
    |
    l
    |
    e*
```

`*` marks nodes where a word ends.

`search("apple")` traverses a-p-p-l-e, ends at a '*' node. True.
`search("app")` traverses a-p-p, ends at a '*' node. True.
`search("appl")` traverses a-p-p-l, ends at a non-* node. False.
`startsWith("appl")` traverses a-p-p-l, ends somewhere valid. True.
`startsWith("cap")` can't start with 'c' (no 'c' child at root). False.

----------------------------------------

## Step 2: Data Structure Design

Each trie node has:
- **Children**: for each possible next letter, either null or another node. Since we have 26 lowercase letters, a fixed-size array `children[26]` works.
- **End-of-word marker**: boolean `isEnd` — true if a word ends at this node.

Root is a special node with no character label.

----------------------------------------

## Step 3: Insert

Traverse character by character. If the child for the current letter doesn't exist, create it. After processing all letters, mark the current node as end-of-word.

```
def insert(word):
    cur = root
    for ch in word:
        if cur.children[ch] is null:
            cur.children[ch] = new Node()
        cur = cur.children[ch]
    cur.isEnd = True
```

O(|word|).

----------------------------------------

## Step 4: Search

Similar to insert, but don't create missing children — return false if missing. At the end, check `isEnd`.

```
def search(word):
    cur = root
    for ch in word:
        if cur.children[ch] is null: return False
        cur = cur.children[ch]
    return cur.isEnd
```

O(|word|).

----------------------------------------

## Step 5: startsWith

Almost identical to search, but we don't require the final node to be end-of-word. Just need to traverse the full prefix successfully.

```
def startsWith(prefix):
    cur = root
    for ch in prefix:
        if cur.children[ch] is null: return False
        cur = cur.children[ch]
    return True
```

Same walk as search, just without the `isEnd` check.

----------------------------------------

## Step 6: Trace Insert → Search → startsWith

Insert "apple":
- Start at root. No 'a' child. Create. Move to 'a'.
- No 'p' child. Create. Move to 'p'.
- No 'p' child. Create. Move to 'p'.
- No 'l' child. Create. Move to 'l'.
- No 'e' child. Create. Move to 'e'.
- Mark 'e' node as isEnd.

Insert "app":
- 'a' exists. Move.
- 'p' exists. Move.
- 'p' exists. Move.
- Mark second 'p' node as isEnd.

Now:
- search("app"): traverse a-p-p, reach the second 'p' node, isEnd = true. Return true. ✓
- search("appl"): traverse a-p-p-l, reach 'l' node, isEnd = false. Return false. ✓
- startsWith("app"): traverse a-p-p, success. Return true. ✓
- search("apply"): traverse a-p-p-l, then look for 'y' child of 'l'. Doesn't exist. Return false. ✓

----------------------------------------

## Step 7: Why a Trie Over a Hashset?

For simple `search(word)`, a hashset of words is O(|word|) too — just as fast.

For `startsWith(prefix)`, a hashset would need O(n·|prefix|) in the worst case (check every stored word). A trie does it in O(|prefix|).

**Tries excel at prefix operations.** If your workload includes:
- Autocomplete.
- Spell-check (find close words).
- Longest common prefix.
- Multi-word lookups.

...then a trie's pointer-based structure pays off.

----------------------------------------

## Step 8: Memory Considerations

Each node has 26 pointers (for lowercase). Many will be null. Memory footprint can be substantial for large dictionaries.

Alternatives:
- **Hashmap children**: only store used letters. Slower per-access but memory-efficient for sparse tries.
- **Compressed trie (radix tree)**: merge chains of single-child nodes into multi-character edges. Significantly faster in practice.

For interviews, the 26-pointer array is standard and usually accepted.

----------------------------------------

## Step 9: Complexity

Insert: **O(|word|)**.
Search: **O(|word|)**.
startsWith: **O(|prefix|)**.
Space: O(total characters × 26) pointer capacity.

----------------------------------------

## Step 10: C++ Implementation

```cpp
class Trie {
    struct Node {
        Node* children[26] = {nullptr};
        bool isEnd = false;
    };
    Node* root;

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

private:
    Node* traverse(const string& s) {
        Node* cur = root;
        for (char ch : s) {
            int idx = ch - 'a';
            if (!cur->children[idx]) return nullptr;
            cur = cur->children[idx];
        }
        return cur;
    }
};
```

`traverse` is a shared helper. `search` adds the `isEnd` check; `startsWith` is satisfied by non-null traversal result.

----------------------------------------

## Step 11: Follow-up Questions

- **Support word deletion.** Adds complexity — need to carefully unmark isEnd and potentially remove empty subtries.
- **Case-sensitive support.** Expand children array to 52 (or use a hashmap).
- **Unicode support.** Use `unordered_map<char, Node*>` children.
- **Autocomplete: return all words with a given prefix.** DFS from the prefix's endpoint to collect all isEnd paths.
- **Count words with a prefix.** Store a word-count at each node (incremented on insert).
- **Longest common prefix of all stored words.** Walk down while each node has exactly 1 child and isn't isEnd.
