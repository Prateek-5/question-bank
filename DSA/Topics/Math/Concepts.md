# Math — Concepts Guide

----------------------------------------

## 1. Introduction

Math problems in DSA interviews are rarely about advanced mathematics. They're about noticing structure — divisibility, modular arithmetic, digit properties, closed-form identities — that lets you skip the loop and jump to the answer. The reward for recognizing this structure is enormous: O(n) problems often collapse to O(1) formulas once you see the pattern.

----------------------------------------

## 2. Real-Life Analogy

Picture a long division problem you had as a kid. At first, you did it digit by digit — it took forever. Later, you noticed shortcuts: 'oh, if the last digit is 0 or 5, it's divisible by 5.' That observation turned minutes of work into a single glance. Math problems in interviews are exactly the same. Simulation always works, but the insight collapses the problem.

----------------------------------------

## 3. Core Idea

The fundamental tools here are modular arithmetic (remainders have beautiful closure properties), the Euclidean algorithm (GCD in O(log n) via repeated remainders), digit manipulation (extract via `% 10`, strip via `/ 10`), and combinatorial identities (sum of 1..n, binomial coefficients, Catalan numbers). Most math problems reduce to applying one of these tools, or combining two.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Signals that suggest a math approach:

- The problem mentions **primes, divisors, GCD, or LCM**.
- You're working with **digits of a number** (add/subtract/count them).
- **Modular constraints** appear: 'find count modulo M'.
- The input size is **huge (10^9 or more)**, suggesting no loop can scan it.
- You spot a **parity, symmetry, or pairing** pattern.

Before writing a loop, always ask: is there a formula for this? Often yes.

----------------------------------------

## 5. Types / Variations

- **Modular arithmetic** for large computations and counting problems mod some prime.
- **Sieve of Eratosthenes** for generating all primes up to N.
- **Fast exponentiation** for a^b mod m in O(log b).
- **Digit DP** for counting numbers in a range with digit constraints.
- **Bezout / Extended Euclidean** for solving linear Diophantine equations.

----------------------------------------

## 6. Step-by-Step Working

**Example — Digital Root (sum of digits iteratively until single digit):**

1. Observation: 10 ≡ 1 (mod 9), so any number is ≡ sum of its digits (mod 9).
2. Therefore digital root is determined entirely by n mod 9.
3. Edge case: multiples of 9 should return 9, not 0. The formula `1 + (n-1) % 9` handles this beautifully.

This is the archetype of math problems: observe a modular invariant → derive a closed form → handle the edge cases.

----------------------------------------

## 7. Visual Explanation

**Modular arithmetic cycle (mod 5):**

```
  0 → 1 → 2 → 3 → 4 → 0 → 1 → 2 → 3 → 4 → ...
```

**GCD via Euclid (a=48, b=18):**

```
gcd(48, 18) → gcd(18, 48%18=12)
            → gcd(12, 18%12=6)
            → gcd(6,  12%6=0)
            → 6
```

Each step halves one value on average — that's why Euclid's algorithm is O(log min(a,b)).

----------------------------------------

## 8. Code Templates (C++)

```cpp
// GCD and LCM
int g = __gcd(a, b);
long long l = (long long)a / g * b;

// Fast power (a^b mod m)
long long power(long long a, long long b, long long m) {
    long long r = 1 % m; a %= m;
    while (b) {
        if (b & 1) r = r * a % m;
        a = a * a % m;
        b >>= 1;
    }
    return r;
}

// Sieve of Eratosthenes
vector<bool> sieve(int n) {
    vector<bool> is_prime(n + 1, true);
    is_prime[0] = is_prime[1] = false;
    for (int i = 2; (long long)i * i <= n; ++i) if (is_prime[i])
        for (int j = i * i; j <= n; j += i) is_prime[j] = false;
    return is_prime;
}
```

----------------------------------------

## 9. Common Mistakes

- **Integer overflow** on multiplication — use `long long` when in doubt.
- **Negative modulo**: `((x % k) + k) % k` to handle negatives correctly.
- **Off-by-one in inclusive/exclusive ranges** — clarify before coding.
- **Assuming 0 is prime** (it's not, and neither is 1).
- **Forgetting that `/` is integer division** on int operands — `5 / 2 = 2`, not `2.5`.

----------------------------------------

## 10. Interview Insights

Math problems are where interviewers test your willingness to observe before you code. They want to see:

1. **Do you pause to find structure, or do you immediately loop?** Pausing is the right habit.
2. **Can you articulate *why* a formula works?** Stating 'it's just `1 + (n-1) % 9`' without justification is weak; explaining 'because 10 ≡ 1 (mod 9)' is strong.
3. **Do you handle edge cases (zero, one, negatives, overflow)?** Math questions are a goldmine for these.

Tip: if the problem constraints allow n up to 10^9 or more, there's almost certainly a formula — don't waste time looking for a loop-based solution.
