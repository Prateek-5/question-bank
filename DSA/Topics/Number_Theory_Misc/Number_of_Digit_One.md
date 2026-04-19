# Number of Digit One

## Problem Link
https://leetcode.com/problems/number-of-digit-one/description/

## Topic
Number Theory Misc

## Core Concept
Digit-DP counting ones across positions.

## Intuition
For each digit position, count how many times '1' appears there among numbers 1..n by comparing the digit at that position with high and low parts.

## Detailed Explanation
For factor f from 1 upward while n >= f: high = n / (f*10); cur = (n / f) % 10; low = n % f. If cur > 1: add (high+1)*f. If cur == 1: add high*f + low + 1. Else add high*f.

## Dry Run
n=13. f=1: high=1,cur=3,low=0 → 2. f=10: high=0,cur=1,low=3 → 0+3+1=4. Total=6.

## Approach
Digit-position counting.

## Time and Space Complexity
Time: O(log n). Space: O(1).

## C++ Implementation
```cpp
int countDigitOne(int n) {
    long long res = 0, f = 1;
    while ((long long)f <= n) {
        long long h = n / (f * 10), cur = (n / f) % 10, low = n % f;
        if (cur > 1) res += (h + 1) * f;
        else if (cur == 1) res += h * f + low + 1;
        else res += h * f;
        f *= 10;
    }
    return (int)res;
}
```

## Follow-up Questions
- Count digit d (other than 1).
- Digit-DP for sums/XOR over ranges.
- Count numbers with specific digit property.
