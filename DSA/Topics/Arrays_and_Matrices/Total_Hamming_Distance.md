# Total Hamming Distance

**Problem Link:**
https://leetcode.com/problems/total-hamming-distance/

**Topic:**
Arrays & Matrices (Bit Manipulation flavored)

----------------------------------------

## Step 1: Understand Hamming Distance

The **Hamming distance** between two integers is the number of bit positions where they differ.

Example: 
- 1 = `0001`. 
- 4 = `0100`. 
- They differ at bits 0 and 2. Hamming distance = 2.

This problem: given `nums`, compute the **sum of Hamming distances over all pairs (i, j) with i < j**.

Example: `nums = [4, 14, 2]`.
- HD(4, 14): 4=0100, 14=1110. Differ at bits 1, 3. HD = 2.
- HD(4, 2): 4=0100, 2=0010. Differ at bits 1, 2. HD = 2.
- HD(14, 2): 14=1110, 2=0010. Differ at bits 2, 3. HD = 2.

Total: 6.

----------------------------------------

## Step 2: Brute Force

For each pair, XOR them, count set bits. O(n² · bits). For n = 10^4, that's 10^9 ops — too slow.

----------------------------------------

## Step 3: Per-Bit Contribution Trick

Think bit by bit. For each bit position `b`, how many pairs differ at bit b?

Count how many numbers have bit b set (call this `c`). How many have bit b **not** set? That's `n - c`.

Pairs that differ at bit b: one number with bit set, one without. Count = `c × (n - c)`.

Total Hamming distance = sum over b of `c_b × (n - c_b)`.

**O(n · bits)** — linear in input size, constant per bit.

----------------------------------------

## Step 4: Trace

`nums = [4, 14, 2]`. 4=100, 14=1110, 2=10. (4 bits.)

Bit 0 (LSB):
- 4 has bit 0 = 0. 14 bit 0 = 0. 2 bit 0 = 0. All zero.
- c = 0. c·(n-c) = 0·3 = 0.

Bit 1:
- 4 bit 1 = 0. 14 bit 1 = 1. 2 bit 1 = 1.
- c = 2. c·(n-c) = 2·1 = 2.

Bit 2:
- 4 bit 2 = 1. 14 bit 2 = 1. 2 bit 2 = 0.
- c = 2. c·(n-c) = 2·1 = 2.

Bit 3:
- 4 bit 3 = 0. 14 bit 3 = 1. 2 bit 3 = 0.
- c = 1. c·(n-c) = 1·2 = 2.

Total: 0 + 2 + 2 + 2 = **6**. ✓

----------------------------------------

## Step 5: Why Per-Bit Decomposition Works

Hamming distance is **additive over bit positions**. HD(a, b) = Σ over bits of (1 if a,b differ at that bit, 0 otherwise).

Sum over all pairs:
```
Total = Σ_{pairs (i, j)} HD(nums[i], nums[j])
      = Σ_{pairs} Σ_{bits} [differ at bit b]
      = Σ_{bits} Σ_{pairs} [differ at bit b]
      = Σ_{bits} (number of pairs differing at bit b)
      = Σ_{bits} c_b × (n - c_b)
```

Swapping the summation order lets us count pair-differences per bit. For each bit, only two configurations exist (0 or 1), and mixed pairs are the "differ" pairs.

----------------------------------------

## Step 6: Implementation

```
total = 0
for bit in 0..31:
    c = 0
    for x in nums:
        if (x >> bit) & 1: c++
    total += c * (len(nums) - c)
return total
```

O(n · 32) = O(n). O(1) extra space.

----------------------------------------

## Step 7: Name It

**Per-bit contribution counting** — a staple technique for problems involving bitwise operations over many numbers. Same pattern solves:
- Counting Bits (for individual numbers).
- Single Number III (isolate bits to partition).
- Number of Different Integers in XOR Pairs.

Whenever a problem asks about "sum/count over pairs" with a bit-related per-pair property, try swapping the summation order and counting per-bit.

----------------------------------------

## Step 8: Complexity

Time: **O(n · 32) = O(n)**.
Space: **O(1)**.

Brute force was O(n² · bits). The per-bit trick is quadratic in speedup.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int totalHammingDistance(vector<int>& nums) {
    int total = 0;
    int n = nums.size();
    for (int bit = 0; bit < 32; ++bit) {
        int c = 0;
        for (int x : nums) {
            if ((x >> bit) & 1) c++;
        }
        total += c * (n - c);
    }
    return total;
}
```

Tight. The double loop is O(32n), which is effectively O(n).

----------------------------------------

## Step 10: Follow-up Questions

- **Hamming distance between just two specific numbers.** One XOR + popcount.
- **Weighted Hamming distance (different weights per bit).** Multiply per-bit contribution by the weight.
- **Longest Hamming distance in the list.** Max of c·(n-c) bit contributions? No — that's total pairs. Finding max pair distance requires different structure.
- **All distances below some threshold.** Per-bit contribution doesn't directly help; may need sort and pair exploration.
- **3-bit distance (modulo, generalizations).** Different metric; analyze per-bit contributions with the new distance.
- **Total Hamming distance over all PERMUTED pairs (2n² / 2 pairs).** Multiply by 2 (or handle ordering).
