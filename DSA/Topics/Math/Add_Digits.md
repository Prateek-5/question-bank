# Add Digits

**Problem Link:**
<a href="https://leetcode.com/problems/add-digits/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/add-digits/</a>

**Topic:**
Math

----------------------------------------

## Step 1: Understand the Process

Given a non-negative integer `num`, repeatedly sum its digits until only one digit remains. Return that digit.

Example: num = 38.
- 3 + 8 = 11. Two digits still.
- 1 + 1 = 2. One digit. Return 2.

Example: num = 0. Return 0.

This is the concept of **digital root** in number theory.

----------------------------------------

## Step 2: Simulate Straightforwardly

A direct implementation:

```
while num >= 10:
    sum = 0
    temp = num
    while temp > 0:
        sum += temp % 10
        temp /= 10
    num = sum
return num
```

Each inner loop sums digits. Each outer iteration replaces num with its digit sum. Eventually, sum drops below 10.

For num = 1e9, digits ≤ 10. After one iteration, num ≤ 81 (max sum of 9 nines for 10-digit). Then after 2-3 iterations, < 10. Very fast.

O(log num) per iteration, O(1) outer iterations for practical input sizes.

----------------------------------------

## Step 3: O(1) Closed-Form Solution

There's a stunning mathematical shortcut. The **digital root** has a closed form:

```
digital_root(n) = 0 if n == 0
               = 9 if n > 0 and n % 9 == 0
               = n % 9 otherwise
```

Or equivalently:
```
digital_root(n) = 1 + (n - 1) % 9 for n > 0
```

Let me verify:
- n = 38. (38 - 1) % 9 = 37 % 9 = 1. +1 = 2. ✓
- n = 0. Return 0 (special case).
- n = 9. (9 - 1) % 9 = 8. +1 = 9. ✓
- n = 18. (18 - 1) % 9 = 17 % 9 = 8. +1 = 9. ✓
- n = 27. (27 - 1) % 9 = 26 % 9 = 8. +1 = 9. ✓

All consistent with digital root values.

----------------------------------------

## Step 4: Why Does Modulo 9 Give the Digital Root?

This is a lovely fact from number theory.

**Claim:** for any non-negative integer n, `n ≡ sum_of_digits(n) (mod 9)`.

**Proof sketch:** in base 10, `10 ≡ 1 (mod 9)`. So `10^k ≡ 1^k = 1 (mod 9)`. Any number `n = a_k · 10^k + ... + a_0 · 10^0` has `n ≡ a_k + ... + a_0 (mod 9)` — its digit sum.

So when we repeatedly take digit sums, we're preserving `n mod 9`. Eventually we reach a single digit, which is:
- `0` if n ≡ 0 (mod 9) and n > 0: but a single digit that's 0 means the result is 0 only if we start at 0. Otherwise, the result is `9`.
- `n mod 9` if n ≢ 0 (mod 9).

The formula `1 + (n - 1) % 9` for n > 0 handles both cases:
- For n ≡ 0 (mod 9): (n - 1) % 9 = 8. Result = 9. ✓
- For n ≡ r (mod 9), r ≠ 0: (n - 1) % 9 = r - 1. Result = r. ✓

----------------------------------------

## Step 5: The Beauty of the Closed Form

This is one of my favorite "look mom, no loop" results. A problem that looks algorithmic (iterative digit summing) has a O(1) formula thanks to a number-theoretic observation.

It's the kind of trick that, once you know it, feels obvious — but recognizing it in the first place requires knowing that `10 ≡ 1 (mod 9)`.

Interview-wise, show both: the iterative approach demonstrates you can code the problem; the closed form demonstrates you understand the math.

----------------------------------------

## Step 6: Trace Both Approaches

**Simulation for num = 99:**
- Digits: 9 + 9 = 18.
- Digits of 18: 1 + 8 = 9. Single digit. Return 9.

**Formula:** 99 > 0, 99 % 9 = 0. Return 9. ✓

**Simulation for num = 1234:**
- 1 + 2 + 3 + 4 = 10. 
- 1 + 0 = 1. Return 1.

**Formula:** 1234 > 0, 1234 % 9 = (1+2+3+4) % 9 = 10 % 9 = 1. Not 0, so return 1. ✓

----------------------------------------

## Step 7: Name It

**Digital root via modulo 9** — classical number theory. The key property `10 ≡ 1 (mod 9)` is a foundation of digit-sum tricks.

Related problems:
- Casting out nines (check arithmetic by looking at digit sums mod 9).
- Number of Digit One (count digit 1 appearances — different but digit-focused).
- Happy Number (cycle-based digit iteration).

----------------------------------------

## Step 8: Complexity

Simulation: O(log num) per iteration, O(log log num) outer iterations. Very fast for any practical input.
Closed form: **O(1)**.

Space: O(1) for both.

----------------------------------------

## Step 9: C++ Implementation

**Closed form:**

```cpp
int addDigits(int num) {
    if (num == 0) return 0;
    return 1 + (num - 1) % 9;
}
```

Two lines. Can't beat this.

**Simulation (for educational or fallback purposes):**

```cpp
int addDigits(int num) {
    while (num >= 10) {
        int sum = 0;
        while (num > 0) {
            sum += num % 10;
            num /= 10;
        }
        num = sum;
    }
    return num;
}
```

----------------------------------------

## Step 10: Follow-up Questions

- **Generalize to digital root in base b.** The formula becomes `1 + (n - 1) % (b - 1)` for n > 0 in base b. For base 10, b - 1 = 9.
- **What's the pattern of iterated digital roots?** They converge to a single digit — they don't have "deeper" structure beyond that.
- **Digital root of the sum / product of two numbers.** Works mod 9: `dr(a + b) = dr(dr(a) + dr(b))`.
- **Digital root of a negative number.** Usually undefined; or use |n|.
- **Iterated digital sum until reaching a fixed point.** Same as digital root.
- **Why is this sometimes called "casting out nines"?** Before calculators, people verified arithmetic by computing digital roots — errors of multiples of 9 would be caught.
