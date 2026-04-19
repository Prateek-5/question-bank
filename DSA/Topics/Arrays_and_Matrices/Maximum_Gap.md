# Maximum Gap

## Problem Link
https://leetcode.com/problems/maximum-gap/

## Topic
Arrays and Matrices

## Core Concept
Bucket/pigeonhole sort for O(n) max adjacent gap.

## Intuition
With n elements in range [min,max], dividing into n-1 buckets of size (max-min)/(n-1) guarantees the max gap lies across two buckets (not within one) by pigeonhole.

## Detailed Explanation
Find min and max. Bucket width w = ceil((max-min)/(n-1)). For each num compute bucket idx (num-min)/w. Track each bucket's min and max. Max gap = max over consecutive non-empty buckets of (nextMin - prevMax).

## Dry Run
nums=[3,6,9,1]. min=1,max=9, n=4, w=3. Buckets: idx 0:{1,3}, idx 1:{6}, idx 2:{9}. Gaps 6-3=3, 9-6=3. Answer=3.

## Approach
Bucket sort is O(n). Radix sort also works.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maximumGap(vector<int>& nums) {
    int n = nums.size();
    if (n < 2) return 0;
    int mn = *min_element(nums.begin(), nums.end()),
        mx = *max_element(nums.begin(), nums.end());
    if (mn == mx) return 0;
    int w = max(1, (mx - mn + n - 2) / (n - 1));
    int cnt = (mx - mn) / w + 1;
    vector<int> bmin(cnt, INT_MAX), bmax(cnt, INT_MIN);
    for (int x : nums) {
        int b = (x - mn) / w;
        bmin[b] = min(bmin[b], x);
        bmax[b] = max(bmax[b], x);
    }
    int prev = mn, ans = 0;
    for (int i = 0; i < cnt; ++i) if (bmin[i] != INT_MAX) {
        ans = max(ans, bmin[i] - prev);
        prev = bmax[i];
    }
    return ans;
}
```

## Follow-up Questions
- Stream version.
- Top-k adjacent gaps.
- 2D extension (nearest-pair).
