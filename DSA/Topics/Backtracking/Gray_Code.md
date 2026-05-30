# Gray Code

**Problem Link:**
<a href="https://leetcode.com/problems/gray-code/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/gray-code/</a>

**Topic:**
Backtracking

----------------------------------------

## Step 1: What's a Gray Code?

Given an integer `n`, return an ordering of all `2^n` non-negative integers less than `2^n` such that **consecutive numbers differ by exactly one bit**, and the first and last numbers also differ by one bit (circular).

Example for n = 2 (numbers 0..3):
- Valid gray code: `[0, 1, 3, 2]`.
  - 0 (00) → 1 (01): differs in bit 0. ✓
  - 1 (01) → 3 (11): differs in bit 1. ✓
  - 3 (11) → 2 (10): differs in bit 0. ✓
  - 2 (10) → 0 (00): differs in bit 1 (circular check). ✓

There are multiple valid orderings (reflections, rotations). The problem accepts any.

----------------------------------------

## Step 2: Try to Construct by Hand for n = 3

We need 8 numbers (0..7), each a 3-bit binary, each differing by one bit from the previous.

Start at 0 (000). What can we do next? Any of 001, 010, 100 (differ by one bit). Let's pick 001.

From 001, next could be 011, 000, or 101. But 000 is already used. Pick 011.

Continue: from 011, next could be 010, 001, or 111. Pick 010.

From 010: next could be 000, 011, 110. Only 110 is new. Pick 110.

From 110: 111, 100, 010. Only 111 or 100 new. Pick 111.

From 111: 110, 101, 011. Only 101 new. Pick 101.

From 101: 100, 111, 001. Only 100 new. Pick 100.

Result: `[0, 1, 3, 2, 6, 7, 5, 4]`.

Verify circular: 4 (100) → 0 (000) differs in bit 2. ✓

----------------------------------------

## Step 3: Notice the Pattern

Look at the n=2 and n=3 sequences:

n=1: [0, 1].
n=2: [0, 1, 3, 2].
n=3: [0, 1, 3, 2, 6, 7, 5, 4].

Compare n=2 and n=3:
- First half of n=3: [0, 1, 3, 2] — exactly the n=2 sequence.
- Second half of n=3: [6, 7, 5, 4] — that's [2, 3, 1, 0] + 4 = [2, 3, 1, 0] with bit 2 set.

Actually, let's look more carefully. [6, 7, 5, 4] has its bit-2 set: 100, 101, 111, 110. And the remaining bits (after removing bit 2) are 10, 11, 01, 00 — which is the n=2 sequence **reversed**!

So: n=3 = (n=2 sequence) followed by (n=2 sequence reversed, with bit 2 added).

This is the **reflect-and-add-MSB** construction. Recursively:
- n=1: [0, 1].
- n=k: (n=(k-1) sequence) + (reversed n=(k-1) sequence, each with bit k-1 set).

Each step doubles the length. After n levels, we have 2^n numbers.

----------------------------------------

## Step 4: Why Reflect-and-Add Works

Consider the n=k sequence. Each consecutive pair differs by one bit (say, in the lower k-1 bits). Adding bit k-1 to the reversed copy means:
- The last element of the first half and the first of the second half: they have the same lower k-1 bits (because reversed), but the second half has bit k-1 set. So they differ by exactly bit k-1. ✓
- Within each half, consecutive differences are preserved (bit k-1 stays constant within a half).
- The last element of the second half has the value of the first element of the first half, plus bit k-1. So closing the circle: last in second half → first in first half differs by exactly bit k-1. ✓

Reflect-and-add maintains all the gray code properties.

----------------------------------------

## Step 5: Algorithm

```
result = [0]
for bit in 0..n-1:
    for i in reversed(result):
        result.append(i | (1 << bit))
return result
```

Iterate for each bit level. Append the reversed current list with the new MSB set.

