# Total Number of Divisors of a Given Number — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Total_Number_of_Divisors_of_a_Given_Number.md`](../Total_Number_of_Divisors_of_a_Given_Number.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://www.geeksforgeeks.org/dsa/total-number-divisors-given-number/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/dsa/total-number-divisors-given-number/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The lesson: divisors come in PAIRS `(d, n/d)`. Loop i from 1 to √n; each divisor i gives a paired divisor n/i. Handle perfect squares (`i == n/i`) to avoid double-counting. O(√n).**

**Map of this file (7 sections):**

1. Read the problem
2. The pairing insight
3. Perfect-square edge case
4. Code
5. Trace it
6. Common pitfalls
7. The shape — trial division with √n bound

---

## 1. Read the problem

Given positive integer `n`, count the number of positive integers that divide it.

**Examples:** n = 12 → divisors {1, 2, 3, 4, 6, 12} → **6**. n = 36 → **9**. n = 17 (prime) → 2.

---

## 2. The pairing insight

> **Mini-refresher: every divisor `d ≤ √n` pairs with `n/d ≥ √n`.**
>
> Loop `i` from 1 to √n. If `n % i == 0`:
> - `i` is a divisor.
> - `n/i` is ALSO a divisor (and it's ≥ √n).
> - Count BOTH — unless they're equal (handled below).
>
> O(√n) instead of O(n) for the naive scan.

---

## 3. Perfect-square edge case

When `i² = n` (e.g., n=36, i=6), then `i = n/i`. Counting both would double-count the same divisor. Add only 1.

---

## 4. Code

**C++:**

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

Complexity: **O(√n)** time, **O(1)** space.

---

## 5. Trace it

n = 36 (√36 = 6):

- i=1: 36 % 1 = 0, 1 ≠ 36 → +2 (divisors 1, 36). count=2.
- i=2: 36 % 2 = 0, 2 ≠ 18 → +2. count=4.
- i=3: 36 % 3 = 0, 3 ≠ 12 → +2. count=6.
- i=4: 36 % 4 = 0, 4 ≠ 9 → +2. count=8.
- i=5: 36 % 5 ≠ 0.
- i=6: 36 % 6 = 0, 6 = 6 (perfect square) → +1. count=**9**.  ✓

---

## 6. Common pitfalls

1. **Looping to n instead of √n.** O(n) is unnecessary.
2. **Using `i <= sqrt(n)` with double sqrt.** Off-by-one rounding issues for large n. Use `i * i <= n` (integer comparison).
3. **Overflow on `i * i` for large n.** Cast to long long.
4. **Forgetting the perfect-square case.** Doubles every divisor of a perfect square (wrong by +1).

---

## 7. The shape — trial division with √n bound

The pattern: **for divisor / factor enumeration, the √n bound captures all divisor pairs.**

| Problem | Use |
|---|---|
| **This problem** | count divisors |
| Sum of divisors | sum i + n/i (or just i for square) |
| Four Divisors | count divisors per number, sum if == 4 |
| Aliquot sum / Perfect numbers | sum of proper divisors |
| Prime check | "no divisors in (1, √n)" |
| Find smallest factor | first i > 1 with n % i == 0 |

**Pattern to internalize:**

> "Divisor enumeration: loop i from 1 to √n. Each match gives TWO divisors (i and n/i) — or ONE if perfect square. O(√n)."

---

> **Self-check — the question to ask next time.**
>
> When you need divisors / factors of n:
>
> > **"Loop i with i*i <= n. Each divisor i gives n/i. Watch the perfect-square case. O(√n)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Total_Number_of_Divisors_of_a_Given_Number.md`](../Total_Number_of_Divisors_of_a_Given_Number.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Open_Doors.md`](./Number_of_Open_Doors.md).
  - Coming next: [`Four_Divisors.md`](./Four_Divisors.md), [`Largest_Multiple_of_Three.md`](./Largest_Multiple_of_Three.md).
