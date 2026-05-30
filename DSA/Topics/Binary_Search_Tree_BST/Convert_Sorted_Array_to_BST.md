# Convert Sorted Array to BST

**Problem Link:**
<a href="https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/</a>

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: What Does the Problem Want?

You're given a sorted array (ascending). Build a **height-balanced Binary Search Tree** from it. "Height-balanced" means every node's left and right subtrees differ in height by at most 1.

Example: `nums = [-10, -3, 0, 5, 9]`. One valid answer:

```
       0
      / \
    -3   9
    /   /
  -10  5
```

Every node's left-right subtree height diff is ≤ 1. And it's a valid BST (in-order traversal gives `-10, -3, 0, 5, 9` — the original sorted order).

Important: the problem says "any balanced BST", so multiple answers can be correct. We just need to produce one.

----------------------------------------

## Step 2: What Makes a BST Balanced?

Balance depends on **which value we pick as the root**. If we pick the smallest value, every other value goes to the right — skewed tree, not balanced. If we pick the largest, every other value goes to the left — also skewed.

To balance, we want roughly equal numbers of nodes on both sides. For an n-element sorted array, the root should split it into left (≈ n/2 nodes) and right (≈ n/2 nodes) subtrees. That's a recursive insight: **picking the middle as root** gives us balance.

Let me verify. For `[-10, -3, 0, 5, 9]`, middle is index 2 (value 0). Left subtree holds `[-10, -3]`, right holds `[5, 9]`. Each side has 2 elements. When we recurse on each side, we again pick their middle as root. Left becomes a 2-node subtree, right becomes a 2-node subtree — both with heights 2. Great, balanced.

----------------------------------------

## Step 3: The Recursive Algorithm Drops Out

```
build(nums, lo, hi):
    if lo > hi: return null
    mid = (lo + hi) / 2
    root = new TreeNode(nums[mid])
    root.left  = build(nums, lo, mid - 1)
    root.right = build(nums, mid + 1, hi)
    return root
```

The recursion essentially performs a binary-search-style divide on the array, making each chosen middle a node of the tree. When the range is empty (`lo > hi`), we return null — no node for this "subtree."

Does this give a balanced tree? Yes, because at every recursion level, the left and right halves differ in size by at most 1. Since we recurse on each half identically, their heights differ by at most 1 too. Induction handles the rest.

----------------------------------------

## Step 4: Trace on `[-10, -3, 0, 5, 9]`

```
build([-10, -3, 0, 5, 9], 0, 4):
  mid = 2, root = 0
  left = build(0, 1):
    mid = 0, root = -10
    left = build(0, -1): null
    right = build(1, 1):
      mid = 1, root = -3
      left = build(1, 0): null
      right = build(2, 1): null
      return TreeNode(-3)
    return TreeNode(-10, null, -3)
  right = build(3, 4):
    mid = 3, root = 5
    left = build(3, 2): null
    right = build(4, 4):
      mid = 4, root = 9
      null, null
      return TreeNode(9)
    return TreeNode(5, null, 9)
  return TreeNode(0, ..., ...)
```

Tree:
```
       0
      / \
    -10   5
      \    \
      -3    9
```

Hmm, that differs from my earlier diagram. Let me re-check. For range `[0, 1]`, mid is 0, root is -10. Right subtree of -10 is -3. So -10 has a right child -3. The tree actually looks like:

```
         0
        / \
     -10   5
        \   \
        -3   9
```

Heights:
- Node -3: height 1.
- Node -10: height 1 + max(0, 1) = 2.
- Node 9: height 1.
- Node 5: height 1 + max(0, 1) = 2.
- Root 0: height 1 + max(2, 2) = 3.

Left-right diff at every node: ≤ 1. Balanced. ✓

My earlier example tree used `(lo + hi + 1) / 2` which picks the *upper* middle when even, giving a slightly different shape. Both are valid answers.

----------------------------------------

## Step 5: Why It's a Valid BST

We need to verify: for each node, all values in its left subtree are less, and all values in its right subtree are greater.

Because the input is sorted, the subarray `nums[lo..mid-1]` contains values all < `nums[mid]` (they came earlier in the sorted order). Similarly, `nums[mid+1..hi]` contains values all > `nums[mid]`. So the recursively-built left subtree has only smaller values, and the right only larger. By induction, the BST property holds at every node.

----------------------------------------

## Step 6: Complexity

Time: every array element becomes exactly one tree node. Work per node is O(1) (allocation, recursive calls). **O(n)**.

Space: the call stack depth equals the tree's height. Since we always split evenly, height is O(log n). **O(log n)** for the stack, **O(n)** for the tree itself (which is the output).

----------------------------------------

## Step 7: C++ Implementation

```cpp
TreeNode* build(vector<int>& nums, int lo, int hi) {
    if (lo > hi) return nullptr;
    int mid = (lo + hi) / 2;
    auto* node = new TreeNode(nums[mid]);
    node->left  = build(nums, lo, mid - 1);
    node->right = build(nums, mid + 1, hi);
    return node;
}

TreeNode* sortedArrayToBST(vector<int>& nums) {
    return build(nums, 0, nums.size() - 1);
}
```

That's it. The whole solution is the recursive build.

Two small thoughts:
- Using `(lo + hi) / 2` picks the *lower* middle when the range has even length. Using `(lo + hi + 1) / 2` picks the upper middle. Both yield valid balanced BSTs.
- For `long long` overflow safety: `lo + (hi - lo) / 2`. Matters for huge n.

----------------------------------------

## Step 8: Follow-up Questions

- **Convert a sorted *linked list* to a balanced BST.** Can't random-access the middle cheaply — two options: (1) copy to an array then use this algorithm (O(n) time, O(n) extra space), or (2) a clever in-order build that walks the list once in tandem with the recursion (O(n) time, O(log n) stack).
- **Keep the BST balanced during random inserts.** Switch to an AVL or red-black tree.
- **Does every input yield a unique answer?** No — even vs odd middle choice produces different (but equally valid) balanced BSTs.
- **What if the input has duplicates?** Depends on how you define BST invariants. If duplicates go left (or right), adapt the middle-split rule accordingly.
- **Build from a sorted array without recursion.** You can build it iteratively using a stack simulating the recursion, but the recursive version is simpler and well within stack limits for n ≤ 10^4.
