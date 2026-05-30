# Balanced Binary Tree — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Balanced_Binary_Tree.md`](../Balanced_Binary_Tree.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/balanced-binary-tree/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/balanced-binary-tree/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: when ONE traversal needs to compute TWO pieces of information (height AND balance), MERGE them into a single post-order pass using a SENTINEL value (-1) to signal "broken."** Naive separate computations are O(n²); merged is O(n). This "encode failure as sentinel" pattern is a classic. **Read [`Maximum_Depth_of_Binary_Tree.md`](./Maximum_Depth_of_Binary_Tree.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. The naive O(n²) approach
3. Why naive is slow
4. The single-pass merge
5. The sentinel trick
6. Code
7. Trace it
8. Common pitfalls
9. The shape — merged-computation pattern

---

## 1. Read the problem

Given a binary tree, return `true` if it's **HEIGHT-BALANCED**, else `false`.

A tree is **height-balanced** if for EVERY node, the heights of its LEFT and RIGHT subtrees differ by AT MOST 1.

> **Mini-refresher: "every node" matters.**
>
> The condition must hold at EVERY node — not just the root. A tree could have balanced top but an unbalanced subtree deep inside, which still makes the whole tree unbalanced.

**Examples:**

- Balanced:
  ```
        3
       / \
      9   20
          / \
         15  7
  ```

- Unbalanced:
  ```
        1
       /
      2
     /
    3
  ```
  At node 1: left height 2, right height 0. Difference 2 > 1. UNBALANCED.

---

## 2. The naive O(n²) approach

Direct from the definition: at every node, compute heights of both subtrees and check the difference.

```
def height(node):
    if not node: return 0
    return 1 + max(height(node.left), height(node.right))

def isBalanced(node):
    if not node: return True
    if abs(height(node.left) - height(node.right)) > 1:
        return False
    return isBalanced(node.left) and isBalanced(node.right)
```

Works. But what's the complexity?

---

## 3. Why naive is slow

For each node, we call `height()` on its subtrees. `height()` itself takes O(subtree size). And we do this for every node.

For a SKEWED tree (n nodes in a chain): at the root we compute height for n-1 nodes (right subtree, say); at the next we compute height for n-2; etc. Total: O(n²).

For BALANCED trees, it's O(n log n) (each level does O(n) work over n/2 nodes, log n levels).

**O(n²) is too slow** for n = 10⁴+. We need O(n).

---

## 4. The single-pass merge

> **Mini-refresher: do TWO things in ONE pass.**
>
> The wasteful work: we compute heights MULTIPLE TIMES for the same nodes.
>
> Insight: at EVERY node, we already need to know the LEFT and RIGHT subtree heights (for the balance check). And computing balance lets us short-circuit early on broken subtrees.
>
> **Merge:** make one function that returns BOTH the height AND whether the subtree is balanced. Combine height computation with balance check in a SINGLE post-order pass.

How to return two pieces of info? Two options:
- Return a struct/tuple `(height, is_balanced)`.
- Use a SENTINEL value: return `-1` to mean "unbalanced," otherwise return the height.

The sentinel approach is more concise.

---

## 5. The sentinel trick

> **Mini-refresher: -1 as a "broken" flag.**
>
> Heights are non-negative integers (0, 1, 2, ...). `-1` is impossible as a valid height. So we can REPURPOSE -1 to mean "this subtree is unbalanced; propagate failure up."
>
> Function semantics:
> - Returns the height (≥ 0) if the subtree is balanced.
> - Returns -1 if the subtree is unbalanced (anywhere within it).

```
check(node):
    if node is null: return 0
    lh = check(node.left)
    if lh == -1: return -1               # already broken below; short-circuit
    rh = check(node.right)
    if rh == -1: return -1
    if abs(lh - rh) > 1: return -1       # current node is unbalanced
    return 1 + max(lh, rh)
```

At root: `check(root) != -1` iff the tree is balanced.

**Two passes merged into one:** height + balance check, with short-circuit on failure. **O(n) time.**

---

## 6. Code

**C++:**

```cpp
class Solution {
    int check(TreeNode* n) {
        if (!n) return 0;
        int l = check(n->left);
        if (l == -1) return -1;
        int r = check(n->right);
        if (r == -1) return -1;
        if (abs(l - r) > 1) return -1;
        return 1 + max(l, r);
    }
public:
    bool isBalanced(TreeNode* root) {
        return check(root) != -1;
    }
};
```

