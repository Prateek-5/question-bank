# Fizz Buzz

## Problem Link
https://leetcode.com/problems/fizz-buzz/

## Topic
Arrays and Matrices

## Core Concept
Modulo classification.

## Intuition
For each i from 1..n print 'FizzBuzz' if i%15==0, 'Fizz' if i%3==0, 'Buzz' if i%5==0, else the number.

## Detailed Explanation
Straightforward loop with modulo checks.

## Dry Run
n=5 → ['1','2','Fizz','4','Buzz'].

## Approach
One pass.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<string> fizzBuzz(int n) {
    vector<string> r;
    for (int i = 1; i <= n; ++i) {
        if (i % 15 == 0) r.push_back("FizzBuzz");
        else if (i % 3 == 0) r.push_back("Fizz");
        else if (i % 5 == 0) r.push_back("Buzz");
        else r.push_back(to_string(i));
    }
    return r;
}
```

## Follow-up Questions
- Arbitrary divisors and tokens.
- Multi-threaded FizzBuzz.
- Reverse order.
