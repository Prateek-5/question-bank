# Construct Binary Tree from Inorder & Postorder

**Problem Link:**
<a href="https://leetcode.com/problems/construct-binary-tree-from-inorder-and-postorder-traversal/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/construct-binary-tree-from-inorder-and-postorder-traversal/</a>

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: Recap the Traversal Orders

Two standard binary tree traversals:
- **Inorder**: left subtree, then root, then right subtree.
- **Postorder**: left subtree, then right subtree, then root.

Given the inorder and postorder sequences (both containing the same set of node values), reconstruct the original tree.

Example:
```
inorder  = [9, 3, 15, 20, 7]
postorder = [9, 15, 7, 20, 3]
```

The original tree should be:
```
    3
   / \
  9  20
     / \
    15  7
```

Let me verify:
- Inorder: 9, then 3, then (15, 20, 7 with 15 left, 20 root, 7 right) → 9, 3, 15, 20, 7. ✓
- Postorder: 9, then (15, 7, 20) then 3 → 9, 15, 7, 20, 3. ✓

So the tree matches.

Problem guarantees all values are distinct.

----------------------------------------

## Step 2: Extract Information From Each Sequence

Two key observations:

**Postorder's last element is always the root.**
Because postorder is "left, right, root," the very last thing visited is the root of the tree (or the root of whichever subtree we're constructing).

For our example, postorder ends with 3 → 3 is the root. ✓

**Inorder tells us which values are on the left vs right of any root.**
In inorder, everything to the left of the root's position is in the left subtree; everything to the right is in the right subtree.

For root 3, find its position in inorder: index 1. Left subtree values = [9]. Right subtree values = [15, 20, 7].

Putting these together:
1. Find the root (last of postorder).
2. Locate root in inorder to split into left/right subtree value sets.
3. Recursively build left and right subtrees from their respective portions of inorder and postorder.

----------------------------------------

## Step 3: Determining Subtree Slices

If left subtree has `L` nodes, then in postorder:
- The first L elements are the left subtree's postorder.
- The next (total-L-1) elements are the right subtree's postorder.
- The last element is the root.

In inorder:
- The first L elements (before root) are the left subtree's inorder.
- The elements after the root's position are the right subtree's inorder.

L is determined by the root's position in inorder.

For our example:
- Root = 3, at inorder position 1. So L = 1 (one element to the left: [9]).
- Left inorder: [9]. Left postorder: first 1 = [9].
- Right inorder: [15, 20, 7]. Right postorder: next 3 = [15, 7, 20].
- Recurse.

----------------------------------------

## Step 4: Recursive Algorithm

```
build(inorder[], postorder[]):
    if inorder is empty: return null
    rootVal = postorder[last]
    rootPos = index of rootVal in inorder
    L = rootPos
    leftIn  = inorder[0..L-1]
    rightIn = inorder[L+1..]
    leftPost  = postorder[0..L-1]
    rightPost = postorder[L..second-to-last]
    root = new Node(rootVal)
    root.left  = build(leftIn, leftPost)
    root.right = build(rightIn, rightPost)
    return root
```

Direct but uses sub-arrays at each step (memory inefficient). Better: pass index ranges into the original arrays.

```
build(inStart, inEnd, postStart, postEnd):
    if inStart > inEnd: return null
    rootVal = postorder[postEnd]
    rootPos = position of rootVal in inorder (lookup by hashmap)
    L = rootPos - inStart
    root = new Node(rootVal)
    root.left  = build(inStart, rootPos - 1, postStart, postStart + L - 1)
    root.right = build(rootPos + 1, inEnd, postStart + L, postEnd - 1)
    return root
```

A precomputed hashmap `inorderIndex` maps values to positions in inorder in O(1).

----------------------------------------

## Step 5: Trace on the Example

`inorder = [9, 3, 15, 20, 7]`, `postorder = [9, 15, 7, 20, 3]`.
Hashmap: `{9:0, 3:1, 15:2, 20:3, 7:4}`.

```
build(inStart=0, inEnd=4, postStart=0, postEnd=4):
  rootVal = postorder[4] = 3.
  rootPos = 1. L = 1 - 0 = 1.
  root = Node(3).
  root.left = build(0, 0, 0, 0):
    rootVal = postorder[0] = 9.
    rootPos = 0. L = 0.
    root = Node(9).
    root.left = build(0, -1, 0, -1) → null.
    root.right = build(1, 0, 1, 0) → null (inStart > inEnd).
    return Node(9).
  root.right = build(2, 4, 1, 3):
    rootVal = postorder[3] = 20.
    rootPos = 3. L = 3 - 2 = 1.
    root = Node(20).
    root.left = build(2, 2, 1, 1):
      rootVal = postorder[1] = 15.
      rootPos = 2. L = 0.
      Node(15) with null children.
    root.right = build(4, 4, 2, 2):
      rootVal = postorder[2] = 7.
      Node(7) with null children.
    return Node(20).
  return Node(3).
```

Tree structure:
```
    3
   / \
  9  20
     / \
    15  7
```

✓

----------------------------------------

## Step 6: Why This Produces a Unique Tree

**Claim:** inorder + postorder (with distinct values) uniquely determines the tree.

**Proof sketch:** The root is fixed (last of postorder). The split at root's position in inorder fixes which values go in each subtree. Recursing, each subtree's root is determined analogously. By induction, the whole tree is uniquely reconstructed.

Note that without **distinct values**, the recursion could pick the wrong position for the root in inorder (if the root's value appears multiple times). Most problems assume distinctness to avoid this.

Also note: preorder + postorder is **not** enough to uniquely determine a general binary tree (they can leave ambiguity about which child is left vs right when a node has only one child). Inorder is essential for uniqueness.

----------------------------------------

## Step 7: Name It

This is **divide-and-conquer tree reconstruction**. The same pattern applies:
- Preorder + inorder → recursively: first of preorder is root, split inorder.
- Inorder + postorder → this problem.
- Preorder + postorder → non-unique in general.
- Level-order + inorder → works, a bit trickier to slice level-order.

The key insight is always: **one traversal tells you the root; inorder tells you the split**.

----------------------------------------

## Step 8: Complexity

With precomputed hashmap for inorder lookups:
- Each node is processed once, O(1) per node (one hashmap lookup, one allocation).
- **O(n)** total time.

Without hashmap: O(n²) from linear searches in inorder.

Space: O(n) for hashmap + O(h) for recursion = **O(n)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class Solution {
    unordered_map<int, int> inorderIndex;
    vector<int> postorder;
    int postPos;

    TreeNode* build(int inStart, int inEnd) {
        if (inStart > inEnd) return nullptr;
        int rootVal = postorder[postPos--];
        TreeNode* root = new TreeNode(rootVal);
        int rootPos = inorderIndex[rootVal];

        // Order matters: process right subtree first because postorder is read backward
        root->right = build(rootPos + 1, inEnd);
        root->left = build(inStart, rootPos - 1);
        return root;
    }

public:
    TreeNode* buildTree(vector<int>& inorder, vector<int>& post) {
        postorder = post;
        postPos = post.size() - 1;
        for (int i = 0; i < (int)inorder.size(); ++i) inorderIndex[inorder[i]] = i;
        return build(0, inorder.size() - 1);
    }
};
```

**Critical detail:** we process the **right subtree first**. Why? Because postorder is "left, right, root." Reading postorder from the end backward gives: root, right-root, left-root, etc. The right subtree's root comes before the left's (when read backward). So we consume `post[postPos]` and assign it as right-subtree-root first, then left.

Getting this order wrong produces mirrored trees — a subtle bug. Think of it as: the "postPos" counter moves right → left in the postorder array, so build the right subtree before the left.

----------------------------------------

## Step 10: Follow-up Questions

- **Preorder + inorder reconstruction.** Similar structure, but first of preorder is root; process **left subtree first** (since preorder is "root, left, right" — reading from start forward gives left's root next).
- **Handle duplicates in values.** Use indices alongside values; pick the correct instance via context.
- **Avoid allocating subarrays.** We already passed indices instead of copies. Explicit wins.
- **Iterative reconstruction.** Use a stack simulating the recursion. Tricky but possible.
- **Serialize-and-deserialize a tree.** Different problem; use preorder with null markers.
- **What if one traversal is given but the other isn't?** A single traversal (even with null markers in preorder) can uniquely identify the tree, but the reconstruction logic differs.
