# Largest Number That Divides X and Is Co-Prime with Y

**Problem Link:**
<a href="https://www.geeksforgeeks.org/dsa/largest-number-divides-x-co-prime-y/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/dsa/largest-number-divides-x-co-prime-y/</a>

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: State the Problem

Given two positive integers X and Y, find the **largest integer D** such that:
- D divides X, AND
- gcd(D, Y) = 1 (D is coprime with Y).

Example: X = 15, Y = 3.
Divisors of 15: {1, 3, 5, 15}. Check coprime with 3:
- gcd(1, 3) = 1 ✓.
- gcd(3, 3) = 3 ✗.
- gcd(5, 3) = 1 ✓.
- gcd(15, 3) = 3 ✗.

Valid: {1, 5}. Largest = **5**.

Example: X = 12, Y = 5.
Divisors of 12: {1, 2, 3, 4, 6, 12}. All coprime with 5 (5 shares no factor with 12). Largest = **12**.

----------------------------------------

## Step 2: Key Observation

gcd(D, Y) = 1 means D and Y share **no prime factors**. So we want the largest divisor of X that avoids all prime factors of Y.

Equivalently: remove all common prime factors from X. The result is the largest divisor of X coprime with Y.

More concretely: let g = gcd(X, Y). Then X / g might still have common factors with Y (if X had higher powers of a shared prime than Y does). We need to strip **all** occurrences of primes shared between X and Y.

----------------------------------------

## Step 3: The Repeated-GCD Trick

Algorithm:
```
D = X
while gcd(D, Y) > 1:
    D = D / gcd(D, Y)
return D
```

Each iteration removes one "round" of common factors. After enough iterations, gcd(D, Y) = 1.

Why does this terminate? Because D strictly decreases each iteration (dividing by gcd > 1). Eventually it hits a value with no common factors (possibly 1).

----------------------------------------

## Step 4: Trace

**X = 15, Y = 3**:
- D = 15. gcd(15, 3) = 3. D = 15 / 3 = 5.
- gcd(5, 3) = 1. Stop.
- Return **5**. ✓

**X = 12, Y = 5**:
- D = 12. gcd(12, 5) = 1. Stop immediately.
- Return **12**. ✓

**X = 100, Y = 10**:
- D = 100. gcd(100, 10) = 10. D = 10.
- D = 10. gcd(10, 10) = 10. D = 1.
- gcd(1, 10) = 1. Stop.
- Return **1**.

Sanity: divisors of 100 are {1, 2, 4, 5, 10, 20, 25, 50, 100}. Coprime with 10 (shared primes 2, 5): only 1 qualifies. ✓

**X = 200, Y = 6**:
- D = 200. gcd(200, 6) = 2. D = 100.
- D = 100. gcd(100, 6) = 2. D = 50.
- D = 50. gcd(50, 6) = 2. D = 25.
- D = 25. gcd(25, 6) = 1. Stop.
- Return **25**.

Check: 25 divides 200? 200 / 25 = 8, yes. gcd(25, 6) = 1? 25 = 5², 6 = 2·3, no common primes. ✓

----------------------------------------

## Step 5: Why Does Each Iteration Progress?

Each iteration removes at least one factor of some common prime. Specifically, after dividing D by gcd(D, Y), every prime that was in both D and Y has its power in D **reduced by the minimum of the two powers** (the gcd operation).

But some primes may still be common — if Y had a prime p with multiplicity 2 but D had p with multiplicity 5, after one division D still has p with multiplicity 5 - 2 = 3. We repeat.

After enough iterations, D's multiplicity for each shared prime drops to 0. gcd becomes 1.

----------------------------------------

## Step 6: Why Not Just Compute Once?

The single-pass `D = X / gcd(X, Y)` would **not** always give the correct answer.

Consider X = 100 = 2² · 5², Y = 10 = 2 · 5. gcd = 10. X / gcd = 10. But 10 still shares factors with Y. The true answer is 1.

The repeated-gcd loop keeps peeling until fully coprime.

----------------------------------------

## Step 7: Alternative — Prime Factorization

Compute prime factorization of X and Y. Remove from X every prime that appears in Y (regardless of multiplicity). The result's numerical value is D.

Example: X = 100 = 2²·5². Y = 10 has primes {2, 5}. Remove all 2's and 5's from X → 1. ✓

This is arguably the conceptually cleanest. The repeated-gcd trick avoids explicit factorization and is usually preferred in code.

----------------------------------------

## Step 8: Name It

**Coprime reduction via iterated GCD**. A specific number-theory idiom.

Related techniques:
- Euler's totient computation: strip shared prime powers.
- Radical of an integer: multiply each distinct prime once.
- Möbius function: tracks square-freeness.

----------------------------------------

## Step 9: Complexity

Each iteration: O(log min(D, Y)) for gcd via Euclidean algorithm.

Iterations: bounded by the number of times we can divide D by a factor ≥ 2 → **O(log X)**.

Total: **O(log²X)** or so.

Space: O(1).

----------------------------------------

## Step 10: C++ Implementation

```cpp
int largestCoprimeDivisor(int X, int Y) {
    int D = X;
    while (true) {
        int g = __gcd(D, Y);
        if (g == 1) break;
        D /= g;
    }
    return D;
}
```

Four lines inside the loop. `__gcd` from `<algorithm>` or write Euclidean manually.

----------------------------------------

## Step 11: Follow-up Questions

- **Smallest such D (≥ 1) instead.** That's just 1 — always coprime with everything, always divides any X. Trivial.
- **Find all divisors of X coprime with Y.** Enumerate divisors of X (O(√X)) and filter those coprime with Y.
- **Given X and Y, find gcd(X, Y^∞).** Repeated gcd converges to the "Y-smooth" part of X. Our D is X / that.
- **What if Y = 1?** gcd(D, 1) = 1 for any D. Return D = X. (Algorithm terminates immediately.)
- **What if X < Y?** Still works; no special case.
- **What if X = 0?** gcd(0, Y) = Y > 1 (assuming Y > 1); division loops. Handle edge case: X = 0 → D = 0 (but 0 divided by anything is 0, and 0 is coprime with 1 only...). The problem usually guarantees X ≥ 1.
