# Bulb Switcher

**Problem Link:**
<a href="https://leetcode.com/problems/bulb-switcher/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/bulb-switcher/</a>

**Topic:**
Greedy

----------------------------------------

## Step 1: Read the Problem

There are `n` bulbs, all initially **off**. You perform `n` rounds:
- Round 1: **toggle every bulb**.
- Round 2: toggle every **2nd** bulb (bulbs 2, 4, 6, ...).
- Round 3: toggle every **3rd** bulb.
- ...
- Round n: toggle **only bulb n**.

After all n rounds, how many bulbs are **on**?

Example: n = 3.

Round 1: toggle 1, 2, 3. All on: [1, 1, 1].
Round 2: toggle 2. [1, 0, 1].
Round 3: toggle 3. [1, 0, 0].

On: 1.

Example: n = 4.

Round 1: all on [1, 1, 1, 1].
Round 2: toggle 2, 4 → [1, 0, 1, 0].
Round 3: toggle 3 → [1, 0, 0, 0].
Round 4: toggle 4 → [1, 0, 0, 1].

On: 2.

----------------------------------------

## Step 2: When Is a Bulb On?

Bulb `i` is toggled in round `r` iff `r` divides `i` (round r toggles every r-th bulb, so bulb r, 2r, 3r, etc.).

So bulb i is toggled **once for each divisor of i**. After all rounds:
- Bulb i is on iff toggled an **odd** number of times.
- Equivalently: i has an **odd number of divisors**.

Which numbers have an odd number of divisors?

----------------------------------------

## Step 3: Number of Divisors Parity

Divisors of n usually come in pairs: if `d` divides `n`, so does `n/d`. For example, divisors of 12: 1, 2, 3, 4, 6, 12. Pairs: (1, 12), (2, 6), (3, 4). 3 pairs, 6 divisors, even count.

**Exception:** if `d = n/d`, i.e., `d² = n`. Then `d` is paired with itself and only counted once. This happens iff n is a **perfect square**.

So:
- **Non-perfect-squares have even divisor counts.**
- **Perfect squares have odd divisor counts.**

Therefore, bulb i is **on** after all rounds iff i is a perfect square.

----------------------------------------

## Step 4: Count Perfect Squares ≤ n

How many perfect squares between 1 and n?
- 1 = 1², 2² = 4, 3² = 9, ..., k² ≤ n iff k ≤ sqrt(n).
- Count = floor(sqrt(n)).

Example: n = 3. floor(sqrt(3)) = 1. Only 1² = 1 ≤ 3. Count = 1. ✓

n = 4. floor(sqrt(4)) = 2. 1 and 4 are perfect squares. Count = 2. ✓

n = 12. floor(sqrt(12)) = 3. Perfect squares: 1, 4, 9. Count = 3.

----------------------------------------

## Step 5: One-Line Solution

```
return floor(sqrt(n))
```

O(1) time and space.

No loops, no simulation. Just math.

----------------------------------------

## Step 6: Why the Simulation-to-Formula Leap

This is classic: a problem that sounds procedural ("perform these n rounds") has a beautiful closed-form solution once you spot the invariant.

Steps of the thought process:
1. "What does a bulb's on/off state depend on?" → Number of toggles.
2. "When is a bulb toggled in round r?" → When r divides bulb number.
3. "So bulb is toggled = divisor count of bulb number." → Odd vs even divisor count.
4. "Odd divisors iff perfect square." → Count perfect squares.

Each step is a reframe that leads to the final formula. This sort of "what's the underlying mathematical structure?" thinking is high-value in interview and competitive settings.

----------------------------------------

## Step 7: Name It

**Divisor parity + perfect squares.** This is a number-theory observation wrapped in a simulation problem. Pattern:
- Simulation feels O(n²) or worse.
- Hunt for an invariant.
- Invariant leads to O(1) or O(log n) formula.

Related insights:
- Sieve of Eratosthenes (perfect-square optimization at the inner loop).
- Counting divisors via prime factorization.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int bulbSwitch(int n) {
    return (int)sqrt((double)n);
}
```

Watch out for floating-point precision at large n. A safer version:

```cpp
int bulbSwitch(int n) {
    int s = (int)sqrt((double)n);
    while ((long long)(s + 1) * (s + 1) <= n) s++;
    while ((long long)s * s > n) s--;
    return s;
}
```

Adjusts for sqrt inaccuracies. For LeetCode's n ≤ 10^9, the simple sqrt usually works.

----------------------------------------

## Step 9: Follow-up Questions

- **Bulb Switcher II (different on/off operations on m lights with limited press counts).** Different combinatorial setup; requires case analysis.
- **If only bulbs at prime positions are toggled.** Fewer toggles; counting argument changes.
- **Divisor parity in other number systems (base b).** Fundamental math — still holds.
- **Count primes up to n (related sieve technique).** Different problem, different algorithm.
- **Why do perfect squares have odd divisors — pictorially?** Divisors pair `(d, n/d)`. For non-squares, all pairs distinct. For squares, one pair degenerates to `(√n, √n)`, counted once — making the total odd.
- **Bulbs toggled prime-indexed rounds only?** Bulb i toggled for each prime divisor of i; different parity analysis.
