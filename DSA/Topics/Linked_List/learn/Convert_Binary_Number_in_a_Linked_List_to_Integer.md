# Convert Binary Number in a Linked List to Integer — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Convert_Binary_Number_in_a_Linked_List_to_Integer.md`](../Convert_Binary_Number_in_a_Linked_List_to_Integer.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/convert-binary-number-in-a-linked-list-to-integer/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/convert-binary-number-in-a-linked-list-to-integer/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **A light traversal problem with one beautiful idea: Horner's method.** Computing a number from MSB-first digits with a running accumulator: `value = value * base + new_digit`. Same trick is used in parsing integer strings, evaluating polynomials, and Rabin-Karp string hashing. **Read [`Design_Linked_List.md`](./Design_Linked_List.md) first** for node traversal mechanics.

**Map of this file (8 short sections):**

1. Read the problem
2. The two-pass approach (and its annoyance)
3. The pivot — Horner's method
4. Why Horner's works
5. Code
6. Trace it
7. Common pitfalls
8. The shape — Horner's everywhere

---

## 1. Read the problem

You're given the head of a singly-linked list. Each node's value is **0 or 1**. The list represents a binary number with the **most significant bit at the head**.

Return the integer value of this binary number.

**Examples:**

- `head = [1, 0, 1]` → binary `101` → decimal `5`.
- `head = [0]` → 0.
- `head = [1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]` → a 30-bit number.

The list length is at most 30, so the answer fits in an `int`.

> **Mini-refresher: binary number representation.**
>
> Binary uses base 2. Digit values are 0 and 1. The value of an n-digit binary number `b_(n-1) b_(n-2) ... b_1 b_0` is:
>
> `b_(n-1) · 2^(n-1) + b_(n-2) · 2^(n-2) + ... + b_1 · 2 + b_0`
>
> For binary `101`: `1·4 + 0·2 + 1·1 = 5`. ✓
>
> The leftmost bit (head of our list) is the MOST SIGNIFICANT (largest power of 2).

---

## 2. The two-pass approach (and its annoyance)

The straightforward read: figure out each bit's power of 2.

```
n = length of list                    # Pass 1: count nodes
value = 0
i = 0
cur = head
while cur:
    value += cur.val * (1 << (n - 1 - i))     # bit i contributes 2^(n-1-i)
    cur = cur.next
    i += 1
return value
```

Works. Two passes (one to count, one to accumulate). Need to know n in advance. Slightly fiddly.

Can we do it in ONE pass, without knowing n? Yes — using Horner's method.

---

## 3. The pivot — Horner's method

Suppose we've walked the list so far and accumulated value `V`. We're about to read the next bit `b`. What's the new value?

Imagine the bits processed so far: `b_0 b_1 b_2`. Their value is `b_0 · 4 + b_1 · 2 + b_2`.

Now we add a fourth bit `b_3`. The new number is `b_0 b_1 b_2 b_3`. Its value:

```
b_0 · 8 + b_1 · 4 + b_2 · 2 + b_3
= 2 · (b_0 · 4 + b_1 · 2 + b_2) + b_3
= 2 · V + b_3
```

**Every new bit DOUBLES the running value and ADDS the new bit.** This is **Horner's method** for evaluating polynomials at `x = 2`.

```
value = 0
for each bit b (from MSB to LSB):
    value = 2 * value + b
return value
```

No need to know the length. No powers of 2 to compute. One pass.

> **Mini-refresher: Horner's method for polynomial evaluation.**
>
> Given a polynomial `P(x) = a_0 x^k + a_1 x^(k-1) + ... + a_k`, Horner's evaluates it as:
>
> `P(x) = (((a_0 · x + a_1) · x + a_2) · x + ... ) · x + a_k`
>
> Starting from the highest-order coefficient and applying `value = value * x + next_coefficient` repeatedly.
>
> For our problem: x = 2 (base of binary), coefficients are the bits. Same shape.
>
> Horner's is also used for:
> - Parsing integer strings: `value = 10 * value + (c - '0')` (base 10).
> - Rabin-Karp rolling hash (string matching): treat strings as base-b numbers.
> - Numerical polynomial evaluation in scientific code.

---

## 4. Why Horner's works

The key observation: shifting bits left (multiplying by 2) "makes room" for the next bit.

If we have bits `1, 0, 1` accumulated as `value = 5`, and we receive a new bit `1`:
- Multiply value by 2: `5 → 10`. Now the bit pattern is `1010` (we left-shifted).
- Add the new bit: `10 + 1 = 11`. Bit pattern `1011`. Correct.

