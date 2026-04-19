# Sum Root to Leaf Numbers

## Problem Link
https://leetcode.com/problems/sum-root-to-leaf-numbers/

## Topic
Trees Binary Trees

## Core Concept
DFS constructing numbers digit-by-digit; sum at leaves.

## Intuition
Each root-to-leaf path represents a number formed by concatenating digits. DFS accumulates the number as num*10+digit and adds it at each leaf.

## Detailed Explanation
dfs(node, cur): if null return 0. cur = cur*10 + node.val. If leaf return cur. Else return dfs(left, cur) + dfs(right, cur).

## Dry Run
Tree 1,2,3. Paths 12 and 13. Sum=25.

## Approach
Single DFS.

## Time and Space Complexity
Time: O(n). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

int dfs(TreeNode* r, int cur) {
    if (!r) return 0;
    cur = cur * 10 + r->val;
    if (!r->left && !r->right) return cur;
    return dfs(r->left, cur) + dfs(r->right, cur);
}
int sumNumbers(TreeNode* root) { return dfs(root, 0); }
```

## Follow-up Questions
- Sum in a different base.
- Print all numbers formed.
- Product of numbers along path.
