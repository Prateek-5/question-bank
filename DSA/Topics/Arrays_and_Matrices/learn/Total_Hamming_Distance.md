# Total Hamming Distance — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Total_Hamming_Distance.md`](../Total_Hamming_Distance.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/total-hamming-distance/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/total-hamming-distance/</a>

---

## How to use this file

Paced for someone seeing the problem for the first time. Reading time: ~30 minutes if you do every small example by hand. Every concept the problem touches — binary, XOR, bit testing, counting pairs, etc. — is explained **inline** so you don't have to go to another tab. No prior knowledge is assumed beyond:

- You can write a `for` loop.
- You can read array indexing like `nums[i]`.
- You know what "modulo" / addition / multiplication are.

**Map of this file (11 short sections):**

1. Read the problem and translate it
2. The natural first attempt (brute force)
3. Why the brute force fails
4. The pivot — looking at the sum a different way
5. The "count differing pairs at one bit" shortcut
6. How to test a single bit of a number (the `(x >> b) & 1` idiom)
7. The full algorithm + code
8. Trace the code line-by-line
9. Complexity comparison
10. Common pitfalls
11. The shape — when else this trick applies + self-check

---

## 1. Read the problem and translate it

The problem talks about something called **Hamming distance**. Don't worry if you've never heard the term — here's the entire definition.

> **The Hamming distance between two numbers is the count of bit positions where they differ.**

To make sense of that, you need to know what a "bit position" is.

---

> **Mini-refresher: numbers in binary.**
>
> Every non-negative integer can be written using only `0` and `1` digits. We call this **binary form**. For example:
>
> ```
> Decimal     Binary
>   4   →     0100
>  14   →     1110
>   2   →     0010
> ```
>
> Each `0` or `1` in that string is called a **bit**. Bits are numbered from the **right side, starting at 0**:
>
> ```
>   4  =  0  1  0  0
>         │  │  │  │
>         │  │  │  └── bit 0  (worth 2⁰ = 1 if set)
>         │  │  └───── bit 1  (worth 2¹ = 2 if set)
>         │  └──────── bit 2  (worth 2² = 4 if set)
>         └─────────── bit 3  (worth 2³ = 8 if set)
> ```
>
> So `4 = 0100` has only bit 2 set (`4 = 4`). `14 = 1110` has bits 1, 2, 3 set (`2 + 4 + 8 = 14`). `2 = 0010` has only bit 1 set.
>
> You don't have to convert numbers by hand for this problem — we'll write a tiny helper later. Just remember: **numbers are stacks of bits, and bit 0 lives on the right.**

---

OK back to Hamming distance. Let me compute HD(4, 14) by lining up their bits:

```
            bit 3   bit 2   bit 1   bit 0
   4   =      0       1       0       0
  14   =      1       1       1       0
  ─────────────────────────────────────────
  differ?    YES      no     YES      no
```

They differ at 2 positions (bit 1 and bit 3). So **HD(4, 14) = 2**.

> **Mini-exercise:** Try HD(4, 2) before reading on. Line them up bit by bit and count differences.
>
> <details>
> <summary>Click to expand answer</summary>
>
> ```
>             bit 3   bit 2   bit 1   bit 0
>    4   =      0       1       0       0
>    2   =      0       0       1       0
>   ─────────────────────────────────────────
>   differ?    no      YES     YES      no
> ```
>
> 2 positions differ. **HD(4, 2) = 2.**
> </details>

---

**Now the actual problem.** Given an array `nums`, return the **sum of Hamming distances over every pair** `(i, j)` with `i < j`.

For `nums = [4, 14, 2]`, the pairs are `(4, 14)`, `(4, 2)`, `(14, 2)` — that's 3 pairs. The answer is:

```
Total = HD(4, 14) + HD(4, 2) + HD(14, 2)
      =     2     +     2     +     2
      =     6
```

That's the answer we have to compute, in any order, for any input array.

---

## 2. The natural first attempt

The obvious approach: try every pair, compute HD of each, add them up. To compute HD between two specific numbers, the classic trick is the **XOR** operator (`^`).

---

