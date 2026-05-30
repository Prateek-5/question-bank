# Binary Tree Left Side View — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Binary_Tree_Left_Side_View.md`](../Binary_Tree_Left_Side_View.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://www.geeksforgeeks.org/print-left-view-binary-tree/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/print-left-view-binary-tree/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **Symmetric mirror of Right Side View.** The lesson: **same template; emit the FIRST node (leftmost) per level instead of the last.** **Read [`Binary_Tree_Right_Side_View.md`](./Binary_Tree_Right_Side_View.md) first.**

**Map of this file (6 short sections):**

1. Read the problem
2. The BFS approach
3. Code
4. Trace it
5. The DFS alternative (left-first)
6. The shape — symmetric to right view

---

## 1. Read the problem

Standing to the LEFT of a binary tree, return the values of nodes you can SEE, top to bottom.

At each level, you see the LEFTMOST node.

**Example:**
```
   1
  / \
 2   3
  \   \
   5   4
```

- Level 0: 1.
- Level 1: 2 (leftmost).
- Level 2: 5 (leftmost; comes before 4).

Return `[1, 2, 5]`.

---

## 2. The BFS approach

Standard BFS with size snapshot. Emit the FIRST node of each level (index 0 in the inner loop).

```
while queue:
    size = len(queue)
    for i in range(size):
        node = queue.popleft()
        if i == 0:
            result.append(node.val)         # FIRST in this level → leftmost
        if node.left: queue.append(node.left)
        if node.right: queue.append(node.right)
```

Only difference from Right Side View: `if i == 0` instead of `if i == size - 1`.

---

## 3. Code

**C++:**

```cpp
vector<int> leftSideView(TreeNode* root) {
    vector<int> result;
    if (!root) return result;
    queue<TreeNode*> q;
    q.push(root);
    while (!q.empty()) {
        int size = q.size();
        for (int i = 0; i < size; ++i) {
            TreeNode* node = q.front(); q.pop();
            if (i == 0) result.push_back(node->val);
            if (node->left) q.push(node->left);
            if (node->right) q.push(node->right);
        }
    }
    return result;
}
```

**Python:**

```python
from collections import deque

def leftSideView(root):
    if not root: return []
    result = []
    q = deque([root])
    while q:
        size = len(q)
        for i in range(size):
            node = q.popleft()
            if i == 0:
                result.append(node.val)
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
    return result
```

Complexity: **O(n) time, O(w) space.**

---

## 4. Trace it

**Tree** above.

```
q = [1]. result = [].

Level 0 (size=1):
  i=0: pop 1. FIRST → record 1. result = [1].
  Push 2, 3.

Level 1 (size=2):
  i=0: pop 2. FIRST → record 2. result = [1, 2]. Push 5.
  i=1: pop 3. NOT first. Push 4.

Level 2 (size=2):
  i=0: pop 5. FIRST → record 5. result = [1, 2, 5].
  i=1: pop 4. NOT first.

Return [1, 2, 5].  ✓
```

---

## 5. The DFS alternative (left-first)

```
result = []
def dfs(node, depth):
    if not node: return
    if depth == len(result):
        result.append(node.val)             # FIRST visit at this depth = LEFTMOST
    dfs(node.left, depth + 1)               # LEFT first
    dfs(node.right, depth + 1)

dfs(root, 0)
```

Symmetric to Right Side View's DFS — just recurse LEFT first.

---

## 6. The shape — symmetric to right view

| View | Per-level pick |
|---|---|
| Right Side View | LAST (index size-1) |
| **This problem** (Left Side View) | FIRST (index 0) |

Same BFS template, different filter.

> **Mini-refresher: many tree views follow the same template.**
>
> "Side views" of a tree (left, right, top, bottom) all share the BFS-by-level structure. They differ in WHICH NODE per level to emit:
> - Left view: first per level (leftmost).
> - Right view: last per level (rightmost).
> - Top view: track by horizontal distance from root; remember first at each distance.
> - Bottom view: track by horizontal distance; remember LAST at each distance (deepest).

---

## Cross-references

- **Reference card (post-mastery):** [`../Binary_Tree_Left_Side_View.md`](../Binary_Tree_Left_Side_View.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Binary_Tree_Right_Side_View.md`](./Binary_Tree_Right_Side_View.md).
  - Coming next: [`All_Elements_in_Two_BSTs.md`](./All_Elements_in_Two_BSTs.md), [`Merge_Two_BSTs.md`](./Merge_Two_BSTs.md), [`Construct_Binary_Tree_from_Traversals.md`](./Construct_Binary_Tree_from_Traversals.md), [`Queue_Reconstruction_by_Height.md`](./Queue_Reconstruction_by_Height.md).
