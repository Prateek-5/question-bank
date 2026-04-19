# Subarrays with XOR Less Than K (Concept)

## Problem Link
https://leetcode.com/problems/subarray-xor-queries/

## Topic
Trie Bit Manipulation Trie

## Core Concept
Binary-trie over prefix XORs to count subarrays with XOR < K.

## Intuition
For each prefix XOR p, count earlier prefix XORs q such that p ^ q < K. A bit-trie lets us count candidates branch-by-branch using bits of K.

## Detailed Explanation
Insert prefix XORs into bit-trie; maintain subtree counts. For query p, traverse bits of K: if K's bit is 1, all numbers with different-current-bit in opposite branch satisfy strict-less; descend into same-bit branch to check the rest. If K's bit is 0, descend into same-bit.

## Dry Run
arr=[1,2,3,4], K=4. Build prefix XOR; count pairs (p,q) with p^q<4 → answer derived via trie.

## Approach
Bit trie with subtree counters.

## Time and Space Complexity
Time: O(n·log max). Space: O(n·log max).

## C++ Implementation
```cpp
// Template omitted for brevity; see Maximum XOR trie structure with additional subtree counts.
```

## Follow-up Questions
- XOR subarrays equal to K.
- XOR in a range K1..K2.
- Max XOR of subarray.
