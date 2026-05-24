# Queues, Deque, Monotonic Queue — Learning Path

> **Stage:** Structures   |   **Prereqs:** [Stack/](../Stack/LEARNING.md), [Hashing_Sliding_Window/](../Hashing_Sliding_Window/LEARNING.md)   |   **Problems:** 5
>
> Queues are FIFO; deques are double-ended; **monotonic deques** are the workhorse for "max/min in sliding window" problems.
>
> **Two-tier format:** each problem has a **reference card** (linked first below) AND a paced **teaching walkthrough** in [`learn/`](./learn/) for first-time learners.

---

## How to study this topic

1. Stack ↔ Queue conversions (design problems).
2. Greedy circular array.
3. Monotonic deque (the crown jewel).

Order matters: design first, then the harder structural use.

---

## Problems in study order

### Conversions — stack ↔ queue

1. **[Implement_Queue_using_Stacks.md](./Implement_Queue_using_Stacks.md)**  ·  [walkthrough →](./learn/Implement_Queue_using_Stacks.md) — Two-stack amortized-O(1) pattern. **must-do**
2. **[Implement_Stack_using_Queues.md](./Implement_Stack_using_Queues.md)**  ·  [walkthrough →](./learn/Implement_Stack_using_Queues.md) — Push-O(n) or pop-O(n) tradeoff.

### Stack-flavored (sometimes filed here, sometimes in Stack)

3. **[Longest_Valid_Parentheses.md](./Longest_Valid_Parentheses.md)**  ·  [walkthrough →](./learn/Longest_Valid_Parentheses.md) — Stack of indices; DP also works.

### Greedy / circular array

4. **[Gas_Station.md](./Gas_Station.md)**  ·  [walkthrough →](./learn/Gas_Station.md) — Single pass + reset-on-deficit. Tank tracks running balance. **must-do**

### Monotonic deque — the real reason this topic exists

5. **[Sliding_Window_Maximum.md](./Sliding_Window_Maximum.md)**  ·  [walkthrough →](./learn/Sliding_Window_Maximum.md) — Decreasing deque; front is window max; pop back while smaller, pop front when out of window. **must-do** (senior bar)

---

## Patterns established

- **Two-stack queue:** One stack for enqueue, one for dequeue. Move all from in→out when out is empty. Amortized O(1) per op.
- **Monotonic decreasing deque:** Front is always the max of the current window. On new element, pop back while smaller. On window advance, pop front if index out of range.
- **Index-based deque:** Store indices, not values, so you can check if front is within window `[i - k + 1, i]`.
- **Gas-station reset trick:** If running sum goes negative at index i, no station in `[start, i]` can be a valid start → reset `start = i + 1`.

---

## Common traps

- **Storing values not indices in monotonic deque.** Without indices you can't expire out-of-window elements.
- **Popping front when not needed.** Only when `front_index < i - k + 1`.
- **Two-stack queue: amortized vs worst-case.** O(1) amortized, O(n) worst-case for a single op. Mention this.
- **Confusing increasing vs decreasing deque.** Decreasing for max-in-window; increasing for min.

---

## After this topic

- **[Graph_BFS_DFS_Dijkstra_DSU/](../Graph_BFS_DFS_Dijkstra_DSU/LEARNING.md)** — BFS uses a queue.
- **[Heap_Priority_Queue/](../Heap_Priority_Queue/LEARNING.md)** — when you need ordered queue with priorities.
- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — Monotonic-deque optimization for sliding-window DP.
