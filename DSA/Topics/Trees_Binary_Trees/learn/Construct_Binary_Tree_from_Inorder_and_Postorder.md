# Construct Binary Tree from Inorder and Postorder — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Construct_Binary_Tree_from_Inorder_and_Postorder.md`](../Construct_Binary_Tree_from_Inorder_and_Postorder.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/construct-binary-tree-from-inorder-and-postorder-traversal/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/construct-binary-tree-from-inorder-and-postorder-traversal/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The lesson: LAST of postorder is the ROOT. Inorder TELLS YOU which values are LEFT vs RIGHT subtree. Recurse.** Same idea applies to preorder+inorder. Precompute inorder positions with a hashmap for O(n). **Read [`Binary_Tree_Postorder_Traversal.md`](./Binary_Tree_Postorder_Traversal.md) and [`Binary_Tree_Inorder_Traversal.md`](./Binary_Tree_Inorder_Traversal.md) first.**

**Map of this file (10 sections):**

1. Read the problem
2. Two crucial observations
3. The recursive construction
4. Index-based recursion (efficient)
5. Why we process RIGHT first
6. Code
7. Trace it
8. Why this is unique
9. Common pitfalls
10. The shape — reconstruct from traversals

---

## 1. Read the problem

Given two integer arrays `inorder` and `postorder`, where `inorder` is the inorder traversal and `postorder` is the postorder traversal of a binary tree with DISTINCT values, **reconstruct and return the binary tree**.

**Example:**

```
inorder  = [9, 3, 15, 20, 7]
postorder = [9, 15, 7, 20, 3]
```

Reconstruct:
```
    3
   / \
  9  20
     / \
    15  7
```

---

## 2. Two crucial observations

> **Mini-refresher: what each traversal tells us.**
>
> **Postorder** = Left, Right, Root. So the LAST element of postorder is the ROOT.
>
> **Inorder** = Left, Root, Right. Once you know the root's value, finding its POSITION in inorder splits inorder into:
> - Everything LEFT of the root = LEFT SUBTREE's inorder.
> - Everything RIGHT of the root = RIGHT SUBTREE's inorder.

For our example:
- Postorder ends with **3** → root is 3.
- In inorder `[9, 3, 15, 20, 7]`, 3 is at position 1.
  - Left subtree inorder: `[9]`.
  - Right subtree inorder: `[15, 20, 7]`.

Now recursively build left and right subtrees, slicing both arrays accordingly.

---

## 3. The recursive construction

```
build(inorder, postorder):
    if either is empty: return null
    root_val = postorder[last]
    root_pos = index of root_val in inorder
    L = root_pos                             # number of left-subtree nodes
    
    left_inorder  = inorder[0..L-1]
    right_inorder = inorder[L+1..]
    left_postorder  = postorder[0..L-1]
    right_postorder = postorder[L..second-to-last]
    
    root = TreeNode(root_val)
    root.left  = build(left_inorder, left_postorder)
    root.right = build(right_inorder, right_postorder)
    return root
```

Slicing is intuitive but inefficient (each call copies sub-arrays). For O(n), use INDEX RANGES into the original arrays + a hashmap of inorder positions.

---

## 4. Index-based recursion (efficient)

> **Mini-refresher: pass index ranges, not slices.**
>
> Instead of `inorder[0..L-1]` (which copies), pass index endpoints: `inStart, inEnd`. Same for postorder. Recurse on shrinking ranges. No copies.
>
> Plus: precompute `inorder_index[value] -> position` as a hashmap. O(1) lookup vs O(n) linear search.

```
inorder_index = {value: position for position, value in enumerate(inorder)}
post_pos = len(postorder) - 1     # global; decrements as we consume postorder

build(in_start, in_end):
    if in_start > in_end: return null
    root_val = postorder[post_pos]
    post_pos -= 1
    root_pos = inorder_index[root_val]
    
    root = TreeNode(root_val)
    # Process RIGHT first (see Section 5)
    root.right = build(root_pos + 1, in_end)
    root.left = build(in_start, root_pos - 1)
    return root
```

Time: each node visited once. **O(n).**

---

## 5. Why we process RIGHT first

> **Mini-refresher: postorder consumed BACKWARD.**
>
> Postorder is Left, Right, Root. Reading FROM THE END BACKWARD: Root, Right (subtree's root next), Left (subtree's root).
>
> So when we consume `postorder[post_pos]` and decrement, the NEXT value (one step back) is the RIGHT SUBTREE's root. Building the right subtree first uses these values in the correct order.

If we built left first, we'd be consuming the wrong values from postorder (off by the right-subtree size).

**Process right subtree BEFORE left.** This is the subtle gotcha.

---

## 6. Code

**C++:**

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

        root->right = build(rootPos + 1, inEnd);    // RIGHT first
        root->left  = build(inStart, rootPos - 1);
        return root;
    }

