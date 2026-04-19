# Memoization / DP Basics

## Problem Link
https://leetcode.com/tag/dynamic-programming/

## Topic
Number Theory Misc

## Core Concept
Memoized recursion — cache results to avoid recomputation.

## Intuition
DP problems often have overlapping subproblems; caching transforms exponential recursion into polynomial.

## Detailed Explanation
Identify state; write recurrence; cache via map/array; base case; return cached on hit.

## Dry Run
Fibonacci f(5)=f(4)+f(3); each subproblem computed once with memo[].

## Approach
Top-down recursion with memoization.

## Time and Space Complexity
Depends on state count × work per state.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int fib(int n, vector<int>& memo) {
    if (n < 2) return n;
    if (memo[n] != -1) return memo[n];
    return memo[n] = fib(n-1, memo) + fib(n-2, memo);
}
```

## Follow-up Questions
- Bottom-up conversion.
- Space optimization with rolling arrays.
- Recognizing DP states in new problems.
