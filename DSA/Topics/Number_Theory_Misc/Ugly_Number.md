# Ugly Number

**Problem Link:**
https://leetcode.com/problems/ugly-number/

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: What's an Ugly Number?

An **ugly number** is a positive integer whose **only prime factors are 2, 3, or 5** (in any quantity, including none).

Examples of ugly numbers: 1 (no prime factors, trivially ugly), 2, 3, 4 (= 2·2), 5, 6 (= 2·3), 8, 9 (= 3·3), 10 (= 2·5), 12 (= 2²·3), etc.

NOT ugly: 7 (prime factor 7), 14 (= 2·7), 11 (prime 11), 0 (not positive), -6 (not positive).

Given n, return true if n is ugly, false otherwise.

----------------------------------------

## Step 2: Direct Approach — Strip Out 2, 3, 5

If n's only prime factors are 2, 3, 5, then dividing n by those primes repeatedly until we can't anymore should leave us with **1**. If we're left with something other than 1, there's some other prime factor — not ugly.

```
def isUgly(n):
    if n <= 0: return False
    for p in [2, 3, 5]:
        while n % p == 0:
            n //= p
    return n == 1
```

Example: n = 14.
- Divide by 2: 14 → 7.
- 7 % 2 ≠ 0. Try 3. 7 % 3 ≠ 0. Try 5. 7 % 5 ≠ 0.
- Final n = 7 ≠ 1. Return false. ✓

Example: n = 30.
- / 2: 30 → 15.
- / 3: 15 → 5.
- / 5: 5 → 1.
- Final n = 1. Return true. ✓

Example: n = 1.
- No divisions apply.
- Return true (1 == 1). ✓

Example: n = 0 or negative.
- Return false immediately.

----------------------------------------

## Step 3: Why This Works

**Claim:** n is ugly iff repeatedly dividing by 2, 3, 5 (in any order) eventually yields 1.

**Proof direction 1:** If n is ugly, then n = 2^a · 3^b · 5^c for some non-negative integers a, b, c. Dividing n by 2 `a` times, by 3 `b` times, and by 5 `c` times leaves 1.

**Proof direction 2:** If dividing yields 1, then n was completely expressible as products of 2, 3, 5. So n's only prime factors are those.

The order of divisions doesn't matter: dividing by 2 first vs. by 3 first gives the same final result because multiplication is commutative.

----------------------------------------

## Step 4: Edge Cases

- **n = 0:** not positive. Return false.
- **n < 0:** negative numbers aren't typically considered "ugly" in this convention. Return false.
- **n = 1:** special case. 1 has no prime factors at all, which vacuously satisfies "only factors are 2, 3, 5." Return true.
- **n is prime and > 5 (e.g., 7, 11):** won't be divisible by any of 2, 3, 5. Final n > 1. Return false.
- **n is a large ugly number:** keeps dividing; eventually reaches 1.

The guard `if n <= 0: return False` catches the first two cases. The loop handles 1 implicitly (0 divisions, returns true). The rest follow naturally.

----------------------------------------

## Step 5: Complexity

Time: each division reduces n by at least a factor of 2. So O(log n) divisions at most.
Space: O(1).

Very fast.

----------------------------------------

## Step 6: Name It

This is **prime-factor filtering** — check if n's prime factors are exactly a given set. The algorithm generalizes: to check if n's prime factors are within any set S, divide by each p ∈ S as long as possible; return n == 1.

Related:
- Ugly Number II: generate the n-th ugly number (different, harder).
- Super Ugly Number: ugly with an arbitrary prime set.
- Check if n is a power of k: similar stripping.

----------------------------------------

## Step 7: C++ Implementation

```cpp
bool isUgly(int n) {
    if (n <= 0) return false;
    for (int p : {2, 3, 5}) {
        while (n % p == 0) n /= p;
    }
    return n == 1;
}
```

Five lines. The `for (int p : {2, 3, 5})` is a range-based loop over an initializer list — a clean C++11 way to list the primes we care about.

----------------------------------------

## Step 8: Follow-up Questions

- **Check if n is a power of two.** Use `n > 0 && (n & (n - 1)) == 0`. Much faster than dividing.
- **Check if n's prime factors are in some arbitrary set.** Same pattern; iterate through each prime in the set.
- **Ugly Number II: return the n-th ugly number.** Different problem — use a min-heap or 3-pointer DP.
- **Count ugly numbers ≤ N.** Harder; involves careful enumeration.
- **What if n can be very large (doesn't fit in int)?** Use long long; same algorithm.
- **What if the set of "allowed" primes is huge?** Trial division by all of them becomes slow; use different factorization techniques.
