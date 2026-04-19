# Single Number II

## Problem Link
https://leetcode.com/problems/single-number-ii/

## Topic
Bit Manipulation

## Core Concept
Bit counting mod 3 — every bit sums to 0 mod 3 except for the unique number.

## Intuition
For each of 32 bits, total count mod 3 is the bit of the lone number.

## Detailed Explanation
For each bit: ones=Σ((x>>b)&1); result bit = ones%3. Or use two-variable state machine (ones/twos).

## Dry Run
nums=[2,2,3,2] → each bit of 3 has one extra → result 3.

## Approach
Bit-count or state machine.

## Time and Space Complexity
Time: O(32n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int singleNumberII(vector<int>& a) {
    int ones = 0, twos = 0;
    for (int x : a) {
        ones = (ones ^ x) & ~twos;
        twos = (twos ^ x) & ~ones;
    }
    return ones;
}
```

## Follow-up Questions
- Others appear k times.
- Two numbers appear once.
- Streaming variant.
