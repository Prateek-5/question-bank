# Reverse Bits

## Problem Link
https://leetcode.com/problems/reverse-bits/

## Topic
Bit Manipulation

## Core Concept
Bit-by-bit reversal or swap-and-shift.

## Intuition
Read LSB of n, set it as the MSB of result. Shift both appropriately.

## Detailed Explanation
For 32 bits: r = (r << 1) | (n & 1); n >>= 1.

## Dry Run
n=43261596 (0000 0010 1001 0100 0001 1110 1001 1100) → reversed = 964176192.

## Approach
Loop 32 iterations.

## Time and Space Complexity
Time: O(32). Space: O(1).

## C++ Implementation
```cpp
unsigned reverseBits(unsigned n) {
    unsigned r = 0;
    for (int i = 0; i < 32; ++i) { r = (r << 1) | (n & 1); n >>= 1; }
    return r;
}
```

## Follow-up Questions
- Parallel reversal via SWAR.
- Reverse k-bit integer.
- Cache repeated reversals with byte-lookup.
