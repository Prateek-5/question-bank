# Number Theory & Misc — Learning Path

> **Stage:** Advanced   |   **Prereqs:** [Math/](../Math/LEARNING.md), [Bit_Manipulation/](../Bit_Manipulation/LEARNING.md)   |   **Problems:** 19
>
> Grab bag of math observation, divisor/prime, power, and randomization puzzles. Useful as warm-ups between heavier topics.

---

## How to study this topic

Order from easy observation → primes/divisors → power/exponent → math + DP → randomization. Treat as warm-ups; not all problems are core interview material.

---

## Problems in study order

### Easy observation — warm-ups

1. **[Self_Dividing_Numbers.md](./Self_Dividing_Numbers.md)** — Digit check; brute force.
2. **[Lucky_Numbers_in_a_Matrix.md](./Lucky_Numbers_in_a_Matrix.md)** — Row-min, col-max intersection.
3. **[Subtract_Product_and_Sum_of_Digits.md](./Subtract_Product_and_Sum_of_Digits.md)** — Two passes over digits.
4. **[Number_of_Good_Pairs.md](./Number_of_Good_Pairs.md)** — `count * (count - 1) / 2` per frequency. **must-do** (the combinatorial reflex)
5. **[Max_Consecutive_Ones.md](./Max_Consecutive_Ones.md)** — Single pass; running count.
6. **[Number_of_Open_Doors.md](./Number_of_Open_Doors.md)** — Square-numbers observation (like Bulb Switcher).

### Divisors / primes

7. **[Total_Number_of_Divisors_of_a_Given_Number.md](./Total_Number_of_Divisors_of_a_Given_Number.md)** — Loop up to √n. **must-do**
8. **[Four_Divisors.md](./Four_Divisors.md)** — Count divisors per number; sum when exactly 4.
9. **[Largest_Multiple_of_Three.md](./Largest_Multiple_of_Three.md)** — Greedy mod-3 digit drops.
10. **[Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md](./Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md)** — GCD repeat.

### Power / exponent

11. **[Pow_x_n.md](./Pow_x_n.md)** — Fast exponentiation via squaring. O(log n). **must-do**
12. **[Ugly_Number.md](./Ugly_Number.md)** — Divide by 2, 3, 5 until 1.

### Math + observation

13. **[Teemo_Attacking.md](./Teemo_Attacking.md)** — Interval merge sums.
14. **[Rectangle_Area.md](./Rectangle_Area.md)** — Overlap = clamp(max-min, 0).
15. **[Subsequence_of_Size_K_With_Largest_Sum.md](./Subsequence_of_Size_K_With_Largest_Sum.md)** — Sort + pick k largest by index.

### Digit DP

16. **[Number_of_Digit_One.md](./Number_of_Digit_One.md)** — Digit DP / math counting. Senior bar.

### Game theory

17. **[Divisor_Game.md](./Divisor_Game.md)** — Parity of n.

### Foundations

18. **[Memoization_DP_Basics.md](./Memoization_DP_Basics.md)** — Concept doc; bridge to DP topic.

### Randomization

19. **[Implement_Rand10_Using_Rand7.md](./Implement_Rand10_Using_Rand7.md)** — Rejection sampling; the classic. **must-do**

---

## Patterns established

- **`count * (count - 1) / 2`** — number of pairs from a frequency. Burn into reflex.
- **Loop up to √n for divisors.** Two divisors per iteration (`i` and `n/i`).
- **Fast exponentiation:** Square the base, halve the exponent. O(log n).
- **Rejection sampling:** Generate uniform from a larger space; reject the excess; map remaining uniformly.
- **Mod arithmetic for divisibility constraints.**
- **Sort + index tracking:** When you need k-largest *in original order*, sort with indices and re-sort by index.

---

## Common traps

- **Power: don't recompute `x*x` per step;** square once, reuse.
- **Rand10 from Rand7:** Need uniform over `[1, 10]`; common buggy attempt is `(rand7() + rand7()) % 10` — NOT uniform.
- **Counting pairs but n=1.** `1 * 0 / 2 = 0` — naturally correct, but watch for negative indices.
- **Mod operation on negatives** in JS / C++ — `((n % m) + m) % m` for positive result.

---

## After this topic

- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — digit DP reappears.
- **[Math/](../Math/LEARNING.md)** — companion / prereq.
- **[Bit_Manipulation/](../Bit_Manipulation/LEARNING.md)** — bit tricks sometimes solve number-theory puzzles.
