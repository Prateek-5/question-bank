# Max Chunks To Make Sorted

## Problem Link
https://leetcode.com/problems/max-chunks-to-make-sorted/

## Topic
1 D and 2 D Arrays

## Core Concept
Count indices where running max equals current index.

## Intuition
A chunk ending at index i is valid iff max(a[0..i]) == i (since values are a permutation of 0..n-1). Each such index marks the end of an independent chunk.

## Detailed Explanation
Iterate with running max m. If m == i at index i, increment chunk count.

## Dry Run
arr=[1,0,2,3,4]. i=0,m=1 !=0. i=1,m=1==1 → chunk. i=2,m=2==2 → chunk. Similarly 3,4. Total 4 chunks.

## Approach
Single scan with running max.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maxChunksToSorted(vector<int>& a) {
    int m = 0, cnt = 0;
    for (int i = 0; i < (int)a.size(); ++i) {
        m = max(m, a[i]);
        if (m == i) cnt++;
    }
    return cnt;
}
```

## Follow-up Questions
- General version where values aren't a permutation (Max Chunks II).
- Prove correctness using permutation property.
- Return the chunk boundaries.
