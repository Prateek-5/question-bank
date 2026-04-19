# Largest Multiple of Three

## Problem Link
https://leetcode.com/problems/largest-multiple-of-three/

## Topic
Number Theory Misc

## Core Concept
Digit sum mod 3 analysis + greedy digit removal.

## Intuition
Sum of digits mod 3 determines divisibility. If sum%3==r, we must remove digits whose mods sum to r — preferring fewest and smallest digits.

## Detailed Explanation
Count digits. Compute total mod 3. If r>0, remove one digit ≡ r (smallest), else two digits ≡ 3-r. After removal, sort digits desc, handle leading zeros.

## Dry Run
digits=[8,1,9]. Sum=18, mod 3=0 → keep all. Sort desc → '981'.

## Approach
Digit-count + greedy.

## Time and Space Complexity
Time: O(n log n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
string largestMultipleOfThree(vector<int>& d) {
    sort(d.begin(), d.end());
    int s = accumulate(d.begin(), d.end(), 0);
    auto removeOne = [&](int mod) {
        for (int i = 0; i < (int)d.size(); ++i) if (d[i] % 3 == mod) { d.erase(d.begin()+i); return true; }
        return false;
    };
    if (s % 3 == 1) { if (!removeOne(1)) { removeOne(2); removeOne(2); } }
    else if (s % 3 == 2) { if (!removeOne(2)) { removeOne(1); removeOne(1); } }
    sort(d.rbegin(), d.rend());
    string r; for (int x : d) r += char('0'+x);
    if (!r.empty() && r[0] == '0') return "0";
    return r;
}
```

## Follow-up Questions
- Largest multiple of N.
- Smallest multiple of 3 using subset of digits.
- Digit rearrangement to reach a divisibility class.
