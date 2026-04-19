# Number of Open Doors

## Problem Link
https://www.geeksforgeeks.org/problems/number-of-open-doors1552/1

## Topic
Number Theory Misc

## Core Concept
Perfect-square toggles — i doors open iff i is a perfect square.

## Intuition
Door i is toggled once per divisor. Divisors pair up symmetrically except for perfect squares — which have an odd divisor count, leaving them toggled (open).

## Detailed Explanation
Count of open doors after n passes = floor(sqrt(n)).

## Dry Run
n=10 → sqrt=3 → 3 doors open (1,4,9).

## Approach
Closed form.

## Time and Space Complexity
O(1).

## C++ Implementation
```cpp
#include <cmath>
int openDoors(int n) { return (int)sqrt((double)n); }
```

## Follow-up Questions
- Which doors are open (list).
- K-pass toggling variant.
- Prime-indexed toggling.
