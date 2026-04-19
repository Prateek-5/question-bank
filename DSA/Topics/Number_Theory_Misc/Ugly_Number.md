# Ugly Number

## Problem Link
https://leetcode.com/problems/ugly-number/

## Topic
Number Theory Misc

## Core Concept
Divide out 2, 3, 5; final value must be 1.

## Intuition
An ugly number's prime factors only include 2, 3, 5. Keep dividing and check if 1 remains.

## Detailed Explanation
While n%2==0 n/=2; while n%3==0 n/=3; while n%5==0 n/=5. Return n==1.

## Dry Run
n=14 → divide 2 → 7. 7≠1 → false.

## Approach
Iterative factor stripping.

## Time and Space Complexity
Time: O(log n). Space: O(1).

## C++ Implementation
```cpp
bool isUgly(int n) {
    if (n <= 0) return false;
    for (int p : {2, 3, 5}) while (n % p == 0) n /= p;
    return n == 1;
}
```

## Follow-up Questions
- Ugly Number II (nth ugly).
- Super Ugly (arbitrary prime list).
- Count uglies up to N.
