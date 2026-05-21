# Math — Learning Path

> **Stage:** Structures   |   **Prereqs:** none   |   **Problems:** 7
>
> Bite-sized math puzzles to build observation reflexes — digit ops, divisibility, GCD, calendar arithmetic.

---

## How to study this topic

Quick topic. Best done as warm-ups before harder DP/Graph sessions. Order is from observation puzzles → arithmetic → GCD/divisibility.

---

## Problems in study order

### Observation / digit ops

1. **[Add_Digits.md](./Add_Digits.md)** — Digital root; closed-form `1 + (n-1) % 9`. **must-do** (the closed form is the senior signal)
2. **[Determine_Color_of_a_Chessboard_Square.md](./Determine_Color_of_a_Chessboard_Square.md)** — Parity of row + column.
3. **[Day_of_the_Week.md](./Day_of_the_Week.md)** — Zeller's congruence or counted-days reference.

### Arithmetic sequences

4. **[Count_of_Matches_in_Tournament.md](./Count_of_Matches_in_Tournament.md)** — Each match eliminates one team → `n - 1`. Closed form > simulation.
5. **[Find_the_Pivot_Integer.md](./Find_the_Pivot_Integer.md)** — Sum-of-1-to-n; algebra over loop.

### GCD / divisibility

6. **[Find_Greatest_Common_Divisor_of_Array.md](./Find_Greatest_Common_Divisor_of_Array.md)** — `gcd(min, max)`. Know Euclid's algorithm. **must-do**
7. **[Subarray_Sums_Divisible_by_K.md](./Subarray_Sums_Divisible_by_K.md)** — Prefix sum mod K; hash. Bridges Math into Hashing. **must-do**

---

## Patterns established

- **Closed-form > simulation:** When a problem looks like "simulate N steps," ask whether there's a formula.
- **Euclid's algorithm:** `gcd(a, b) = gcd(b, a % b)`. Base case `b == 0 → a`.
- **Modular arithmetic for "divisible by K" subarray problems:** Prefix sum mod K + hash of counts.
- **Parity arguments:** `(row + col) % 2` for grid coloring.

---

## Common traps

- **Integer overflow** when summing large arrays (irrelevant in JS up to 2^53, critical in C++).
- **GCD with negative numbers** — `Math.abs` first.
- **Off-by-one in 1-indexed calendar problems** (e.g., Zeller's months Jan/Feb are treated as months 13/14 of previous year).

---

## After this topic

- **[Number_Theory_Misc/](../Number_Theory_Misc/LEARNING.md)** — primes, divisors, power.
- **[Bit_Manipulation/](../Bit_Manipulation/LEARNING.md)** — math's siblings via bitwise ops.
- **[Hashing_Sliding_Window/](../Hashing_Sliding_Window/LEARNING.md)** — already entered via Subarray Sums Divisible by K.
