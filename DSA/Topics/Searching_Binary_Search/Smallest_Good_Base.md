# Smallest Good Base

## Problem Link
https://leetcode.com/problems/smallest-good-base/description/

## Topic
Searching Binary Search

## Core Concept
For each possible base length m, binary search base k such that 1+k+k²+...+k^(m-1) = n.

## Intuition
If n has m representation digits of all 1s in base k, then n = (k^m - 1)/(k-1). For small m, solve for k by binary search.

## Detailed Explanation
For m from log2(n+1) down to 2: binary search k in [2, n^(1/(m-1))]. Evaluate polynomial; if equals n, return k. Default m=1 → k=n-1.

## Dry Run
n=13. m=3: binary search k; 1+k+k²=13 → k=3. Return '3'.

## Approach
Outer loop on digit count, inner binary search.

## Time and Space Complexity
Time: O(log² n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
string smallestGoodBase(string s) {
    long long n = stoll(s);
    for (int m = 60; m >= 2; --m) {
        long long lo = 2, hi = pow(n, 1.0/(m-1)) + 1;
        while (lo <= hi) {
            long long k = (lo + hi) / 2, sum = 0, p = 1;
            bool over = false;
            for (int i = 0; i < m; ++i) {
                if (p > n) { over = true; break; }
                sum += p;
                if (i < m-1) p *= k;
            }
            if (!over && sum == n) return to_string(k);
            if (over || sum > n) hi = k - 1;
            else lo = k + 1;
        }
    }
    return to_string(n - 1);
}
```

## Follow-up Questions
- Largest good base instead.
- Good base in fixed range of m.
- Represent n with digits in [0,d].
