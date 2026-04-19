# Pow(x, n)

## Problem Link
https://leetcode.com/problems/powx-n/

## Topic
Number Theory Misc

## Core Concept
Binary exponentiation.

## Intuition
x^n = (x²)^(n/2) if n even; x * x^(n-1) if odd. Repeated squaring yields O(log n) multiplications.

## Detailed Explanation
If n < 0: x = 1/x, n = -n. Loop: if n odd multiply result by x; x = x*x; n >>= 1.

## Dry Run
x=2, n=10. x^10 = 4^5 = (16)·4 = 64·16 = 1024.

## Approach
Iterative binary exponentiation.

## Time and Space Complexity
Time: O(log n). Space: O(1).

## C++ Implementation
```cpp
double myPow(double x, int n) {
    long long N = n;
    if (N < 0) { x = 1.0 / x; N = -N; }
    double r = 1.0;
    while (N) {
        if (N & 1) r *= x;
        x *= x; N >>= 1;
    }
    return r;
}
```

## Follow-up Questions
- Modular exponentiation (x^n mod M).
- Matrix exponentiation (Fibonacci).
- Handle underflow/overflow.
