# Stack — Learning Path

> **Stage:** Foundation   |   **Prereqs:** Arrays   |   **Problems:** 10
>
> Stack = last-in-first-out. Two families: **balanced parens / expression parsing** and **monotonic stack** (next-greater-element).

---

## How to study this topic

1. Balanced parens / string simulation.
2. Stack design.
3. Expression evaluation.
4. Monotonic stack family — culminates in Largest Rectangle in Histogram.

---

## Problems in study order

### Balanced parens / string simulation

1. **[Valid_Parentheses.md](./Valid_Parentheses.md)** — The hello-world of stacks. Push openers, match on closers. **must-do**
2. **[Remove_Outermost_Parentheses.md](./Remove_Outermost_Parentheses.md)** — Depth counter (a stack of size 1 conceptually).
3. **[Remove_All_Adjacent_Duplicates_in_String.md](./Remove_All_Adjacent_Duplicates_in_String.md)** — Stack of chars; pop on match. **must-do**

### Stack design

4. **[Min_Stack.md](./Min_Stack.md)** — Auxiliary stack tracking min so far. O(1) min. **must-do**

### Expression eval

5. **[Baseball_Game.md](./Baseball_Game.md)** — Stack of scores; operations transform top elements.
6. **[Evaluate_Reverse_Polish_Notation.md](./Evaluate_Reverse_Polish_Notation.md)** — Postfix → stack of operands. **must-do**
7. **[Expression_Contains_Redundant_Bracket_or_Not.md](./Expression_Contains_Redundant_Bracket_or_Not.md)** — Detect `(...)` with no operator inside.

### Monotonic stack

8. **[Next_Greater_Element_I.md](./Next_Greater_Element_I.md)** — Build NGE for nums2 via decreasing stack, look up for nums1. The template. **must-do**
9. **[Daily_Temperatures.md](./Daily_Temperatures.md)** — NGE returning distance. **must-do**
10. **[Largest_Rectangle_in_Histogram.md](./Largest_Rectangle_in_Histogram.md)** — Increasing stack; on pop compute area with current index as right boundary. THE classic. **must-do**

---

## Patterns established

- **Push openers, match closers:** balanced-paren template.
- **Auxiliary stack for derived state:** Min Stack pattern; track companion info per push.
- **Monotonic decreasing stack:** For each element, while stack top is smaller, pop — the popped element's next-greater is current. Used in NGE, Daily Temperatures.
- **Monotonic increasing stack:** For "next-smaller-element" or histogram problems. Pop when current is smaller; on pop, current is right boundary.
- **Sentinel values:** Push `INT_MIN` or `INT_MAX` to flush remaining stack at end (Largest Rectangle).

---

## Common traps

- **Forgetting to flush the stack at end** (Daily Temperatures et al). Remaining stack entries have no next-greater.
- **`while` vs `if`** when popping. Almost always `while`.
- **Comparison direction.** Decreasing stack pops when `top < current`; increasing stack pops when `top > current`.
- **Off-by-one on histogram width.** Width is `current_index - new_stack_top - 1` (after pop), not `current_index - popped_index`.

---

## After this topic

- **[Queues_Deque_Monotonic_Queue/](../Queues_Deque_Monotonic_Queue/LEARNING.md)** — monotonic deque for sliding-window max/min.
- **[Trees_Binary_Trees/](../Trees_Binary_Trees/LEARNING.md)** — iterative traversal uses an explicit stack.
- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — Maximal Rectangle uses the histogram trick on each row.
