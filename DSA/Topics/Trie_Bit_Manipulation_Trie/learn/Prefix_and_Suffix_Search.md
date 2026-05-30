# Prefix and Suffix Search — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Prefix_and_Suffix_Search.md`](../Prefix_and_Suffix_Search.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/prefix-and-suffix-search/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/prefix-and-suffix-search/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The clever "suffix#word" trick.** The lesson: **fuse two constraints (prefix + suffix) into one trie key by storing every `suffix#word` variant. Query becomes `suffix#prefix`.** A senior-bar problem. **Read [`Implement_Trie_Prefix_Tree.md`](./Implement_Trie_Prefix_Tree.md) and [`Shortest_Unique_prefix_for_every_word.md`](./Shortest_Unique_prefix_for_every_word.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. Two separate tries (and why it's slow)
3. The "suffix#word" trick
4. Why the delimiter `#` matters
5. Code
6. Trace it
7. Common pitfalls
8. Complexity tradeoffs
9. The shape — key augmentation for multiple constraints

---

## 1. Read the problem

Design class `WordFilter`:
- Constructor takes `words` array.
- `f(prefix, suffix)` returns the LARGEST INDEX of a word in `words` that has both this PREFIX and this SUFFIX. Return `-1` if none.

**Example:** `words = ["apple"]`.

- `f("a", "e")` → 0 (apple starts with "a" and ends with "e").
- `f("b", "")` → -1.

For ties, return the LARGEST index — "most recent insertion wins."

---

## 2. Two separate tries (and why it's slow)

Naive: build a TRIE for prefixes and a TRIE OF REVERSED WORDS for suffixes. For each query:
1. Find indices matching prefix → set A.
2. Find indices matching suffix → set B.
3. Return max(A ∩ B).

For n words and q queries, worst-case O(n × q) per query if both sets are large. Slow for large inputs.

**We want SINGLE-TRIE single-walk lookup.**

---

## 3. The "suffix#word" trick

> **Mini-refresher: encode both constraints in one key.**
>
> For each word `w`, generate ALL "suffix + # + word" combinations:
> ```
> w = "apple"
> Keys: "#apple", "e#apple", "le#apple", "ple#apple", "pple#apple", "apple#apple"
> ```
> That's `|w| + 1` keys per word, one for each possible suffix (including the empty suffix).
>
> A query `f(prefix, suffix)` is converted to the lookup key `suffix + "#" + prefix`. A trie walk on this combined key answers both constraints AT ONCE.

Why? The generated key `"le#apple"` has structure `[suffix part] # [word]`. The query string `"le#ap"` matches as a PREFIX of `"le#apple"`:
- `"le"` matches the suffix portion.
- `"#"` matches the delimiter.
- `"ap"` matches the start of the word.

So if the trie has key `"le#apple"`, then `"le#ap"` walks the trie successfully — meaning some word ends with "le" AND starts with "ap" (namely "apple").

---

## 4. Why the delimiter `#` matters

Without `#`, key `"leapple"` and query `"leap"` would match — but query intended "le" suffix + "ap" prefix is now ambiguous. The `#` is a GUARD CHARACTER ensuring the suffix portion ends cleanly.

Any character not in the alphabet works (`#`, `$`, `~`, etc.). The 27th index in our children array.

---

## 5. Code

**C++:**

```cpp
class WordFilter {
    struct Node {
        Node* ch[27] = {};    // 26 letters + 1 for '#'
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
            cur->idx = max(cur->idx, wordIdx);    // largest index wins
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

**Python:**

```python
class WordFilter:
    def __init__(self, words):
        self.root = {}
        for i, w in enumerate(words):
            for k in range(len(w) + 1):
                key = w[k:] + "#" + w
                cur = self.root
                for c in key:
                    if c not in cur:
                        cur[c] = {}
                    cur = cur[c]
                    cur['_idx'] = i      # overwrites with latest = largest index
    
    def f(self, prefix, suffix):
        q = suffix + "#" + prefix
        cur = self.root
        for c in q:
            if c not in cur: return -1
            cur = cur[c]
        return cur.get('_idx', -1)
