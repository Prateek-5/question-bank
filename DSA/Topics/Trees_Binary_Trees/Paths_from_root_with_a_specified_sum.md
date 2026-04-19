# Paths from root with a specified sum

## Problem Link
https://www.geeksforgeeks.org/problems/paths-from-root-with-a-specified-sum/1

## Topic
Trees Binary Trees

## Core Concept
DFS enumerating root-downward paths with running sum.

## Intuition
Generate every downward path from the root (full or partial) and check which sum equals the target.

## Detailed Explanation
Recurse with current path. At each node, add to current path; check each *suffix* starting from root to current equaling target (or use prefix-sum map for efficiency).

## Dry Run
Tree 10,5,-3,3,2,_,11,3,-2,_,1. Target=8. Paths: 5→3, 5→2→1, -3→11.

## Approach
DFS with prefix-sum map (see Path Sum III).

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
// See Path Sum III implementation — same pattern with prefix-sum map.
```

## Follow-up Questions
- Constrain path to a minimum length.
- Count vs enumerate the paths.
- Extend to any two nodes (not just downward).
