# Number Theory / Misc — Concepts

## Core Theory
Number theory problems involve primes, divisors, modular arithmetic, GCD/LCM, and digit manipulations. Efficient techniques: trial division up to √n, sieve of Eratosthenes, fast exponentiation, digit DP.

## Common Patterns
- **Sieve of Eratosthenes** for all primes up to N.
- **Digit extraction** via repeated `% 10` / `/ 10`.
- **Divisor enumeration** up to √n.
- **Digit DP** for counts over ranges.

## When to Use
When inputs relate to integers, digits, primes, or modular structure. Often O(1) closed forms lurk behind seemingly complex problems.

## Template
```cpp
vector<bool> sieve(int n) {
    vector<bool> p(n+1, true); p[0]=p[1]=false;
    for (int i = 2; (long long)i*i <= n; ++i) if (p[i])
        for (int j = i*i; j <= n; j += i) p[j] = false;
    return p;
}
```

## Common Mistakes
- Integer overflow in products.
- Forgetting 1 and n as trivial divisors.
- Negative numbers in modular arithmetic.