Each iteration, we "shift in" a new bit at the right end. The bit-shift operator `<<` makes this explicit:

```
value = (value << 1) | new_bit
```

`<< 1` doubles. `| new_bit` ORs in the new bit at position 0 (the LSB).

---

## 5. Code

**C++:**

```cpp
int getDecimalValue(ListNode* head) {
    int value = 0;
    for (ListNode* cur = head; cur; cur = cur->next) {
        value = (value << 1) | cur->val;
    }
    return value;
}
```

**Python:**

```python
def getDecimalValue(head):
    value = 0
    cur = head
    while cur:
        value = (value << 1) | cur.val
        cur = cur.next
    return value
```

**JavaScript:**

```javascript
function getDecimalValue(head) {
    let value = 0;
    for (let cur = head; cur; cur = cur.next) {
        value = (value << 1) | cur.val;
    }
    return value;
}
```

Complexity: **O(n) time, O(1) space.** One pass.

---

## 6. Trace it

`head = [1, 0, 1, 1]`:

```
value = 0.

Node 1: value = (0 << 1) | 1 = 0 | 1 = 1.        # binary so far: 1
Node 0: value = (1 << 1) | 0 = 2 | 0 = 2.        # binary so far: 10
Node 1: value = (2 << 1) | 1 = 4 | 1 = 5.        # binary so far: 101
Node 1: value = (5 << 1) | 1 = 10 | 1 = 11.      # binary so far: 1011

Return 11.   ✓   (binary 1011 = 8 + 2 + 1 = 11)
```

Notice the running value tracks the binary number "built so far":
- After 1 bit: `1` = 1.
- After 2 bits: `10` = 2.
- After 3 bits: `101` = 5.
- After 4 bits: `1011` = 11.

Each step shifts left and ORs in the new bit. Horner's in action.

---

## 7. Common pitfalls

1. **Computing `pow(2, i)` for each bit.** Works but wasteful (`pow` is floating-point in C++). Horner's eliminates the need.

2. **Forgetting the MSB-at-head convention.** The problem specifies MSB at the head. If the spec were LSB at head, you'd need a different formula (track power explicitly, or reverse the list first).

3. **Using `+` instead of `|` or `+` instead of `* 2 + bit`.** All work in this problem (since bits are 0 or 1, `2*value + bit` and `(value << 1) | bit` are identical). For OTHER bases, you'd use `value = base * value + digit`.

4. **Off-by-one on the loop.** Process EVERY node, not "size - 1." A single-node list with value 1 should give value 1, not 0.

5. **Forgetting to traverse — using the head value only.** The head is just one bit. You must walk to the tail.

6. **Initializing `value = 1` instead of `value = 0`.** Off by ... a lot. Start at 0 — the empty prefix has value 0.

7. **Overflow for very long lists.** Problem says at most 30 bits → fits in int. For longer, use `long long` or big-integer.

---

## 8. The shape — Horner's everywhere

Horner's method appears wherever you're CONSTRUCTING a value from a stream of MSB-first digits/coefficients.

| Problem | Base | Digits |
|---|---|---|
| **This problem** | 2 (binary) | 0, 1 |
| Parsing integer strings (e.g., "12345") | 10 | 0-9 |
| Parsing hex strings | 16 | 0-9, a-f |
| Evaluating a polynomial | x (variable) | coefficients |
| Rabin-Karp rolling hash | prime base | string char codes |
| Base conversion in general | any b | 0..b-1 |
| Continued fractions (variant) | varies | varies |

**Pattern to internalize:**

> "MSB-first digits + running accumulator + 'value = base · value + new digit' = Horner's method. O(n) time, O(1) space, no powers needed."

The recognition cue: "given digits in MSB-first order, compute the value."

---

> **Self-check — the question to ask next time.**
>
> When you face "convert MSB-first digit stream to an integer," ask:
>
> > **"Can I use Horner's method: maintain a running accumulator, and for each new digit do `value = base * value + digit`?"**
>
> If yes, one pass, no powers, no length-counting.

---

## Cross-references

- **Reference card (post-mastery):** [`../Convert_Binary_Number_in_a_Linked_List_to_Integer.md`](../Convert_Binary_Number_in_a_Linked_List_to_Integer.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Design_Linked_List.md`](./Design_Linked_List.md), [`Reverse_Linked_List.md`](./Reverse_Linked_List.md) — traversal mechanics.
  - Topic complete! Next topic: Searching_Binary_Search.
