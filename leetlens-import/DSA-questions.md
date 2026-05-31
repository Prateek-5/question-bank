# LeetLens — DSA Questions (Categorized)

> **302 questions** from `processed.extracted_questions` (snapshot 2026-05-31).
> Buckets are listed in **pedagogical study order** — go top-down for a structured path.
> Within each bucket, questions are sorted Easy → Medium → Hard.
> Companion file: [`STUDY-GUIDE.md`](./STUDY-GUIDE.md) for the cross-category sequence.

## Bucket index (in study order)

| # | Bucket | Count | Difficulty mix | Layer |
|---|---|---:|---|---|
| 1 | [`Arrays & Matrices`](#arrays_and_matrices) | 43 | Easy:33 · Medium:9 · Hard:1 | Foundation — start here |
| 3 | [`Hashing & Sliding Window`](#hashing_sliding_window) | 55 | Easy:22 · Medium:26 · Hard:7 | Foundation — high-frequency |
| 5 | [`Binary Search`](#searching_binary_search) | 42 | Easy:9 · Medium:25 · Hard:8 | Pattern — after sorted-array intuition |
| 6 | [`Stack & Monotonic Stack`](#stack) | 11 | Easy:5 · Medium:6 | Linear DS |
| 7 | [`Queues, Deque, Monotonic Queue`](#queues_deque_monotonic_queue) | 3 | Medium:3 | Linear DS |
| 8 | [`Linked List`](#linked_list) | 4 | Easy:3 · Medium:1 | Linear DS |
| 9 | [`Trees & Binary Trees`](#trees_binary_trees) | 4 | Easy:1 · Medium:1 · Hard:2 | Hierarchical DS |
| 11 | [`Trie`](#trie_bit_manipulation_trie) | 5 | Hard:5 | Specialized DS |
| 12 | [`Heap / Priority Queue`](#heap_priority_queue) | 8 | Medium:8 | Specialized DS |
| 18 | [`Graph (BFS/DFS/Dijkstra/DSU)`](#graph_bfs_dfs_dijkstra_dsu) | 42 | Easy:1 · Medium:29 · Hard:12 | Advanced |
| 22 | [`JS Coding (overflow)`](#js_coding_(out_of_dsa_scope)) | 56 | Easy:1 · Medium:26 · Hard:29 | Not really DSA — belongs in JS vertical |
| 23 | [`Distributed Systems (overflow)`](#distributed_systems_(out_of_dsa_scope)) | 24 | Hard:24 | Not really DSA — belongs in HLD |
| 24 | [`Uncategorized`](#uncategorized) | 5 | Easy:4 · Hard:1 | Needs manual review |
| **Total** | | **302** | | |

---

## <a id="arrays_and_matrices"></a>1. Arrays & Matrices — 43 questions

_Layer: **Foundation — start here**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Easy | Google | Arrays, Binary Search | Find the middle index in array ⚠️ also fits: `Searching_Binary_Search` |
| 2 | Easy | Google | Arrays, Hash Map | Insert Interval (2nd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 3 | Easy | Google | Array, Two Pointers | Odd Even Jump ⚠️ also fits: `Two_Pointers` |
| 4 | Easy | Google | Arrays, Hash Map | Product of array except self (2nd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 5 | Easy | Google | Arrays, Hash Map | Basic Merge: Merge Intervals (2nd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 6 | Easy | Google | Arrays, Hash Map | Basic Merge: Merge Intervals (4th) ⚠️ also fits: `Hashing_Sliding_Window` |
| 7 | Easy | Google | Array, Two Pointers | Max Distance ⚠️ also fits: `Two_Pointers` |
| 8 | Easy | Google | Matrix, Hash Map | Fill Matrix ⚠️ also fits: `Hashing_Sliding_Window` |
| 9 | Easy | Google | Arrays, Hash Map | Insert Interval ⚠️ also fits: `Hashing_Sliding_Window` |
| 10 | Easy | Google | Arrays, Hash Map, Two Pointers | Given an array of integers, find two numbers that add up to a target sum ⚠️ also fits: `Hashing_Sliding_Window` · `Two_Pointers` |
| 11 | Easy | Google | Arrays, Hash Map | Basic Merge: Merge Intervals (5th) ⚠️ also fits: `Hashing_Sliding_Window` |
| 12 | Easy | Google | Arrays, Queue | Design a queue using arrays and pointers ⚠️ also fits: `Queues_Deque_Monotonic_Queue` |
| 13 | Easy | Google | Arrays, Hash Map | Remove nth Node from end of list (2nd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 14 | Easy | Google | Arrays, Hash Map | Find the duplicate number ⚠️ also fits: `Hashing_Sliding_Window` |
| 15 | Easy | Google | Arrays, Hash Map, Two Pointers | Given an array of integers, find two numbers that add up to a target sum ⚠️ also fits: `Hashing_Sliding_Window` · `Two_Pointers` |
| 16 | Easy | Google | Array, Two Pointers | Decreasing Subsequences ⚠️ also fits: `Two_Pointers` |
| 17 | Easy | Google | Arrays, Binary Search | Find the middle index in array (2nd) ⚠️ also fits: `Searching_Binary_Search` |
| 18 | Easy | Google | Arrays, Hash Map | Product of array except self (3rd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 19 | Easy | Google | Arrays, Stack | Design a stack using arrays and pointers ⚠️ also fits: `Stack` |
| 20 | Easy | Google | Arrays, Hash Map | Find the duplicate number (2nd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 21 | Easy | Google | Arrays, Hash Map | Basic Merge: Merge Intervals ⚠️ also fits: `Hashing_Sliding_Window` |
| 22 | Easy | Google | Arrays, Hash Map | Non-overlapping Intervals ⚠️ also fits: `Hashing_Sliding_Window` |
| 23 | Easy | Google | Arrays, Hash Map, Two Pointers | Given an array of integers, find two numbers that add up to a target sum ⚠️ also fits: `Hashing_Sliding_Window` · `Two_Pointers` |
| 24 | Easy | Google | Arrays, Hash Map | Basic Merge: Merge Intervals (3rd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 25 | Easy | Meta | Arrays, Hash Map, Two Pointers | Given an array of integers, find two numbers that add up to a target sum ⚠️ also fits: `Hashing_Sliding_Window` · `Two_Pointers` |
| 26 | Easy | Meta | Arrays, Hash Map, Two Pointers | Given an array of integers, find two numbers that add up to a target sum ⚠️ also fits: `Hashing_Sliding_Window` · `Two_Pointers` |
| 27 | Easy | — | Arrays, Hash Map, Two Pointers | Given an array of integers, find two numbers that add up to a target sum ⚠️ also fits: `Hashing_Sliding_Window` · `Two_Pointers` |
| 28 | Easy | — | Array, Stack | Design a stack using array and pointer ⚠️ also fits: `Stack` |
| 29 | Easy | — | Array, Stack | Design a stack using array and pointer with push, pop, and peek operations ⚠️ also fits: `Stack` |
| 30 | Easy | — | Arrays, Hash Map, Two Pointers | Given an array of integers, find two numbers that add up to a target sum ⚠️ also fits: `Hashing_Sliding_Window` · `Two_Pointers` |
| 31 | Easy | — | Arrays, Hash Map, Two Pointers | Given an array of integers, find two numbers that add up to a target sum ⚠️ also fits: `Hashing_Sliding_Window` · `Two_Pointers` |
| 32 | Easy | — | Array, Stack | Design a stack using arrays ⚠️ also fits: `Stack` |
| 33 | Easy | — | Arrays, Two Pointers | Two Pointers ⚠️ also fits: `Two_Pointers` |
| 34 | Medium | Google | Arrays, Hash Map | Palindrome Linked List (2nd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 35 | Medium | Google | Arrays, Hash Map | My Calendar ii (2nd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 36 | Medium | Google | Arrays, Hash Map | Product of array except self ⚠️ also fits: `Hashing_Sliding_Window` |
| 37 | Medium | Google | Array, Hash Map, Two Pointers | Stock prices are given for each day in an array. You can make any number of transactions, but at any time you can either buy or sell (no two buys or sells consecutively) ⚠️ also fits: `Hashing_Sliding_Window` · `Two_Pointers` |
| 38 | Medium | Google | Arrays, Hash Map | My Calendar ii ⚠️ also fits: `Hashing_Sliding_Window` |
| 39 | Medium | Google | Arrays, Hash Map | Find the longest subarray with distinct elements ⚠️ also fits: `Hashing_Sliding_Window` |
| 40 | Medium | Google | Arrays, Hash Map | Remove nth Node from end of list ⚠️ also fits: `Hashing_Sliding_Window` |
| 41 | Medium | Google | Arrays, Hash Map | Palindrome Linked List ⚠️ also fits: `Hashing_Sliding_Window` |
| 42 | Medium | — | Arrays, Hash Map | Design a Maximum Subarray Sum ⚠️ also fits: `Hashing_Sliding_Window` |
| 43 | Hard | Google | Arrays, Dynamic Programming | Maximum product subarray ⚠️ also fits: `Dynamic_Programming_DP` |

## <a id="hashing_sliding_window"></a>3. Hashing & Sliding Window — 55 questions

_Layer: **Foundation — high-frequency**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Easy | Google | Hash Map, Two Pointers | Fruit Into Baskets ⚠️ also fits: `Two_Pointers` |
| 2 | Easy | Google | Hash Map, Two Pointers | Two Sum II - Input Array Is Sorted ⚠️ also fits: `Two_Pointers` |
| 3 | Easy | Google | Hash Map, Two Pointers | Design a search engine for a large dataset ⚠️ also fits: `Two_Pointers` |
| 4 | Easy | Google | Hash Map, Two Pointers | Two Sum, Three Sum, Valid Parentheses ⚠️ also fits: `Two_Pointers` |
| 5 | Easy | Google | Hash Map, Two Pointers | Design a search engine for a large dataset ⚠️ also fits: `Two_Pointers` |
| 6 | Easy | Google | Hash Map, Two Pointers | Two Sum II - Input Array Is Sorted ⚠️ also fits: `Two_Pointers` |
| 7 | Easy | Google | Hash Map, Two Pointers | Design a search engine for a large dataset ⚠️ also fits: `Two_Pointers` |
| 8 | Easy | Google | Hash Map, Two Pointers | Two Sum II - Input Array Is Sorted ⚠️ also fits: `Two_Pointers` |
| 9 | Easy | Google | String, Hash Map | Unique Email Addresses |
| 10 | Easy | Google | Hash Map, Two Pointers | Two Sum II - Input Array Is Sorted ⚠️ also fits: `Two_Pointers` |
| 11 | Easy | Google | Hash Map, Two Pointers | Find longest substring with k distinct characters ⚠️ also fits: `Two_Pointers` |
| 12 | Easy | Google | String, Hash Map | Time to Type a String |
| 13 | Easy | — | Hash Table, Data Structure | Design a map with insert, delete, and search operations (with duplicates) and range queries |
| 14 | Easy | — | Hash Map, Two Pointers | Two Sum II - Input Array Is Sorted ⚠️ also fits: `Two_Pointers` |
| 15 | Easy | — | Hash Map, Two Pointers | Two Sum II - Input Array Is Sorted ⚠️ also fits: `Two_Pointers` |
| 16 | Easy | — | Hash Map, Two Pointers | Longest Increasing Subsequence (LIS) ⚠️ also fits: `Two_Pointers` |
| 17 | Easy | — | Hash Table, Data Structure | Design a hash table with insert, delete, and search operations |
| 18 | Easy | — | Hash Map, Two Pointers | Longest Common Subsequence (LCS) ⚠️ also fits: `Two_Pointers` |
| 19 | Easy | — | Hash Table, Data Structure | Design a map with insert, delete, and search operations (with duplicates) and range queries |
| 20 | Easy | — | Hash Table, Data Structure | Design a hash table with insert, delete, and search operations (with collisions) and range queries |
| 21 | Easy | — | Hash Table, Data Structure | Design a map with insert, delete, and search operations |
| 22 | Easy | — | Hash Table, Data Structure | Design a hash table with insert, delete, and search operations (with collisions) |
| 23 | Medium | Google | Hash Map, Two Pointers | Subarray Sum Equals K ⚠️ also fits: `Two_Pointers` |
| 24 | Medium | Google | Hash Map, Two Pointers | Neetcode 150 ⚠️ also fits: `Two_Pointers` |
| 25 | Medium | Google | Hash Map, Sorting | Design a system for handling large amounts of unsorted data with complex queries and ensuring data consistency, using techniques like transactional updates, and caching ⚠️ also fits: `Sorting_Divide_and_Conquer` |
| 26 | Medium | Google | Hash Map, Sorting | Design a system for handling large amounts of unsorted data with complex queries ⚠️ also fits: `Sorting_Divide_and_Conquer` |
| 27 | Medium | Google | Hash Map, Sorting | Design a system for handling large amounts of unsorted data with complex queries and caching ⚠️ also fits: `Sorting_Divide_and_Conquer` |
| 28 | Medium | Google | Hash Map, Sorting | Design a system for handling large amounts of unsorted data with complex queries and caching, and ensuring data consistency ⚠️ also fits: `Sorting_Divide_and_Conquer` |
| 29 | Medium | Google | Cache Invalidation, Redis | Design a caching system for a web application ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 30 | Medium | Google | Hash Map, Two Pointers | Design a distributed cache for caching HTTP responses ⚠️ also fits: `Two_Pointers` |
| 31 | Medium | Google | Cache Invalidation, Redis | Design a caching layer for an e-commerce application ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 32 | Medium | Google | Hash Map, Sorting | Design a system for handling large amounts of unsorted data with complex queries and ensuring data consistency, and using techniques like transactional updates ⚠️ also fits: `Sorting_Divide_and_Conquer` |
| 33 | Medium | Google | Hash Map, Sorting | Design a system for handling large amounts of unsorted data ⚠️ also fits: `Sorting_Divide_and_Conquer` |
| 34 | Medium | Google | Cache, Hash Map | Design a cache system with multiple levels of caching |
| 35 | Medium | Google | Cache Invalidation, Redis | Design a caching layer for an e-commerce application ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 36 | Medium | Google | Cache Invalidation, Redis | Design a caching layer for an e-commerce application ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 37 | Medium | Google | Hash Map, Two Pointers | Design a binary search tree with insert and delete operations ⚠️ also fits: `Two_Pointers` |
| 38 | Medium | Meta | Hash Table, Cache | Design a caching system with a cache invalidation strategy |
| 39 | Medium | Meta | Hash Table, Cache | Design a caching system with a cache invalidation strategy and a time-to-live (TTL) policy |
| 40 | Medium | Meta | Hash Table, Cache | Design a caching system for a web application |
| 41 | Medium | Meta | Hash Table, Cache | Design a caching layer for an e-commerce application |
| 42 | Medium | Meta | Hash Table, Cache | Design a caching layer with a cache expiration strategy and a time-based eviction policy |
| 43 | Medium | Meta | Hash Table, Cache | Design a caching layer with a cache expiration strategy |
| 44 | Medium | — | Hash Map, Two Pointers | Maximum Product Subarray ⚠️ also fits: `Two_Pointers` |
| 45 | Medium | — | Hash Map, Two Pointers | Maximum Sum Circular Subarray ⚠️ also fits: `Two_Pointers` |
| 46 | Medium | — | Cache Invalidation, Redis | Design a caching system for a web application ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 47 | Medium | — | Hash Table, LRU Cache | Design LRU Cache |
| 48 | Medium | — | Hash Map, Two Pointers | Edit Distance (Manhattan Distance) ⚠️ also fits: `Two_Pointers` |
| 49 | Hard | — | Hash Map, Two Pointers | Design a Least Frequently Occurring (LFO) Key ⚠️ also fits: `Two_Pointers` |
| 50 | Hard | — | Cache, Hash Map | Design a Least Recently Used (LRU) Cache |
| 51 | Hard | — | Hash Map, Queue, Two Pointers | Design a Least Frequently Occurring (LFO) Key with Support for Push and Pop Operations, and a Queue ⚠️ also fits: `Queues_Deque_Monotonic_Queue` · `Two_Pointers` |
| 52 | Hard | — | Hash Map, Two Pointers | Design a Least Frequently Occurring (LFO) Key with Support for Push and Pop Operations ⚠️ also fits: `Two_Pointers` |
| 53 | Hard | — | Cache, Hash Map, Trie | Design a Least Recently Used (LRU) Cache with Support for Push and Pop Operations, and a Trie ⚠️ also fits: `Trie_Bit_Manipulation_Trie` |
| 54 | Hard | — | Hash Map, Trie, Two Pointers | Design a Least Frequently Occurring (LFO) Key with Support for Push and Pop Operations, and a Trie ⚠️ also fits: `Trie_Bit_Manipulation_Trie` · `Two_Pointers` |
| 55 | Hard | — | Cache, Hash Map | Design a Least Recently Used (LRU) Cache with Support for Push and Pop Operations |

## <a id="searching_binary_search"></a>5. Binary Search — 42 questions

_Layer: **Pattern — after sorted-array intuition**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Easy | Google | Binary Search, Tree | Design a binary search tree ⚠️ also fits: `Trees_Binary_Trees` |
| 2 | Easy | Meta | Binary Search, Hash Map | Design a binary tree FAANG Questions ⚠️ also fits: `Hashing_Sliding_Window` |
| 3 | Easy | Meta | Binary Search, Trees | Validate Binary Search Tree ⚠️ also fits: `Trees_Binary_Trees` |
| 4 | Easy | Meta | Binary Search, Trees | Symmetric Tree ⚠️ also fits: `Trees_Binary_Trees` |
| 5 | Easy | Meta | Binary Search, Trees | Design a binary search tree with O(log n) time complexity for insert, delete, and search operations ⚠️ also fits: `Trees_Binary_Trees` |
| 6 | Easy | Meta | Binary Search, Hash Map | Validate Binary Search Tree ⚠️ also fits: `Hashing_Sliding_Window` |
| 7 | Easy | Meta | Binary Search, Hash Map | Design a binary search tree ⚠️ also fits: `Hashing_Sliding_Window` |
| 8 | Easy | Meta | Binary Search, Trees | Invert Binary Tree ⚠️ also fits: `Trees_Binary_Trees` |
| 9 | Easy | — | Binary Search, Tree Data Structure | Design a binary search tree ⚠️ also fits: `Trees_Binary_Trees` |
| 10 | Medium | Google | Binary Search, Tree | Design a binary search tree with insert and delete operations ⚠️ also fits: `Trees_Binary_Trees` |
| 11 | Medium | Google | Binary Search, Tree | Design a binary search tree with insert and delete operations (2-3 levels of nesting) (2-3 levels of nesting) ⚠️ also fits: `Trees_Binary_Trees` |
| 12 | Medium | Google | Binary Search, Tree | Design a binary search tree with insert and delete operations (2-3 levels of nesting) (2-3 levels of nesting) ⚠️ also fits: `Trees_Binary_Trees` |
| 13 | Medium | Google | Binary Search, Tree | Design a binary search tree with insert and delete operations (2-3 levels of nesting) ⚠️ also fits: `Trees_Binary_Trees` |
| 14 | Medium | Google | Binary Search, Tree | Design a binary search tree with insert and delete operations (2-3 levels of nesting) (2-3 levels of nesting) ⚠️ also fits: `Trees_Binary_Trees` |
| 15 | Medium | Meta | Binary Search, Hash Map | Maximum Depth of Binary Tree ⚠️ also fits: `Hashing_Sliding_Window` |
| 16 | Medium | Meta | Binary Search, Trees | Maximum Depth of Binary Tree ⚠️ also fits: `Trees_Binary_Trees` |
| 17 | Medium | Meta | Binary Search, Hash Map | Invert Binary Tree ⚠️ also fits: `Hashing_Sliding_Window` |
| 18 | Medium | Meta | Binary Search, Hash Map | Binary Tree Right Side View ⚠️ also fits: `Hashing_Sliding_Window` |
| 19 | Medium | Meta | Binary Search, Trees | Cousins in Binary Tree ⚠️ also fits: `Trees_Binary_Trees` |
| 20 | Medium | Meta | Binary Search, Hash Map | Cousins in Binary Tree ⚠️ also fits: `Hashing_Sliding_Window` |
| 21 | Medium | Meta | Binary Search, Hash Map | Lowest Common Ancestor of a Binary Tree ⚠️ also fits: `Hashing_Sliding_Window` |
| 22 | Medium | Meta | Binary Search, Hash Map | Diameter of Binary Tree ⚠️ also fits: `Hashing_Sliding_Window` |
| 23 | Medium | Meta | Binary Search, Trees | Design a binary tree zigzag level order traversal ⚠️ also fits: `Trees_Binary_Trees` |
| 24 | Medium | Meta | Binary Search, Hash Map | Average of Levels in Binary Tree ⚠️ also fits: `Hashing_Sliding_Window` |
| 25 | Medium | Meta | Binary Search, Trees | Diameter of Binary Tree ⚠️ also fits: `Trees_Binary_Trees` |
| 26 | Medium | Meta | Binary Search, Hash Map | Populating Next Right Pointers in Each Node ⚠️ also fits: `Hashing_Sliding_Window` |
| 27 | Medium | Meta | Binary Search, Hash Map | Symmetric Tree ⚠️ also fits: `Hashing_Sliding_Window` |
| 28 | Medium | Meta | Binary Search, Hash Map | Level Order Successor of a Node ⚠️ also fits: `Hashing_Sliding_Window` |
| 29 | Medium | Meta | Binary Search, Trees | Design a binary tree level order traversal II ⚠️ also fits: `Trees_Binary_Trees` |
| 30 | Medium | Meta | Binary Search, Trees | Flatten Binary Tree to Linked List ⚠️ also fits: `Trees_Binary_Trees` |
| 31 | Medium | Meta | Binary Search, Trees | Populating next right pointers in each node ⚠️ also fits: `Trees_Binary_Trees` |
| 32 | Medium | — | Binary Search, Tree Data Structure | Design a binary search tree with insert, delete, and search operations (with duplicates) and range queries ⚠️ also fits: `Trees_Binary_Trees` |
| 33 | Medium | — | Binary Search, Tree Data Structure | Design a binary search tree with insert, delete, and search operations (with duplicates) ⚠️ also fits: `Trees_Binary_Trees` |
| 34 | Medium | — | Binary Search, Tree Data Structure | Design a binary search tree with insert, delete, and search operations ⚠️ also fits: `Trees_Binary_Trees` |
| 35 | Hard | Google | Binary Search, Hash Map | Minimum Number of Arrows to Burst Balloons (5th) ⚠️ also fits: `Hashing_Sliding_Window` |
| 36 | Hard | Google | Binary Search, Hash Map | Minimum Number of Arrows to Burst Balloons (4th) ⚠️ also fits: `Hashing_Sliding_Window` |
| 37 | Hard | Google | Binary Search, Hash Map | Minimum Number of Arrows to Burst Balloons ⚠️ also fits: `Hashing_Sliding_Window` |
| 38 | Hard | Google | Binary Search, Hash Map | Minimum Number of Arrows to Burst Balloons (2nd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 39 | Hard | Google | Binary Search, Hash Map | Minimum Number of Arrows to Burst Balloons (3rd) ⚠️ also fits: `Hashing_Sliding_Window` |
| 40 | Hard | Meta | Binary Search, Hash Map | Convert Sorted Array to Binary Search Tree ⚠️ also fits: `Hashing_Sliding_Window` |
| 41 | Hard | Meta | Binary Search, Hash Map | Flatten Binary Tree to Linked List ⚠️ also fits: `Hashing_Sliding_Window` |
| 42 | Hard | Meta | Binary Search, Trees | Convert Sorted Array to Binary Search Tree ⚠️ also fits: `Trees_Binary_Trees` |

## <a id="stack"></a>6. Stack & Monotonic Stack — 11 questions

_Layer: **Linear DS**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Easy | Google | Stacks, Queue | Design a queue using two stacks (2-3 levels of nesting) with multiple operations ⚠️ also fits: `Queues_Deque_Monotonic_Queue` |
| 2 | Easy | Google | Stacks, Two Pointers | Design a stack for parsing parentheses ⚠️ also fits: `Two_Pointers` |
| 3 | Easy | Google | Stack, Push/Pop | Design a stack with push and pop operations |
| 4 | Easy | Google | Stacks, Queue | Design a queue using two stacks (2-3 levels of nesting) ⚠️ also fits: `Queues_Deque_Monotonic_Queue` |
| 5 | Easy | Google | Stacks, Queue | Design a queue using two stacks ⚠️ also fits: `Queues_Deque_Monotonic_Queue` |
| 6 | Medium | Google | Stacks, Two Pointers | Design a queue for maximum sum of two subarrays ⚠️ also fits: `Two_Pointers` |
| 7 | Medium | — | Stacks, Two Pointers | Design a Min Stack ⚠️ also fits: `Two_Pointers` |
| 8 | Medium | — | Stacks, Queue, Two Pointers | Design a Min Stack with Support for Push and Pop Operations, and a Queue ⚠️ also fits: `Queues_Deque_Monotonic_Queue` · `Two_Pointers` |
| 9 | Medium | — | Stacks, Trie, Two Pointers | Design a Min Stack with Support for Push and Pop Operations, and a Trie ⚠️ also fits: `Trie_Bit_Manipulation_Trie` · `Two_Pointers` |
| 10 | Medium | — | Stacks, Two Pointers | Design a Min Stack with Support for Push and Pop Operations ⚠️ also fits: `Two_Pointers` |
| 11 | Medium | — | Stacks, Trie, Two Pointers | Design a Min Stack with Support for Push and Pop Operations, and a Trie ⚠️ also fits: `Trie_Bit_Manipulation_Trie` · `Two_Pointers` |

## <a id="queues_deque_monotonic_queue"></a>7. Queues, Deque, Monotonic Queue — 3 questions

_Layer: **Linear DS**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | — | Queue, Two Pointers | Design a Min Queue ⚠️ also fits: `Two_Pointers` |
| 2 | Medium | — | Queue, Trie, Two Pointers | Design a Min Queue with Support for Push and Pop Operations, and a Trie ⚠️ also fits: `Trie_Bit_Manipulation_Trie` · `Two_Pointers` |
| 3 | Medium | — | Queue, Two Pointers | Design a Min Queue with Support for Push and Pop Operations ⚠️ also fits: `Two_Pointers` |

## <a id="linked_list"></a>8. Linked List — 4 questions

_Layer: **Linear DS**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Easy | — | Linked List, Queue | Design a queue using linked list and pointer with enqueue, dequeue, and peek operations ⚠️ also fits: `Queues_Deque_Monotonic_Queue` |
| 2 | Easy | — | Linked List, Queue | Design a queue using linked list ⚠️ also fits: `Queues_Deque_Monotonic_Queue` |
| 3 | Easy | — | Linked List, Queue | Design a queue using linked list and pointer ⚠️ also fits: `Queues_Deque_Monotonic_Queue` |
| 4 | Medium | Google | Linked List, Insertion/Deletion | Design a linked list with insertion and deletion at any position |

## <a id="trees_binary_trees"></a>9. Trees & Binary Trees — 4 questions

_Layer: **Hierarchical DS**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Easy | Google | Tree, Binary Search | Design a binary search tree ⚠️ also fits: `Searching_Binary_Search` |
| 2 | Medium | Google | Tree, Binary Search | Design a binary search tree with range query ⚠️ also fits: `Searching_Binary_Search` |
| 3 | Hard | Google | Tree, Depth-First Search | Maximum Level Sum of a Binary Tree |
| 4 | Hard | Google | Tree, Hash Map | Design a binary tree for range sum queries ⚠️ also fits: `Hashing_Sliding_Window` |

## <a id="trie_bit_manipulation_trie"></a>11. Trie — 5 questions

_Layer: **Specialized DS**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Hard | — | Trie, Hash Map | Design a Trie for the Maximum Subarray Sum with Support for Push and Pop Operations, and a Trie ⚠️ also fits: `Hashing_Sliding_Window` |
| 2 | Hard | — | Trie, Hash Map | Design a Trie for the Maximum Subarray Sum ⚠️ also fits: `Hashing_Sliding_Window` |
| 3 | Hard | — | Trie, Hash Map | Design a Trie for the Maximum Subarray Sum with Support for Push and Pop Operations, and a Trie ⚠️ also fits: `Hashing_Sliding_Window` |
| 4 | Hard | — | Trie, Hash Map | Design a Trie for the Maximum Subarray Sum with Support for Push and Pop Operations ⚠️ also fits: `Hashing_Sliding_Window` |
| 5 | Hard | — | Trie, Hash Map | Design a Trie for the Maximum Subarray Sum with Support for Push and Pop Operations, and a Queue ⚠️ also fits: `Hashing_Sliding_Window` |

## <a id="heap_priority_queue"></a>12. Heap / Priority Queue — 8 questions

_Layer: **Specialized DS**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Medium | — | Binary Heap, Priority Queue | Design a priority queue using binary heap |
| 2 | Medium | — | Binary Heap, Priority Queue | Design a priority queue using binary heap and sorting (with duplicates) and range queries |
| 3 | Medium | — | Heap, Two Pointers | Design a Min Heap with Support for Push and Pop Operations ⚠️ also fits: `Two_Pointers` |
| 4 | Medium | — | Heap, Trie, Two Pointers | Design a Min Heap with Support for Push and Pop Operations, and a Trie ⚠️ also fits: `Trie_Bit_Manipulation_Trie` · `Two_Pointers` |
| 5 | Medium | — | Heap, Two Pointers | Design a Min Heap ⚠️ also fits: `Two_Pointers` |
| 6 | Medium | — | Binary Heap, Priority Queue | Design a priority queue using binary heap and sorting (with duplicates) |
| 7 | Medium | — | Heap, Trie, Two Pointers | Design a Min Heap with Support for Push and Pop Operations, and a Trie ⚠️ also fits: `Trie_Bit_Manipulation_Trie` · `Two_Pointers` |
| 8 | Medium | — | Heap, Queue, Two Pointers | Design a Min Heap with Support for Push and Pop Operations, and a Queue ⚠️ also fits: `Queues_Deque_Monotonic_Queue` · `Two_Pointers` |

## <a id="graph_bfs_dfs_dijkstra_dsu"></a>18. Graph (BFS/DFS/Dijkstra/DSU) — 42 questions

_Layer: **Advanced**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Easy | Google | Graph, Dijkstra | Min Number of Chairs |
| 2 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS, DFS, topological sorting, strongly connected components, cycle detection, shortest path, Dijkstra's algorithm, Bellman-Ford algorithm, Floyd-Warshall al |
| 3 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS) |
| 4 | Medium | Google | Graph, Traversal | Design a graph traversal problem (DFS, BFS) |
| 5 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS, DFS, topological sorting, strongly connected components, cycle detection, shortest path, Dijkstra's algorithm, Bellman-Ford algorithm, Floyd-Warshall al |
| 6 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with DFS) |
| 7 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS, DFS, and topological sorting) |
| 8 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS and DFS) |
| 9 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix |
| 10 | Medium | Google | Graph, Traversal | Design a graph traversal problem (DFS, BFS) with multiple levels of nesting |
| 11 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS, DFS, topological sorting, strongly connected components, cycle detection, shortest path, Dijkstra's algorithm, and Bellman-Ford algorithm) |
| 12 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS, DFS, topological sorting, strongly connected components, cycle detection, shortest path, and Dijkstra's algorithm) |
| 13 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS, DFS, topological sorting, strongly connected components, and cycle detection) |
| 14 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS, DFS, topological sorting, strongly connected components, cycle detection, and shortest path) |
| 15 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS, DFS, topological sorting, and strongly connected components) |
| 16 | Medium | Google | Graph, Traversal | Design a graph traversal problem (DFS, BFS) with multiple levels of nesting and multiple operations |
| 17 | Medium | Google | Graph, Adjacency List | Design a graph using adjacency list and adjacency matrix (with BFS, DFS, topological sorting, strongly connected components, cycle detection, shortest path, Dijkstra's algorithm, Bellman-Ford algorithm, and Floyd-Warshal |
| 18 | Medium | — | Graph, Distributed Systems | Design a system to manage user data retrieval ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 19 | Medium | — | Graph, Distributed Systems | Design a system to manage user data ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 20 | Medium | — | Graph Data Structure, Node-Edge Relationship | Design a graph with nodes and edges (with weights) and range queries |
| 21 | Medium | — | Graph, Distributed Systems | Design a system to manage user data compression ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 22 | Medium | — | Graph Data Structure, Node-Edge Relationship | Design a graph with nodes and edges (with weights) |
| 23 | Medium | — | Graph, Distributed Systems | Design a system to manage user data anonymization auditing security ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 24 | Medium | — | Graph, Distributed Systems | Design a system to manage user data anonymization policies ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 25 | Medium | — | Graph, Distributed Systems | Design a system to manage user data deduplication ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 26 | Medium | — | Graph Data Structure, Node-Edge Relationship | Design a graph with nodes and edges |
| 27 | Medium | — | Graph, Distributed Systems | Design a system to manage user data anonymization auditing techniques ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 28 | Medium | — | Graph, Distributed Systems | Design a system to manage user data anonymization metrics ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 29 | Medium | — | Graph, Distributed Systems | Design a system to manage user data anonymization techniques ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 30 | Medium | — | Graph, Distributed Systems | Design a system to manage inventory levels in e-commerce ⚠️ also fits: `Distributed_Systems_(out_of_DSA_scope)` |
| 31 | Hard | Google | Graph, Disjoint Set Union | Design a system for finding the maximum flow in a flow network with multiple sources and sinks |
| 32 | Hard | Google | Graph, Weighted Edges | Design a graph with weighted edges and find the shortest path |
| 33 | Hard | Google | Graph, Disjoint Set Union | Design a system for finding the minimum cost flow in a flow network with negative weights and capacity constraints |
| 34 | Hard | Google | Graph, Disjoint Set Union | Design a system for finding the minimum cost flow in a flow network |
| 35 | Hard | Google | Graph, Disjoint Set Union | Design a graph for finding connected components |
| 36 | Hard | Google | Graph, Disjoint Set Union | Design a system for finding the minimum cost flow in a flow network with multiple sources and sinks and capacity constraints |
| 37 | Hard | Google | Graph, Disjoint Set Union | Design a system for finding the maximum flow in a flow network with multiple sources and sinks and capacity constraints and negative weights |
| 38 | Hard | Google | Graph, Disjoint Set Union | Design a system for finding the maximum flow in a flow network with negative weights |
| 39 | Hard | Google | Graph, Disjoint Set Union | Design a system for finding the minimum cost flow in a flow network with multiple sources and sinks and capacity constraints and negative weights and capacity constraints |
| 40 | Hard | Google | Graph, Dijkstra | Stores and Houses |
| 41 | Hard | Google | Graph, Disjoint Set Union | Design a system for finding the maximum flow in a flow network |
| 42 | Hard | Google | Graph, Disjoint Set Union | Design a system for finding the shortest path between two nodes in a graph |

## <a id="js_coding_(out_of_dsa_scope)"></a>22. JS Coding (overflow) — 56 questions

_Layer: **Not really DSA — belongs in JS vertical**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Easy | Microsoft | JavaScript, Type Coercion, Equality, Abstract Comparison | Explain the difference between == and === in JavaScript. What is the abstract equality comparison algorithm? What are the type coercion rules? Give examples of surprising coercion results like [] == false and null == und |
| 2 | Medium | Airbnb | JavaScript, Currying, Partial Application, Functional Programming | Implement a curry function that supports both curry(fn)(a)(b)(c) and curry(fn)(a, b)(c) calling patterns. How does currying differ from partial application? What are practical use cases for currying in JavaScript? |
| 3 | Medium | Airbnb | JavaScript, Intl API, Internationalization, Localization | Explain the JavaScript Intl API. How do you handle internationalization for number formatting, date formatting, relative time, pluralization rules, and collation/sorting across different locales? What are the performance |
| 4 | Medium | Airbnb | JavaScript, Memoization, Caching, LRU | Implement a memoize function that supports caching based on all arguments (using JSON serialization and WeakMap for object arguments). Add cache size limit (LRU eviction), TTL support, and cache invalidation. ⚠️ also fits: `Dynamic_Programming_DP` |
| 5 | Medium | Amazon | JavaScript, Event Emitter, Observer Pattern, Memory Management | Implement a JavaScript event emitter class with on, off, once, and emit methods. Support wildcard events, namespaced events (event.namespace), and maxListeners warning. How would you prevent memory leaks from forgotten l |
| 6 | Medium | Amazon | JavaScript, TDZ, Hoisting, let | What is the Temporal Dead Zone (TDZ) in JavaScript? How do let, const, and class declarations behave differently from var in terms of hoisting? Explain the difference between declaration, initialization, and assignment p |
| 7 | Medium | Amazon | JavaScript, Retry, Exponential Backoff, Error Handling | Implement a retry function with exponential backoff and jitter. Support configurable max retries, base delay, max delay, retryable error conditions, and abort signal cancellation. Handle both sync and async operations. |
| 8 | Medium | Amazon | JavaScript, bind, call, apply | Implement Function.prototype.bind from scratch. It should handle partial application, preserve prototype chain for constructor calls, and maintain the correct this binding. How does bind differ from call and apply? |
| 9 | Medium | Amazon | JavaScript, WeakMap, WeakSet, Garbage Collection | What are WeakMap and WeakSet in JavaScript? How do they differ from Map and Set in terms of garbage collection? Provide practical use cases such as private data storage, DOM metadata caching, and circular reference handl |
| 10 | Medium | Amazon | JavaScript, Prototypal Inheritance, Prototype Chain, ES6 Classes | Compare prototypal inheritance with class-based inheritance in JavaScript. How does the prototype chain work? What happens when you access a property that does not exist on an object? How do ES6 classes relate to prototy |
| 11 | Medium | Amazon | JavaScript, Promises, Error Handling, Async Patterns | Implement Promise.all, Promise.allSettled, Promise.race, and Promise.any from scratch. Explain the differences in error handling between them. What happens when an empty array is passed to each? |
| 12 | Medium | Google | JavaScript, Array Methods, Polyfills, Spec Compliance | Implement Array.prototype methods from scratch: map, filter, reduce, flat, flatMap, and find. How does the spec define these methods? What are the edge cases with sparse arrays, deleted elements, and the thisArg paramete |
| 13 | Medium | Google | JavaScript, Symbols, Well-known Symbols, Metaprogramming | Explain JavaScript Symbols in depth. What are well-known Symbols like Symbol.iterator, Symbol.toPrimitive, Symbol.hasInstance? How do Symbols enable metaprogramming? Why are they useful for defining non-enumerable proper |
| 14 | Medium | Google | JavaScript, Closures, Scope Chain, IIFE | Explain closures in JavaScript with a practical example. How does the closure scope chain work? What are common pitfalls with closures in loops, and how do you fix them using IIFE or let? |
| 15 | Medium | Google | JavaScript, Core Web Vitals, LCP, CLS | How do you measure and optimize Core Web Vitals (LCP, FID/INP, CLS) in a JavaScript application? Explain each metric, common causes of poor scores, and specific optimization techniques for each. |
| 16 | Medium | Google | JavaScript, Structured Clone, Serialization, postMessage | What is the Structured Clone Algorithm in JavaScript? How does it differ from JSON serialization? What types can it handle that JSON cannot? How is it used in postMessage, IndexedDB, and the new structuredClone() global  |
| 17 | Medium | Meta | JavaScript, Event Delegation, Event Bubbling, Event Capturing | Explain event delegation in JavaScript. How does event bubbling and capturing work? Implement a performant event delegation system for a dynamic list with 10,000 items. When should you use stopPropagation vs stopImmediat |
| 18 | Medium | Microsoft | JavaScript, this Keyword, Binding Rules, Arrow Functions | Explain all the rules governing the "this" keyword in JavaScript: default binding, implicit binding, explicit binding (call, apply, bind), new binding, and arrow function behavior. What is the priority order when multipl |
| 19 | Medium | Microsoft | JavaScript, CommonJS, ES Modules, Tree Shaking | Compare CommonJS (require/module.exports) with ES Modules (import/export). How does tree-shaking work with ESM but not CJS? What are the loading differences (sync vs async)? How do you handle interop between them? |
| 20 | Medium | Microsoft | JavaScript, Async/Await, Promises, Generator Transform | Explain how async/await works internally in JavaScript. How does the engine transform async functions? What happens when you await a non-Promise value? How do you handle errors in async functions compared to Promise chai |
| 21 | Medium | Microsoft | JavaScript, AbortController, AbortSignal, Fetch | Explain the AbortController and AbortSignal APIs. How do you use them to cancel fetch requests, event listeners, and custom async operations? Implement a timeout wrapper using AbortSignal.timeout(). |
| 22 | Medium | Microsoft | JavaScript, Decorators, TypeScript, Metaprogramming | What are JavaScript decorators (Stage 3 proposal)? How do they work for classes, methods, and fields? Compare with the legacy decorator pattern using higher-order functions. How does TypeScript implement decorators? |
| 23 | Medium | Netflix | JavaScript, Function Composition, Functional Programming, Pipe | Implement a function composition utility (compose and pipe) in JavaScript. Support both synchronous and asynchronous functions. How does this relate to functional programming principles like point-free style? |
| 24 | Medium | Stripe | JavaScript, IEEE 754, Floating Point, BigInt | Explain how JavaScript handles numbers. Why does 0.1 + 0.2 !== 0.3? What is IEEE 754 double-precision? How do you handle precise decimal arithmetic in JavaScript (for financial calculations)? |
| 25 | Medium | Uber | JavaScript, Middleware, Chain of Responsibility, Async | Implement a middleware pipeline system in JavaScript (like Express/Koa). Support sync and async middleware, next() function, error-handling middleware, and context passing. Demonstrate with practical examples. |
| 26 | Medium | Uber | JavaScript, Debounce, Throttle, Performance | Implement debounce and throttle functions from scratch. Explain the difference between them with real-world use cases. Add support for leading/trailing edge options, cancel, and flush functionality. |
| 27 | Medium | Uber | JavaScript, React, Custom Hooks, Async | Implement a custom React hook useAsync that handles loading, error, and data states for async operations. Support cancellation on unmount, retry mechanism, and dependent re-fetching when parameters change. |
| 28 | Hard | Airbnb | JavaScript, Deep Comparison, Recursion, Type Checking | Implement a deep comparison function (isEqual) that handles primitives, objects, arrays, Date, RegExp, NaN, +0/-0, Map, Set, and handles circular references. Compare your approach with lodash isEqual implementation. ⚠️ also fits: `Recursion` |
| 29 | Hard | Airbnb | JavaScript, Template Engine, String Parsing, RegExp | Implement a simple JavaScript template engine that supports variable interpolation, conditionals (if/else), loops (each/for), and expression evaluation. Parse a template string and produce the rendered output. |
| 30 | Hard | Airbnb | JavaScript, Drag and Drop, DOM Events, Touch Events | Implement a drag-and-drop system in vanilla JavaScript. Handle mouse events, touch events, drag preview, drop targets, reordering items in a list, and accessibility (keyboard-based dragging). |
| 31 | Hard | Amazon | JavaScript, Deep Clone, Recursion, Type Checking | Implement a deep clone function that handles all JavaScript types: primitives, objects, arrays, Date, RegExp, Map, Set, circular references, and functions. Compare with structured clone and JSON.parse/stringify limitatio ⚠️ also fits: `Recursion` |
| 32 | Hard | Google | JavaScript, Signals, Reactivity, SolidJS | Implement a JavaScript signal-based reactivity system (like SolidJS or Angular Signals). Support signal(), computed(), and effect() primitives. Explain how signals differ from observables and how they enable fine-grained |
| 33 | Hard | Google | JavaScript, Bundler, Dependency Graph, Module Resolution | Implement a basic JavaScript bundler that resolves imports, builds a dependency graph, handles circular dependencies, and outputs a single bundled file. How does Webpack module resolution work? |
| 34 | Hard | Google | JavaScript, SharedArrayBuffer, Atomics, Shared Memory | What are SharedArrayBuffer and Atomics in JavaScript? How do they enable shared memory between workers? Explain the memory model, atomic operations, and when you would use them vs message passing. |
| 35 | Hard | Google | JavaScript, Web Workers, Service Workers, Concurrency | Explain Web Workers and Service Workers in JavaScript. How do they differ from the main thread? Implement a practical example of offloading CPU-intensive work to a Web Worker. How does message passing work with structure |
| 36 | Hard | Google | JavaScript, V8 Engine, Garbage Collection, Memory Management | How does garbage collection work in JavaScript (V8 engine)? Explain generational GC, Scavenger (Young generation), Mark-Sweep-Compact (Old generation), and incremental/concurrent marking. How can you optimize code for GC |
| 37 | Hard | Google | JavaScript, TypeScript, Generics, Conditional Types | Explain TypeScript generics in depth. Implement a type-safe event emitter using generics. What are conditional types, mapped types, and template literal types? How do you use infer keyword for type extraction? |
| 38 | Hard | Google | JavaScript, Pub-Sub, WeakRef, FinalizationRegistry | Implement a publish-subscribe system in JavaScript with support for once-only subscriptions, wildcard topics, event history/replay for late subscribers, and automatic cleanup of dead subscriptions using WeakRef. |
| 39 | Hard | Google | JavaScript, Promises, Async, Microtasks | Implement a Promise class from scratch with support for then, catch, finally, and static methods (resolve, reject, all, allSettled, race, any). Handle chaining, error propagation, and the microtask queue scheduling. |
| 40 | Hard | Google | JavaScript, Virtual Scroll, DOM Performance, Intersection Observer | Implement a virtual scroll / infinite scroll component in vanilla JavaScript. Support dynamic item heights, smooth scrolling, buffer zones above and below the viewport, and efficient DOM recycling. |
| 41 | Hard | Google | JavaScript, Module Loading, Circular Dependencies, Live Bindings | Explain the JavaScript module loading and execution order. When you import a module, when does its code run? How are circular dependencies handled in CJS vs ESM? What is the difference between live bindings and value cop |
| 42 | Hard | Google | JavaScript, Dependency Injection, IoC Container, Design Patterns | Implement a JavaScript dependency injection container without decorators. Support constructor injection, factory functions, singleton and transient lifetimes, and lazy resolution. How does this compare to Angular DI or I |
| 43 | Hard | Meta | JavaScript, Virtual DOM, React, Reconciliation | Explain how Virtual DOM reconciliation works in React. What is the diffing algorithm? How does React determine when to re-render? Compare with Svelte compiler approach and direct DOM manipulation performance. |
| 44 | Hard | Meta | JavaScript, React, Hooks, useState | Explain React hooks internals: how do useState, useEffect, useCallback, and useMemo work under the hood? Why is hook call order important? How does the fiber linked list store hook state? What are the rules of hooks? |
| 45 | Hard | Meta | JavaScript, Reactivity, Proxy, Dependency Tracking | Implement a basic JavaScript reactivity system from scratch: reactive(), effect(), and computed(). When a reactive property is modified, all dependent effects should automatically re-run. Handle nested effects and cleanu |
| 46 | Hard | Meta | TypeScript, Template Literal Types, Type Inference, Generics | Implement a TypeScript type-safe router that infers path parameters from route patterns. For example, given "/users/:id/posts/:postId", it should infer the params type as { id: string, postId: string }. Use template lite |
| 47 | Hard | Meta | JavaScript, Event Loop, Microtasks, Macrotasks | Explain the JavaScript event loop in detail. How do the call stack, task queue (macrotasks), and microtask queue interact? What is the execution order of setTimeout, Promise.then, queueMicrotask, and requestAnimationFram |
| 48 | Hard | Meta | JavaScript, Redux, State Management, Middleware | Implement a simple state management library (like a minimal Redux) with createStore, dispatch, subscribe, getState, and middleware support. How does Redux middleware chain work? Implement thunk middleware from scratch. |
| 49 | Hard | Meta | JavaScript, Proxy, Reflect, Reactivity | Explain the Proxy and Reflect APIs in JavaScript. Implement a reactive system using Proxy that automatically tracks property access and triggers re-renders when data changes. How does Vue.js use Proxy for reactivity? |
| 50 | Hard | Meta | JavaScript, Testing, Framework Design, Assertions | Design and implement a JavaScript testing utility that includes: describe/it/test blocks, expect assertions with matchers (toBe, toEqual, toThrow), beforeEach/afterEach hooks, mock functions, and spy capability. |
| 51 | Hard | Netflix | JavaScript, Observable, RxJS, Reactive Programming | Implement a JavaScript observable (pub/sub) pattern from scratch. Support subscribe, unsubscribe, and next operations. Add operators like map, filter, and debounce. How does RxJS implement cold vs hot observables? |
| 52 | Hard | Netflix | JavaScript, CSR, SSR, SSG | Explain the different rendering strategies in modern web applications: CSR (Client-Side Rendering), SSR (Server-Side Rendering), SSG (Static Site Generation), ISR (Incremental Static Regeneration), and streaming SSR. Whe |
| 53 | Hard | Netflix | JavaScript, Generators, Iterators, Lazy Evaluation | Explain generator functions and iterators in JavaScript. Implement a lazy evaluation pipeline using generators. How can generators be used for async flow control? What is the relationship between generators and async/awa |
| 54 | Hard | Netflix | JavaScript, Memory Leaks, Garbage Collection, Chrome DevTools | What causes memory leaks in JavaScript applications? Identify common patterns: detached DOM nodes, forgotten timers, closures holding references, global variables, and event listeners. How do you diagnose and fix them us |
| 55 | Hard | Uber | JavaScript, Promises, Concurrency, Async | Implement a Promise pool / concurrent task executor that limits the number of concurrent promises. Given an array of async tasks and a concurrency limit N, execute at most N tasks concurrently and return all results in o |
| 56 | Hard | Uber | JavaScript, Task Queue, Concurrency, Priority Queue | Implement a JavaScript task queue that processes tasks with configurable concurrency, priority levels, task timeout, pause/resume capability, and progress reporting. Handle task cancellation and graceful queue draining. ⚠️ also fits: `Heap_Priority_Queue` |

## <a id="distributed_systems_(out_of_dsa_scope)"></a>23. Distributed Systems (overflow) — 24 questions

_Layer: **Not really DSA — belongs in HLD**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Hard | Meta | Online Gaming, Distributed Systems | Design a system to optimize the performance of a large-scale online gaming platform |
| 2 | Hard | Meta | Social Media, Distributed Systems | Design a system to manage and optimize the performance of a large-scale social media platform |
| 3 | Hard | Meta | Data Compression, Distributed Systems | Design a system to optimize the performance of a large-scale data compression platform |
| 4 | Hard | Meta | Data Anonymization, Distributed Systems | Design a system to manage and optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy |
| 5 | Hard | Meta | Data Anonymization, Distributed Systems | Design a system to manage and optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy, low latency, scalability, security, and compliance |
| 6 | Hard | Meta | Distributed Systems, Cache | Design a distributed cache system with multiple data centers and high availability requirements ⚠️ also fits: `Hashing_Sliding_Window` |
| 7 | Hard | Meta | Data Integration, Distributed Systems | Design a system to manage and optimize the performance of a large-scale data integration platform |
| 8 | Hard | Meta | Data Anonymization, Distributed Systems | Design a system to optimize the performance of a large-scale data anonymization platform for sensitive data |
| 9 | Hard | Meta | Data Encryption, Distributed Systems | Design a system to manage and optimize the performance of a large-scale data encryption platform |
| 10 | Hard | Meta | SQL Injection, Distributed Systems | Design a system to detect and prevent SQL injection attacks in a web application |
| 11 | Hard | Meta | Data Warehousing, Distributed Systems | Design a system to manage and optimize the performance of a large-scale data warehousing platform |
| 12 | Hard | Meta | IoT, Distributed Systems | Design a system to manage and optimize the performance of a large-scale IoT device network |
| 13 | Hard | Meta | Data Analytics, Distributed Systems | Design a system to manage and optimize the performance of a large-scale data analytics platform |
| 14 | Hard | Meta | Data Deduplication, Distributed Systems | Design a system to optimize the performance of a large-scale data deduplication platform |
| 15 | Hard | Meta | Data Anonymization, Distributed Systems | Design a system to manage and optimize the performance of a large-scale data anonymization platform |
| 16 | Hard | Meta | Data Anonymization, Distributed Systems | Design a system to optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy and low latency |
| 17 | Hard | Meta | Data Anonymization, Distributed Systems | Design a system to optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy, low latency, scalability, and security |
| 18 | Hard | Meta | Data Storage, Distributed Systems | Design a system to optimize the performance of a large-scale data storage platform |
| 19 | Hard | Meta | Data Anonymization, Distributed Systems | Design a system to optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy, low latency, scalability, security, compliance, and auditing |
| 20 | Hard | Meta | E-commerce, Distributed Systems | Design a system to optimize the performance of a large-scale e-commerce platform |
| 21 | Hard | Meta | Cloud Computing, Distributed Systems | Design a system to optimize the performance of a large-scale cloud-based data processing platform |
| 22 | Hard | Meta | Machine Learning, Distributed Systems | Design a system to optimize the performance of a large-scale machine learning model training platform |
| 23 | Hard | Meta | Data Anonymization, Distributed Systems | Design a system to manage and optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy, low latency, and scalability |
| 24 | Hard | Meta | Data Anonymization, Distributed Systems | Design a system to manage and optimize the performance of a large-scale data anonymization platform for sensitive data with high accuracy, low latency, scalability, security, compliance, auditing, and data governance |

## <a id="uncategorized"></a>24. Uncategorized — 5 questions

_Layer: **Needs manual review**_

| # | Difficulty | Company | Topics | Question (excerpt) |
|---|---|---|---|---|
| 1 | Easy | Google | Point, Distance | K Closest Points to Origin |
| 2 | Easy | Meta | String, Regular Expression | Given a list of strings, find the first string that contains a given substring |
| 3 | Easy | — | Fibonacci Sequence, Generator | Design a Fibonacci number sequence generator with memoization |
| 4 | Easy | — | Fibonacci Sequence, Generator | Design a Fibonacci number sequence generator |
| 5 | Hard | Google | Locking, Concurrent Programming | Design a system for handling concurrent updates to a shared data structure |
