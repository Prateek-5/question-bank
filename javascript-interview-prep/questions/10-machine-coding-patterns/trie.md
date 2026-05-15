# Implement a Trie (insert, search, startsWith)

## Source
- Canonical data-structures interview problem (LeetCode #208 "Implement Trie (Prefix Tree)").
- Used in autocomplete, spellcheckers, IP routing tables, URL routers (Express, Fastify).

## Why this question matters in interviews
Trie is the **string-keyed tree** every backend engineer should know. The naive substring-match approach (loop over a list, check prefix) is O(n*L) per query; a trie collapses this to O(L) — independent of the dictionary size. Implementing one tests **Map-of-Map nesting**, **path-walking with create-or-traverse**, **end-of-word marking**, and the ability to spot when a problem really is a tree problem in disguise. Backend interviewers ask trie when probing **URL routers** (Express stores routes in a trie-like radix tree), **autocomplete services**, **IP longest-prefix matches**, **rate limiter buckets keyed by API path**, and **command-completion in CLIs**. The implementation is small; the family of problems it unlocks is huge.

## Concepts involved

### Syntax to lock in
```js
class TrieNode {
  constructor() {
    this.children = new Map();    // char -> TrieNode
    this.isEnd = false;            // does a word end here?
  }
}

class Trie {
  constructor() { this.root = new TrieNode(); }

  insert(word) {
    let node = this.root;
    for (const c of word) {
      if (!node.children.has(c)) node.children.set(c, new TrieNode());
      node = node.children.get(c);
    }
    node.isEnd = true;
  }

  search(word) {
    const n = this._walk(word);
    return !!n && n.isEnd;
  }

  startsWith(prefix) {
    return !!this._walk(prefix);
  }

  _walk(s) {
    let node = this.root;
    for (const c of s) {
      node = node.children.get(c);
      if (!node) return null;
    }
    return node;
  }
}
```

### Runtime / engine behavior
- The trie is a **tree where edges are labelled by characters**. The root holds the empty prefix.
- `children` is a Map (or plain object) keyed by single characters. For ASCII-only dictionaries you can use an array of size 26, but Map handles Unicode for free.
- `isEnd` is the **terminator flag** — without it you can't distinguish "this prefix is a valid word" from "this prefix is just on the way to longer words." `insert('cat')` and `insert('cats')` need both `t` (after `ca`) and `s` (after `cat`) to have `isEnd=true`.
- Time complexity is O(L) where L is the length of the input word — **independent of the dictionary size**. This is the trie's killer feature.
- Space is O(total characters across all inserted words) in the worst case (no sharing). Real corpora share heavy prefixes and use much less.

### Edge cases (these are the interview traps)
1. **Empty string** — `insert('')` should mark the root as `isEnd`. `search('')` → true. `startsWith('')` → true (every string starts with empty). Some impls reject empty; spec your behavior.
2. **`search` vs `startsWith` confusion** — `search` requires `isEnd`; `startsWith` doesn't. The two are the same walk with a different terminal check. Classic LeetCode test.
3. **Repeated insert of the same word** — should be idempotent. `isEnd` flips to true (already true) — no duplicate stored.
4. **Case sensitivity** — by default the trie is case-sensitive. If you want case-insensitive lookup, lowercase at the boundary, not inside.
5. **Unicode / surrogate pairs** — iterating with `for (const c of word)` correctly handles BMP and astral plane code points. Iterating with `for (let i = 0; i < word.length; i++)` splits surrogate pairs. Use `for...of`.
6. **Deletion** — not commonly asked, but: walk to the end, flip `isEnd=false`, then walk back deleting nodes that have no children AND are not `isEnd`. Easy to get wrong; rehearse if asked.
7. **Memory for sparse tries** — if you use a fixed-size array (size 26 or 128) per node, sparse tries waste massive memory. Map per node is the safe default. Radix/PATRICIA tries compress chains-of-single-children into a single edge — common in production routers.
8. **Autocomplete (collect all words with prefix)** — walk to the prefix node, then DFS the subtree collecting every path that ends at `isEnd`. O(prefix length + answer size).

## Brute force approach
"I'll store words in a Set; for `search`, check `set.has(word)`; for `startsWith`, iterate the set and check `word.startsWith(prefix)`." Works but `startsWith` is O(n * L) — for a million-word dictionary, every autocomplete keystroke scans the whole set. Trie reduces this to O(L). State the trade-off and pick trie when prefix queries dominate.

Another non-starter: sort the dictionary and binary-search by prefix. Better than the Set approach (O(L log n)), still worse than O(L) trie. Only worth it if you also need ordered iteration — but a sorted trie traversal gives you that too.

## Optimal approach
Map-of-Map tree. `children: Map<char, TrieNode>` per node, `isEnd: boolean`. Insert walks creating nodes as needed; `_walk` is shared by `search` and `startsWith`. O(L) per operation, O(total chars) space.

## Solution (JavaScript)

```js
/**
 * Trie (prefix tree). Stores strings; supports O(L) exact lookup and prefix
 * lookup independent of dictionary size.
 */
class TrieNode {
  constructor() {
    this.children = new Map();
    this.isEnd = false;
  }
}

class Trie {
  constructor() {
    this.root = new TrieNode();
  }

  /** Insert a word. Idempotent. */
  insert(word) {
    let node = this.root;
    for (const ch of word) {
      let next = node.children.get(ch);
      if (!next) {
        next = new TrieNode();
        node.children.set(ch, next);
      }
      node = next;
    }
    node.isEnd = true;
  }

  /** Exact-match lookup. */
  search(word) {
    const node = this._walk(word);
    return !!node && node.isEnd;
  }

  /** Any inserted word starts with `prefix`? */
  startsWith(prefix) {
    return !!this._walk(prefix);
  }

  /** Walk down by characters; return the node at the end, or null. */
  _walk(s) {
    let node = this.root;
    for (const ch of s) {
      node = node.children.get(ch);
      if (!node) return null;
    }
    return node;
  }

  /** Autocomplete: all stored words that start with `prefix`. */
  autocomplete(prefix, limit = Infinity) {
    const startNode = this._walk(prefix);
    if (!startNode) return [];
    const out = [];
    const dfs = (node, path) => {
      if (out.length >= limit) return;
      if (node.isEnd) out.push(path);
      for (const [ch, child] of node.children) dfs(child, path + ch);
    };
    dfs(startNode, prefix);
    return out;
  }
}
```

## Step-by-step dry run

Input:
```js
const t = new Trie();
t.insert('cat');
t.insert('cats');
t.insert('cup');
t.insert('cap');

t.search('cat');         // true
t.search('ca');          // false (not isEnd)
t.search('cats');        // true
t.startsWith('ca');      // true
t.startsWith('cab');     // false
t.autocomplete('ca');    // ['cat','cats','cap']
```

Trace tree after inserts (text):
```
root
└── c
    └── a
    │   ├── t  (isEnd)
    │   │   └── s  (isEnd)
    │   └── p  (isEnd)
    └── u
        └── p  (isEnd)
```

- `insert('cat')`: walk c → a (create) → t (create). Mark t.isEnd=true.
- `insert('cats')`: walk c → a → t (exists) → s (create). Mark s.isEnd=true. (t.isEnd still true.)
- `insert('cup')`: walk c → u (create) → p (create). Mark p.isEnd=true.
- `insert('cap')`: walk c → a → p (create). Mark p.isEnd=true.
- `search('cat')`: walk reaches t-node. `t.isEnd === true` → true.
- `search('ca')`: walk reaches a-node. `a.isEnd === false` → false.
- `startsWith('ca')`: walk reaches a-node → true (not null).
- `startsWith('cab')`: walk c → a → b. b not in children. Return null → false.
- `autocomplete('ca')`: walk to a-node, DFS. Visits t (isEnd, push 'cat'), then s (isEnd, push 'cats'), then p (isEnd, push 'cap'). Returns ['cat','cats','cap'].

## Important takeaways

**Syntax to memorize**
- `class TrieNode { children = new Map(); isEnd = false; }`.
- Insert: `for (const ch of word) { if (!has) create; node = next; } node.isEnd = true;`.
- Shared `_walk` helper for search and startsWith — keeps DRY.
- O(L) per op, regardless of dictionary size.

**Patterns to reuse**
- Trie nesting (Map of Map) is the same shape as: nested router tables, telephone-number area-code trees, IP prefix tables.
- DFS-collect pattern (`autocomplete`) is the canonical "walk to a point, then enumerate the subtree" — same shape as filesystem `find` with a base path.

**Common mistakes**
- Forgetting `isEnd` — can't distinguish "cat is a word" from "ca is on the way to cats." `search('ca')` returns true incorrectly.
- Using `word.length` + index loops on Unicode strings — splits surrogate pairs. Always `for (const ch of word)`.
- Using a fixed-size array per node for non-ASCII alphabets — wastes memory or breaks on non-ASCII input.
- Trying to optimize prematurely with a radix trie before you've measured. Map-of-Map is fast enough for most interview workloads.
- Calling `Object.create(null)` for children instead of Map. Works but loses iteration order and the helpful Map API.

**Related questions**
- Suffix tree / suffix array (similar idea for substring queries).
- Radix / PATRICIA trie (compressed chains).
- Aho-Corasick (multi-pattern matching on top of trie).
- Express route trie / Fastify radix router.
- Longest-prefix-match for IP routing.

## Variants

1. **Word-count / multiset trie** — store a counter at each `isEnd` instead of a boolean. Supports `count(word)` and `decrement(word)` for word-frequency tasks.

2. **Wildcard search** — support `?` (any single char) or `*` (any sequence). DFS with backtracking; explore all children when seeing `?`. LeetCode #211 "Add and Search Word."

3. **Autocomplete ranked by frequency** — store a frequency in each node (or at `isEnd`). Maintain a heap during DFS to keep top-K. Used in real autocomplete services.

4. **Compressed (radix) trie** — collapse single-child chains: edges hold strings, not single chars. Used by Express/Fastify routers. Implementation is fiddlier; mention as the production-grade variant.

5. **Persistent (immutable) trie** — each insert returns a new root sharing unchanged subtrees. Functional data structure; used in Clojure/Immutable.js.

## Revision notes

> **Trie — 60 second recap**
> - Node = `{ children: Map<char, Node>, isEnd: boolean }`. Root is empty.
> - `insert(word)`: walk, create nodes for missing chars, mark last `isEnd=true`.
> - `search(word)`: walk; return true iff end node exists AND `isEnd`.
> - `startsWith(prefix)`: walk; return true iff end node exists. (no isEnd check)
> - O(L) per op, independent of dictionary size.
> - Autocomplete: walk to prefix node, DFS collecting `isEnd` paths.
> - Trap: forgetting `isEnd` conflates "prefix" with "word." Using indexed loops splits surrogate pairs. Fixed-size arrays waste memory.
> - Family: URL routers, IP prefix tables, autocomplete, suffix trees, Aho-Corasick.
