# Binary Tree Right Side View — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Binary_Tree_Right_Side_View.md`](../Binary_Tree_Right_Side_View.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/binary-tree-right-side-view/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **A BFS-based "per-level" problem.** The lesson: **iterate level by level; emit the LAST node of each level (which is the rightmost). Snapshot the queue size at the start of each level.** Same template solves Left Side View, Level Averages, Largest in Each Row. **Read [`Binary_Tree_Level_Order_Traversal.md`](../../Trees_Binary_Trees/learn/Binary_Tree_Level_Order_Traversal.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. The BFS approach
3. The "last-at-level" extraction
4. Code
5. Trace it
6. The DFS alternative (right-first)
7. Common pitfalls
8. The shape — per-level extraction

---

## 1. Read the problem

Standing to the RIGHT of a binary tree, return the values of nodes you can SEE, from top to bottom.

At each LEVEL, you see the RIGHTMOST node (others are blocked).

**Example:**
```
   1
  / \
 2   3
  \   \
   5   4
```

- Level 0: see 1.
- Level 1: see 3 (rightmost; 2 is blocked).
- Level 2: see 4 (rightmost; 5 is blocked).

Return `[1, 3, 4]`.

> **Mini-refresher: "rightmost per level" — NOT just right children.**
>
> The rightmost node at a level is the LAST one encountered in left-to-right traversal of that level. It might be the right child of a parent, OR a left child if its sibling tree doesn't extend that deep.

---

## 2. The BFS approach

> **Mini-refresher: per-level BFS with the size-snapshot trick.**
>
> Standard level-order BFS:
> ```
> while queue:
>     size = len(queue)
>     for _ in range(size):
>         node = queue.popleft()
>         # process node
>         if node.left: queue.append(node.left)
>         if node.right: queue.append(node.right)
> ```
> The `size = len(queue)` snapshot is the count of THIS LEVEL'S nodes. We process them in the inner loop, leaving the next level in the queue.

To get the RIGHTMOST per level, take the LAST node in the inner loop (the one at index `size - 1`).

---

## 3. The "last-at-level" extraction

```
while queue:
    size = len(queue)
    for i in range(size):
        node = queue.popleft()
        if i == size - 1:
            result.append(node.val)              # LAST in this level → rightmost
        if node.left: queue.append(node.left)
        if node.right: queue.append(node.right)
```

The `i == size - 1` check fires once per level — on the last iteration of the inner loop. That node IS the rightmost.

---

## 4. Code

**C++:**

```cpp
vector<int> rightSideView(TreeNode* root) {
    vector<int> result;
    if (!root) return result;
    queue<TreeNode*> q;
    q.push(root);
    while (!q.empty()) {
        int size = q.size();
        for (int i = 0; i < size; ++i) {
            TreeNode* node = q.front(); q.pop();
            if (i == size - 1) {
                result.push_back(node->val);
            }
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

def rightSideView(root):
    if not root: return []
    result = []
    q = deque([root])
    while q:
        size = len(q)
        for i in range(size):
            node = q.popleft()
            if i == size - 1:
                result.append(node.val)
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
    return result
```

Complexity: **O(n) time, O(w) space** (w = max width).

---

## 5. Trace it

**Tree:**
```
   1
  / \
 2   3
  \   \
   5   4
```

```
q = [1]. result = [].

Level 0 (size=1):
  i=0: pop 1. i == size-1 → record 1. result = [1].
  Push 2, 3.
q = [2, 3].

Level 1 (size=2):
  i=0: pop 2. NOT last. Push 5 (only right child).
  i=1: pop 3. LAST → record 3. result = [1, 3]. Push 4.
q = [5, 4].

Level 2 (size=2):
  i=0: pop 5. NOT last. No children.
  i=1: pop 4. LAST → record 4. result = [1, 3, 4]. No children.
q = [].

Return [1, 3, 4].  ✓
```

---

## 6. The DFS alternative (right-first)

```
result = []
def dfs(node, depth):
    if not node: return
    if depth == len(result):              # first node at this depth
        result.append(node.val)
    dfs(node.right, depth + 1)            # RIGHT first
    dfs(node.left, depth + 1)

dfs(root, 0)
return result
```

**Right-first preorder DFS.** The FIRST node encountered at any depth is automatically the RIGHTMOST (since we recurse right first).

The check `depth == len(result)` records the FIRST visit at each new depth.

Trace on the example:

```
dfs(1, 0): len=0, depth=0 → record 1.
  dfs(3, 1): len=1, depth=1 → record 3.
    dfs(4, 2): len=2, depth=2 → record 4.
    dfs(null, 3).
  dfs(null, 2).
  dfs(2, 1): len=3, depth=1 → 3 != 1, don't record.
    dfs(5, 2): len=3, depth=2 → 3 != 2, don't record.
    dfs(null, 3).
  dfs(null, 2).

result = [1, 3, 4]. ✓
```

Same output. Both approaches are O(n) time.

---

## 7. Common pitfalls

1. **Confusing "rightmost" with "right child."** The rightmost node at a level might be a LEFT child of some parent (if that subtree doesn't reach as deep).

2. **In BFS: forgetting to snapshot `size`.** Without it, the inner loop runs while the queue grows — never separates levels.

3. **In DFS: recursing LEFT first.** Then the first-visited-at-depth would be the LEFTMOST, giving Left Side View instead.

4. **Recording at index 0 instead of size-1.** That would be Left Side View.

5. **Returning the LEFTMOST node at a level when no right-side nodes exist.** Correct — that IS the rightmost. Don't filter.

6. **Forgetting the empty-tree case.** Return [].

---

## 8. The shape — per-level extraction

The pattern:

> **"For tree problems asking for ONE NODE per level (rightmost, leftmost, max, average), use BFS with size-snapshot, emit ONE node per level based on the criterion."**

| Problem | What to emit per level |
|---|---|
| **This problem** | LAST node (rightmost) |
| Left Side View | FIRST node (leftmost) |
| Largest Value in Each Row | MAX value at each level |
| Average of Levels | average of all values |
| Level Order Traversal | ALL nodes (per-level list) |
| Minimum Depth | depth of first leaf encountered |
| Right Side View II (level-by-level with prev pointers) | similar BFS variant |

**Pattern to internalize:**

> "PER-LEVEL extraction = BFS with size-snapshot + filter/aggregate per level. Two lines of customization on the standard BFS template."

---

## Cross-references

- **Reference card (post-mastery):** [`../Binary_Tree_Right_Side_View.md`](../Binary_Tree_Right_Side_View.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`../../Trees_Binary_Trees/learn/Binary_Tree_Level_Order_Traversal.md`](../../Trees_Binary_Trees/learn/Binary_Tree_Level_Order_Traversal.md).
  - Coming next: [`Binary_Tree_Left_Side_View.md`](./Binary_Tree_Left_Side_View.md) — symmetric.
