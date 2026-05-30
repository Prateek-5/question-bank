# Implement a Trie (insert / search / startsWith)

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md), [`concepts/recursion.md`](../../concepts/recursion.md)
>
> **Source:** <a href="https://leetcode.com/problems/implement-trie-prefix-tree/" target="_blank" rel="noopener noreferrer">LeetCode 208 — Implement Trie (Prefix Tree)</a>. Used in autocomplete, URL routers (Express, Fastify), IP routing tables.

---

## 1. Problem statement

**Signature**
```ts
class Trie {
  insert(word: string): void;
  search(word: string): boolean;       // exact match
  startsWith(prefix: string): boolean; // any inserted word with this prefix
  autocomplete(prefix: string, limit?: number): string[];   // optional
}
```

**Input / Output examples**

| Operation                         | Result                                   |
|-----------------------------------|------------------------------------------|
| `insert('cat'); insert('cats'); insert('cup'); insert('cap')` |  |
| `search('cat')`                   | `true`                                   |
| `search('ca')`                    | `false` (not a stored word)             |
| `search('cats')`                  | `true`                                   |
| `startsWith('ca')`                | `true`                                   |
| `startsWith('cab')`               | `false`                                  |
| `autocomplete('ca')`              | `['cat', 'cats', 'cap']`                |

**Constraints**
- O(L) per op where L = word/prefix length — independent of dictionary size.
- `isEnd` boolean distinguishes "stored word" from "internal node."
- Node = `{ children: Map<char, Node>, isEnd: boolean }`.

---

## 2. Plain-English restatement

A tree where each edge is labeled with a single character. The root represents the empty prefix; walking down spells a string. A `isEnd` flag marks "a word ends here." Insertion creates nodes along the path; lookup walks the path; prefix lookup walks and just checks "did we reach a node?" Autocomplete walks to the prefix node, then DFS-collects every `isEnd` descendant.

---

## 3. Why this matters in interviews

The **string-keyed tree** every backend engineer should know. Naive substring match is O(n*L) per query; trie is O(L) regardless of dictionary size. Tests Map-of-Map nesting, path-walking with create-or-traverse, end-of-word marking, and unlocks: URL routers (Express stores routes in radix tries), autocomplete services, IP longest-prefix matches, command-completion CLIs.

---

## 4. Mental model

```
   After insert('cat'), insert('cats'), insert('cup'), insert('cap'):

   root
   └── c
       ├── a
       │   ├── t  isEnd=true
       │   │   └── s  isEnd=true
       │   └── p  isEnd=true
       └── u
           └── p  isEnd=true

   search('cat'):  walk c → a → t. t.isEnd? true → true
   search('ca'):   walk c → a. a.isEnd? false → FALSE (prefix, not word)
   startsWith('ca'): walk c → a. node exists → true (no isEnd check)
   autocomplete('ca'): walk to a. DFS collecting isEnd paths:
                       't' (end), 'ts' (end), 'p' (end) → ['cat', 'cats', 'cap']
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `insert('cat')`, what does `search('ca')` return? Why?
> 2. Why is `for (const ch of word)` safer than `word[i]` iteration?
> 3. Why use `Map<char, Node>` instead of a fixed-size array `new Array(26)`?

---

## 6. Brute force — walked through

### Wrong attempt 1: Set + linear scan
```js
this.words = new Set();
startsWith(prefix) {
  for (const w of this.words) if (w.startsWith(prefix)) return true;
  return false;
}
```
O(N×L) per query. Fails at scale.

### Wrong attempt 2: sorted array + binary search
O(L log N) for `startsWith`. Better, still beaten by trie's O(L).

### Wrong attempt 3: forget `isEnd`
Can't distinguish "cat is a word" from "ca is on the way to cats." `search('ca')` returns true incorrectly.

---

## 7. The unlocking insight

> **Tree of `{children: Map<char, Node>, isEnd: boolean}`. Walking is O(L). `search` requires `isEnd`; `startsWith` doesn't — they share the same walk helper.**

Three properties:

1. **Map-of-Map nesting** — O(1) per character lookup.
2. **`isEnd` flag** — separates "word" from "prefix-only."
3. **Shared `_walk` helper** — `search` and `startsWith` differ only in the terminal check.

---

## 8. Solution (annotated)

```js
class TrieNode {
  constructor() {
    this.children = new Map();                                       // char → TrieNode
    this.isEnd = false;
  }
}

class Trie {
  constructor() {
    this.root = new TrieNode();
  }

  insert(word) {                                                      // step 1: idempotent
    let node = this.root;
    for (const ch of word) {                                          // step 2: for-of handles surrogates
      let next = node.children.get(ch);
      if (!next) {
        next = new TrieNode();
        node.children.set(ch, next);
      }
      node = next;
    }
    node.isEnd = true;                                                // step 3: mark terminator
  }

  search(word) {
    const node = this._walk(word);
    return !!node && node.isEnd;                                      // step 4: exact match needs isEnd
  }

  startsWith(prefix) {
    return !!this._walk(prefix);                                      // step 5: prefix needs only path
  }

  _walk(s) {                                                          // step 6: shared walker
    let node = this.root;
    for (const ch of s) {
      node = node.children.get(ch);
      if (!node) return null;
    }
    return node;
  }

