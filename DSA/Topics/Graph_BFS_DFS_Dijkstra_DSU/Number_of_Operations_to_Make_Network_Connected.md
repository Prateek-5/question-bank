# Number of Operations to Make Network Connected

## Problem Link
https://leetcode.com/problems/number-of-operations-to-make-network-connected/description/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Duplicate of earlier problem — see the first entry.

## Intuition
Same as 'Number of Operations to Make Network Connected': DSU; components-1 moves if enough extra cables.

## Detailed Explanation
Count components via DSU; count extra edges (those that would form a cycle). If extras >= components-1, answer = components-1; else -1.

## Dry Run
See 'Number of Operations to Make Network Connected'.

## Approach
Union-Find.

## Time and Space Complexity
Time: O(E α). Space: O(n).

## C++ Implementation
```cpp
// See 'Number of Operations to Make Network Connected' implementation above.
```

## Follow-up Questions
- See original entry.
