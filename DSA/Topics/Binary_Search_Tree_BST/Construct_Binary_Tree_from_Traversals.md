# Construct Binary Tree from Traversals

**Problem Link:**
<a href="https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/</a>

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: The Setup

Given two integer arrays `preorder` and `inorder`, each representing one traversal of the same binary tree (all values distinct), reconstruct the original tree.

**Preorder:** root, left subtree, right subtree. Always visits root first.
**Inorder:** left subtree, root, right subtree. Root appears between its left and right subtree values.

Example:
```
preorder = [3, 9, 20, 15, 7]
inorder  = [9, 3, 15, 20, 7]
```

Reconstructed tree:
```
    3
   / \
  9  20
     / \
    15  7
```

Verify:
- Preorder: 3 (root), 9 (left), 20 (right-root), 15 (right-left), 7 (right-right). ✓
- Inorder: 9 (left), 3 (root), 15 (right-left), 20 (right-root), 7 (right-right). ✓

----------------------------------------

## Step 2: Extract Key Information

Two critical observations:

1. **Preorder's first element is the root of the current tree.** Always. Because preorder visits root before anything else.

2. **In inorder, the root's position splits the array into left subtree values (before root) and right subtree values (after root).** Because inorder visits the entire left subtree before the root, then the entire right subtree after.

So given `preorder[0] = 3`, find 3's position in inorder. Position 1. So inorder[0..0] = [9] is the left subtree's inorder traversal, and inorder[2..4] = [15, 20, 7] is the right subtree's inorder traversal.

Correspondingly in preorder: after the root (position 0), the next `len(left)` = 1 elements are the left subtree's preorder, and the remaining 3 are the right subtree's preorder.

Recurse on left and right halves.

----------------------------------------

## Step 3: The Recursive Reconstruction

```
build(preorder, inorder):
    if empty: return null
    root_val = preorder[0]
    root = new Node(root_val)
    split = position of root_val in inorder
    left_inorder  = inorder[:split]
    right_inorder = inorder[split+1:]
    left_preorder  = preorder[1 : 1 + len(left_inorder)]
    right_preorder = preorder[1 + len(left_inorder):]
    root.left  = build(left_preorder, left_inorder)
    root.right = build(right_preorder, right_inorder)
    return root
```

Straightforward. Each recursion handles a smaller portion.

The only inefficiency: "position of root_val in inorder" is O(n) per call if we search linearly. Cumulatively O(n²).

Fix: precompute a hashmap `value → inorder_index`. Then position lookup is O(1), making the whole algorithm O(n).

----------------------------------------

## Step 4: Use Indices, Not Slices

Slicing arrays (copying) is expensive. Instead, track index ranges into the original arrays.

```
build(preStart, inStart, inEnd):
    if inStart > inEnd: return null
    root_val = preorder[preStart]
    root = new Node(root_val)
    split = indexOf[root_val]   # position in inorder
    leftSize = split - inStart
    root.left  = build(preStart + 1, inStart, split - 1)
    root.right = build(preStart + 1 + leftSize, split + 1, inEnd)
    return root
```

Call: `build(0, 0, n - 1)`.

No array copying. Everything's index arithmetic.

----------------------------------------

## Step 5: Walk Through Example

preorder = [3, 9, 20, 15, 7], inorder = [9, 3, 15, 20, 7]. indexOf = {9:0, 3:1, 15:2, 20:3, 7:4}.

```
build(0, 0, 4):
  root_val = preorder[0] = 3. Root = Node(3).
  split = indexOf[3] = 1. leftSize = 1 - 0 = 1.
  
  Left: build(1, 0, 0):
    root_val = preorder[1] = 9. Root = Node(9).
    split = indexOf[9] = 0. leftSize = 0.
    Left: build(2, 0, -1) → null.
    Right: build(2, 1, 0) → null (inStart > inEnd).
    Return Node(9).
  
  Right: build(2, 2, 4):
    root_val = preorder[2] = 20. Root = Node(20).
    split = indexOf[20] = 3. leftSize = 3 - 2 = 1.
    
    Left: build(3, 2, 2):
      root_val = preorder[3] = 15. Root = Node(15).
      split = indexOf[15] = 2. leftSize = 0.
      Left: build(4, 2, 1) → null.
      Right: build(4, 3, 2) → null.
      Return Node(15).
    
    Right: build(4, 4, 4):
      root_val = preorder[4] = 7. Root = Node(7).
      split = 4. leftSize = 0.
      Children null.
      Return Node(7).
    
    Return Node(20, Node(15), Node(7)).
  
  Return Node(3, Node(9), Node(20, Node(15), Node(7))).
```

Final tree matches expected. ✓

----------------------------------------

## Step 6: Why Preorder + Inorder Uniquely Determines the Tree

Claim: given both preorder and inorder (with distinct values), the tree is uniquely determined.

Proof sketch: the root is fixed (preorder[0]). The split of inorder at the root's position uniquely determines which values belong to the left subtree vs right subtree. Recursively, each subtree is uniquely determined. By strong induction, the entire tree is unique.

Contrast: preorder + postorder (without inorder) is **not** sufficient to uniquely determine a tree, because we can't always tell whether a given node has its single child on the left or right. The inorder traversal is the one that reveals structure unambiguously.

----------------------------------------

## Step 7: Name It

**Tree reconstruction from traversals.** The general pattern: one traversal identifies the root, another (inorder) splits the remaining values into left/right subtrees. Recurse.

Variants:
- Preorder + Inorder (this problem).
- Postorder + Inorder (similar, just the root is preorder's first vs postorder's last).
- Level-order + Inorder (trickier: level-order doesn't nest naturally).

Understanding why inorder is required (unique split on values) is the key takeaway.

----------------------------------------

## Step 8: Complexity

Time: **O(n)** with precomputed hashmap. O(n²) without.
Space: **O(n)** for the hashmap + O(h) for the recursion stack.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class Solution {
    unordered_map<int, int> indexOf;
    vector<int> preorder;

    TreeNode* build(int preStart, int inStart, int inEnd) {
        if (inStart > inEnd) return nullptr;
        int rootVal = preorder[preStart];
        TreeNode* root = new TreeNode(rootVal);
        int split = indexOf[rootVal];
        int leftSize = split - inStart;
        root->left = build(preStart + 1, inStart, split - 1);
        root->right = build(preStart + 1 + leftSize, split + 1, inEnd);
        return root;
    }

public:
    TreeNode* buildTree(vector<int>& preorder_in, vector<int>& inorder) {
        preorder = preorder_in;
        for (int i = 0; i < (int)inorder.size(); ++i) indexOf[inorder[i]] = i;
        return build(0, 0, inorder.size() - 1);
    }
};
```

Clean. The hashmap and stored preorder are member variables for convenience.

----------------------------------------

## Step 10: Follow-up Questions

- **Reconstruct from postorder + inorder.** Root is postorder's last; process right subtree first in recursion.
- **Handle duplicate values.** Multiple positions for root_val in inorder — ambiguity. Problem typically guarantees distinct.
- **Build tree iteratively (no recursion).** Use a stack; more complex but avoids recursion overflow.
- **Level-order + inorder.** Each level has roots and their children. Split into sub-trees by matching with inorder positions.
- **Verify that the traversals are consistent.** Optional validation: ensure all indexing works out.
- **Memory optimization with in-place array manipulation.** Usually not worth the complexity; O(n) is already tight.
