# Number of Good Pairs

## Problem Link
https://leetcode.com/problems/number-of-good-pairs/

## Topic
Number Theory Misc

## Core Concept
For each value of count c, pairs = C(c,2).

## Intuition
Two indices i<j form a good pair iff nums[i]==nums[j]. For each value with count c, pairs = c*(c-1)/2.

## Detailed Explanation
Count occurrences; sum c*(c-1)/2.

## Dry Run
nums=[1,2,3,1,1,3]. Counts {1:3,2:1,3:2}. Pairs 3+0+1=4.

## Approach
Hashmap frequency.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int numIdenticalPairs(vector<int>& a) {
    unordered_map<int,int> c;
    int ans = 0;
    for (int x : a) ans += c[x]++;
    return ans;
}
```

## Follow-up Questions
- Good pairs at distance ≤ k.
- Ordered pairs (i<j with constraint).
- With updates.
