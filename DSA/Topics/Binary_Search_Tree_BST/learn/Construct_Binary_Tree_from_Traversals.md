# Construct Binary Tree from Traversals (Preorder + Inorder) — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Construct_Binary_Tree_from_Traversals.md`](../Construct_Binary_Tree_from_Traversals.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: PREORDER's FIRST element is the root. INORDER tells you which values go LEFT vs RIGHT. Same template as Postorder+Inorder, just different direction.** **Read [`Construct_Binary_Tree_from_Inorder_and_Postorder.md`](../../Trees_Binary_Trees/learn/Construct_Binary_Tree_from_Inorder_and_Postorder.md) first.**

**Map of this file (7 short sections):**

1. Read the problem
2. Two crucial observations
3. The recursive construction
4. Index-based with hashmap (O(n))
5. Code
6. Trace it
7. Common pitfalls + the shape

---

## 1. Read the problem

Given two integer arrays `preorder` and `inorder` representing the preorder and inorder traversals of a binary tree with DISTINCT values, reconstruct the tree.

**Example:**

```
preorder = [3, 9, 20, 15, 7]
inorder  = [9, 3, 15, 20, 7]
```

Tree:
```
    3
   / \
  9  20
     / \
    15  7
```

---

## 2. Two crucial observations

> **Mini-refresher: preorder vs postorder for reconstruction.**
>
> - **Preorder** (Root, Left, Right): FIRST element is the ROOT.
> - **Postorder** (Left, Right, Root): LAST element is the ROOT.
> - **Inorder** (Left, Root, Right): root's POSITION splits inorder into LEFT and RIGHT subtree values.
>
> Both Preorder+Inorder and Postorder+Inorder uniquely reconstruct.

For our example:
- Preorder's first = 3 → ROOT is 3.
- In inorder, 3 is at index 1. Values BEFORE: `[9]` (left subtree). AFTER: `[15, 20, 7]` (right subtree).
- Left subtree has 1 node → preorder's next 1 element after root = `[9]` (left preorder).
- Right subtree has 3 nodes → preorder's remaining = `[20, 15, 7]` (right preorder).
- Recurse.

---

## 3. The recursive construction

```
def build(preorder, inorder):
    if not inorder: return None
    root_val = preorder[0]
    root = TreeNode(root_val)
    split = inorder.index(root_val)
    left_inorder  = inorder[:split]
    right_inorder = inorder[split+1:]
    left_preorder  = preorder[1 : 1 + len(left_inorder)]
    right_preorder = preorder[1 + len(left_inorder):]
    root.left  = build(left_preorder, left_inorder)
    root.right = build(right_preorder, right_inorder)
    return root
```

Works but slices arrays → expensive. Use INDEX RANGES + HASHMAP for O(n).

---

## 4. Index-based with hashmap (O(n))

Precompute `inorder_index[value] -> position`. Pass index ranges to avoid copies.

```
inorder_index = {v: i for i, v in enumerate(inorder)}

def build(preStart, inStart, inEnd):
    if inStart > inEnd: return None
    root_val = preorder[preStart]
    root = TreeNode(root_val)
    split = inorder_index[root_val]
    leftSize = split - inStart
    root.left = build(preStart + 1, inStart, split - 1)
    root.right = build(preStart + 1 + leftSize, split + 1, inEnd)
    return root
```

Total time: O(n). Space: O(n) for hashmap + O(h) for recursion.

---

## 5. Code

**C++:**

```cpp
class Solution {
    unordered_map<int, int> indexOf;
    vector<int> pre;

    TreeNode* build(int preStart, int inStart, int inEnd) {
        if (inStart > inEnd) return nullptr;
        int rootVal = pre[preStart];
        TreeNode* root = new TreeNode(rootVal);
        int split = indexOf[rootVal];
        int leftSize = split - inStart;
        root->left = build(preStart + 1, inStart, split - 1);
        root->right = build(preStart + 1 + leftSize, split + 1, inEnd);
        return root;
    }

public:
    TreeNode* buildTree(vector<int>& preorder, vector<int>& inorder) {
        pre = preorder;
        for (int i = 0; i < (int)inorder.size(); ++i) indexOf[inorder[i]] = i;
        return build(0, 0, (int)inorder.size() - 1);
    }
};
```

