# Trapping Rain Water — Cross-Reference Redirect

> **This problem appears in two topics:** `Arrays_and_Matrices` and `Two_Pointers`. To avoid duplicating the walkthrough, the full v2 teaching file lives in `Arrays_and_Matrices/learn/`. This file is a short redirect.

---

## Where the full walkthrough lives

> **➡️ Full v2 walkthrough:** [`../../Arrays_and_Matrices/learn/Trapping_Rain_Water.md`](../../Arrays_and_Matrices/learn/Trapping_Rain_Water.md)

That file covers the same problem in full (40-minute paced read), including:

- Per-position water-height formula derivation.
- Brute force, prefix-arrays version (O(n) time, O(n) space), and the two-pointer version (O(n) time, O(1) space).
- The "process shorter side" proof — the key reasoning that earns Trapping Rain Water its place in this topic's two-pointer family.
- Full line-by-line trace and pitfalls.

---

## Why this problem also appears in Two_Pointers

The most space-efficient solution to Trapping Rain Water uses the **two-pointer "process the shorter side"** idiom — the same shape you saw in:

- [`Two_Sum_II_Input_Array_Is_Sorted.md`](./Two_Sum_II_Input_Array_Is_Sorted.md) — the simpler "comparison-driven pointer move."
- [`Container_With_Most_Water.md`](./Container_With_Most_Water.md) — "discard the dominated side" with a max-area metric.

Trapping Rain Water is the **hardest pure two-pointer** problem in this topic. The decision rule "process the shorter side" is similar to Container With Most Water, but the metric being computed (water trapped at each position) is more subtle — it requires the running-max invariant on each side.

The full v2 walkthrough in `Arrays_and_Matrices/learn/` derives all of this from scratch. Once you've worked through it once (in either topic), the reference card here in `Two_Pointers/` becomes your quick-refresh.

---

## Cross-references

- **Reference card (post-mastery):** [`../Trapping_Rain_Water.md`](../Trapping_Rain_Water.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Full v2 walkthrough:** [`../../Arrays_and_Matrices/learn/Trapping_Rain_Water.md`](../../Arrays_and_Matrices/learn/Trapping_Rain_Water.md)
- **Related v2 walkthroughs in Two_Pointers:**
  - [`Two_Sum_II_Input_Array_Is_Sorted.md`](./Two_Sum_II_Input_Array_Is_Sorted.md)
  - [`Container_With_Most_Water.md`](./Container_With_Most_Water.md)
  - [`3Sum.md`](./3Sum.md)
