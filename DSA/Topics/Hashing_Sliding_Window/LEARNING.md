# Hashing & Sliding Window — Learning Path

> **Stage:** Foundation   |   **Prereqs:** [Arrays_and_Matrices/](../Arrays_and_Matrices/LEARNING.md), [1_D_and_2_D_Arrays/](../1_D_and_2_D_Arrays/LEARNING.md)   |   **Problems:** 10
>
> Hash for O(1) lookup; window for amortized O(n) range tracking. Together they handle most "subarray with property X" problems.
>
> **Two-tier format:** each problem has a **reference card** (linked first below) AND a paced **teaching walkthrough** in [`learn/`](./learn/) for first-time learners.

---

## How to study this topic

1. Basic hashing for frequency / lookup.
2. Multi-key hashing (Sudoku).
3. Prefix-sum + hash (the subarray-sum power combo).
4. Set-based for hard array problems.
5. Sliding window (fixed and variable size).
6. Hardest: hash + observation.

---

## Problems in study order

### Hash for frequency

1. **[Valid_Anagram.md](./Valid_Anagram.md)**  ·  [walkthrough →](./learn/Valid_Anagram.md) — Char count map. **must-do**

### Multi-key hash

2. **[Valid_Sudoku.md](./Valid_Sudoku.md)**  ·  [walkthrough →](./learn/Valid_Sudoku.md) — Three sets per category (row, col, box). **must-do**

### Prefix sum + hash (subarray-sum)

3. **[Subarray_Sum_Equals_K.md](./Subarray_Sum_Equals_K.md)**  ·  [walkthrough →](./learn/Subarray_Sum_Equals_K.md) — `count[prefix - k]`. THE canonical pattern. **must-do**
4. **[Maximum_Size_Subarray_Sum_Equals_K.md](./Maximum_Size_Subarray_Sum_Equals_K.md)**  ·  [walkthrough →](./learn/Maximum_Size_Subarray_Sum_Equals_K.md) — Variant: track first occurrence for max length.
5. **[Largest_Subarray_With_0_Sum.md](./Largest_Subarray_With_0_Sum.md)**  ·  [walkthrough →](./learn/Largest_Subarray_With_0_Sum.md) — Same idea, target = 0.

### Set-based

6. **[Longest_Consecutive_Sequence.md](./Longest_Consecutive_Sequence.md)**  ·  [walkthrough →](./learn/Longest_Consecutive_Sequence.md) — Build set, start only at run-beginnings (where `n-1` not in set). O(n). **must-do**

### Sliding window — variable size

7. **[Longest_Substring_Without_Repeating_Characters.md](./Longest_Substring_Without_Repeating_Characters.md)**  ·  [walkthrough →](./learn/Longest_Substring_Without_Repeating_Characters.md) — Window + last-index map. **must-do**
8. **[Minimum_Window_Substring.md](./Minimum_Window_Substring.md)**  ·  [walkthrough →](./learn/Minimum_Window_Substring.md) — Window + need-count + satisfied counter. The hardest window template.

### Hash + clever insight

9. **[Palindrome_Pairs.md](./Palindrome_Pairs.md)**  ·  [walkthrough →](./learn/Palindrome_Pairs.md) — Map word → index; for each word, check splits where one side is palindrome and other reversed exists.
10. **[Max_Points_on_a_Line.md](./Max_Points_on_a_Line.md)**  ·  [walkthrough →](./learn/Max_Points_on_a_Line.md) — Slope hash; tricky equal-points and vertical-line edge cases.

---

## Patterns established

- **Frequency map:** `map[k] = (map[k] || 0) + 1`. The `?? 0` / `(map[k] || 0)` idiom.
- **Prefix sum + hash:** Map prefix-sum → count (or first-index). Subarray sum `k` exists when `currentPrefix - k` was seen before.
- **Sliding window invariants:** Expand right; while invalid, contract left. Update answer when valid.
- **Last-index map for "no repeats" windows:** Jump `left` past previous index of current char.
- **Need-have-satisfied for minimum windows:** Counts of each required char; increment "satisfied" when all of one char are present; shrink window while still satisfied.

---

## Common traps

- **Forgetting `prefix = 0` seed.** For Subarray Sum Equals K, `map.set(0, 1)` before the loop so prefixes equal to target are counted.
- **Sliding window: shrink with `if` not `while`.** Must shrink until invariant restored.
- **Modifying frequency map while iterating.** Build first, iterate second.
- **`a.indexOf(NaN)` for arrays of numbers.** Use Set or `Number.isNaN` in some hash schemes.

---

## After this topic

- **[Stack/](../Stack/LEARNING.md)** — monotonic stack solves problems sliding window can't (e.g., next-greater-element).
- **[Two_Pointers/](../Two_Pointers/LEARNING.md)** — sliding window IS a same-direction two-pointer pattern.
- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — prefix sum is the DP-on-arrays building block.
