# Path Sum III — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Path_Sum_III.md`](../Path_Sum_III.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/path-sum-iii/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The senior-bar prefix-sum-on-tree problem.** The lesson: **the "Subarray Sum Equals K" prefix-sum-plus-hashmap trick generalizes to TREE PATHS via DFS with backtracking on the hashmap.** **Read [`Path_Sum.md`](./Path_Sum.md) and [`Subarray_Sum_Equals_K.md`](../../Hashing_Sliding_Window/learn/Subarray_Sum_Equals_K.md) first.**

**Map of this file (10 sections):**

1. Read the problem
2. The brute force
3. The prefix-sum insight
4. The hashmap trick
5. Why backtracking is required
6. The sentinel `{0: 1}`
7. Code
8. Trace it
9. Common pitfalls
10. The shape — prefix-sum-on-tree

---

## 1. Read the problem

Given a binary tree and an integer `targetSum`, return the **COUNT of paths** where the sum of values equals `targetSum`.

**Key constraint:** the path does NOT need to start at the root or end at a leaf. It must go DOWNWARD (from a node to one of its descendants).

**Example:**

Tree:
```
         10
        /  \
       5   -3
      / \    \
     3   2   11
    / \   \
   3  -2   1
```
`targetSum = 8`. Valid paths:
- `5 → 3` (sum 8)
- `5 → 2 → 1` (sum 8)
- `-3 → 11` (sum 8)

Return **3**.

---

## 2. The brute force

For each node as a STARTING POINT, DFS downward counting paths with sum = target.

```
def countPaths(root, target):
    if not root: return 0
    return (pathsFrom(root, target)
            + countPaths(root.left, target)
            + countPaths(root.right, target))

def pathsFrom(node, target):
    if not node: return 0
    count = 0
    if node.val == target: count += 1
    count += pathsFrom(node.left, target - node.val)
    count += pathsFrom(node.right, target - node.val)
    return count
```

For each of n nodes, we do a DFS over its descendants — O(n²) in skewed trees, O(n log n) in balanced.

**We can do O(n)** with the prefix-sum + hashmap trick.

---

## 3. The prefix-sum insight

