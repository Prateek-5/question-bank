# Partition Equal Subset Sum

## Problem Link
https://leetcode.com/problems/partition-equal-subset-sum/

## Topic
Dynamic Programming DP

## Core Concept
0/1 subset-sum DP target = total/2.

## Intuition
Can we pick a subset that sums to half the total? If total is odd, impossible; else boolean DP on reachable sums.

## Detailed Explanation
target = sum/2. dp bitset of size target+1; dp[0]=true. For each num: dp |= dp << num. Return dp[target].

## Dry Run
nums=[1,5,11,5]. sum=22, target=11. Reachable includes 11 → true.

## Approach
Bitset DP.

## Time and Space Complexity
Time: O(n·target/64). Space: O(target/64).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool canPartition(vector<int>& a) {
    int s = accumulate(a.begin(), a.end(), 0);
    if (s & 1) return false;
    int t = s / 2;
    bitset<10001> dp; dp[0] = 1;
    for (int x : a) dp |= dp << x;
    return dp[t];
}
```

## Follow-up Questions
- k-partition into equal sums.
- Minimum difference between two subsets.
- Count subsets summing to target.
