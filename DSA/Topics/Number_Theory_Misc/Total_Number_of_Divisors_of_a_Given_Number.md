# Total Number of Divisors of a Given Number

**Problem Link:**
<a href="https://www.geeksforgeeks.org/dsa/total-number-divisors-given-number/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/dsa/total-number-divisors-given-number/</a>

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: Define the Task

Given a positive integer n, count how many **positive divisors** it has. A divisor of n is any integer d ≥ 1 such that `n mod d == 0`.

Example: n = 12. Divisors: 1, 2, 3, 4, 6, 12. Count = **6**.
Example: n = 1. Divisors: just 1. Count = 1.
Example: n = 17 (prime). Divisors: 1, 17. Count = 2.
Example: n = 100. Divisors: 1, 2, 4, 5, 10, 20, 25, 50, 100. Count = **9**.

----------------------------------------

## Step 2: Naive Approach — Try Every Integer

Loop i from 1 to n. If `n % i == 0`, count it.

O(n). Fine for n ≤ 10^6, slow for n ≈ 10^12.

Can we be smarter?

----------------------------------------

## Step 3: Divisors Come in Pairs

Observation: if `d` is a divisor of n, then so is `n / d`. They pair up.

For n = 12:
- 1 × 12 = 12.
- 2 × 6 = 12.
- 3 × 4 = 12.

Three pairs → 6 divisors. Every divisor pairs with its "complement."

**Key insight:** in each pair (d, n/d), the smaller one is ≤ √n. So if we only scan `i` from 1 to √n and look for divisors, we find the smaller element of each pair — and pair it with `n/i` to get the larger.

Total work: O(√n). For n = 10^12, that's 10^6 operations — fast.

----------------------------------------

## Step 4: Handle Perfect Squares

For n = 36: √36 = 6. At i = 6, we have `n / i = 6` — same number. Counting (6, 6) as a pair would double-count.

So when `i * i == n`, count only once. Otherwise (i and n/i distinct), count both.

----------------------------------------

## Step 5: Algorithm

```
count = 0
for i from 1 to √n:
    if n % i == 0:
        if i * i == n:
            count += 1          # perfect-square pair, one element
        else:
            count += 2          # pair (i, n/i), both distinct
return count
```

----------------------------------------

## Step 6: Trace on n = 36

√36 = 6. Iterate i = 1..6.

- i = 1: 36 % 1 = 0. 1 ≠ 36. count += 2. count = 2. (Found divisors 1, 36.)
- i = 2: 36 % 2 = 0. 2 ≠ 18. count += 2. count = 4. (Found 2, 18.)
- i = 3: 36 % 3 = 0. 3 ≠ 12. count += 2. count = 6. (Found 3, 12.)
- i = 4: 36 % 4 = 0. 4 ≠ 9. count += 2. count = 8. (Found 4, 9.)
- i = 5: 36 % 5 = 1 ≠ 0. skip.
- i = 6: 36 % 6 = 0. 6 × 6 = 36. count += 1. count = 9. (Found 6 once.)

Total: **9**. ✓

Trace on n = 12: √12 ≈ 3.46, iterate i = 1..3.
- i = 1: 12 % 1 = 0. 1 ≠ 12. count = 2.
- i = 2: 12 % 2 = 0. 2 ≠ 6. count = 4.
- i = 3: 12 % 3 = 0. 3 ≠ 4. count = 6.
- (i = 4 stops loop since 4² > 12? Depends on loop condition; we use `i ≤ √n` ≈ 3.46, so stop at 3.)

Total: **6**. ✓

----------------------------------------

## Step 7: Alternative — Prime Factorization Formula

If n's prime factorization is `n = p1^a1 · p2^a2 · ... · pk^ak`, then the number of divisors is:

```
(a1 + 1) · (a2 + 1) · ... · (ak + 1)
```

Why? A divisor is `p1^b1 · p2^b2 · ...` where `0 ≤ bi ≤ ai`. Each bi has `ai + 1` choices, and all combinations give distinct divisors.

Example: n = 36 = 2² · 3². Divisors count = (2+1)(2+1) = 9. ✓

To use this, factor n first (O(√n)) then multiply. Same asymptotic complexity, but elegant for analysis.

----------------------------------------

## Step 8: Name It

**Trial division with pairing**. The square-root pairing trick is the universal speed-up for any "enumerate divisors" problem.

Applications:
- Count divisors (this problem).
- Sum of divisors.
- Check for perfect number / abundant number.
- Find smallest proper divisor.

Related:
- **Sieve of divisor counts**: for counting divisors of *all* numbers up to N, use a sieve in O(N log N).
- **Euler's totient**: uses the same prime factorization framework.

----------------------------------------

## Step 9: Complexity

Time: **O(√n)** per query.
Space: **O(1)**.

For n up to 10^12 or so, comfortably fast.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int countDivisors(long long n) {
    int count = 0;
    for (long long i = 1; i * i <= n; ++i) {
        if (n % i == 0) {
            if (i * i == n) count += 1;
            else count += 2;
        }
    }
    return count;
}
```

Two critical details:
1. Loop condition `i * i <= n`, not `i <= sqrt(n)` — avoids floating-point issues for large n.
2. Handle the perfect-square case (`i * i == n`) separately to avoid double-counting.

----------------------------------------

## Step 11: Follow-up Questions

- **Sum of divisors.** Same loop: when i divides n, add `i + n/i` (or just `i` for perfect square).
- **Count of divisors for all numbers 1..N.** Sieve: for each i, iterate its multiples and increment their count. O(N log N).
- **Very large n (10^18).** Trial division up to √n = 10^9 is too slow. Use Pollard's rho factorization.
- **Count odd divisors only.** Same loop, but skip when i (or n/i) is even.
- **Why `i * i <= n` not `i <= sqrt(n)`?** `sqrt` returns a double; for n near long-long max, rounding can cause off-by-one. Integer comparison is exact.
- **Relationship to divisor function τ(n).** Yes — τ(n) is this count. Multiplicative, meaning `τ(a·b) = τ(a) · τ(b)` when gcd(a, b) = 1.
