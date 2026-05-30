# Single Number — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Single_Number.md`](../Single_Number.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/single-number/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/single-number/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The introduction to XOR algebra.** The lesson: **`x XOR x = 0` and XOR is commutative + associative — so XORing pairs cancels.** When you need O(n) time AND O(1) space and the structure has "pairs cancel," XOR is the tool.

**Map of this file (9 short sections):**

1. Read the problem
2. The obvious approaches (and why they fail constraints)
3. The XOR insight
4. XOR's four key properties
5. Code
6. Trace it
7. Common pitfalls
8. Why XOR is uniquely suited
9. The shape — XOR algebra family

---

## 1. Read the problem

Given a non-empty array `nums` of integers where **every element appears EXACTLY TWICE, except for one element that appears ONCE**, find the singleton.

**Required:** O(n) time AND O(1) space.

**Examples:**

- `[2, 2, 1]` → **1**.
- `[4, 1, 2, 1, 2]` → **4**.
- `[1]` → **1**.

The two constraints together are what make this interesting. Without O(1) space, a hashmap solves it trivially. Without O(n) time, sorting solves it.

---

## 2. The obvious approaches (and why they fail constraints)

**Hashmap:** count occurrences; return the one with count 1.
- Time: O(n). Space: O(n). **Fails O(1) space.**

**Sort + scan:** sort `nums`; scan adjacent pairs; the singleton is unpaired.
- Time: O(n log n). Space: O(1) for in-place sort. **Fails O(n) time.**

**Math (sum * 2 - total):** `2 * sum(set(nums)) - sum(nums) = singleton`.
- Time: O(n). Space: O(n) for the set. **Fails O(1) space.**

We need O(n) time AND O(1) space. The trick: **XOR**.

---

## 3. The XOR insight

