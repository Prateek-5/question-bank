# Hashing Sliding Window — Extracted Questions

> **55 questions** sourced from the LeetLens DB (`processed.extracted_questions`, snapshot 2026-05-31).
> Vertical: **DSA** · Bucket: `Hashing_Sliding_Window` · Bucket study-order rank in vertical: **3**.
> See [`../../../leetlens-import/STUDY-GUIDE.md`](../../../leetlens-import/STUDY-GUIDE.md) for the cross-vertical sequence.

## Triage summary

- **Total LeetLens questions assigned to this bucket:** 55
- **Net-new (to author):** 45
- **Already incorporated:** 10 (1 match a card in THIS folder, 9 match a card in a sibling folder)
- **Companies (both groups):** Google (27), Meta (6)

---

## 1. Net-new questions to author (45)

_Difficulty mix: Easy: 14 · Medium: 24 · Hard: 7_

Recommended execution order: Easy → Hard, then by LLM quality score.

| Seq | Difficulty | Company | Question | Topics | LeetLens ID | Also fits |
|---:|---|---|---|---|---|---|
| 1 | Easy | Google | Fruit Into Baskets | Hash Map, Two Pointers | `055d39bd` | `Two_Pointers` |
| 2 | Easy | Google | Design a search engine for a large dataset | Hash Map, Two Pointers | `344ef7cc` | `Two_Pointers` |
| 3 | Easy | Google | Two Sum, Three Sum, Valid Parentheses | Hash Map, Two Pointers | `43a648bb` | `Two_Pointers` |
| 4 | Easy | Google | Design a search engine for a large dataset | Hash Map, Two Pointers | `48962032` | `Two_Pointers` |
| 5 | Easy | Google | Design a search engine for a large dataset | Hash Map, Two Pointers | `7ec87524` | `Two_Pointers` |
| 6 | Easy | Google | Unique Email Addresses | String, Hash Map | `88425ca0` | — |
| 7 | Easy | Google | Find longest substring with k distinct characters | Hash Map, Two Pointers | `ac33b85d` | `Two_Pointers` |
| 8 | Easy | Google | Time to Type a String | String, Hash Map | `b3ce6d14` | — |
| 9 | Easy | — | Design a map with insert, delete, and search operations (with duplicates) and range queries | Hash Table, Data Structure | `016a51e5` | — |
| 10 | Easy | — | Design a hash table with insert, delete, and search operations | Hash Table, Data Structure | `690d380f` | — |
| 11 | Easy | — | Design a map with insert, delete, and search operations (with duplicates) and range queries | Hash Table, Data Structure | `a7881740` | — |
| 12 | Easy | — | Design a hash table with insert, delete, and search operations (with collisions) and range queries | Hash Table, Data Structure | `ad3b9d83` | — |
| 13 | Easy | — | Design a map with insert, delete, and search operations | Hash Table, Data Structure | `e472ce93` | — |
| 14 | Easy | — | Design a hash table with insert, delete, and search operations (with collisions) | Hash Table, Data Structure | `e786cbad` | — |
| 15 | Medium | Google | Neetcode 150 | Hash Map, Two Pointers | `20dadda9` | `Two_Pointers` |
| 16 | Medium | Google | Design a system for handling large amounts of unsorted data with complex queries and ensuring data consistency, using techniques like transactional updates, and caching | Hash Map, Sorting | `2bdef5be` | `Sorting_Divide_and_Conquer` |
| 17 | Medium | Google | Design a system for handling large amounts of unsorted data with complex queries | Hash Map, Sorting | `40536c9b` | `Sorting_Divide_and_Conquer` |
| 18 | Medium | Google | Design a system for handling large amounts of unsorted data with complex queries and caching | Hash Map, Sorting | `57a397b9` | `Sorting_Divide_and_Conquer` |
| 19 | Medium | Google | Design a system for handling large amounts of unsorted data with complex queries and caching, and ensuring data consistency | Hash Map, Sorting | `58471661` | `Sorting_Divide_and_Conquer` |
| 20 | Medium | Google | Design a caching system for a web application | Cache Invalidation, Redis | `70c71ed6` | `Distributed_Systems_(out_of_DSA_scope)` |
| 21 | Medium | Google | Design a distributed cache for caching HTTP responses | Hash Map, Two Pointers | `71d08ff1` | `Two_Pointers` |
| 22 | Medium | Google | Design a caching layer for an e-commerce application | Cache Invalidation, Redis | `907849a3` | `Distributed_Systems_(out_of_DSA_scope)` |
| 23 | Medium | Google | Design a system for handling large amounts of unsorted data with complex queries and ensuring data consistency, and using techniques like transactional updates | Hash Map, Sorting | `a914523f` | `Sorting_Divide_and_Conquer` |
| 24 | Medium | Google | Design a system for handling large amounts of unsorted data | Hash Map, Sorting | `aafa9ae1` | `Sorting_Divide_and_Conquer` |
| 25 | Medium | Google | Design a cache system with multiple levels of caching | Cache, Hash Map | `b47ce573` | — |
| 26 | Medium | Google | Design a caching layer for an e-commerce application | Cache Invalidation, Redis | `b80df5f6` | `Distributed_Systems_(out_of_DSA_scope)` |
| 27 | Medium | Google | Design a caching layer for an e-commerce application | Cache Invalidation, Redis | `c8be7aad` | `Distributed_Systems_(out_of_DSA_scope)` |
| 28 | Medium | Google | Design a binary search tree with insert and delete operations | Hash Map, Two Pointers | `eb6323ff` | `Two_Pointers` |
| 29 | Medium | Meta | Design a caching system with a cache invalidation strategy | Hash Table, Cache | `2ddac532` | — |
| 30 | Medium | Meta | Design a caching system with a cache invalidation strategy and a time-to-live (TTL) policy | Hash Table, Cache | `51029401` | — |
| 31 | Medium | Meta | Design a caching system for a web application | Hash Table, Cache | `530c5797` | — |
| 32 | Medium | Meta | Design a caching layer for an e-commerce application | Hash Table, Cache | `9033fa15` | — |
| 33 | Medium | Meta | Design a caching layer with a cache expiration strategy and a time-based eviction policy | Hash Table, Cache | `ea7d7a2a` | — |
| 34 | Medium | Meta | Design a caching layer with a cache expiration strategy | Hash Table, Cache | `f89faf70` | — |
| 35 | Medium | — | Maximum Product Subarray | Hash Map, Two Pointers | `3f97a909` | `Two_Pointers` |
| 36 | Medium | — | Maximum Sum Circular Subarray | Hash Map, Two Pointers | `40f5fea7` | `Two_Pointers` |
| 37 | Medium | — | Design a caching system for a web application | Cache Invalidation, Redis | `8aad3c8f` | `Distributed_Systems_(out_of_DSA_scope)` |
| 38 | Medium | — | Design LRU Cache | Hash Table, LRU Cache | `d935564a` | — |
| 39 | Hard | — | Design a Least Frequently Occurring (LFO) Key | Hash Map, Two Pointers | `0c1abca8` | `Two_Pointers` |
| 40 | Hard | — | Design a Least Recently Used (LRU) Cache | Cache, Hash Map | `169d6447` | — |
| 41 | Hard | — | Design a Least Frequently Occurring (LFO) Key with Support for Push and Pop Operations, and a Queue | Hash Map, Queue, Two Pointers | `57d0f2dd` | `Queues_Deque_Monotonic_Queue` · `Two_Pointers` |
| 42 | Hard | — | Design a Least Frequently Occurring (LFO) Key with Support for Push and Pop Operations | Hash Map, Two Pointers | `9436913e` | `Two_Pointers` |
| 43 | Hard | — | Design a Least Recently Used (LRU) Cache with Support for Push and Pop Operations, and a Trie | Cache, Hash Map, Trie | `9551b1e0` | `Trie_Bit_Manipulation_Trie` |
| 44 | Hard | — | Design a Least Frequently Occurring (LFO) Key with Support for Push and Pop Operations, and a Trie | Hash Map, Trie, Two Pointers | `a4263dc9` | `Trie_Bit_Manipulation_Trie` · `Two_Pointers` |
| 45 | Hard | — | Design a Least Recently Used (LRU) Cache with Support for Push and Pop Operations | Cache, Hash Map | `ba0464f9` | — |

