# Ugly Number — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Ugly_Number.md`](../Ugly_Number.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/ugly-number/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/ugly-number/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **The lesson: strip factors of 2, 3, 5. If what remains is 1, n was UGLY (all prime factors in {2, 3, 5}). Else, NOT ugly.**

**Map of this file (7 sections):**

1. Read the problem
2. The strip-and-check idea
3. Edge cases
4. Code
5. Trace it
6. Common pitfalls
7. The shape — prime-factor filtering

---

## 1. Read the problem

Return true iff `n` is a POSITIVE integer whose ONLY prime factors are 2, 3, or 5.

**Examples:** 6 = 2·3 → true. 8 = 2³ → true. 14 = 2·7 → false. 1 → true (no prime factors, vacuously). 0, -1 → false (not positive).

---

## 2. The strip-and-check idea

> **Mini-refresher: divide out 2, 3, 5 as long as possible.**
>
> ```
> for p in [2, 3, 5]:
>     while n % p == 0:
>         n //= p
> return n == 1
> ```
>
> If n's prime factors are ALL in {2, 3, 5}, repeatedly dividing strips them all → leaves 1. Else, leaves a value > 1 with a different prime factor → false.

---

## 3. Edge cases

- **n ≤ 0:** not positive → false.
- **n = 1:** no prime factors → vacuously true.
- **n is a prime > 5 (7, 11, 13, ...):** division leaves it unchanged → false.
- **n is HUGE but ugly (e.g., 2^30):** strips down to 1 quickly.

---

## 4. Code

**C++:**

```cpp
bool isUgly(int n) {
    if (n <= 0) return false;
    for (int p : {2, 3, 5}) {
        while (n % p == 0) n /= p;
    }
    return n == 1;
}
```

**Python:**

```python
def isUgly(n):
    if n <= 0:
        return False
    for p in (2, 3, 5):
        while n % p == 0:
            n //= p
    return n == 1
```

Complexity: **O(log n)** time (each division halves or more), **O(1)** space.

---

## 5. Trace it

- n = 6: /2 → 3, /3 → 1. Return **true**. ✓
- n = 14: /2 → 7. 7 not divisible by 2, 3, 5. Return **false**. ✓
- n = 30: /2 → 15, /3 → 5, /5 → 1. Return **true**. ✓
- n = 0: return **false** (positivity check). ✓
- n = 1: no divisions; return **true**. ✓

---

## 6. Common pitfalls

1. **Missing the n ≤ 0 check.** 0 and negatives are NOT ugly.
2. **Hardcoding ugly numbers in a list.** Doesn't scale; algorithm is fast.
3. **Order of primes affecting result.** It doesn't — divisions commute. Any order of 2, 3, 5 is fine.
4. **Confusing with Ugly Number II.** This is the BOOLEAN check. Ugly Number II asks for the n-th ugly number — different (uses heap or 3-pointer DP).
5. **Treating 1 as not ugly.** By convention, 1 IS ugly (vacuously).

---

## 7. The shape — prime-factor filtering

The pattern: **strip allowed primes; check if result is 1.**

| Problem | Allowed primes |
|---|---|
| **This problem** | {2, 3, 5} |
| Power of 2 | {2} (or `n & (n-1) == 0` trick) |
| Power of 3 | {3} |
| Super Ugly Number (LC 313) | arbitrary set |
| Is Smooth Number | small prime set |

**Pattern to internalize:**

> "To check if n's prime factors are confined to a set S, repeatedly divide n by each p ∈ S. If result is 1, yes; else no."

---

> **Self-check — the question to ask next time.**
>
> When asked if all prime factors of n lie in a given set:
>
> > **"Loop each allowed prime p; while n % p == 0, n /= p. Check n == 1 at end."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Ugly_Number.md`](../Ugly_Number.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Pow_x_n.md`](./Pow_x_n.md), [`Total_Number_of_Divisors_of_a_Given_Number.md`](./Total_Number_of_Divisors_of_a_Given_Number.md).
  - Coming next: [`Teemo_Attacking.md`](./Teemo_Attacking.md), [`Rectangle_Area.md`](./Rectangle_Area.md), [`Subsequence_of_Size_K_With_Largest_Sum.md`](./Subsequence_of_Size_K_With_Largest_Sum.md).
