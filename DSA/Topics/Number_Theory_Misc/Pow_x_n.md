# Pow(x, n)

**Problem Link:**
<a href="https://leetcode.com/problems/powx-n/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/powx-n/</a>

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: The Problem

Implement `pow(x, n)` — raise a floating-point `x` to the integer power `n`. Support negative `n` too (which means divide instead of multiply).

Examples:
- `pow(2.0, 10) = 1024.0`
- `pow(2.0, -2) = 0.25`
- `pow(2.0, 0) = 1.0` (by convention, anything^0 = 1)

Doesn't sound hard. Why is this an interview problem? Because the obvious solution doesn't scale, and the clever one teaches a really useful pattern.

----------------------------------------

## Step 2: The Naïve Multiplication Loop

Just multiply `x` by itself `n` times:

```cpp
double ans = 1;
for (int i = 0; i < n; ++i) ans *= x;
```

For n = 10, this is fine. For n = 2^31 - 1 (around 2 billion), you'd wait forever. Modern CPUs do ~10^9 ops/second — so 2 billion multiplies is about 2 seconds. Not impossible, but wasteful.

There must be a way to compute `x^n` with far fewer multiplications. What's the structure we're missing?

----------------------------------------

## Step 3: A Really Useful Observation

Take `x^10`. Naively, that's 10 multiplications: `x * x * x * x * x * x * x * x * x * x`.

But `x^10 = (x^5)^2`. So if I know `x^5`, I can get `x^10` with one additional multiply. That's two pieces of work: compute `x^5`, then square it.

And `x^5 = (x^2)^2 * x`. So `x^5` from `x^2` is: square it (getting `x^4`) then multiply by `x`. Two multiplies.

And `x^2 = x * x`. One multiply.

So the chain is: 1 (for x^2) + 2 (for x^5) + 1 (for x^10) = **4 multiplies**, not 10.

For `x^10`, savings are small. But for `x^(2^30)`, naive is 2^30 ≈ 1 billion; smart is 30 multiplies. That's the improvement.

The trick: **halving the exponent halves the work recursively**.

----------------------------------------

## Step 4: The Recursive Formulation

```
pow(x, n):
    if n == 0: return 1
    if n is even: return pow(x * x, n / 2)
    if n is odd:  return x * pow(x * x, n / 2)
```

Reading this: when the exponent is even, double the base and halve the exponent. When odd, do the same but also multiply by `x` (because odd = even + 1, and the "+1" means one extra factor of `x`).

The recursion depth is O(log n) — each step halves n.

Verify on `pow(2, 10)`:

```
pow(2, 10): even → pow(4, 5)
pow(4, 5):  odd  → 4 * pow(16, 2)
pow(16, 2): even → pow(256, 1)
pow(256, 1): odd → 256 * pow(65536, 0)
pow(65536, 0): → 1

Unrolling: 256 * 1 = 256. 4 * 256 = 1024. Back at top: 1024.
```

`pow(2, 10) = 1024`. ✓

----------------------------------------

## Step 5: Iterative Version

Recursion is fine but we can do it iteratively with the same O(log n) count:

```
ans = 1
while n > 0:
    if n is odd: ans *= x
    x *= x             # square the base for the next bit
    n /= 2             # shift exponent right
return ans
```

This is **binary exponentiation** (or "fast exponentiation"). Conceptually: we're reading `n`'s binary representation from least significant bit to most. Each bit that's 1 means "multiply ans by the current power of x."

Binary of 10 is `1010`. So:
- Bit 0 (value 1): 0. skip. x becomes x^2.
- Bit 1 (value 2): 1. ans *= x^2 = 4. x becomes x^4.
- Bit 2 (value 4): 0. skip. x becomes x^8.
- Bit 3 (value 8): 1. ans *= x^8 = 4 * 256 = 1024. x becomes x^16.
- n=0, loop ends.

`ans = 1024`. ✓

----------------------------------------

## Step 6: Handle Negative n

If n is negative, `x^n = 1 / x^(-n)`. So just compute `pow(x, -n)` with the positive version, then reciprocate.

But there's a gotcha: **if n is `INT_MIN`**, then `-n` overflows a signed int (because `INT_MIN = -2^31` and `2^31` doesn't fit in a signed int). Fix: convert to `long long` before negating.

```cpp
long long N = n;
if (N < 0) { x = 1 / x; N = -N; }
```

Now N is safely non-negative and the loop proceeds normally.

----------------------------------------

## Step 7: What About n = 0?

By math convention, `x^0 = 1` for any x. If we start `ans = 1` and the loop doesn't execute (n = 0 fails the `n > 0` condition), we return 1. Correct.

Edge case: `pow(0, 0)` is mathematically ambiguous, but most languages (including C++ and the problem spec here) treat it as 1. Our algorithm does too.

----------------------------------------

## Step 8: Name It

**Binary exponentiation** (aka **fast power**, aka **exponentiation by squaring**). It's one of the most useful algorithmic tricks — extends to:
- Modular exponentiation (`x^n mod m` in O(log n) — foundation of RSA).
- Matrix exponentiation (compute `M^n` for a matrix in O(log n) matrix multiplies — used for fast Fibonacci).
- Repeated function application (apply a function n times efficiently).

The general principle: **any associative operation can be fast-exponentiated**. Doesn't have to be multiplication.

----------------------------------------

## Step 9: Complexity

Time: **O(log n)** multiplications.
Space: **O(log n)** for recursive; **O(1)** for iterative.

Far better than O(n) naive.

----------------------------------------

## Step 10: C++ Implementation

Iterative version (cleaner, constant space):

```cpp
double myPow(double x, int n) {
    long long N = n;
    if (N < 0) { x = 1 / x; N = -N; }

    double ans = 1.0;
    while (N > 0) {
        if (N & 1) ans *= x;      // current bit of N is 1
        x *= x;                    // square x for the next bit
        N >>= 1;
    }
    return ans;
}
```

Reading the loop:
- `N & 1` checks if the least significant bit is 1. If yes, the current `x` (which is `x^(2^k)` where k = current bit position) contributes to `ans`.
- `x *= x` prepares `x` for the next bit position (`x^(2^(k+1))`).
- `N >>= 1` shifts N right, moving to the next bit.

----------------------------------------

## Step 11: Follow-up Questions

- **Modular exponentiation: compute `x^n mod m`.** Same loop, apply `% m` after each multiply. Used in cryptography.
- **Matrix exponentiation.** Replace `double` with square matrices and `*=` with matrix multiplication. Classic use: Fibonacci in O(log n).
- **Pow(x, n) for very large n (bigint exponent).** The algorithm still works, but n is stored as a bit string and shifted accordingly.
- **Precision issues with floating-point.** For very large n and borderline x near 1, precision drops. Use more careful numeric techniques if needed.
- **What if we need `x^(1/n)` (nth root)?** Different problem — use Newton's method or binary search on the value.
- **Why does iterative binary exp handle `INT_MIN` correctly?** Because we cast n to `long long` before negating. Without that cast, `-INT_MIN` overflows.
