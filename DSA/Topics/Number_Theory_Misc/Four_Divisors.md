# Four Divisors

**Problem Link:**
<a href="https://leetcode.com/problems/four-divisors/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/four-divisors/</a>

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: Understand the Problem

Given an integer array `nums`, find all numbers in nums that have **exactly four divisors**. Sum the divisors of those numbers. Return the grand total.

Example: `nums = [21, 4, 7]`.
- 21: divisors are 1, 3, 7, 21. Four divisors. Sum = 32.
- 4: divisors are 1, 2, 4. Three. Exclude.
- 7: divisors are 1, 7. Two. Exclude.

Total: 32.

----------------------------------------

## Step 2: How to Count Divisors Efficiently

For each number n, find all divisors by trial division up to sqrt(n):
- For each i from 1 to sqrt(n), if n % i == 0:
  - i is a divisor.
  - n / i is also a divisor.
  - If i ≠ n / i, they're two distinct divisors.

If we only care about **exactly four divisors**, we can short-circuit: stop checking as soon as we exceed 4 divisors.

```
def sumIfFourDivisors(n):
    divisors = []
    for i in 1..sqrt(n):
        if n % i == 0:
            divisors.append(i)
            if i != n // i: divisors.append(n // i)
            if len(divisors) > 4: return 0
    if len(divisors) == 4: return sum(divisors)
    return 0
```

O(sqrt(n)) per number. For nums of size m with numbers up to N, total: O(m · sqrt(N)).

----------------------------------------

## Step 3: What Numbers Have Exactly Four Divisors?

Interesting number-theory observation:

A positive integer's divisor count depends on its prime factorization. If n = p^a · q^b · ..., then divisor count = (a+1)(b+1)... 

To have exactly 4 divisors:
- n = p³ for a prime p (divisors: 1, p, p², p³). Four divisors.
- n = p · q for distinct primes p and q (divisors: 1, p, q, pq). Four divisors.

These are the only two cases.

You could use this to short-circuit: check if n is p³ or pq.

But the direct trial-division approach is simpler and fast enough for typical constraints.

----------------------------------------

## Step 4: Trace on `[21, 4, 7]`

**n = 21:**
- i = 1: 21 % 1 = 0. Divisors: 1, 21. [1, 21].
- i = 2: 21 % 2 ≠ 0.
- i = 3: 21 % 3 = 0. Divisors: 3, 7. [1, 21, 3, 7].
- i = 4: 21 % 4 ≠ 0.
- i = 5 > sqrt(21) ≈ 4.58. Stop.
- 4 divisors. Sum = 1 + 21 + 3 + 7 = 32.

**n = 4:**
- i = 1: 4 % 1 = 0. Divisors: 1, 4. [1, 4].
- i = 2: 4 % 2 = 0. 4 / 2 = 2 == i, so don't add twice. [1, 4, 2].
- i = 3 > sqrt(4) = 2. Stop.
- 3 divisors. Not 4. Return 0.

**n = 7:**
- i = 1: 7 % 1 = 0. [1, 7].
- i = 2: 7 % 2 ≠ 0.
- i = 3 > sqrt(7) ≈ 2.65. Stop.
- 2 divisors. Return 0.

Total: 32 + 0 + 0 = **32**. ✓

----------------------------------------

## Step 5: Why sqrt(n) Bound Is Sufficient

Divisors come in pairs (d, n/d) with d ≤ sqrt(n) ≤ n/d. So iterating i up to sqrt(n) finds all pairs. The edge case d = sqrt(n) (when n is a perfect square) is handled by checking `i != n / i` before counting twice.

So trial division up to sqrt(n) is both correct and efficient.

----------------------------------------

## Step 6: Name It

**Divisor enumeration via trial division.** Fundamental number-theory technique. Used in:
- Counting divisors.
- Summing divisors (sigma function).
- Perfect number checks.
- Prime testing (up to sqrt).
- Factorization (extending to prime factors).

For counting, O(sqrt(n)) trial division is standard. For very large n (cryptography-scale), use Miller-Rabin primality + Pollard's rho factorization.

----------------------------------------

## Step 7: Complexity

Time: **O(m · sqrt(max_n))**. For m = 10^4 and max_n = 10^5, that's about 10^6 · 316 ≈ 3 × 10^6 ops — fast.

Space: O(1) extra per number (we can sum divisors on the fly instead of storing them).

----------------------------------------

## Step 8: C++ Implementation

```cpp
class Solution {
    int sumIfFourDivisors(int n) {
        int count = 0, sum = 0;
        for (int i = 1; (long long)i * i <= n; ++i) {
            if (n % i == 0) {
                count++;
                sum += i;
                if (i != n / i) {
                    count++;
                    sum += n / i;
                }
                if (count > 4) return 0;   // early exit
            }
        }
        return count == 4 ? sum : 0;
    }

public:
    int sumFourDivisors(vector<int>& nums) {
        int total = 0;
        for (int n : nums) total += sumIfFourDivisors(n);
        return total;
    }
};
```

The early exit (`count > 4 return 0`) skips numbers with many divisors quickly — useful optimization for composite-heavy inputs.

`(long long)i * i <= n` avoids overflow for large n (~10^9).

----------------------------------------

## Step 9: Follow-up Questions

- **Sum divisors for numbers with **exactly k** divisors.** Same template, different count check.
- **Count numbers up to N with exactly 4 divisors.** Use the p³ or pq characterization + sieve of primes.
- **Divisor sigma function σ(n).** Sum of all divisors. Same enumeration.
- **Aliquot sum (sum of proper divisors, excluding n).** Skip n in the final sum.
- **Perfect numbers (σ(n) = 2n).** Check σ(n) == 2n.
- **Find the smallest number ≤ N with exactly k divisors.** Brute force or smarter search with factorization structure.
