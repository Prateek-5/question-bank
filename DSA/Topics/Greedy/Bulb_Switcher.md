# Bulb Switcher

## Problem Link
https://leetcode.com/problems/bulb-switcher/

## Topic
Greedy

## Core Concept
Perfect-square observation — bulbs toggled an odd number of times remain on.

## Intuition
Bulb i is toggled once per divisor of i. Divisors come in pairs except when i is a perfect square. So only perfect squares end ON. Count perfect squares ≤ n = floor(sqrt(n)).

## Detailed Explanation
Return floor(sqrt(n)). Based on parity of divisor count.

## Dry Run
n=3. sqrt(3)≈1.73 → 1 bulb on (bulb 1).

## Approach
Closed form.

## Time and Space Complexity
O(1).

## C++ Implementation
```cpp
#include <cmath>
int bulbSwitch(int n) { return (int)sqrt((double)n); }
```

## Follow-up Questions
- Bulb switcher II (4 operations, pattern recognition).
- Bulb Switcher III (time until all blue).
- Generalized toggling with k-divisor rule.
