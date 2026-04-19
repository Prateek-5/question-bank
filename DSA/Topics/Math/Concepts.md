# Math — Concepts

## Core Theory
Math problems often reduce to modular arithmetic, divisibility rules, combinatorics, or closed-form identities. Recognizing structure — like digital roots, pigeonhole principle, Euclidean GCD — converts naive simulations into O(1) or O(log n) solutions.

## Common Patterns
- **Digital root:** 1 + (n-1) % 9 for positive n.
- **Prefix sums modulo k:** detect subarrays divisible by k.
- **Pigeonhole:** n+1 items in n boxes forces a collision.
- **GCD via Euclid:** gcd(a, b) = gcd(b, a%b); O(log min).
- **Modular exponentiation:** binary fast power in O(log exp).

## When to Use
Whenever brute force over values or pairs feels excessive. Look for modular invariants, symmetries, and closed forms before coding a loop.

## Template
```cpp
long long power(long long a, long long b, long long m) {
    long long r = 1 % m; a %= m;
    while (b) { if (b & 1) r = r * a % m; a = a * a % m; b >>= 1; }
    return r;
}
```

## Common Mistakes
- Overflow on intermediate products (use 64-bit).
- Negative modulo: `((x % k) + k) % k`.
- Integer division rounding for floors/ceilings.
- Off-by-one with inclusive/exclusive ranges.
