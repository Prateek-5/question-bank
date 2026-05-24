# Path Sum II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Path_Sum_II.md`](../Path_Sum_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/path-sum-ii/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: from "does a path exist?" (Path Sum I) to "collect all matching paths" — add a PATH BUFFER, snapshot at matching leaves, BACKTRACK on return.** Classic backtracking on trees. **Read [`Path_Sum.md`](./Path_Sum.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. The backtracking on trees
3. The snapshot-and-pop pattern
4. Code
5. Trace it
6. Why we MUST copy the path
7. Common pitfalls
8. The shape — path enumeration on trees

---

## 1. Read the problem

Given the root of a binary tree and an integer `targetSum`, return **ALL ROOT-TO-LEAF PATHS** where the sum of node values equals `targetSum`. Each path is a list of values.

**Example:** for tree
```
       5
      / \
     4   8
    /   / \
   11  13  4
  /  \    / \
 7    2  5   1
```
`targetSum = 22`. Matching paths:
- `[5, 4, 11, 2]` (sum 22)
- `[5, 8, 4, 5]` (sum 22)

Return `[[5,4,11,2], [5,8,4,5]]`.

---

## 2. The backtracking on trees

> **Mini-refresher: backtracking on a tree.**
>
> Walk DFS. Carry a PATH BUFFER (list of values from root to current). At each step:
> 1. **EXTEND**: append `node.val` to path.
> 2. **CHECK**: if leaf and sum matches → record a SNAPSHOT of path.
> 3. **RECURSE**: into left and right children.
> 4. **REVERT**: pop the last value (we're going back up).

This "extend going down, revert going up" is identical to backtracking on arrays or subsets — just applied to a tree's recursion.

---

## 3. The snapshot-and-pop pattern

```
def dfs(node, remaining):
    if node is null: return
    path.append(node.val)
    
    if node is leaf and node.val == remaining:
        result.append(path.copy())          # SNAPSHOT
    
    dfs(node.left, remaining - node.val)
    dfs(node.right, remaining - node.val)
    
    path.pop()                                # REVERT
```

Three critical lines:
- `path.append(node.val)` — extend.
- `result.append(path.copy())` — SNAPSHOT (don't share reference; see Section 6).
- `path.pop()` — revert before returning.

The pop is what makes it backtracking. Without it, path accumulates incorrectly across sibling subtrees.

---

## 4. Code

**C++:**

```cpp
class Solution {
    vector<vector<int>> result;
    vector<int> path;

    void dfs(TreeNode* node, int remaining) {
        if (!node) return;
        path.push_back(node->val);

        if (!node->left && !node->right && node->val == remaining) {
            result.push_back(path);          // copy by value
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

**Python:**

```python
def pathSum(root, targetSum):
    result = []
    path = []
    def dfs(node, remaining):
        if not node: return
        path.append(node.val)
        if not node.left and not node.right and node.val == remaining:
            result.append(path[:])           # snapshot copy
        dfs(node.left, remaining - node.val)
        dfs(node.right, remaining - node.val)
        path.pop()
    dfs(root, targetSum)
    return result
```

Complexity: **O(n × h) worst case** (n nodes; each matching path is O(h) to copy). Space: O(h) for recursion + output.

---

## 5. Trace it

**Tree:**
```
       5
      / \
     4   8
    /   / \
   11  13  4
  /  \    / \
 7    2  5   1
```
**target = 22.**

```
dfs(5, 22). path = [5].
  Not leaf.
  dfs(4, 17). path = [5, 4].
    Not leaf.
    dfs(11, 13). path = [5, 4, 11].
      Not leaf.
      dfs(7, 2). path = [5, 4, 11, 7]. LEAF. 7 != 2 → no record. POP path = [5, 4, 11].
      dfs(2, 2). path = [5, 4, 11, 2]. LEAF. 2 == 2 → RECORD [5, 4, 11, 2]. POP.
      POP path = [5, 4].
    POP path = [5].
  dfs(8, 17). path = [5, 8].
    Not leaf.
    dfs(13, 9). LEAF. 13 != 9 → no record. POP.
    dfs(4, 9). path = [5, 8, 4].
      Not leaf.
      dfs(5, 5). LEAF. 5 == 5 → RECORD [5, 8, 4, 5]. POP.
      dfs(1, 5). LEAF. 1 != 5 → no record. POP.
      POP.
    POP.
  POP.

Final: result = [[5, 4, 11, 2], [5, 8, 4, 5]].  ✓
```

Watch the path "breathe" — extend going down, contract on return. The pops restore state for sibling exploration.

---

## 6. Why we MUST copy the path

> **Mini-refresher: copy vs reference when recording.**
>
> If we did `result.append(path)` (Python) without `[:]`, we'd append a REFERENCE to the live `path` list. Subsequent `path.pop()` calls would mutate the recorded entry too — final `result` would contain references to the (eventually empty) `path`.
>
> SNAPSHOT: `path[:]` (Python), `path` (C++ — vector pushes by value), `[...path]` (JS spread).
>
> Always copy when recording mutable state in backtracking.

**C++ note:** `result.push_back(path)` COPIES the vector by default. So no explicit `.copy()` needed.

**Python/JS:** need explicit copy.

---

## 7. Common pitfalls

1. **Forgetting to POP at the end.** Path accumulates across siblings. Wrong results.

2. **Recording a REFERENCE instead of a snapshot.** All entries in `result` end up pointing to the same (final-empty) path.

3. **Recording BEFORE checking leaf.** Records partial paths too. Must check leaf condition.

4. **Recording WHEN remaining < 0 prematurely.** Don't prune on negative remaining unless all values are non-negative (and the problem doesn't promise that — values can be negative).

5. **Wrong leaf check.** A leaf is a node with NO CHILDREN — both `left == null AND right == null`. A node with one child is NOT a leaf.

6. **Not handling the empty tree.** If `root == null`, the recursion returns immediately — `result` stays empty. Correct.

7. **Sum check at leaf uses `node.val == remaining` (not `+= node.val`).** After deducting earlier nodes, `remaining` is what's left to match at the leaf.

---

## 8. The shape — path enumeration on trees

The pattern this problem teaches:

> **"Enumerate root-to-leaf paths satisfying property P = backtracking on the tree. Push value on descent, pop on ascent. Record snapshots at qualifying leaves."**

| Problem | Snapshot at leaf if... |
|---|---|
| **This problem** | sum matches target |
| Binary Tree Paths | always (collect ALL root-to-leaf paths) |
| Smallest String Starting From Leaf | always; reverse path string |
| Longest String Path | record max length |
| Sum Root to Leaf Numbers | accumulate path as a number; sum at leaves |
| All Paths From Source to Target (graph) | reached the target node |

**Pattern to internalize:**

> "Path enumeration = backtracking on the tree. Append, recurse, pop. Snapshot AT LEAVES (or wherever the path-ending condition is)."

---

> **Self-check — the question to ask next time.**
>
> When you face "collect all paths satisfying property P," ask:
>
> > **"Can I DFS with a path buffer, snapshotting (copying) at qualifying leaves, and popping on return?"**
>
> If yes, you've got the template.

---

## Cross-references

- **Reference card (post-mastery):** [`../Path_Sum_II.md`](../Path_Sum_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Path_Sum.md`](./Path_Sum.md).
  - Coming next: [`Path_Sum_III.md`](./Path_Sum_III.md) — same family with a TWIST.