> **Mini-refresher: XOR's behavior on duplicates.**
>
> - `x XOR x = 0` (any value XOR'd with itself yields 0).
> - `x XOR 0 = x` (XOR with 0 is identity).
>
> Combined: XORing any value an EVEN number of times gives 0. An ODD number of times gives that value.
>
> So if we XOR all elements in `nums`: every "appears twice" element cancels itself to 0, and the singleton (appearing once) is XOR'd in once. Result: the singleton.

**Algorithm:**

```
result = 0
for x in nums:
    result ^= x
return result
```

One pass, single accumulator. **O(n) time, O(1) space.**

---

## 4. XOR's four key properties

> **Mini-refresher: the four XOR properties.**
>
> 1. **Closed:** `a XOR b` is an integer.
> 2. **Commutative:** `a XOR b = b XOR a`.
> 3. **Associative:** `(a XOR b) XOR c = a XOR (b XOR c)`.
> 4. **Self-inverse:** `a XOR a = 0`. Identity: `a XOR 0 = a`.
>
> These four make XOR a **group operation** with identity 0. So XORing a sequence is order-independent.

For our problem: XOR the entire array. We can mentally REARRANGE so duplicates are adjacent:

`4 XOR 1 XOR 2 XOR 1 XOR 2` = `4 XOR (1 XOR 1) XOR (2 XOR 2)` = `4 XOR 0 XOR 0` = **4**.

The actual processing order doesn't matter (associativity + commutativity). The duplicates cancel; the singleton survives.

---

## 5. Code

**C++:**

```cpp
int singleNumber(vector<int>& nums) {
    int result = 0;
    for (int x : nums) {
        result ^= x;
    }
    return result;
}
```

**Python:**

```python
def singleNumber(nums):
    result = 0
    for x in nums:
        result ^= x
    return result
```

Or with `reduce`:

```python
from functools import reduce
from operator import xor

def singleNumber(nums):
    return reduce(xor, nums, 0)
```

**JavaScript:**

```javascript
function singleNumber(nums) {
    let result = 0;
    for (const x of nums) {
        result ^= x;
    }
    return result;
}
```

Complexity: **O(n) time, O(1) space.**

---

## 6. Trace it

**`nums = [4, 1, 2, 1, 2]`:**

```
result = 0.
After x=4: result = 0 XOR 4 = 4.
After x=1: result = 4 XOR 1 = 5.
After x=2: result = 5 XOR 2 = 7.
After x=1: result = 7 XOR 1 = 6.
After x=2: result = 6 XOR 2 = 4.

Return 4.  ✓
```

The intermediate values (4, 5, 7, 6) are meaningless — they don't represent anything. Only the FINAL XOR equals the singleton.

**`nums = [2, 2, 1, 4, 4, 3, 3]` → singleton = 1:**

```
0 XOR 2 = 2
2 XOR 2 = 0
0 XOR 1 = 1
1 XOR 4 = 5
5 XOR 4 = 1
1 XOR 3 = 2
2 XOR 3 = 1

Return 1.  ✓
```

---

## 7. Common pitfalls

1. **Trying to use `+` or `*`.** Addition doesn't have `a + a = 0`; can't cancel pairs.

2. **Trying to use a set.** Works but O(n) space. Violates constraints.

3. **Returning 0 by accident.** If you initialize `result` correctly to 0 and XOR everything, you should NEVER return 0 (unless the singleton is itself 0, which is valid).

4. **Sorting first.** O(n log n). Defeats the O(n) requirement.

5. **Trying to use addition + a hash for tracking.** Same hash issue — O(n) space.

6. **Misreading "twice" as "exactly twice or more."** The problem says EXACTLY twice. If elements could appear more times, XOR's behavior changes.

7. **Not understanding why intermediate XORs are nonsense.** Only the FINAL XOR is meaningful. Don't try to "decode" intermediate values.

---

## 8. Why XOR is uniquely suited

> **Mini-refresher: comparing operations.**
>
> | Operation | Commutative? | Associative? | `op(x, x) = identity`? |
> |---|---|---|---|
> | `+` | yes | yes | no (`x + x = 2x`) |
> | `*` | yes | yes | no (`x * x = x²`) |
> | `-` | no | no | yes (`x - x = 0`) but messes up order |
> | `XOR` | yes | yes | YES (`x XOR x = 0`) |
>
> XOR is the ONLY common arithmetic operation that's both order-independent (commutative + associative) AND has the "self-cancellation" property.

This combination is rare and powerful. It's the reason XOR shows up in cryptography, error correction, hashing, and these "find the odd-one-out" problems.

---

## 9. The shape — XOR algebra family

XOR-based problems:

| Problem | Use |
|---|---|
| **This problem** | XOR all → singleton |
| Single Number II (each appears 3x except one) | XOR doesn't directly work; bit-count mod 3 |
| Single Number III (two singletons) | XOR all → `a XOR b`; partition by a distinguishing bit |
| Missing Number in `[0, n]` | XOR `[0..n]` and the array; result is the missing one |
| Find the Duplicate Number (one duplicate) | XOR + structural tricks (or Floyd) |
| Hamming Distance | `popcount(a XOR b)` |
| Encrypt a value with a key | `cipher = plaintext XOR key`, decrypt with same XOR |

**Pattern to internalize:**

> "When elements come in pairs (or k-groups) and you need an odd-one-out in O(n) time + O(1) space, XOR them all. Pairs cancel; the odd-one survives."

The technique extends with bit-counting (Single Number II) or partitioning (Single Number III). XOR is the foundation.

---

> **Self-check — the question to ask next time.**
>
> When you face "find the unique element among duplicates" with tight time/space constraints, ask:
>
> > **"Do pairs CANCEL under some operation? If XOR, then XOR everything and the singleton emerges."**
>
> If yes, O(n) time, O(1) space, one-line solution.

---

## Cross-references

- **Reference card (post-mastery):** [`../Single_Number.md`](../Single_Number.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_1_Bits.md`](./Number_of_1_Bits.md), [`Reverse_Bits.md`](./Reverse_Bits.md) — other bit problems.
  - Coming next: [`Single_Number_II.md`](./Single_Number_II.md) — same idea, with triples.
