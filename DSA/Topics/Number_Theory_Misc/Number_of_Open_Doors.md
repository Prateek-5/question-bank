# Number of Open Doors

**Problem Link:**
https://www.geeksforgeeks.org/problems/number-of-open-doors1552/1

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: The Puzzle

There are N doors, numbered 1 to N, all initially **closed**. N passes are made:
- On pass `i` (i = 1, 2, ..., N): toggle every door whose number is divisible by i. ("Toggle" = close if open, open if closed.)

After all N passes, how many doors are **open**?

Example: N = 5.

| Door | Pass 1 | Pass 2 | Pass 3 | Pass 4 | Pass 5 |
|---|---|---|---|---|---|
| 1 | Open | — | — | — | — |
| 2 | Open | Close | — | — | — |
| 3 | Open | — | Close | — | — |
| 4 | Open | Close | — | Open | — |
| 5 | Open | — | — | — | Close |

Final state: doors 1 and 4 are open. Answer: **2**.

----------------------------------------

## Step 2: Reframe — How Many Toggles Per Door?

Door `d` is toggled on pass `i` iff `i` divides `d`. So the number of toggles on door `d` = number of divisors of `d`.

A door is **open** at the end iff it was toggled an **odd** number of times (starting closed → odd flips → open).

So: count how many numbers in [1, N] have an **odd number of divisors**.

----------------------------------------

## Step 3: Which Numbers Have Odd Divisor Count?

Divisors of `d` come in pairs: for each divisor x, `d / x` is also a divisor. If x ≠ d / x, they pair up and contribute 2 to the count.

The only exception: when `x = d / x`, i.e., `x² = d` — this means `d` is a **perfect square**, and x appears only once (not as a pair).

**So d has an odd number of divisors iff d is a perfect square.**

Example: 4 has divisors 1, 2, 4 — count 3 (odd). 4 = 2². ✓
Example: 36 has divisors 1, 2, 3, 4, 6, 9, 12, 18, 36 — count 9 (odd). 36 = 6². ✓

----------------------------------------

## Step 4: Count Perfect Squares ≤ N

Perfect squares ≤ N: 1, 4, 9, 16, ..., floor(√N)². There are exactly **floor(√N)** of them.

So the answer is `floor(√N)`.

Example: N = 5. floor(√5) = 2. Answer: **2**. ✓
Example: N = 100. floor(√100) = 10. Answer: 10. (Doors 1, 4, 9, 16, 25, 36, 49, 64, 81, 100.)

----------------------------------------

## Step 5: Algorithm

```
return floor(sqrt(N))
```

Literally one operation. O(1) time, O(1) space.

For integer-exact answer, avoid floating-point square root for large N. Use integer sqrt or binary search.

----------------------------------------

## Step 6: Trace

N = 10.
- Perfect squares ≤ 10: 1, 4, 9 → 3.
- floor(√10) = 3. ✓

N = 100. Answer = 10.
N = 99. floor(√99) = 9 (since 10² = 100 > 99). ✓

----------------------------------------

## Step 7: Why the Pairing Insight Is Beautiful

The naive approach would be:
1. For each d in [1, N], count divisors: O(√d) per door.
2. Check if count is odd.
3. Total: O(N · √N).

For N = 10⁹, that's 10^13.5 — impossibly slow.

The divisor-pairing observation collapses this to **O(1)**: just take the integer square root. The abstract insight ("perfect squares have odd divisor counts") transforms a simulation into a closed-form formula.

This is the kind of elegance that makes number theory problems rewarding.

----------------------------------------

## Step 8: Name It

**Classical "divisor count is odd iff perfect square" theorem.** A staple of number theory. Applications:
- This "doors" / "bulb switcher" type puzzle.
- Divisor-counting sieves.
- Counting perfect squares in ranges.
- Problems built around multiplicative function parity.

Related: the sum of divisors (σ) and totient (φ) functions. All multiplicative, with clean formulas for prime powers.

----------------------------------------

## Step 9: Complexity

Time: **O(1)** — just an integer square root.
Space: **O(1)**.

No loops, no data structures.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int numberOfOpenDoors(int N) {
    // Integer sqrt using binary search for precision on large N.
    long long lo = 0, hi = N;
    while (lo < hi) {
        long long mid = lo + (hi - lo + 1) / 2;
        if (mid * mid <= N) lo = mid;
        else hi = mid - 1;
    }
    return (int)lo;
}
```

For small N, `(int)sqrt((double)N)` works (double precision is enough up to ~2^53). For very large N, binary search avoids float rounding errors.

**Shorter (safe up to 32-bit):**

```cpp
int numberOfOpenDoors(int N) {
    int r = (int)sqrt((double)N);
    while ((long long)(r + 1) * (r + 1) <= N) r++;
    while ((long long)r * r > N) r--;
    return r;
}
```

Correct the rounding near the boundary.

----------------------------------------

## Step 11: Follow-up Questions

- **K passes instead of N, where K may differ from N.** Door d is toggled on pass i iff i ≤ K and i | d. So count divisors of d that are ≤ K. Parity check per door → not collapsible to a formula.
- **Doors of size 2N (start the other way).** If they start open, toggling an odd number of times makes them closed. Swap "odd" with "even."
- **Count closed doors at the end.** N minus the open count = N - floor(√N).
- **Three-state doors** (e.g., 0 → 1 → 2 → 0). Modular toggling; requires divisor counts mod 3.
- **Why does the theorem work?** Because divisors pair into (d, N/d) — either distinct (even count) or coincident (perfect square, odd count).
- **Can we efficiently check if an integer is a perfect square?** Yes: compute integer sqrt, square it, compare.
