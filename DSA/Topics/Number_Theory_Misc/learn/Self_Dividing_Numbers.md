# Self Dividing Numbers — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Self_Dividing_Numbers.md`](../Self_Dividing_Numbers.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/self-dividing-numbers/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/self-dividing-numbers/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **The lesson: digit-extraction loop via `% 10` and `/ 10`. Check the property per digit; reject digit == 0 (division by zero).**

**Map of this file (7 sections):**

1. Read the problem
2. The digit-extraction loop
3. Code
4. Trace it
5. Edge cases (zero digit)
6. Common pitfalls
7. The shape — digit-property check

---

## 1. Read the problem

A number is SELF-DIVIDING if it's divisible by EACH of its digits. No digit can be 0 (else division by zero). Return all self-dividing numbers in `[left, right]`.

**Example:** left=1, right=22 → `[1,2,3,4,5,6,7,8,9,11,12,15,22]`.

---

## 2. The digit-extraction loop

> **Mini-refresher: extract digits right-to-left with `% 10` and `/ 10`.**
>
> ```
> while n > 0:
>     d = n % 10        # rightmost digit
>     n /= 10           # drop it
>     ...check d...
> ```
>
> Test `original % d == 0` for each digit. Reject if d == 0.

We keep the ORIGINAL value to test divisibility — `n` itself is shrinking each iteration.

---

## 3. Code

**C++:**

```cpp
class Solution {
    bool isSelfDividing(int n) {
        int original = n;
        while (n > 0) {
            int d = n % 10;
            if (d == 0 || original % d != 0) return false;
            n /= 10;
        }
        return true;
    }
public:
    vector<int> selfDividingNumbers(int left, int right) {
        vector<int> result;
        for (int n = left; n <= right; ++n) {
            if (isSelfDividing(n)) result.push_back(n);
        }
        return result;
    }
};
```

Complexity: O((right - left) · log max) time, O(output) space.

---

## 4. Trace it

n = 128:
- d = 8, 128 % 8 = 0. n = 12.
- d = 2, 128 % 2 = 0. n = 1.
- d = 1, 128 % 1 = 0. n = 0.
- Return true.

n = 26: d = 6, 26 % 6 = 2 ≠ 0 → false.

n = 102: d = 2 OK, n = 10. d = 0 → false.

---

## 5. Edge cases (zero digit)

- **Digits 1-9:** any single digit n is self-dividing (n % n = 0).
- **Any n containing 0:** always fails (division by zero would be undefined).
- **Large n:** `int` is fine for typical constraints (≤ 10^4 here).

---

## 6. Common pitfalls

1. **Dividing by `n` (the shrinking value) instead of `original`.** Loses the original number.
2. **Forgetting the d == 0 check.** Causes division by zero / undefined behavior.
3. **Returning false too eagerly.** Each digit must pass; only one failure rejects.
4. **Using string conversion.** Works but slower; the arithmetic loop is cleaner.

---

## 7. The shape — digit-property check

The pattern: **iterate digits via `% 10` and `/ 10`; check the property per digit.**

| Problem | Per-digit check |
|---|---|
| **This problem** | original % d == 0, d ≠ 0 |
| Sum of digits | accumulate d |
| Product of digits | multiply d |
| Reverse a number | build result digit-by-digit |
| Palindrome number | compare reversed half |
| Armstrong number | sum of d^k = n |
| Happy Number | sum of d² iterated |

**Pattern to internalize:**

> "Digit problems: extract via `% base` and `/ base`. Per-digit check or accumulation. O(log n) per number."

---

> **Self-check — the question to ask next time.**
>
> When you need to check a per-digit property:
>
> > **"Loop while n > 0: d = n % 10, process d, n /= 10. Handle d == 0 if division might happen."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Self_Dividing_Numbers.md`](../Self_Dividing_Numbers.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Lucky_Numbers_in_a_Matrix.md`](./Lucky_Numbers_in_a_Matrix.md), [`Subtract_Product_and_Sum_of_Digits.md`](./Subtract_Product_and_Sum_of_Digits.md), [`Number_of_Good_Pairs.md`](./Number_of_Good_Pairs.md).
