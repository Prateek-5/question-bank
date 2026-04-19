# Minimum Number of Bottles Visible

## Problem Link
https://leetcode.com/problems/minimum-number-of-bottles-visible-when-standing-on-a-shelf/

## Topic
Sorting Divide and Conquer

## Core Concept
Greedy subtraction of consumed bottles based on exchange ratio.

## Intuition
Each exchange reduces total bottles; the minimum visible at end is (initial - fully consumed). Iteratively exchange until fewer than needed remain.

## Detailed Explanation
total = numBottles. empty = numBottles. While empty >= numExchange: new = empty / numExchange; total += new; empty = new + empty % numExchange.

## Dry Run
numBottles=9, numExchange=3. Drink 9. Exchange 9/3=3 → drink 3. Exchange 3/3=1 → drink 1. Total=13.

## Approach
Iterative exchange loop.

## Time and Space Complexity
Time: O(log). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int numWaterBottles(int nB, int nE) {
    int total = nB, empty = nB;
    while (empty >= nE) {
        int got = empty / nE;
        total += got;
        empty = got + empty % nE;
    }
    return total;
}
```

## Follow-up Questions
- Upper bound formula (nB + (nB-1)/(nE-1)).
- Multi-currency exchange.
- Rate-limited exchanges.
