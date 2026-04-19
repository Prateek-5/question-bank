# Largest Number That Divides X and Is Co-Prime with Y

## Problem Link
https://www.geeksforgeeks.org/dsa/largest-number-divides-x-co-prime-y/

## Topic
Number Theory Misc

## Core Concept
Divide x by gcd(x,y) repeatedly — remove all prime factors shared with y.

## Intuition
We want d | x and gcd(d,y)=1. Strip from x all prime factors it shares with y, leaving the largest coprime divisor.

## Detailed Explanation
Loop: g = gcd(x, y). If g == 1 stop. Else x /= g. Return x.

## Dry Run
x=12, y=15. gcd=3, x=4. gcd(4,15)=1 → 4. 4 divides 12 and gcd(4,15)=1.

## Approach
Iterative gcd peeling.

## Time and Space Complexity
Time: O(log x). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int largestCoprimeDivisor(int x, int y) {
    while (__gcd(x, y) != 1) x /= __gcd(x, y);
    return x;
}
```

## Follow-up Questions
- Smallest coprime divisor >1.
- Coprime divisors count.
- Modular variant.
