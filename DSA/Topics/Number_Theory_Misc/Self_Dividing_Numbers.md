# Self Dividing Numbers

## Problem Link
https://leetcode.com/problems/self-dividing-numbers/

## Topic
Number Theory Misc

## Core Concept
For each n in [L,R], check all its digits are non-zero and divide n.

## Intuition
A self-dividing number has only digits that are divisors of itself. Enumerate and test.

## Detailed Explanation
For each n: d=n; while d: q=d%10; if q==0 or n%q!=0 fail; d/=10. If pass, add n.

## Dry Run
Range [1,22]. Numbers 1..9 all qualify. 11 works (1,1). 12 (1,2) works. 13 (1,3) 13%3≠0 fail. Etc.

## Approach
Brute force digit test.

## Time and Space Complexity
Time: O((R-L+1)·logR). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> selfDividingNumbers(int L, int R) {
    vector<int> r;
    for (int n = L; n <= R; ++n) {
        int d = n; bool ok = true;
        while (d) {
            int q = d % 10;
            if (!q || n % q) { ok = false; break; }
            d /= 10;
        }
        if (ok) r.push_back(n);
    }
    return r;
}
```

## Follow-up Questions
- Self-dividing with custom base.
- Harshad numbers.
- Armstrong numbers.
