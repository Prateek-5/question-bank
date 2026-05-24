# 1D & 2D Arrays — Learning Path

> **Stage:** Foundation   |   **Prereqs:** [Arrays_and_Matrices/](../Arrays_and_Matrices/LEARNING.md)   |   **Problems:** 8
>
> The prefix-sum gateway. Master `prefix[i+1] = prefix[i] + nums[i]` and you've unlocked half of array problems.
>
> **Two-tier format:** each problem has a **reference card** (linked first below) AND a paced **teaching walkthrough** in [`learn/`](./learn/) for first-time learners.

---

## How to study this topic

1. Build the prefix-sum reflex on 1D problems first.
2. Then 2D scans (no prefix).
3. Then 2D prefix sum and the search-a-matrix trick.
4. Finish with the harder observational ones.

Then proceed to **[Two_Pointers/](../Two_Pointers/LEARNING.md)**.

---

## Problems in study order

### Prefix sum — 1D

1. **[Running_Sum_of_1D_Array.md](./Running_Sum_of_1D_Array.md)**  ·  [walkthrough →](./learn/Running_Sum_of_1D_Array.md) — Literally the prefix-sum array. The reflex starts here. **must-do**

### 2D scan (no prefix yet)

2. **[Richest_Customer_Wealth.md](./Richest_Customer_Wealth.md)**  ·  [walkthrough →](./learn/Richest_Customer_Wealth.md) — Row sums + max. **must-do**
3. **[Special_Positions_in_a_Binary_Matrix.md](./Special_Positions_in_a_Binary_Matrix.md)**  ·  [walkthrough →](./learn/Special_Positions_in_a_Binary_Matrix.md) — Precompute row + column counts.

### Index mapping

4. **[Convert_1D_Array_Into_2D_Array.md](./Convert_1D_Array_Into_2D_Array.md)**  ·  [walkthrough →](./learn/Convert_1D_Array_Into_2D_Array.md) — `i = k/cols, j = k%cols`. **must-do**

### Greedy on arrays

5. **[Max_Chunks_To_Make_Sorted.md](./Max_Chunks_To_Make_Sorted.md)**  ·  [walkthrough →](./learn/Max_Chunks_To_Make_Sorted.md) — Running max equals current index → chunk boundary.

### Contribution / submatrix sums

6. **[Sum_of_All_Submatrices_Odd_Length_Subarrays.md](./Sum_of_All_Submatrices_Odd_Length_Subarrays.md)**  ·  [walkthrough →](./learn/Sum_of_All_Submatrices_Odd_Length_Subarrays.md) — Each element's contribution = (number of subarrays containing it). Classic counting trick.

### 2D prefix sum

7. **[Range_Sum_Query_2D_Immutable.md](./Range_Sum_Query_2D_Immutable.md)**  ·  [walkthrough →](./learn/Range_Sum_Query_2D_Immutable.md) — 2D prefix sum via inclusion-exclusion. **must-do**

### Sorted 2D search

8. **[Search_a_2D_Matrix_II.md](./Search_a_2D_Matrix_II.md)**  ·  [walkthrough →](./learn/Search_a_2D_Matrix_II.md) — Staircase search from top-right (or bottom-left). O(n+m). **must-do**

---

## Patterns established

- **1D prefix sum:** `prefix[i+1] = prefix[i] + nums[i]`; range sum `prefix[r+1] - prefix[l]`.
- **2D prefix sum:** `P[i+1][j+1] = nums[i][j] + P[i][j+1] + P[i+1][j] - P[i][j]`. Inclusion-exclusion.
- **Index mapping:** `i = k / cols`, `j = k % cols` (and inverse).
- **Contribution counting:** Instead of "sum over subarrays of elements," ask "for each element, how many subarrays contain it?"
- **Staircase search on sorted matrix:** Sorted rows + sorted columns → start at corner where one direction shrinks each value.

---

## Common traps

- **Off-by-one in prefix array size.** Use `prefix[n+1]` (size n+1) so `range(l, r) = prefix[r+1] - prefix[l]` works without conditionals.
- **2D prefix forgetting inclusion-exclusion.** It's `+` row-prefix + col-prefix `-` overlap.
- **Mutating input vs allocating prefix.** Most problems allow allocation; check if O(1) extra space is required.

---

## After this topic

- **[Two_Pointers/](../Two_Pointers/LEARNING.md)** — uses these scans plus pointers.
- **[Hashing_Sliding_Window/](../Hashing_Sliding_Window/LEARNING.md)** — prefix sum + hash map is a power combo (subarray-sum problems).
- **[Searching_Binary_Search/](../Searching_Binary_Search/LEARNING.md)** — uses the staircase search idea.
