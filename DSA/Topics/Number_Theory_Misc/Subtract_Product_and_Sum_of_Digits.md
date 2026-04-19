# Subtract Product and Sum of Digits

## Problem Link
https://leetcode.com/problems/subtract-the-product-and-sum-of-digits-of-an-integer/

## Topic
Number Theory Misc

## Core Concept
Compute digit product and sum in one pass.

## Intuition
Simple decomposition of n into digits.

## Detailed Explanation
While n>0: d=n%10; p*=d; s+=d; n/=10. Return p-s.

## Dry Run
n=234 → digits 2,3,4. p=24, s=9 → 15.

## Approach
Loop.

## Time and Space Complexity
Time: O(log n). Space: O(1).

## C++ Implementation
```cpp
int subtractProductAndSum(int n) {
    int p = 1, s = 0;
    while (n) { int d = n % 10; p *= d; s += d; n /= 10; }
    return p - s;
}
```

## Follow-up Questions
- Handle arbitrary base.
- Digit GCD/LCM.
- Digit power sum.
