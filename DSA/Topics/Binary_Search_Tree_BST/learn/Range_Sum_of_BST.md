# Range Sum of BST — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Range_Sum_of_BST.md`](../Range_Sum_of_BST.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/range-sum-of-bst/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/range-sum-of-bst/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The introduction to BST property exploitation.** The lesson: **the BST ordering lets you PRUNE entire subtrees from a range query — if `node.val < low`, skip the LEFT subtree entirely (all values there are < node.val < low).** Same template solves range count, range list, range min/max. **Read [`Binary_Tree_Inorder_Traversal.md`](../../Trees_Binary_Trees/learn/Binary_Tree_Inorder_Traversal.md) first** for the BST → sorted intuition.

**Map of this file (8 short sections):**

1. Read the problem
2. The naive O(n) traversal
3. The BST pruning insight
4. The three cases
5. Code
6. Trace it
7. Common pitfalls
8. The shape — BST range queries

---

## 1. Read the problem

Given the root of a **BST** and integers `low` and `high`, return the SUM of all node values where `low <= val <= high`.

**Example:**

```
       10
      /  \
     5   15
    / \    \
   3   7   18
```
`low = 7, high = 15`. In-range nodes: 7, 10, 15. **Sum = 32.**

---

## 2. The naive O(n) traversal

Visit every node; sum values in range.

```
def rangeSum(node, low, high):
    if not node: return 0
    s = 0
    if low <= node.val <= high: s += node.val
    return s + rangeSum(node.left, low, high) + rangeSum(node.right, low, high)
```

O(n). Works on ANY tree (BST or not).

But the BST property gives us PRUNING power.

---

## 3. The BST pruning insight

> **Mini-refresher: BST invariant.**
>
> For any BST node N:
> - All values in N's LEFT subtree are LESS than N.val.
> - All values in N's RIGHT subtree are GREATER than N.val.

**Pruning logic at each node:**

- **If `node.val < low`**: the WHOLE LEFT SUBTREE has values < node.val < low → ALL out of range. **Skip the left subtree.** But the right subtree might have in-range values. Recurse right only.

- **If `node.val > high`**: the WHOLE RIGHT SUBTREE has values > node.val > high → ALL out of range. **Skip the right subtree.** Recurse left only.

- **If `low <= node.val <= high`**: include node.val in the sum. Both subtrees MAY have in-range values; recurse into both.

---

## 4. The three cases

```
def rangeSum(node, low, high):
    if not node: return 0
    
    if node.val < low:
        return rangeSum(node.right, low, high)   # skip left
    if node.val > high:
        return rangeSum(node.left, low, high)    # skip right
    # in range
    return node.val + rangeSum(node.left, low, high) + rangeSum(node.right, low, high)
```

Three branches matching the three cases. Each branch either makes ONE recursive call (pruning the other side) or TWO calls (when current is in range).

> **Mini-refresher: why the pruning is SAFE.**
>
> If `node.val < low`, the BST invariant guarantees ALL left-subtree values < node.val < low. So no in-range values exist in the left subtree. Skipping it is correctness-preserving.

---

## 5. Code

**C++:**

```cpp
int rangeSumBST(TreeNode* root, int low, int high) {
    if (!root) return 0;
    if (root->val < low)  return rangeSumBST(root->right, low, high);
    if (root->val > high) return rangeSumBST(root->left, low, high);
    return root->val
         + rangeSumBST(root->left, low, high)
         + rangeSumBST(root->right, low, high);
}
```

Six lines.

**Python:**

```python
def rangeSumBST(root, low, high):
    if not root: return 0
    if root.val < low:  return rangeSumBST(root.right, low, high)
    if root.val > high: return rangeSumBST(root.left, low, high)
    return root.val + rangeSumBST(root.left, low, high) + rangeSumBST(root.right, low, high)
```

Complexity: **O(n) worst case** (range covers everything), **O(log n + k)** typical (k = nodes in range, balanced tree). **O(h) space.**

---

## 6. Trace it

**Tree** as in Section 1. `low=7, high=15`.

```
rangeSum(10):
  10 in [7, 15] → include 10. Recurse both.
  rangeSum(5):
    5 < 7 → skip left. Recurse right only.
    rangeSum(7):
      7 in [7, 15] → include 7. Recurse both.
      Both children null → return 7.
    Return 7.
  rangeSum(15):
    15 in [7, 15] → include 15. Recurse both.
    rangeSum(null left) → 0.
    rangeSum(18):
      18 > 15 → skip right. Recurse left only.
      Left is null → return 0.
    Return 15.
  Return 10 + 7 + 15 = 32.
```

**Sum: 32.** ✓

Notice: we NEVER visited node 3 (the left subtree of 5 was pruned). Significant savings on narrow range queries.

---

## 7. Common pitfalls

1. **Always recursing into BOTH subtrees.** That's O(n); misses the pruning opportunity.

2. **Pruning incorrectly.** Pay close attention: if `node.val < low`, prune the LEFT (not right). Easy to flip.

3. **Forgetting the "low <= node.val <= high" inclusion check.** Both endpoints inclusive per problem spec.

4. **Treating duplicates wrong.** BST convention varies for duplicates; the algorithm handles equality cases at boundaries correctly with `<=` comparisons.

5. **Stack overflow on deeply skewed trees.** Use iterative version with a stack if recursion depth is a concern.

6. **Trying this on a non-BST tree.** Algorithm fails — BST property is what makes pruning valid.

---

## 8. The shape — BST range queries

The pattern:

> **"BST ordering lets you PRUNE entire subtrees that can't contain values in your range. O(log n + k) typical instead of O(n)."**

| Query type | Pruning rule |
|---|---|
| **This problem** (range sum) | `node.val < low` → only right; `> high` → only left |
| Range Count | same pruning, return 1 |
| Range Min / Max | same pruning |
| Insert/Delete in BST | walk down; left vs right based on comparison |
| Search in BST | walk down; left vs right; O(h) |
| Validate BST | maintain low/high bounds as you recurse |

**Pattern to internalize:**

> "BSTs let you efficiently answer 'is this value here?' and 'sum/count/list values in this range' in O(h) or O(h + k) — much better than scanning the whole tree."

---

## Cross-references

- **Reference card (post-mastery):** [`../Range_Sum_of_BST.md`](../Range_Sum_of_BST.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Lowest_Common_Ancestor_of_BST.md`](./Lowest_Common_Ancestor_of_BST.md), [`Kth_Smallest_Element_in_BST.md`](./Kth_Smallest_Element_in_BST.md).
