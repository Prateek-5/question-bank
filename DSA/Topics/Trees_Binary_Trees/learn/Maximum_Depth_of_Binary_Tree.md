# Maximum Depth of Binary Tree — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximum_Depth_of_Binary_Tree.md`](../Maximum_Depth_of_Binary_Tree.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/maximum-depth-of-binary-tree/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The canonical post-order tree recursion.** The lesson: **`depth(tree) = 1 + max(depth(left), depth(right))` with `depth(null) = 0`. Three lines.** This recurrence IS the algorithm. Same template solves diameter, balanced check, and many height-related tree problems. **Read [`Binary_Tree_Postorder_Traversal.md`](./Binary_Tree_Postorder_Traversal.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. The recurrence
3. Why this works (induction)
4. Code
5. Trace it
6. The BFS alternative
7. Common pitfalls
8. The shape — post-order aggregation

---

## 1. Read the problem

Given the root of a binary tree, return its **MAXIMUM DEPTH** — the length of the longest root-to-leaf path, counted in NODES.

- Empty tree: depth 0.
- Single node: depth 1.

**Examples:**

- Tree:
  ```
      3
     / \
    9   20
        / \
       15  7
  ```
  Longest path: 3 → 20 → 15 (or 3 → 20 → 7). **Depth = 3.**

- Tree `[1, null, 2]`: 1 → 2. Depth = 2.

---

## 2. The recurrence

> **Mini-refresher: tree depth defined recursively.**
>
> What's the depth of a tree?
> - If the tree is EMPTY: 0.
> - Otherwise: 1 (for the root) + the depth of the DEEPER subtree (max of left and right depths).
>
> Mathematically:
> ```
> depth(null) = 0
> depth(node) = 1 + max(depth(node.left), depth(node.right))
> ```

The recurrence IS the algorithm.

---

## 3. Why this works (induction)

> **Mini-refresher: induction on tree size.**
>
> Claim: `depth(t)` equals the longest root-to-leaf path length.
>
> **Base case:** empty tree. No nodes → no path → depth 0. ✓
>
> **Inductive step:** assume the formula works for all smaller subtrees. For a non-null `node`:
> - Any root-to-leaf path through `node` goes ROOT → one of (left, right) → ... → leaf.
> - The path length = 1 (for node) + path length from that child to a leaf.
> - By induction, `depth(node.left)` is the longest such for left, and `depth(node.right)` for right.
> - The MAX over the two children's depths, plus 1, is the longest path through `node`.
>
> So `depth(node) = 1 + max(depth(left), depth(right))`. ✓

Inductive proof is short and watertight. The recurrence handles all trees.

---

## 4. Code

**C++:**

```cpp
int maxDepth(TreeNode* root) {
    if (!root) return 0;
    return 1 + max(maxDepth(root->left), maxDepth(root->right));
}
```

**Python:**

```python
def maxDepth(root):
    if not root: return 0
    return 1 + max(maxDepth(root.left), maxDepth(root.right))
```

**JavaScript:**

```javascript
function maxDepth(root) {
    if (!root) return 0;
    return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
}
```

THREE LINES. The recurrence is the code.

Complexity: **O(n) time** (visit each node once), **O(h) space** (recursion stack, h = tree height).

---

## 5. Trace it

**Tree:**
```
    3
   / \
  9   20
      / \
     15  7
```

```
maxDepth(3):
  maxDepth(9):
    maxDepth(null left) = 0
    maxDepth(null right) = 0
    return 1 + max(0, 0) = 1
  maxDepth(20):
    maxDepth(15):
      null children → returns 1
    maxDepth(7):
      null children → returns 1
    return 1 + max(1, 1) = 2
  return 1 + max(1, 2) = 3

Final: 3.  ✓
```

Each non-null node returns `1 + max(left_depth, right_depth)`. Nulls return 0.

---

## 6. The BFS alternative

If the tree could be VERY deep (recursion overflows), use BFS-based level counting:

```
if not root: return 0
queue = [root]
depth = 0
while queue:
    size = len(queue)
    for _ in range(size):
        node = queue.popleft()
        if node.left:  queue.append(node.left)
        if node.right: queue.append(node.right)
    depth += 1
return depth
```

Same level-snapshot trick as Level Order Traversal. Each outer iteration processes one level; increment depth. When queue is empty, depth = number of levels = max depth.

O(n) time, O(w) space (where w is the max width).

---

## 7. Common pitfalls

1. **`depth(null) = 1` instead of 0.** Off-by-one — would inflate depth by 1 throughout.

2. **Using `max(maxDepth(left), maxDepth(right)) + 1` only for non-leaf nodes.** Leaves correctly return 1 = 1 + max(0, 0). No special case needed.

3. **Computing `min` instead of `max`.** That would give MINIMUM depth (different problem — and careful: min depth has its own gotcha around single-child nodes).

4. **Using a global variable.** Unnecessary — return values suffice.

5. **Treating depth as "number of edges" instead of "number of nodes."** Convention varies; the LeetCode problem uses node count. A single-node tree has depth 1.

6. **Stack overflow on deep trees.** Use BFS or convert to iterative DFS with explicit stack.

---

## 8. The shape — post-order aggregation

The pattern this problem teaches:

> **"For tree properties computed from subtree information, use POST-ORDER recursion: recurse left, recurse right, combine results."**

| Problem | Combine function |
|---|---|
| **This problem** (depth) | `1 + max(left, right)` |
| Count nodes | `1 + left + right` |
| Sum of nodes | `node.val + left + right` |
| Diameter | tracks max of `left + right` via reference, returns height |
| Balanced check | returns -1 if unbalanced, else height |
| LCA | propagates "found" boolean |
| Subtree-sum tree problems | sum of subtree |
| Convert to linked list | flatten subtree |
| Path sum from root | accumulate; check at leaves |

**Pattern to internalize:**

> "Tree problems that compute a SUBTREE PROPERTY follow the same shape: recursively compute the property for LEFT and RIGHT, COMBINE the results, return. This IS post-order recursion."

---

> **Self-check — the question to ask next time.**
>
> When you face a tree task asking for a SUBTREE PROPERTY (depth, size, sum, etc.), ask:
>
> > **"Can I write `f(node) = combine(node.val, f(left), f(right))` with `f(null) = base_case`? That's post-order recursion."**
>
> If yes, three lines of code.

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximum_Depth_of_Binary_Tree.md`](../Maximum_Depth_of_Binary_Tree.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Binary_Tree_Postorder_Traversal.md`](./Binary_Tree_Postorder_Traversal.md), [`Binary_Tree_Level_Order_Traversal.md`](./Binary_Tree_Level_Order_Traversal.md).
  - Coming next: [`Balanced_Binary_Tree.md`](./Balanced_Binary_Tree.md) — depth + balance in one pass.