> **Mini-refresher: XOR (`^`).**
>
> XOR is a bit-by-bit comparison operator. For a single bit pair:
>
> ```
> 0 XOR 0  =  0    (same)
> 0 XOR 1  =  1    (differ)
> 1 XOR 0  =  1    (differ)
> 1 XOR 1  =  0    (same)
> ```
>
> Notice the rule: **XOR is 1 exactly when the two bits differ**. That's literally what we want for Hamming distance.
>
> When you XOR two whole integers, it does bit-by-bit XOR at every position. Example: `4 XOR 14`:
>
> ```
>      0 1 0 0     ← 4
>  XOR 1 1 1 0     ← 14
>  ─────────────
>      1 0 1 0     ← result: 10 in decimal
> ```
>
> The result has a `1` exactly where 4 and 14 differed. **So Hamming distance is the count of 1-bits in the XOR.**
>
> Counting 1-bits has a name — **popcount** (population count). Most languages have a built-in:
> - C++: `__builtin_popcount(x)`
> - Python: `bin(x).count('1')` or `x.bit_count()` (3.10+)
> - JavaScript: no built-in; loop manually or use `x.toString(2).split('1').length - 1`

---

So the brute-force code is:

```cpp
int totalHammingDistance(vector<int>& nums) {
    int n = nums.size();
    int total = 0;
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            total += __builtin_popcount(nums[i] ^ nums[j]);
        }
    }
    return total;
}
```

Two nested loops over pairs. Let me trace it on `[4, 14, 2]`:

```
i=0, j=1:  4 XOR 14 = 1010, popcount = 2,  total = 2
i=0, j=2:  4 XOR  2 = 0110, popcount = 2,  total = 4
i=1, j=2: 14 XOR  2 = 1100, popcount = 2,  total = 6
```

Returns 6. ✓ Submit it to LeetCode.

---

## 3. Why this fails on big inputs

The judge rejects with **TLE (Time Limit Exceeded)**. Why?

Look at the loops. For an array of size `n`, how many pairs `(i, j)` with `i < j` are there?

---