> **Mini-refresher: prefix sum on a tree path.**
>
> Define `prefix[v]` = sum of values from ROOT to node v (inclusive). As we DFS from root, we maintain this running prefix.
>
> For any path from ancestor `u` to descendant `v`:
>
> `sum(u → v) = prefix[v] - prefix[parent of u]`
>
> (Because adding parent_of_u's prefix to the path u→v gives root→v.)

We want paths with sum equal to target:
```
target = prefix[v] - prefix_at_some_ancestor
prefix_at_some_ancestor = prefix[v] - target
```

So: as we DFS, at each node `v` with current prefix sum `S`, COUNT how many ancestor prefixes equal `S - target`. That's the number of target-sum paths ENDING at v.

Sum across all v = total count of target-sum paths.

This is EXACTLY the Subarray Sum Equals K technique, on a tree path!

---

## 4. The hashmap trick

Maintain a hashmap `prefixCount[prefix_value] → count of ancestors with that prefix`.

At each node:
1. Update running prefix: `prefix += node.val`.
2. **LOOK UP** how many ancestors have `prefix - target` as their prefix: that's the count of target-sum paths ending at this node.
3. **REGISTER** the current prefix in the map (so descendants can use it).
4. **RECURSE** into children.
5. **BACKTRACK**: decrement the registered prefix when leaving (so siblings don't see this node's prefix).

```
def dfs(node, current_prefix):
    if not node: return 0
    current_prefix += node.val
    
    # Step 2: count paths ending here
    count = prefixCount.get(current_prefix - target, 0)
    
    # Step 3: register
    prefixCount[current_prefix] += 1
    
    # Step 4: recurse
    count += dfs(node.left, current_prefix)
    count += dfs(node.right, current_prefix)
    
    # Step 5: backtrack
    prefixCount[current_prefix] -= 1
    
    return count
```

---

## 5. Why backtracking is required

> **Mini-refresher: WHY decrement on return.**
>
> The hashmap must reflect ONLY the PREFIXES OF THE CURRENT ROOT-TO-NODE PATH. NOT prefixes from sibling subtrees.
>
> If we don't backtrack: after exploring the left subtree, its prefixes linger in the map. When we explore the right subtree, those left-subtree prefixes are STILL THERE — and we'd erroneously count "paths" starting in the LEFT subtree and ending in the RIGHT (which isn't an ancestor-descendant relationship).
>
> Decrementing on return REMOVES the current prefix from the map, keeping it path-relative.

This is the SAME backtracking discipline as in Path Sum II — undo state changes on return.

---

## 6. The sentinel `{0: 1}`

> **Mini-refresher: why `prefixCount[0] = 1` initially.**
>
> For paths that START AT THE ROOT, the "ancestor prefix" we'd subtract is THE EMPTY PREFIX (sum 0). The empty prefix represents "no ancestors" — i.e., starting at the root.
>
> By pre-seeding `prefixCount[0] = 1`, we account for the empty prefix. When a root-to-current path has sum equal to target, we look up `current_prefix - target = 0`, find 1, and count this path.
>
> Without the sentinel, we'd miss paths starting at the root.

---

## 7. Code

**C++:**

```cpp
class Solution {
    unordered_map<long long, int> prefixCount;
    int target;
    int count;

    void dfs(TreeNode* node, long long current_prefix) {
        if (!node) return;
        current_prefix += node->val;

        auto it = prefixCount.find(current_prefix - target);
        if (it != prefixCount.end()) count += it->second;

        prefixCount[current_prefix]++;
        dfs(node->left, current_prefix);
        dfs(node->right, current_prefix);
        prefixCount[current_prefix]--;
    }

public:
    int pathSum(TreeNode* root, int targetSum) {
        target = targetSum;
        count = 0;
        prefixCount[0] = 1;
        dfs(root, 0);
        return count;
    }
};
```

**Python:**

```python
from collections import defaultdict

def pathSum(root, targetSum):
    prefix_count = defaultdict(int)
    prefix_count[0] = 1
    count = 0
    
    def dfs(node, current):
        nonlocal count
        if not node: return
        current += node.val
        count += prefix_count[current - targetSum]
        prefix_count[current] += 1
        dfs(node.left, current)
        dfs(node.right, current)
        prefix_count[current] -= 1
    
    dfs(root, 0)
    return count
```

Complexity: **O(n) time, O(n) space.** Beats brute-force O(n²).

---

## 8. Trace it

**Tree:**
```
         10
        /  \
       5   -3
      / \    \
     3   2   11
    / \   \
   3  -2   1
```
**target = 8.**

```
prefix_count = {0: 1}. count = 0.

dfs(10, 0):
  current = 10.
  Look up 10 - 8 = 2. prefix_count[2] = 0. count += 0.
  prefix_count = {0:1, 10:1}.

  dfs(5, 10):
    current = 15.
    Look up 15 - 8 = 7. Not in map. count += 0.
    prefix_count = {0:1, 10:1, 15:1}.

    dfs(3, 15):
      current = 18.
      Look up 18 - 8 = 10. prefix_count[10] = 1. count += 1 → 1.   (path 5→3)
      prefix_count = {0:1, 10:1, 15:1, 18:1}.
      
      dfs(3, 18):
        current = 21. Look up 13. Not in map. ...
        ... (no matches in this subtree)
        prefix_count restored.
      
      dfs(-2, 18):
        current = 16. Look up 8. Not in map.
        ...
      
      prefix_count[18]-- = {0:1, 10:1, 15:1, 18:0}.

    dfs(2, 15):
      current = 17. Look up 9. Not in map.
      prefix_count[17]++.
      
      dfs(1, 17):
        current = 18. Look up 10. prefix_count[10] = 1. count += 1 → 2.   (path 5→2→1)
        ...
      
      prefix_count[17]-- back.
    
    prefix_count[15]-- back.

  dfs(-3, 10):
    current = 7. Look up -1. Not in map. count += 0.
    prefix_count = {0:1, 10:1, 7:1}.
    
    dfs(11, 7):
      current = 18. Look up 10. prefix_count[10] = 1. count += 1 → 3.   (path -3→11)
      ...
    
    prefix_count[7]-- back.

  prefix_count[10]-- back.

Return 3.  ✓
```

Three paths counted, each via the prefix-sum lookup.

---

## 9. Common pitfalls

1. **Forgetting the sentinel `prefix_count[0] = 1`.** Misses paths starting at the root.

2. **Forgetting to decrement on return.** Sibling subtrees see stale prefixes; over-counts.

3. **Using `int` for prefix sums.** For deep trees with large values, prefix sums overflow. Use `long long` in C++.

4. **Counting `current - target == 0` as a special case.** Already handled by the sentinel — `prefix_count[0] = 1` is exactly what `current - target = 0` looks up.

5. **Doing a fresh DFS from each node (brute force).** O(n²). The hashmap trick gives O(n).

6. **Incrementing the COUNT before LOOKING UP.** Order matters. Look up FIRST (before adding current prefix), then register.

7. **Using a stack instead of a hashmap.** Possible (you can scan the stack), but hashmap is O(1) lookup, stack is O(h). Use hashmap.

---

## 10. The shape — prefix-sum-on-tree

The pattern this problem teaches:

> **"Subarray Sum Equals K's prefix-sum + hashmap technique generalizes to TREE PATHS via DFS with backtracking on the hashmap."**

| Problem | Domain | Trick |
|---|---|---|
| Subarray Sum Equals K | array | prefix sum + hashmap |
| **This problem** | tree (ancestor-descendant paths) | prefix sum + hashmap + backtrack |
| Continuous Subarray Sum | array (modular) | prefix mod + hashmap |
| Subarray Sums Divisible by K | array | prefix mod + hashmap |
| Longest Subarray with Sum K | array | prefix + first-seen-index hashmap |
| Longest Path with Sum K on Tree | tree | prefix + first-seen-depth (with backtrack) |

**Pattern to internalize:**

> "Whenever a problem asks about CONTIGUOUS (sub-array or sub-path) SUMS, prefix sums are your friend. When checking 'sum equals target,' a hashmap of prefix sums seen so far gives O(1) lookup. On TREES, add BACKTRACKING — increment on entry, decrement on exit."

---

> **Self-check — the question to ask next time.**
>
> When you face counting paths on a tree with a sum property, ask:
>
> > **"Can I use prefix sums on the root-to-current path, look up `prefix - target` in a hashmap, and backtrack the hashmap on return?"**
>
> If yes, O(n) instead of O(n²).

---

## Cross-references

- **Reference card (post-mastery):** [`../Path_Sum_III.md`](../Path_Sum_III.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Path_Sum.md`](./Path_Sum.md), [`Path_Sum_II.md`](./Path_Sum_II.md).
  - [`../../Hashing_Sliding_Window/learn/Subarray_Sum_Equals_K.md`](../../Hashing_Sliding_Window/learn/Subarray_Sum_Equals_K.md) — array version.
  - Coming next: [`Paths_from_root_with_a_specified_sum.md`](./Paths_from_root_with_a_specified_sum.md), [`Sum_Root_to_Leaf_Numbers.md`](./Sum_Root_to_Leaf_Numbers.md), [`Lowest_Common_Ancestor_of_Binary_Tree.md`](./Lowest_Common_Ancestor_of_Binary_Tree.md).
