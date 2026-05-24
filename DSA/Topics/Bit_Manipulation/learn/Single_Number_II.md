# Single Number II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Single_Number_II.md`](../Single_Number_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/single-number-ii/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: when XOR's "pairs cancel" doesn't apply, fall back to counting individual BITS modulo k.** For "appears k times except one," count each bit-position's appearances across all numbers, take mod k, reconstruct. **Read [`Single_Number.md`](./Single_Number.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. Why XOR alone doesn't work
3. The bit-counting insight
4. The algorithm
5. Code
6. Trace it
7. The state-machine alternative (advanced)
8. Common pitfalls
9. The shape — generalizing "find the odd-frequency element"

---

## 1. Read the problem

Given a non-empty integer array `nums` where **every element appears EXACTLY THREE TIMES except for one element that appears ONCE**, find the singleton.

**Required:** O(n) time, O(1) extra space.

**Examples:**

- `[2, 2, 3, 2]` → **3**.
- `[0, 1, 0, 1, 0, 1, 99]` → **99**.

---

## 2. Why XOR alone doesn't work

In Single Number I (appears 2x except one), XOR works because `x XOR x = 0` (pairs cancel).

In Single Number II (appears 3x except one):
- `x XOR x XOR x = x`. **Triples DON'T cancel.**

If we XOR everything: each "triple-element" contributes `x XOR x XOR x = x` once to the XOR. The singleton contributes once. Result: XOR of (each-triple-element) and (the singleton). Not the singleton alone.

So XOR fails. We need a different technique.

---

## 3. The bit-counting insight

> **Mini-refresher: bits and modular counting.**
>
> Look at each BIT POSITION separately. For each bit b (0 through 31):
> - Across all elements that have bit b set, count how many elements they are.
> - Each "triple-element" with bit b set contributes 3 to this count.
> - The singleton contributes 0 or 1 to this count (depending on whether IT has bit b set).
>
> Total count at bit b = `3 * (count of triples with bit b set) + (singleton's bit b)`.
>
> Taking MOD 3: `total % 3` = singleton's bit b. (3 * anything mod 3 = 0; only the singleton's contribution survives.)

So: for each bit position, count occurrences, take mod 3 — that gives the singleton's bit at that position. Reconstruct the singleton bit-by-bit.

> **Mini-refresher: extracting and setting bits.**
>
> - To CHECK if `x` has bit `b` set: `(x >> b) & 1`.
> - To SET bit `b` in `result`: `result |= (1 << b)`.

---

## 4. The algorithm

```
result = 0
for bit in 0..31:
    count = 0
    for x in nums:
        count += (x >> bit) & 1     # count elements with bit `bit` set
    if count % 3 == 1:
        result |= (1 << bit)         # singleton has this bit set
return result
```

Time: O(32 · n) = O(n). Space: O(1). Meets the constraints.

---

## 5. Code

**C++:**

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

Careful with bit 31 (the sign bit). In C++ signed types, `1 << 31` is implementation-defined / UB depending on standard. Safer:

```cpp
int singleNumber(vector<int>& nums) {
    unsigned result = 0;
    for (int bit = 0; bit < 32; ++bit) {
        unsigned count = 0;
        for (int x : nums) count += ((unsigned)x >> bit) & 1u;
        if (count % 3 == 1) result |= (1u << bit);
    }
    return (int)result;
}
```

**Python** (arbitrary precision; no sign-bit issues):

```python
def singleNumber(nums):
    result = 0
    for bit in range(32):
        count = sum(((x >> bit) & 1) for x in nums)
        if count % 3 == 1:
            result |= (1 << bit)
    # Handle negative result (if singleton is negative)
    if result >= (1 << 31):
        result -= (1 << 32)
    return result
```

The Python tail-fix handles the case where the singleton is negative (Python integers are unbounded; LeetCode expects 32-bit signed representation).

**JavaScript:**

```javascript
function singleNumber(nums) {
    let result = 0;
    for (let bit = 0; bit < 32; bit++) {
        let count = 0;
        for (const x of nums) count += (x >> bit) & 1;
        if (count % 3 === 1) result |= (1 << bit);
    }
    return result;
}
```

Complexity: **O(n) time, O(1) space.**

---

## 6. Trace it

**`nums = [0, 1, 0, 1, 0, 1, 99]`** → expected singleton: **99** (binary: `1100011`).

For each bit, count occurrences across nums and check `mod 3`:

