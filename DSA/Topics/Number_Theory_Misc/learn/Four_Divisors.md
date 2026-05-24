# Four Divisors — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Four_Divisors.md`](../Four_Divisors.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/four-divisors/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The lesson: trial-divide each number, count + sum divisors as you go, early-exit if count exceeds 4. Numbers with exactly 4 divisors are EITHER `p³` (prime cubes) OR `p · q` (semiprimes with distinct primes).**

**Map of this file (7 sections):**

1. Read the problem
2. Per-number divisor enumeration
3. The early-exit trick
4. Structural classification
5. Code
6. Trace it
7. The shape — divisor-property filter

---

## 1. Read the problem

Given integer array `nums`, find all numbers with EXACTLY 4 divisors. Sum the divisors of those numbers. Return the grand total.

**Example:** `nums = [21, 4, 7]`.
- 21: divisors {1, 3, 7, 21} → 4 divisors, sum = 32.
- 4: divisors {1, 2, 4} → 3 divisors, skip.
- 7: divisors {1, 7} → 2 divisors, skip.

Result: **32**.

---

## 2. Per-number divisor enumeration

For each n: loop i from 1 to √n. For each match, count and accumulate.

```
count = 0, sum = 0
for i in 1..√n:
    if n % i == 0:
        count++; sum += i
        if i != n/i: count++; sum += n/i
        if count > 4: break and skip n
if count == 4: total += sum
```

O(√n) per number → O(m · √max_n) overall.

---

## 3. The early-exit trick

> **Mini-refresher: short-circuit when count exceeds 4.**
>
> If count grows past 4 mid-loop, we can stop early — this number won't qualify. Saves work on highly composite numbers.

---

## 4. Structural classification

Numbers with exactly 4 divisors have ONE of two forms:

> **Mini-refresher: 4-divisor structure.**
>
> 1. **p³** for a prime p — divisors {1, p, p², p³}.
> 2. **p · q** for distinct primes p, q — divisors {1, p, q, pq}.
>
> These are the ONLY shapes that produce exactly 4 divisors.

For interview purposes, trial division is fine — but knowing the structure is useful for optimizing or for related questions.

---

## 5. Code

**C++:**

```cpp
class Solution {
    int sumIfFourDivisors(int n) {
        int count = 0, sum = 0;
        for (int i = 1; (long long)i * i <= n; ++i) {
            if (n % i == 0) {
                count++; sum += i;
                if (i != n / i) {
                    count++; sum += n / i;
                }
                if (count > 4) return 0;
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

Complexity: **O(m · √max_n)** time, **O(1)** extra per number.

---

## 6. Trace it

`nums = [21, 4, 7]`:

n = 21 (√21 ≈ 4.58):
- i=1: 21 % 1 = 0. count=2, sum=22.
- i=2: 21 % 2 ≠ 0.
- i=3: 21 % 3 = 0. 3 ≠ 7. count=4, sum=32.
- i=4: 21 % 4 ≠ 0.
- Loop ends. count == 4 → return 32.

n = 4 (√4 = 2):
- i=1: count=2, sum=5.
- i=2: 4 % 2 = 0. 2 = 4/2 (perfect square). count=3, sum=7.
- count == 3, return 0.

n = 7 (√7 ≈ 2.6):
- i=1: count=2, sum=8.
- i=2: 7 % 2 ≠ 0.
- count == 2, return 0.

Total: 32 + 0 + 0 = **32**.  ✓

---

## 7. The shape — divisor-property filter

The pattern: **enumerate divisors per number, filter by a property of the divisor count or sum.**

| Problem | Property |
|---|---|
| **This problem** | exactly 4 divisors |
| Perfect Number | divisor sum equals 2n |
| Abundant / Deficient Numbers | divisor sum > / < 2n |
| Smallest Prime Divisor | first i > 1 dividing n |
| Aliquot Sequence | iterate proper-divisor sum |
| Aliquot sum problem variants | sums or counts |

**Pattern to internalize:**

> "Per-number divisor enumeration via trial division. EARLY-EXIT when the running count clearly disqualifies. O(√n) per number."

---

> **Self-check — the question to ask next time.**
>
> When filtering numbers by divisor property:
>
> > **"Trial divide each n up to √n. Accumulate count + sum + structural info. Early-exit if disqualified."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Four_Divisors.md`](../Four_Divisors.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Total_Number_of_Divisors_of_a_Given_Number.md`](./Total_Number_of_Divisors_of_a_Given_Number.md), [`Number_of_Open_Doors.md`](./Number_of_Open_Doors.md).
  - Coming next: [`Largest_Multiple_of_Three.md`](./Largest_Multiple_of_Three.md), [`Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md`](./Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md).
