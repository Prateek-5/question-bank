# Number of 1 Bits

**Problem Link:**
https://leetcode.com/problems/number-of-1-bits/

**Topic:**
Bit Manipulation

----------------------------------------

## Step 1: What's Being Asked

Given an unsigned 32-bit integer, return the count of `1` bits in its binary representation. (This count is called the **Hamming weight** or **population count / popcount**.)

Examples:
- `n = 11` = binary `1011` → 3 one-bits.
- `n = 128` = binary `10000000` → 1 one-bit.
- `n = 0` = binary `0` → 0 one-bits.

----------------------------------------

## Step 2: The Obvious Approach

Iterate through each bit position 0..31. For each, check if that bit is set. Sum them up.

```cpp
int count = 0;
for (int i = 0; i < 32; ++i) {
    if (n & (1u << i)) count++;
}
```

Or equivalently, shift n right by 1 each step and check the low bit:

```cpp
int count = 0;
while (n) {
    count += n & 1;
    n >>= 1;
}
```

Both are O(32) = O(1) time for 32-bit integers. Works. But let me think about whether there's a smarter way that's faster in practice.

For inputs with very few 1-bits (like `n = 1` — a single bit at position 0), these loops still iterate 32 times. Wasteful.

----------------------------------------

## Step 3: The Magical Trick — `n & (n - 1)`

Consider what happens when you subtract 1 from a number. Take `n = 12` (binary `1100`).
- `n - 1 = 11` (binary `1011`).

Notice how the lowest set bit of `n` (position 2, value 4) flipped to 0, and every bit *below* it (positions 0 and 1) flipped to 1.

Now AND them: `n & (n-1)` = `1100 & 1011` = `1000`. That's `n` with its lowest set bit removed.

This works for any n ≠ 0. The pattern:
- Binary of n ends with `...X 1 000...0` where X is some prefix and there are k zeros after the lowest 1.
- n - 1 becomes `...X 0 111...1` (the 1 flips, the zeros below flip to 1s).
- n & (n-1) becomes `...X 0 000...0` — the lowest 1 is gone, bits below are still 0.

So each `n &= (n - 1)` operation strips one 1-bit from n. Count how many times we do this until n becomes 0: that's the count of 1-bits.

----------------------------------------

## Step 4: The Brian Kernighan Algorithm

Here's the trick wrapped in a loop:

```cpp
int count = 0;
while (n) {
    n &= (n - 1);
    count++;
}
return count;
```

The loop executes exactly k times, where k is the number of 1-bits. For numbers with few 1-bits, this is much faster than the fixed 32-iteration loop.

Let me trace on n = 11 (binary `1011`):

```
Iteration 1: n=1011, n-1=1010, n&(n-1)=1010. count=1.
Iteration 2: n=1010, n-1=1001, n&(n-1)=1000. count=2.
Iteration 3: n=1000, n-1=0111, n&(n-1)=0000. count=3.
Iteration 4: n=0. Exit. Return 3. ✓
```

Three iterations — matching the bit count. Compared to the 32-iteration shift loop, that's a 10x speedup for numbers with few set bits.

----------------------------------------

## Step 5: Why "Stripping the Lowest Bit" Works

Let me be really precise. Let L be the position of the lowest 1-bit in n. Then:

- `n` in binary: bits at positions > L may be anything; bit L is 1; bits below L are all 0.
- `n - 1`: bit L becomes 0; bits below L become 1; bits above L are unchanged.
- `n & (n-1)`: bit L becomes 0 (1 AND 0); bits below L become 0 (0 AND 1); bits above L are unchanged (same AND same).

Result: the lowest 1-bit is cleared, everything else is intact. Exactly one 1-bit is removed per operation.

So after k applications, all k original 1-bits are gone, and n = 0. Loop exit. Count is k.

----------------------------------------

## Step 6: Three Other Ways Worth Knowing

**Built-in intrinsic.** Most compilers provide `__builtin_popcount(n)` which generates a single hardware instruction (POPCNT) on x86 CPUs that support it. Fastest option:

```cpp
return __builtin_popcount(n);
```

**SWAR (SIMD Within A Register).** Parallelize the bit count using arithmetic tricks. Lookup-free, branchless, 12 operations for 32 bits:

```cpp
int count(uint32_t x) {
    x = x - ((x >> 1) & 0x55555555);
    x = (x & 0x33333333) + ((x >> 2) & 0x33333333);
    x = (x + (x >> 4)) & 0x0f0f0f0f;
    return (x * 0x01010101) >> 24;
}
```

This is a genuinely clever trick (groups pairs, nibbles, bytes, and sums via multiplication). Used in older CPUs without hardware popcount.

**Precomputed table.** Precompute the popcount of every 16-bit value. Then split the 32-bit number into two halves and sum:

```cpp
int table[65536]; // precomputed
return table[n & 0xFFFF] + table[n >> 16];
```

Uses 64 KB of memory. Trades space for speed.

----------------------------------------

## Step 7: Name the Trick

`n & (n - 1)` is the **Brian Kernighan bit trick** (sometimes called the "clear lowest bit" trick). It's one of the most useful bit-manipulation idioms:

- Strip lowest set bit: `n & (n - 1)`.
- Isolate lowest set bit: `n & -n`.
- Check if power of 2: `(n > 0) && ((n & (n - 1)) == 0)`.

These three are frequently asked in interviews.

----------------------------------------

## Step 8: Complexity

Time: O(k) where k is the number of 1-bits in n (0 ≤ k ≤ 32).
Space: O(1).

Worst case O(32) — same as the simple shift loop. Best case O(1) for n = 0 or n = 1. On average for random 32-bit ints, about 16 iterations — still faster than the always-32-iteration loop.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int hammingWeight(uint32_t n) {
    int count = 0;
    while (n) {
        n &= (n - 1);
        count++;
    }
    return count;
}
```

Or if you prefer the one-liner with compiler intrinsic (faster in practice):

```cpp
int hammingWeight(uint32_t n) {
    return __builtin_popcount(n);
}
```

Both are interview-acceptable. The Brian Kernighan version showcases your understanding of bit tricks; the intrinsic shows you know language tooling.

----------------------------------------

## Step 10: Follow-up Questions

- **Counting Bits (count popcount for every number 0..n).** Use DP: `count[i] = count[i >> 1] + (i & 1)` or `count[i] = count[i & (i-1)] + 1`. O(n) total.
- **Number of 1 bits in a long long (64-bit).** Extend the same logic; `__builtin_popcountll` handles 64-bit.
- **Hamming distance between two numbers.** Popcount of `a ^ b`. The XOR has 1s exactly where the two numbers differ.
- **Reverse the bits of a 32-bit integer.** Shift and mask, 32 iterations — or SWAR-style parallel bit reversal.
- **Find the position of the only 1-bit in a power-of-two.** `__builtin_ctz(n)` — count trailing zeros.
- **Bit manipulation in big integers.** Apply the same tricks per 64-bit chunk.
