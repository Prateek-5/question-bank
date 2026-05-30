# Path Sum — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Path_Sum.md`](../Path_Sum.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/path-sum/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/path-sum/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The introduction to the path-sum family.** The lesson: **DFS with a running ACCUMULATOR (or remaining target). At each leaf, check if the path completes the target.** Same template solves Path Sum II (collect paths), Sum Root to Leaf, Maximum Path Sum (root-to-leaf variant). **Read [`Maximum_Depth_of_Binary_Tree.md`](./Maximum_Depth_of_Binary_Tree.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. The DFS recurrence
3. Two equivalent formulations
4. Code
5. Trace it
6. Edge cases
7. Common pitfalls
8. The shape — path-walking DFS

---

## 1. Read the problem

Given a binary tree and an integer `targetSum`, return `true` if there is a **ROOT-TO-LEAF PATH** whose values sum to `targetSum`.

> **Mini-refresher: ROOT-TO-LEAF specifically.**
>
> The path must START at the root and END at a LEAF (a node with NO CHILDREN). Internal nodes and partial paths don't count.

**Examples:**

- Tree:
  ```
         5
        / \
       4   8
      /   / \
     11  13  4
    /  \      \
   7    2      1
  ```
  `targetSum = 22`. Path `5 → 4 → 11 → 2` sums to 22. Return **true**.

- Tree `[1, 2, 3]`, target 5: paths are `1→2`=3 and `1→3`=4. Neither matches. Return **false**.

- Empty tree, target anything: no path exists. Return **false**.

---

## 2. The DFS recurrence

> **Mini-refresher: track "remaining target" while walking.**
>
> As we descend, subtract each node's value from the target. At a LEAF, check if the remaining target equals the leaf's value (meaning the full path sums to the original target).
>
> Equivalently: track the running SUM and check at a leaf if it equals target. Both forms work.

Recurrence:

```
hasPathSum(node, remaining):
    if node is null: return False
    if node is a leaf: return node.val == remaining
    return hasPathSum(node.left,  remaining - node.val)
        or hasPathSum(node.right, remaining - node.val)
```

OR (equivalent, tracking accumulated sum):

```
hasPathSum(node, cur_sum, target):
    if node is null: return False
    cur_sum += node.val
    if node is leaf: return cur_sum == target
    return hasPathSum(node.left, cur_sum, target) or hasPathSum(node.right, cur_sum, target)
```

Initial call: `hasPathSum(root, targetSum)`.

---

## 3. Two equivalent formulations

The "remaining target" form:

```
return hasPathSum(node.left, remaining - node.val) or hasPathSum(node.right, remaining - node.val)
```

The "accumulating sum" form:

```
cur_sum += node.val
if leaf: return cur_sum == target
return ... or ...
```

> **Mini-refresher: which is better?**
>
> "Remaining" form: fewer parameters; subtraction at each call.
> "Accumulating" form: extra parameter (cur_sum); easier to debug (you SEE the running total).
>
> Both are correct. Pick whichever feels clearer. Most interview solutions use "remaining."

---

## 4. Code

**C++:**

```cpp
bool hasPathSum(TreeNode* root, int targetSum) {
    if (!root) return false;
    if (!root->left && !root->right) {
        return root->val == targetSum;
    }
    int remaining = targetSum - root->val;
    return hasPathSum(root->left, remaining)
        || hasPathSum(root->right, remaining);
}
```

**Python:**

```python
def hasPathSum(root, targetSum):
    if not root: return False
    if not root.left and not root.right:
        return root.val == targetSum
    remaining = targetSum - root.val
    return hasPathSum(root.left, remaining) or hasPathSum(root.right, remaining)
```

**JavaScript:**

```javascript
function hasPathSum(root, targetSum) {
    if (!root) return false;
    if (!root.left && !root.right) return root.val === targetSum;
    const remaining = targetSum - root.val;
    return hasPathSum(root.left, remaining) || hasPathSum(root.right, remaining);
}
```

Complexity: **O(n) time, O(h) space.**

---

## 5. Trace it

**Tree:**
```
       5
      / \
     4   8
    /   / \
   11  13  4
  /  \      \
 7    2      1
```
**targetSum = 22.**

```
hasPathSum(5, 22):
  Not leaf. remaining = 17.
  hasPathSum(4, 17):
    Not leaf. remaining = 13.
    hasPathSum(11, 13):
      Not leaf. remaining = 2.
      hasPathSum(7, 2):
        LEAF. 7 == 2? NO. Return false.
      hasPathSum(2, 2):
        LEAF. 2 == 2? YES. Return TRUE.
      → 11 returns true (OR short-circuits).
    → 4 returns true.
  → 5 returns TRUE.

Return true.  ✓
```

The `||` short-circuit means once one path matches, we don't explore the other.

---

## 6. Edge cases

- **Empty tree (`root = null`):** no path exists. Return false. ✓ (Base case.)

- **Single-node tree:** root is also a leaf. Check `root.val == targetSum`.

- **All nodes negative; target negative.** Arithmetic works for negative values.

- **`targetSum = 0`** with a tree of zeros: there might or might not be a path. Algorithm handles it.

---

## 7. Common pitfalls

1. **Forgetting the LEAF check.** Without it, you'd accept any partial path (e.g., root-to-internal-node). Must check `node.left == null AND node.right == null`.

2. **Returning true at internal nodes** when `remaining == 0`. WRONG — even if you've accumulated to the right sum, you need to be AT A LEAF.

3. **Returning false on null nodes**, but treating "node with one missing child" as a leaf. NO — a node with one child is NOT a leaf. The leaf check requires BOTH children null.

4. **Off-by-one in remaining.** Use `remaining - node.val` when recursing INTO children (the child handles the rest of the path).

5. **Using OR but writing `+` or `&&`.** OR is correct (any path that works → return true).

6. **Treating leaves with `node == null`.** Null nodes are NOT leaves; they're missing. Leaves are real nodes with no children.

---

## 8. The shape — path-walking DFS

The pattern this problem teaches:

> **"Walk root-to-leaf paths with a RUNNING STATE (sum, count, accumulated value). At each leaf, check if the state satisfies the goal."**

| Problem | State at each node | Goal at leaf |
|---|---|---|
| **This problem** | remaining target | `node.val == remaining` |
| Path Sum II | path so far | record path if sum matches |
| Sum Root to Leaf Numbers | accumulated number (10*acc + node.val) | sum into total |
| Max Root-to-Leaf Path Sum | running sum | track max |
| Smallest String from Leaf | path string | compare lex |
| Binary Tree Paths (return all) | path string | snapshot at leaf |

**Pattern to internalize:**

> "Root-to-leaf path problems follow the same shape: DFS with an accumulator, check at leaves. The traversal is always preorder-style (process node, then recurse)."

---

> **Self-check — the question to ask next time.**
>
> When you face "is there a path from root to leaf with property P," ask:
>
> > **"Can I DFS with an accumulator, checking property P at each LEAF?"**
>
> If yes, you've got the template.

---

## Cross-references

- **Reference card (post-mastery):** [`../Path_Sum.md`](../Path_Sum.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Maximum_Depth_of_Binary_Tree.md`](./Maximum_Depth_of_Binary_Tree.md).
  - Coming next: [`Path_Sum_II.md`](./Path_Sum_II.md), [`Path_Sum_III.md`](./Path_Sum_III.md).
