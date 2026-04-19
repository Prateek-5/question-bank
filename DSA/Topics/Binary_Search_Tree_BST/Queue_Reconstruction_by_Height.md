# Queue Reconstruction by Height

## Problem Link
https://leetcode.com/problems/queue-reconstruction-by-height/description/

## Topic
Binary Search Tree BST

## Core Concept
Sort by height desc, k asc; insert at position k.

## Intuition
If we process people from tallest to shortest, when inserting each person, taller people (already placed) are the only ones that matter for their k value; the current person's k equals exactly their target index.

## Detailed Explanation
Sort people by (−h, k). Iterate; for each (h,k) insert at position k in the result list. List insertion ensures taller-already-placed count equals k.

## Dry Run
Input [[7,0],[4,4],[7,1],[5,0],[6,1],[5,2]]. Sort desc h: [[7,0],[7,1],[6,1],[5,0],[5,2],[4,4]]. Insert: [7,0]; [7,0],[7,1]; [7,0],[6,1],[7,1]; ... final [[5,0],[7,0],[5,2],[6,1],[4,4],[7,1]].

## Approach
Sort + list.insert.

## Time and Space Complexity
Time: O(n²). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> reconstructQueue(vector<vector<int>>& p) {
    sort(p.begin(), p.end(), [](auto& a, auto& b){
        return a[0] != b[0] ? a[0] > b[0] : a[1] < b[1];
    });
    vector<vector<int>> res;
    for (auto& x : p) res.insert(res.begin() + x[1], x);
    return res;
}
```

## Follow-up Questions
- Use a Fenwick tree for O(n log n).
- What if k counts shorter people?
- Stream reconstruction.
