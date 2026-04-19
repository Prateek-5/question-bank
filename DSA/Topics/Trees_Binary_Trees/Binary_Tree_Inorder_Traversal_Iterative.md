# Binary Tree Inorder Traversal (Iterative)

## Problem Link
https://leetcode.com/problems/binary-tree-inorder-traversal/

## Topic
Trees Binary Trees

## Core Concept
Stack-based inorder: walk left, pop, go right.

## Intuition
Simulate recursion explicitly using a stack. Push left children until null; pop and visit; then move to right child.

## Detailed Explanation
cur = root. While cur or stack non-empty: push all left descendants of cur; pop, record value, set cur = popped->right.

## Dry Run
Tree 1,_,2,3. cur=1, push [1]. cur=null. pop 1→visit. cur=2. push [2,3]. pop 3→visit. pop 2→visit. Result [1,3,2].

## Approach
Explicit stack.

## Time and Space Complexity
Time: O(n). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

vector<int> inorderIter(TreeNode* root) {
    vector<int> res; stack<TreeNode*> st; auto* cur = root;
    while (cur || !st.empty()) {
        while (cur) { st.push(cur); cur = cur->left; }
        cur = st.top(); st.pop();
        res.push_back(cur->val);
        cur = cur->right;
    }
    return res;
}
```

## Follow-up Questions
- Morris traversal for O(1) space.
- Iterative preorder and postorder.
- Handle threaded binary trees.
