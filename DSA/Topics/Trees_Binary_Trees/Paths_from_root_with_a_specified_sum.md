# Paths from Root with a Specified Sum

**Problem Link:**
<a href="https://www.geeksforgeeks.org/problems/paths-from-root-with-a-specified-sum/1" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/problems/paths-from-root-with-a-specified-sum/1</a>

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: Understand What's Being Asked

Given a binary tree and a target integer `k`, find **all root-to-node paths** (not necessarily leaf-ending — the path may end at any node) whose node values sum to exactly `k`.

Return each path as a list of node values, in order from root to the ending node.

Example:
```
        1
       / \
      3   -1
     / \  / \
    2   1 4  5
        |
        1
```

Target k = 5. Root-to-any-node paths summing to 5:
- 1 → 3 → 1 = 5 ✓
- 1 → 3 → 1 → 1 ... that's a different path, let me check carefully.
- 1 → -1 → 5 = 5 ✓

(The tree above has node 1 as a child of the first 1 under 3. If such a node exists: 1 → 3 → 1 → 1 = 6, not 5.)

----------------------------------------

## Step 2: Why DFS (Preorder)

A **root-to-node path** is exactly the stack of ancestors while doing DFS. As we descend from the root, we can accumulate the running sum and maintain the path.

Whenever the running sum equals k, we've found a valid path — emit it.

After processing a node, we backtrack (pop from path, subtract from sum). This is classic DFS with backtracking.

----------------------------------------

## Step 3: Algorithm

```
result = []
path = []

def dfs(node, current_sum):
    if node is null: return
    path.append(node.val)
    current_sum += node.val

    if current_sum == k:
        result.append(path.copy())
        # Don't return yet — a child might also form a valid continuation? No — longer paths have different sums, but we'd capture them separately. Continue descending.

    dfs(node.left, current_sum)
    dfs(node.right, current_sum)

    path.pop()   # backtrack
```

Depth-first traversal. O(n) time for traversal; emitting paths is O(path_length) per emit, which can aggregate to O(n × paths_found).

----------------------------------------

## Step 4: Trace on a Small Tree

```
        1
       / \
      3   -1
     / \   
    2   1  
```

Target k = 4.

```
dfs(root=1, sum=0).
  path = [1], sum = 1. 1 != 4.
  dfs(3, 1).
    path = [1, 3], sum = 4. 4 == 4 → emit [1, 3].
    dfs(2, 4).
      path = [1, 3, 2], sum = 6. 6 != 4.
      (no children)
      Backtrack: path = [1, 3].
    dfs(1, 4).
      path = [1, 3, 1], sum = 5. 5 != 4.
      Backtrack: path = [1, 3].
    Backtrack: path = [1].
  dfs(-1, 1).
    path = [1, -1], sum = 0.
    (no children)
    Backtrack: path = [1].
  Backtrack: path = [].
```

Result: `[[1, 3]]`. ✓

Sanity: root-to-any-node paths summing to 4: only 1 → 3 = 4. Verified.

----------------------------------------

## Step 5: Key Point — Don't Stop at a Match

When we find a path summing to k, we **still continue the DFS** into its children. Why? Because a longer path through a child may also hit k if subsequent values sum to 0 (e.g., path continues with +5 and -5). Do NOT early-return after a match; just emit and keep descending.

Alternatively, if the problem specifies root-to-leaf paths only, we'd add a check `if node is a leaf: ...` and return.

----------------------------------------

## Step 6: Path Storage Detail

We accumulate `path` as a mutable list. Each emit **copies** the current path into the result. If we forgot to copy and just appended `path` itself, later backtracking would mutate the stored reference, corrupting the result.

Always copy (slice, clone) when emitting a mutable structure you'll continue modifying.

----------------------------------------

## Step 7: Name It

**DFS with path accumulation and backtracking**. A universal pattern for tree problems asking "enumerate paths satisfying a property."

Related problems:
- Path Sum II (root-to-leaf paths summing to k).
- Binary Tree Paths (all root-to-leaf paths).
- Sum Root to Leaf Numbers.
- Path Sum III (path may start and end anywhere — use prefix-sum trick).

All share the recursive descent + backtracking structure.

----------------------------------------

## Step 8: Complexity

Time: **O(n)** for traversal, plus O(total output size) for the result list. Worst case (all paths match), output can be O(n²) (quadratic in nodes).
Space: **O(h)** for recursion + path + result, where h = tree height.

----------------------------------------

## Step 9: C++ Implementation

```cpp
struct Node { int data; Node *left, *right; };

class Solution {
    vector<vector<int>> result;
    vector<int> path;

    void dfs(Node* node, int target, int currentSum) {
        if (!node) return;
        path.push_back(node->data);
        currentSum += node->data;

        if (currentSum == target) {
            result.push_back(path);
        }

        dfs(node->left, target, currentSum);
        dfs(node->right, target, currentSum);

        path.pop_back();   // backtrack
    }

public:
    vector<vector<int>> printPaths(Node* root, int k) {
        dfs(root, k, 0);
        return result;
    }
};
```

Key detail: `path.push_back` / `path.pop_back` mirror entry and exit from the node in the recursion.

----------------------------------------

## Step 10: Follow-up Questions

- **Paths in any direction (not just root-to-node).** Path Sum III; use running prefix-sum hashmap to find sub-paths.
- **Exactly K nodes in the path (not sum).** Track depth instead of sum.
- **Only leaf-ending paths.** Add `if !node->left && !node->right` check before emitting.
- **Return just the count.** Increment a counter instead of storing paths.
- **Negative values allowed?** This algorithm handles them naturally — running sum can decrease.
- **Memoization?** Not generally useful here — paths are position-specific; no overlapping subproblems.