  autocomplete(prefix, limit = Infinity) {                            // step 7: walk + DFS collect
    const start = this._walk(prefix);
    if (!start) return [];
    const out = [];
    const dfs = (node, path) => {
      if (out.length >= limit) return;
      if (node.isEnd) out.push(path);
      for (const [ch, child] of node.children) dfs(child, path + ch);
    };
    dfs(start, prefix);
    return out;
  }
}
```

**Try it yourself**

```js
const t = new Trie();
['cat', 'cats', 'cup', 'cap'].forEach(w => t.insert(w));

t.search('cat');           // true
t.search('ca');            // false
t.startsWith('ca');        // true
t.startsWith('cab');       // false
t.autocomplete('ca');      // ['cat', 'cats', 'cap']
t.autocomplete('c', 2);    // ['cat', 'cats']  (limit 2)
```

---

## 9. Step-by-step dry run

```
After inserts, tree:

   root
   └── c
       ├── a
       │   ├── t  (isEnd)
       │   │   └── s  (isEnd)
       │   └── p  (isEnd)
       └── u
           └── p  (isEnd)

search('cat'):
  walk c → a → t. node!=null, isEnd=true → TRUE.

search('ca'):
  walk c → a. node!=null, isEnd=false → FALSE.

startsWith('cab'):
  walk c → a. then look for 'b' in a.children → undefined → null → FALSE.

autocomplete('ca'):
  walk c → a → start
  dfs(start, 'ca'):
    isEnd? no
    children: {t, p}
    dfs(t, 'cat'):
      isEnd? yes → push 'cat'
      children: {s}
      dfs(s, 'cats'):
        isEnd? yes → push 'cats'
        no children
    dfs(p, 'cap'):
      isEnd? yes → push 'cap'
      no children
  return ['cat', 'cats', 'cap']
```

---

## 10. Common confusion + traps

1. **Forgetting `isEnd`** — `search('ca')` returns true when only `'cat'` was inserted.
2. **`word.length` + index loop on Unicode** — splits surrogate pairs. Use `for...of`.
3. **Fixed-size array `new Array(128)`** for non-ASCII alphabets — wasteful or breaks on Unicode.
4. **`Object.create(null)` instead of Map** — works but loses iteration order and Map API.
5. **Empty string semantics** — `insert('')` marks root as `isEnd`. State the choice.
6. **Case sensitivity** — case-fold at the boundary, not inside.
7. **Deletion edge cases** — flip `isEnd=false`, then walk back deleting childless non-end nodes.

---

## 11. Senior follow-ups & variants

### Variant 1 — Word-count multiset trie
Counter at each `isEnd` for frequency tracking; `count(word)`, `decrement(word)`.

### Variant 2 — Wildcard search
`?` (any char), `*` (any sequence). DFS with backtracking — <a href="https://leetcode.com/problems/design-add-and-search-words-data-structure/" target="_blank" rel="noopener noreferrer">LeetCode 211</a>.

### Variant 3 — Ranked autocomplete
Frequency stored at each node; DFS keeps a heap of top-K. Used by real autocomplete services.

### Variant 4 — Radix / PATRICIA trie
Compress single-child chains; edges hold strings, not single chars. Express/Fastify routers.

### Variant 5 — Persistent (immutable) trie
Each insert returns a new root sharing unchanged subtrees. Clojure/Immutable.js.

### Variant 6 — Suffix tree / suffix array
Substring queries (not just prefix). Aho-Corasick = trie + failure links for multi-pattern matching.

---

## 12. How to think aloud

> "Tree of `{children: Map<char, Node>, isEnd: boolean}`. Insert walks creating nodes; `search` walks and checks `isEnd`; `startsWith` walks and just checks if the node exists. Share a `_walk` helper. O(L) per op, independent of dictionary size. Autocomplete: walk to prefix node, DFS the subtree collecting paths where `isEnd=true`. Trap: forgetting `isEnd` conflates prefix with word — `search('ca')` would return true incorrectly. Trap: indexed loop on Unicode splits surrogate pairs — use `for...of`. Trap: fixed-size array per node wastes memory and breaks on Unicode. Family: URL routers (radix tries), IP prefix tables, autocomplete, suffix trees, Aho-Corasick."

---

## 13. 60-second revision

> - **Node** = `{children: Map<char, Node>, isEnd: boolean}`.
> - **`insert`**: walk, create missing nodes, mark last `isEnd=true`.
> - **`search`**: walk, require `isEnd`.
> - **`startsWith`**: walk, require node (no `isEnd` check).
> - **O(L) per op**; independent of dictionary size.
> - **`autocomplete(prefix)`**: walk to node, DFS collect `isEnd` paths.
> - **Use `for...of`** for Unicode safety.
> - **Family:** Express router (radix trie), IP prefix, suffix tree, Aho-Corasick.
> - **Trap:** missing `isEnd`; indexed loop on Unicode; fixed-size array.

---

**Related:** [json-parse-recursive-descent.md](./json-parse-recursive-descent.md) · [min-heap-priority-queue.md](./min-heap-priority-queue.md) · [`09-recursion/dfs-iterative-vs-recursive.md`](../09-recursion/dfs-iterative-vs-recursive.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
