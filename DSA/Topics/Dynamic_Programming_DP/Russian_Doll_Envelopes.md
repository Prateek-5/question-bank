# Russian Doll Envelopes

## Problem Link
https://leetcode.com/problems/russian-doll-envelopes/

## Topic
Dynamic Programming DP

## Core Concept
Sort by width asc, height desc for same width; run LIS on heights.

## Intuition
We want a chain where each envelope strictly fits inside the next. Sorting with the twist prevents same-width envelopes from nesting during LIS on heights.

## Detailed Explanation
Sort envelopes by w asc, h desc (tie-break). Then LIS on h sequence gives the answer.

## Dry Run
envelopes=[[5,4],[6,4],[6,7],[2,3]] → sort [[2,3],[5,4],[6,7],[6,4]]. LIS on heights [3,4,7,4]=3.

## Approach
Sort + patience-sort LIS.

## Time and Space Complexity
Time: O(n log n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maxEnvelopes(vector<vector<int>>& e) {
    sort(e.begin(), e.end(), [](auto& x, auto& y){ return x[0]!=y[0] ? x[0]<y[0] : x[1]>y[1]; });
    vector<int> t;
    for (auto& x : e) {
        auto it = lower_bound(t.begin(), t.end(), x[1]);
        if (it == t.end()) t.push_back(x[1]); else *it = x[1];
    }
    return t.size();
}
```

## Follow-up Questions
- Allow equality in nesting.
- 3D boxes.
- Maximize sum of widths/heights along chain.
