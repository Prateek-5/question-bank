# Bit Manipulation — Concepts

## Core Theory
Bit-level operations manipulate integers at the binary level. Common tricks involve AND/OR/XOR/NOT, shifts, and Brian Kernighan's trick (`n & (n-1)` clears the lowest set bit).

## Common Patterns
- **XOR cancels pairs** — single-number problems.
- **Masking subsets** via bitmask DP.
- **Popcount** via `__builtin_popcount`.
- **Bit reversal** by bit-by-bit loop or SWAR.

## When to Use
When problems hinge on binary properties, subset enumeration (n ≤ 20), or XOR invariants.

## Template
```cpp
for (int mask = 0; mask < (1 << n); ++mask)
    for (int sub = mask; sub; sub = (sub - 1) & mask) { /* iterate subsets */ }
```

## Common Mistakes
- Signed right-shift vs unsigned for top bits.
- Forgetting to clear bits before setting.
- Overflow with shifts ≥ bit width.
