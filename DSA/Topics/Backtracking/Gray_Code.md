# Gray Code

## Problem Link
https://leetcode.com/problems/gray-code/

## Topic
Backtracking

## Core Concept
Reflect-and-prefix construction.

## Intuition
A Gray code of n bits is the (n-1)-bit code followed by its reverse with MSB set.

## Detailed Explanation
Start with [0,1]. For each bit from 1 to n-1: duplicate list in reverse, OR top bit (1<<i) onto the new half.

## Dry Run
n=2: start [0,1]. Reflect → [0,1,1,0]. OR with 2 on new half → [0,1,3,2].

## Approach
Iterative reflection.

## Time and Space Complexity
Time: O(2^n). Space: O(2^n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> grayCode(int n) {
    vector<int> r = {0};
    for (int i = 0; i < n; ++i) {
        int sz = r.size();
        for (int j = sz - 1; j >= 0; --j) r.push_back(r[j] | (1 << i));
    }
    return r;
}
```

## Follow-up Questions
- Direct formula: i ^ (i>>1).
- Gray code for non-powers-of-two.
- Balanced Gray code.
