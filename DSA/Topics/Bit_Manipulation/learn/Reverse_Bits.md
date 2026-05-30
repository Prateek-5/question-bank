# Reverse Bits — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Reverse_Bits.md`](../Reverse_Bits.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/reverse-bits/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/reverse-bits/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: walking bits one-by-one is a clean O(32) approach.** Bonus: the SWAR ("SIMD Within A Register") technique reverses in O(log 32) = 5 operations via masks and shifts. **Read [`Number_of_1_Bits.md`](./Number_of_1_Bits.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. The bit-by-bit approach
3. Why shift-left on result, shift-right on n
4. The SWAR (parallel) approach
5. Code
6. Trace it
7. Lookup-table approach
8. Common pitfalls
9. The shape — bit reversal patterns

---

## 1. Read the problem

Given an unsigned 32-bit integer `n`, **reverse its bits**. The least significant bit becomes the most significant, and vice versa.

**Example:**

- `n = 43261596` = binary `00000010 10010100 00011110 10011100`.
- Reversed: binary `00111001 01111000 00101001 01000000` = `964176192`.

Treat n as a fixed 32-bit string. Reverse the order of its bits.

---

## 2. The bit-by-bit approach

Extract bits from `n` one at a time (LSB-first) and append them to `result` in reverse order (so the first extracted bit becomes the most significant).

```
result = 0
for _ in 0..31:
    result = (result << 1) | (n & 1)    # make room, then append
    n >>= 1
return result
```

