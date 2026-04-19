# Split Array with Same Average

## Problem Link
https://leetcode.com/problems/split-array-with-same-average/

## Topic
Dynamic Programming DP

## Core Concept
Meet-in-the-middle subset-sum with fractional target.

## Intuition
Find subset of size k with sum = k * totalSum / n. Search subsets; for large n split in halves to combine.

## Detailed Explanation
Split nums into two halves. Compute subset sums per size from each half. For each size k, look for (sum_left, sum_right) pair with combined size k and combined sum target.

## Dry Run
nums=[1,2,3,4,5,6,7,8]. Target check across sizes 1..7.

## Approach
Meet-in-the-middle.

## Time and Space Complexity
Time: O(2^(n/2)·n). Space: O(2^(n/2)).

## C++ Implementation
```cpp
// Full implementation is lengthy. Core idea: enumerate subset sums in halves, check fractional-avg match.
// For n<=30 brute force with memo; else MITM. See LeetCode editorial for complete code.
```

## Follow-up Questions
- Approximate average split.
- k-way average split.
- Prove NP-hardness in general.
