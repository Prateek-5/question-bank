# Single Number

**Problem Link:**
<a href="https://leetcode.com/problems/single-number/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/single-number/</a>

**Topic:**
Bit Manipulation

----------------------------------------

## Step 1: Understand the Setup

Given a non-empty integer array where every element appears **twice**, except for **one** element which appears just once — find that unique element. The solution should run in linear time and use constant extra memory.

Example: `[4, 1, 2, 1, 2]` → answer is `4` (1 and 2 each appear twice; 4 once).

Two constraints make this interesting: O(n) time and O(1) space. If we could use O(n) space, a hashmap would solve it instantly. We can't. So we need to be clever.

----------------------------------------

## Step 2: First Ideas (Before Cleverness)

**Sorting approach:** sort the array, then pairs of duplicates will sit next to each other. Walk the array and find the position where a number doesn't equal its neighbor. Works. O(n log n) time, O(1) space (or O(n) if the sort isn't in-place). Misses the linear-time requirement.

**Hashmap approach:** count occurrences, return the one with count 1. O(n) time, O(n) space. Misses the constant-space requirement.

So both obvious approaches fail one constraint. We need a fundamentally different trick.

----------------------------------------

## Step 3: Hunt for an Invariant

What property of pairs would let me "cancel them out" as I sweep through the array? I need an operation `op` such that `op(x, x) = identity` — where the identity doesn't affect further combinations.

Subtraction: `x - x = 0`. But `0 + y != y + y` in a useful sense. Doesn't chain well.

Addition: `x + x = 2x`, not zero. Also tricky.

XOR: `x XOR x = 0`. And `0 XOR y = y`. That's promising. Plus, XOR is commutative and associative, so the order of combination doesn't matter.

So if I XOR everything together, every pair cancels (because `x XOR x = 0`), and what remains is `0 XOR unique = unique`.

This is the insight. Let me verify on the example.

`4 XOR 1 XOR 2 XOR 1 XOR 2`

Rearrange (using commutativity): `4 XOR (1 XOR 1) XOR (2 XOR 2) = 4 XOR 0 XOR 0 = 4`.

Answer: 4. ✓

----------------------------------------

## Step 4: Why XOR Is the Right Operation

Let me be precise about XOR's properties:

1. **Associative:** `(a XOR b) XOR c = a XOR (b XOR c)`.
2. **Commutative:** `a XOR b = b XOR a`.
3. **Self-inverse:** `a XOR a = 0`.
4. **Identity:** `a XOR 0 = a`.

Because XOR is commutative and associative, XORing all `n` numbers is equivalent to XORing them in *any* order. I can rearrange so all the duplicates are adjacent, cancel them to 0, and the remaining singleton is the final result.

No other common arithmetic operation has all four properties. Addition is commutative and associative, but `a + a ≠ 0`. Multiplication is too. Subtraction isn't associative. XOR is uniquely suited here.

----------------------------------------

## Step 5: The Algorithm in One Line

```cpp
int result = 0;
for (int x : nums) result ^= x;
return result;
```

Three lines of code. One pass. No extra data structures.

Reading it: `result` accumulates the running XOR. Every paired element contributes nothing (its two appearances cancel). The unique element contributes its value once.

----------------------------------------

## Step 6: Trace on a Slightly Longer Example

`[2, 2, 1, 4, 4, 3, 3]` → expected unique = 1.

```
result = 0
After 2: 0 ^ 2 = 2
After 2: 2 ^ 2 = 0
After 1: 0 ^ 1 = 1
After 4: 1 ^ 4 = 5
After 4: 5 ^ 4 = 1
After 3: 1 ^ 3 = 2
After 3: 2 ^ 3 = 1
```

Final result: 1. ✓

Notice how the intermediate values bounce around — they don't represent anything meaningful. Only the *final* result is the answer. That's OK; the invariant (XOR of processed elements so far) only reveals the unique value once everything's been XOR'd in.

----------------------------------------

## Step 7: Why O(n) Time and O(1) Space

Time: one pass of XORs, each O(1). **O(n)**.
Space: a single accumulator integer. **O(1)**.

Exactly what the problem asked for, and the XOR trick is what makes it possible.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int singleNumber(vector<int>& nums) {
    int result = 0;
    for (int x : nums) result ^= x;
    return result;
}
```

That's the entire solution.

----------------------------------------

## Step 9: Follow-up Questions

- **Single Number II:** every element appears three times except one (which appears once). XOR alone doesn't work because `x XOR x XOR x = x`. Solution: bit-count each bit mod 3, or use a state machine with two accumulators.
- **Single Number III:** two unique elements, rest appear twice. First XOR everything → you get `a XOR b` where `a, b` are the two unique. Find any bit where `a XOR b` is 1 (they differ there). Partition the array by that bit; XOR each partition separately — one gives `a`, the other gives `b`.
- **Missing number in `[0, n]`.** Similar XOR idea: XOR all numbers 0 through n, XOR all array elements, XOR the two — the missing number pops out.
- **Find the element appearing more than n/2 times (majority).** Boyer-Moore voting — a similar O(n) time, O(1) space trick, but with a counter-based approach rather than XOR.
- **If the array is streaming (you can't re-read).** XOR still works — accumulate on the fly.
