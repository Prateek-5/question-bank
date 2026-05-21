# Heap / Priority Queue — Learning Path

> **Stage:** Trees & Graphs   |   **Prereqs:** [Trees_Binary_Trees/](../Trees_Binary_Trees/LEARNING.md), [Sorting_Divide_and_Conquer/](../Sorting_Divide_and_Conquer/LEARNING.md)   |   **Problems:** 11
>
> Heap = O(log n) insert + remove-min/max. Three killer patterns: **top-K**, **K-way merge**, **two-heap median**.

---

## How to study this topic

1. Heap mechanics (simple ops).
2. Top-K family.
3. K-closest / K-points.
4. K-way merge.
5. Two-heap median (the senior bar).

---

## Problems in study order

### Heap mechanics

1. **[Last_Stone_Weight.md](./Last_Stone_Weight.md)** — Max heap; simulate. **must-do**

### Top-K — size-k min heap

2. **[Kth_Largest_Element_in_a_Stream.md](./Kth_Largest_Element_in_a_Stream.md)** — Size-k min-heap; root is kth largest. **must-do**
3. **[Kth_Largest_Element_in_an_Array.md](./Kth_Largest_Element_in_an_Array.md)** — Either size-k heap O(n log k) or quickselect O(n) avg. Compare. **must-do**
4. **[Top_K_Frequent_Elements.md](./Top_K_Frequent_Elements.md)** — Frequency map + size-k heap (or bucket sort). **must-do**

### K-closest

5. **[K_Closest_Points_to_Origin.md](./K_Closest_Points_to_Origin.md)** — Max-heap of size k.
6. **[Find_K_Closest_Elements.md](./Find_K_Closest_Elements.md)** — Sorted array; binary search the window OR heap.

### K-way merge

7. **[Minimum_Cost_to_Connect_Ropes.md](./Minimum_Cost_to_Connect_Ropes.md)** — Min-heap; always merge two smallest. Huffman vibe. **must-do**
8. **[Find_K_Pairs_with_Smallest_Sums.md](./Find_K_Pairs_with_Smallest_Sums.md)** — Heap of pair-sums; expand neighbors. K-way merge variant.
9. **[Kth_Smallest_Element_in_Sorted_Matrix.md](./Kth_Smallest_Element_in_Sorted_Matrix.md)** — Heap of row pointers; pop k times. Or binary search on value.
10. **[Merge_K_Sorted_Lists.md](./Merge_K_Sorted_Lists.md)** — THE K-way merge. Heap of K heads. **must-do**

### Two-heap median

11. **[Find_Median_from_Data_Stream.md](./Find_Median_from_Data_Stream.md)** — Max-heap (lower half) + min-heap (upper half), kept balanced. Senior bar. **must-do**

---

## Patterns established

- **Size-k min-heap for top-K:** Insert each, pop if size > k. Root is the k-th largest. O(n log k).
- **K-way merge:** Heap of current heads of each list. Pop minimum, push successor. Total O(n log k).
- **Two-heap median:** Lower half in max-heap (root = max of lower), upper half in min-heap (root = min of upper). Balance sizes within 1.
- **Heap of (value, source) tuples:** When you need to know which list a value came from.
- **Heap vs quickselect tradeoff:** Heap is O(n log k), quickselect O(n) average but no stream support and worst-case O(n²).

---

## Common traps

- **Forgetting comparator on heap of objects.** Need explicit comparator function.
- **Two-heap median: balancing rule.** After insert, ensure `|lower.size - upper.size| <= 1`. Push to lower first, move root over if needed.
- **Inserting same value twice across heaps** during median balancing.
- **Heap size off-by-one in top-K:** `if (heap.size > k) heap.pop()` AFTER push, or check size BEFORE push.

---

## After this topic

- **[Graph_BFS_DFS_Dijkstra_DSU/](../Graph_BFS_DFS_Dijkstra_DSU/LEARNING.md)** — Dijkstra uses a min-heap.
- **[Greedy/](../Greedy/LEARNING.md)** — many greedy algorithms use a heap (Huffman, scheduling).
- **[Sorting_Divide_and_Conquer/](../Sorting_Divide_and_Conquer/LEARNING.md)** — comparison to quickselect.
