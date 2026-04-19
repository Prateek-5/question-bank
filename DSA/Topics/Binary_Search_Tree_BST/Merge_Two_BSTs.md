# Merge Two BSTs

**Problem Link:**
https://www.geeksforgeeks.org/merge-two-balanced-binary-search-trees/

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: What Does "Merge" Mean?

Given two Binary Search Trees, merge them into a **single balanced BST** containing all elements from both.

Example:
```
Tree 1:     Tree 2:
  3            5
 / \          / \
1   5        4   6
```

Combined values: {1, 3, 4, 5, 5, 6}. We need a balanced BST on these values.

One valid output:
```
    4
   / \
  3   5
 /   / \
1   5   6
```

All values included, BST invariant holds, balanced (height diff ≤ 1 per node).

----------------------------------------

## Step 2: Key Observation — In-Order Traversal of a BST is Sorted

An in-order traversal of a BST visits nodes in sorted order. This is the defining property that makes BSTs useful for ordered operations.

So:
- In-order traversal of Tree 1: `[1, 3, 5]`.
- In-order traversal of Tree 2: `[4, 5, 6]`.

Now we have two sorted arrays. Merging them gives `[1, 3, 4, 5, 5, 6]`. Sorted.

That's the first key step. The second: how do we build a **balanced BST** from a sorted array?

----------------------------------------

## Step 3: Balanced BST from a Sorted Array

Take the **middle** element of the sorted array and make it the root. Recursively build the left subtree from the left half, right subtree from the right half.

This produces a balanced BST because each recursion level splits the array roughly in half, yielding log(n) levels.

```
def buildBST(arr, lo, hi):
    if lo > hi: return null
    mid = (lo + hi) / 2
    root = new Node(arr[mid])
    root.left = buildBST(arr, lo, mid - 1)
    root.right = buildBST(arr, mid + 1, hi)
    return root
```

O(n) time, O(n) space (for the tree + recursion stack).

----------------------------------------

## Step 4: Put It All Together

Three-phase algorithm:
1. In-order traverse Tree 1 → sorted list A.
2. In-order traverse Tree 2 → sorted list B.
3. Merge A and B into a single sorted list M.
4. Build balanced BST from M.

Each step is O(n). Total: O(n1 + n2) time, O(n1 + n2) space.

----------------------------------------

## Step 5: Merging Two Sorted Lists

Two-pointer merge:

```
def merge(A, B):
    merged = []
    i = j = 0
    while i < len(A) and j < len(B):
        if A[i] <= B[j]: merged.append(A[i]); i++
        else: merged.append(B[j]); j++
    merged.extend(A[i:])
    merged.extend(B[j:])
    return merged
```

Classic — identical to the merge step in merge-sort.

----------------------------------------

## Step 6: Trace on the Example

Tree 1 in-order: [1, 3, 5]. Tree 2 in-order: [4, 5, 6].

Merge: [1, 3, 4, 5, 5, 6].

Build BST from [1, 3, 4, 5, 5, 6]:
- Length 6. Mid index = 3. Root value = arr[3] = 5.
- Left sub-array: [1, 3, 4]. Mid index = 1. Root = 3.
  - Left: [1]. Root = 1.
  - Right: [4]. Root = 4.
- Right sub-array: [5, 6]. Mid index = 0. Root = 5.
  - Left: []. Null.
  - Right: [6]. Root = 6.

Tree:
```
     5
    / \
   3   5
  / \   \
 1   4   6
```

Valid BST, balanced. ✓

(My "one valid output" in Step 1 was slightly different — multiple balanced BSTs are valid depending on where we split on even lengths.)

----------------------------------------

## Step 7: Why In-Order Is the Natural Choice

BST ↔ sorted-array is a dual relationship:
- **BST → sorted array:** in-order traversal.
- **Sorted array → BST:** median-split construction.

The cycle is symmetric. Merging two BSTs is cleanest via this cycle: BSTs → sorted arrays → merged sorted array → balanced BST.

Alternative: merge in place during tree traversal (using BST iterators instead of full arrays). Saves memory (O(h) per iterator instead of O(n) for the array). But implementation is more complex.

----------------------------------------

## Step 8: Name It

This is **sorted-array-based BST construction**, applied twice (in-order extraction + balanced rebuild) with a merge in the middle.

Key techniques combined:
- In-order traversal (DFS with left-root-right order).
- Merge step (two-pointer).
- Balanced BST from sorted array (median recursion).

Related:
- Convert Sorted Array to BST (just the build step).
- Convert Sorted List to BST (same, but from a linked list).
- Flatten BST to a sorted list (just the extraction step).

----------------------------------------

## Step 9: Complexity

Time: **O(n1 + n2)** — linear in total size.
Space: **O(n1 + n2)** for the sorted arrays and the new tree.

Can be reduced to O(h1 + h2) memory with in-place iterator merging, but that complicates code.

----------------------------------------

## Step 10: C++ Implementation

```cpp
class Solution {
    void inorder(TreeNode* node, vector<int>& out) {
        if (!node) return;
        inorder(node->left, out);
        out.push_back(node->val);
        inorder(node->right, out);
    }

    vector<int> mergeSorted(vector<int>& a, vector<int>& b) {
        vector<int> merged;
        merged.reserve(a.size() + b.size());
        int i = 0, j = 0;
        while (i < (int)a.size() && j < (int)b.size()) {
            if (a[i] <= b[j]) merged.push_back(a[i++]);
            else merged.push_back(b[j++]);
        }
        while (i < (int)a.size()) merged.push_back(a[i++]);
        while (j < (int)b.size()) merged.push_back(b[j++]);
        return merged;
    }

    TreeNode* buildBalanced(vector<int>& arr, int lo, int hi) {
        if (lo > hi) return nullptr;
        int mid = lo + (hi - lo) / 2;
        TreeNode* root = new TreeNode(arr[mid]);
        root->left = buildBalanced(arr, lo, mid - 1);
        root->right = buildBalanced(arr, mid + 1, hi);
        return root;
    }

public:
    TreeNode* mergeBSTs(TreeNode* root1, TreeNode* root2) {
        vector<int> a, b;
        inorder(root1, a);
        inorder(root2, b);
        vector<int> merged = mergeSorted(a, b);
        return buildBalanced(merged, 0, merged.size() - 1);
    }
};
```

Three distinct helpers, each doing one thing clearly:
- `inorder`: sorted list from a BST.
- `mergeSorted`: standard merge.
- `buildBalanced`: median-recursive build.

----------------------------------------

## Step 11: Follow-up Questions

- **Merge k BSTs.** Extract all, k-way merge, then build.
- **Merge BSTs with duplicates.** Our algorithm handles duplicates already (via `<=` in merge).
- **In-place merge (without extracting to arrays).** Use BST iterators for both trees; take the smaller head at each step; build the result tree simultaneously. Complex but O(h1 + h2) memory.
- **Return the k-th smallest of the merged set without building the full tree.** Walk the two iterators simultaneously k times.
- **Handle trees that aren't BSTs.** If either tree isn't a BST, in-order doesn't give sorted output — need to sort afterward.
- **Persistence (multiple merged versions).** Use persistent BSTs to share structure between versions.
