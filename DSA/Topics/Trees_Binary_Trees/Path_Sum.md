# Path Sum

**Problem Link:**
https://leetcode.com/problems/path-sum/

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: Define "Path" Precisely

Given a binary tree and a target integer `targetSum`, return `true` if there exists a **root-to-leaf path** whose values sum exactly to `targetSum`.

Three things to nail down:
- **Root-to-leaf**: starts at the root, ends at a leaf. Not "any path" in the tree, and not "root to any node."
- **Leaf**: a node with no children (both left and right are null).
- **Sum**: add up every node's value on the path.

Example:
```
         5
        / \
       4   8
      /   / \
     11  13  4
    /  \      \
   7    2      1
```
targetSum = 22.

Possible root-to-leaf sums:
- 5 → 4 → 11 → 7 = 27.
- 5 → 4 → 11 → 2 = 22. ✓
- 5 → 8 → 13 = 26.
- 5 → 8 → 4 → 1 = 18.

One of them hits 22 → return true.

If targetSum were 100, none would match → false.

----------------------------------------

## Step 2: How Would I Solve by Hand?

I'd start at the root, explore down, keeping a running sum. When I reach a leaf, check if the running sum equals the target. If yes, done. If not, backtrack and try a different branch.

This is exactly **recursion**. Each branch corresponds to "go left" or "go right." The base case is "we're at a leaf — does our current running sum match?"

----------------------------------------

## Step 3: Craft the Recurrence

Let `check(node, remaining)` = true if there's a path starting at `node` going down to a leaf with total equal to `remaining` (what's left to match).

- If `node` is null: no path exists from a null node. Return false.
- If `node` is a leaf (both children null): we've reached the end. Return true iff `node.val == remaining`.
- Else: recurse on children with a reduced remaining. Return true if either child can finish the job.

```
check(node, remaining):
    if node is null: return false
    if node is leaf: return node.val == remaining
    return check(node.left,  remaining - node.val)
        or check(node.right, remaining - node.val)
```

Initial call: `check(root, targetSum)`.

Subtle point: the null check returns false, but what does it mean at an internal node with one missing child? If node has a left child but no right, we'd recurse into the right (null) and get false — that's correct, because there's no path via a non-existent child. The left recurse could return true if the left path works.

The **leaf check** is what makes this "root-to-leaf" rather than "root-to-any-node." Without it, we'd accept any prefix summing to the target.

----------------------------------------

## Step 4: Trace on the Example

targetSum = 22.

```
check(5, 22):
  not leaf.
  check(4, 22-5=17) or check(8, 17).
    check(4, 17):
      not leaf.
      check(11, 17-4=13) or check(None, 13)=false.
        check(11, 13):
          not leaf.
          check(7, 13-11=2) or check(2, 2).
            check(7, 2):
              leaf. 7 == 2? No. Return false.
            check(2, 2):
              leaf. 2 == 2? YES. Return true.
          check(11, 13) = true.
        check(4, 17) = true.
      check(5, 22) = true. Return true early.
```

Got it in the second leaf we checked (path 5-4-11-2). ✓

----------------------------------------

## Step 5: Why This Pattern Works

The recursion mirrors the tree structure:
- At each node, we consume `node.val` from the remaining target.
- At leaves, we check if the exact amount remains.
- At internal nodes, we try both children.

Each node is visited at most once (by the recursion). We never visit the same subtree twice for the same remaining value. So total work is O(n).

----------------------------------------

## Step 6: An Alternative — Track Running Sum

Instead of decrementing `targetSum`, we could add as we go and compare at the leaf:

```
check(node, currentSum):
    if node is null: return false
    currentSum += node.val
    if node is leaf: return currentSum == targetSum
    return check(node.left, currentSum) or check(node.right, currentSum)
```

Mathematically identical. Some people prefer the decrementing form (fewer parameters to think about); some prefer the accumulating form (easier to debug, running sum matches intuition).

----------------------------------------

## Step 7: Naming What We Did

This is a standard **DFS with a running accumulator** — a ubiquitous tree pattern. Each recursive call contributes a bit of state (the current node's value) that the subtree uses to make its decision. The same shape solves:
- Path Sum II (return all matching paths).
- Path Sum III (count paths with any starting/ending node matching a sum).
- Sum Root to Leaf Numbers (accumulate via digit concatenation instead of sum).
- Max root-to-leaf path sum (replace equality with max).

----------------------------------------

## Step 8: Edge Cases

- **Empty tree (root is null):** no root-to-leaf path exists. Return false. The base case handles this automatically.
- **Single node tree:** it's both root and leaf. Return `root.val == targetSum`.
- **Negative values / target:** the arithmetic still works — no restriction.

----------------------------------------

## Step 9: Complexity

Time: every node is visited at most once. **O(n)** where n is the node count.
Space: the recursion depth is the tree's height. For balanced trees, O(log n). Worst case (skewed), O(n).

----------------------------------------

## Step 10: C++ Implementation

```cpp
bool hasPathSum(TreeNode* root, int targetSum) {
    if (!root) return false;
    // leaf: no children
    if (!root->left && !root->right) {
        return root->val == targetSum;
    }
    int remaining = targetSum - root->val;
    return hasPathSum(root->left,  remaining)
        || hasPathSum(root->right, remaining);
}
```

Reading the code:
- The null check is the base for recursion into missing children — we just return false, no path possible.
- The leaf check is what makes the semantic "root-to-leaf" correct.
- We use `||` short-circuit evaluation: if the left subtree finds a match, we never recurse into the right.

----------------------------------------

## Step 11: Follow-up Questions

- **Path Sum II.** Return all root-to-leaf paths with the target sum. Use backtracking — build a path as you descend, copy it at leaves.
- **Path Sum III.** Count paths from any node to any descendant that sum to target. Prefix-sum + hashmap DFS: O(n).
- **Maximum root-to-leaf sum.** Replace the equality check with a running max.
- **Paths of length exactly k (node count).** Track depth along with sum.
- **Support weighted edges instead of node values.** Adjust the accumulation accordingly.
- **Trees with more than two children (N-ary).** Same recursion pattern, loop over children instead of two recursive calls.