| Bit | Bit values across nums (0, 1, 0, 1, 0, 1, 99) | Sum | Sum % 3 | Set in result? |
|---|---|---|---|---|
| 0 | 0, 1, 0, 1, 0, 1, 1 | 4 | 1 | YES |
| 1 | 0, 0, 0, 0, 0, 0, 1 | 1 | 1 | YES |
| 2 | 0, 0, 0, 0, 0, 0, 0 | 0 | 0 | no |
| 3 | 0, 0, 0, 0, 0, 0, 0 | 0 | 0 | no |
| 4 | 0, 0, 0, 0, 0, 0, 0 | 0 | 0 | no |
| 5 | 0, 0, 0, 0, 0, 0, 1 | 1 | 1 | YES |
| 6 | 0, 0, 0, 0, 0, 0, 1 | 1 | 1 | YES |
| 7+ | all 0 | 0 | 0 | no |

Result has bits 0, 1, 5, 6 set: `1100011` binary = **99**. ✓

(Note: 99 = 64 + 32 + 2 + 1 = bits 0, 1, 5, 6.)

---

## 7. The state-machine alternative (advanced)

There's an O(n) time, O(1) space solution using TWO integer accumulators acting as a per-bit state machine:

```
ones, twos = 0, 0
for x in nums:
    ones = (ones XOR x) AND NOT twos
    twos = (twos XOR x) AND NOT ones
return ones
```

**How it works:** for each bit position, the state cycles `00 → 01 → 10 → 00` as that bit is "seen" 1, 2, 3 times. `ones` and `twos` together track the count mod 3 per bit, in parallel for all 32 bits.

After processing all numbers, `ones` has 1s exactly at the positions where the count was 1 mod 3 — the singleton's bits.

This is elegant but extremely error-prone to derive on the spot. In interviews, the bit-counting approach is more defensible.

> **Mini-refresher: state machine intuition (skim if confused).**
>
> Per bit, "how many times has the value 1 appeared mod 3" goes through three states:
> - State 0: seen 0 (or 3, 6, ...) times.
> - State 1: seen 1 time.
> - State 2: seen 2 times.
>
> Encoded with two bits: `(ones, twos) = (0,0), (1,0), (0,1)` for states 0, 1, 2.
>
> The update equations track these transitions for ALL 32 bits in parallel. Show this if asked; otherwise use bit counting.

---

## 8. Common pitfalls

1. **Trying XOR.** XOR triples don't cancel. See Section 2.

2. **Forgetting to handle negative numbers.** In Python, bit 31 set means the number is "negative" in 32-bit signed semantics. Adjust if needed.

3. **Off-by-one in mod 3 check.** `count % 3 == 1` (singleton has this bit set). Not `== 2`.

4. **Using bit-by-bit but iterating 32 times INSIDE the array loop.** Reverse the loops if it confuses you, but the standard order (bit outer, nums inner) is fine.

5. **Memorizing the state-machine version without understanding.** Will fail in interviews when you can't explain. Use bit-counting.

6. **C++ undefined behavior with `1 << 31`.** Use unsigned types or `(int)(1u << 31)`.

7. **Confusing this with Single Number III (two singletons).** Different problem; different technique.

---

## 9. The shape — generalizing "find the odd-frequency element"

The bit-counting approach generalizes to ANY "appears k times except one":

| k | XOR works? | Bit-count |
|---|---|---|
| 2 (Single Number I) | YES | mod 2 (same as XOR per bit) |
| 3 (this problem) | no | mod 3 |
| 4 | no | mod 4 |
| general k | only if k = 2 | mod k |

**Pattern to internalize:**

> "When 'every element appears k times except one,' COUNT THE BITS MOD K. The remaining counts reveal the singleton's bits. O(n) time, O(1) space."

XOR (mod 2) is just the k=2 special case where binary addition gives this automatically. For general k, do explicit counting.

---

> **Self-check — the question to ask next time.**
>
> When you face "find the element with a UNIQUE frequency among a uniform-frequency rest," ask:
>
> > **"For each bit position, count occurrences across all numbers, take mod k (the rest's frequency). The remainder reveals the singleton's bits."**
>
> If yes, you have a general O(n) bit-counting solution.

---

## Cross-references

- **Reference card (post-mastery):** [`../Single_Number_II.md`](../Single_Number_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Single_Number.md`](./Single_Number.md) — the k=2 case.
  - Topic complete! Next: Queues_Deque_Monotonic_Queue.
