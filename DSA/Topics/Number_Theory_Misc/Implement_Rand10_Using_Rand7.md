# Implement Rand10() Using Rand7()

## Problem Link
https://leetcode.com/problems/implement-rand10-using-rand7/description/

## Topic
Number Theory Misc

## Core Concept
Rejection sampling from a uniform 49-sample space.

## Intuition
rand7()·7+rand7() generates uniform [1..49]. Keep only 1..40 for uniform [1..10] via mod.

## Detailed Explanation
Loop: x = (rand7()-1)*7 + rand7() ∈ [1,49]. If x <= 40, return 1 + (x-1)%10.

## Dry Run
Expected rejection chance 9/49. On accept, value 1..10 uniform.

## Approach
Rejection sampling.

## Time and Space Complexity
Expected O(1) samples.

## C++ Implementation
```cpp
int rand7();
int rand10() {
    while (true) {
        int x = (rand7() - 1) * 7 + rand7();
        if (x <= 40) return 1 + (x - 1) % 10;
    }
}
```

## Follow-up Questions
- Generate rand(n) using rand(m).
- Minimize expected calls.
- Rand10 from rand2 (binary expansion).
