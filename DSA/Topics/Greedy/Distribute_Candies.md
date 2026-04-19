# Distribute Candies

## Problem Link
https://leetcode.com/problems/distribute-candies/

## Topic
Greedy

## Core Concept
Return min(unique kinds, n/2).

## Intuition
Sister can get at most n/2 candies. Among those, distinct kinds are capped by the number of unique candies overall.

## Detailed Explanation
Count unique types (set). Answer = min(unique, n/2).

## Dry Run
candies=[1,1,2,2,3,3]. unique=3, n/2=3 → 3.

## Approach
Single pass + set.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int distributeCandies(vector<int>& c) {
    return min((int)c.size()/2, (int)unordered_set<int>(c.begin(), c.end()).size());
}
```

## Follow-up Questions
- Distribute among k siblings.
- Weighted candies (different value per type).
- Maximize minimum across siblings.
