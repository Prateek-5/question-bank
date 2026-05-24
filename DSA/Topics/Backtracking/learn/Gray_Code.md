# Gray Code — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Gray_Code.md`](../Gray_Code.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/gray-code/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **A bit-twiddling marvel.** The lesson: **the formula `gray(i) = i XOR (i >> 1)` generates a gray code sequence in O(2^n) time, one line.** Alternative recursive "reflect and add" construction also works. **Read [`../../Bit_Manipulation/learn/Number_of_1_Bits.md`](../../Bit_Manipulation/learn/Number_of_1_Bits.md) first** for XOR basics.

**Map of this file (8 short sections):**

1. Read the problem
2. What's a Gray code?
3. The reflect-and-add construction
4. The XOR formula
5. Code
6. Trace it
7. Why the XOR formula works
8. The shape — bit-twiddle closed forms

---

## 1. Read the problem

Given an integer `n`, return an array of `2^n` distinct non-negative integers (representing `2^n` n-bit strings) such that:
- The list starts with `0`.
- Consecutive integers DIFFER BY EXACTLY ONE BIT.
- The first and last also differ by exactly one bit (CIRCULAR property).
- Each integer in `[0, 2^n)` appears exactly once.

**Examples:**

- `n = 2` → `[0, 1, 3, 2]`.
  - 0 (00) → 1 (01): differ in bit 0. ✓
  - 1 (01) → 3 (11): differ in bit 1. ✓
  - 3 (11) → 2 (10): differ in bit 0. ✓
  - 2 (10) → 0 (00): differ in bit 1. ✓ (circular)
- `n = 1` → `[0, 1]`.

---

## 2. What's a Gray code?

> **Mini-refresher: Gray codes in the real world.**
>
> A **Gray code** is an ordering of binary numbers such that consecutive values differ by ONLY ONE bit.
>
> Used in:
> - **Rotary encoders**: physical devices where only ONE bit can be misread during a transition; Gray code prevents catastrophic misreads (e.g., 011 → 100 → many bits flipping vs Gray: 011 → 010 → one bit).
> - **Karnaugh maps**: simplifying Boolean expressions; adjacent cells differ by one variable.
> - **Error-correcting codes**: single-bit-flip detection.

Multiple Gray codes exist for each n (reflections, rotations). This problem accepts ANY valid one.

---

## 3. The reflect-and-add construction

The standard recursive construction:

```
n = 1: [0, 1]
n = k: (n = k-1 sequence) + (n = k-1 sequence REVERSED, with bit k-1 set)
```

For n=2:
- n=1 sequence: `[0, 1]`.
- Reversed with bit 1 set: `[3, 2]` (bit 1 of 1 = 1|10 = 3; bit 1 of 0 = 0|10 = 2).
- Concatenated: `[0, 1, 3, 2]`. ✓

For n=3:
- n=2 sequence: `[0, 1, 3, 2]`.
- Reversed with bit 2 set: `[6, 7, 5, 4]`.
- Concatenated: `[0, 1, 3, 2, 6, 7, 5, 4]`. ✓

**Why this works:**
- Within the first half: same as n-1 sequence (one-bit-different consecutive).
- Between halves: last of first half vs first of second half — same lower bits, differ only in bit n-1.
- Within the second half: reversed sequence, bit n-1 stays constant — still one-bit-different consecutive.
- Circular: last of second half vs first of first half — same lower bits (because reversed), differ only in bit n-1.

All Gray-code properties preserved.

---

## 4. The XOR formula

A remarkable closed form:

> **`gray(i) = i XOR (i >> 1)`**

For i in `0..(2^n - 1)`, compute `i XOR (i >> 1)`. The sequence is a Gray code.

Verify for n=2 (i=0..3):
- i=0: `0 XOR 0 = 0`.
- i=1: `1 XOR 0 = 1`.
- i=2: `2 XOR 1 = 3`.
- i=3: `3 XOR 1 = 2`.

Sequence: `[0, 1, 3, 2]`. ✓

For n=3:
- i=0..3: same as n=2 above.
- i=4: `4 XOR 2 = 6`.
- i=5: `5 XOR 2 = 7`.
- i=6: `6 XOR 3 = 5`.
- i=7: `7 XOR 3 = 4`.

Sequence: `[0, 1, 3, 2, 6, 7, 5, 4]`. ✓

---

## 5. Code

**C++ — XOR formula (one-liner):**

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

