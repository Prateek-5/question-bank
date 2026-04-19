# Number Theory / Misc — Concepts Guide

----------------------------------------

## 1. Introduction

Number theory problems are elegance in disguise. An O(n) brute force often hides an O(1) formula, an O(n²) check often hides an O(log n) trick. The skill is recognizing the structure quickly — digit patterns, divisibility, modular arithmetic — before racing to code.

----------------------------------------

## 2. Real-Life Analogy

Think of a lock with a specific combination pattern (every third digit must be even, say). A brute-force solver tries every combination. A pattern-recognizer enumerates only the valid ones — maybe 1/10th the work. Number theory gives us the tools to identify those patterns and skip ahead.

----------------------------------------

## 3. Core Idea

The core tools are: modular arithmetic (closure, inverse), prime factorization (trial division up to √n), the Euclidean algorithm (GCD/LCM), digit decomposition (% 10 / divide by 10), and digit-DP for counting-over-ranges problems. Most 'miscellaneous' problems combine two of these tools.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Signals for number theory:

- **Digits of a number are involved.**
- **Primes, factors, divisors are mentioned.**
- **Constraints are gigantic (10^9+)** — formula required.
- **Counts modulo a prime.**
- **Periodicity or parity shows up.**

----------------------------------------

## 5. Types / Variations

- **Sieve of Eratosthenes** for listing primes up to N.
- **Fast exponentiation** for a^b mod m in O(log b).
- **Euler's totient** for counting integers coprime to n.
- **Digit DP** for counting numbers in [L, R] with some digit property.
- **Chinese Remainder Theorem** for systems of congruences.

----------------------------------------

## 6. Step-by-Step Working

**Digit sum / digital root:**
1. Observation: 10 ≡ 1 (mod 9), so digit sum ≡ n (mod 9).
2. Therefore digital root = 1 + (n-1) mod 9 for n ≥ 1.

**Sieve:**
1. Mark 0 and 1 as non-prime.
2. For i = 2 to √n: if i is prime, mark i·i, i·i+i, ... as composite.
3. Remaining unmarked indices are prime.

----------------------------------------

## 7. Visual Explanation

**Sieve up to 10:**

```
Init: 2 3 4 5 6 7 8 9 10  (all candidate)
i=2 (prime): cross out 4, 6, 8, 10
Remaining: 2 3 5 7 9
i=3 (prime): cross out 9
Remaining: 2 3 5 7

√10 ≈ 3.16, stop.

Primes ≤ 10: 2, 3, 5, 7.
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Sieve
vector<bool> sieve(int n) {
    vector<bool> p(n + 1, true);
    p[0] = p[1] = false;
    for (int i = 2; (long long)i * i <= n; ++i) if (p[i])
        for (int j = i * i; j <= n; j += i) p[j] = false;
    return p;
}

// Divisor count via factorization
int divisorCount(int n) {
    int ans = 1;
    for (int p = 2; (long long)p * p <= n; ++p) {
        if (n % p) continue;
        int e = 0;
        while (n % p == 0) { n /= p; e++; }
        ans *= (e + 1);
    }
    if (n > 1) ans *= 2;
    return ans;
}
```

----------------------------------------

## 9. Common Mistakes

- **Integer overflow** on products of large numbers.
- **Negative modulo** — always `((x % m) + m) % m`.
- **Forgetting that 1 is not prime.**
- **Sieving without `i * i` optimization** — doubles runtime.
- **Confusing GCD and LCM formulas.**

----------------------------------------

## 10. Interview Insights

Number theory problems test structural observation. Interviewers want to see:

1. **You pause to find a formula before coding.**
2. **You can explain *why* the formula works.**
3. **You handle edge cases** (0, 1, negatives).
4. **You're aware of overflow.**

If n ≤ 10^6, a sieve is probably fine. If n ≤ 10^9, you need a formula or a per-query O(√n). If n ≤ 10^18, only O(log n) or O(1) survives.
