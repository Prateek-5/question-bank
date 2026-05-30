# Convert Sorted Array to BST — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Convert_Sorted_Array_to_BST.md`](../Convert_Sorted_Array_to_BST.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: pick the MIDDLE of a sorted array as the root; recurse on halves. The middle-as-root choice produces a HEIGHT-BALANCED BST automatically.** Same template builds balanced BSTs from sorted linked lists, balanced segment trees, and more. **Read [`Construct_Binary_Tree_from_Inorder_and_Postorder.md`](../../Trees_Binary_Trees/learn/Construct_Binary_Tree_from_Inorder_and_Postorder.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. What makes a BST balanced?
3. The middle-as-root insight
4. The recursive build
5. Code
6. Trace it
7. Common pitfalls
8. The shape — divide-and-conquer construction

---

## 1. Read the problem

Given an integer array `nums` **sorted in ASCENDING order**, convert it to a **HEIGHT-BALANCED** Binary Search Tree.

A height-balanced binary tree: depths of left and right subtrees of every node differ by at most 1.

**Example:** `nums = [-10, -3, 0, 5, 9]`. One valid answer:

```
       0
      / \
    -3   9
    /   /
  -10  5
```

Multiple correct answers exist — the problem accepts any valid balanced BST.

---

## 2. What makes a BST balanced?

> **Mini-refresher: balanced = left/right subtree heights differ by ≤ 1 at every node.**
>
> If we picked the SMALLEST value as root, every other value goes right → SKEWED, not balanced.
> If we picked the LARGEST, every other goes left → also skewed.
>
> **BALANCE comes from picking the MIDDLE.** Each side gets ~n/2 nodes → height differences naturally stay small.

For n elements, the middle as root splits into:
- Left subtree: ~n/2 elements.
- Right subtree: ~n/2 elements.

Recurse on each. The recursive structure produces a tree of height O(log n).

---

## 3. The middle-as-root insight

The sorted array has a natural BST structure: values in `nums[0..mid-1]` are LESS than `nums[mid]`, and `nums[mid+1..n-1]` are GREATER.

So:
- **Root = `nums[mid]`** (the middle value).
- **Left subtree** = BST built from `nums[0..mid-1]`.
- **Right subtree** = BST built from `nums[mid+1..n-1]`.

This is a CLEAN divide-and-conquer. Recursive structure mirrors binary search.

> **Mini-refresher: BST property automatically preserved.**
>
> Since the input is sorted:
> - All values in `nums[0..mid-1]` < `nums[mid]` → left subtree values are all less. ✓
> - All values in `nums[mid+1..n-1]` > `nums[mid]` → right subtree values are all greater. ✓
>
> The BST property holds trivially.

---

## 4. The recursive build

```
def build(nums, lo, hi):
    if lo > hi: return None
    mid = (lo + hi) // 2
    root = TreeNode(nums[mid])
    root.left = build(nums, lo, mid - 1)
    root.right = build(nums, mid + 1, hi)
    return root

return build(nums, 0, len(nums) - 1)
```

Each subarray `nums[lo..hi]` becomes a subtree rooted at `nums[mid]`. Empty subarray → null.

---

## 5. Code

**C++:**

```cpp
TreeNode* build(vector<int>& nums, int lo, int hi) {
    if (lo > hi) return nullptr;
    int mid = lo + (hi - lo) / 2;
    auto* node = new TreeNode(nums[mid]);
    node->left = build(nums, lo, mid - 1);
    node->right = build(nums, mid + 1, hi);
    return node;
}

TreeNode* sortedArrayToBST(vector<int>& nums) {
    return build(nums, 0, nums.size() - 1);
}
```

**Python:**

```python
def sortedArrayToBST(nums):
    def build(lo, hi):
        if lo > hi: return None
        mid = (lo + hi) // 2
        node = TreeNode(nums[mid])
        node.left = build(lo, mid - 1)
        node.right = build(mid + 1, hi)
        return node
    return build(0, len(nums) - 1)
```

Complexity: **O(n) time** (each element becomes one node), **O(log n) space** (recursion).

---

## 6. Trace it

**`nums = [-10, -3, 0, 5, 9]`** (5 elements, indices 0..4):

```
build(0, 4): mid = 2, root = nums[2] = 0.
  build(0, 1): mid = 0, root = -10.
    build(0, -1) → null.
    build(1, 1): mid = 1, root = -3.
      build(1, 0) → null.
      build(2, 1) → null.
      Return Node(-3).
    Return Node(-10) with right=-3.
  build(3, 4): mid = 3, root = 5.
    build(3, 2) → null.
    build(4, 4): mid = 4, root = 9.
      build(4, 3), build(5, 4) → both null.
      Return Node(9).
    Return Node(5) with right=9.
  Return Node(0) with left=Node(-10), right=Node(5).
```

Tree:
```
       0
      / \
    -10   5
       \   \
       -3   9
```

Heights:
- -3: 1. -10: 2 (right child).
- 9: 1. 5: 2 (right child).
- 0: 1 + max(2, 2) = 3.

Differences: ≤ 1 at every node. **Balanced.** ✓

---

## 7. Common pitfalls

1. **Picking the first or last element as root.** Produces a skewed tree. Always pick the middle.

2. **Using `(lo + hi) / 2` and overflowing.** For huge n, prefer `lo + (hi - lo) / 2`.

3. **Off-by-one in mid calculation.** Floor division gives the LOWER middle for even-length ranges. The UPPER middle (`(lo + hi + 1) // 2`) also works — produces a different but valid balanced BST.

4. **Forgetting the base case `lo > hi`.** Without it, infinite recursion.

5. **Returning the wrong node.** Each recursive call returns its subtree's root; parent assigns it as left/right child.

6. **Trying to do this from an UNSORTED array.** Would not produce a BST. Sort first if needed.

7. **Producing a perfectly-balanced tree (all leaves at same depth).** Not required. Height-balanced is enough.

---

## 8. The shape — divide-and-conquer construction

The pattern:

> **"Construct a balanced data structure by splitting the input in HALF and recursing. The 'middle' becomes the local root."**

| Problem | Input | Local root choice |
|---|---|---|
| **This problem** | sorted array | middle element |
| Convert Sorted Linked List to BST | sorted linked list | middle node (slow/fast) |
| Build a Segment Tree | array | midpoint of range |
| Skip List construction | sorted data | random promotion |
| Merge Sort | array | midpoint of indices |
| Quickselect | array (unsorted) | pivot |

**Pattern to internalize:**

> "For BALANCED construction, RECURSE ON HALVES. The middle of each subarray becomes that subtree's root. O(n) time, O(log n) recursion."

---

> **Self-check — the question to ask next time.**
>
> When asked to build a balanced tree from sorted data, ask:
>
> > **"Can I pick the middle as root and recurse on the two halves?"**
>
> If yes, balanced BST in O(n).

---

## Cross-references

- **Reference card (post-mastery):** [`../Convert_Sorted_Array_to_BST.md`](../Convert_Sorted_Array_to_BST.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Range_Sum_of_BST.md`](./Range_Sum_of_BST.md), [`Lowest_Common_Ancestor_of_BST.md`](./Lowest_Common_Ancestor_of_BST.md).
  - Coming next: [`Binary_Tree_Right_Side_View.md`](./Binary_Tree_Right_Side_View.md), [`Binary_Tree_Left_Side_View.md`](./Binary_Tree_Left_Side_View.md).
