# Path Sum II

**Problem Link:**
<a href="https://leetcode.com/problems/path-sum-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/path-sum-ii/</a>

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: What's Changed From Path Sum I?

Path Sum I asked a yes/no: does **any** root-to-leaf path sum to the target?

Path Sum II asks: **return every root-to-leaf path** whose sum equals the target.

So we need to *construct* paths, not just check for existence. Every matching path becomes a list of node values.

Example:
```
         5
        / \
       4   8
      /   / \
     11  13  4
    /  \    / \
   7    2  5   1
```
targetSum = 22.

Root-to-leaf paths and their sums:
- 5, 4, 11, 7 → 27.
- 5, 4, 11, 2 → 22. ✓
- 5, 8, 13 → 26.
- 5, 8, 4, 5 → 22. ✓
- 5, 8, 4, 1 → 18.

Return `[[5, 4, 11, 2], [5, 8, 4, 5]]`.

----------------------------------------

## Step 2: How Would You Track Paths By Hand?

Walking the tree top-down, you'd carry along a **current partial path** — the sequence of node values from the root to wherever you currently are. When you hit a leaf, check if the running sum matches the target; if yes, snapshot the path into your result list.

When you descend into a child, you extend the partial path. When you return (backtrack) from that child, you'd remove the last node — because now you're ascending back to the parent and about to try a different branch.

This "extend going down, revert going up" pattern is **backtracking**.

----------------------------------------

## Step 3: The Algorithm Sketch

```
dfs(node, remaining, path):
    if node is null: return
    path.append(node.val)          # extend
    
    if node is a leaf and remaining == node.val:
        result.append(path.copy())  # matched — record
    
    dfs(node.left,  remaining - node.val, path)
    dfs(node.right, remaining - node.val, path)
    
    path.pop()                     # revert
```

The crucial bits:
- `path.append` before recursing into children.
- `path.pop()` after both recursions — this is the backtracking.
- `result.append(path.copy())` at matching leaves — **copy** is essential; if we appended the path itself, future modifications would corrupt the recorded result.

At a leaf, "remaining == node.val" means subtracting this node's value would bring remaining to 0 — a match.

----------------------------------------

## Step 4: Trace on the Example

targetSum = 22. result = []. path = [].

```
dfs(5, 22):
  path = [5].
  Not leaf (has children).
  dfs(4, 17):
    path = [5, 4].
    dfs(11, 13):
      path = [5, 4, 11].
      dfs(7, 2):
        path = [5, 4, 11, 7]. Leaf. remaining=2 ≠ 7. Not recorded.
        No children to recurse into.
        path.pop → [5, 4, 11].
      dfs(2, 2):
        path = [5, 4, 11, 2]. Leaf. remaining=2 == 2. RECORD [5, 4, 11, 2].
        No children.
        path.pop → [5, 4, 11].
      path.pop → [5, 4].
    path.pop → [5].
  dfs(8, 17):
    path = [5, 8].
    dfs(13, 9):
      path = [5, 8, 13]. Leaf. remaining=9 ≠ 13. Not recorded.
      path.pop → [5, 8].
    dfs(4, 9):
      path = [5, 8, 4].
      dfs(5, 5):
        path = [5, 8, 4, 5]. Leaf. remaining=5 == 5. RECORD [5, 8, 4, 5].
        path.pop → [5, 8, 4].
      dfs(1, 5):
        path = [5, 8, 4, 1]. Leaf. remaining=5 ≠ 1. Not recorded.
        path.pop → [5, 8, 4].
      path.pop → [5, 8].
    path.pop → [5].
  path.pop → [].
```

result = `[[5, 4, 11, 2], [5, 8, 4, 5]]`. ✓

You can see the **path** variable breathing in and out — extending when we descend, contracting when we ascend. Exactly like following branches of a maze and leaving a breadcrumb trail that you pick back up.

----------------------------------------

## Step 5: Why the Pop Matters

Without `path.pop()` at the end, when we return from `dfs(7, 2)` and start `dfs(2, 2)` from the same parent, `path` would still contain `[5, 4, 11, 7]` instead of `[5, 4, 11]`. We'd then extend it to `[5, 4, 11, 7, 2]` — wrong!

The pop resets `path` to the state it was in when the current call started. That's the essence of backtracking: each recursive call returns shared state exactly as it found it.

----------------------------------------

## Step 6: Why Copy at Record Time

When we hit a matching leaf and say `result.append(path)`, we'd be appending a **reference** to `path`. Later when we pop and extend `path` for different branches, the recorded entry would change too — shared mutable state is sneaky.

By copying, we take a snapshot. Future modifications to `path` don't affect already-recorded paths. This is a standard backtracking gotcha.

----------------------------------------

## Step 7: Name It

This is **DFS with backtracking for path enumeration**. Same shape appears in:
- Sum Root to Leaf Numbers (record numbers formed by digit concatenation).
- All Paths From Source to Target (graph variant).
- Word Search (path in a grid).
- Generate Parentheses (building strings).
- Subsets and Permutations.

The skeleton: **extend → record (at goal) → recurse → revert**.

----------------------------------------

## Step 8: Complexity

Time: Each node visited once. Plus the cost of copying a path (length up to h) at every matching leaf. If there are k matching paths, total copying is O(k · h). Worst case k = O(2^h / 2) paths for a full tree, so **O(n·h)** or **O(n²)** worst case.

Space: O(h) for recursion + O(result size). The result can be up to O(n²) in the worst case.

For typical trees, this is well within interview constraints.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class Solution {
    vector<vector<int>> result;
    vector<int> path;

    void dfs(TreeNode* node, int remaining) {
        if (!node) return;
        path.push_back(node->val);

        // Check leaf
        if (!node->left && !node->right && remaining == node->val) {
            result.push_back(path);   // copy by value
        }

        dfs(node->left,  remaining - node->val);
        dfs(node->right, remaining - node->val);

        path.pop_back();
    }

public:
    vector<vector<int>> pathSum(TreeNode* root, int targetSum) {
        dfs(root, targetSum);
        return result;
    }
};
```

Implementation notes:
- `result.push_back(path)` copies by value (C++'s default for pushing into a vector of vectors). That's exactly what we want.
- We don't check "remaining < 0" pruning because the problem allows negative values.
- The leaf check is `!node->left && !node->right`.

----------------------------------------

## Step 10: Follow-up Questions

- **Count matching paths without listing them.** Same DFS, but increment a counter instead of copying.
- **Paths with sum less than or equal to target.** Check `remaining >= node->val` at leaves; less clean, more case-heavy.
- **Paths not ending at leaves (any node-to-descendant path).** This is Path Sum III. Prefix-sum + hashmap trick.
- **Longest path with sum ≤ target.** Return path length instead of path itself.
- **Paths in a graph (not tree).** Handle cycles; need visited tracking.
- **Iterative version (no recursion).** Use an explicit stack with (node, remainingSum, pathSoFar) tuples.
