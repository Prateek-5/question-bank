# Merge Two BSTs — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Merge_Two_BSTs.md`](../Merge_Two_BSTs.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://www.geeksforgeeks.org/merge-two-balanced-binary-search-trees/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/merge-two-balanced-binary-search-trees/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: BST ↔ sorted array is a duality. To merge two BSTs into a balanced BST, FLATTEN both via inorder, MERGE the sorted arrays, then BUILD a balanced BST from the merged array.** Three classic primitives chained. **Read [`All_Elements_in_Two_BSTs.md`](./All_Elements_in_Two_BSTs.md) and [`Convert_Sorted_Array_to_BST.md`](./Convert_Sorted_Array_to_BST.md) first.**

**Map of this file (7 short sections):**

1. Read the problem
2. The three-phase plan
3. Phase 1: inorder extraction
4. Phase 2: merge sorted arrays
5. Phase 3: balanced rebuild
6. Code
7. The shape — BST ↔ sorted array duality

---

## 1. Read the problem

Given two BSTs, merge them into a single **BALANCED** BST containing all elements from both.

**Example:**

Tree 1: `{3, 1, 5}`. Tree 2: `{5, 4, 6}`.

Combined values: `{1, 3, 4, 5, 5, 6}`.

Output: any valid balanced BST containing these values, e.g.:
```
     4
    / \
   3   5
  /   / \
 1   5   6
```

---

## 2. The three-phase plan

> **Mini-refresher: BST ↔ sorted array duality.**
>
> - BST → sorted array: inorder traversal (covered in earlier file).
> - Sorted array → BST: middle-as-root recursion (covered in earlier file).
>
> These are INVERSES of each other.

So merging two BSTs cleanly factors as:

1. **EXTRACT** each BST to a sorted array (inorder).
2. **MERGE** the two sorted arrays (two-pointer merge).
3. **REBUILD** a balanced BST from the merged array (middle-as-root).

Each phase is O(N). Total: O(N).

---

## 3. Phase 1: inorder extraction

```
def inorder(node, out):
    if not node: return
    inorder(node.left, out)
    out.append(node.val)
    inorder(node.right, out)
```

For Tree 1 above: inorder = `[1, 3, 5]`. For Tree 2: `[4, 5, 6]`.

---

## 4. Phase 2: merge sorted arrays

Standard two-pointer merge (from All_Elements_in_Two_BSTs):

```
merged = []
i = j = 0
while i < len(A) and j < len(B):
    if A[i] <= B[j]: merged.append(A[i]); i += 1
    else: merged.append(B[j]); j += 1
merged += A[i:]
merged += B[j:]
```

For our trees: `[1, 3, 5]` ⨁ `[4, 5, 6]` → `[1, 3, 4, 5, 5, 6]`.

---

## 5. Phase 3: balanced rebuild

```
def build(arr, lo, hi):
    if lo > hi: return None
    mid = (lo + hi) // 2
    root = TreeNode(arr[mid])
    root.left = build(arr, lo, mid - 1)
    root.right = build(arr, mid + 1, hi)
    return root
```

For `[1, 3, 4, 5, 5, 6]`: mid=3, root=5. Recurse on `[1, 3, 4]` and `[5, 6]`.

Resulting tree:
```
     5
    / \
   3   5
  / \   \
 1   4   6
```

---

## 6. Code

**C++:**

```cpp
class Solution {
    void inorder(TreeNode* node, vector<int>& out) {
        if (!node) return;
        inorder(node->left, out);
        out.push_back(node->val);
        inorder(node->right, out);
    }

    vector<int> merge(vector<int>& a, vector<int>& b) {
        vector<int> result;
        result.reserve(a.size() + b.size());
        int i = 0, j = 0;
        while (i < (int)a.size() && j < (int)b.size()) {
            if (a[i] <= b[j]) result.push_back(a[i++]);
            else result.push_back(b[j++]);
        }
        while (i < (int)a.size()) result.push_back(a[i++]);
        while (j < (int)b.size()) result.push_back(b[j++]);
        return result;
    }

    TreeNode* build(vector<int>& arr, int lo, int hi) {
        if (lo > hi) return nullptr;
        int mid = lo + (hi - lo) / 2;
        TreeNode* root = new TreeNode(arr[mid]);
        root->left = build(arr, lo, mid - 1);
        root->right = build(arr, mid + 1, hi);
        return root;
    }

public:
    TreeNode* mergeBSTs(TreeNode* root1, TreeNode* root2) {
        vector<int> a, b;
        inorder(root1, a);
        inorder(root2, b);
        vector<int> merged = merge(a, b);
        return build(merged, 0, (int)merged.size() - 1);
    }
};
```

**Python:**

```python
def mergeBSTs(root1, root2):
    def inorder(node, out):
        if not node: return
        inorder(node.left, out)
        out.append(node.val)
        inorder(node.right, out)
    
    a, b = [], []
    inorder(root1, a)
    inorder(root2, b)
    
    merged = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]: merged.append(a[i]); i += 1
        else: merged.append(b[j]); j += 1
    merged.extend(a[i:])
    merged.extend(b[j:])
    
    def build(lo, hi):
        if lo > hi: return None
        mid = (lo + hi) // 2
        node = TreeNode(merged[mid])
        node.left = build(lo, mid - 1)
        node.right = build(mid + 1, hi)
        return node
    
    return build(0, len(merged) - 1)
```

Complexity: **O(N) time, O(N) space.**

---

## 7. The shape — BST ↔ sorted array duality

The pattern:

> **"BST problems can often be 'flattened' to sorted arrays, manipulated, and 'unflattened' back to a balanced BST."**

| Problem | Phases |
|---|---|
| **This problem** (merge BSTs) | extract + merge + rebuild |
| Convert BST to sorted DLL | extract via inorder + rebuild as DLL |
| Recover BST (swap two nodes) | extract + spot mismatches + fix |
| Validate BST | extract + check strict increase |

**Pattern to internalize:**

> "For complex BST operations, the FLATTEN → MANIPULATE → REBUILD pipeline is clear and O(N). Each phase is a known primitive."

---

## Cross-references

- **Reference card (post-mastery):** [`../Merge_Two_BSTs.md`](../Merge_Two_BSTs.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`All_Elements_in_Two_BSTs.md`](./All_Elements_in_Two_BSTs.md), [`Convert_Sorted_Array_to_BST.md`](./Convert_Sorted_Array_to_BST.md).
  - Coming next: [`Construct_Binary_Tree_from_Traversals.md`](./Construct_Binary_Tree_from_Traversals.md), [`Queue_Reconstruction_by_Height.md`](./Queue_Reconstruction_by_Height.md).