**Python:**

```python
def buildTree(preorder, inorder):
    inorder_index = {v: i for i, v in enumerate(inorder)}
    def build(pre_start, in_start, in_end):
        if in_start > in_end: return None
        root_val = preorder[pre_start]
        root = TreeNode(root_val)
        split = inorder_index[root_val]
        left_size = split - in_start
        root.left = build(pre_start + 1, in_start, split - 1)
        root.right = build(pre_start + 1 + left_size, split + 1, in_end)
        return root
    return build(0, 0, len(inorder) - 1)
```

Complexity: **O(n) time, O(n) space.**

---

## 6. Trace it

**`preorder = [3, 9, 20, 15, 7]`, `inorder = [9, 3, 15, 20, 7]`.**

Hashmap: `{9:0, 3:1, 15:2, 20:3, 7:4}`.

```
build(preStart=0, inStart=0, inEnd=4):
  root_val = preorder[0] = 3.
  split = 1. leftSize = 1 - 0 = 1.
  
  Left: build(1, 0, 0):
    root_val = preorder[1] = 9.
    split = 0. leftSize = 0.
    Left: build(2, 0, -1) → null.
    Right: build(2, 1, 0) → null.
    Return Node(9).
  
  Right: build(2, 2, 4):
    root_val = preorder[2] = 20.
    split = 3. leftSize = 3 - 2 = 1.
    
    Left: build(3, 2, 2):
      root_val = preorder[3] = 15.
      split = 2. leftSize = 0.
      Children null.
      Return Node(15).
    
    Right: build(4, 4, 4):
      root_val = preorder[4] = 7.
      split = 4. leftSize = 0.
      Children null.
      Return Node(7).
    
    Return Node(20) with left=15, right=7.
  
  Return Node(3) with left=9, right=20-subtree.
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

## 7. Common pitfalls + the shape

**Pitfalls:**

1. **Forgetting the hashmap.** Linear `index_of` per call → O(n²) instead of O(n).

2. **Wrong leftSize.** It's `split - inStart` (size of inorder's left part).

3. **Wrong preorder index for right subtree.** Use `preStart + 1 + leftSize` — skip root + left subtree.

4. **Processing LEFT before RIGHT.** For PREORDER, build LEFT FIRST (since preorder reads `Root, Left, Right` left to right, consuming preorder forward means left's root comes next).
   - **Compare with postorder version:** postorder reads BACKWARD, so RIGHT first.

5. **Slicing instead of index ranges.** Slicing copies arrays → O(n²) space.

**The shape:**

> **"Tree reconstruction: one traversal identifies the ROOT; INORDER splits left/right. Recurse with hashmap for O(n)."**

| Traversals | Root from | Process subtree order |
|---|---|---|
| Preorder + Inorder | first of preorder | LEFT first (forward consumption) |
| Postorder + Inorder | last of postorder | RIGHT first (backward consumption) |
| Level Order + Inorder | first of level order | similar, more complex |

---

## Cross-references

- **Reference card (post-mastery):** [`../Construct_Binary_Tree_from_Traversals.md`](../Construct_Binary_Tree_from_Traversals.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`../../Trees_Binary_Trees/learn/Construct_Binary_Tree_from_Inorder_and_Postorder.md`](../../Trees_Binary_Trees/learn/Construct_Binary_Tree_from_Inorder_and_Postorder.md) — postorder variant.
  - Coming next: [`Queue_Reconstruction_by_Height.md`](./Queue_Reconstruction_by_Height.md) — greedy reconstruction.
