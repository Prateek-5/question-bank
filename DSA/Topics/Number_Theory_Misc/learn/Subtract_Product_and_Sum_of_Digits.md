# Subtract Product and Sum of Digits — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Subtract_Product_and_Sum_of_Digits.md`](../Subtract_Product_and_Sum_of_Digits.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/subtract-the-product-and-sum-of-digits-of-an-integer/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~8 minutes. **The lesson: single-pass digit extraction with two accumulators (product starting at 1, sum at 0). Return product - sum.**

**Map of this file (6 sections):**

1. Read the problem
2. The two-accumulator loop
3. Identity values (1 for product, 0 for sum)
4. Code
5. Trace it
6. The shape — multi-accumulator digit pass

---

## 1. Read the problem

Given positive integer n, return `product_of_digits(n) - sum_of_digits(n)`.

**Examples:**

- n = 234 → digits 2, 3, 4. Product = 24, Sum = 9, Result = **15**.
- n = 4421 → Product = 32, Sum = 11, Result = **21**.

---

## 2. The two-accumulator loop

Single digit-extraction loop; maintain BOTH accumulators in lockstep:

```
product = 1
sum = 0
while n > 0:
    d = n % 10
    product *= d
    sum += d
    n /= 10
return product - sum
```

O(log n) time, O(1) space.

---

## 3. Identity values (1 for product, 0 for sum)

> **Mini-refresher: each operation has an IDENTITY value to start from.**
>
> - Sum: identity = 0. `0 + d` doesn't change d.
> - Product: identity = 1. `1 * d` doesn't change d.
> - Min: identity = +∞.
> - Max: identity = -∞.
>
> Initialize accumulators to the identity to handle the "empty" case (n with zero digits processed so far) correctly.

If you initialize product to 0, EVERY product would be 0 — bug.

---

## 4. Code

**C++:**

```cpp
int subtractProductAndSum(int n) {
    int product = 1;
    int sum = 0;
    while (n > 0) {
        int d = n % 10;
        product *= d;
        sum += d;
        n /= 10;
    }
    return product - sum;
}
```

---

## 5. Trace it

n = 234:
- d = 4, product = 4, sum = 4, n = 23.
- d = 3, product = 12, sum = 7, n = 2.
- d = 2, product = 24, sum = 9, n = 0.
- Return 24 - 9 = **15**.  ✓

n = 4421:
- 1 → product=1, sum=1.
- 2 → 2, 3.
- 4 → 8, 7.
- 4 → 32, 11.
- Return 32 - 11 = **21**.  ✓

---

## 6. The shape — multi-accumulator digit pass

The pattern: **digit-extraction loop with MULTIPLE accumulators tracked in parallel.**

| Problem | Accumulators |
|---|---|
| **This problem** | product (×, init 1), sum (+, init 0) |
| Digit count, digit sum, digit max | count (+), sum (+), max (init -∞) |
| Reverse number | result (×10 + d), no init |
| Check palindrome number | reversed half + comparator |
| Armstrong number | sum of d^k (init 0) |

**Pattern to internalize:**

> "Digit problems often need MULTIPLE summary stats. One pass, multiple accumulators, each initialized to its operation's IDENTITY value."

---

> **Self-check — the question to ask next time.**
>
> When digits need to be processed for several stats:
>
> > **"One pass via `% 10` / `/ 10`. Multiple accumulators in parallel. Initialize each to operation's identity (0 sum, 1 product, ±∞ min/max)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Subtract_Product_and_Sum_of_Digits.md`](../Subtract_Product_and_Sum_of_Digits.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Self_Dividing_Numbers.md`](./Self_Dividing_Numbers.md), [`Add_Digits.md`](../../Math/learn/Add_Digits.md).
  - Coming next: [`Number_of_Good_Pairs.md`](./Number_of_Good_Pairs.md).
