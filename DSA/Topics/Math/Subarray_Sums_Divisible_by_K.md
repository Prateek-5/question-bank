# Subarray Sums Divisible by K

## Problem Link
https://leetcode.com/problems/subarray-sums-divisible-by-k/

## Topic
Math

## Core Concept
Prefix-sum + modulo bucket counting.

## Intuition
If two prefix sums have the same remainder mod k, the subarray between them sums to a multiple of k. Count how many prefix sums share each remainder and combine in pairs.

## Detailed Explanation
Maintain count[r] = number of prefix sums with remainder r. Initialize count[0]=1 (empty prefix). For each element, update running sum, compute r = ((sum % k) + k) % k to handle negatives, add count[r] to the answer, then increment count[r].

## Dry Run
nums=[4,5,0,-2,-3,1], k=5. Prefix mods: 4,4,4,2,4,0. count[0]=1 initial. Step 1: r=4, add 0, count[4]=1. Step 2: r=4, add 1, count[4]=2. Step 3: r=4, add 2, count[4]=3. Step 4: r=2, add 0, count[2]=1. Step 5: r=4, add 3, count[4]=4. Step 6: r=0, add 1, count[0]=2. Total=7.

## Approach
One pass with a size-k bucket; uses pigeonhole over prefix remainders.

## Time and Space Complexity
Time: O(n). Space: O(k).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

int subarraysDivByK(vector<int>& nums, int k) {
    vector<int> cnt(k, 0); cnt[0] = 1;
    int sum = 0, ans = 0;
    for (int x : nums) {
        sum += x;
        int r = ((sum % k) + k) % k;
        ans += cnt[r];
        cnt[r]++;
    }
    return ans;
}
```

## Follow-up Questions
- Return the actual subarrays (not just count).
- Subarray sums divisible by K with minimum length.
- What if we want sums divisible by any of several ks?