## 2. Already incorporated by existing reference cards (10)

_Difficulty mix: Easy: 8 · Medium: 2_

Each row is folded into the matched reference card's **Interview Signals** section. `cross-folder` rows mean the concept is covered, but the canonical reference card lives in a different topic folder.

| Seq | Difficulty | Company | Question | Matched card | Scope | Score (method) | LeetLens ID |
|---:|---|---|---|---|---|---|---|
| 1 | Medium | Google | Subarray Sum Equals K | [Subarray_Sum_Equals_K.md](./Subarray_Sum_Equals_K.md) | local | 1.00 (exact-title) | `1c2d3772` |
| 2 | Medium | — | Edit Distance (Manhattan Distance) | [Dynamic_Programming_DP/Edit_Distance.md](../Dynamic_Programming_DP/Edit_Distance.md) | cross-folder | 1.00 (exact-title) | `f1f60fe7` |
| 3 | Easy | — | Longest Common Subsequence (LCS) | [Dynamic_Programming_DP/Longest_Common_Subsequence.md](../Dynamic_Programming_DP/Longest_Common_Subsequence.md) | cross-folder | 1.00 (exact-title) | `8fd212c7` |
| 4 | Easy | — | Longest Increasing Subsequence (LIS) | [Dynamic_Programming_DP/Longest_Increasing_Subsequence.md](../Dynamic_Programming_DP/Longest_Increasing_Subsequence.md) | cross-folder | 1.00 (exact-title) | `51c1cc90` |
| 5 | Easy | — | Two Sum II - Input Array Is Sorted | [Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md](../Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md) | cross-folder | 0.95 (card-contains-title) | `016ea76a` |
| 6 | Easy | Google | Two Sum II - Input Array Is Sorted | [Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md](../Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md) | cross-folder | 0.95 (card-contains-title) | `14770997` |
| 7 | Easy | — | Two Sum II - Input Array Is Sorted | [Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md](../Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md) | cross-folder | 0.95 (card-contains-title) | `3038cf99` |
| 8 | Easy | Google | Two Sum II - Input Array Is Sorted | [Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md](../Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md) | cross-folder | 0.95 (card-contains-title) | `5301618f` |
| 9 | Easy | Google | Two Sum II - Input Array Is Sorted | [Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md](../Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md) | cross-folder | 0.95 (card-contains-title) | `7edf6c6c` |
| 10 | Easy | Google | Two Sum II - Input Array Is Sorted | [Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md](../Two_Pointers/Two_Sum_II_Input_Array_Is_Sorted.md) | cross-folder | 0.95 (card-contains-title) | `9361d0e9` |

---

## How to use this file

1. **Section 1 (net-new):** active authoring queue — candidates for future v2 walkthroughs (`learn/<Problem>.md`).
2. **Section 2 (incorporated):** verification log — concept already covered; the company-context signal is in the matched card's **Interview Signals** section.
3. **Match score interpretation:** `token-coverage` ≥ 0.70 means ≥70% of the existing filename's tokens appear in the question. `substring` is a direct hit. `jaccard`/`ratio` are fuzzy. Spot-check anything below 0.75.