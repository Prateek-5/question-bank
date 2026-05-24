# Bit Manipulation — Learning Path

> **Stage:** Structures   |   **Prereqs:** Math basics   |   **Problems:** 4
>
> Bitwise reasoning at three levels: counting bits, manipulating bits, exploiting XOR's algebraic properties (involution, commutativity).
>
> **Two-tier format:** each problem has a **reference card** (linked first below) AND a paced **teaching walkthrough** in [`learn/`](./learn/) for first-time learners.

---

## How to study this topic

Small topic. Do all four in one session.

---

## Problems in study order

### Counting / popcount

1. **[Number_of_1_Bits.md](./Number_of_1_Bits.md)**  ·  [walkthrough →](./learn/Number_of_1_Bits.md) — Brian Kernighan's trick: `n & (n-1)` clears the lowest set bit. **must-do**

### Bit movement

2. **[Reverse_Bits.md](./Reverse_Bits.md)**  ·  [walkthrough →](./learn/Reverse_Bits.md) — Bit-by-bit shift, or divide-and-conquer swap (halves, quarters, ...).

### XOR algebra

3. **[Single_Number.md](./Single_Number.md)**  ·  [walkthrough →](./learn/Single_Number.md) — `a ^ a = 0`, `a ^ 0 = a`. XOR all elements; pairs cancel. **must-do**
4. **[Single_Number_II.md](./Single_Number_II.md)**  ·  [walkthrough →](./learn/Single_Number_II.md) — Bit-count mod 3, or two-counter state machine. The state-machine version is the senior signal.

---

## Patterns established

- **`n & (n-1)`:** Clears the lowest set bit. Loops over `n` until 0 count the bits in O(popcount) instead of O(32).
- **`n & -n`:** Isolates the lowest set bit (used in Fenwick trees later).
- **XOR involution:** `a ^ a = 0`. Lets you find an odd-occurrence element among many.
- **XOR commutativity:** Order doesn't matter when XORing.
- **Bit-by-bit counting:** For "every element except one appears K times," count bits mod K.
- **Two-bit state machine:** For "appears 3 times" — encode states `00 → 01 → 10 → 00` per bit, using two `int` accumulators.

---

## Common traps

- **JS bitwise operates on 32-bit signed integers.** Numbers above 2^31 produce surprises. Use `>>>` for unsigned right shift.
- **`-n` in two's complement** isolates lowest bit; in JS `n & -n` works for positive 32-bit values.
- **Reverse-bits direction.** Most-significant bit goes to least-significant slot; off-by-one easy.

---

## After this topic

- **[Trie_Bit_Manipulation_Trie/](../Trie_Bit_Manipulation_Trie/LEARNING.md)** — XOR Maximum problem uses a bit trie.
- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — bitmask DP for subset problems (later).
