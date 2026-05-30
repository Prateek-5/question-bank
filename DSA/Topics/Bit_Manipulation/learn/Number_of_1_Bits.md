# Number of 1 Bits — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Number_of_1_Bits.md`](../Number_of_1_Bits.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/number-of-1-bits/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/number-of-1-bits/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The introduction to bit manipulation.** The lesson: **`n & (n - 1)` clears the LOWEST set bit of n.** This Brian Kernighan trick lets you count bits in O(popcount) instead of O(32). Once you know it, you'll see it everywhere — power-of-2 check, subset enumeration, Fenwick trees.

**Map of this file (9 short sections):**

1. Read the problem
2. The shift-loop approach
3. Brian Kernighan's trick
4. Why `n & (n - 1)` clears the lowest bit
5. Code
6. Trace it
7. Other approaches (intrinsics, SWAR, lookup)
8. Common pitfalls
9. The shape — bit tricks toolkit

---

## 1. Read the problem

Given an unsigned 32-bit integer `n`, return the number of `1` bits in its binary representation. This is also known as the **Hamming weight** or **popcount**.

**Examples:**

- `n = 11` (binary `1011`) → **3**.
- `n = 128` (binary `10000000`) → **1**.
- `n = 4294967293` (binary `11111111 11111111 11111111 11111101`) → **31**.
- `n = 0` → **0**.

---

## 2. The shift-loop approach

```
count = 0
while n != 0:
    count += n & 1     # extract lowest bit
    n >>= 1             # shift right
return count
```

> **Mini-refresher: bitwise basics.**
>
> - `n & 1`: returns the LOWEST bit of n (0 or 1).
> - `n >> 1`: right-shifts n by one position. Equivalent to integer division by 2.
> - `n << 1`: left-shifts. Equivalent to multiplication by 2.
> - `n | mask`: sets bits where mask has 1s.
> - `n & mask`: clears bits where mask has 0s.
> - `n ^ mask`: flips bits where mask has 1s.
>
> For unsigned ints, right shift is logical (fills with 0). For signed negative ints in C++, right shift may be implementation-defined.

This loop runs at most 32 times (for 32-bit ints). O(32) = O(1).

But there's a smarter loop that runs only as many times as there are 1-bits.

---

## 3. Brian Kernighan's trick

The clever trick:

> **`n & (n - 1)` clears the LOWEST SET BIT of n.**

So if we replace `n` with `n & (n - 1)` and increment a counter each time, each iteration removes exactly one 1-bit. Loop until n is 0; the counter holds the popcount.

```
count = 0
while n != 0:
    n &= (n - 1)
    count += 1
return count
```

For numbers with few 1-bits (like `n = 1` or `n = 4`), this is much faster than the 32-iteration shift loop.

---

## 4. Why `n & (n - 1)` clears the lowest bit

Look at the binary representation:

> **Example: n = 12 (binary `1100`).**
>
> - `n - 1 = 11` (binary `1011`).
> - `n & (n - 1)` = `1100 & 1011` = `1000`.
>
> The lowest set bit (position 2) was removed.

Why does this work?

Let `L` be the position of the lowest 1-bit in `n`. Then `n` looks like `...X 1 000...0` where:
- The 1 is at position `L`.
- Below position `L` are all zeros.
- Above position `L` is the prefix `X` (unspecified).

Now `n - 1`:
- Bit `L` (which was 1) becomes 0.
- Bits below `L` (which were 0) become 1.
- The prefix `X` above `L` is UNCHANGED (no borrow propagates past the lowest 1).

So `n - 1` looks like `...X 0 111...1`.

ANDing:
- Position `L`: `1 AND 0 = 0`. Cleared.
- Positions below `L`: `0 AND 1 = 0`. Still cleared.
- Positions above `L` (prefix X): `X AND X = X`. Unchanged.

Result: lowest 1-bit is gone; everything else is intact.

> **Mini-refresher: the operation as a sentence.**
>
> "`n & (n - 1)` removes the rightmost 1-bit." If you can recall this sentence, you have the trick.
>
> The complement: `n & -n` ISOLATES the rightmost 1-bit (gives `n` with all OTHER bits cleared). Useful in Fenwick trees and other algorithms.

---

## 5. Code

**C++ (Brian Kernighan):**

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

**C++ (intrinsic — fastest in practice):**

```cpp
int hammingWeight(uint32_t n) {
    return __builtin_popcount(n);     // GCC/Clang; uses POPCNT instruction
}
```

**Python:**

```python
def hammingWeight(n):
    count = 0
    while n:
        n &= (n - 1)
        count += 1
    return count
```

Or use the built-in:

