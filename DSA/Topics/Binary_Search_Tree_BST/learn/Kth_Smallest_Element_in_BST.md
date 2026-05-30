# Kth Smallest Element in BST — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Kth_Smallest_Element_in_BST.md`](../Kth_Smallest_Element_in_BST.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/kth-smallest-element-in-a-bst/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/kth-smallest-element-in-a-bst/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: BST inorder traversal yields values in SORTED order. Iterative inorder with a counter stops AT THE K-TH VISIT — no need to traverse the whole tree.** **Read [`Binary_Tree_Inorder_Traversal_Iterative.md`](../../Trees_Binary_Trees/learn/Binary_Tree_Inorder_Traversal_Iterative.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. The BST inorder property
3. The naive full-inorder approach
4. The early-termination optimization
5. Code (iterative)
6. Trace it
7. The augmented BST follow-up
8. The shape — exploit "inorder = sorted"

---

## 1. Read the problem

Given the root of a **BST** and a positive integer `k`, return the **k-th SMALLEST value** in the tree (1-indexed: k=1 = smallest, k=2 = second smallest, ...).

**Example:**
```
     5
    / \
   3   6
  / \
 2   4
/
1
```
Sorted values: 1, 2, 3, 4, 5, 6. For `k = 3`, return **3**.

---

## 2. The BST inorder property

> **Mini-refresher: BST inorder = sorted.**
>
> Inorder traversal: LEFT, ROOT, RIGHT. For BSTs:
> - LEFT subtree's values are all < ROOT.
> - RIGHT subtree's values are all > ROOT.
>
> So inorder visits values in STRICTLY INCREASING order.

For our tree, inorder yields: 1, 2, 3, 4, 5, 6 — already sorted.

**Consequence:** the k-th visited node in inorder IS the k-th smallest. Just count.

---

## 3. The naive full-inorder approach

```
def kthSmallest(root, k):
    vals = []
    def inorder(node):
        if not node: return
        inorder(node.left)
        vals.append(node.val)
        inorder(node.right)
    inorder(root)
    return vals[k - 1]
```

Works. O(n) time (visits all nodes), O(n) space (the list).

But we don't need to visit ALL nodes — only the first k. Stop early.

---

## 4. The early-termination optimization

Use ITERATIVE inorder (with an explicit stack) and a counter. Stop when the counter reaches k.

```
def kthSmallest(root, k):
    stack = []
    cur = root
    while cur or stack:
        # Walk left as far as possible
        while cur:
            stack.append(cur)
            cur = cur.left
        # Visit
        cur = stack.pop()
        k -= 1
        if k == 0:
            return cur.val
        # Go to right subtree
        cur = cur.right
```

The iterative inorder template, augmented with a counter. When k hits 0, we've just visited the k-th smallest.

**Time complexity: O(h + k)** — walk down to leftmost (h steps), then process k nodes.

---

## 5. Code (iterative)

**C++:**

```cpp
int kthSmallest(TreeNode* root, int k) {
    stack<TreeNode*> st;
    TreeNode* cur = root;
    while (cur || !st.empty()) {
        while (cur) {
            st.push(cur);
            cur = cur->left;
        }
        cur = st.top(); st.pop();
        if (--k == 0) return cur->val;
        cur = cur->right;
    }
    return -1;  // unreachable for valid k
}
```

**Python:**

```python
def kthSmallest(root, k):
    stack = []
    cur = root
    while cur or stack:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        k -= 1
        if k == 0:
            return cur.val
        cur = cur.right
```

**JavaScript:**

```javascript
function kthSmallest(root, k) {
    const stack = [];
    let cur = root;
    while (cur || stack.length) {
        while (cur) {
            stack.push(cur);
            cur = cur.left;
        }
        cur = stack.pop();
        if (--k === 0) return cur.val;
        cur = cur.right;
    }
    return -1;
}
```

Complexity: **O(h + k) time, O(h) space.**

---

## 6. Trace it

**Tree** as in Section 1. **k = 3.**

```
cur = 5, stack = [].

OUTER iter 1:
  Inner: push 5, cur=3. push 3, cur=2. push 2, cur=1. push 1, cur=null. (EXIT inner.)
  Pop 1. k = 3-1 = 2.
  cur = 1.right = null.

OUTER iter 2:
  Inner: cur null → skip.
  Pop 2. k = 1.
  cur = 2.right = null.

OUTER iter 3:
  Inner: cur null → skip.
  Pop 3. k = 0 → RETURN 3.   ✓
```

Three pops, exactly k=3. No need to visit 4, 5, or 6.

---

## 7. The augmented BST follow-up

If the BST is modified frequently (inserts/deletes) and we need many kth-smallest queries, we can do better than O(h + k).

> **Mini-refresher: augment with subtree sizes.**
>
> Add a field `size` to each node = total nodes in its subtree.
>
> **Kth-smallest walk:**
> ```
> def kth(node, k):
>     left_size = node.left.size if node.left else 0
>     if k == left_size + 1: return node.val
>     if k <= left_size: return kth(node.left, k)
>     return kth(node.right, k - left_size - 1)
> ```
>
> Each call descends one level. **O(h) per query.** For balanced BSTs, O(log n).
>
> Maintenance: inserts and deletes update `size` along the path — O(h).

This trade-off — extra memory per node for fast queries — is the staple "augment a tree" technique.

---

## 8. The shape — exploit "inorder = sorted"

The pattern:

> **"For BST problems involving ORDER (kth smallest, validate, finding successor), use INORDER traversal — it visits values in sorted order. Early-terminate when you have enough."**

| Problem | Uses inorder for... |
|---|---|
| **This problem** | k-th smallest = k-th visit |
| Validate BST | inorder must be STRICTLY INCREASING |
| Find inorder successor | next inorder visit after a given node |
| Convert BST to sorted DLL | inorder yields the sorted order |
| Recover BST | two swapped nodes break inorder; find and fix |
| All Elements in Two BSTs | merge two inorder sequences |

**Pattern to internalize:**

> "BST property + inorder traversal = SORTED visit order. Many BST problems reduce to manipulations of this sorted sequence."

---

## Cross-references

- **Reference card (post-mastery):** [`../Kth_Smallest_Element_in_BST.md`](../Kth_Smallest_Element_in_BST.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Range_Sum_of_BST.md`](./Range_Sum_of_BST.md), [`Lowest_Common_Ancestor_of_BST.md`](./Lowest_Common_Ancestor_of_BST.md).
  - [`../../Trees_Binary_Trees/learn/Binary_Tree_Inorder_Traversal_Iterative.md`](../../Trees_Binary_Trees/learn/Binary_Tree_Inorder_Traversal_Iterative.md).
  - Coming next: [`Binary_Search_Tree_Iterator.md`](./Binary_Search_Tree_Iterator.md) — same iterative inorder, encapsulated as a class.
