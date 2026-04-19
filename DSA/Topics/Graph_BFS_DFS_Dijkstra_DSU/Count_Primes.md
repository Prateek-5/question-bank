# Count Primes

**Problem Link:**
https://leetcode.com/problems/count-primes/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: What's the Ask?

Given an integer n, count the number of primes **strictly less than n**. That is, count primes in the range `[2, n-1]`.

Examples:
- n = 10: primes < 10 are 2, 3, 5, 7. Count = **4**.
- n = 0 or n = 1: no primes < 1. Count = 0.
- n = 2: no primes < 2. Count = 0.
- n = 3: 2 is prime. Count = 1.

----------------------------------------

## Step 2: Naïve Approach

For each integer from 2 to n-1, check if it's prime. Primality check by trial division up to sqrt: for i, check divisibility by 2, 3, ..., up to sqrt(i).

```
count = 0
for i in 2..n-1:
    if is_prime(i): count++
return count
```

Each primality check: O(√i). Sum over i up to n: O(n√n). For n = 10^6, that's about 10^9 — slow.

Can we be smarter by checking many numbers at once?

----------------------------------------

## Step 3: The Sieve of Eratosthenes Idea

Instead of testing each number independently, **mark composites**. Start with all numbers 2..n-1 as "possibly prime." Then:

- 2 is prime. Mark all multiples of 2 greater than 2 as composite: 4, 6, 8, ...
- 3 is prime (still unmarked). Mark multiples: 6, 9, 12, ... (6 already marked, but that's fine).
- 4 is marked — skip.
- 5 is unmarked — prime. Mark 10, 15, 20, ...
- 6 marked — skip.
- 7 unmarked — prime. Mark 14, 21, ...
- ...

When we reach some number not yet marked, it must be prime — because if it had a divisor < itself, that divisor would be prime (or have prime factors) and we'd have already marked the number through that prime's multiples.

After this process, count the unmarked numbers in [2, n-1] — those are the primes.

This is the classical **Sieve of Eratosthenes**.

----------------------------------------

## Step 4: Why We Only Need to Sieve Up to sqrt(n)

Here's an optimization. We only need to mark multiples starting from primes up to sqrt(n). Why?

If `p * q = n` where p ≤ q, then `p ≤ sqrt(n)`. So every composite number ≤ n has a prime factor ≤ sqrt(n). Marking multiples of every prime up to sqrt(n) covers all composites.

For primes p > sqrt(n), their smallest un-marked multiple is p² > n, which is out of range. Nothing new to mark.

So the outer loop goes i = 2, 3, 5, ..., up to sqrt(n).

----------------------------------------

## Step 5: Further: Start Marking From p²

Another optimization. When we find a prime p, its multiples are 2p, 3p, 4p, ..., (p-1)p, p², (p+1)p, ...

The multiples 2p, 3p, ..., (p-1)p are all `p * k` for k < p. Each such k has a prime factor ≤ k < p — so these multiples were already marked when processing smaller primes.

So we only need to start marking from **p²**.

For p = 5, don't mark 10 (5·2), 15 (5·3), 20 (5·4) — those are already marked. Start from 25 (5²).

This slightly reduces the constant factor.

----------------------------------------

## Step 6: The Algorithm

```
if n <= 2: return 0

isComposite = [False] * n   # indices 0..n-1
count = 0

for i in 2..n-1:
    if not isComposite[i]:
        count++
        if i * i < n:     # only sieve when p² fits
            for j in i*i, i*i + i, i*i + 2i, ..., up to n-1:
                isComposite[j] = True

return count
```

Two loops: outer for primes, inner for marking their multiples starting from p².

----------------------------------------

## Step 7: Trace for n = 20

```
isComposite = all False. count = 0.

i=2: not marked. count=1. i²=4 < 20. Mark 4, 6, 8, 10, 12, 14, 16, 18.
i=3: not marked. count=2. i²=9 < 20. Mark 9, 12, 15, 18.
i=4: marked. Skip. (but count still increments? Wait, we don't enter the "prime" branch, so no.)
Actually let me re-read my code. `if not isComposite[i]: count++; ... else: skip`. So:
i=4: marked. Do nothing.
i=5: not marked. count=3. i²=25 >= 20. No marking needed.
i=6: marked. Skip.
i=7: not marked. count=4. i²=49 >= 20. No marking.
i=8: marked. Skip.
i=9: marked. Skip.
i=10: marked.
i=11: not marked. count=5. i²=121 >= 20. No marking.
i=12: marked.
i=13: not marked. count=6. No marking.
i=14: marked.
i=15: marked.
i=16: marked.
i=17: not marked. count=7. No marking.
i=18: marked.
i=19: not marked. count=8. No marking.
```

Primes < 20: 2, 3, 5, 7, 11, 13, 17, 19. Count = **8**. ✓

----------------------------------------

## Step 8: Why It's Fast

The inner "mark multiples" loop runs `n/p` times for each prime p. Summing over primes p:
```
n/2 + n/3 + n/5 + n/7 + ... + n/p_max
```

Mathematical fact: the sum of reciprocals of primes up to N is approximately `ln(ln(N))`. So total inner work is `O(n · ln(ln(n)))`.

That's much faster than O(n · sqrt(n)). For n = 10^6, it's about 10^6 · ~3 = 3 million ops. Blazing fast.

----------------------------------------

## Step 9: Naming

This is the **Sieve of Eratosthenes** — attributed to Eratosthenes of Cyrene (276-194 BCE). One of the oldest algorithms still in regular use, and still the standard way to enumerate primes up to a moderate bound.

Variants:
- **Linear sieve** / **Euler's sieve**: O(n), eliminates redundant markings. Each composite marked exactly once by its smallest prime factor.
- **Segmented sieve**: for enormous n where the array doesn't fit in memory.
- **Wheel factorization**: skips multiples of small primes entirely.

For interview scope, Eratosthenes is fine.

----------------------------------------

## Step 10: Complexity

Time: **O(n log log n)**.
Space: **O(n)** for the isComposite array.

----------------------------------------

## Step 11: C++ Implementation

```cpp
int countPrimes(int n) {
    if (n <= 2) return 0;
    vector<bool> isComposite(n, false);
    int count = 0;
    for (int i = 2; i < n; ++i) {
        if (!isComposite[i]) {
            count++;
            if ((long long)i * i < n) {
                for (int j = i * i; j < n; j += i) {
                    isComposite[j] = true;
                }
            }
        }
    }
    return count;
}
```

Implementation notes:
- Cast to `long long` for `i * i` to avoid overflow when i ~ sqrt(INT_MAX).
- Use `vector<bool>` — compact bit representation.
- Start the inner loop from `i * i`, not `2 * i`, to skip already-marked multiples.

----------------------------------------

## Step 12: Follow-up Questions

- **Enumerate the primes (not just count).** Modify to collect unmarked indices.
- **Smallest prime factor of every number up to n.** Variant sieve: when marking `j = i * k`, record `smallestPrimeFactor[j] = i` (if not already set).
- **Primes in a range [L, R] for large L, R.** Segmented sieve: precompute primes up to sqrt(R), then sieve the range [L, R] block by block.
- **Is a given number n prime (single query, very large n)?** Miller-Rabin primality test — probabilistic O(k log³ n).
- **Count primes up to 10^12.** Far beyond sieve memory. Use Meissel-Mertens or Lucy_Hedgehog's algorithm, O(n^(2/3)).
- **Why not check primality by n mod 2, 3, 5, ... (Wilson's Theorem, etc.)?** Those are single-number tests, not batch. Sieve amortizes work across many numbers.