```python
def hammingWeight(n):
    return bin(n).count('1')           # short but slightly slower than the loop
```

**JavaScript:**

```javascript
function hammingWeight(n) {
    let count = 0;
    while (n !== 0) {
        n &= (n - 1);
        count++;
    }
    return count;
}
```

Complexity: **O(popcount(n)) time, O(1) space.** Worst case O(32) for 32-bit.

---

## 6. Trace it

**n = 11 (binary `1011`):**

```
n = 1011 (binary).

Iter 1: n - 1 = 1010. n & (n-1) = 1010. count = 1.   ← cleared bit 0
Iter 2: n = 1010. n - 1 = 1001. n & (n-1) = 1000. count = 2.   ← cleared bit 1
Iter 3: n = 1000. n - 1 = 0111. n & (n-1) = 0000. count = 3.   ← cleared bit 3
Iter 4: n = 0. EXIT.

Return 3. ✓
```

3 iterations for 3 one-bits. Matches expected.

**n = 0:** loop doesn't execute. Return 0.

**n = 1:** one iteration. Return 1.

---

## 7. Other approaches (intrinsics, SWAR, lookup)

- **Hardware intrinsic (`__builtin_popcount`):** uses the CPU's POPCNT instruction. One CPU cycle. Fastest in practice.
- **SWAR (SIMD Within A Register):** branchless arithmetic that counts bits in parallel via masks. About 12 ops for 32 bits. Used historically before POPCNT existed.
- **Lookup table:** precompute popcount for each 16-bit value (64 KB table). Two lookups per 32-bit number. Trades memory for time.

In an interview, **show Brian Kernighan's trick** (demonstrates understanding). Mention intrinsic if asked about real-world performance.

---

## 8. Common pitfalls

1. **Forgetting that the inner loop modifies n.** Some try `for i in range(32): if n & (1 << i): count++` — fine, but doesn't use the Kernighan trick.

2. **Using signed int for input.** For negative numbers in C++, `n >> 1` may sign-extend. Use `uint32_t` or use the `&` trick (which is sign-agnostic when shifting isn't involved).

3. **Counting iterations not bits.** The Kernighan loop counts the WHILE iterations, which equals the popcount. Don't accidentally count something else.

4. **Returning `n` instead of `count`.** Easy slip — `n` becomes 0 at the end.

5. **Confusing popcount with TOTAL bits.** A 32-bit `n = 1` has 32 BITS (mostly 0) but popcount 1.

6. **JS bitwise quirks.** JS converts operands to 32-bit signed ints. For very large numbers (> 2^31), behavior changes. Use `>>>` for unsigned right shift.

---

## 9. The shape — bit tricks toolkit

Three foundational bit tricks every programmer should know:

| Trick | What it does | Use case |
|---|---|---|
| **`n & (n - 1)`** | clear lowest set bit | popcount (THIS problem), power-of-2 check, subset iteration |
| **`n & -n`** | isolate lowest set bit | Fenwick trees (BIT), low-bit-only mask |
| **`n & (n + 1)`** | clear lowest set GROUP of 1s | rare but useful |

> **Mini-refresher: power-of-2 check.**
>
> A positive integer `n` is a power of 2 iff it has EXACTLY ONE bit set. So:
>
> ```
> isPowerOfTwo(n) = (n > 0) && ((n & (n - 1)) == 0)
> ```
>
> If `n` has only one 1-bit, clearing it leaves 0. If `n` has zero or multiple 1-bits, clearing the lowest leaves a non-zero result.

Where popcount appears:

| Problem | Use |
|---|---|
| **This problem** | direct |
| Hamming Distance | popcount of XOR (bits that differ) |
| Power of Two check | popcount == 1 |
| Subset iteration via bitmask | enumerating all sub-masks |
| Counting bits 0..n | DP: `count[i] = count[i & (i-1)] + 1` |
| Find odd-frequency element | XOR all, then popcount |

**Pattern to internalize:**

> "Bit tricks reduce O(32) operations to O(popcount). They aren't just optimizations — they're the canonical idioms of bit manipulation."

---

> **Self-check — the question to ask next time.**
>
> When you face any problem about counting, isolating, or clearing specific bits, ask:
>
> > **"Can I use `n & (n - 1)` or `n & -n` to do bit-level surgery in O(1)?"**
>
> If yes, you've unlocked classical bit tricks.

---

## Cross-references

- **Reference card (post-mastery):** [`../Number_of_1_Bits.md`](../Number_of_1_Bits.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Reverse_Bits.md`](./Reverse_Bits.md), [`Single_Number.md`](./Single_Number.md), [`Single_Number_II.md`](./Single_Number_II.md).
