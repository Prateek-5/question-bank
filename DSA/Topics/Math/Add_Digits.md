# Add Digits

## Problem Link
https://leetcode.com/problems/add-digits/

## Topic
Math

## Core Concept
Digital root — closed-form using modulo 9.

## Intuition
Repeatedly summing digits until one digit remains is the digital root. For any positive n, the digital root equals 1 + (n-1) % 9. This works because 10 ≡ 1 (mod 9), so a number is congruent to the sum of its digits modulo 9.

## Detailed Explanation
If n == 0 return 0. Else return 1 + (n - 1) % 9. The formula handles the special case where n is a multiple of 9 (should yield 9, not 0). The iterative simulation is also O(log n) per layer but the closed form is O(1).

## Dry Run
n = 38. 1 + (37 % 9) = 1 + 1 = 2. Verify: 3+8=11 → 1+1=2. ✓

## Approach
Either simulate by summing digits in a loop or use the O(1) digital-root formula.

## Time and Space Complexity
O(1) time and space.

## C++ Implementation
```cpp
int addDigits(int n) {
    if (n == 0) return 0;
    return 1 + (n - 1) % 9;
}
```

## Follow-up Questions
- What if n can be arbitrary precision (string input)? Sum ASCII digits, mod 9.
- Generalize to any base b (digital root mod b-1).
- Prove the closed form via modular arithmetic.