```

Complexity:
- **Construction**: O(N × L²) (each word has L+1 suffixes × L chars).
- **Query**: O(|prefix| + |suffix|).

---

## 6. Trace it

`words = ["apple", "ape"]`.

Insert "apple" (index 0) with keys: "apple#apple", "pple#apple", "ple#apple", "le#apple", "e#apple", "#apple".

Insert "ape" (index 1) with keys: "ape#ape", "pe#ape", "e#ape", "#ape".

At nodes shared by both, max_idx = 1 (ape wins as later index).

**Query `f("a", "e")`**: query string = "e#a".

Walk:
- 'e' → root.children['e'] exists. max_idx at this node = max(0, 1) = 1.
- '#' → exists.
- 'a' → exists. max_idx here = 1.

Return **1**. ✓

**Query `f("ap", "le")`**: query string = "le#ap".

Walk:
- 'l' → root.children['l'] (from "le#apple") = exists. idx = 0.
- 'e' → exists. idx = 0.
- '#' → exists. idx = 0.
- 'a' → exists. idx = 0.
- 'p' → exists. idx = 0.

Return **0**. ✓ Only "apple" matches.

**Query `f("b", "")`**: query string = "#b".

Walk:
- '#' → exists.
- 'b' → not in root's '#' child (no word starts with 'b'). Return **-1**. ✓

---

## 7. Common pitfalls

1. **Putting prefix BEFORE suffix in the key.** Doesn't work — word lengths vary, so the suffix portion couldn't be matched by a query whose prefix is shorter than the word.

2. **Forgetting the `#` delimiter.** Word characters bleed into suffix characters → false positives.

3. **Storing the FIRST index instead of MAX.** Problem asks for LARGEST index.

4. **Inserting only the word + '#' + word.** Misses partial suffix queries.

5. **Inserting all w[k:] without '#'**. Same issue as no delimiter.

6. **Memory blowup.** For long words, L² per word can be large. Watch out.

---

## 8. Complexity tradeoffs

**Construction:** O(N × L²) time and space.

For N = 15000, L = 10: 1.5 × 10⁶ trie node entries. OK.

For L = 20: 6 × 10⁶ — getting big.

For L > 30: alternative approaches like Aho-Corasick or suffix automata may be needed.

**Query:** O(|prefix| + |suffix|). Very fast.

---

## 9. The shape — key augmentation for multiple constraints

The pattern:

> **"To handle MULTIPLE INDEPENDENT CONSTRAINTS with a single data structure lookup, COMBINE THEM INTO ONE KEY using a delimiter."**

| Problem | Combined key |
|---|---|
| **This problem** | suffix + '#' + word |
| Find Longest Common Substring (with constraints) | concatenate + special separator |
| Suffix Trees / Suffix Arrays | implicit "end of string" markers |
| Aho-Corasick (multi-pattern) | shared prefix structure |

**Pattern to internalize:**

> "When you have multiple string constraints and need fast queries, ENCODE all constraints in a key prefix (using delimiters), then SINGLE-LOOKUP gives the answer."

---

## Cross-references

- **Reference card (post-mastery):** [`../Prefix_and_Suffix_Search.md`](../Prefix_and_Suffix_Search.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Implement_Trie_Prefix_Tree.md`](./Implement_Trie_Prefix_Tree.md), [`Design_Add_and_Search_Words_DS.md`](./Design_Add_and_Search_Words_DS.md), [`Shortest_Unique_prefix_for_every_word.md`](./Shortest_Unique_prefix_for_every_word.md).
  - Coming next: [`Subarrays_with_XOR_Less_Than_K_Concept.md`](./Subarrays_with_XOR_Less_Than_K_Concept.md), [`Count_Substrings_That_Differ_by_One_Character.md`](./Count_Substrings_That_Differ_by_One_Character.md).
