# Searching / Binary Search — Learning Path

> **Stage:** Foundation   |   **Prereqs:** [Arrays_and_Matrices/](../Arrays_and_Matrices/LEARNING.md)   |   **Problems:** 8
>
> Binary search on **values** (sorted array) and on **answers** (monotonic predicate). The second is the senior-bar variant.

---

## How to study this topic

1. Lower/upper bound — get the boundaries right first.
2. Search on shape (peak, rotated).
3. Invariant search (single element among pairs).
4. Sorted matrix.
5. Binary search on the **answer** (the harder pattern).

---

## Problems in study order

### Lower / upper bound — boundary precision

1. **[Find_First_and_Last_Position_of_Element_in_Sorted_Array.md](./Find_First_and_Last_Position_of_Element_in_Sorted_Array.md)** — Lower-bound for first, upper-bound for last. Memorize the templates. **must-do**

### Shape-based search

2. **[Find_Peak_Element.md](./Find_Peak_Element.md)** — Move toward the larger neighbor. **must-do**
3. **[Search_in_Rotated_Sorted_Array.md](./Search_in_Rotated_Sorted_Array.md)** — Decide which half is sorted, then check target's range. **must-do**

### Invariant search

4. **[Single_Element_in_a_Sorted_Array.md](./Single_Element_in_a_Sorted_Array.md)** — Pair-index invariant (`mid ^ 1`) breaks when single element is to the left.

### Sorted matrix

5. **[Search_a_2D_Matrix.md](./Search_a_2D_Matrix.md)** — Treat matrix as flat sorted array; binary search with index math.

### Binary search on the answer

6. **[Capacity_To_Ship_Packages_Within_D_Days.md](./Capacity_To_Ship_Packages_Within_D_Days.md)** — Binary search the capacity; predicate is `canShipIn(D, capacity)`. **must-do**
7. **[Magnetic_Force_Between_Two_Balls.md](./Magnetic_Force_Between_Two_Balls.md)** — Binary search the gap; predicate is `canPlaceMBallsWithGap(g)`.

### Math + search

8. **[Smallest_Good_Base.md](./Smallest_Good_Base.md)** — Number-theoretic; binary search on the base. Hardest of the set.

---

## Patterns established

- **Lower bound:** `while (lo < hi) { mid = (lo+hi)/2; if (nums[mid] < target) lo = mid+1; else hi = mid; } return lo;` Returns first index ≥ target.
- **Upper bound:** Same loop, `<=` instead of `<`. Returns first index > target.
- **Half-decision in rotated array:** One half is always sorted; check `nums[lo] <= nums[mid]` to know which.
- **Binary search on answer:** Define monotonic predicate `feasible(x)`. Binary-search the smallest x with `feasible(x) = true`. Doesn't require the input to be sorted; requires the *predicate's monotonicity*.
- **`lo + (hi - lo) / 2` for overflow safety.** Doesn't matter in JS (safe up to 2^53), matters in C++.

---

## Common traps

- **Off-by-one collapse.** `lo <= hi` with `mid+1`/`mid-1`, vs `lo < hi` with `mid`/`mid+1`. Pick a template and stick with it.
- **Infinite loop.** `lo = mid` with `lo < hi` loops forever when `lo + 1 == hi`. Use `lo = mid + 1`.
- **Forgetting to handle "not found"** in lower bound (`lo == n` means target larger than all).
- **Wrong predicate direction** in binary-search-on-answer. Draw the feasibility line.

---

## After this topic

- **[Sorting_Divide_and_Conquer/](../Sorting_Divide_and_Conquer/LEARNING.md)** — quickselect is binary search's cousin.
- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — LIS uses binary search.
- **[Heap_Priority_Queue/](../Heap_Priority_Queue/LEARNING.md)** — Kth Smallest in Sorted Matrix has a binary-search-on-answer solution.
