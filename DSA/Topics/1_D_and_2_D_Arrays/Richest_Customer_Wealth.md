# Richest Customer Wealth

## Problem Link
https://leetcode.com/problems/richest-customer-wealth/

## Topic
1 D and 2 D Arrays

## Core Concept
Max of row sums.

## Intuition
Each customer's wealth is the sum of their row; answer is the maximum row sum.

## Detailed Explanation
Iterate rows, accumulate sum, track max.

## Dry Run
accounts=[[1,2,3],[3,2,1]]. Sums 6 and 6 → 6.

## Approach
Straightforward double loop.

## Time and Space Complexity
Time: O(n*m). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maximumWealth(vector<vector<int>>& a) {
    int best = 0;
    for (auto& r : a) best = max(best, accumulate(r.begin(), r.end(), 0));
    return best;
}
```

## Follow-up Questions
- Tie-breaking by customer index.
- Online updates to accounts.
- Top-k richest customers.