For n = 2:
- Start: [0].
- bit 0: append reversed [0] with bit 0 set: [1]. Result: [0, 1].
- bit 1: append reversed [0, 1] with bit 1 set: [3, 2]. Result: [0, 1, 3, 2]. ✓

For n = 3:
- After bit 0, 1: [0, 1, 3, 2].
- bit 2: append reversed [0, 1, 3, 2] with bit 2 set: [6, 7, 5, 4]. Result: [0, 1, 3, 2, 6, 7, 5, 4]. ✓

----------------------------------------

## Step 6: An Even Cooler Formula

Every gray code has a beautiful closed form:
```
gray(i) = i XOR (i >> 1)
```

That is, the i-th gray code value is `i ^ (i >> 1)`.

Let me verify for n = 2:
- i=0: 0 ^ 0 = 0. ✓
- i=1: 1 ^ 0 = 1. ✓
- i=2: 2 ^ 1 = 3. ✓
- i=3: 3 ^ 1 = 2. ✓

And n = 3:
- i=0: 0. i=1: 1. i=2: 3. i=3: 2. i=4: 4 ^ 2 = 6. i=5: 5 ^ 2 = 7. i=6: 6 ^ 3 = 5. i=7: 7 ^ 3 = 4.

Sequence: [0, 1, 3, 2, 6, 7, 5, 4]. ✓

Where does this formula come from? It's a remarkable bit-twiddle: XORing i with i shifted right by 1 bit effectively "flips" adjacent-bit transitions, producing exactly the gray code encoding.

Using this formula:
```
result = []
for i in 0..(2^n - 1):
    result.append(i ^ (i >> 1))
return result
```

O(2^n) time, no recursion, no iteration over bits.

----------------------------------------

## Step 7: Name It

This is the **reflected binary code**, or **Gray code**, named after Frank Gray. Both techniques — recursive reflect-and-add and the XOR formula — are standard.

Gray codes appear in real hardware: rotary encoders, Karnaugh maps, error-correction codes. The defining property (consecutive values differ by one bit) means "adjacent states" in physical devices.

----------------------------------------

## Step 8: Complexity

Both approaches: **O(2^n)** time and space.
The XOR formula is slightly faster (no reversal) and uses constant extra space beyond the output.

----------------------------------------

## Step 9: C++ Implementation

**XOR formula (shortest):**

```cpp
vector<int> grayCode(int n) {
    vector<int> result;
    result.reserve(1 << n);
    for (int i = 0; i < (1 << n); ++i) {
        result.push_back(i ^ (i >> 1));
    }
    return result;
}
```

**Reflect-and-add (more illustrative of the construction):**

```cpp
vector<int> grayCode(int n) {
    vector<int> result = {0};
    for (int bit = 0; bit < n; ++bit) {
        int size = result.size();
        int mask = 1 << bit;
        for (int i = size - 1; i >= 0; --i) {
            result.push_back(result[i] | mask);
        }
    }
    return result;
}
```

The XOR version is one-liner-simple and hardware-efficient. The reflect-and-add version is more illustrative of where the pattern comes from.

----------------------------------------

## Step 10: Follow-up Questions

- **Inverse: given a Gray code value, find its index `i`.** Also a simple formula. Gray-to-binary: `g ^ (g >> 1) ^ (g >> 2) ^ ...`.
- **Next gray code value given the current.** Find the lowest set bit of `(i + 1)` and flip that bit in the current code... trickier. Formula exists.
- **Generate all Gray codes with some additional property.** Usually requires backtracking — the reflect-and-add doesn't easily accommodate extra constraints.
- **2D Gray code (sweeping a grid).** Different construction; see "snake" traversals.
- **Balanced Gray code (every bit flips roughly equal number of times).** Harder combinatorial object.
- **Why does `i XOR (i >> 1)` work?** It encodes "position" by XOR-ing adjacent bits. Adjacent i values differ by 1, which in binary flips exactly one "run" of trailing bits; XOR with shift localizes that change to exactly one bit in the gray code. Cute bit theory.
