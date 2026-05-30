# Subtract Product and Sum of Digits

**Problem Link:**
<a href="https://leetcode.com/problems/subtract-the-product-and-sum-of-digits-of-an-integer/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/subtract-the-product-and-sum-of-digits-of-an-integer/</a>

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: The Task

Given a positive integer n, compute:
- Product of its digits.
- Sum of its digits.

Return `product - sum`.

Example: n = 234.
- Digits: 2, 3, 4.
- Product: 2 * 3 * 4 = 24.
- Sum: 2 + 3 + 4 = 9.
- Result: 24 - 9 = 15.

Example: n = 4421.
- Digits: 4, 4, 2, 1.
- Product: 4 * 4 * 2 * 1 = 32.
- Sum: 4 + 4 + 2 + 1 = 11.
- Result: 32 - 11 = 21.

----------------------------------------

## Step 2: Digit Extraction

Standard pattern: repeatedly take `n % 10` (rightmost digit), then `n /= 10` (drop it).

```
product = 1
sum = 0
while n > 0:
    d = n % 10
    product *= d
    sum += d
    n //= 10
return product - sum
```

O(log n) — number of digits.

Note: `product` starts at 1 (multiplicative identity); `sum` starts at 0 (additive identity).

----------------------------------------

## Step 3: Trace

n = 234.
- n = 234: d = 4. product = 4. sum = 4. n = 23.
- n = 23: d = 3. product = 12. sum = 7. n = 2.
- n = 2: d = 2. product = 24. sum = 9. n = 0.
- Loop ends. Return 24 - 9 = 15. ✓

n = 4421.
- d = 1. prod = 1, sum = 1. n = 442.
- d = 2. prod = 2, sum = 3. n = 44.
- d = 4. prod = 8, sum = 7. n = 4.
- d = 4. prod = 32, sum = 11. n = 0.
- Return 32 - 11 = 21. ✓

----------------------------------------

## Step 4: Why Does Product - Sum Make Sense?

Just a combination of two common digit operations. No deep insight — the problem is a warm-up.

However, note: if any digit is 0, product becomes 0 immediately. That makes "product - sum" negative for most multi-digit numbers containing a 0.

E.g., n = 10: digits 1, 0. Product = 0. Sum = 1. Result = -1.

The subtraction doesn't have a clean mathematical property; it's just practice with digit manipulation.

----------------------------------------

## Step 5: Name It

**Digit manipulation via `% 10` and `/ 10`**. Along with digital root and digit sum, this is a foundational pattern for integer-digit problems.

Related:
- Subtract Product / Digit Count. 
- Number of matching digits.
- Find the maximum digit in n.
- Palindrome number check.

----------------------------------------

## Step 6: Complexity

Time: **O(log n)** — linear in digit count.
Space: **O(1)**.

----------------------------------------

## Step 7: C++ Implementation

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

Seven lines. Direct implementation of the spec.

----------------------------------------

## Step 8: Follow-up Questions

- **Product / sum of digits at even positions only.** Alternate extraction.
- **Handle negative n.** Usually the problem specifies positive; otherwise absolute-value first.
- **Product modulo a prime.** Apply modulus at each multiplication to avoid overflow.
- **Digits in a different base.** `n % b` and `n /= b`.
- **Stream digits from a string representation.** Parse chars.
- **Return product AND sum as a pair.** Return a struct or tuple instead of difference.
