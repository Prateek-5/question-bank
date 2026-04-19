# Path Sum III

**Problem Link:**
https://leetcode.com/problems/path-sum-iii/

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: Understand the New Twist

This is **not** the same as Path Sum I or II.

- **Path Sum I/II**: root-to-leaf paths with sum equal to target.
- **Path Sum III**: **any** path (can start and end at any nodes) where the sum equals target, as long as it goes strictly **top to bottom** (from an ancestor to one of its descendants).

Count the number of such paths.

Example:
```
         10
        /  \
       5   -3
      / \    \
     3   2   11
    / \   \
   3  -2   1
```
targetSum = 8.

Valid paths with sum 8:
- `5 → 3`: 5+3=8. ✓
- `5 → 2 → 1`: 5+2+1=8. ✓
- `-3 → 11`: -3+11=8. ✓

Count = **3**.

Notice these paths don't need to start at the root or end at a leaf. Any ancestor-descendant path works.

----------------------------------------

## Step 2: The Brute Force

For each node in the tree, treat it as a potential **starting node** of a path, and DFS downward counting paths with the given sum. That's O(n²) if we do a full DFS from every node.

```
def countPaths(root, target):
    if root is null: return 0
    return (pathsFrom(root, target)
            + countPaths(root.left, target)
            + countPaths(root.right, target))

def pathsFrom(node, target):
    if node is null: return 0
    count = 0
    if node.val == target: count += 1
    count += pathsFrom(node.left, target - node.val)
    count += pathsFrom(node.right, target - node.val)
    return count
```

Works correctly but re-visits descendants many times. For a balanced tree, O(n log n); worst case (skewed), O(n²).

We can do better with a clever observation.

----------------------------------------

## Step 3: Prefix Sums on a Path

Here's a beautiful reuse of a classic array technique.

Consider the **prefix sums along the root-to-current-node path**. If we're at some node v, the prefix sum is the sum of values from the root down to v.

Now consider any path from ancestor `u` to descendant `v`. Its sum equals:
```
sum(u → v) = prefixSum(v) - prefixSum(parent of u)
```