**C++ — reflect-and-add:**

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

**Python:**

```python
def grayCode(n):
    return [i ^ (i >> 1) for i in range(1 << n)]
```

**JavaScript:**

```javascript
function grayCode(n) {
    const result = [];
    for (let i = 0; i < (1 << n); i++) {
        result.push(i ^ (i >> 1));
    }
    return result;
}
```

Complexity: **O(2^n) time and space** (output-bound).

---

## 6. Trace it

**`n = 3`** with XOR formula:

```
i=0: 0 XOR 0 = 0. Binary 000.
i=1: 1 XOR 0 = 1. Binary 001.
i=2: 2 XOR 1 = 3. Binary 011.
i=3: 3 XOR 1 = 2. Binary 010.
i=4: 4 XOR 2 = 6. Binary 110.
i=5: 5 XOR 2 = 7. Binary 111.
i=6: 6 XOR 3 = 5. Binary 101.
i=7: 7 XOR 3 = 4. Binary 100.
```

Verify consecutive differences:
- 000 → 001: bit 0. ✓
- 001 → 011: bit 1. ✓
- 011 → 010: bit 0. ✓
- 010 → 110: bit 2. ✓
- 110 → 111: bit 0. ✓
- 111 → 101: bit 1. ✓
- 101 → 100: bit 0. ✓
- (circular) 100 → 000: bit 2. ✓

All Gray code properties hold. ✓

---

## 7. Why the XOR formula works

> **Mini-refresher: Adjacent binary numbers and bit flips.**
>
> Consecutive integers `i` and `i+1`: they differ by a "carry" pattern. For example:
> - 7 (0111) → 8 (1000): four bits change.
> - 11 (1011) → 12 (1100): two bits change.
>
> In binary, adding 1 to `i` flips a RUN of trailing 1's (and the first 0 above them). So `i` and `i+1` can differ by MANY bits.

XOR with shifted-right: `gray(i) = i ^ (i >> 1)`.

**Effect:** for any two adjacent values `i` and `i + 1`:
- `i + 1` has its trailing 1s flipped to 0s and the next bit flipped to 1 (carry propagation).
- `(i + 1) >> 1` shifts this pattern by one.
- `(i + 1) ^ ((i + 1) >> 1)` produces a value that differs from `gray(i)` by EXACTLY ONE BIT.

The mathematical proof involves carry chains and is satisfying but technical. The empirical verification (above) is sufficient to TRUST the formula.

**Practical takeaway:** `i XOR (i >> 1)` is the canonical Gray code formula. Memorize and use.

---

## 8. The shape — bit-twiddle closed forms

The pattern this problem teaches:

> **"Some combinatorial sequences have ELEGANT BIT-MANIPULATION CLOSED FORMS. Knowing them turns O(2^n × n) constructions into O(2^n) one-liners."**

Where bit-twiddle formulas shine:

| Problem | Formula |
|---|---|
| **This problem** (Gray code) | `i XOR (i >> 1)` |
| Power of 2 check | `n > 0 && (n & (n-1)) == 0` |
| Lowest set bit | `n & -n` |
| Clear lowest set bit | `n & (n - 1)` |
| Count bits 0..n (Counting Bits) | `count[i] = count[i & (i-1)] + 1` |
| Reverse bits | SWAR mask trick |
| Sum without `+` | XOR + carry shifts |
| Single Number (XOR all) | `result XOR= x for x in nums` |

**Pattern to internalize:**

> "For sequences over bit patterns, ASK FIRST: is there a bit-arithmetic closed form? Closed forms beat iterative construction in elegance and often in speed."

---

> **Self-check — the question to ask next time.**
>
> When you face a sequence over binary numbers (Gray, popcount, single-bit-difference series), ask:
>
> > **"Is there a closed-form BIT EXPRESSION (XOR, AND, shift) that computes the i-th element directly?"**
>
> If yes, you've got a one-liner instead of a recursion.

---

## Cross-references

- **Reference card (post-mastery):** [`../Gray_Code.md`](../Gray_Code.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`../../Bit_Manipulation/learn/Number_of_1_Bits.md`](../../Bit_Manipulation/learn/Number_of_1_Bits.md), [`../../Bit_Manipulation/learn/Reverse_Bits.md`](../../Bit_Manipulation/learn/Reverse_Bits.md).
  - Coming next: [`Sudoku_Solver.md`](./Sudoku_Solver.md) — the hardest backtracking problem.
