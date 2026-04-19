# Total Number of Divisors of a Given Number

## Problem Link
https://www.geeksforgeeks.org/dsa/total-number-divisors-given-number/

## Topic
Number Theory Misc

## Core Concept
Divisor-count via prime factorization: (e1+1)(e2+1)...

## Intuition
Each divisor corresponds to a choice of exponents within the prime factorization. Sum up exponent+1 product gives divisor count.

## Detailed Explanation
Factorize n by trial division up to sqrt(n). For each prime p with exponent e, multiply answer by (e+1).

## Dry Run
n=12=2²·3. (2+1)(1+1)=6 → divisors: 1,2,3,4,6,12.

## Approach
Trial division + exponent collection.

## Time and Space Complexity
Time: O(sqrt n). Space: O(1).

## C++ Implementation
```cpp
int divisorCount(int n) {
    int ans = 1;
    for (int p = 2; (long long)p*p <= n; ++p) {
        if (n % p) continue;
        int e = 0; while (n % p == 0) { n /= p; e++; }
        ans *= (e + 1);
    }
    if (n > 1) ans *= 2;
    return ans;
}
```

## Follow-up Questions
- Sum of divisors formula.
- Count divisors sieve for many n.
- Aliquot sum.
