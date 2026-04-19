# Trees / Binary Trees — Concepts Guide

----------------------------------------

## 1. Introduction

Binary trees are hierarchical structures where each node has up to two children. They show up everywhere — from expression parsing to decision trees to game state trees. The key skill isn't memorizing algorithms; it's learning to *think recursively*. Almost every binary tree problem has the shape: 'solve it for the two subtrees, then combine'.

----------------------------------------

## 2. Real-Life Analogy

Think of a family tree. If you want to know how many descendants someone has, you don't count them manually — you ask each of their children 'how many descendants do you have?', sum the answers, and add 1 (for the person themselves). That's divide-and-conquer on a tree. Every binary tree algorithm is basically this recursive conversation.

----------------------------------------

## 3. Core Idea

The foundational operations on binary trees are the four traversals: preorder (root, left, right), inorder (left, root, right), postorder (left, right, root), and level-order (BFS). Most problems map naturally to one of these. Post-order is the workhorse for problems that aggregate information from subtrees: the recursive call returns child data, we combine it, we return the combined result. If you master that pattern, you can solve a wide class of tree problems almost by reflex.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

You're probably working with a binary tree when the problem describes:

- **Hierarchical data** (parent-child relationships).
- **Expression parsing** (operators as internal nodes, operands as leaves).
- **Decision processes** (each node is a decision with two outcomes).
- **Any structure with 'each node has at most two children'.**

For problems on such structures, ask yourself: 'What's the answer for a subtree?' — that's the recursive subproblem.

----------------------------------------

## 5. Types / Variations

- **Full binary tree:** every node has 0 or 2 children.
- **Complete binary tree:** all levels filled except possibly the last, which is filled left-to-right.
- **Perfect binary tree:** all internal nodes have two children and all leaves are at the same depth.
- **BST (Binary Search Tree):** adds the ordering invariant.
- **Balanced tree:** AVL, red-black — height is O(log n).
- **N-ary tree:** generalization where each node has up to N children.

----------------------------------------

## 6. Step-by-Step Working

**The recursive template for most tree problems:**

1. Base case: if the node is null, return the identity value (0, null, true — depends on the problem).
2. Recurse on the left child → get `leftResult`.
3. Recurse on the right child → get `rightResult`.
4. Combine `leftResult`, `rightResult`, and the current node's data.
5. Return the combined result.

**Example — Compute height:**
- Base: null → return 0.
- Recurse left and right.
- Return 1 + max(leftHeight, rightHeight).

**Example — Sum of all node values:**
- Base: null → return 0.
- Recurse left and right.
- Return node.val + leftSum + rightSum.

Notice the pattern is the same — only the combine step changes.

----------------------------------------

## 7. Visual Explanation

**A sample tree:**

```
         1
       /   \
      2     3
     / \     \
    4   5     6
```

- **Preorder** (root, L, R): 1 → 2 → 4 → 5 → 3 → 6
- **Inorder** (L, root, R): 4 → 2 → 5 → 1 → 3 → 6
- **Postorder** (L, R, root): 4 → 5 → 2 → 6 → 3 → 1
- **Level-order**: 1 → 2 → 3 → 4 → 5 → 6

Each traversal paints a different picture; pick the one that fits your problem.

----------------------------------------

## 8. Code Templates (C++)

```cpp
struct TreeNode {
    int val;
    TreeNode *left, *right;
    TreeNode(int x): val(x), left(nullptr), right(nullptr) {}
};

// Generic postorder aggregator template
int solve(TreeNode* root) {
    if (!root) return /* identity */;
    int l = solve(root->left);
    int r = solve(root->right);
    return /* combine l, r, root->val */;
}

// Height
int height(TreeNode* r) {
    if (!r) return 0;
    return 1 + max(height(r->left), height(r->right));
}

// Level-order
vector<vector<int>> levelOrder(TreeNode* root) {
    vector<vector<int>> res;
    if (!root) return res;
    queue<TreeNode*> q; q.push(root);
    while (!q.empty()) {
        int sz = q.size();
        vector<int> lvl;
        while (sz--) {
            auto* n = q.front(); q.pop();
            lvl.push_back(n->val);
            if (n->left) q.push(n->left);
            if (n->right) q.push(n->right);
        }
        res.push_back(lvl);
    }
    return res;
}
```

----------------------------------------

## 9. Common Mistakes

- **Missing null checks.** A single unguarded dereference will crash your code.
- **Confusing preorder, inorder, postorder.** Write them down as strings and trace each before coding.
- **Using BFS when DFS is needed (or vice versa).** Level-order = BFS; divide-and-conquer = DFS.
- **Recursion depth issues on skewed trees.** For very deep trees, iterative traversals with an explicit stack are safer.
- **Forgetting to update the result when the subtree itself is the answer.** (Diameter is a classic example — the longest path might not include the root.)

----------------------------------------

## 10. Interview Insights

Binary tree problems are interviewer favorites because they reveal whether you can think recursively. Interviewers want to see:

1. **Do you formulate the recursive subproblem clearly?** Naming what each call returns is half the battle.
2. **Do you pick the right traversal?** A clear justification scores points.
3. **Do you handle edge cases?** Empty tree, single node, skewed tree.
4. **Can you convert recursion to iteration if asked?** Many follow-ups test this.

Tip: when you're stuck on a tree problem, ask 'what does the answer look like for a single node? For a leaf?' Those extremes usually seed the recursion.
