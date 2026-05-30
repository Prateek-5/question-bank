# Single Number II

**Problem Link:**
<a href="https://leetcode.com/problems/single-number-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/single-number-ii/</a>

**Topic:**
Bit Manipulation

----------------------------------------

## Step 1: Read the Problem

Every element in `nums` appears **exactly three times** except for **one** element, which appears once. Find and return the one element.

Must run in O(n) time and O(1) extra space.

Example: `nums = [2, 2, 3, 2]`. Output: 3.
Example: `nums = [0, 1, 0, 1, 0, 1, 99]`. Output: 99.

----------------------------------------

## Step 2: XOR Doesn't Work Directly (Unlike Single Number I)

**Single Number I**: everything appears twice except one. XOR-ing all gives the unique (since `x XOR x = 0` cancels pairs).

**Single Number II**: everything appears thrice except one. But `x XOR x XOR x = x` — XOR doesn't cancel triples. We'd be left with the XOR of all elements, which is everything combined, not just the unique.

So XOR is out. We need a different trick.

----------------------------------------

## Step 3: Bit-Counting Mod 3

For each bit position (say bit 0, bit 1, ..., bit 31), count how many elements have that bit set.

If the unique element has bit b set, the count at position b is `3k + 1` (k repeats contribute 3k, the unique adds 1).

If the unique element doesn't have bit b set, the count is `3k` (only repeats contribute).

So for each bit, `count % 3` gives us whether the unique element has that bit set (1 if count ≡ 1 mod 3, else 0).

Reconstruct the answer bit by bit.

```
result = 0
for bit in 0..31:
    count = 0
    for x in nums:
        count += (x >> bit) & 1
    if count % 3 == 1:
        result |= (1 << bit)
return result
```

O(n · 32) = O(n) time, O(1) space. Works!

----------------------------------------

## Step 4: Trace

`nums = [0, 1, 0, 1, 0, 1, 99]`. 99 in binary: `1100011`.

For bit 0: count of elements with bit 0 set.
- 0: bit 0 = 0.
- 1: bit 0 = 1. (count: 1.)
- 0: 0.
- 1: 1. (count: 2.)
- 0: 0.
- 1: 1. (count: 3.)
- 99 = 0b1100011: bit 0 = 1. (count: 4.)

count = 4. 4 % 3 = 1. So bit 0 of result is set.

For bit 1: 99 has bit 1 set (1100011). Count of bit 1 across: only 99. Count = 1. 1 % 3 = 1. Set.

For bit 2: 99 has bit 2 = 0. 0s: bit 2 = 0. 1s: bit 2 = 0. Only 99 contributes 0. Count = 0. 0 % 3 = 0. Don't set.

...continuing for each bit, only the bits where 99 has a 1 will set in result.

Final result: 99. ✓

----------------------------------------

## Step 5: The State Machine Trick (Classic Interview Flex)

There's a famous O(n) time, O(1) space approach using two integer variables acting as a **state machine** over each bit independently.

Each bit of each element can be in one of three states relative to "how many times has it been set, mod 3":
- Seen 0 times (or 3 times, 6 times, ...) → "zero".
- Seen 1 time → "one".
- Seen 2 times → "two".

Track these states with two bits per position, across all 32 positions in parallel using two integers `ones` and `twos`:

- `ones`: bit b is 1 if the "count of bit-b set across all numbers so far" ≡ 1 (mod 3).
- `twos`: bit b is 1 if count ≡ 2 (mod 3).
- (If both are 0, count ≡ 0.)

Transitions (for each incoming number `x`):
```
ones = (ones XOR x) AND NOT twos
twos = (twos XOR x) AND NOT ones
```

After processing all numbers, bits where the count is ≡ 1 mod 3 remain in `ones`. Those are the bits of the unique element.

Let me trace the transitions briefly: when x has a 1 at some bit b,
- `ones_new[b] = (ones[b] XOR 1) AND NOT twos[b]`.
- `twos_new[b] = (twos_updated_below XOR 1) AND NOT ones_new[b]`.

The state transitions (zero, one, two) cycle on each 1-seen, giving the mod 3 effect.

This approach is clever but error-prone to explain and memorize. The **bit-counting-mod-3 approach is clearer and equally efficient** for interviews.

----------------------------------------

## Step 6: Clean Bit-Count Implementation

```cpp
int singleNumber(vector<int>& nums) {
    int result = 0;
    for (int bit = 0; bit < 32; ++bit) {
        int count = 0;
        for (int x : nums) {
            count += (x >> bit) & 1;
        }
        if (count % 3 == 1) {
            result |= (1 << bit);
        }
    }
    return result;
}
```

Direct, clear, correct. O(32n) = O(n). O(1) space.

Watch out for **negative numbers**: the sign bit (bit 31 in 32-bit int) needs care. If the unique number is negative, bit 31 has `1`s that should be counted.

```cpp
if (count % 3 == 1) result |= (1 << bit);
```

Setting bit 31 via `1 << 31` in signed int is undefined behavior in C++. Use `1u << 31` and then cast, or use 32-bit unsigned and cast back.

Cleaner: treat bits as unsigned.

```cpp
int singleNumber(vector<int>& nums) {
    unsigned result = 0;
    for (int bit = 0; bit < 32; ++bit) {
        unsigned count = 0;
        for (int x : nums) count += ((unsigned)x >> bit) & 1;
        if (count % 3 == 1) result |= (1u << bit);
    }
    return (int)result;
}
```

----------------------------------------

## Step 7: Name It

**Bit-counting modulo k**, with k = 3 here. Generalizes: if each element appears k times except one appearing once, count each bit mod k.

Related:
- Single Number I (k = 2) → XOR.
- Single Number III (two uniques, rest twice) → XOR + group split by a distinguishing bit.

For **any** k and the "appears k times except one appearing once" variant, the bit-count approach scales directly. The state-machine trick gets more complex for higher k.

----------------------------------------

## Step 8: Complexity

Time: **O(32n) = O(n)**.
Space: **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int singleNumber(vector<int>& nums) {
    int result = 0;
    for (int bit = 0; bit < 32; ++bit) {
        int count = 0;
        for (int x : nums) {
            count += (x >> bit) & 1;
        }
        if (count % 3 == 1) {
            result |= (1 << bit);
        }
    }
    return result;
}
```

For handling negatives safely across all compilers, prefer the unsigned version.

State-machine version (for completeness):

```cpp
int singleNumber(vector<int>& nums) {
    int ones = 0, twos = 0;
    for (int x : nums) {
        ones = (ones ^ x) & ~twos;
        twos = (twos ^ x) & ~ones;
    }
    return ones;
}
```

Elegant but requires believing the state transitions. The bit-count version is easier to explain under pressure.

----------------------------------------

## Step 10: Follow-up Questions

- **All appear k times except one (general k).** Bit-count mod k; same template.
- **All appear 3 times except two appearing once.** More complex — combine with Single Number III-like ideas.
- **Streaming input.** Bit-count works online; maintain running counts per bit.
- **Negative numbers.** Use unsigned carefully or signed-mindful bit operations.
- **Bounded value range.** If values ≤ some V, use a V-sized counting array instead of bit-counting.
- **Find the number that appears exactly twice (rest appear three times).** Different: adjust the count%3 check to == 2.
