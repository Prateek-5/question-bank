# Total Hamming Distance

## Problem Link
https://leetcode.com/problems/total-hamming-distance/

## Topic
Arrays and Matrices

## Core Concept
Bitwise counting — per bit, contribution = ones * zeros.

## Intuition
Hamming distance sums over pairs. Each bit position contributes count_of_1s * count_of_0s pairs that differ in that bit.

## Detailed Explanation
For each bit b (0..31): count ones among nums with (num>>b)&1. answer += ones * (n - ones). Sum over all bits.

## Dry Run
nums=[4,14,2]. Bit 1: binaries 100,1110,010. ones=2, zeros=1 → 2. Bit 2: ones=1,zeros=2→2. Bit 3: ones=1,zeros=2→2. Total=6.

## Approach
32 * n per-bit count.

## Time and Space Complexity
Time: O(32n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int totalHammingDistance(vector<int>& nums) {
    int n = nums.size(), ans = 0;
    for (int b = 0; b < 32; ++b) {
        int ones = 0;
        for (int x : nums) ones += (x >> b) & 1;
        ans += ones * (n - ones);
    }
    return ans;
}
```

## Follow-up Questions
- Hamming distance of single pair.
- Total weighted Hamming distance.
- Minimum Hamming distance via sorting.
