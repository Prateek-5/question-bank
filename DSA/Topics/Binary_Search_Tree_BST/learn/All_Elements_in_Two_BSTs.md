# All Elements in Two BSTs — Teaching Walkthrough

> **Reference card (post-mastery):** [`../All_Elements_in_Two_BSTs.md`](../All_Elements_in_Two_BSTs.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/all-elements-in-two-binary-search-trees/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: inorder gives sorted output for free from a BST — then it's a standard merge of two sorted lists.** O(N) instead of O(N log N) sort. **Read [`Merge_Two_Sorted_Lists.md`](../../Linked_List/learn/Merge_Two_Sorted_Lists.md) and [`Kth_Smallest_Element_in_BST.md`](./Kth_Smallest_Element_in_BST.md) first.**

**Map of this file (7 short sections):**

1. Read the problem
2. The naive O(N log N) approach
3. Exploit BST inorder → sorted
4. Merge two sorted lists
5. Code
6. Trace it
7. The shape — sort-free BST combination

---

## 1. Read the problem

Given two BSTs `root1` and `root2`, return ALL values from BOTH trees, combined and **sorted in ascending order**. Duplicates preserved.

**Example:**

Tree 1: `{2, 1, 4}`. Tree 2: `{1, 0, 3}`.

Output: `[0, 1, 1, 2, 3, 4]`.

---

## 2. The naive O(N log N) approach

Collect all values from both trees into one array; sort.

```
all = []
collect(root1, all)
collect(root2, all)
all.sort()
return all
```

O(N) traversal + O(N log N) sort = O(N log N).

We can do **O(N)** by exploiting the BST structure.

---

## 3. Exploit BST inorder → sorted

> **Mini-refresher: BST inorder is sorted.**
>
> Inorder traversal of a BST visits values in ascending order (because LEFT subtree < ROOT < RIGHT subtree, recursively).

So:
1. **Inorder traverse Tree 1** → sorted list `L1`.
2. **Inorder traverse Tree 2** → sorted list `L2`.
3. **MERGE the two sorted lists** → sorted combined.

No sort needed; merging two sorted lists is O(|L1| + |L2|).

---

## 4. Merge two sorted lists

Standard two-pointer merge:

```
i = j = 0
merged = []
while i < len(L1) and j < len(L2):
    if L1[i] <= L2[j]:
        merged.append(L1[i]); i += 1
    else:
        merged.append(L2[j]); j += 1
merged += L1[i:]
merged += L2[j:]
return merged
```

O(|L1| + |L2|). Same as the merge step in merge-sort.

---

## 5. Code

**C++:**

```cpp
class Solution {
    void inorder(TreeNode* node, vector<int>& out) {
        if (!node) return;
        inorder(node->left, out);
        out.push_back(node->val);
        inorder(node->right, out);
    }

public:
    vector<int> getAllElements(TreeNode* root1, TreeNode* root2) {
        vector<int> L1, L2;
        inorder(root1, L1);
        inorder(root2, L2);

        vector<int> result;
        result.reserve(L1.size() + L2.size());
        int i = 0, j = 0;
        while (i < (int)L1.size() && j < (int)L2.size()) {
            if (L1[i] <= L2[j]) result.push_back(L1[i++]);
            else result.push_back(L2[j++]);
        }
        while (i < (int)L1.size()) result.push_back(L1[i++]);
        while (j < (int)L2.size()) result.push_back(L2[j++]);
        return result;
    }
};
```

**Python:**

```python
def getAllElements(root1, root2):
    def inorder(node, out):
        if not node: return
        inorder(node.left, out)
        out.append(node.val)
        inorder(node.right, out)
    
    L1, L2 = [], []
    inorder(root1, L1)
    inorder(root2, L2)
    
    result = []
    i = j = 0
    while i < len(L1) and j < len(L2):
        if L1[i] <= L2[j]:
            result.append(L1[i]); i += 1
        else:
            result.append(L2[j]); j += 1
    result.extend(L1[i:])
    result.extend(L2[j:])
    return result
```

Complexity: **O(N) time** (N = total nodes). **O(N) space.**

---

## 6. Trace it

Tree 1 inorder: `[1, 2, 4]`. Tree 2 inorder: `[0, 1, 3]`.

Merge:
```
i=0, j=0: L1[0]=1, L2[0]=0. 0 smaller → 0. j=1.
i=0, j=1: 1 vs 1. 1 <= 1 → 1 from L1. i=1.
i=1, j=1: 2 vs 1. 1 smaller → 1. j=2.
i=1, j=2: 2 vs 3. 2 smaller → 2. i=2.
i=2, j=2: 4 vs 3. 3 smaller → 3. j=3.
L2 exhausted. Append L1[i:] = [4]. result = [0, 1, 1, 2, 3, 4].
```

Output: `[0, 1, 1, 2, 3, 4]`. ✓

---

## 7. The shape — sort-free BST combination

The pattern:

> **"BST inorder gives sorted FOR FREE. For 'combine two BSTs' problems, EXTRACT (inorder) + MERGE (two-pointer) beats EXTRACT + SORT."**

| Problem | Pattern |
|---|---|
| **This problem** | inorder + merge |
| Merge Two BSTs (rebuild as BST) | inorder + merge + balanced build |
| Intersection of two BSTs | inorder + merge with "equal only" |
| Difference of two BSTs | inorder + merge with "from one only" |
| K-th smallest in two BSTs | inorder iterators + walk to k-th |

**Pattern to internalize:**

> "Whenever you process MULTIPLE BSTs together, the BST property (inorder = sorted) reduces the problem to standard sorted-list operations. Avoid full sorts."

---

## Cross-references

- **Reference card (post-mastery):** [`../All_Elements_in_Two_BSTs.md`](../All_Elements_in_Two_BSTs.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Kth_Smallest_Element_in_BST.md`](./Kth_Smallest_Element_in_BST.md), [`Convert_Sorted_Array_to_BST.md`](./Convert_Sorted_Array_to_BST.md).
  - Coming next: [`Merge_Two_BSTs.md`](./Merge_Two_BSTs.md) — same idea, rebuild as BST.