Each iteration:
1. **Shift `result` LEFT by 1** to make room for the new bit at the low position.
2. **OR in `n & 1`** (n's current LSB) into that slot.
3. **Shift `n` RIGHT by 1** to move to the next bit.

After 32 iterations, all of n's bits have been transferred to result in reverse order.

> **Mini-refresher: why `result << 1 | (n & 1)`?**
>
> - `result << 1`: shifts existing bits up, opens a 0 at the bottom.
> - `n & 1`: gives 0 or 1 from n's current LSB.
> - `OR`-ing puts that 0 or 1 into the newly-opened slot.
>
> Net effect: result grows by one bit at the LOW position each iteration. After 32 iterations, the first-extracted bit has been shifted up 31 times — it's now at the TOP of result. The last-extracted bit is at position 0.
>
> Reversed.

---

## 3. Why shift-left on result, shift-right on n

It's a "conveyor belt" model:

- `n` is the SOURCE conveyor; we PULL bits from the right (LSB) by `n & 1`, then `n >>= 1` to advance.
- `result` is the DESTINATION conveyor; we PUSH bits onto the right, then `result <<= 1` to advance.

The two directions are OPPOSITE because:
- In `n`, the LSB is "first to read" (rightmost).
- In `result`, the LSB is "first to write," but we want it to end up as the MSB after all writes. Each write shifts it FURTHER LEFT.

After 32 iterations, the FIRST bit read ends up FURTHEST LEFT — exactly the reverse position.

---

## 4. The SWAR (parallel) approach

Instead of 32 iterations, we can reverse bits in just 5 operations using "divide-and-conquer" with bitmasks:

```
n = (n >> 16) | (n << 16);                                      # swap top 16 and bottom 16
n = ((n & 0xff00ff00) >> 8) | ((n & 0x00ff00ff) << 8);          # swap bytes within 16-bit halves
n = ((n & 0xf0f0f0f0) >> 4) | ((n & 0x0f0f0f0f) << 4);          # swap nibbles
n = ((n & 0xcccccccc) >> 2) | ((n & 0x33333333) << 2);          # swap 2-bit groups
n = ((n & 0xaaaaaaaa) >> 1) | ((n & 0x55555555) << 1);          # swap individual bits
return n;
```

Each step swaps progressively-smaller groups of bits:
1. Top 16 ↔ Bottom 16.
2. Within each 16-bit half, swap bytes.
3. Within each byte, swap nibbles.
4. Within each nibble, swap 2-bit groups.
5. Within each 2-bit group, swap single bits.

After 5 steps, the bits are fully reversed. The masks (`0xaaaaaaaa = 1010...1010`, `0x55555555 = 0101...0101`, etc.) isolate alternating groups.

This is SWAR ("SIMD Within A Register"): parallel operations on multiple data slots using one wide register.

---

## 5. Code

**C++ — bit-by-bit (preferred for interviews):**

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

**C++ — SWAR (faster, harder to remember):**

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

**Python:**

```python
def reverseBits(n):
    result = 0
    for _ in range(32):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result
```

**JavaScript** (careful — JS bitwise is 32-bit SIGNED):

```javascript
function reverseBits(n) {
    let result = 0;
    for (let i = 0; i < 32; i++) {
        result = (result << 1) | (n & 1);
        n >>>= 1;       // unsigned right shift
    }
    return result >>> 0;  // force unsigned 32-bit result
}
```

Complexity: **O(1) time** (32 iterations max), **O(1) space.**

---

## 6. Trace it

Use a simple 8-bit example: `n = 5` (binary `00000101`). Expected reversed: binary `10100000` = `160`.

(For demonstration; actual problem uses 32-bit. Same pattern.)

```
result = 0. n = 00000101.

Iter 0: n & 1 = 1. result = (0 << 1) | 1 = 1.   n >>= 1 → 00000010 (= 2).
Iter 1: n & 1 = 0. result = (1 << 1) | 0 = 2.   n >>= 1 → 00000001 (= 1).
Iter 2: n & 1 = 1. result = (2 << 1) | 1 = 5.   n >>= 1 → 0.
Iter 3: n & 1 = 0. result = (5 << 1) | 0 = 10.  n = 0.
Iter 4: 0. result = 20.
Iter 5: 0. result = 40.
Iter 6: 0. result = 80.
Iter 7: 0. result = 160.

Return 160. ✓
```

The reversal is built up incrementally, with the first-extracted bit (LSB of original) ending up at the top of `result`.

---

## 7. Lookup-table approach

For repeated calls, precompute a table of byte-reversals (256 entries).

```
byte_reversal_table[0..255] = ...   // precomputed

result = (byte_reversal_table[n & 0xff] << 24)
       | (byte_reversal_table[(n >> 8) & 0xff] << 16)
       | (byte_reversal_table[(n >> 16) & 0xff] << 8)
       | (byte_reversal_table[(n >> 24) & 0xff])
```

Four lookups + bit-shifts. Very fast. Used in libraries where bit reversal is called frequently. Overkill for a single call.

---

## 8. Common pitfalls

1. **Wrong direction.** Easy to swap which bit goes where. Test on small examples to verify direction.

2. **Forgetting to make `n` unsigned.** In C++, right-shifting a signed negative number is implementation-defined (can sign-extend). Use `uint32_t`.

3. **JS quirk: signed bitwise.** `>>>` for unsigned right shift. `>>> 0` at the end to force unsigned result.

4. **Loop runs 32 or n's bit length?** Always loop 32 times (the bit width). Don't stop early when n becomes 0 — you still need to shift result left for the remaining bits.

5. **Order of operations: shift then OR vs OR then shift.** `result = (result << 1) | (n & 1)` is correct. `result = (result | (n & 1)) << 1` would OR FIRST (placing the bit at LSB) and THEN shift it — different result.

6. **Memorizing SWAR without understanding the masks.** SWAR is elegant but error-prone to recall. For interviews, bit-by-bit is safer.

7. **Reversing only the meaningful bits.** Don't try to reverse "just the bits up to the highest 1." Reverse ALL 32 bits.

---

## 9. The shape — bit reversal patterns

The pattern: **process bits one-at-a-time with a conveyor-belt model**, OR use **SWAR parallel-mask tricks** for log-factor speedups.

Where bit reversal appears:
- **FFT (Fast Fourier Transform):** bit-reversal permutation is the first step.
- **Image processing:** reverse pixel data.
- **Network protocols:** bit ordering conversions.
- **Crypto:** some hash functions use bit-reversal subroutines.

The bit-by-bit pattern also generalizes to **bit-by-bit processing of any kind**:
- Counting trailing zeros.
- Finding the highest set bit.
- Bit-by-bit arithmetic (add, subtract, multiply without `+`).

**Pattern to internalize:**

> "Bit processing is often a 32-iteration loop with `n & 1` to read the current bit and `n >>= 1` to advance. Pair with the appropriate accumulator update for the task."

---

> **Self-check — the question to ask next time.**
>
> When you face a bit-level transformation, ask:
>
> > **"Can I loop 32 times, reading the LSB and updating an accumulator, then shifting both? Or do I need a parallel SWAR approach for speed?"**
>
> If yes, you've got the bit-by-bit template.

---

## Cross-references

- **Reference card (post-mastery):** [`../Reverse_Bits.md`](../Reverse_Bits.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_1_Bits.md`](./Number_of_1_Bits.md) — popcount, also bit-by-bit.
  - Coming next: [`Single_Number.md`](./Single_Number.md), [`Single_Number_II.md`](./Single_Number_II.md) — XOR algebra.
