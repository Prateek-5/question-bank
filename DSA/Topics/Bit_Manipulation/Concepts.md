# Bit Manipulation — Concepts Guide

----------------------------------------

## 1. Introduction

Bit manipulation is the closest most of us get to talking directly to hardware. A handful of operators — AND, OR, XOR, NOT, and shifts — unlock elegant O(1) or O(log n) solutions for problems that look much harder at first glance.

----------------------------------------

## 2. Real-Life Analogy

Think of bits as a row of light switches. AND turns off all lights that aren't on in both rows; OR turns on all lights that are on in either row; XOR flips lights that differ between rows. These basic operations compose into rich tricks — like 'flip only the lights that were off before' or 'count the lit bulbs'.

----------------------------------------

## 3. Core Idea

The essential tools: AND (`&`) masks, OR (`|`) sets, XOR (`^`) toggles, NOT (`~`) inverts, and shifts (`<<`, `>>`) scale by powers of two. Two particularly powerful tricks: `n & (n-1)` clears the lowest set bit (useful for popcount), and `n & -n` isolates the lowest set bit (useful for binary indexed trees).

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Bit manipulation shines when:

- **XOR elegantly handles 'paired' data** (find the lone non-duplicate).
- **Sets of size ≤ 32 can be represented as bitmasks.**
- **Powers of two** are central to the problem.
- **Bit tricks provide constant-factor speedups.**

If n ≤ 20, bitmask DP is often feasible (2^20 ≈ 10^6 states).

----------------------------------------

## 5. Types / Variations

- **Basic tricks** (popcount, isolate low bit, toggle bit).
- **Bitmask DP** for subset problems.
- **Bit trie** for max XOR.
- **Hamming weight / distance** computations.
- **SWAR (SIMD within a register)** for parallel bit tricks.

----------------------------------------

## 6. Step-by-Step Working

**Popcount via Brian Kernighan:**
1. cnt = 0.
2. While n != 0: n &= n-1; cnt++.
3. Return cnt.

**Iterate over all subsets of a mask:**
1. sub = mask.
2. While sub != 0: process sub; sub = (sub - 1) & mask.
3. Process the empty subset separately if needed.

----------------------------------------

## 7. Visual Explanation

**`n & (n-1)` strips the lowest set bit:**

```
n    = 10110100
n-1  = 10110011
AND  = 10110000   ← lowest '1' cleared
```

**XOR cancels pairs in `[4, 1, 2, 1, 2]`:**

```
0 ^ 4 = 4
4 ^ 1 = 5
5 ^ 2 = 7
7 ^ 1 = 6
6 ^ 2 = 4
```

Only the lone `4` survives.

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Popcount
int popcount(int n) {
    int c = 0;
    while (n) { n &= (n - 1); c++; }
    return c;
}

// Check if power of two
bool isPow2(int n) { return n > 0 && (n & (n - 1)) == 0; }

// Iterate over subsets of mask
for (int sub = mask; sub; sub = (sub - 1) & mask) { /* process sub */ }
// Don't forget the empty subset

// Set, clear, toggle, test bit b
n |= (1 << b);
n &= ~(1 << b);
n ^= (1 << b);
bool on = n & (1 << b);
```

----------------------------------------

## 9. Common Mistakes

- **Signed right shift** on negatives — use unsigned types.
- **Shifting by ≥ bit width** is undefined behavior.
- **Forgetting operator precedence** — always parenthesize bit ops in comparisons.
- **Assuming 32-bit** when values can exceed 2^31 — use `long long`.

----------------------------------------

## 10. Interview Insights

Bit manipulation questions test sharpness. Interviewers want to see:

1. **Quick recall of tricks** like popcount and subset iteration.
2. **Clear reasoning** about what each bit represents.
3. **Parenthesization and overflow awareness.**

Knowing `__builtin_popcount` and `__builtin_ctz` saves time; knowing how to implement them from scratch shows depth.