(Because adding `parent of u`'s prefix to the path `u → v` gives `root → v`, which is `prefixSum(v)`. Subtract the former to isolate the latter.)

We want paths with sum == target:
```
target = prefixSum(v) - prefixSumAtSomeAncestor
prefixSumAtSomeAncestor = prefixSum(v) - target
```

So as we DFS from root, at each node v we count how many ancestor prefix sums equal `prefixSum(v) - target`. That count is the number of target-sum paths ending at v.

This is exactly the **subarray sum equals k** technique, but on a tree path instead of an array!

----------------------------------------

## Step 4: The Algorithm

Walk the tree DFS. Maintain a hashmap `prefixCount` mapping prefix sums (along the current root-to-node path) to their occurrence counts.

```
dfs(node, currentSum):
    if node is null: return 0
    currentSum += node.val
    
    # count paths ending at `node` with sum == target
    count = prefixCount.get(currentSum - target, 0)
    
    # register current prefix sum for descendants to use
    prefixCount[currentSum] += 1
    
    # recurse
    count += dfs(node.left, currentSum)
    count += dfs(node.right, currentSum)
    
    # backtrack: remove current prefix from map before returning
    prefixCount[currentSum] -= 1
    
    return count
```

Initial call: `prefixCount = {0: 1}` (empty prefix has sum 0, needed so paths starting at root are counted), then `dfs(root, 0)`.

The **backtrack step** (decrementing when leaving) is critical. Without it, a prefix from one branch would pollute counts in a sibling branch.

----------------------------------------

## Step 5: Trace on the Example

Tree (again):
```
         10
        /  \
       5   -3
      / \    \
     3   2   11
    / \   \
   3  -2   1
```
target = 8.

I'll track `(node, currentSum)` and the `prefixCount` map. Initial `prefixCount = {0: 1}`.

```
dfs(10, 0):
  currentSum = 10.
  need prefix = 10 - 8 = 2. prefixCount.get(2, 0) = 0. count = 0.
  prefixCount[10] += 1 → {0:1, 10:1}.
  
  dfs(5, 10):
    currentSum = 15.
    need 7. not in map. count = 0.
    prefixCount[15]++ → {0:1, 10:1, 15:1}.
    
    dfs(3, 15):
      currentSum = 18.
      need 10. prefixCount[10] = 1. count = 1.  ← one path
      prefixCount[18]++.
      
      dfs(3, 18):  (left child, value 3)
        currentSum = 21.
        need 13. Not in map. count = 0.
        prefixCount[21]++.
        children null, return 0.
        prefixCount[21]-- (backtrack).
      
      dfs(-2, 18):
        currentSum = 16.
        need 8. Not in map. count = 0.
        (similar backtrack.)
      
      prefixCount[18]-- (backtrack).
      returns 1 (from this node).
    
    dfs(2, 15):
      currentSum = 17.
      need 9. Not in map. count = 0.
      prefixCount[17]++.
      
      dfs(1, 17):
        currentSum = 18.
        need 10. prefixCount[10] = 1. count = 1.  ← another path (5→2→1)
        ... 
      prefixCount[17]-- (backtrack).
    
    prefixCount[15]--.
    returns 1 + 1 = 2 (from left subtree).
  
  dfs(-3, 10):
    currentSum = 7.
    need -1. Not in map. count = 0.
    prefixCount[7]++.
    
    dfs(11, 7):
      currentSum = 18.
      need 10. prefixCount[10] = 1. count = 1.  ← third path (-3→11)
    prefixCount[7]--.
    returns 1.
  
  prefixCount[10]--.
  returns 0 + 2 + 1 = 3.
```

Total paths = **3**. ✓

The prefix-sum trick let us compute the count in a single DFS without the O(n²) nested traversals.

----------------------------------------

## Step 6: Why the Backtrack Is Crucial

When we leave a node (the recursive DFS returns), we decrement `prefixCount[currentSum]`. This removes the current prefix sum from the map so it doesn't affect sibling subtrees.

If we forgot to decrement: when processing the right subtree of a node, prefix sums from the left subtree would still be in the map. We'd count nonexistent "paths" — a path can't start in the left subtree and end in the right, since it must be ancestor-descendant.

The backtrack keeps the map **path-relative** — it only ever reflects prefix sums along the current root-to-node path.

----------------------------------------

## Step 7: Name It

**Prefix sum with hashmap**, applied to a tree path. This is a direct cousin of "Subarray Sum Equals K" — the same key trick, just with recursion-plus-backtracking replacing the linear scan.

This pattern is a favorite for any problem that says "count paths/subarrays with property X" — when X is "sum equals k," prefix sums plus hashmap almost always win.

----------------------------------------

## Step 8: Complexity

Time: each node is visited once. At each node, we do O(1) hashmap operations. **O(n)**.
Space: O(h) for the recursion stack + O(n) for the hashmap (at worst). **O(n)**.

Down from O(n²) brute force. The prefix-sum-plus-hashmap idiom really pays off here.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class Solution {
    unordered_map<long long, int> prefixCount;
    int target;
    int count;

    void dfs(TreeNode* node, long long currentSum) {
        if (!node) return;
        currentSum += node->val;

        // count ancestors with prefix == currentSum - target
        auto it = prefixCount.find(currentSum - target);
        if (it != prefixCount.end()) count += it->second;

        // register current prefix for descendants
        prefixCount[currentSum]++;

        dfs(node->left, currentSum);
        dfs(node->right, currentSum);

        // backtrack
        prefixCount[currentSum]--;
    }

public:
    int pathSum(TreeNode* root, int targetSum) {
        target = targetSum;
        count = 0;
        prefixCount[0] = 1;       // empty prefix for root-starting paths
        dfs(root, 0);
        return count;
    }
};
```

Implementation details:
- Use `long long` for prefix sums to avoid overflow if the tree is deep and values large.
- `prefixCount[0] = 1` is the "sentinel" for paths starting at the root. Omitting it misses those cases.
- The backtrack step is the pair to the "increment" step — strict discipline.

----------------------------------------

## Step 10: Follow-up Questions

- **Any path, not just ancestor-descendant (can also go across via LCA).** Different problem; usually needs a more involved LCA-based DP.
- **Longest path with target sum (not count).** Adjust the hashmap to track earliest occurrence of each prefix; compute length as depth difference.
- **Paths with sum in a range [lo, hi].** Harder; hashmap on prefix sum doesn't directly give range queries. Use a sorted multiset.
- **Paths with weighted edges (not node values).** Adjust the prefix sum accumulation accordingly.
- **2D extension: grid paths with sum = target.** Totally different — uses prefix sums on the grid.
- **Why not store prefix sums as an array along the path?** The hashmap gives O(1) lookup; an array-and-scan would be O(depth) per lookup, bringing us back toward O(n²).