> **Mini-refresher: counting pairs.**
>
> If you have `n` items and want unordered pairs (so `{A, B}` and `{B, A}` count as one pair):
>
> Each item can pair with `n − 1` others (anything except itself). That gives `n × (n − 1)` ordered pairs. But each unordered pair was counted twice (once when A came first, once when B came first), so divide by 2:
>
> ```
> number of pairs = n × (n − 1) / 2
> ```
>
> Examples:
> - 4 items → `4 × 3 / 2 = 6` pairs
> - 100 items → `100 × 99 / 2 = 4,950` pairs
> - 10,000 items → `10,000 × 9,999 / 2 ≈ 5 × 10⁷` pairs
>
> When we say an algorithm is **O(n²)**, this is what we mean — its work grows like `n²` (the constants like `/2` don't change the growth rate).

---

LeetCode's constraint here is `n ≤ 10⁴`. So:

- Pairs: about `5 × 10⁷`.
- Per pair: XOR + popcount ≈ a few cheap ops.
- Total ops: roughly `2 × 10⁸` to `10⁹` depending on the machine.

LeetCode judges accept roughly `10⁸` simple ops per second. We're looking at maybe `5–10` seconds — well past the time limit.

So the brute force is **correct but too slow**. We need a different approach. The problem: we're enumerating all pairs, and there are quadratically many. **Can we get the answer WITHOUT looking at all pairs?**

That feels impossible — every pair contributes to the answer. But hold on. Let me look at WHAT we're summing more carefully.

---

## 4. The pivot — looking at the sum a different way

Let me write out, in painstaking detail, what the brute force computed for `[4, 14, 2]`.

```
Total = HD(4, 14) + HD(4, 2) + HD(14, 2)
```

Each `HD` is itself a sum across bit positions — we expand them. From section 1:

- HD(a, b) = (do they differ at bit 0?) + (do they differ at bit 1?) + (do they differ at bit 2?) + (do they differ at bit 3?)

Each term is 0 or 1. Let me lay out all 3 HDs as rows in a table, with one column per bit position:

```
                    bit 0    bit 1    bit 2    bit 3
HD(4, 14)    =        0   +    1   +    0   +    1     = 2
HD(4,  2)    =        0   +    1   +    1   +    0     = 2
HD(14, 2)    =        0   +    0   +    1   +    1     = 2
                                                         ─────
                                                         Total = 6
```

Total = 6. ✓

Now look at this table as a list of 12 little numbers (each 0 or 1). If you add them up in any order, you get 6.

---

> **Mini-refresher: addition doesn't care about order.**
>
> If you have a list of numbers, **the order you add them in doesn't change the total**. Example:
> ```
> 1 + 2 + 3 = 6
> 3 + 1 + 2 = 6
> 2 + 1 + 3 = 6
> ```
> Same for any rearrangement. This is just basic arithmetic (the technical names are "commutative" and "associative" — fancy words for "order doesn't matter"). We're going to use this freedom to rearrange the 12 numbers in our table.

---

Here's the pivot. The brute force adds those 12 numbers **row-by-row** — that is, it computes HD(pair 1), then HD(pair 2), then HD(pair 3). What if I add them **column-by-column** instead?

```
Bit 0 column:  0 + 0 + 0  =  0
Bit 1 column:  1 + 1 + 0  =  2
Bit 2 column:  0 + 1 + 1  =  2
Bit 3 column:  1 + 0 + 1  =  2
                            ───
                            Total = 6  ✓
```

**Same 12 numbers, same total** — we just chose to add them in a different order.

Why does this matter? Because each column has a really clean meaning:

> **Bit b's column-sum = "how many pairs differ at bit b?"**

If we can compute that quickly for each bit, we're done — and we've avoided enumerating any pairs. The new question:

> **"For each bit position separately, how many pairs differ at THAT bit?"**

We haven't solved anything yet. We just chose to add the same 12 things in a different order. But the new order makes each piece much easier to compute — as we'll see now.

---

## 5. The "count differing pairs at one bit" shortcut

Let me focus on just **bit 1** for `[4, 14, 2]`. I want to know: how many pairs differ at bit 1?

From section 1, the bit-1 values are:

```
 4 → bit 1 is 0
14 → bit 1 is 1
 2 → bit 1 is 1
```

A pair "differs at bit 1" exactly when one number has a `0` here and the other has a `1`. Checking by hand:

- pair (4, 14): 0 and 1 → DIFFER ✓
- pair (4, 2): 0 and 1 → DIFFER ✓
- pair (14, 2): 1 and 1 → SAME

2 pairs differ at bit 1. (Same as the bit-1 column-sum in the table from section 4.)

Now here's the shortcut. I want to count these without enumerating any pairs. Group the numbers by their bit-1 value:

```
Group "bit is 1":  {14, 2}   ← size 2
Group "bit is 0":  {4}       ← size 1
```

A differing pair = pick one number from the "bit is 1" group and pair it with one from the "bit is 0" group. How many ways to do that?

---

> **Mini-refresher: multiplication rule for counting.**
>
> If you're forming a pair by picking one item from set A and one item from set B, and:
> - `|A|` = size of A
> - `|B|` = size of B
>
> ...then there are `|A| × |B|` possible pairs.
>
> Example: 3 shirts, 4 pants → 3 × 4 = 12 outfits. (Each shirt can match any of the 4 pants, and there are 3 shirts.)
>
> This works for any "pick one from each side" pairing.

---

By the multiplication rule:

```
differing pairs at bit 1 = (size of bit-is-1 group) × (size of bit-is-0 group)
                         = 2 × 1
                         = 2  ✓
```

Matches our hand-count. **No pair enumeration.**

Let me give these group sizes simpler names so they work for any bit:

```
c        = count of numbers whose bit is set to 1
n − c    = count of numbers whose bit is 0  (the rest of the array)
```

Then the formula for one bit is:

```
differing pairs at this bit = c × (n − c)
```

That's the whole shortcut.

**Verification on all 4 bits for `[4, 14, 2]`:**

| bit | numbers with 1 here | `c` | `n − c` | `c × (n − c)` | column-sum from §4? |
|-----|---------------------|-----|---------|---------------|---------------------|
|  0  | (none)              |  0  |    3    | `0 × 3 = 0`   | 0 ✓                 |
|  1  | 14, 2               |  2  |    1    | `2 × 1 = 2`   | 2 ✓                 |
|  2  | 4, 14               |  2  |    1    | `2 × 1 = 2`   | 2 ✓                 |
|  3  | 14                  |  1  |    2    | `1 × 2 = 2`   | 2 ✓                 |

Sum of the right column: `0 + 2 + 2 + 2 = 6`. ✓ Total matches.

So the algorithm is just: **for each bit, count `c`, add `c × (n − c)` to the total.**

---

## 6. How to test a single bit of a number

The algorithm needs to ask, for each number `x` and each bit `b`: **"is bit `b` of `x` set to 1?"** Time to learn the standard idiom.

---

> **Mini-refresher: testing bit `b` of integer `x`.**
>
> The expression is `(x >> b) & 1`. Two parts.
>
> **Part 1: `x >> b` ("right shift")**
>
> `>>` slides all the bits of `x` to the right by `b` positions. Bits that fall off the right edge are gone; new `0`s come in from the left.
>
> Example: `14 >> 2`.
> ```
> 14  =  1 1 1 0    (bit 3, bit 2, bit 1, bit 0)
>        ──────→ shift right by 2 ──────→
>        0 0 1 1    (the rightmost two bits dropped off; two zeros come in on the left)
>      =  3 in decimal
> ```
>
> The important point: **after `x >> b`, the bit that used to be at position `b` of `x` is now at position 0 of the result** (the rightmost bit).
>
> **Part 2: `... & 1` ("AND with 1")**
>
> `1` in binary is `…0001` (bit 0 set, all others 0).
>
> The `&` operator compares each bit pair and returns 1 only if both are 1:
> ```
> 0 & 0 = 0,  0 & 1 = 0,  1 & 0 = 0,  1 & 1 = 1
> ```
>
> ANDing with `1` (which is `…0001`) keeps bit 0 of the left operand and zeros out everything else.
>
> Example: `3 & 1`.
> ```
>     0 0 1 1     ← 3
> AND 0 0 0 1     ← 1
> ────────────
>     0 0 0 1     ← result = 1
> ```
>
> **Part 1 + Part 2 combined:**
>
> `(x >> b) & 1` shifts bit `b` of `x` down to position 0, then keeps only that position. Result is **exactly 0 or 1** — telling you whether bit `b` of `x` was set.
>
> Quick check: `(14 >> 2) & 1`.
> - `14 >> 2 = 3` (just shown).
> - `3 & 1 = 1`.
> - So bit 2 of 14 was set. (And indeed `14 = 1110`, bit 2 = `1`. ✓)

---

> **Mini-exercise:** What does `(4 >> 1) & 1` return? (`4 = 0100`.)
>
> <details>
> <summary>Click to expand answer</summary>
>
> - `4 >> 1`: shift `0100` right by 1 → `0010` = 2.
> - `2 & 1`: `0010 & 0001 = 0000` = 0.
> - So bit 1 of 4 is `0`. (Matches `4 = 0100` — bit 1 is the second-from-right and it's 0. ✓)
> </details>

---

## 7. The full algorithm + code

Now we have all the pieces:

```
for each bit position b in 0..31:
    c = 0
    for each x in nums:
        if (x >> b) & 1 is 1:    // is bit b of x set?
            c = c + 1
    total = total + c * (n - c)
return total
```

(Why 32 bits? Because LeetCode's `int` is 32 bits, and `nums[i]` fits in there. Iterating to a constant 32 keeps the code simple and removes off-by-one risk.)

In C++:

```cpp
int totalHammingDistance(vector<int>& nums) {
    int n = nums.size();
    int total = 0;
    for (int b = 0; b < 32; b++) {          // outer: 32 bit positions
        int c = 0;                           // count of numbers with bit b set
        for (int x : nums) {                 // inner: scan the array once
            if ((x >> b) & 1) c++;           // bit b of x is set?
        }
        total += c * (n - c);                // this bit's contribution
    }
    return total;
}
```

Three things to internalize:

1. The **outer loop is over bits** (32 of them). The inner loop is over the array.
2. Each iteration of the outer loop scans all `n` elements once to compute `c`. That's `n` work per bit.
3. After computing `c`, we add `c × (n − c)` to the total. That's the contribution of this bit.

---

## 8. Trace the code line-by-line

`nums = [4, 14, 2]`, so `n = 3` and we start with `total = 0`.

**Bit b = 0:**

```
c = 0
x = 4:  (4 >> 0) & 1 = (4) & 1 = 0.        Not set, skip.
x = 14: (14 >> 0) & 1 = (14) & 1 = 0.      Not set, skip.
x = 2:  (2 >> 0) & 1 = (2) & 1 = 0.        Not set, skip.
c = 0.
total += 0 * (3 - 0) = 0.
total = 0.
```

**Bit b = 1:**

```
c = 0
x = 4:  (4 >> 1) & 1 = (2) & 1 = 0.        Not set.
x = 14: (14 >> 1) & 1 = (7) & 1 = 1.       Set!  c = 1.
x = 2:  (2 >> 1) & 1 = (1) & 1 = 1.        Set!  c = 2.
c = 2.
total += 2 * (3 - 2) = 2.
total = 2.
```

**Bit b = 2:**

```
c = 0
x = 4:  (4 >> 2) & 1 = (1) & 1 = 1.        Set!  c = 1.
x = 14: (14 >> 2) & 1 = (3) & 1 = 1.       Set!  c = 2.
x = 2:  (2 >> 2) & 1 = (0) & 1 = 0.        Not set.
c = 2.
total += 2 * (3 - 2) = 2.
total = 4.
```

**Bit b = 3:**

```
c = 0
x = 4:  (4 >> 3) & 1 = (0) & 1 = 0.
x = 14: (14 >> 3) & 1 = (1) & 1 = 1.       c = 1.
x = 2:  (2 >> 3) & 1 = (0) & 1 = 0.
c = 1.
total += 1 * (3 - 1) = 2.
total = 6.
```

**Bits b = 4 through 31:**

All three numbers fit in 4 bits, so `(x >> b) & 1 = 0` for `b ≥ 4`. Every iteration: `c = 0`, `total += 0`. No change.

**Return `total = 6`.** ✓

---

## 9. Complexity comparison

**Brute force:**
- Time: O(n²). For `n = 10⁴`, that's ~10⁸ ops × small constant.
- Space: O(1).

**This version:**
- Time: outer loop 32 times, inner loop `n` times → **32n ops = O(n)** (32 is a constant).
- Space: O(1).

For `n = 10⁴`, the new version does ~`32 × 10⁴ = 3.2 × 10⁵` ops. That's **about 1000× faster** than brute force on the max-size input. Well within time limits.

---

## 10. Common pitfalls

1. **Multiplication overflow.** `c × (n − c)` with `n = 10⁴` peaks at `~2.5 × 10⁷` — fits in `int32`. The sum of 32 such terms is at most `~8 × 10⁸` — *barely* fits. For larger `n`, switch `total` to `long long`.

2. **Iterating fewer than 32 bits.** If you stop at bit 29, you'll silently miss contributions from numbers ≥ 2³⁰. Iterating to 32 is constant cost — just do it.

3. **Using `(x & (1 << b))` and adding directly to `c`.** Watch out: `x & (1 << b)` returns the bit at position `b` *as a power of 2* — so for bit 3 it returns `8`, not `1`. Either:
   - Convert it: `if (x & (1 << b)) c++;` (the `if` makes it a boolean) — ✓
   - Or shift back down: `c += (x >> b) & 1;` — ✓
   - **Don't do** `c += (x & (1 << b));` — this adds the value (1, 2, 4, 8, …) not the count. ✗

4. **Forgetting bit 0 is the rightmost.** When debugging, write the binary out with bit 0 on the right. Mixing up the direction leads to off-by-one bugs.

5. **Trying this trick where the per-pair property doesn't decompose.** This works because Hamming distance breaks into a sum-across-bit-positions. It does NOT directly help on problems like "sum of `a_i × a_j` over pairs" — multiplication doesn't decompose this way. (Section 11 has more.)

---

## 11. The shape — when else this trick applies (+ self-check)

The technique is sometimes called **per-position contribution counting** or **swap-the-order-of-summation**. The general recipe:

> When you face a **"sum over all pairs (or tuples) of some property"** problem, AND that property breaks down as **"sum across independent positions / bits / dimensions"**, you can switch from O(n²) pair enumeration to O(positions × n) per-position counting.

Examples in this family:

| Problem | Per-pair property | Decomposes by | Per-position formula |
|---|---|---|---|
| Total Hamming Distance | bits that differ | bit position | `c × (n − c)` |
| Sum of `a_i XOR a_j` over pairs | bits set in XOR | bit position | `c × (n − c) × 2^b` (each differing pair contributes `2^b` to the XOR value at bit `b`) |
| Sum of `a_i AND a_j` over pairs | bits set in AND | bit position | `C(c, 2) × 2^b` (need both numbers to have the bit; that's "choose 2 from group of size c") |
| Sum of `a_i + a_j` over pairs | identity | (trivial) | each element appears in `n − 1` pairs → answer = `(n − 1) × sum(a)` |
| Sum of `a_i × a_j` over pairs | product | (DOESN'T decompose per-bit) | use `((Σa)² − Σ(a²)) / 2` instead |

---

> **Self-check — the question to ask next time.**
>
> When you see a problem that asks for **some aggregate over all pairs / tuples**, before reaching for a nested loop, ask:
>
> > **"Does the per-pair quantity decompose as a sum over independent positions / bits / dimensions? If yes, can I count per-position contributions instead?"**
>
> If yes, you've turned `O(n²)` (or worse) into `O(positions × n)`. For 32-bit ints, "positions" is 32 — effectively constant. For 26-letter strings, it's 26. Either way: linear in `n` after the swap.

---

## Cross-references

- **Reference card (post-mastery):** [`../Total_Hamming_Distance.md`](../Total_Hamming_Distance.md) — quick refresher when you've already understood this.
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md) — study order for Arrays & Matrices.
- **Related topics that use bit-level reasoning:** see the **Bit_Manipulation** topic — Number of 1 Bits, Single Number, Reverse Bits — they reuse `(x >> b) & 1` and similar idioms.