**Python:**

```python
def isBalanced(root):
    def check(node):
        if not node: return 0
        l = check(node.left)
        if l == -1: return -1
        r = check(node.right)
        if r == -1: return -1
        if abs(l - r) > 1: return -1
        return 1 + max(l, r)
    return check(root) != -1
```

**JavaScript:**

```javascript
function isBalanced(root) {
    function check(node) {
        if (!node) return 0;
        const l = check(node.left);
        if (l === -1) return -1;
        const r = check(node.right);
        if (r === -1) return -1;
        if (Math.abs(l - r) > 1) return -1;
        return 1 + Math.max(l, r);
    }
    return check(root) !== -1;
}
```

Complexity: **O(n) time, O(h) space.**

---

## 7. Trace it

**Balanced example:**

```
    3
   / \
  9   20
      / \
     15  7
```

```
check(3):
  check(9):
    check(null left) = 0.
    check(null right) = 0.
    |0 - 0| ≤ 1. return 1.
  check(20):
    check(15):
      null, null → return 1.
    check(7):
      null, null → return 1.
    |1 - 1| ≤ 1. return 2.
  |1 - 2| ≤ 1. return 3.

Final: 3 (not -1). Return TRUE.  ✓
```

**Unbalanced example:**

```
  1
 /
2
 \
  3
```

```
check(1):
  check(2):
    check(null left) = 0.
    check(3):
      null, null → return 1.
    |0 - 1| ≤ 1. return 2.
  check(null right) = 0.
  |2 - 0| > 1. return -1.

Final: -1. Return FALSE.  ✓
```

The -1 propagates immediately; no further computation needed once detected.

---

## 8. Common pitfalls

1. **Computing heights separately for each node.** O(n²); use the merged approach.

2. **Forgetting to propagate -1 from one child.** If `lh == -1`, the WHOLE subtree is unbalanced — return -1 immediately without computing rh.

3. **Using -1 as a valid height value.** Heights are ≥ 0 in standard convention. -1 is the sentinel.

4. **Confusing the check: should compare HEIGHTS, not COUNTS.** Height = longest root-to-leaf in nodes; count = total nodes. Different.

5. **Forgetting the empty-tree case.** `check(null) = 0`. Balanced.

6. **Returning `True` instead of `1 + max(lh, rh)`.** The function returns HEIGHTS (or sentinel), not booleans. Wrap in `isBalanced` for the public API.

7. **Treating "balanced" as "perfect binary tree."** They're different! Balanced just means depths differ by ≤ 1; a perfect tree has ALL leaves at the same depth.

---

## 9. The shape — merged-computation pattern

The pattern this problem teaches:

> **"When you need to compute MULTIPLE properties of a tree, MERGE them into ONE traversal pass. Use a sentinel or tuple to carry multiple results."**

Where this applies:

| Problem | Two things computed in one pass |
|---|---|
| **This problem** | height + balance |
| Diameter of Binary Tree | height + diameter (via reference) |
| Validate BST | min + max + valid flag |
| Maximum Path Sum | path-through-here + max-anywhere |
| Sum of Distances in Tree | subtree sums + answer |
| Distribute Coins | excess + moves |
| Count Univalue Subtrees | univalue flag + count |
| Longest Univalue Path | longest-from-here + global max |

**Pattern to internalize:**

> "If your tree problem has TWO related properties (one is the COMPUTATION, one is the CHECK), merge them: ONE traversal pass that computes both, with a sentinel for early termination."

This is one of the most powerful tree-algorithm patterns. O(n²) → O(n) speedup.

---

> **Self-check — the question to ask next time.**
>
> When you face a tree problem requiring BOTH a computation AND a property check, ask:
>
> > **"Can I MERGE them into one post-order traversal? Use a sentinel value to signal 'broken' for early termination."**
>
> If yes, O(n) instead of O(n²).

---

## Cross-references

- **Reference card (post-mastery):** [`../Balanced_Binary_Tree.md`](../Balanced_Binary_Tree.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Maximum_Depth_of_Binary_Tree.md`](./Maximum_Depth_of_Binary_Tree.md).
  - Coming next: [`Invert_Binary_Tree.md`](./Invert_Binary_Tree.md), Path_Sum family.
