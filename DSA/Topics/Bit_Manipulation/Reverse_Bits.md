# Reverse Bits

**Problem Link:**
https://leetcode.com/problems/reverse-bits/

**Topic:**
Bit Manipulation

----------------------------------------

## Step 1: What Does "Reverse Bits" Mean?

Given a 32-bit unsigned integer, reverse its binary representation. Bit 0 becomes bit 31, bit 1 becomes bit 30, etc.

Example: `n = 43261596` (binary `00000010100101000001111010011100`).

Reversed: `00111001011110000010100101000000` = `964176192`.

The leftmost bit of the input becomes the rightmost bit of the output, and vice versa. We're treating n as a fixed-width 32-bit string and reversing it.

----------------------------------------

## Step 2: Bit-by-Bit Approach

The straightforward method: peel off bits from the input one at a time and attach them to the output in reverse order.

```
result = 0
for _ in range(32):
    result = (result << 1) | (n & 1)   # shift result left, append the last bit of n
    n >>= 1                              # move to next bit of n
return result
```

Reading this: at each iteration, the rightmost bit of `n` (via `n & 1`) becomes the new rightmost bit of `result` (via the OR). Then we shift `result` one bit left for the next iteration, placing that new bit into position.

Wait — we shift `result` left *before* appending? Let me re-read the loop.

```
result << 1: makes room by shifting result left.
OR with n&1: place the new bit into the freshly-made rightmost slot.
```

So after one iteration, result has 1 meaningful bit. After 2, it has 2. After 32, result holds all 32 bits in reversed order.

Trace for n = 5 (binary 101, on 4 bits for simplicity, reversed = 1010 = 10):

Actually let me just trace on a small example. n = 5 = 0b00000101 (8-bit). Expected reverse: 0b10100000 = 160.

```
result = 0.
Iter 0: n & 1 = 1. result = (0 << 1) | 1 = 1. n = 2 (0b10).
Iter 1: n & 1 = 0. result = (1 << 1) | 0 = 2 (0b10). n = 1.
Iter 2: n & 1 = 1. result = (2 << 1) | 1 = 5 (0b101). n = 0.
Iter 3: n & 1 = 0. result = (5 << 1) | 0 = 10 (0b1010). n = 0.
Iter 4..7: n = 0, so n & 1 = 0. Each iteration shifts result left:
  result = 20 (0b10100), 40 (0b101000), 80 (0b1010000), 160 (0b10100000).
```

Final result = 160. ✓

O(32) = O(1) operations. Done.

----------------------------------------

## Step 3: Why Shift-Left on result and Shift-Right on n

Mental model: we're reading n's bits from least significant to most significant, and writing result's bits from most significant to least significant.

- n is read LSB-first via `n & 1` and `n >>= 1`.
- Result is written LSB-first via appending new bits at the rightmost position; since we shift result left each iteration, older bits move "up" to more significant positions.

After 32 iterations, the first bit we read (n's original LSB) ends up at the top of result (its MSB). Perfect reversal.

----------------------------------------

## Step 4: SWAR — Parallel Bit Reversal

There's a cool divide-and-conquer approach that reverses in O(log bits) = O(5) ops for 32-bit:

```
n = (n >> 16) | (n << 16);                       // swap 16-bit halves
n = ((n & 0xff00ff00) >> 8) | ((n & 0x00ff00ff) << 8);  // swap bytes within 16-bit halves
n = ((n & 0xf0f0f0f0) >> 4) | ((n & 0x0f0f0f0f) << 4);  // swap nibbles
n = ((n & 0xcccccccc) >> 2) | ((n & 0x33333333) << 2);  // swap bit pairs
n = ((n & 0xaaaaaaaa) >> 1) | ((n & 0x55555555) << 1);  // swap single bits
```

Each step swaps progressively-smaller groups of bits:
- Step 1: swap the top 16 bits with the bottom 16.
- Step 2: swap bytes within each 16-bit half.
- Step 3: swap nibbles within each byte.
- Step 4: swap 2-bit groups within each nibble.
- Step 5: swap single bits within each pair.

After all 5 steps, the bits are fully reversed.

This is classic **SWAR** ("SIMD Within A Register"): parallel bit manipulation using masks and shifts. Super fast in practice, just a few ops.

----------------------------------------

## Step 5: Choose Your Approach

Both are O(1) for 32-bit ints (since the bit width is fixed). The bit-by-bit loop is more readable; the SWAR version is slightly faster but trickier.

For interview, the bit-by-bit version is usually preferred — it's clear, concise, and correct. Mention SWAR if the interviewer seems to want more depth.

----------------------------------------

## Step 6: Cached / Lookup Table Approach

A third option: precompute the reversal of every 8-bit value (256 entries). To reverse a 32-bit value, split into four bytes, look up each reversal, and stitch in reverse byte order.

```
byte[4] = precomputed reversals
result = (byte[n & 0xff] << 24)
       | (byte[(n >> 8) & 0xff] << 16)
       | (byte[(n >> 16) & 0xff] << 8)
       | (byte[(n >> 24) & 0xff])
```

4 lookups + bit manipulation. Very fast if you'll call `reverseBits` many times — the precomputation amortizes over calls.

For a single call, the overhead of building the table isn't worth it.

----------------------------------------

## Step 7: Name the Techniques

- **Bit-by-bit loop**: direct, O(bits).
- **SWAR (parallel bit swap)**: log(bits) ops, hardware-friendly.
- **Lookup table**: O(1) per call after O(constant) preprocessing.

For problem classes like this, knowing all three flavors marks you as someone who's seriously looked at bit manipulation.

----------------------------------------

## Step 8: Complexity

Time: **O(32)** = O(1). SWAR is O(5) ops, lookup is O(4) lookups.
Space: **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

**Bit-by-bit (clean, preferred):**

```cpp
uint32_t reverseBits(uint32_t n) {
    uint32_t result = 0;
    for (int i = 0; i < 32; ++i) {
        result = (result << 1) | (n & 1);
        n >>= 1;
    }
    return result;
}
```

**SWAR (fast):**

```cpp
uint32_t reverseBits(uint32_t n) {
    n = (n >> 16) | (n << 16);
    n = ((n & 0xff00ff00) >> 8) | ((n & 0x00ff00ff) << 8);
    n = ((n & 0xf0f0f0f0) >> 4) | ((n & 0x0f0f0f0f) << 4);
    n = ((n & 0xcccccccc) >> 2) | ((n & 0x33333333) << 2);
    n = ((n & 0xaaaaaaaa) >> 1) | ((n & 0x55555555) << 1);
    return n;
}
```

Both return the same value; pick based on readability vs. speed preference.

----------------------------------------

## Step 10: Follow-up Questions

- **Reverse 64-bit integer.** Same patterns, loop to 64 or extend SWAR with one more level.
- **Reverse bits within a byte.** One SWAR operation or small lookup.
- **Reverse bits but preserve the sign bit.** For signed integers; reverse lower 31 bits, leave MSB alone.
- **Reverse the bits of each byte independently.** Apply SWAR within byte boundaries.
- **If reverseBits is called frequently, how do we optimize?** Cache the 8-bit reversal table.
- **Why does SWAR use those specific masks?** The masks (0xff00ff00, etc.) isolate alternating groups of bits, letting us swap halves, quarters, etc., in parallel.
