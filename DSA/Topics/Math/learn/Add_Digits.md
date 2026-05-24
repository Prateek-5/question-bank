# Add Digits — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Add_Digits.md`](../Add_Digits.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/add-digits/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **A beautiful "closed-form vs simulation" problem.** The lesson: **`n ≡ digit_sum(n) (mod 9)`** — a fact that turns iterative digit-summing into a one-line formula. Knowing this idea (called "casting out nines") is a senior signal.

**Map of this file (9 short sections):**

1. Read the problem
2. The simulation
3. The pivot — observe a pattern
4. Why `mod 9` gives the digital root
5. The closed-form formula
6. Code
7. Trace it
8. Common pitfalls
9. The shape — closed forms beat simulation

---

## 1. Read the problem

Given a non-negative integer `num`, **repeatedly sum its digits until only one digit remains**. Return that digit.

**Examples:**

- `num = 38`: 3 + 8 = 11 → 1 + 1 = 2. Return **2**.
- `num = 0`: already one digit. Return **0**.
- `num = 9`: already one digit. Return **9**.
- `num = 100`: 1 + 0 + 0 = 1. Return **1**.

This single-digit result is called the **digital root** of `num`.

---

## 2. The simulation

Direct loop:

```
while num >= 10:
    s = 0
    while num > 0:
        s += num % 10        # extract least significant digit
        num //= 10
    num = s
return num
```

> **Mini-refresher: extracting digits.**
>
> For a non-negative integer `n`:
> - `n % 10` gives the **last digit**.
> - `n // 10` (integer division) **drops** the last digit.
>
> Repeat: extract, divide, extract, divide... until `n == 0`. That gives all digits in reverse order.

Each pass of the outer while sums digits. Inner is O(log num). Outer is also small — after one pass, num is at most ~9 × number_of_digits. For 32-bit ints, that's at most 81. After one more pass, at most ~18, etc.

Total: O(log num) per pass, just a few passes. Effectively very fast.

But there's an O(1) formula.

---

## 3. The pivot — observe a pattern

Compute the digital root of n for n = 0, 1, 2, ..., 30:

| n | digit_sum once | digital root |
|---|---|---|
| 0 | 0 | 0 |
| 1 | 1 | 1 |
| 2 | 2 | 2 |
| 3 | 3 | 3 |
| 4 | 4 | 4 |
| 5 | 5 | 5 |
| 6 | 6 | 6 |
| 7 | 7 | 7 |
| 8 | 8 | 8 |
| 9 | 9 | 9 |
| 10 | 1 | 1 |
| 11 | 2 | 2 |
| 12 | 3 | 3 |
| ... | ... | ... |
| 17 | 8 | 8 |
| 18 | 9 | 9 |
| 19 | 10 → 1 | 1 |
| 20 | 2 | 2 |
| ... | ... | ... |
| 27 | 9 | 9 |
| 28 | 10 → 1 | 1 |

**Pattern:** the digital root cycles 1, 2, 3, ..., 9, 1, 2, 3, ..., 9, ... starting from n = 1. Position 9, 18, 27, ... give digital root 9 (not 0).

This looks like `(n - 1) mod 9 + 1` for n ≥ 1, with the special case 0 → 0.

---

## 4. Why `mod 9` gives the digital root

> **Mini-refresher: 10 ≡ 1 (mod 9).**
>
> In base 10, the number `n = a_k · 10^k + a_(k-1) · 10^(k-1) + ... + a_1 · 10 + a_0`.
>
> Since `10 ≡ 1 (mod 9)`, also `10^k ≡ 1^k = 1 (mod 9)` for all k.
>
> Therefore: `n ≡ a_k · 1 + a_(k-1) · 1 + ... + a_0 · 1 = (sum of digits) (mod 9)`.
>
> So a number and its DIGIT SUM are CONGRUENT MODULO 9.

This means: every time we replace `n` with its digit sum, we PRESERVE `n mod 9`. Eventually we converge to a single digit. That single digit must equal `n mod 9` — except:

- If `n mod 9 = 0` and `n > 0`: the single digit is 9 (since 9 ≡ 0 mod 9 but is a "single digit").
- If `n = 0`: the single digit is 0.
- Otherwise: the single digit is `n mod 9`.

Combined formula:

```
digital_root(0) = 0
digital_root(n > 0) = 1 + (n - 1) mod 9
```

Verify:
- n = 38: 1 + (37 % 9) = 1 + 1 = 2. ✓
- n = 9: 1 + (8 % 9) = 1 + 8 = 9. ✓
- n = 18: 1 + (17 % 9) = 1 + 8 = 9. ✓
- n = 100: 1 + (99 % 9) = 1 + 0 = 1. ✓

