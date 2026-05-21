# Arrays & Matrices — Learning Path

> **Stage:** Foundation (start here)   |   **Prereqs:** none   |   **Problems:** 9
>
> First topic to attempt. Builds "scan, sweep, simulate" intuition that every later topic relies on. Read [`Concepts.md`](./Concepts.md) first.

---

## How to study this topic

1. Warm-ups establish indexing and loop patterns.
2. Then matrix access (2D indexing, boundaries, diagonals).
3. Then sweep / simulation problems.
4. Finally, math-trick and the all-time classic Trapping Rain Water.

After this topic, move to **[1_D_and_2_D_Arrays/](../1_D_and_2_D_Arrays/LEARNING.md)** for prefix sums.

---

## Problems in study order

### Warm-ups — basic scan and indexing

1. **[Concatenation_of_Array.md](./Concatenation_of_Array.md)** — Re-index into a 2×N array. **must-do**
2. **[Fizz_Buzz.md](./Fizz_Buzz.md)** — Branching on divisibility; cleanest hello-world. **must-do**
3. **[Maximum_Number_of_Words_Found_in_Sentences.md](./Maximum_Number_of_Words_Found_in_Sentences.md)** — Per-row max via split.

### Matrix access — 2D indexing

4. **[Matrix_Diagonal_Sum.md](./Matrix_Diagonal_Sum.md)** — Main + anti-diagonal; handle odd-size middle. **must-do**
5. **[Spiral_Matrix_II.md](./Spiral_Matrix_II.md)** — Boundary-walking simulation with four directions. **must-do**

### Sweep / observation

6. **[Maximum_Gap.md](./Maximum_Gap.md)** — Bucket sort to beat sort's O(n log n). Senior signal.
7. **[Total_Hamming_Distance.md](./Total_Hamming_Distance.md)** — Bit-by-bit contribution; O(n × 32) not O(n²).
8. **[Maximum_Absolute_Value_Expression.md](./Maximum_Absolute_Value_Expression.md)** — Math trick to remove absolute values via sign enumeration.

### Classic finale

9. **[Trapping_Rain_Water.md](./Trapping_Rain_Water.md)** — Two-pointer or precomputed L/R max. THE classic. **must-do**

---

## Patterns established

- **Index arithmetic.** `nums[(i + n) % n]` for wrap; `nums[i + n]` for double-length view.
- **Row/column traversal.** Nested loops; direction vectors.
- **Spiral simulation.** Four boundaries that shrink as you walk.
- **Bucket sort.** When you need linear time and the input range is bounded.
- **Bit-contribution counting.** Each bit independently contributes to the answer; sum over bits.
- **L-R / R-L precomputation.** Trapping Rain Water trick that generalizes to many "look both ways" problems.

---

## Common traps

- **Off-by-one in matrix loops.** Always verify `i < rows` and `j < cols`, not `i <= rows`.
- **Mutating input you'll need later.** Copy if the problem doesn't say in-place.
- **Naive O(n²) when O(n) is expected.** Especially for Trapping Rain Water and Maximum Gap.

---

## After this topic

- **[1_D_and_2_D_Arrays/](../1_D_and_2_D_Arrays/LEARNING.md)** — adds prefix sums on top of these scans.
- **[Two_Pointers/](../Two_Pointers/LEARNING.md)** — generalizes the Trapping Rain Water pointer trick.
- **[Hashing_Sliding_Window/](../Hashing_Sliding_Window/LEARNING.md)** — once O(n) scans aren't enough.
