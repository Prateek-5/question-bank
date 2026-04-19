# Self Dividing Numbers

**Problem Link:**
https://leetcode.com/problems/self-dividing-numbers/

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: Understand the Definition

A **self-dividing number** is a number that is divisible by **every one of its digits**.

Additionally, a self-dividing number cannot contain the digit **0** (division by zero is undefined).

Example: 128 is self-dividing because 128 % 1 = 0, 128 % 2 = 0, 128 % 8 = 0.
Example: 102 contains 0; not self-dividing.
Example: 26 is not self-dividing (26 % 2 = 0 but 26 % 6 ≠ 0).

Given `left` and `right`, return all self-dividing numbers in `[left, right]` (inclusive).

Example: left = 1, right = 22. Output: [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 15, 22].

----------------------------------------

## Step 2: For Each Number, Check Digits

For each candidate n in [left, right]:
1. Extract digits of n.
2. If any digit is 0, fail.
3. Else, check if n % digit == 0 for each digit.
4. If all pass, add to result.

Digit extraction: keep dividing by 10, examining `% 10`.

```
def isSelfDividing(n):
    original = n
    while n > 0:
        d = n % 10
        if d == 0 or original % d != 0: return False
        n //= 10
    return True

result = [n for n in [left, right] if isSelfDividing(n)]
```

O((right - left) · log(max)). For right ≤ 10^4, this is fast.

----------------------------------------

## Step 3: Trace

For n = 128:
- d = 128 % 10 = 8. 128 % 8 = 0. OK. n becomes 12.
- d = 2. 128 % 2 = 0. OK. n becomes 1.
- d = 1. 128 % 1 = 0. OK. n becomes 0. Loop ends.
- Return true.

For n = 26:
- d = 6. 26 % 6 = 2. Not 0. Return false.

For n = 102:
- d = 2. 102 % 2 = 0. OK. n becomes 10.
- d = 0. Return false.

----------------------------------------

## Step 4: Edge Cases

- **Single-digit numbers (1-9).** Self-dividing trivially (n % n == 0).
- **Numbers containing 0.** Always fail.
- **Large numbers.** Up to 10^9 works with a `long long` but the digit loop is fast.

The digit-by-digit check naturally handles all cases.

----------------------------------------

## Step 5: Name It

**Digit-based checking on integers.** A foundational pattern for problems involving digit properties:
- Armstrong numbers (sum of digits raised to n = number).
- Harshad numbers (divisible by digit sum).
- Palindrome numbers.
- Happy numbers (iterated sum of squared digits = 1).

Digit extraction via `% 10` and `/ 10` is a core skill.

----------------------------------------

## Step 6: Complexity

Time: **O((right - left) · log max)** — n numbers, each with log(max) digits.
Space: O(output size) for the result list.

For typical constraints, very fast.

----------------------------------------

## Step 7: C++ Implementation

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

Clean separation: `isSelfDividing` helper for per-number logic; main function iterates the range.

----------------------------------------

## Step 8: Follow-up Questions

- **Find the n-th self-dividing number.** Iterate and count.
- **Sum of self-dividing numbers in a range.** Same filter, sum results.
- **Count them up to N without enumerating?** Hard — no known closed form.
- **"Digits divide each other" — all digits are mutually divisible.** Different problem; check pairs.
- **Generalize to base b.** Digits 0..b-1; extraction via % b and / b.
- **Harshad numbers (divisible by digit sum, not each digit).** Similar pattern, different check.
