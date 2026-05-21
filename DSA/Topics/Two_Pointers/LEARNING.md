# Two Pointers — Learning Path

> **Stage:** Foundation   |   **Prereqs:** Arrays   |   **Problems:** 7
>
> Two indices, both moving forward (one direction or opposite). Each pointer moves O(n) times total → linear algorithms for problems that look quadratic.

---

## How to study this topic

1. Sorted-array two-pointer (closing in from both ends).
2. k-sum family.
3. Same-direction (slow/fast) and hybrid problems.

Pair this topic with **[Hashing_Sliding_Window/](../Hashing_Sliding_Window/LEARNING.md)** — they share many problems.

---

## Problems in study order

### Sorted-array opposing pointers

1. **[Two_Sum_II_Input_Array_Is_Sorted.md](./Two_Sum_II_Input_Array_Is_Sorted.md)** — The template. `lo, hi`, move based on sum vs target. **must-do**
2. **[Container_With_Most_Water.md](./Container_With_Most_Water.md)** — Same shape, different metric. Move the shorter side. **must-do**

### k-sum family

3. **[3Sum.md](./3Sum.md)** — Fix one, two-pointer the rest. Dedup carefully. **must-do**

### Pair problems with constraints

4. **[Minimize_Maximum_Pair_Sum_in_Array.md](./Minimize_Maximum_Pair_Sum_in_Array.md)** — Sort + pair from ends.
5. **[K_diff_Pairs_in_an_Array.md](./K_diff_Pairs_in_an_Array.md)** — Sorted two-pointer with difference target.

### Two-pointer variant of a classic

6. **[Trapping_Rain_Water.md](./Trapping_Rain_Water.md)** — Same problem as in `Arrays_and_Matrices/`, but solved with O(1) extra space via two pointers. Compare to the L/R precomputed version.

### Multi-pointer DP-flavored

7. **[Ugly_Number_II.md](./Ugly_Number_II.md)** — Three pointers tracking ×2, ×3, ×5 progress. Atypical but illuminating.

---

## Patterns established

- **Opposing pointers on sorted array:** Move the side that makes the metric better.
- **Fix-one-then-two-pointer:** k-sum reduces to (k-1)-sum by fixing the first element.
- **Skip-duplicates idiom:** `while (lo < hi && nums[lo] == nums[lo+1]) lo++;` after each move.
- **Same-direction two pointers:** One reads, one writes (covered in Linked List & sliding window).
- **Multi-pointer DP:** Each pointer tracks progress through a sub-sequence.

---

## Common traps

- **Forgetting to dedup in 3Sum.** Same element used twice or same triplet emitted twice.
- **Moving the wrong pointer.** In Container With Most Water, move the *shorter* side (moving taller can't increase area).
- **`lo < hi` vs `lo <= hi`.** Pair problems exclude self-pairing → `<` strict.

---

## After this topic

- **[Hashing_Sliding_Window/](../Hashing_Sliding_Window/LEARNING.md)** — sibling pattern; many problems solvable either way.
- **[Linked_List/](../Linked_List/LEARNING.md)** — slow/fast is two pointers on linked nodes.
- **[Sorting_Divide_and_Conquer/](../Sorting_Divide_and_Conquer/LEARNING.md)** — Dutch flag = three pointers.
