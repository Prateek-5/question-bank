# Convert Binary Number in a Linked List to Integer

**Problem Link:**
<a href="https://leetcode.com/problems/convert-binary-number-in-a-linked-list-to-integer/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/convert-binary-number-in-a-linked-list-to-integer/</a>

**Topic:**
Linked List

----------------------------------------

## Step 1: What Are We Given?

A singly linked list where each node's value is 0 or 1. The list represents a **binary number**, with the **most significant bit (MSB) at the head** and the least significant bit at the tail.

Example: `head = [1, 0, 1]`.
- Binary: 101.
- Decimal: 1·4 + 0·2 + 1·1 = **5**.

Example: `head = [0]` → 0. `head = [1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]` → a big 30-bit number.

Return the integer value.

----------------------------------------

## Step 2: First Instinct — Count Nodes, Then Use Powers

One obvious approach:
1. Walk the list once to count length n.
2. Walk again; for position i (0-indexed from head), contribute `val_i · 2^(n-1-i)`.

Works. Two passes, and we need to track both a position and a power.

Can we do it in **one pass**?

----------------------------------------

## Step 3: The Horner's Method Reformulation

Think about building up the number as we traverse. Suppose we've read bits `b_0 b_1 b_2` so far (in MSB-first order). Their value is:

```
b_0 · 4 + b_1 · 2 + b_2
```

Now we read a fourth bit `b_3`. The new value is:

```
b_0 · 8 + b_1 · 4 + b_2 · 2 + b_3
= 2 · (b_0 · 4 + b_1 · 2 + b_2) + b_3
= 2 · (old_value) + new_bit
```

**Each new bit doubles the running value and adds the new bit's contribution.** This is exactly **Horner's method** for evaluating polynomials at x = 2.

So: one pass, starting from value 0, for each node do `value = 2 * value + node->val`. Done.

----------------------------------------

## Step 4: Algorithm

```
value = 0
node = head
while node:
    value = 2 * value + node.val
    node = node.next
return value
```

One pass. O(n) time, O(1) space. No need to know the length in advance.

A bit-shift version is equivalent: `value = (value << 1) | node.val`. Cleaner in C/C++ where bit ops are idiomatic.

----------------------------------------

## Step 5: Trace

`head = [1, 0, 1]`:

```
value = 0.
Node 1: value = 2·0 + 1 = 1.     # 1
Node 0: value = 2·1 + 0 = 2.     # 10
Node 1: value = 2·2 + 1 = 5.     # 101
```

Return **5**. ✓

Try `head = [1, 0, 1, 1]`:
```
value = 0.
Node 1: value = 1.
Node 0: value = 2.
Node 1: value = 5.
Node 1: value = 11.     # 1011 = 11. ✓
```

----------------------------------------

## Step 6: Why Horner's Is the Right Frame

A number in base b is a polynomial in b: `b_0·b^k + b_1·b^(k-1) + ... + b_k`. Evaluating polynomials left-to-right (MSB first) is exactly Horner's rule:

```
P(x) = ((...(b_0 · x + b_1) · x + b_2) · x + ...) · x + b_k
```

For binary, x = 2 — the "shift left and OR" idiom is Horner's in disguise. This trick works for **any base**: decimal strings, hex, arbitrary.

It also avoids computing explicit powers of 2 — no `pow` calls, no overflow risk from large powers multiplied with zero bits.

----------------------------------------

## Step 7: Name It

**Horner's method** (for polynomial / base-conversion evaluation). A foundational technique.

Applications:
- Parsing integer strings: `num = 10 * num + (c - '0')`.
- Evaluating polynomials in numerical code.
- Rolling hashes in string matching (Rabin-Karp: treat strings as base-b numbers).
- This problem: LSB-first stream requires a different framing; MSB-first is Horner-friendly.

----------------------------------------

## Step 8: Complexity

Time: **O(n)** where n is the number of nodes.
Space: **O(1)** extra.

----------------------------------------

## Step 9: C++ Implementation

```cpp
struct ListNode { int val; ListNode* next; };

int getDecimalValue(ListNode* head) {
    int value = 0;
    for (ListNode* cur = head; cur; cur = cur->next) {
        value = (value << 1) | cur->val;
    }
    return value;
}
```

`<<` doubles the running value; `|` sets the low bit to the current node's value. Equivalent to `value = 2 * value + cur->val` and often compiled identically, but reads cleanly as "shift in the next bit."

----------------------------------------

## Step 10: Follow-up Questions

- **LSB at the head instead of MSB.** Reverse the linked list first, or track `2^i` as you walk and sum `val · 2^i`.
- **Very long binary (more bits than int).** Use `long long` or big-integer library.
- **Arbitrary base (e.g., base 10 as a linked list of digits).** Same recurrence: `value = base * value + digit`.
- **Produce the binary string from an int.** Opposite direction; bit-shift out and prepend '0' or '1'.
- **Detect overflow.** Before the multiply, check if `value > INT_MAX / 2`. Safer: accumulate in 64-bit and cast at the end.
- **Why not count length first and use `pow(2, n-1-i)`?** Two passes and floating-point inaccuracies for large n. Horner is one pass, integer-only.
