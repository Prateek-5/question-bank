# Sorting & Divide-and-Conquer — Learning Path

> **Stage:** Structures   |   **Prereqs:** [Two_Pointers/](../Two_Pointers/LEARNING.md), [Searching_Binary_Search/](../Searching_Binary_Search/LEARNING.md)   |   **Problems:** 6
>
> Beyond `arr.sort()`: in-place partitioning, quickselect, and merge-sort as a primitive that counts pairs.
>
> **Two-tier format:** each problem has a **reference card** (linked first below) AND a paced **teaching walkthrough** in [`learn/`](./learn/) for first-time learners.

---

## How to study this topic

1. Dutch flag (in-place partition).
2. Quickselect (binary-search-style partition).
3. Merge-sort as a counting primitive (Reverse Pairs, Smaller After Self).
4. Misfits (Open the Lock is BFS).

---

## Problems in study order

### Dutch flag — 3-way partition

1. **[Sort_Colors.md](./Sort_Colors.md)**  ·  [walkthrough →](./learn/Sort_Colors.md) — Three pointers `lo, mid, hi`. The classic. **must-do**

### Quickselect

2. **[Kth_Largest_Element_in_an_Array.md](./Kth_Largest_Element_in_an_Array.md)**  ·  [walkthrough →](./learn/Kth_Largest_Element_in_an_Array.md) — Partition until pivot lands at index k. Average O(n). **must-do** (also lives in Heap with O(n log k) approach — compare)

### Counting via merge sort

3. **[Reverse_Pairs.md](./Reverse_Pairs.md)**  ·  [walkthrough →](./learn/Reverse_Pairs.md) — During merge, count `i, j` with `nums[i] > 2*nums[j]`. Senior bar.
4. **[Count_of_Smaller_Numbers_After_Self.md](./Count_of_Smaller_Numbers_After_Self.md)**  ·  [walkthrough →](./learn/Count_of_Smaller_Numbers_After_Self.md) — Same idea — count during merge, but track original indices.

### Observation / greedy

5. **[Minimum_Number_of_Bottles_Visible.md](./Minimum_Number_of_Bottles_Visible.md)**  ·  [walkthrough →](./learn/Minimum_Number_of_Bottles_Visible.md) — Sort + greedy stacking.

### Misfit (BFS — slotted here historically)

6. **[Open_the_Lock.md](./Open_the_Lock.md)**  ·  [walkthrough →](./learn/Open_the_Lock.md) — BFS on the state graph; mention this is really a Graph problem.

---

## Patterns established

- **Dutch flag (3-way partition):** Three pointers; lo is "next 0 slot", hi is "next 2 slot", mid is the scan cursor.
- **Quickselect:** Lomuto or Hoare partition; recurse only into the side containing k. O(n) average, O(n²) worst-case (mitigate with median-of-3 or random pivot).
- **Merge-sort counting:** When merging two sorted halves, count cross-pair properties in O(n) per level. Total O(n log n).
- **Index tracking through sort:** When you need original positions, sort `(value, originalIndex)` pairs.

---

## Common traps

- **Quickselect worst-case O(n²)** on already-sorted input with first-element pivot. Mitigate.
- **Off-by-one in Dutch flag.** When swapping at `mid` with `lo`, you've just placed a known value at `mid`; advance `mid`. When swapping with `hi`, you haven't yet seen what's there; don't advance `mid`.
- **Merge-sort counting after merging vs during.** Must count during merge (when `left[i]` is still > `2 * right[j]`).

---

## After this topic

- **[Heap_Priority_Queue/](../Heap_Priority_Queue/LEARNING.md)** — Kth Largest also solvable with a size-k min-heap; compare.
- **[Segment_Tree_Range_Queries/](../Segment_Tree_Range_Queries/LEARNING.md)** — Count of Smaller After Self also solvable with BIT/segment tree.
- **[Graph_BFS_DFS_Dijkstra_DSU/](../Graph_BFS_DFS_Dijkstra_DSU/LEARNING.md)** — Open the Lock belongs here conceptually.
