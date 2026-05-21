# Greedy — Learning Path

> **Stage:** Advanced   |   **Prereqs:** [Sorting_Divide_and_Conquer/](../Sorting_Divide_and_Conquer/LEARNING.md), [Heap_Priority_Queue/](../Heap_Priority_Queue/LEARNING.md)   |   **Problems:** 7
>
> Sort then pick. The hardest part of greedy is **proving the greedy choice is optimal** (exchange argument).

---

## How to study this topic

1. Two-pointer greedy matches.
2. Sort + arithmetic.
3. Sign-flipping with priority queue.
4. Interval scheduling.
5. Observation puzzles.

---

## Problems in study order

### Two-pointer greedy match

1. **[Assign_Cookies.md](./Assign_Cookies.md)** — Sort both, two pointers; smallest greedy match. **must-do**

### Sort + product / sign

2. **[Distribute_Candies.md](./Distribute_Candies.md)** — Distinct types; `min(distinct, n/2)`.
3. **[Maximum_Product_of_Three_Numbers.md](./Maximum_Product_of_Three_Numbers.md)** — Sort; max of `(last 3) vs (first 2 + last 1)`. Handles negatives.
4. **[Maximize_Sum_After_K_Negations.md](./Maximize_Sum_After_K_Negations.md)** — Sort or min-heap; flip smallest K times.

### Interval scheduling

5. **[Non_overlapping_Intervals.md](./Non_overlapping_Intervals.md)** — Sort by end time; pick if start ≥ last end. The interval-greedy template. **must-do**
6. **[Minimum_Platforms.md](./Minimum_Platforms.md)** — Sort starts and ends separately; two-pointer sweep. **must-do**

### Math observation

7. **[Bulb_Switcher.md](./Bulb_Switcher.md)** — Square numbers have odd divisors → `floor(sqrt(n))`.

---

## Patterns established

- **Sort + greedy match:** Two arrays sorted; pair them in order.
- **Interval greedy:** Sort by **end** time, not start. Pick if compatible.
- **Sweep line:** Sort all events (start = +1, end = -1); scan for max concurrent.
- **Min-heap for "always pick smallest"** (Maximize Sum After K Negations).
- **Exchange argument:** Prove correctness by showing any swap can't improve.

---

## Common traps

- **Sorting by start in interval scheduling.** Use **end** time for "max non-overlapping."
- **Greedy where DP is required.** Some problems look greedy but aren't (e.g., knapsack with fractional capacity is greedy; 0/1 knapsack isn't).
- **Maximum Product of Three Numbers ignoring negatives.** Two big negatives × one big positive can beat three positives.
- **Off-by-one in sweep line** (handle ties: end before start? after?).

---

## After this topic

- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — when greedy fails.
- **[Heap_Priority_Queue/](../Heap_Priority_Queue/LEARNING.md)** — many greedy algorithms use a heap.
- **[Sorting_Divide_and_Conquer/](../Sorting_Divide_and_Conquer/LEARNING.md)** — companion to sort-based greedy.
