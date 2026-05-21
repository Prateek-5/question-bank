# Trie / Bit-Manipulation Trie — Learning Path

> **Stage:** Trees & Graphs   |   **Prereqs:** [Trees_Binary_Trees/](../Trees_Binary_Trees/LEARNING.md), [Bit_Manipulation/](../Bit_Manipulation/LEARNING.md)   |   **Problems:** 7
>
> Two distinct tries: **character trie** for prefix problems, **bit trie** for XOR maximization.

---

## How to study this topic

1. Build the trie (memorize the node + insert + search template).
2. Wildcards and design problems.
3. Prefix tasks (shortest unique prefix).
4. Bit trie (XOR family).
5. Hardest substring problems.

---

## Problems in study order

### Build the trie

1. **[Implement_Trie_Prefix_Tree.md](./Implement_Trie_Prefix_Tree.md)** — `insert`, `search`, `startsWith`. Memorize. **must-do**

### Wildcards / design

2. **[Design_Add_and_Search_Words_DS.md](./Design_Add_and_Search_Words_DS.md)** — Recursive search with `.` wildcard tries all children. **must-do**

### Prefix tasks

3. **[Shortest_Unique_prefix_for_every_word.md](./Shortest_Unique_prefix_for_every_word.md)** — Build trie with frequency counts; first single-occurrence node = shortest unique prefix.
4. **[Prefix_and_Suffix_Search.md](./Prefix_and_Suffix_Search.md)** — Insert each word's `suffix#word` variants into one trie. Powerful trick.

### Bit trie — XOR family

5. **[Maximum_XOR_of_Two_Numbers.md](./Maximum_XOR_of_Two_Numbers.md)** — Bit trie; greedily pick opposite-bit branch at each level. **must-do**
6. **[Subarrays_with_XOR_Less_Than_K_Concept.md](./Subarrays_with_XOR_Less_Than_K_Concept.md)** — Bit trie + counting; harder generalization.

### Hardest

7. **[Count_Substrings_That_Differ_by_One_Character.md](./Count_Substrings_That_Differ_by_One_Character.md)** — Trie + dynamic programming hybrid; advanced.

---

## Patterns established

- **Trie node structure:** Children map (26-array for lowercase or hash for general); `isEnd` flag.
- **Insert / search / startsWith templates:** Walk the trie, create nodes as needed (insert) or fail early (search).
- **Wildcard recursion:** On `.`, recurse into all children; on letter, recurse into matching child only.
- **Frequency counting on trie nodes:** Tracks how many words pass through this prefix; used for "shortest unique prefix" and similar.
- **Suffix-trick:** For prefix+suffix search, insert all `suffix#word` rotations into the trie; query is `suffix#prefix`.
- **Bit trie (32-level binary trie):** For max-XOR, at each bit greedily go opposite direction if that subtree is non-empty.

---

## Common traps

- **26-array vs map.** Array is fast but assumes lowercase a-z; map is general but slower.
- **Forgetting `isEnd`** when search hits the trie path but no word ends here.
- **Bit trie order:** Insert from most-significant bit to least; greedy match same direction.
- **Memory blowup:** Trie can be huge (one node per char per word). For 10K words averaging 100 chars, that's 1M nodes.

---

## After this topic

- **[Segment_Tree_Range_Queries/](../Segment_Tree_Range_Queries/LEARNING.md)** — another tree variant for ranges.
- **[Bit_Manipulation/](../Bit_Manipulation/LEARNING.md)** — companion if you skipped it.
