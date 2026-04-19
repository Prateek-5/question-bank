# Number of 1 Bits

## Problem Link
https://leetcode.com/problems/number-of-1-bits/

## Topic
Bit Manipulation

## Core Concept
Bit trick — n & (n-1) clears lowest set bit.

## Intuition
Each n&(n-1) drops exactly one set bit. Count iterations until zero.

## Detailed Explanation
while (n) { n &= n-1; cnt++; }.

## Dry Run
n=11 (1011). 1011→1010→1000→0000. 3 iterations → 3.

## Approach
Brian Kernighan's trick.

## Time and Space Complexity
Time: O(popcount). Space: O(1).

## C++ Implementation
```cpp
int hammingWeight(unsigned n) { int c = 0; while (n) { n &= n - 1; c++; } return c; }
```

## Follow-up Questions
- Use __builtin_popcount.
- SWAR parallel bit counting.
- Hamming weight of a range of integers.
