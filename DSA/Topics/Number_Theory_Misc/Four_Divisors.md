# Four Divisors

## Problem Link
https://leetcode.com/problems/four-divisors/

## Topic
Number Theory Misc

## Core Concept
For each n, find divisors up to sqrt; only sum if divisor count is exactly 4.

## Intuition
A number with exactly 4 divisors has divisors {1, p, q, pq} for primes p≠q, or {1, p, p², p³} for prime p. Detect by enumerating up to sqrt(n).

## Detailed Explanation
For each n, collect divisors ≤ sqrt(n); pair with n/d unless d*d==n. If count is 4, add sum to answer.

## Dry Run
nums=[21,4,7]. 21: divisors 1,3,7,21 → sum=32. 4: 1,2,4 → 3 divisors. 7: 2 divisors. Answer=32.

## Approach
sqrt scan per number.

## Time and Space Complexity
Time: O(N·sqrt(max)). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int sumFourDivisors(vector<int>& nums) {
    int ans = 0;
    for (int n : nums) {
        int cnt = 0, sum = 0;
        for (int i = 1; (long long)i*i <= n && cnt <= 4; ++i) if (n % i == 0) {
            cnt++; sum += i;
            if (i != n / i) { cnt++; sum += n / i; }
        }
        if (cnt == 4) ans += sum;
    }
    return ans;
}
```

## Follow-up Questions
- Numbers with exactly k divisors.
- Sum of divisors sieve for many n.
- Euler totient counting.
