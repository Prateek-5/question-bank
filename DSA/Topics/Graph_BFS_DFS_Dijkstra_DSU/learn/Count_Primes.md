# Count Primes — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Count_Primes.md`](../Count_Primes.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/count-primes/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: SIEVE OF ERATOSTHENES marks composites by their PRIME multiples — O(n log log n). Two optimizations: (1) only sieve up to sqrt(n); (2) start marking from p² (smaller multiples already marked).**

**Map of this file (9 sections):**

1. Read the problem
2. Naive primality (and its limit)
3. The sieve idea
4. Two optimizations: stop at √n, start at p²
5. Code
6. Trace it
7. Why it's O(n log log n)
8. Common pitfalls
9. The shape — bulk sieve enumeration

---

## 1. Read the problem

Given integer n, return the count of primes STRICTLY LESS THAN n. (i.e., primes in [2, n-1].)

**Examples:**

- n = 10 → primes {2, 3, 5, 7} → **4**.
- n = 0 or n = 1 or n = 2 → no primes < n → **0**.

---

## 2. Naive primality (and its limit)

```
for i in 2..n-1:
    if is_prime(i): count++
```

Per `is_prime(i)`: trial divide by 2..√i → O(√i). Total: O(n√n).

For n = 10^6 → 10^9 ops. Slow.

The waste: testing each number INDEPENDENTLY ignores that we've already learned which numbers ≤ i are prime.

---

## 3. The sieve idea

> **Mini-refresher: Sieve of Eratosthenes — mark composites in bulk.**
>
> Start with all 2..n-1 as "possibly prime." Walk through:
> - When you reach an UNMARKED i, it's prime (any smaller divisor would have marked it).
> - Mark all multiples of i (2i, 3i, ...) as composite.
>
> At the end, count the unmarked numbers.

Marking is the speedup: we mark each composite a few times (once per prime factor), instead of testing each number's primality independently.

---

## 4. Two optimizations: stop at √n, start at p²

> **Mini-refresher: two key optimizations.**
>
> 1. **Stop the outer loop at √n.** Every composite c ≤ n has a prime factor p ≤ √c ≤ √n. Marking multiples of primes up to √n covers all composites.
> 2. **Start the inner loop at p², not 2p.** Multiples 2p, 3p, ..., (p-1)p are already marked (they have smaller prime factors). Marking starts giving "new" composites at p².

Together these reduce constants substantially.

---

## 5. Code

**C++:**

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

**Python:**

```python
def countPrimes(n):
    if n <= 2:
        return 0
    is_composite = [False] * n
    count = 0
    for i in range(2, n):
        if not is_composite[i]:
            count += 1
            if i * i < n:
                for j in range(i * i, n, i):
                    is_composite[j] = True
    return count
```

Complexity: **O(n log log n)** time, **O(n)** space.

---

## 6. Trace it

**n = 20:**

```
is_composite all False.
i=2: unmarked, count=1. i²=4 < 20. Mark 4, 6, 8, 10, 12, 14, 16, 18.
i=3: unmarked, count=2. i²=9 < 20. Mark 9, 12, 15, 18.
i=4: marked. skip.
i=5: unmarked, count=3. i²=25 ≥ 20. No marking needed.
i=6: marked.
i=7: unmarked, count=4. i²=49 ≥ 20.
i=8: marked.
i=9: marked.
i=10: marked.
i=11: unmarked, count=5.
i=12: marked.
i=13: unmarked, count=6.
i=14: marked.
i=15: marked.
i=16: marked.
i=17: unmarked, count=7.
i=18: marked.
i=19: unmarked, count=8.

Return 8.  ✓ (Primes < 20: 2, 3, 5, 7, 11, 13, 17, 19.)
```

---

## 7. Why it's O(n log log n)

Inner loop runs n/p times per prime p. Total work = `n × (1/2 + 1/3 + 1/5 + 1/7 + ... + 1/p_max)`.

The sum of reciprocals of primes ≤ N grows as `ln(ln(N))` (a classical number-theory result). So total = O(n · log log n).

For n = 10^6: roughly 3 million operations — sub-second on commodity hardware.

---

## 8. Common pitfalls

1. **Off-by-one on the strict inequality.** Count primes < n (NOT ≤ n).
2. **Counting `1` as prime.** It's not. Outer loop starts at 2.
3. **`i * i` overflow.** Cast to `long long` (or use `i ≤ (n - 1) / i` form).
4. **Inner loop starting at 2 * i instead of i * i.** Correct but does redundant work.
5. **Using `vector<int>` instead of `vector<bool>`.** Both work, but `vector<bool>` is compact (1 bit per entry).
6. **Returning 0 for n=2 incorrectly:** primes < 2 is the empty set, so 0 is correct.

---

## 9. The shape — bulk sieve enumeration

The pattern: **trade independent per-element tests for ONE bulk pass.**

| Problem | Sieve idea |
|---|---|
| **This problem** | mark multiples of primes |
| Smallest Prime Factor of every number | record smallest prime factor when marking |
| Primes in a range [L, R] (large L, R) | segmented sieve |
| Möbius function | sieve-based number-theoretic function |
| Multiplicative function tabulation | Euler sieve (linear) |

**Pattern to internalize:**

> "When you need to test a property for MANY numbers in a range and the property has structure (divisibility, factorization), SIEVE instead of testing one by one. O(n log log n) vs O(n √n)."

---

> **Self-check — the question to ask next time.**
>
> When you need primes/factors up to n, ask:
>
> > **"Sieve of Eratosthenes — O(n log log n). Mark composites starting from p². Stop the outer loop at √n."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Count_Primes.md`](../Count_Primes.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md`](./Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md), [`Minimum_Weight_Cycle.md`](./Minimum_Weight_Cycle.md).
  - Number-theory related: [`Find_GCD_of_Array.md`](../../Math/learn/Find_GCD_of_Array.md).
