# Binary Search Tree Iterator

## Problem Link
https://leetcode.com/problems/binary-search-tree-iterator/

## Topic
Binary Search Tree BST

## Core Concept
Lazy in-order iterator using a stack.

## Intuition
An iterator should expose next() in O(1) amortized. Maintain a stack storing the left spine of the current subtree; on next() pop top, then push the left spine of its right child.

## Detailed Explanation
Init: push left-spine of root. next(): pop node, if it has a right child, push left-spine of the right. hasNext(): stack non-empty.

## Dry Run
BST 7,3,15,_,_,9,20. Stack after init: [7,3]. next→3; stack=[7]. next→7, push 15 then 9 → [15,9]. next→9, stack=[15]. next→15, push 20 → [20].

## Approach
Amortized O(1) per next with O(h) space.

## Time and Space Complexity
Time: O(1) amortized. Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

class BSTIterator {
    stack<TreeNode*> st;
    void pushLeft(TreeNode* n) { while (n) { st.push(n); n = n->left; } }
public:
    BSTIterator(TreeNode* root) { pushLeft(root); }
    int next() {
        TreeNode* n = st.top(); st.pop();
        pushLeft(n->right);
        return n->val;
    }
    bool hasNext() { return !st.empty(); }
};
```

## Follow-up Questions
- prev() operation (requires parent pointers or Morris).
- Range iterator [lo, hi].
- Iterator with updates during iteration.
