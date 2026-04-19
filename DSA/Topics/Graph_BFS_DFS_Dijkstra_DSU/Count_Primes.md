# Count Primes

## Problem Link
https://leetcode.com/problems/count-primes/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Sieve of Eratosthenes.

## Intuition
Start from 2; for each prime, mark its multiples composite. What remains unmarked below n are primes.

## Detailed Explanation
Create isComposite[n] = false. For i from 2 to sqrt(n): if !isComposite[i], mark i*i, i*i+i, ... up to n-1. Count unmarked indices from 2..n-1.

## Dry Run
n=10. i=2: mark 4,6,8. i=3: mark 9. Unmarked 2..9: 2,3,5,7 → 4 primes.

## Approach
Classic sieve.

## Time and Space Complexity
Time: O(n log log n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int countPrimes(int n) {
    if (n < 3) return 0;
    vector<char> comp(n, 0);
    int cnt = 0;
    for (int i = 2; i < n; ++i) {
        if (comp[i]) continue;
        cnt++;
        if ((long long)i * i < n)
            for (int j = i*i; j < n; j += i) comp[j] = 1;
    }
    return cnt;
}
```

## Follow-up Questions
- Segmented sieve for huge n.
- Prime factorization using smallest-prime-factor array.
- Count primes in a range [L,R].
