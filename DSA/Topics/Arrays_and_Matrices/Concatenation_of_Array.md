# Concatenation of Array

## Problem Link
https://leetcode.com/problems/concatenation-of-array/

## Topic
Arrays and Matrices

## Core Concept
Build [nums, nums] concatenated.

## Intuition
Just double the array: answer[i]=nums[i%n].

## Detailed Explanation
Create ans of size 2n; copy nums twice.

## Dry Run
nums=[1,2,1]. Answer=[1,2,1,1,2,1].

## Approach
Single loop copy.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> getConcatenation(vector<int>& a) {
    int n = a.size();
    vector<int> r(2*n);
    for (int i = 0; i < 2*n; ++i) r[i] = a[i % n];
    return r;
}
```

## Follow-up Questions
- Generalize to k concatenations.
- Reverse-concatenation.
- Memory-efficient virtual concatenation.