public:
    TreeNode* buildTree(vector<int>& inorder, vector<int>& post) {
        postorder = post;
        postPos = post.size() - 1;
        for (int i = 0; i < (int)inorder.size(); ++i) {
            inorderIndex[inorder[i]] = i;
        }
        return build(0, inorder.size() - 1);
    }
};
```

**Python:**

```python
def buildTree(inorder, postorder):
    inorder_index = {v: i for i, v in enumerate(inorder)}
    self_post = postorder[:]
    pos = [len(postorder) - 1]    # mutable counter
    
    def build(in_start, in_end):
        if in_start > in_end: return None
        root_val = self_post[pos[0]]
        pos[0] -= 1
        root = TreeNode(root_val)
        root_pos = inorder_index[root_val]
        # RIGHT first
        root.right = build(root_pos + 1, in_end)
        root.left  = build(in_start, root_pos - 1)
        return root
    
    return build(0, len(inorder) - 1)
```

Complexity: **O(n) time, O(n) space.**

---

## 7. Trace it

**`inorder = [9, 3, 15, 20, 7]`, `postorder = [9, 15, 7, 20, 3]`.**

Hashmap: `{9: 0, 3: 1, 15: 2, 20: 3, 7: 4}`. `postPos = 4`.

```
build(0, 4):
  root_val = postorder[4] = 3. postPos = 3.
  root_pos = 1.
  root = Node(3).
  
  build right (root_pos + 1 = 2, in_end = 4):
    root_val = postorder[3] = 20. postPos = 2.
    root_pos = 3.
    root = Node(20).
    
    build right (4, 4):
      root_val = postorder[2] = 7. postPos = 1.
      root_pos = 4.
      root = Node(7).
      build right (5, 4): in_start > in_end → null.
      build left (4, 3): in_start > in_end → null.
      Return Node(7).
    
    build left (2, 2):
      root_val = postorder[1] = 15. postPos = 0.
      root_pos = 2.
      root = Node(15).
      build right (3, 2): null.
      build left (2, 1): null.
      Return Node(15).
    
    Return Node(20) with right=7, left=15.
  
  build left (0, 0):
    root_val = postorder[0] = 9. postPos = -1.
    root_pos = 0.
    root = Node(9).
    build right (1, 0): null.
    build left (0, -1): null.
    Return Node(9).
  
  Return Node(3) with right=20-subtree, left=9.
```

Tree:
```
    3
   / \
  9  20
     / \
    15  7
```
✓

---

## 8. Why this is unique

> **Mini-refresher: inorder + postorder uniquely identifies a tree.**
>
> Postorder fixes the ROOT (last element). Inorder split fixes which values are LEFT vs RIGHT.
>
> Recursion fixes subtrees by induction.
>
> All nodes' positions are determined → unique tree.
>
> NOTE: This requires DISTINCT values. With duplicates, the recursion can't tell which occurrence in inorder corresponds to the root.

**Preorder + Postorder alone is NOT unique** — they can't always distinguish "one child left vs right" when a node has one child.

**Inorder is essential** for unique reconstruction. Pairing inorder with preorder OR postorder works.

---

## 9. Common pitfalls

1. **Processing LEFT subtree first.** Wrong! Postorder read backward gives Right first. Process RIGHT first.

2. **Forgetting the hashmap.** Without it, linear search makes each call O(n) → total O(n²).

3. **Wrong slicing.** Need to compute left/right subtree lengths from inorder; use `root_pos - in_start` to find left length.

4. **Off-by-one in indices.** `root_pos + 1` to `in_end` for right; `in_start` to `root_pos - 1` for left.

5. **Decrementing `postPos` at the wrong time.** Decrement AFTER reading, BEFORE the recursive calls.

6. **Using global `postPos` without care.** It MUST be modified by RIGHT first, so the recursion sees the correct value when building LEFT.

7. **Failing on empty input.** Check `in_start > in_end` for null.

---

## 10. The shape — reconstruct from traversals

The pattern this problem teaches:

> **"From traversal arrays, identify the ROOT and SPLIT the tree. Recurse on subtrees."**

| Traversals given | Identify root from | Identify subtree split via |
|---|---|---|
| **Inorder + Postorder (this)** | last of postorder | root's position in inorder |
| Inorder + Preorder | first of preorder | root's position in inorder |
| Preorder + Postorder (NOT UNIQUE in general) | first of preorder | second of preorder (next root, if it exists) |
| Level Order + Inorder | first of level order at root's level | root's position in inorder |
| Just Preorder with null markers | inorder isn't needed; nulls signal subtree boundaries | preorder structure |

**Pattern to internalize:**

> "For tree reconstruction: ONE traversal tells you the ROOT (first or last). INORDER tells you the LEFT/RIGHT split. Recurse on subtrees."

---

> **Self-check — the question to ask next time.**
>
> When given two traversal arrays and asked to reconstruct, ask:
>
> > **"Which traversal identifies the root? Use inorder to split into left/right subtrees. Recurse, with hashmap for O(n)."**
>
> If yes, you've got the reconstruction template.

---

## Cross-references

- **Reference card (post-mastery):** [`../Construct_Binary_Tree_from_Inorder_and_Postorder.md`](../Construct_Binary_Tree_from_Inorder_and_Postorder.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Binary_Tree_Postorder_Traversal.md`](./Binary_Tree_Postorder_Traversal.md), [`Binary_Tree_Inorder_Traversal.md`](./Binary_Tree_Inorder_Traversal.md).
  - Trees topic COMPLETE!
  - Next topic: Binary_Search_Tree_BST.