---

## 5. The closed-form formula

Two equivalent forms, both O(1):

**Form A:** `1 + (n - 1) % 9` for `n > 0`, else `0`.

**Form B:**
```
if n == 0: return 0
if n % 9 == 0: return 9
return n % 9
```

Both compute the same value. Form A is more concise. Form B is more readable.

---

## 6. Code

**C++ — closed form:**

```cpp
int addDigits(int num) {
    if (num == 0) return 0;
    return 1 + (num - 1) % 9;
}
```

**C++ — simulation (for completeness):**

```cpp
int addDigits(int num) {
    while (num >= 10) {
        int s = 0;
        while (num > 0) {
            s += num % 10;
            num /= 10;
        }
        num = s;
    }
    return num;
}
```

**Python:**

```python
def addDigits(num):
    if num == 0:
        return 0
    return 1 + (num - 1) % 9
```

**JavaScript:**

```javascript
function addDigits(num) {
    if (num === 0) return 0;
    return 1 + (num - 1) % 9;
}
```

Complexity: **O(1) time, O(1) space.**

---

## 7. Trace it

**n = 38:** `1 + (38 - 1) % 9 = 1 + 37 % 9 = 1 + 1 = 2`. ✓

**n = 9:** `1 + (9 - 1) % 9 = 1 + 8 = 9`. ✓

**n = 0:** special case, return 0.

**n = 99:** `1 + (99 - 1) % 9 = 1 + 98 % 9 = 1 + 8 = 9`. Sanity: 9+9=18, 1+8=9. ✓

**n = 1234:** `1 + 1233 % 9 = 1 + (1233 - 137 × 9) = 1 + 0 = 1`. Sanity: 1+2+3+4=10, 1+0=1. ✓

---

## 8. Common pitfalls

1. **Forgetting the `n == 0` special case.** `1 + (0 - 1) % 9` is `1 + (-1) % 9`, which is language-dependent (Python gives 8, C++ gives -1). Either way wrong.

2. **Using `n % 9` directly.** Works EXCEPT for multiples of 9 (where it gives 0, but the digital root is 9). Use the `1 + (n - 1) % 9` formula.

3. **Treating this as a base-10-only formula.** The formula `1 + (n - 1) mod (b - 1)` generalizes to any base `b`. For binary: `1 + (n - 1) % 1 = 1` always (trivial; binary digital root is 0 or 1).

4. **Trying it on negative numbers.** Digital root is typically defined for non-negative integers only. For negative input, use `|n|` (problem usually rules this out).

5. **Submitting the simulation when O(1) is expected.** Simulation passes LeetCode tests but doesn't demonstrate the math insight. Show the closed form in an interview.

6. **Confusing digital root with digit sum.** Digit sum: one pass (e.g., 38 → 11). Digital root: iterate until single digit (38 → 11 → 2).

---

## 9. The shape — closed forms beat simulation

The pattern:

> **When a problem describes an ITERATIVE PROCESS, ask whether the process has a mathematical SHORTCUT — a closed form, an invariant, or a number-theoretic property.**

| Problem | Iterative description | Closed form / shortcut |
|---|---|---|
| **This problem** | repeatedly sum digits | `1 + (n - 1) % 9` |
| Sum 1 to n | iterate, accumulate | `n(n+1)/2` |
| Count of Matches in Tournament | simulate rounds | `n - 1` (each match eliminates 1 team) |
| Fibonacci-style recursions | iterate | sometimes closed-form via Binet's formula |
| Geometric series sum | iterate | `(r^n - 1)/(r - 1)` |
| Happy Number (LC #202) | iterate digit-square-sum until 1 or cycle | cycle detection (Floyd's) |

**Pattern to internalize:**

> "When a problem starts with 'repeatedly do X until Y,' before coding the loop, look for an invariant or closed form. The exam-quality answer is the formula; the working answer is the loop."

The "casting out nines" trick (`n ≡ digit_sum(n) mod 9`) is a classic — knowing it elevates this problem from "easy simulation" to "elegant one-liner."

---

> **Self-check — the question to ask next time.**
>
> When you face a problem about iteratively summing/manipulating digits, ask:
>
> > **"Is there a number-theoretic invariant (like `mod 9` or `mod (base - 1)`) that lets me compute the answer directly?"**
>
> If yes, you've turned a loop into a formula.

---

## Cross-references

- **Reference card (post-mastery):** [`../Add_Digits.md`](../Add_Digits.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Determine_Color_of_a_Chessboard_Square.md`](./Determine_Color_of_a_Chessboard_Square.md), [`Count_of_Matches_in_Tournament.md`](./Count_of_Matches_in_Tournament.md).
