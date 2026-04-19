# DSA Preparation Repository

A topic-wise, interview-ready collection of DSA problems with detailed explanations and C++ implementations. Generated from a curated spreadsheet of 230 problems across 22 topics.

## What's Inside

For every problem you get:
- **Problem Link** to the original source
- **Core Concept** — the underlying idea in one line
- **Intuition** — how to think about the problem from scratch
- **Detailed Explanation** — step-by-step reasoning, no skipped logic
- **Dry Run** — worked example on sample input
- **Approach** — algorithm and key observations
- **Time and Space Complexity**
- **Clean C++ Implementation** with comments where non-obvious
- **Follow-up Questions** to stretch your understanding

Each topic also has a `Concepts.md` that summarizes the core theory, common patterns, when-to-use guidance, and template code snippets.

## Folder Structure

```
DSA/
├── CPP_Concepts.md            # STL + C++ primer for DSA
├── Cheat_Sheet.md             # Formulas, patterns, complexity targets
├── Quick_Revision_Guide.md    # Skimmable per-topic reminders
├── README.md                  # This file
└── Topics/
    ├── Heap_Priority_Queue/
    │   ├── Concepts.md
    │   ├── Minimum_Cost_to_Connect_Ropes.md
    │   ├── Find_K_Pairs_with_Smallest_Sums.md
    │   └── ...
    ├── Math/
    ├── Graph_BFS_DFS_Dijkstra_DSU/
    ├── Binary_Search_Tree_BST/
    ├── Trees_Binary_Trees/
    ├── Greedy/
    ├── 1_D_and_2_D_Arrays/
    ├── Segment_Tree_Range_Queries/
    ├── Arrays_and_Matrices/
    ├── Searching_Binary_Search/
    ├── Two_Pointers/
    ├── Linked_List/
    ├── Number_Theory_Misc/
    ├── Trie_Bit_Manipulation_Trie/
    ├── Dynamic_Programming_DP/
    ├── Bit_Manipulation/
    ├── Hashing_Sliding_Window/
    ├── Queues_Deque_Monotonic_Queue/
    ├── Stack/
    ├── Recursion/
    ├── Backtracking/
    └── Sorting_Divide_and_Conquer/
```

## How to Use

1. **Study a topic end-to-end.** Read `Concepts.md`, then work through problems inside that folder.
2. **Before a problem:** read only the *Problem Link* and think. Write a plan.
3. **When stuck:** open the question file and read sections in order — Core Concept → Intuition → Approach. Avoid jumping to the code.
4. **After solving:** compare your solution with the provided C++ implementation. Check complexity and edge cases.
5. **Before review sessions:** skim `Quick_Revision_Guide.md` and `Cheat_Sheet.md`.

## Topics Covered

1. Heap / Priority Queue
2. Math
3. Graph (BFS / DFS / Dijkstra / DSU)
4. Binary Search Tree (BST)
5. Trees / Binary Trees
6. Greedy
7. 1-D & 2-D Arrays
8. Segment Tree / Range Queries
9. Arrays & Matrices
10. Searching / Binary Search
11. Two Pointers
12. Linked List
13. Number Theory / Misc
14. Trie / Bit Manipulation Trie
15. Dynamic Programming (DP)
16. Bit Manipulation
17. Hashing / Sliding Window
18. Queues / Deque / Monotonic Queue
19. Stack
20. Recursion
21. Backtracking
22. Sorting / Divide & Conquer

## Compiling the C++ Solutions

Most solutions include `#include <bits/stdc++.h>` for brevity. To compile a standalone snippet:

```bash
g++ -std=c++17 -O2 solution.cpp -o solution
./solution
```

Snippets that define class-like structures (segment trees, min-stack, iterators) are provided as the core class — wire them into your own `main` for testing.

## Suggested Study Order

1. **Foundational:** Arrays, Strings, Hashing, Two Pointers, Sliding Window.
2. **Structural:** Linked List, Stack, Queues/Deque, Heap.
3. **Tree/Graph basics:** Trees, BST, BFS/DFS on graphs.
4. **Algorithms:** Binary Search, Sorting / Divide & Conquer, Greedy.
5. **Advanced:** DP, Segment Tree, Trie, Bit Manipulation, Backtracking.

## Contributing

This repo is generated from a spreadsheet. Update the spreadsheet and regenerate to add problems; edit individual `*.md` files directly to refine explanations.

## License

For personal study use. Problem statements and links belong to their original platforms.
