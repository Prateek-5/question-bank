# Climbing Stairs

## Problem Link
https://leetcode.com/problems/climbing-stairs/

## Topic
Dynamic Programming DP

## Core Concept
Fibonacci recurrence f(n) = f(n-1) + f(n-2).

## Intuition
To reach step n you come from step n-1 (one step) or n-2 (two steps). Ways combine additively.

## Detailed Explanation
Rolling variables a=1, b=1; loop n times: c=a+b; a=b; b=c.

## Dry Run
n=4: 1,2,3,5 → 5 ways.

## Approach
O(n) DP with O(1) space.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
int climbStairs(int n) {
    int a = 1, b = 1;
    for (int i = 2; i <= n; ++i) { int c = a + b; a = b; b = c; }
    return b;
}
```

## Follow-up Questions
- k-step climbing (DP over k).
- Cost at each step (Min Cost Climbing).
- Matrix exponentiation for large n.
